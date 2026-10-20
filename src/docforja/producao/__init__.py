"""Módulo de produção final e exportação (13 §2)."""

from docforja.producao.execucao import (
    executar_r1_imagens,
    executar_r2_tratamento,
    executar_r3_mapas,
    executar_r4_trilha_sfx,
    executar_r5_montagem,
    executar_r6_mix,
    executar_r7_render,
    executar_r8_qa,
    executar_r9_pacote,
    executar_r10_biblioteca,
)
from docforja.producao.otio import exportar_projeto_otio, gerar_timeline_otio_dict
from docforja.producao.saida import (
    gerar_creditos_txt,
    gerar_relatorio_md,
    montar_arvore_saida,
    montar_pacote_saida_completo,
)

__all__ = [
    "executar_r1_imagens",
    "executar_r2_tratamento",
    "executar_r3_mapas",
    "executar_r4_trilha_sfx",
    "executar_r5_montagem",
    "executar_r6_mix",
    "executar_r7_render",
    "executar_r8_qa",
    "executar_r9_pacote",
    "executar_r10_biblioteca",
    "exportar_projeto_otio",
    "gerar_creditos_txt",
    "gerar_relatorio_md",
    "gerar_timeline_otio_dict",
    "montar_arvore_saida",
    "montar_pacote_saida_completo",
]
