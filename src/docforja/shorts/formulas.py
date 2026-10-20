"""Carregamento e validação das fórmulas estruturadas de shorts."""

from __future__ import annotations

from pathlib import Path

import yaml

from docforja.shorts.modelos import FormulaShort


def carregar_formulas(pasta: Path = Path("global/formulas_shorts")) -> dict[str, FormulaShort]:
    """Lê YAMLs versionados de fórmulas; não grava nem modifica os arquivos."""
    if not pasta.is_dir():
        raise FileNotFoundError(f"Pasta de fórmulas não encontrada: {pasta}")
    formulas: dict[str, FormulaShort] = {}
    for caminho in sorted(pasta.glob("*.yaml")):
        with caminho.open(encoding="utf-8") as arquivo:
            formula = FormulaShort.model_validate(yaml.safe_load(arquivo) or {})
        if formula.id in formulas:
            raise ValueError(f"ID de fórmula duplicado: {formula.id}")
        if caminho.stem != formula.id:
            raise ValueError(f"Nome de arquivo deve corresponder ao ID: {caminho.name}")
        formulas[formula.id] = formula
    return formulas
