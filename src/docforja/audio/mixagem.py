"""Mixagem final de voz e trilha com loudness medido pelo FFmpeg."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from docforja.io import atomic_write_json
from docforja.nucleo.etapas import calcular_hash_dados

GANHO_TRILHA_SOB_FALA = 0.034


class RelatorioMix(BaseModel):
    """Medições e entradas usadas para produzir uma mix final."""

    model_config = ConfigDict(extra="forbid", strict=True)

    etapa: str = "R6_mix"
    idioma: str
    alvo_lufs: float = -14.0
    medido_lufs: float
    true_peak_dbtp: float
    lra_lu: float
    ganho_trilha_sob_fala: float | None
    sidechain_ducking: str
    hash_mix: str
    hash_narracao: str
    hash_trilha: str | None
    hash_config: str
    sfx_incluidos: list[str] = Field(default_factory=list)
    observacoes: list[str] = Field(default_factory=list)


def _executar_ffmpeg(comando: list[str]) -> str:
    resultado = subprocess.run(
        comando,
        capture_output=True,
        text=True,
        timeout=1800,
        check=False,
    )
    if resultado.returncode:
        raise RuntimeError(f"FFmpeg falhou na mixagem: {resultado.stderr[-1600:]}")
    return f"{resultado.stdout}\n{resultado.stderr}"


def _extrair_loudnorm(texto: str, campo: str) -> dict[str, Any]:
    """Extrai o último objeto JSON do filtro loudnorm e valida campos numéricos."""
    objetos = re.findall(r'\{\s*"input_i".*?\}', texto, flags=re.DOTALL)
    if not objetos:
        raise ValueError("FFmpeg não retornou as medições JSON do loudnorm.")
    try:
        dados = json.loads(objetos[-1])
    except json.JSONDecodeError as exc:
        raise ValueError("Medições JSON do loudnorm são inválidas.") from exc
    campos = ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")
    try:
        medidas = {nome: float(dados[nome]) for nome in campos}
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Medição {campo} do loudnorm ausente ou não finita.") from exc
    if not all(math.isfinite(valor) for valor in medidas.values()):
        raise ValueError(f"Medição {campo} do loudnorm não é finita.")
    if campo == "saida":
        saidas = ("output_i", "output_tp", "output_lra")
        try:
            medidas.update({nome: float(dados[nome]) for nome in saidas})
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Medição final do loudnorm ausente ou não finita.") from exc
        if not all(math.isfinite(medidas[nome]) for nome in saidas):
            raise ValueError("Medição final do loudnorm não é finita.")
    return medidas


def _filtro_mixagem(com_trilha: bool = False) -> str:
    """Retorna o grafo de mixagem; a música é reduzida e ducked pela voz."""
    if com_trilha:
        return (
            f"[1:a]volume={GANHO_TRILHA_SOB_FALA}[musica];"
            "[musica][0:a]sidechaincompress=threshold=0.02:ratio=8:"
            "attack=50:release=400:makeup=1[ducked];"
            "[0:a][ducked]amix=inputs=2:duration=first:normalize=0[mix]"
        )
    return "[0:a]anull[mix]"


def _hash_config_mix(trilha: bool) -> str:
    configuracao = {
        "alvo_lufs": -14.0,
        "true_peak_dbtp": -1.0,
        "lra_alvo": 11.0,
        "ganho_trilha_sob_fala": GANHO_TRILHA_SOB_FALA if trilha else None,
        "sidechain": "threshold=0.02;ratio=8;attack=50;release=400;makeup=1" if trilha else None,
        "sample_rate": 48000,
        "bit_depth": 24,
    }
    serializado = json.dumps(configuracao, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()


def mixar_audio(
    narracao: Path,
    destino: Path,
    idioma: str,
    trilha: Path | None = None,
) -> RelatorioMix:
    """Cria mix 48 kHz/24-bit em dois passes e registra medições reais."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg não está instalado ou não está no PATH.")
    if not narracao.is_file():
        raise FileNotFoundError(f"Narração ausente para mix em {idioma}.")
    usa_trilha = bool(trilha and trilha.is_file())
    caminho_relatorio = destino.with_name("relatorio_mix.json")
    hash_narracao = calcular_hash_dados(narracao)
    hash_trilha = calcular_hash_dados(trilha) if usa_trilha and trilha else None
    if destino.is_file() and caminho_relatorio.is_file():
        try:
            cache = RelatorioMix.model_validate_json(
                caminho_relatorio.read_text(encoding="utf-8")
            )
            if (
                cache.hash_narracao == hash_narracao
                and cache.hash_trilha == hash_trilha
                and cache.hash_mix == calcular_hash_dados(destino)
                and cache.hash_config == _hash_config_mix(usa_trilha)
            ):
                return cache
        except (OSError, ValueError):
            pass
    entradas = ["-i", str(narracao)]
    if usa_trilha and trilha:
        entradas.extend(["-stream_loop", "-1", "-i", str(trilha)])

    grafo = _filtro_mixagem(usa_trilha)
    filtro_base = f"{grafo};[mix]loudnorm=I=-14:TP=-1:LRA=11:print_format=json[out]"
    primeiro_passe = [
        ffmpeg, "-hide_banner", "-nostats", "-i", str(narracao),
    ]
    if usa_trilha and trilha:
        primeiro_passe.extend(["-stream_loop", "-1", "-i", str(trilha)])
    primeiro_passe.extend([
        "-filter_complex", filtro_base, "-map", "[out]", "-f", "null", "-",
    ])
    medidas_entrada = _extrair_loudnorm(_executar_ffmpeg(primeiro_passe), "entrada")

    normalizacao = (
        "loudnorm=I=-14:TP=-1:LRA=11:linear=true:"
        f"measured_I={medidas_entrada['input_i']}:"
        f"measured_TP={medidas_entrada['input_tp']}:"
        f"measured_LRA={medidas_entrada['input_lra']}:"
        f"measured_thresh={medidas_entrada['input_thresh']}:"
        f"offset={medidas_entrada['target_offset']}:print_format=json"
    )
    grafo_saida = f"{grafo};[mix]{normalizacao}[out]"
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_name(f"{destino.stem}.tmp{destino.suffix}")
    comando_saida = [ffmpeg, "-y", "-hide_banner", "-nostats", *entradas]
    comando_saida.extend([
        "-filter_complex", grafo_saida, "-map", "[out]", "-ar", "48000", "-ac", "2",
        "-c:a", "pcm_s24le", str(temporario),
    ])
    try:
        texto_saida = _executar_ffmpeg(comando_saida)
        medidas_saida = _extrair_loudnorm(texto_saida, "saida")
        if not temporario.is_file() or temporario.stat().st_size == 0:
            raise RuntimeError("FFmpeg não criou o arquivo de mix esperado.")
        os.replace(temporario, destino)
    finally:
        temporario.unlink(missing_ok=True)

    relatorio = RelatorioMix(
        idioma=idioma,
        medido_lufs=medidas_saida["output_i"],
        true_peak_dbtp=medidas_saida["output_tp"],
        lra_lu=medidas_saida["output_lra"],
        ganho_trilha_sob_fala=GANHO_TRILHA_SOB_FALA if usa_trilha else None,
        sidechain_ducking=(
            f"ativo (ganho inicial {GANHO_TRILHA_SOB_FALA} sob fala; threshold 0.02, ratio 8:1, "
            "ataque 50 ms, release 400 ms)" if usa_trilha else "inativo (sem trilha)"
        ),
        hash_mix=calcular_hash_dados(destino),
        hash_narracao=calcular_hash_dados(narracao),
        hash_trilha=calcular_hash_dados(trilha) if usa_trilha and trilha else None,
        hash_config=_hash_config_mix(usa_trilha),
        observacoes=["SFX/ambiências não foram incluídos: não há manifesto temporal configurado."],
    )
    atomic_write_json(caminho_relatorio, relatorio.model_dump(mode="json"))
    return relatorio
