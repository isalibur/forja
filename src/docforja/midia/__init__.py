"""Subpacote de mídia, acervos, curadoria e resolução de ativos do DocForja."""

from __future__ import annotations

from docforja.midia.acervo import AcervoAdapter, AdaptadorAcervoMock, AdaptadorWikimedia
from docforja.midia.curadoria import CuradorImagens
from docforja.midia.licenca import (
    FichaLicenca,
    carregar_ficha_licenca,
    classificar_licenca,
    detectar_patrimonio_restrito,
    salvar_ficha_licenca,
)
from docforja.midia.lista_busca import gerar_lista_de_busca_md
from docforja.midia.pasta_manual import escanear_pasta_manual, identificar_ativo_por_nome
from docforja.midia.resolucao import resolver_ativos_projeto

__all__ = [
    "AcervoAdapter",
    "AdaptadorAcervoMock",
    "AdaptadorWikimedia",
    "CuradorImagens",
    "FichaLicenca",
    "carregar_ficha_licenca",
    "classificar_licenca",
    "detectar_patrimonio_restrito",
    "escanear_pasta_manual",
    "gerar_lista_de_busca_md",
    "identificar_ativo_por_nome",
    "resolver_ativos_projeto",
    "salvar_ficha_licenca",
]
