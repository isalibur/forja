"""Ferramentas estruturais para criação e validação de shorts."""

from docforja.shorts.avulsos import PedidoShortAvulso, ler_lote_avulsos
from docforja.shorts.candidatos import (
    gerar_frases_ponte,
    pontuar_candidatos,
    pontuar_candidatos_do_plano,
    segmentos_de_plano,
)
from docforja.shorts.mascaramento import MedicaoMascaramento, medir_mascaramento
from docforja.shorts.modelos import (
    CandidatoShort,
    FrasePonte,
    ManifestoVertical,
    ResultadoDosagemShort,
    SegmentoShort,
    ShortParaVerificar,
)
from docforja.shorts.verificador import verificar_short
from docforja.shorts.verticalizar import calcular_recorte_vertical, verticalizar_plano

__all__ = [
    "CandidatoShort",
    "FrasePonte",
    "ManifestoVertical",
    "MedicaoMascaramento",
    "PedidoShortAvulso",
    "ResultadoDosagemShort",
    "SegmentoShort",
    "ShortParaVerificar",
    "calcular_recorte_vertical",
    "gerar_frases_ponte",
    "ler_lote_avulsos",
    "medir_mascaramento",
    "pontuar_candidatos",
    "pontuar_candidatos_do_plano",
    "segmentos_de_plano",
    "verificar_short",
    "verticalizar_plano",
]
