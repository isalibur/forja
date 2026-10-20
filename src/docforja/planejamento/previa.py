"""P8: manifesto sincronizado ao áudio e prévia de planejamento em 540p."""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import wave
from itertools import pairwise
from pathlib import Path

from docforja.esquemas import Ativo, Plano
from docforja.io import atomic_write_json, atomic_write_text
from docforja.nucleo.etapas import calcular_hash_dados
from docforja.nucleo.projeto import Projeto
from docforja.planejamento.dosagem import VerificadorDosagem
from docforja.planejamento.estimativa import estimar_tempo_plano
from docforja.planejamento.leitura import ler_roteiro_formatado
from docforja.planejamento.relatorios import gerar_estimativa_md, gerar_plano_md
from docforja.planejamento.tempos import intervalos_narrados

FPS_PREVIA = 24
KIT_REMOTION = Path(__file__).resolve().parents[3] / "kits" / "cinza-e-brasa"


def _duracao_wav(caminho: Path) -> float:
    with wave.open(str(caminho), "rb") as arquivo:
        return arquivo.getnframes() / arquivo.getframerate()


def montar_manifesto_previa(
    plano: Plano, segmentos_audio: list[dict], ativos_resolvidos: dict[str, Ativo]
) -> dict:
    """Usa os intervalos reais; cartões sem segmento aparecem sobre a narração."""
    if not segmentos_audio:
        raise ValueError("Tempos reais da narração ausentes.")
    intervalos = intervalos_narrados(
        (shot for bloco in plano.blocos for shot in bloco.shots), segmentos_audio
    )
    if abs(float(segmentos_audio[0]["inicio_s"])) > 0.05:
        raise ValueError("A narração não começa em zero.")
    for anterior, atual in pairwise(segmentos_audio):
        if abs(float(anterior["fim_s"]) - float(atual["inicio_s"])) > 0.05:
            raise ValueError("Há lacuna ou sobreposição nos segmentos de áudio.")

    shots: list[dict] = []
    cartoes: list[dict] = []
    for bloco in plano.blocos:
        for indice, shot in enumerate(bloco.shots):
            ativo = ativos_resolvidos.get(shot.ativos[0]) if shot.ativos else None
            descricao = ativo.descricao if ativo else ""
            situacao = (
                "ATIVO LOCALIZADO" if ativo and ativo.caminho and ativo.caminho.is_file()
                else "ATIVO PENDENTE" if ativo else "SEM IMAGEM"
            )
            texto = " · ".join(shot.textos) or str(shot.params.get("texto", ""))
            if shot.segmentos:
                inicio, fim = intervalos[shot.id]
            else:
                proximo = next(
                    (s for s in bloco.shots[indice + 1 :] if s.segmentos), None
                )
                if proximo:
                    inicio = intervalos[proximo.id][0]
                    fim = min(inicio + shot.duracao_s, intervalos[proximo.id][1])
                else:
                    ultimo = segmentos_audio[-1]
                    fim = float(ultimo["fim_s"])
                    inicio = max(float(ultimo["inicio_s"]), fim - shot.duracao_s)
            item = {
                "id": shot.id,
                "template": shot.template,
                "inicio_frame": round(inicio * FPS_PREVIA),
                "fim_frame": max(round(inicio * FPS_PREVIA) + 1, round(fim * FPS_PREVIA)),
                "bloco": bloco.titulo,
                "descricao": descricao,
                "texto": texto or (bloco.titulo if not shot.segmentos else ""),
                "situacao": situacao,
            }
            (shots if shot.segmentos else cartoes).append(item)
    duracao_frames = math.ceil(float(segmentos_audio[-1]["fim_s"]) * FPS_PREVIA)
    if shots:
        shots[-1]["fim_frame"] = duracao_frames
    if shots[0]["inicio_frame"] != 0 or shots[-1]["fim_frame"] != duracao_frames:
        raise ValueError("A prévia não cobre os extremos da narração.")
    if any(a["fim_frame"] != b["inicio_frame"] for a, b in pairwise(shots)):
        raise ValueError("Há lacuna ou sobreposição na linha do tempo da prévia.")
    return {
        "titulo": plano.projeto,
        "shots": shots,
        "cartoes": cartoes,
        "duracao_frames": duracao_frames,
    }


def renderizar_previa(projeto: Projeto) -> dict:
    """Atualiza os relatórios finais e renderiza um animatic, sem usar mídia sem licença."""
    pasta = projeto.pastas.plano
    idioma = projeto.obter_opcoes().get("idiomas", {}).get("principal", "pt-BR")
    wav = projeto.pastas.audio / idioma / "narracao_completa.wav"
    segmentos_path = projeto.pastas.audio / idioma / "segmentos.json"
    segmentos = json.loads(segmentos_path.read_text(encoding="utf-8"))
    plano = Plano.model_validate_json((pasta / "plano_verificado.json").read_text(encoding="utf-8"))
    resolvidos = json.loads((pasta / "ativos_resolvidos.json").read_text(encoding="utf-8"))
    ativos = {aid: Ativo.model_validate(a) for aid, a in resolvidos["ativos"].items()}
    if set(ativos) != set(plano.ativos):
        raise ValueError("Os ativos resolvidos não correspondem aos do plano verificado.")
    manifesto = montar_manifesto_previa(plano, segmentos, ativos)
    duracao_real = _duracao_wav(wav)
    if abs(duracao_real - manifesto["duracao_frames"] / FPS_PREVIA) > 0.1:
        raise ValueError("A duração do WAV diverge dos tempos dos segmentos.")

    duracao_plano_original = sum(
        shot.duracao_s for bloco in plano.blocos for shot in bloco.shots
    )
    plano.ativos = ativos
    intervalos = {
        item["id"]: item for item in [*manifesto["shots"], *manifesto["cartoes"]]
    }
    for bloco in plano.blocos:
        for shot in bloco.shots:
            item = intervalos[shot.id]
            shot.inicio_s = item["inicio_frame"] / FPS_PREVIA
            shot.fim_s = item["fim_frame"] / FPS_PREVIA
            shot.duracao_s = round(shot.fim_s - shot.inicio_s, 3)
    preset = projeto.obter_opcoes().get("preset", "padrao")
    config_preset = VerificadorDosagem().config.get("presets", {}).get(preset)
    if config_preset is None:
        raise ValueError(f"Preset desconhecido: {preset}")
    variacoes = int(config_preset["variacoes_imagem"])
    estimativa = estimar_tempo_plano(
        plano, variacoes_imagem=variacoes, duracao_audio_s=duracao_real
    )
    if not estimativa.aprovado and variacoes > 1:
        reduzida = estimar_tempo_plano(
            plano, variacoes_imagem=1, duracao_audio_s=duracao_real
        )
        if reduzida.aprovado:
            estimativa = reduzida
            estimativa.ajustes_realizados.append(
                "Reduzir variações de imagens geradas para 1 no render final."
            )
    if not estimativa.aprovado:
        raise RuntimeError("A estimativa excede o orçamento do preset; revisar o plano.")
    plano.estimativa_producao_min = math.ceil(estimativa.tempo_total_minutos)

    staging = projeto.pastas.sistema / "previa"
    public = staging / "public"
    public.mkdir(parents=True, exist_ok=True)
    audio_publico = public / "narracao.wav"
    if not audio_publico.is_file() or (
        calcular_hash_dados(audio_publico) != calcular_hash_dados(wav)
    ):
        temporario_audio = public / "narracao.novo.wav"
        shutil.copyfile(wav, temporario_audio)
        os.replace(temporario_audio, audio_publico)
    props = staging / "props.json"
    atomic_write_json(props, manifesto)
    saida_temporaria = staging / "previa.nova.mp4"
    if saida_temporaria.exists():
        saida_temporaria.unlink()
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if npm is None:
        raise RuntimeError("Node/npm não está disponível para renderizar a prévia.")
    comando = [
        npm, "exec", "--offline", "--", "remotion", "render", "src/index.ts",
        "Previa-Plano-540p", str(saida_temporaria),
        f"--props={props}", f"--public-dir={public}", "--concurrency=2", "--log=error",
    ]
    resultado = subprocess.run(
        comando, cwd=KIT_REMOTION, capture_output=True, text=True, timeout=3600, check=False
    )
    if resultado.returncode != 0 or not saida_temporaria.is_file():
        raise RuntimeError(f"Falha ao renderizar prévia: {resultado.stderr[-1200:]}")

    destino = pasta / "previa.mp4"
    if destino.exists():
        base = calcular_hash_dados(destino)[:12]
        versao = pasta / f"previa.{base}.mp4"
        if versao.exists():
            versao = pasta / f"previa.{base}.{destino.stat().st_mtime_ns}.mp4"
        os.replace(destino, versao)
    os.replace(saida_temporaria, destino)
    blocos_proc = ler_roteiro_formatado(projeto.obter_roteiro())
    atomic_write_json(pasta / "plano.json", plano.model_dump(mode="json"))
    aviso_previa = (
        "> Prévia de planejamento: imagens são placeholders identificados; "
        "não representam arquivos finais nem autorização de uso. "
        "A narração está sincronizada ao WAV real; trilha provisória ainda não incluída.\n\n"
    )
    atomic_write_text(
        pasta / "plano.md", aviso_previa + gerar_plano_md(plano, blocos_proc)
    )
    atomic_write_text(pasta / "estimativa.md", gerar_estimativa_md(estimativa))
    meta = {
        "versao": 1,
        "fase": "planejamento_completo",
        "hash_verificacao": calcular_hash_dados(pasta / "verificacao.json"),
        "hash_resolvidos": calcular_hash_dados(pasta / "ativos_resolvidos.json"),
        "hash_audio": calcular_hash_dados(wav),
        "hash_segmentos": calcular_hash_dados(segmentos_path),
        "hash_saidas": {
            nome: calcular_hash_dados(pasta / nome)
            for nome in ["previa.mp4", "plano.json", "plano.md", "estimativa.md"]
        },
        "duracao_s": round(duracao_real, 3),
        "duracao_plano_original_s": round(duracao_plano_original, 3),
    }
    atomic_write_json(pasta / "previa.json", meta)
    return meta


def reconciliar_relatorios_previa(projeto: Projeto) -> dict:
    """Atualiza relatórios de uma prévia íntegra sem codificar o MP4 novamente."""
    pasta = projeto.pastas.plano
    meta_path = pasta / "previa.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    idioma = projeto.obter_opcoes().get("idiomas", {}).get("principal", "pt-BR")
    audio = projeto.pastas.audio / idioma
    entradas = {
        "hash_verificacao": pasta / "verificacao.json",
        "hash_resolvidos": pasta / "ativos_resolvidos.json",
        "hash_audio": audio / "narracao_completa.wav",
        "hash_segmentos": audio / "segmentos.json",
    }
    if any(meta.get(chave) != calcular_hash_dados(caminho) for chave, caminho in entradas.items()):
        raise ValueError("As entradas mudaram; a prévia precisa ser renderizada novamente.")
    video = pasta / "previa.mp4"
    if meta.get("hash_saidas", {}).get("previa.mp4") != calcular_hash_dados(video):
        raise ValueError("O MP4 mudou; não é seguro reconciliar os relatórios.")
    manifesto_path = projeto.pastas.sistema / "previa" / "props.json"
    manifesto = json.loads(manifesto_path.read_text(encoding="utf-8"))
    verificado = Plano.model_validate_json(
        (pasta / "plano_verificado.json").read_text(encoding="utf-8")
    )
    segmentos = json.loads((audio / "segmentos.json").read_text(encoding="utf-8"))
    resolvidos = json.loads((pasta / "ativos_resolvidos.json").read_text(encoding="utf-8"))
    ativos = {aid: Ativo.model_validate(a) for aid, a in resolvidos["ativos"].items()}
    if manifesto != montar_manifesto_previa(verificado, segmentos, ativos):
        raise ValueError("O manifesto não corresponde ao plano e ao áudio verificados.")
    plano = Plano.model_validate_json((pasta / "plano.json").read_text(encoding="utf-8"))
    intervalos = {item["id"]: item for item in [*manifesto["shots"], *manifesto["cartoes"]]}
    for bloco in plano.blocos:
        for shot in bloco.shots:
            item = intervalos[shot.id]
            shot.inicio_s = item["inicio_frame"] / FPS_PREVIA
            shot.fim_s = item["fim_frame"] / FPS_PREVIA
            shot.duracao_s = round(shot.fim_s - shot.inicio_s, 3)
    aviso = (
        "> Prévia de planejamento: imagens são placeholders identificados; "
        "não representam arquivos finais nem autorização de uso. "
        "A narração está sincronizada ao WAV real; trilha provisória ainda não incluída.\n\n"
    )
    atomic_write_json(pasta / "plano.json", plano.model_dump(mode="json"))
    atomic_write_text(
        pasta / "plano.md",
        aviso + gerar_plano_md(plano, ler_roteiro_formatado(projeto.obter_roteiro())),
    )
    meta["hash_saidas"] = {
        nome: calcular_hash_dados(pasta / nome)
        for nome in ["previa.mp4", "plano.json", "plano.md", "estimativa.md"]
    }
    atomic_write_json(meta_path, meta)
    return meta
