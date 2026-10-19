"""Módulo núcleo do DocForja: projetos, banco, pipeline, GPU, cotas e eventos."""

from __future__ import annotations

from docforja.nucleo.banco import BancoProjeto
from docforja.nucleo.cotas import GerenciadorCotas, gerenciador_cotas
from docforja.nucleo.etapas import DefinicaoEtapa, PipelineGrafo, calcular_hash_dados
from docforja.nucleo.eventos import BarramentoEventos, Evento, barramento_global
from docforja.nucleo.executor import ContextoEtapa, ExecutorPipeline
from docforja.nucleo.gpu import SemaforoGPU, semaforo_gpu
from docforja.nucleo.projeto import PastasProjeto, Projeto, slugificar

__all__ = [
    "BancoProjeto",
    "BarramentoEventos",
    "ContextoEtapa",
    "DefinicaoEtapa",
    "Evento",
    "ExecutorPipeline",
    "GerenciadorCotas",
    "PastasProjeto",
    "PipelineGrafo",
    "Projeto",
    "SemaforoGPU",
    "barramento_global",
    "calcular_hash_dados",
    "gerenciador_cotas",
    "semaforo_gpu",
    "slugificar",
]
