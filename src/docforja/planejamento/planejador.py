"""Orquestrador do Planejamento do Vídeo (Marco M4).

Executa o fluxo completo P1 -> P3 -> P4 -> P5 -> P6 -> P8:
1. Leitura do roteiro (se não fornecida)
2. Estratégia visual por bloco (P3)
3. Decupagem em shots (P4)
4. Consolidação de ativos (P5)
5. Verificação e autocorreção de dosagem D1-D17 (P6)
6. Estimativa de produção e adequação orçamentária (P8)
7. Geração de relatórios oficiais (plano.json, plano.md, verificacao.md, estimativa.md,
   numeros_na_tela.md)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docforja.esquemas import Bloco, Plano
from docforja.planejamento.ativos import consolidar_ativos_plano
from docforja.planejamento.dosagem import ResultadoVerificacao, VerificadorDosagem
from docforja.planejamento.estimativa import RelatorioEstimativa, estimar_tempo_plano
from docforja.planejamento.estrategia import planejar_estrategias
from docforja.planejamento.leitura import ler_roteiro_formatado
from docforja.planejamento.relatorios import gravar_relatorios_planejamento
from docforja.planejamento.shots import gerar_shots_bloco


class PlanejadorVideo:
    """Orquestrador do plano de vídeo de um projeto."""

    def __init__(
        self,
        caminho_dosagem_yaml: Path = Path("config/dosagem.yaml"),
        caminho_benchmark_json: Path = Path("config/benchmark.json"),
    ) -> None:
        self.verificador = VerificadorDosagem(caminho_config=caminho_dosagem_yaml)
        self.caminho_benchmark_json = caminho_benchmark_json

    def planejar_projeto(
        self,
        slug_projeto: str,
        roteiro_texto: str,
        diretorio_saida: Path | None = None,
        preset: str = "padrao",
        kit: str = "cinza-e-brasa@1.0",
        idiomas: dict[str, Any] | None = None,
        tempos_reais_segmentos: dict[str, float] | None = None,
    ) -> tuple[Plano, ResultadoVerificacao, RelatorioEstimativa, dict[str, Path] | None]:
        """Gera o plano completo do projeto, valida com D1-D17 e escreve os relatórios."""
        idiomas_cfg = idiomas or {"principal": "pt-BR", "extras": ["en", "es"]}
        orcamento = 120
        if preset == "rapido":
            orcamento = 60
        elif preset == "caprichado":
            orcamento = 240

        # P1: Leitura do roteiro
        blocos_proc = ler_roteiro_formatado(roteiro_texto)

        # P3: Estratégia por bloco
        estrategias = planejar_estrategias(blocos_proc)

        # P4: Geração de shots
        blocos_plano: list[Bloco] = []
        ativo_counter = [1]
        total_blocos = len(blocos_proc)

        for b_proc, est in zip(blocos_proc, estrategias, strict=True):
            shots = gerar_shots_bloco(
                bloco=b_proc,
                estrategia=est,
                tempos_reais=tempos_reais_segmentos,
                total_blocos=total_blocos,
                ativo_counter=ativo_counter,
            )
            blocos_plano.append(
                Bloco(
                    id=b_proc.id,
                    titulo=b_proc.nome,
                    modo_visual=est.modo_visual,
                    clima_musical=est.clima_musical,
                    contexto=est.contexto,
                    shots=shots,
                )
            )

        # P5: Consolidação de ativos
        ativos_map = consolidar_ativos_plano(blocos_plano, preset=preset)

        # Cria instância master do Plano
        plano = Plano(
            versao=3,
            projeto=slug_projeto,
            kit=kit,
            preset=preset,
            tipo="longo",
            idiomas=idiomas_cfg,
            orcamento_producao_min=orcamento,
            estimativa_producao_min=0,
            blocos=blocos_plano,
            ativos=ativos_map,
            musica=[{"bloco": b.id, "clima": b.clima_musical, "faixa": None} for b in blocos_plano],
            verificacao={},
        )

        # P6: Verificação de dosagem e autocorreções (máx 3 voltas se necessário)
        resultado_verif = self.verificador.verificar_e_corrigir(
            plano=plano,
            blocos_processados=blocos_proc,
            autocorrige=True,
        )

        # P8: Estimativa de produção e conformidade D15
        relatorio_est = estimar_tempo_plano(plano)
        plano.estimativa_producao_min = int(relatorio_est.tempo_total_minutos)

        # Gravação de relatórios se diretório fornecido
        caminhos_relatorios = None
        if diretorio_saida:
            caminhos_relatorios = gravar_relatorios_planejamento(
                diretorio_saida=diretorio_saida,
                plano=plano,
                resultado_verificacao=resultado_verif,
                relatorio_estimativa=relatorio_est,
                blocos_processados=blocos_proc,
                roteiro_texto=roteiro_texto,
            )

        return plano, resultado_verif, relatorio_est, caminhos_relatorios
