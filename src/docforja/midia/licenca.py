"""Classificação de licenças e detecção de patrimônio restrito (P7 / M5).

Aplica as regras de docs/pipeline/07-assets-e-direitos.md:
- NC (não comercial) e ND (não derivativo) proibidos em projetos monetizados.
- PD, CC0, CC BY, CC BY-SA, Pexels e Pixabay permitidos comercialmente.
- Heurística de patrimônio cultural italiano (Codice dei beni culturali) marca RISCO_IT.
- Gravação atômica de sidecar .licenca.json para cada imagem de arquivo.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from docforja.io import atomic_write_json

# Termos que identificam bens culturais restritos (ex.: Lei italiana de patrimônio)
TERMOS_PATRIMONIO_RESTRITO = [
    "pompei",
    "pompeii",
    "ercolano",
    "herculaneum",
    "mann",
    "museo archeologico",
    "parco archeologico",
    "ministero della cultura",
    "bene culturale",
    "soprintendenza",
    "casa del centenario",
    "casa del poeta tragico",
    "casa del fauno",
    "villa dei misteri",
]

# Padrões que proíbem uso comercial ou modificação em vídeo
PADROES_NAO_COMERCIAL = [
    r"\bnc\b",
    r"non-commercial",
    r"noncommercial",
    r"não-comercial",
    r"nao-comercial",
    r"não comercial",
]

PADROES_SEM_DERIVADOS = [
    r"\bnd\b",
    r"no-derivatives",
    r"noderivs",
    r"sem derivados",
]

# Padrões que liberam uso comercial aberto
PADROES_DOMINIO_PUBLICO = [
    r"\bpd\b",
    r"public domain",
    r"domínio público",
    r"dominio publico",
    r"\bcc0\b",
    r"cc-0",
    r"usgov",
    r"usgs",
    r"nasa",
]

PADROES_LIVRE_COM_ATRIBUICAO = [
    r"cc[\s_-]?by",
    r"creative commons attribution",
    r"pexels",
    r"pixabay",
    r"unsplash",
]


class FichaLicenca(BaseModel):
    """Ficha cadastral de licença e autoria de um ativo de mídia."""

    url_origem: str = ""
    autor: str = ""
    licenca: str = "desconhecida"
    comercial: bool = True
    patrimonio_restrito: bool = False
    credito_obrigatorio: bool = True
    texto_credito: str = ""
    detalhes: dict[str, Any] = Field(default_factory=dict)


def classificar_licenca(licenca_str: str) -> tuple[bool, bool]:
    """Classifica se uma licença permite uso comercial e se exige crédito.

    Retorna:
        (comercial_permitido, credito_obrigatorio)
    """
    texto = licenca_str.strip().lower()
    if not texto:
        return False, True

    # 1. Se tem restrição NC ou ND, uso comercial é bloqueado
    for padrao in PADROES_NAO_COMERCIAL:
        if re.search(padrao, texto):
            return False, True

    for padrao in PADROES_SEM_DERIVADOS:
        if re.search(padrao, texto):
            return False, True

    # 2. Domínio público e CC0: comercial liberado, atribuição não legalmente exigida
    for padrao in PADROES_DOMINIO_PUBLICO:
        if re.search(padrao, texto):
            return True, False

    # 3. Licenças com atribuição comercial permitida
    for padrao in PADROES_LIVRE_COM_ATRIBUICAO:
        if re.search(padrao, texto):
            return True, True

    # Licenças desconhecidas por segurança não são consideradas comercialmente aprovadas
    return False, True


def detectar_patrimonio_restrito(*textos: str) -> bool:
    """Verifica se algum dos textos contém referências a bens culturais restritos."""
    texto_unificado = " ".join(t for t in textos if t).lower()
    return any(termo in texto_unificado for termo in TERMOS_PATRIMONIO_RESTRITO)


def caminho_sidecar_licenca(caminho_imagem: Path) -> Path:
    """Retorna o caminho do arquivo .licenca.json correspondente."""
    return caminho_imagem.with_name(f"{caminho_imagem.name}.licenca.json")


def salvar_ficha_licenca(caminho_imagem: Path, ficha: FichaLicenca) -> Path:
    """Salva a ficha de licença como sidecar .licenca.json de forma atômica."""
    sidecar = caminho_sidecar_licenca(caminho_imagem)
    atomic_write_json(sidecar, ficha.model_dump())
    return sidecar


def carregar_ficha_licenca(caminho_imagem: Path) -> FichaLicenca | None:
    """Carrega o sidecar .licenca.json se ele existir."""
    sidecar = caminho_sidecar_licenca(caminho_imagem)
    if not sidecar.is_file():
        return None
    try:
        dados = json.loads(sidecar.read_text(encoding="utf-8"))
        return FichaLicenca.model_validate(dados)
    except Exception:
        return None
