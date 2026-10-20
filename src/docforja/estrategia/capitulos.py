"""Geração e formatação de capítulos do vídeo com tempos reais (13 §4.2)."""

from __future__ import annotations

import math

from docforja.esquemas import Plano
from docforja.estrategia.modelos import Capitulo


def _formatar_timestamp(segundos: float) -> str:
    """Converte segundos em formato MM:SS ou HH:MM:SS."""
    seg = max(0, math.floor(segundos))
    horas = seg // 3600
    minutos = (seg % 3600) // 60
    segs = seg % 60
    if horas > 0:
        return f"{horas:02d}:{minutos:02d}:{segs:02d}"
    return f"{minutos:02d}:{segs:02d}"


def extrair_capitulos_plano(plano: Plano) -> list[Capitulo]:
    """Extrai os marcadores de capítulos com tempos reais a partir dos blocos do plano."""
    capitulos: list[Capitulo] = []

    for i, bloco in enumerate(plano.blocos):
        # Determina o início real do primeiro shot do bloco
        if bloco.shots and bloco.shots[0].inicio_s is not None:
            inicio_s = float(bloco.shots[0].inicio_s)
        else:
            inicio_s = 0.0 if i == 0 else (capitulos[-1].tempo_s + 60.0 if capitulos else 0.0)

        # O primeiro capítulo é obrigatoriamente 00:00 pelas regras do YouTube
        if i == 0:
            inicio_s = 0.0

        titulo_limpo = bloco.titulo.replace("##", "").strip()
        capitulos.append(
            Capitulo(
                tempo_s=round(inicio_s, 2),
                timestamp=_formatar_timestamp(inicio_s),
                titulo=titulo_limpo,
            )
        )

    # Garante que haja pelo menos 1 capítulo
    if not capitulos:
        capitulos.append(Capitulo(tempo_s=0.0, timestamp="00:00", titulo="Início"))

    return capitulos


def formatar_capitulos_txt(capitulos: list[Capitulo]) -> str:
    """Gera o arquivo capitulos.txt no padrão do YouTube (00:00 Título)."""
    linhas = [f"{c.timestamp} {c.titulo}" for c in capitulos]
    return "\n".join(linhas) + "\n"
