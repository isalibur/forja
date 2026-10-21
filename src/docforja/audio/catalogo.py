"""Catálogo de vozes e motores do TTS, lido de `config/modelos.yaml`."""

from __future__ import annotations

from pathlib import Path
from typing import Any

MODELOS_CONFIG = Path(__file__).resolve().parents[3] / "config" / "modelos.yaml"


def _catalogo() -> dict[str, Any]:
    import yaml

    if not MODELOS_CONFIG.is_file():
        return {}
    dados = yaml.safe_load(MODELOS_CONFIG.read_text(encoding="utf-8")) or {}
    tts = dados.get("tts", {})
    return tts if isinstance(tts, dict) else {}


def listar_candidatos(adaptador: str) -> list[dict[str, Any]]:
    """Candidatos de TTS de um adaptador, na ordem do catálogo."""
    candidatos = []
    for item in _catalogo().get("candidatos", []):
        if isinstance(item, dict) and item.get("adaptador") == adaptador:
            candidatos.append(item)
    return candidatos


def listar_vozes(adaptador: str, voz: str | None = None) -> list[dict[str, Any]]:
    """Vozes de um adaptador; com `voz`, devolve só a voz pedida."""
    encontradas: list[dict[str, Any]] = []
    for candidato in listar_candidatos(adaptador):
        benchmark = candidato.get("benchmark", {}) or {}
        vozes = benchmark.get("voices", []) or []
        for item in vozes:
            if not isinstance(item, dict):
                continue
            if voz is None:
                encontradas.append(item)
            elif str(item.get("id")) == voz:
                return [item]
    return encontradas


def resolver_voz(adaptador: str, voz: str | None) -> dict[str, Any] | None:
    """Dados da voz pedida (id, idioma, caminho do prompt/arquivo de referência)."""
    vozes = listar_vozes(adaptador, voz)
    return vozes[0] if vozes else None


__all__ = [
    "MODELOS_CONFIG",
    "listar_candidatos",
    "listar_vozes",
    "resolver_voz",
]
