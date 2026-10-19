"""Executor de pipeline com paralelismo, controle de GPU, retomada e gates."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from docforja.nucleo.banco import BancoProjeto
from docforja.nucleo.etapas import DefinicaoEtapa, PipelineGrafo, calcular_hash_dados
from docforja.nucleo.eventos import BarramentoEventos, Evento, barramento_global
from docforja.nucleo.gpu import SemaforoGPU, semaforo_gpu
from docforja.nucleo.projeto import Projeto


@dataclass
class ContextoEtapa:
    """Contexto passado para o handler de cada etapa."""

    projeto: Projeto
    etapa: DefinicaoEtapa
    banco: BancoProjeto
    alvo: str | None = None  # Bloco, ativo ou idioma específico
    dados_extras: dict[str, Any] | None = None


HandlerEtapa = Callable[[ContextoEtapa], Coroutine[Any, Any, Any] | Any]


class HandlerEtapaAusenteError(RuntimeError):
    """Indica que uma etapa não possui implementação registrada."""


class ExecutorPipeline:
    """Executa o pipeline do projeto respeitando DAG, concorrência e semáforo de GPU."""

    def __init__(
        self,
        projeto: Projeto,
        grafo: PipelineGrafo | None = None,
        semaforo: SemaforoGPU | None = None,
        barramento: BarramentoEventos | None = None,
    ) -> None:
        self.projeto = projeto
        self.banco = BancoProjeto(projeto.banco_file)
        self.semaforo = semaforo or semaforo_gpu
        self.barramento = barramento or barramento_global
        self._handlers: dict[str, HandlerEtapa] = {}

        # Carrega o grafo de acordo com o tipo de projeto
        opcoes = projeto.obter_opcoes()
        tipo_projeto = opcoes.get("tipo", "longo")
        self.grafo = grafo or PipelineGrafo.carregar(tipo_projeto=tipo_projeto)

        # Trata retomada: se o processo anterior foi derrubado em 'executando', volta a 'pendente'
        for etapa in self.banco.listar_etapas():
            if etapa["status"] == "executando":
                self.banco.salvar_etapa(
                    etapa["id"],
                    status="pendente",
                    erro="Interrompido por encerramento do processo",
                )

    def registrar_handler(self, etapa_id: str, handler: HandlerEtapa) -> None:
        self._handlers[etapa_id] = handler

    def aprovar_gate(self, etapa_id: str) -> None:
        """Libera um gate (como REVISAO) para prosseguir para a produção."""
        self.banco.definir_meta(f"gate_{etapa_id}_aprovado", "true")
        self.banco.salvar_etapa(etapa_id, status="concluida")
        self.barramento.emitir(
            Evento(
                projeto=self.projeto.slug,
                tipo="etapa_concluida",
                etapa_id=etapa_id,
                dados={"mensagem": f"Gate {etapa_id} aprovado"},
            )
        )

    def invalidar(self, etapa_id: str) -> list[str]:
        """Invalida seletivamente a etapa e todas as etapas dependentes a jusante."""
        dependentes = self.grafo.obter_dependentes(etapa_id)
        alvos = [etapa_id, *sorted(dependentes)]
        self.banco.invalidar_etapas(alvos)
        self.barramento.emitir(
            Evento(
                projeto=self.projeto.slug,
                tipo="invalidacao_seletiva",
                etapa_id=etapa_id,
                dados={"invalidadas": alvos},
            )
        )
        return alvos

    def _calcular_hash_etapa(self, def_etapa: DefinicaoEtapa) -> str:
        """Calcula o hash de entrada representativo desta etapa para idempotência."""
        opcoes = self.projeto.obter_opcoes()
        dados = {
            "id": def_etapa.id,
            "needs": def_etapa.needs,
            "preset": opcoes.get("preset"),
            "kit": opcoes.get("kit"),
            "roteiro_hash": calcular_hash_dados(self.projeto.obter_roteiro()),
        }
        return calcular_hash_dados(dados)

    async def _executar_etapa(self, def_etapa: DefinicaoEtapa) -> None:
        """Executa uma única etapa com suporte a semáforo de GPU e medição de tempo."""
        # Se for gate, verifica se foi aprovado
        if def_etapa.gate:
            aprovado = self.banco.obter_meta(f"gate_{def_etapa.id}_aprovado") == "true"
            if not aprovado:
                self.banco.salvar_etapa(def_etapa.id, status="pausada_revisao")
                self.barramento.emitir(
                    Evento(
                        projeto=self.projeto.slug,
                        tipo="etapa_pausada",
                        etapa_id=def_etapa.id,
                        dados={"mensagem": f"Aguardando liberação do gate {def_etapa.id}"},
                    )
                )
                return

        # Verifica idempotência via hash de entrada
        hash_atual = self._calcular_hash_etapa(def_etapa)
        registro = self.banco.obter_etapa(def_etapa.id)
        if (
            registro
            and registro["status"] == "concluida"
            and registro["hash_entrada"] == hash_atual
            and def_etapa.id in self._handlers
        ):
            # Já concluído com a mesma entrada; não reexecuta
            return

        self.banco.salvar_etapa(def_etapa.id, status="executando", hash_entrada=hash_atual)
        self.barramento.emitir(
            Evento(
                projeto=self.projeto.slug,
                tipo="etapa_iniciada",
                etapa_id=def_etapa.id,
                dados={"gpu": def_etapa.gpu},
            )
        )

        started = time.perf_counter()
        ctx = ContextoEtapa(projeto=self.projeto, etapa=def_etapa, banco=self.banco)

        try:
            # Executa com semáforo de GPU se a etapa exigir GPU
            if def_etapa.gpu:
                async with self.semaforo.adquirir(
                    modelo=def_etapa.gpu,
                    tarefa=def_etapa.id,
                    projeto=self.projeto.slug,
                ):
                    await self._despachar_handler(def_etapa.id, ctx)
            else:
                await self._despachar_handler(def_etapa.id, ctx)

            duracao = time.perf_counter() - started
            self.banco.salvar_etapa(
                def_etapa.id,
                status="concluida",
                hash_entrada=hash_atual,
                duracao_s=round(duracao, 3),
            )
            self.barramento.emitir(
                Evento(
                    projeto=self.projeto.slug,
                    tipo="etapa_concluida",
                    etapa_id=def_etapa.id,
                    dados={"duracao_s": round(duracao, 3)},
                )
            )
        except Exception as exc:
            duracao = time.perf_counter() - started
            erro_msg = str(exc) or type(exc).__name__
            self.banco.salvar_etapa(
                def_etapa.id,
                status="falhou",
                duracao_s=round(duracao, 3),
                erro=erro_msg,
            )
            self.barramento.emitir(
                Evento(
                    projeto=self.projeto.slug,
                    tipo="etapa_falhou",
                    etapa_id=def_etapa.id,
                    dados={"erro": erro_msg, "duracao_s": round(duracao, 3)},
                )
            )
            raise exc

    async def _despachar_handler(self, etapa_id: str, ctx: ContextoEtapa) -> None:
        handler = self._handlers.get(etapa_id)
        if handler is None:
            raise HandlerEtapaAusenteError(
                f"A etapa {etapa_id} não possui um processador registrado."
            )

        res = handler(ctx)
        if asyncio.iscoroutine(res):
            await res

    async def executar(self, max_concorrencia: int = 4) -> dict[str, str]:
        """Loop de execução contínua até que não haja mais etapas prontas ou atinja um gate."""
        executando: set[str] = set()
        background_tasks: set[asyncio.Task[None]] = set()

        # Bancos de versões anteriores podem conter etapas concluídas pelo handler
        # placeholder. Rebaixa esses resultados para falha até que haja processador real.
        for etapa in self.grafo.etapas.values():
            registro = self.banco.obter_etapa(etapa.id)
            if (
                registro
                and registro["status"] == "concluida"
                and not etapa.gate
                and etapa.id not in self._handlers
            ):
                self.banco.salvar_etapa(
                    etapa.id,
                    status="falhou",
                    erro=f"A etapa {etapa.id} não possui um processador registrado.",
                )

        def _coletar_tarefa(task: asyncio.Task[None]) -> None:
            background_tasks.discard(task)
            if not task.cancelled():
                # O estado de falha já é persistido em _executar_etapa; consumir
                # a exceção evita avisos não tratados no loop do asyncio.
                task.exception()

        while True:
            # Atualiza status das etapas no banco
            todas = {r["id"]: r["status"] for r in self.banco.listar_etapas()}
            concluidas = {k for k, v in todas.items() if v == "concluida"}
            falhadas = {k for k, v in todas.items() if v == "falhou"}
            pausadas = {k for k, v in todas.items() if v == "pausada_revisao"}

            if falhadas:
                # Interrompe se houve falha crítica em alguma etapa
                break

            prontas = self.grafo.obter_prontas(concluidas=concluidas, executando=executando)
            # Filtra etapas pausadas em gate
            prontas = [e for e in prontas if e.id not in pausadas]

            if not prontas and not executando:
                # Não há mais trabalho a ser feito
                break

            # Dispara tarefas prontas até o limite de concorrência
            slots_livres = max(1, max_concorrencia - len(executando))
            lote = prontas[:slots_livres]

            if not lote and executando:
                # Aguarda alguma tarefa em andamento concluir
                await asyncio.sleep(0.02)
                continue

            tarefas_coros = []
            for etapa in lote:
                executando.add(etapa.id)

                async def wrapper(e: DefinicaoEtapa) -> None:
                    try:
                        await self._executar_etapa(e)
                    finally:
                        executando.discard(e.id)

                tarefas_coros.append(wrapper(etapa))

            if tarefas_coros:
                # Inicia as tarefas do lote sem bloquear o loop
                for coro in tarefas_coros:
                    task = asyncio.create_task(coro)
                    background_tasks.add(task)
                    task.add_done_callback(_coletar_tarefa)

            await asyncio.sleep(0.02)

        return {r["id"]: r["status"] for r in self.banco.listar_etapas()}
