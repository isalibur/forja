"""Estratégia visual por bloco (Etapa P3 do planejamento).

Define modo visual dominante, color script LUT, elementos recorrentes e clima musical.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from docforja.planejamento.entidades import BlocoProcessado


@dataclass
class EstrategiaBloco:
    """Estratégia visual e sonora de um bloco."""

    bloco_id: str
    titulo: str
    modo_visual: str  # arquivo, reconstituição, dados, geografia, misto
    lut: str  # quente, tensao, brasa, arquivo, ciencia, contemporaneo
    clima_musical: str
    contexto: dict[str, Any] | None = None
    elementos_recorrentes: list[str] = field(default_factory=list)


def inferir_estrategia_bloco_heuristica(bloco: BlocoProcessado) -> EstrategiaBloco:
    """Gera estratégia visual do bloco de forma determinística/heurística."""
    titulo_limpo = bloco.nome.lower()
    bid = bloco.id.upper()

    # Mapeamento canônico para o documentário do Vesúvio quando reconhecido
    if "cold open" in titulo_limpo or "data errada" in titulo_limpo or bid == "B0":
        return EstrategiaBloco(
            bloco_id=bloco.id,
            titulo=bloco.nome,
            modo_visual="misto",
            lut="arquivo",
            clima_musical="drone escuro e pulso que cresce",
            contexto=None,
            elementos_recorrentes=["inscrição_carvao"],
        )
    if "montanha verde" in titulo_limpo or bid == "B1":
        return EstrategiaBloco(
            bloco_id=bloco.id,
            titulo=bloco.nome,
            modo_visual="reconstituição",
            lut="quente",
            clima_musical="Campania Felix, cordas quentes e harpa",
            contexto=None,
            elementos_recorrentes=[],
        )
    if "aviso" in titulo_limpo or bid == "B2":
        return EstrategiaBloco(
            bloco_id=bloco.id,
            titulo=bloco.nome,
            modo_visual="misto",
            lut="tensao",
            clima_musical="inquietação e suspense crescente",
            contexto=None,
            elementos_recorrentes=[],
        )
    if "coluna" in titulo_limpo or bid == "B3":
        return EstrategiaBloco(
            bloco_id=bloco.id,
            titulo=bloco.nome,
            modo_visual="misto",
            lut="brasa",
            clima_musical="construção épica controlada",
            contexto={
                "usar": True,
                "itens": [{"apos_segmento": f"{bid}-S01", "texto": "DIA 1 · ≈ 13:00 · POMPEIA"}],
            },
            elementos_recorrentes=["hud_relogio"],
        )
    if "herculano" in titulo_limpo or "noite" in titulo_limpo or bid == "B4":
        return EstrategiaBloco(
            bloco_id=bloco.id,
            titulo=bloco.nome,
            modo_visual="reconstituição",
            lut="brasa",
            clima_musical="horror contido e grave",
            contexto={
                "usar": True,
                "itens": [{"apos_segmento": f"{bid}-S01", "texto": "NOITE · ≈ 01:00 · HERCULANO"}],
            },
            elementos_recorrentes=["hud_relogio"],
        )
    if "fim" in titulo_limpo or bid == "B5":
        return EstrategiaBloco(
            bloco_id=bloco.id,
            titulo=bloco.nome,
            modo_visual="reconstituição",
            lut="brasa",
            clima_musical="clímax dramático e silêncio no ápice",
            contexto={
                "usar": True,
                "itens": [{"apos_segmento": f"{bid}-S01", "texto": "DIA 2 · ≈ 07:30 · POMPEIA"}],
            },
            elementos_recorrentes=["hud_relogio"],
        )
    if "esquecimento" in titulo_limpo or bid == "B6":
        return EstrategiaBloco(
            bloco_id=bloco.id,
            titulo=bloco.nome,
            modo_visual="arquivo",
            lut="arquivo",
            clima_musical="respiro melancólico",
            contexto=None,
            elementos_recorrentes=["moldes_fiorelli"],
        )
    if "nunca viu" in titulo_limpo or "ciência" in titulo_limpo or bid == "B7":
        return EstrategiaBloco(
            bloco_id=bloco.id,
            titulo=bloco.nome,
            modo_visual="dados",
            lut="ciencia",
            clima_musical="descoberta científica e revelação",
            contexto=None,
            elementos_recorrentes=["dossie_dna"],
        )
    if "hoje" in titulo_limpo or "vulcão hoje" in titulo_limpo or bid == "B8":
        return EstrategiaBloco(
            bloco_id=bloco.id,
            titulo=bloco.nome,
            modo_visual="geografia",
            lut="contemporaneo",
            clima_musical="tensão contemporânea e reflexão",
            contexto=None,
            elementos_recorrentes=["mapa_zona_vermelha"],
        )

    # Heurística genérica para outros roteiros
    texto_total = " ".join(s.texto_original for s in bloco.segmentos).lower()

    if re.search(r"\b(dna|ia|tomografia|laborat[oó]rio|pesquisa|an[aá]lise|dados)\b", texto_total):
        modo = "dados"
        lut = "ciencia"
        clima = "revelação e tecnologia"
    elif re.search(
        r"\b(s[eé]culo|escava[çc][aã]o|documento|foto|arquivo|18\d\d|19\d\d)\b", texto_total
    ):
        modo = "arquivo"
        lut = "arquivo"
        clima = "memória e história"
    elif re.search(r"\b(hoje|atualmente|habitantes|sat[eé]lite|mapa|cidade)\b", texto_total):
        modo = "geografia"
        lut = "contemporaneo"
        clima = "urgência e reflexão"
    elif bloco.intensidade_fim >= 7.0:
        modo = "misto"
        lut = "brasa"
        clima = "ação e intensidade"
    else:
        modo = "reconstituição"
        lut = "quente"
        clima = "imersão narrativa"

    return EstrategiaBloco(
        bloco_id=bloco.id,
        titulo=bloco.nome,
        modo_visual=modo,
        lut=lut,
        clima_musical=clima,
        contexto=None,
        elementos_recorrentes=[],
    )


def planejar_estrategias(blocos: list[BlocoProcessado]) -> list[EstrategiaBloco]:
    """Planeja a estratégia visual para todos os blocos do projeto."""
    return [inferir_estrategia_bloco_heuristica(b) for b in blocos]
