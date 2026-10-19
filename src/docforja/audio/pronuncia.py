from __future__ import annotations

import re
from pathlib import Path

import yaml


class DicionarioPronuncia:
    def __init__(self, caminho_yaml: Path | None = None) -> None:
        self.caminho_yaml = caminho_yaml or Path("config/pronuncia.yaml")
        self.dados: dict[str, dict[str, str]] = {}
        self._carregar()

    def _carregar(self) -> None:
        if not self.caminho_yaml.exists():
            return
        try:
            with open(self.caminho_yaml, encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
            for idioma, config in raw.items():
                if isinstance(config, dict) and "substituicoes" in config:
                    self.dados[idioma] = config["substituicoes"]
        except Exception:
            self.dados = {}

    def aplicar(self, texto: str, idioma: str = "pt-BR") -> str:
        """Aplica substituicoes foneticas de palavras inteiras para o idioma fornecido."""
        subs = self.dados.get(idioma)
        if not subs:
            return texto

        resultado = texto
        for palavra_orig, pronuncia in subs.items():
            # Substitui apenas palavras inteiras respeitando limites de palavra
            padrao = rf"\b{re.escape(palavra_orig)}\b"
            resultado = re.sub(padrao, pronuncia, resultado)
        return resultado


_instancia_padrao: DicionarioPronuncia | None = None


def aplicar_pronuncia(texto: str, idioma: str = "pt-BR", caminho_yaml: Path | None = None) -> str:
    """Funcao utilitaria para aplicar o dicionario de pronuncia."""
    global _instancia_padrao
    if caminho_yaml is not None:
        return DicionarioPronuncia(caminho_yaml).aplicar(texto, idioma)
    if _instancia_padrao is None:
        _instancia_padrao = DicionarioPronuncia()
    return _instancia_padrao.aplicar(texto, idioma)
