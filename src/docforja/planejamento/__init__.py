"""Módulo de planejamento do DocForja: leitura, estratégia, shots, ativos, dosagem e estimativa."""

from docforja.planejamento.ativos import consolidar_ativos_plano
from docforja.planejamento.dosagem import ResultadoVerificacao, VerificadorDosagem, Violacao
from docforja.planejamento.entidades import (
    BlocoProcessado,
    SegmentoProcessado,
    extrair_entidades_heuristica,
    inferir_batida_heuristica,
)
from docforja.planejamento.estimativa import RelatorioEstimativa, estimar_tempo_plano
from docforja.planejamento.estrategia import EstrategiaBloco, planejar_estrategias
from docforja.planejamento.leitura import (
    limpar_texto_para_tts,
    normalizar_palavras,
    verificar_preservacao_palavras,
)
from docforja.planejamento.planejador import PlanejadorVideo
from docforja.planejamento.relatorios import (
    gerar_estimativa_md,
    gerar_numeros_na_tela_md,
    gerar_plano_md,
    gerar_verificacao_md,
    gravar_relatorios_planejamento,
)
from docforja.planejamento.shots import gerar_shots_bloco

__all__ = [
    "BlocoProcessado",
    "EstrategiaBloco",
    "PlanejadorVideo",
    "RelatorioEstimativa",
    "ResultadoVerificacao",
    "SegmentoProcessado",
    "VerificadorDosagem",
    "Violacao",
    "consolidar_ativos_plano",
    "estimar_tempo_plano",
    "extrair_entidades_heuristica",
    "gerar_estimativa_md",
    "gerar_numeros_na_tela_md",
    "gerar_plano_md",
    "gerar_shots_bloco",
    "gerar_verificacao_md",
    "gravar_relatorios_planejamento",
    "inferir_batida_heuristica",
    "limpar_texto_para_tts",
    "normalizar_palavras",
    "planejar_estrategias",
    "verificar_preservacao_palavras",
]
