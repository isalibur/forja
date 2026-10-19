"""Handlers reais atualmente disponíveis para execução de projetos."""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from pathlib import Path

from docforja.audio.adaptadores.kokoro import AdaptadorKokoro
from docforja.audio.alinhamento import AlinhadorWhisperX
from docforja.audio.metricas import calcular_wer
from docforja.audio.narracao import OrquestradorNarracao, ResultadoSegmentoAudio
from docforja.esquemas import Ativo, Bloco, Plano, Shot
from docforja.io import atomic_write_json
from docforja.nucleo.etapas import calcular_hash_dados
from docforja.nucleo.executor import ContextoEtapa, ExecutorPipeline
from docforja.nucleo.projeto import Projeto
from docforja.planejamento.ativos import consolidar_ativos_plano
from docforja.planejamento.dosagem import VerificadorDosagem
from docforja.planejamento.entidades import SegmentoProcessado
from docforja.planejamento.estrategia import EstrategiaBloco, planejar_estrategias
from docforja.planejamento.leitura import ler_roteiro_formatado
from docforja.planejamento.shots import TEMPLATES_CATALOGO, gerar_shots_bloco
from docforja.settings import load_settings


def _criar_orquestrador() -> OrquestradorNarracao:
    ambientes = load_settings().python_environments
    kokoro = AdaptadorKokoro(python_path=ambientes.get("kokoro"))
    whisperx = AlinhadorWhisperX(python_path=ambientes.get("whisperx"))
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


def registrar_handlers_disponiveis(
    executor: ExecutorPipeline,
    orquestrador: OrquestradorNarracao | None = None,
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
        ativo_counter = [1]
        saidas = []
        for bloco, estrategia in zip(blocos, estrategias, strict=True):
            shots = gerar_shots_bloco(
                bloco,
                estrategia,
                total_blocos=len(blocos),
                ativo_counter=ativo_counter,
            )
            ids_roteiro = [segmento.id for segmento in bloco.segmentos]
            ids_cobertos = [sid for shot in shots for sid in shot.segmentos]
            if ids_cobertos != ids_roteiro:
                raise ValueError(f"Shots do bloco {bloco.id} não cobrem o roteiro exatamente.")
            saidas.append({"bloco_id": bloco.id, "shots": [shot.model_dump() for shot in shots]})
        atomic_write_json(
            ctx.projeto.pastas.plano / "shots.json",
            {"versao": 1, "tempos": "estimados", "blocos": saidas},
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
        if not estrategia_valida(ctx) or not ativos_validos(ctx):
            raise ValueError("Estratégia, shots ou ativos ausentes/inválidos para verificação.")

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
        resultado = verificador.verificar_e_corrigir(
            plano, blocos_processados=ler_roteiro_formatado(ctx.projeto.obter_roteiro())
        )
        plano_dados = plano.model_dump(mode="json")
        relatorio_dados = asdict(resultado)
        relatorio_dados["hash_plano"] = calcular_hash_dados(plano_dados)
        relatorio_dados["hash_entradas"] = hashes_entradas_p6(ctx)
        atomic_write_json(pasta / "plano_verificado.json", plano_dados)
        atomic_write_json(pasta / "verificacao.json", relatorio_dados)
        if not resultado.aprovado:
            raise RuntimeError("Plano reprovado pela verificação de dosagem D1-D17.")

    def obter_orquestrador() -> OrquestradorNarracao:
        nonlocal orquestrador
        if orquestrador is None:
            orquestrador = _criar_orquestrador()
        return orquestrador

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

    def alinhar_narracao_sync(ctx: ContextoEtapa) -> None:
        motor = obter_orquestrador()
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
                arquivo_wav=pasta_idioma / "segmentos" / f"{item['id']}.wav",
                duracao_s=float(item["fim_s"]) - float(item["inicio_s"]),
            )
            for item in segmentos_info
        ]
        motor._atualizar_wer_segmentos(
            resultados, segmentos_info, transcricao, idioma=idioma
        )
        segmentos_reprovados = any(
            item.wer is not None and item.wer > limite_wer for item in resultados
        )
        if wer > limite_wer or segmentos_reprovados:
            # A rotina existente refaz os trechos reprovados uma vez.
            relatorio = motor.processar_projeto_completo(
                segmentos=segmentos,
                pasta_audio=ctx.projeto.pastas.audio,
                idioma=idioma,
                voz=ctx.projeto.obter_opcoes().get("voz"),
                executar_alinhamento=True,
                limite_wer=limite_wer,
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
                    "status": "reprovado",
                    "wer": wer,
                    "wer_bruto_primeira_passagem": wer_bruto_primeira_passagem,
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
                "status": "aprovado",
                "wer": wer,
                "wer_bruto_primeira_passagem": wer_bruto_primeira_passagem,
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
        ids_shots: set[str] = set()
        for bloco, saida in zip(blocos, saidas, strict=True):
            if saida.get("bloco_id") != bloco.id:
                return False
            shots = [Shot.model_validate(item) for item in saida.get("shots", [])]
            if not shots or any(
                shot.template not in TEMPLATES_CATALOGO or shot.duracao_s <= 0
                for shot in shots
            ):
                return False
            if [sid for shot in shots for sid in shot.segmentos] != [
                segmento.id for segmento in bloco.segmentos
            ]:
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
        plano = Plano.model_validate_json(
            (pasta / "plano_verificado.json").read_text(encoding="utf-8")
        )
        relatorio = json.loads((pasta / "verificacao.json").read_text(encoding="utf-8"))
        segmentos_esperados = [
            segmento.id
            for bloco in ler_roteiro_formatado(ctx.projeto.obter_roteiro())
            for segmento in bloco.segmentos
        ]
        segmentos_cobertos = [
            sid for bloco in plano.blocos for shot in bloco.shots for sid in shot.segmentos
        ]
        return (
            plano.projeto == ctx.projeto.slug
            and segmentos_cobertos == segmentos_esperados
            and relatorio.get("hash_plano") == calcular_hash_dados(plano.model_dump(mode="json"))
            and relatorio.get("hash_entradas") == hashes_entradas_p6(ctx)
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
        return (
            qualidade.get("origem") == "whisperx"
            and qualidade.get("status") == "aprovado"
            and isinstance(qualidade.get("wer"), (float, int))
            and qualidade["wer"] <= qualidade.get("limite_wer", 0.02)
            and bool(palavras)
            and {item.get("segmento_id") for item in palavras} == ids_esperados
        )

    executor.registrar_handler("E00_entrada", validar_entrada)
    executor.registrar_handler("P1_leitura", ler_roteiro, validador=leitura_valida)
    executor.registrar_handler("P3_estrategia", planejar_estrategia, validador=estrategia_valida)
    executor.registrar_handler("P4_shots", gerar_shots, validador=shots_validos)
    executor.registrar_handler("P5_ativos", consolidar_ativos, validador=ativos_validos)
    executor.registrar_handler("P6_verificador", verificar_dosagem, validador=dosagem_valida)
    executor.registrar_handler("P2_narracao", gerar_narracao, validador=narracao_valida)
    executor.registrar_handler("P2b_alinhamento", alinhar_narracao, validador=alinhamento_valido)
    return executor


def criar_executor_projeto(projeto: Projeto) -> ExecutorPipeline:
    """Cria um executor com o mesmo conjunto explícito de handlers em toda a app."""
    return registrar_handlers_disponiveis(ExecutorPipeline(projeto))
