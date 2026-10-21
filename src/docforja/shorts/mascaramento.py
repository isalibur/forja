"""Medição diagnóstica da relação entre voz e música após o ducking."""

from __future__ import annotations

import math
import sys
import wave
from array import array
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class MedicaoMascaramento(BaseModel):
    """Amplitude relativa em janelas com voz; não equivale a inteligibilidade percebida."""

    model_config = ConfigDict(extra="forbid", strict=True)

    janela_ms: int
    janelas_com_voz: int = Field(ge=0)
    percentil_95_db: float | None
    pior_janela_db: float | None
    fracao_janelas_acima_menos_6_db: float | None
    possivel_mascaramento: bool | None


def _rms_pcm16(dados: bytes) -> float:
    amostras = array("h")
    amostras.frombytes(dados)
    if sys.byteorder != "little":
        amostras.byteswap()
    if not amostras:
        return 0.0
    return math.sqrt(sum(valor * valor for valor in amostras) / len(amostras))


def medir_mascaramento(
    voz: Path,
    musica_apos_ducking: Path,
    *,
    janela_ms: int = 200,
    limiar_voz_dbfs: float = -40.0,
) -> MedicaoMascaramento:
    """Sinaliza janelas em que a música chega a 6 dB da voz ou mais.

    Os dois WAVs devem representar a mesma linha do tempo em PCM16. Um alerta
    pede revisão auditiva; o resultado não aprova sozinho a regra DS9.
    """
    if janela_ms <= 0:
        raise ValueError("A janela de análise deve ser positiva.")
    diferencas: list[float] = []
    with wave.open(str(voz), "rb") as arquivo_voz, wave.open(
        str(musica_apos_ducking), "rb"
    ) as arquivo_musica:
        formatos = (
            arquivo_voz.getframerate(),
            arquivo_voz.getnchannels(),
            arquivo_voz.getsampwidth(),
        )
        if formatos != (
            arquivo_musica.getframerate(),
            arquivo_musica.getnchannels(),
            arquivo_musica.getsampwidth(),
        ) or arquivo_voz.getsampwidth() != 2:
            raise ValueError("Voz e música devem ter o mesmo formato PCM16.")
        quadros = max(1, arquivo_voz.getframerate() * janela_ms // 1000)
        limiar_rms = 32767 * 10 ** (limiar_voz_dbfs / 20)
        while True:
            voz_bytes = arquivo_voz.readframes(quadros)
            musica_bytes = arquivo_musica.readframes(quadros)
            if not voz_bytes and not musica_bytes:
                break
            if len(voz_bytes) != len(musica_bytes):
                raise ValueError("Voz e música devem cobrir a mesma duração.")
            rms_voz = _rms_pcm16(voz_bytes)
            if rms_voz < limiar_rms:
                continue
            rms_musica = _rms_pcm16(musica_bytes)
            diferencas.append(20 * math.log10(max(rms_musica, 1e-9) / rms_voz))
    if not diferencas:
        return MedicaoMascaramento(
            janela_ms=janela_ms,
            janelas_com_voz=0,
            percentil_95_db=None,
            pior_janela_db=None,
            fracao_janelas_acima_menos_6_db=None,
            possivel_mascaramento=None,
        )
    diferencas.sort()
    fracao_alerta = sum(valor > -6 for valor in diferencas) / len(diferencas)
    return MedicaoMascaramento(
        janela_ms=janela_ms,
        janelas_com_voz=len(diferencas),
        percentil_95_db=diferencas[min(len(diferencas) - 1, int(0.95 * len(diferencas)))],
        pior_janela_db=diferencas[-1],
        fracao_janelas_acima_menos_6_db=fracao_alerta,
        possivel_mascaramento=fracao_alerta > 0,
    )
