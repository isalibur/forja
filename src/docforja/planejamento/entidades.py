from __future__ import annotations

import re
from dataclasses import dataclass, field

from docforja.esquemas import BatidaSegmento


@dataclass
class SegmentoProcessado:
    id: str
    texto_original: str
    texto_limpo: str
    direcao_voz: str | None = None
    fatos: list[str] = field(default_factory=list)
    batida: BatidaSegmento | None = None
    intensidade: float | None = None
    visual_sugerido: str | None = None
    silencio_apos_s: float = 0.0
    pausas: list[str] = field(default_factory=list)
    entidades: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class BlocoProcessado:
    id: str
    nome: str
    intensidade_inicio: float = 5.0
    intensidade_fim: float = 5.0
    segmentos: list[SegmentoProcessado] = field(default_factory=list)


def extrair_entidades_heuristica(texto: str) -> dict[str, list[str]]:
    """Extrai entidades basicas (datas, numeros, nomes proprios) do texto por regex."""
    entidades: dict[str, list[str]] = {
        "pessoas": [],
        "lugares": [],
        "datas": [],
        "numeros": [],
    }

    # Numeros e medidas
    padrao_num = (
        r"\b(?:\d+[\.,]?\d*|\w+)\s*"
        r"(?:quilômetros|km|metros|m|graus|°C|anos|dias|horas|mil|milhões|por cento|%)\b"
    )
    nums = re.findall(padrao_num, texto, re.IGNORECASE)
    if nums:
        entidades["numeros"] = list(dict.fromkeys(nums))

    # Datas (ex: "vinte e quatro de agosto", "ano setenta e nove", "79 d.C.", "outubro")
    padrao_data = (
        r"\b(?:dezessete de outubro|vinte e quatro de agosto|ano setenta e nove|"
        r"79 d\.C\.|outubro|novembro|agosto|73 a\.C\.)\b"
    )
    datas = re.findall(padrao_data, texto, re.IGNORECASE)
    if datas:
        entidades["datas"] = list(dict.fromkeys(datas))

    # Lugares historicos comuns
    lugares_conhecidos = [
        "Pompeia",
        "Herculano",
        "Miseno",
        "Vesúvio",
        "Nápoles",
        "Estábia",
        "Campânia",
        "Roma",
        "Somma",
    ]
    for lugar in lugares_conhecidos:
        if re.search(rf"\b{lugar}\b", texto, re.IGNORECASE):
            entidades["lugares"].append(lugar)

    # Pessoas historicas comuns
    pessoas_conhecidas = [
        "Plínio, o Jovem",
        "Plínio, o Velho",
        "Plínio",
        "Rectina",
        "Espártaco",
        "Estrabão",
        "Baco",
        "Fiorelli",
    ]
    for pessoa in pessoas_conhecidas:
        if re.search(rf"\b{pessoa}\b", texto, re.IGNORECASE):
            entidades["pessoas"].append(pessoa)

    return {k: v for k, v in entidades.items() if v}


def inferir_batida_heuristica(direcao: str | None, texto: str) -> BatidaSegmento:
    """Infere a batida dramatica do segmento a partir da direcao de voz ou texto."""
    combined = f"{direcao or ''} {texto}".lower()

    if "revelação" in combined or "revelacao" in combined:
        return BatidaSegmento.REVELACAO
    if (
        "tensão" in combined
        or "tensao" in combined
        or "inquiet" in combined
        or "alarme" in combined
    ):
        return BatidaSegmento.TENSAO
    if "respiro" in combined or "pausa" in combined or "calmo" in combined:
        return BatidaSegmento.RESPIRO
    if "dado" in combined or "preciso" in combined or "número" in combined:
        return BatidaSegmento.DADO
    if "gancho" in combined or "promessa" in combined or "intriga" in combined:
        return BatidaSegmento.GANCHO
    if "citação" in combined or "citacao" in combined or '"' in combined:
        return BatidaSegmento.CITACAO
    if "fechamento" in combined or "conclusivo" in combined:
        return BatidaSegmento.FECHAMENTO

    return BatidaSegmento.CONTEXTO
