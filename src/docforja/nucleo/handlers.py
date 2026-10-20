"""Handlers reais atualmente disponíveis para execução de projetos."""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import asdict
from pathlib import Path

from docforja.audio.adaptadores.kokoro import AdaptadorKokoro
from docforja.audio.alinhamento import AlinhadorWhisperX
from docforja.audio.metricas import calcular_wer
from docforja.audio.narracao import OrquestradorNarracao, ResultadoSegmentoAudio
from docforja.esquemas import Ativo, Bloco, Plano, Shot
from docforja.io import atomic_write_json, atomic_write_text
from docforja.llm.roteador import RoteadorLLM
from docforja.midia.resolucao import resolver_ativos_projeto
from docforja.nucleo.etapas import calcular_hash_dados
from docforja.nucleo.executor import ContextoEtapa, ExecutorPipeline
from docforja.nucleo.projeto import Projeto
from docforja.planejamento.ativos import consolidar_ativos_plano
from docforja.planejamento.dosagem import VerificadorDosagem
from docforja.planejamento.entidades import SegmentoProcessado
from docforja.planejamento.estimativa import estimar_tempo_plano
from docforja.planejamento.estrategia import EstrategiaBloco, planejar_estrategias
from docforja.planejamento.leitura import ler_roteiro_formatado
from docforja.planejamento.previa import renderizar_previa
from docforja.planejamento.relatorios import (
    gerar_estimativa_md,
    gerar_numeros_na_tela_md,
    gerar_plano_md,
    gerar_verificacao_md,
)
from docforja.planejamento.shots import (
    TEMPLATES_CATALOGO,
    gerar_shots_bloco,
    reparar_shots_bloco_via_llm,
)
from docforja.planejamento.tempos import intervalos_narrados, segmentos_em_ordem
from docforja.settings import load_settings


def _criar_orquestrador() -> OrquestradorNarracao:
    settings = load_settings()
    ambientes = settings.python_environments
    kokoro = AdaptadorKokoro(python_path=ambientes.get("kokoro"))
    whisperx = AlinhadorWhisperX(
        python_path=ambientes.get("whisperx"), modelo=settings.alinhamento.modelo_asr
    )
    return OrquestradorNarracao(adaptador_tts=kokoro, alinhador=whisperx)


def _segmentos_projeto(projeto: Projeto) -> list[SegmentoProcessado]:
    blocos = ler_roteiro_formatado(projeto.obter_roteiro())
    segmentos = [segmento for bloco in blocos for segmento in bloco.segmentos]
    if not segmentos:
        raise ValueError("Não há segmentos para narrar.")
    return segmentos


def _audio_idioma(projeto: Projeto) -> tuple[str, Path]:
    idioma = projeto.obter_opcoes().get("idiomas", {}).get("principal", "pt-BR")
    return idioma, projeto.pastas.audio / idioma


def _localizar_audio_segmento(pasta_segs: Path, sid: str) -> Path:
    candidatos: list[tuple[int, int, Path]] = []
    for f in pasta_segs.glob(f"{sid}*.wav"):
        if f.name.endswith(("_silence.wav", "_raw.wav")):
            continue
        m = re.search(r"_take(\d+)", f.name)
        take_num = int(m.group(1)) if m else 1
        is_final = 1 if f.name.endswith("_final.wav") else 0
        candidatos.append((take_num, is_final, f))
    if candidatos:
        candidatos.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return candidatos[0][2]
    return pasta_segs / f"{sid}.wav"


def registrar_handlers_disponiveis(
    executor: ExecutorPipeline,
    orquestrador: OrquestradorNarracao | None = None,
    roteador_llm: RoteadorLLM | None = None,
) -> ExecutorPipeline:
    """Registra as etapas implementadas e compartilhadas por CLI e API.

    Etapas ainda sem implementação permanecem sem handler para que o executor
    reporte a lacuna, em vez de marcá-las como concluídas artificialmente.
    """

    def validar_entrada(ctx: ContextoEtapa) -> None:
        roteiro = ctx.projeto.obter_roteiro()
        if not roteiro.strip():
            raise ValueError("O projeto não possui roteiro em 00_entrada/roteiro.md.")

    def ler_roteiro(ctx: ContextoEtapa) -> None:
        roteiro = ctx.projeto.obter_roteiro()
        blocos = ler_roteiro_formatado(roteiro)
        total_segmentos = sum(len(bloco.segmentos) for bloco in blocos)
        if total_segmentos == 0:
            raise ValueError(
                "Nenhum segmento reconhecido. Use o formato ## B<n> e **B<n>-S<nn>**."
            )

        atomic_write_json(
            ctx.projeto.pastas.plano / "leitura.json",
            {
                "versao": 1,
                "blocos": [asdict(bloco) for bloco in blocos],
                "total_segmentos": total_segmentos,
            },
        )

    def planejar_estrategia(ctx: ContextoEtapa) -> None:
        leitura_path = ctx.projeto.pastas.plano / "leitura.json"
        if not leitura_path.is_file():
            raise FileNotFoundError("Leitura do roteiro ausente para a estratégia.")
        leitura = json.loads(leitura_path.read_text(encoding="utf-8"))
        blocos = ler_roteiro_formatado(ctx.projeto.obter_roteiro())
        if not blocos or leitura.get("blocos") != [asdict(bloco) for bloco in blocos]:
            raise ValueError("A leitura salva não corresponde aos blocos do roteiro atual.")
        estrategias = planejar_estrategias(blocos)
        atomic_write_json(
            ctx.projeto.pastas.plano / "estrategia.json",
            {"versao": 1, "blocos": [asdict(item) for item in estrategias]},
        )

    def gerar_shots(ctx: ContextoEtapa) -> None:
        estrategia_path = ctx.projeto.pastas.plano / "estrategia.json"
        if not estrategia_path.is_file():
            raise FileNotFoundError("Estratégia ausente para gerar os shots.")
        dados = json.loads(estrategia_path.read_text(encoding="utf-8"))
        blocos = ler_roteiro_formatado(ctx.projeto.obter_roteiro())
        estrategias = [EstrategiaBloco(**item) for item in dados.get("blocos", [])]
        if [item.bloco_id for item in estrategias] != [bloco.id for bloco in blocos]:
            raise ValueError("Estratégia não corresponde aos blocos do roteiro atual.")

        _, pasta_audio = _audio_idioma(ctx.projeto)
        segmentos_audio_path = pasta_audio / "segmentos.json"
        tempos_reais = None
        segs_audio: list[dict] = []
        modo_tempos = "estimados"
        if segmentos_audio_path.is_file():
            try:
                segs_audio = json.loads(segmentos_audio_path.read_text(encoding="utf-8"))
                ids_audio = {item["id"] for item in segs_audio}
                ids_roteiro = {s.id for b in blocos for s in b.segmentos}
                if ids_audio == ids_roteiro:
                    tempos_reais = {
                        item["id"]: round(float(item["fim_s"]) - float(item["inicio_s"]), 3)
                        for item in segs_audio
                    }
                    modo_tempos = "reais"
            except Exception:
                tempos_reais = None
                modo_tempos = "estimados"

        ativo_counter = [1]
        saidas = []
        for bloco, estrategia in zip(blocos, estrategias, strict=True):
            shots = gerar_shots_bloco(
                bloco,
                estrategia,
                tempos_reais=tempos_reais,
                total_blocos=len(blocos),
                ativo_counter=ativo_counter,
            )
            ids_roteiro = [segmento.id for segmento in bloco.segmentos]
            ids_cobertos = segmentos_em_ordem(shots)
            if ids_cobertos != ids_roteiro:
                raise ValueError(f"Shots do bloco {bloco.id} não cobrem o roteiro exatamente.")
            if tempos_reais is not None:
                intervalos_narrados(
                    shots, [item for item in segs_audio if item["id"] in ids_roteiro]
                )
            saidas.append({"bloco_id": bloco.id, "shots": [shot.model_dump() for shot in shots]})
        atomic_write_json(
            ctx.projeto.pastas.plano / "shots.json",
            {"versao": 1, "tempos": modo_tempos, "blocos": saidas},
        )

    def blocos_com_shots(ctx: ContextoEtapa) -> list[Bloco]:
        if not shots_validos(ctx):
            raise ValueError("Shots ausentes ou inválidos para consolidar os ativos.")
        dados = json.loads(
            (ctx.projeto.pastas.plano / "shots.json").read_text(encoding="utf-8")
        )
        roteiro = ler_roteiro_formatado(ctx.projeto.obter_roteiro())
        return [
            Bloco(
                id=bloco.id,
                titulo=bloco.nome,
                shots=[Shot.model_validate(item) for item in saida["shots"]],
            )
            for bloco, saida in zip(roteiro, dados["blocos"], strict=True)
        ]

    def consolidar_ativos(ctx: ContextoEtapa) -> None:
        blocos = blocos_com_shots(ctx)
        preset = ctx.projeto.obter_opcoes().get("preset", "padrao")
        ativos = consolidar_ativos_plano(blocos, preset=preset)
        atomic_write_json(
            ctx.projeto.pastas.plano / "ativos.json",
            {
                "versao": 1,
                "ativos": {aid: item.model_dump(mode="json") for aid, item in ativos.items()},
            },
        )

    def verificar_dosagem(ctx: ContextoEtapa) -> None:
        if not alinhamento_valido(ctx):
            raise ValueError("Alinhamento aprovado ausente para verificar a dosagem.")
        if not estrategia_valida(ctx):
            raise ValueError("Estratégia ausente ou inválida para verificação.")

        # Se os shots foram gerados com tempos estimados mas o áudio já tem tempos reais, recalcula
        if not shots_validos(ctx):
            gerar_shots(ctx)
            consolidar_ativos(ctx)
        if not shots_validos(ctx) or not ativos_validos(ctx):
            raise ValueError("Shots ou ativos ausentes/inválidos para verificação.")

        pasta = ctx.projeto.pastas.plano
        estrategias = json.loads((pasta / "estrategia.json").read_text(encoding="utf-8"))["blocos"]
        estrategias_por_id = {item["bloco_id"]: item for item in estrategias}
        blocos = blocos_com_shots(ctx)
        for bloco in blocos:
            estrategia = estrategias_por_id[bloco.id]
            bloco.modo_visual = estrategia["modo_visual"]
            bloco.clima_musical = estrategia["clima_musical"]
            bloco.contexto = estrategia.get("contexto")
        ativos_dados = json.loads((pasta / "ativos.json").read_text(encoding="utf-8"))["ativos"]
        ativos = {aid: Ativo.model_validate(item) for aid, item in ativos_dados.items()}
        opcoes = ctx.projeto.obter_opcoes()
        preset = opcoes.get("preset", "padrao")
        verificador = VerificadorDosagem()
        presets = verificador.config.get("presets", {})
        if preset not in presets:
            raise ValueError(f"Preset de dosagem desconhecido: {preset}")
        plano = Plano(
            versao=3,
            projeto=ctx.projeto.slug,
            kit=opcoes.get("kit", "cinza-e-brasa@1.0"),
            preset=preset,
            tipo="longo",
            idiomas=opcoes.get("idiomas", {"principal": "pt-BR", "extras": []}),
            orcamento_producao_min=int(presets[preset]["orcamento_minutos"]),
            blocos=blocos,
            ativos=ativos,
            musica=[{"bloco": b.id, "clima": b.clima_musical, "faixa": None} for b in blocos],
        )
        blocos_processados = ler_roteiro_formatado(ctx.projeto.obter_roteiro())
        _, pasta_audio = _audio_idioma(ctx.projeto)
        segmentos_audio = json.loads(
            (pasta_audio / "segmentos.json").read_text(encoding="utf-8")
        )
        tempos_reais = {
            item["id"]: float(item["fim_s"]) - float(item["inicio_s"])
            for item in segmentos_audio
        }
        resultado = verificador.verificar_e_corrigir(
            plano,
            blocos_processados=blocos_processados,
            autocorrige=True,
            tempos_reais=tempos_reais,
        )

        # Loop de reenvio ao LLM só dos blocos reprovados (máx. 3 voltas)
        loop_llm = 3
        voltas = 0
        while not resultado.aprovado and voltas < loop_llm:
            voltas += 1
            blocos_violados = {
                v.bloco_id for v in resultado.violacoes if not v.corrigida and v.bloco_id
            }
            if not blocos_violados:
                break

            roteador = obter_roteador()
            if roteador is None:
                break

            blocos_por_id = {b.id: b for b in plano.blocos}
            blocos_proc_por_id = {b.id: b for b in blocos_processados}
            reparou_algum = False

            for bid in sorted(blocos_violados):
                if bid not in blocos_por_id or bid not in blocos_proc_por_id:
                    continue
                violacoes_bloco = [
                    v for v in resultado.violacoes if not v.corrigida and v.bloco_id == bid
                ]
                novos_shots = reparar_shots_bloco_via_llm(
                    bloco=blocos_por_id[bid],
                    bloco_proc=blocos_proc_por_id[bid],
                    estrategia=estrategias_por_id.get(bid, {}),
                    violacoes=violacoes_bloco,
                    roteador=roteador,
                )
                if novos_shots:
                    blocos_por_id[bid].shots = novos_shots
                    reparou_algum = True

            if not reparou_algum:
                break

            plano.ativos = consolidar_ativos_plano(plano.blocos, preset=preset)
            resultado = verificador.verificar_e_corrigir(
                plano,
                blocos_processados=blocos_processados,
                autocorrige=True,
                tempos_reais=tempos_reais,
            )

        plano.verificacao["fase"] = "pre_resolucao_ativos"
        plano_dados = plano.model_dump(mode="json")
        relatorio_dados = asdict(resultado)
        relatorio_dados["hash_plano"] = calcular_hash_dados(plano_dados)
        relatorio_dados["hash_entradas"] = hashes_entradas_p6(ctx)
        atomic_write_json(pasta / "plano_verificado.json", plano_dados)
        if not resultado.aprovado:
            atomic_write_json(pasta / "verificacao.json", relatorio_dados)
            raise RuntimeError("Plano reprovado pela verificação de dosagem D1-D17.")

        blocos_processados = ler_roteiro_formatado(ctx.projeto.obter_roteiro())
        aviso = "> Rascunho M4: ativos ainda não resolvidos e prévia em vídeo pendente.\n\n"
        relatorios = {
            "plano.md": aviso + gerar_plano_md(plano, blocos_processados),
            "verificacao.md": gerar_verificacao_md(resultado),
            "estimativa.md": aviso + gerar_estimativa_md(estimar_tempo_plano(plano)),
            "numeros_na_tela.md": gerar_numeros_na_tela_md(
                plano, ctx.projeto.obter_roteiro()
            ),
        }
        atomic_write_json(pasta / "plano.json", plano_dados)
        for nome, conteudo in relatorios.items():
            atomic_write_text(pasta / nome, conteudo)
        relatorio_dados["hash_relatorios"] = {
            nome: calcular_hash_dados(pasta / nome)
            for nome in ["plano.json", *relatorios]
        }
        atomic_write_json(pasta / "verificacao.json", relatorio_dados)

    def resolver_ativos(ctx: ContextoEtapa) -> None:
        if not dosagem_valida(ctx):
            raise ValueError("Plano verificado e dosagem aprovada ausentes para resolver ativos.")
        resolver_ativos_projeto(ctx.projeto)

    async def estimar_e_renderizar_previa(ctx: ContextoEtapa) -> None:
        if previa_valida(ctx):
            return
        if not dosagem_valida(ctx) or not resolucao_valida(ctx):
            raise ValueError("Plano verificado ou ativos resolvidos ausentes para P8.")
        await asyncio.to_thread(renderizar_previa, ctx.projeto)

    def obter_orquestrador() -> OrquestradorNarracao:
        nonlocal orquestrador
        if orquestrador is None:
            orquestrador = _criar_orquestrador()
        return orquestrador

    def obter_roteador() -> RoteadorLLM | None:
        nonlocal roteador_llm
        if roteador_llm is None:
            try:
                roteador_llm = RoteadorLLM()
            except Exception:
                roteador_llm = None
        return roteador_llm

    async def gerar_narracao(ctx: ContextoEtapa) -> None:
        opcoes = ctx.projeto.obter_opcoes()
        if opcoes.get("narracao_pronta"):
            raise RuntimeError("Narração pronta ainda não está integrada ao pipeline.")
        motor = obter_orquestrador()
        if not motor.tts.disponivel():
            raise RuntimeError("Motor de narração configurado não está disponível.")
        idioma, pasta_idioma = _audio_idioma(ctx.projeto)
        pasta_idioma.mkdir(parents=True, exist_ok=True)
        (pasta_idioma / "palavras.json").unlink(missing_ok=True)
        (pasta_idioma / "qualidade.json").unlink(missing_ok=True)
        relatorio = await asyncio.to_thread(
            motor.processar_projeto_completo,
            segmentos=_segmentos_projeto(ctx.projeto),
            pasta_audio=ctx.projeto.pastas.audio,
            idioma=idioma,
            voz=opcoes.get("voz"),
            executar_alinhamento=False,
            gerar_timestamps_estimados=False,
        )
        if not relatorio.arquivo_completo_wav.is_file() or relatorio.duracao_total_s <= 0:
            raise RuntimeError("A narração não produziu um WAV válido.")
        if not relatorio.arquivo_segmentos_json.is_file():
            raise RuntimeError("A narração não produziu os tempos dos segmentos.")
        if (ctx.projeto.pastas.plano / "shots.json").is_file() and estrategia_valida(ctx):
            gerar_shots(ctx)
            if (ctx.projeto.pastas.plano / "ativos.json").is_file():
                consolidar_ativos(ctx)

    def alinhar_narracao_sync(ctx: ContextoEtapa) -> None:
        motor = obter_orquestrador()
        modelo_asr = getattr(motor.alinhador, "modelo", None)
        if not motor.alinhador.disponivel():
            raise RuntimeError("WhisperX configurado não está disponível.")
        idioma, pasta_idioma = _audio_idioma(ctx.projeto)
        narracao_wav = pasta_idioma / "narracao_completa.wav"
        segmentos_json = pasta_idioma / "segmentos.json"
        palavras_json = pasta_idioma / "palavras.json"
        qualidade_json = pasta_idioma / "qualidade.json"
        if not narracao_wav.is_file() or not segmentos_json.is_file():
            raise FileNotFoundError("Narração ou tempos dos segmentos ausentes para alinhamento.")
        palavras_json.unlink(missing_ok=True)
        qualidade_json.unlink(missing_ok=True)

        segmentos = _segmentos_projeto(ctx.projeto)
        segmentos_info = json.loads(segmentos_json.read_text(encoding="utf-8"))
        if {item["id"] for item in segmentos_info} != {item.id for item in segmentos}:
            raise ValueError("Os IDs da narração não correspondem ao roteiro atual.")
        idioma_whisper = idioma.split("-")[0].lower()
        asr_palavras = pasta_idioma / "asr_palavras_temp.json"
        asr_segmentos = pasta_idioma / "asr_segmentos_temp.json"
        try:
            motor.alinhador.alinhar(
                audio_wav=narracao_wav,
                saida_palavras=asr_palavras,
                saida_segmentos=asr_segmentos,
                idioma=idioma_whisper,
            )
            transcricao = json.loads(asr_segmentos.read_text(encoding="utf-8"))
        finally:
            asr_palavras.unlink(missing_ok=True)
            asr_segmentos.unlink(missing_ok=True)

        referencia = " ".join(item.texto_limpo for item in segmentos)
        hipotese = " ".join(item.get("texto", "") for item in transcricao)
        wer_bruto_primeira_passagem = calcular_wer(referencia, hipotese)
        wer = calcular_wer(referencia, hipotese, idioma=idioma)
        limite_wer = 0.02
        resultados = [
            ResultadoSegmentoAudio(
                id=item["id"],
                texto=item["texto"],
                arquivo_wav=_localizar_audio_segmento(pasta_idioma / "segmentos", str(item["id"])),
                duracao_s=float(item["fim_s"]) - float(item["inicio_s"]),
            )
            for item in segmentos_info
        ]
        motor._atualizar_wer_segmentos(
            resultados, segmentos_info, transcricao, idioma=idioma
        )
        wer_segmentos_primeira_passagem = {item.id: item.wer for item in resultados}
        if wer > limite_wer:
            # A rotina existente refaz os trechos reprovados uma vez.
            relatorio = motor.processar_projeto_completo(
                segmentos=segmentos,
                pasta_audio=ctx.projeto.pastas.audio,
                idioma=idioma,
                voz=ctx.projeto.obter_opcoes().get("voz"),
                executar_alinhamento=True,
                limite_wer=limite_wer,
                resultados_iniciais=resultados,
            )
            wer = relatorio.wer_medio if relatorio.wer_medio is not None else 1.0
        else:
            motor.alinhador.alinhar(
                audio_wav=narracao_wav,
                saida_palavras=palavras_json,
                saida_segmentos=segmentos_json,
                segmentos_info=segmentos_info,
                idioma=idioma_whisper,
            )

        if wer > limite_wer:
            atomic_write_json(
                qualidade_json,
                {
                    "origem": "whisperx",
                    "modelo_asr": modelo_asr,
                    "status": "reprovado",
                    "wer": wer,
                    "wer_bruto_primeira_passagem": wer_bruto_primeira_passagem,
                    "wer_segmentos_primeira_passagem": wer_segmentos_primeira_passagem,
                    "limite_wer": limite_wer,
                    "transcricao_primeira_passagem": hipotese,
                },
            )
            raise RuntimeError(f"WER da narração acima do limite: {wer:.2%} > {limite_wer:.2%}.")
        if not palavras_json.is_file() or not segmentos_json.is_file():
            raise RuntimeError("WhisperX não produziu os arquivos de alinhamento.")
        palavras = json.loads(palavras_json.read_text(encoding="utf-8"))
        ids_com_palavras = {item.get("segmento_id") for item in palavras}
        ids_esperados = {item.id for item in segmentos if item.texto_limpo.split()}
        if not palavras or ids_com_palavras != ids_esperados:
            raise RuntimeError("WhisperX não alinhou palavras de todos os segmentos.")
        atomic_write_json(
            qualidade_json,
            {
                "origem": "whisperx",
                "modelo_asr": modelo_asr,
                "status": "aprovado",
                "wer": wer,
                "wer_bruto_primeira_passagem": wer_bruto_primeira_passagem,
                "wer_segmentos_primeira_passagem": wer_segmentos_primeira_passagem,
                "limite_wer": limite_wer,
            },
        )

    async def alinhar_narracao(ctx: ContextoEtapa) -> None:
        await asyncio.to_thread(alinhar_narracao_sync, ctx)

    def leitura_valida(ctx: ContextoEtapa) -> bool:
        caminho = ctx.projeto.pastas.plano / "leitura.json"
        return caminho.is_file() and json.loads(caminho.read_text(encoding="utf-8")).get(
            "total_segmentos", 0
        ) > 0

    def estrategia_valida(ctx: ContextoEtapa) -> bool:
        caminho = ctx.projeto.pastas.plano / "estrategia.json"
        if not caminho.is_file():
            return False
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        ids = [item.get("bloco_id") for item in dados.get("blocos", [])]
        esperados = [bloco.id for bloco in ler_roteiro_formatado(ctx.projeto.obter_roteiro())]
        return dados.get("versao") == 1 and bool(ids) and ids == esperados

    def shots_validos(ctx: ContextoEtapa) -> bool:
        caminho = ctx.projeto.pastas.plano / "shots.json"
        if not caminho.is_file():
            return False
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        blocos = ler_roteiro_formatado(ctx.projeto.obter_roteiro())
        saidas = dados.get("blocos", [])
        if dados.get("versao") != 1 or len(saidas) != len(blocos):
            return False

        _, pasta_audio = _audio_idioma(ctx.projeto)
        if (
            (pasta_audio / "segmentos.json").is_file()
            and narracao_valida(ctx)
            and dados.get("tempos") != "reais"
        ):
            return False

        ids_shots: set[str] = set()
        verificador_d1 = VerificadorDosagem()
        for bloco, saida in zip(blocos, saidas, strict=True):
            if saida.get("bloco_id") != bloco.id:
                return False
            shots = [Shot.model_validate(item) for item in saida.get("shots", [])]
            if not shots or any(
                shot.template not in TEMPLATES_CATALOGO or shot.duracao_s <= 0
                for shot in shots
            ):
                return False
            if segmentos_em_ordem(shots) != [
                segmento.id for segmento in bloco.segmentos
            ]:
                return False
            if dados.get("tempos") == "reais":
                intensidades = {seg.id: int(seg.intensidade or 5) for seg in bloco.segmentos}
                if any(
                    shot.segmentos
                    and shot.duracao_s > verificador_d1.limites_d1(
                        intensidades[shot.segmentos[0]]
                    )[1] + 0.05
                    for shot in shots
                ):
                    return False
                audio_bloco = [
                    item for item in json.loads(
                        (pasta_audio / "segmentos.json").read_text(encoding="utf-8")
                    ) if item["id"] in {seg.id for seg in bloco.segmentos}
                ]
                try:
                    intervalos_narrados(shots, audio_bloco)
                except ValueError:
                    return False
            for shot in shots:
                if shot.id in ids_shots:
                    return False
                ids_shots.add(shot.id)
        return True

    def ativos_validos(ctx: ContextoEtapa) -> bool:
        caminho = ctx.projeto.pastas.plano / "ativos.json"
        if not caminho.is_file():
            return False
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        if dados.get("versao") != 1 or not isinstance(dados.get("ativos"), dict):
            return False
        blocos = blocos_com_shots(ctx)
        esperados = consolidar_ativos_plano(
            blocos, preset=ctx.projeto.obter_opcoes().get("preset", "padrao")
        )
        try:
            ativos = {
                aid: Ativo.model_validate(item)
                for aid, item in dados["ativos"].items()
            }
        except (TypeError, ValueError):
            return False
        return {aid: item.model_dump(mode="json") for aid, item in ativos.items()} == {
            aid: item.model_dump(mode="json") for aid, item in esperados.items()
        }

    def hashes_entradas_p6(ctx: ContextoEtapa) -> dict[str, str]:
        _, pasta_audio = _audio_idioma(ctx.projeto)
        caminhos = {
            "estrategia": ctx.projeto.pastas.plano / "estrategia.json",
            "shots": ctx.projeto.pastas.plano / "shots.json",
            "ativos": ctx.projeto.pastas.plano / "ativos.json",
            "qualidade": pasta_audio / "qualidade.json",
            "palavras": pasta_audio / "palavras.json",
            "segmentos": pasta_audio / "segmentos.json",
        }
        return {nome: calcular_hash_dados(caminho) for nome, caminho in caminhos.items()}

    def dosagem_valida(ctx: ContextoEtapa) -> bool:
        pasta = ctx.projeto.pastas.plano
        if not (pasta / "plano_verificado.json").is_file() or not (
            pasta / "verificacao.json"
        ).is_file():
            return False
        if not alinhamento_valido(ctx) or not estrategia_valida(ctx) or not ativos_validos(ctx):
            return False
        plano_dados = json.loads((pasta / "plano_verificado.json").read_text(encoding="utf-8"))
        plano = Plano.model_validate(plano_dados)
        relatorio = json.loads((pasta / "verificacao.json").read_text(encoding="utf-8"))
        nomes_relatorios = [
            "plano.json",
            "plano.md",
            "verificacao.md",
            "estimativa.md",
            "numeros_na_tela.md",
        ]
        if any(not (pasta / nome).is_file() for nome in nomes_relatorios):
            return False
        segmentos_esperados = [
            segmento.id
            for bloco in ler_roteiro_formatado(ctx.projeto.obter_roteiro())
            for segmento in bloco.segmentos
        ]
        todos_shots = [shot for bloco in plano.blocos for shot in bloco.shots]
        segmentos_cobertos = segmentos_em_ordem(todos_shots)
        _, pasta_audio = _audio_idioma(ctx.projeto)
        duracoes_audio = {
            item["id"]: float(item["fim_s"]) - float(item["inicio_s"])
            for item in json.loads(
                (pasta_audio / "segmentos.json").read_text(encoding="utf-8")
            )
        }
        try:
            intervalos_narrados(
                todos_shots,
                [{"id": sid, "inicio_s": 0.0, "fim_s": duracao}
                 for sid, duracao in duracoes_audio.items()],
            )
            tempos_conferem = True
        except ValueError:
            tempos_conferem = False
        meta_previa = pasta / "previa.json"
        hashes_relatorios = {
            nome: calcular_hash_dados(pasta / nome) for nome in nomes_relatorios
        }
        if meta_previa.is_file():
            dados_previa = json.loads(meta_previa.read_text(encoding="utf-8"))
            relatorios_previa_validos = (
                dados_previa.get("hash_verificacao")
                == calcular_hash_dados(pasta / "verificacao.json")
                and all(
                    dados_previa.get("hash_saidas", {}).get(nome) == hashes_relatorios[nome]
                    for nome in ["plano.json", "plano.md", "estimativa.md"]
                )
                and all(
                    relatorio.get("hash_relatorios", {}).get(nome) == hashes_relatorios[nome]
                    for nome in ["verificacao.md", "numeros_na_tela.md"]
                )
            )
            # Uma prévia antiga pode permanecer no disco após refazer P6.
            # Nesse intervalo, os relatórios recém-gerados de P6 são a fonte válida.
            relatorios_validos = relatorios_previa_validos or (
                relatorio.get("hash_relatorios") == hashes_relatorios
            )
        else:
            relatorios_validos = relatorio.get("hash_relatorios") == hashes_relatorios
        return (
            plano.projeto == ctx.projeto.slug
            and segmentos_cobertos == segmentos_esperados
            and tempos_conferem
            and relatorio.get("hash_plano") == calcular_hash_dados(plano_dados)
            and relatorio.get("hash_entradas") == hashes_entradas_p6(ctx)
            and relatorios_validos
            and plano.verificacao.get("fase") == "pre_resolucao_ativos"
            and plano.verificacao.get("aprovado") is True
            and relatorio.get("aprovado") is True
            and plano.verificacao.get("total_violacoes") == relatorio.get("total_violacoes")
            and plano.verificacao.get("ajustes") == len(relatorio.get("ajustes", []))
        )

    def narracao_valida(ctx: ContextoEtapa) -> bool:
        _, pasta = _audio_idioma(ctx.projeto)
        wav = pasta / "narracao_completa.wav"
        segmentos_path = pasta / "segmentos.json"
        if not wav.is_file() or wav.stat().st_size <= 44 or not segmentos_path.is_file():
            return False
        segmentos = json.loads(segmentos_path.read_text(encoding="utf-8"))
        return bool(segmentos) and {item["id"] for item in segmentos} == {
            item.id for item in _segmentos_projeto(ctx.projeto)
        }

    def alinhamento_valido(ctx: ContextoEtapa) -> bool:
        _, pasta = _audio_idioma(ctx.projeto)
        qualidade_path = pasta / "qualidade.json"
        palavras_path = pasta / "palavras.json"
        if not qualidade_path.is_file() or not palavras_path.is_file():
            return False
        qualidade = json.loads(qualidade_path.read_text(encoding="utf-8"))
        palavras = json.loads(palavras_path.read_text(encoding="utf-8"))
        ids_esperados = {
            item.id for item in _segmentos_projeto(ctx.projeto) if item.texto_limpo.split()
        }
        modelo_asr = getattr(obter_orquestrador().alinhador, "modelo", None)
        return (
            qualidade.get("origem") == "whisperx"
            and qualidade.get("modelo_asr") == modelo_asr
            and qualidade.get("status") == "aprovado"
            and isinstance(qualidade.get("wer"), (float, int))
            and qualidade["wer"] <= qualidade.get("limite_wer", 0.02)
            and bool(palavras)
            and {item.get("segmento_id") for item in palavras} == ids_esperados
        )

    def resolucao_valida(ctx: ContextoEtapa) -> bool:
        pasta_plano = ctx.projeto.pastas.plano
        arquivo_resolvidos = pasta_plano / "ativos_resolvidos.json"
        arquivo_lista_busca = pasta_plano / "lista_de_busca.md"
        arquivo_escolhas = ctx.projeto.pastas.midias / "escolhas.json"
        if (
            not arquivo_resolvidos.is_file()
            or not arquivo_lista_busca.is_file()
            or not arquivo_escolhas.is_file()
        ):
            return False
        try:
            dados = json.loads(arquivo_resolvidos.read_text(encoding="utf-8"))
            valido = (
                bool(dados.get("ativos"))
                and dados.get("total_ativos") == len(dados["ativos"])
            )
            plano_verificado = pasta_plano / "plano_verificado.json"
            if plano_verificado.is_file():
                verificado = json.loads(plano_verificado.read_text(encoding="utf-8"))
                valido = valido and set(dados["ativos"]) == set(verificado["ativos"])
            return valido
        except Exception:
            return False

    def previa_valida(ctx: ContextoEtapa) -> bool:
        pasta = ctx.projeto.pastas.plano
        meta_path = pasta / "previa.json"
        if not meta_path.is_file() or not resolucao_valida(ctx):
            return False
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            _, pasta_audio = _audio_idioma(ctx.projeto)
            return (
                meta.get("fase") == "planejamento_completo"
                and meta.get("hash_verificacao")
                == calcular_hash_dados(pasta / "verificacao.json")
                and meta.get("hash_resolvidos")
                == calcular_hash_dados(pasta / "ativos_resolvidos.json")
                and meta.get("hash_audio")
                == calcular_hash_dados(pasta_audio / "narracao_completa.wav")
                and meta.get("hash_segmentos")
                == calcular_hash_dados(pasta_audio / "segmentos.json")
                and meta.get("hash_saidas")
                == {
                    nome: calcular_hash_dados(pasta / nome)
                    for nome in ["previa.mp4", "plano.json", "plano.md", "estimativa.md"]
                }
            )
        except (OSError, ValueError, KeyError):
            return False

    executor.registrar_handler("E00_entrada", validar_entrada)
    executor.registrar_handler("P1_leitura", ler_roteiro, validador=leitura_valida)
    executor.registrar_handler("P3_estrategia", planejar_estrategia, validador=estrategia_valida)
    executor.registrar_handler("P4_shots", gerar_shots, validador=shots_validos)
    executor.registrar_handler("P5_ativos", consolidar_ativos, validador=ativos_validos)
    executor.registrar_handler("P6_verificador", verificar_dosagem, validador=dosagem_valida)
    executor.registrar_handler("P7_resolucao", resolver_ativos, validador=resolucao_valida)
    executor.registrar_handler(
        "P8_estimativa_previa", estimar_e_renderizar_previa, validador=previa_valida
    )
    executor.registrar_handler("P2_narracao", gerar_narracao, validador=narracao_valida)
    executor.registrar_handler("P2b_alinhamento", alinhar_narracao, validador=alinhamento_valido)
    return executor


def criar_executor_projeto(projeto: Projeto) -> ExecutorPipeline:
    """Cria um executor com o mesmo conjunto explícito de handlers em toda a app."""
    return registrar_handlers_disponiveis(ExecutorPipeline(projeto))
