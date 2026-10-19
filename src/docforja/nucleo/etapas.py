"""Definição de etapas, grafo de dependências (DAG) e regras de pipeline."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class DefinicaoEtapa:
    """Configuração declarativa de uma etapa do pipeline."""

    id: str
    needs: list[str] = field(default_factory=list)
    llm: str | None = None
    gpu: str | None = None
    por: str | None = None
    gate: bool = False
    skip_if: str | None = None
    opcional: bool = False
    loop_llm: int | None = None
    autocorrecao: int | None = None


class PipelineGrafo:
    """Gerenciador do DAG de etapas para um tipo de projeto."""

    def __init__(self, etapas: dict[str, DefinicaoEtapa]) -> None:
        self.etapas = etapas
        self._validar_sem_ciclos()

    @classmethod
    def carregar(
        cls,
        caminho_yaml: Path = Path("config/pipeline.yaml"),
        tipo_projeto: str = "longo",
    ) -> PipelineGrafo:
        if not caminho_yaml.is_file():
            raise FileNotFoundError(f"Arquivo de pipeline não encontrado: {caminho_yaml}")
        with caminho_yaml.open("r", encoding="utf-8") as handle:
            dados = yaml.safe_load(handle) or {}

        config_tipo = dados.get("tipos", {}).get(tipo_projeto, {})
        if not config_tipo:
            # Fallback para o nível raiz se for o formato antigo
            config_tipo = {k: v for k, v in dados.items() if k not in ("schema_version", "tipos")}

        etapas: dict[str, DefinicaoEtapa] = {}
        for etapa_id, cfg in config_tipo.items():
            if not isinstance(cfg, dict):
                continue
            etapas[etapa_id] = DefinicaoEtapa(
                id=etapa_id,
                needs=cfg.get("needs", []),
                llm=cfg.get("llm"),
                gpu=cfg.get("gpu"),
                por=cfg.get("por"),
                gate=bool(cfg.get("gate", False)),
                skip_if=cfg.get("skip_if"),
                opcional=bool(cfg.get("opcional", False)),
                loop_llm=cfg.get("loop_llm"),
                autocorrecao=cfg.get("autocorrecao"),
            )
        return cls(etapas)

    def _validar_sem_ciclos(self) -> None:
        """Verifica se existem ciclos ou dependências inexistentes no grafo."""
        visitados: dict[str, int] = {}  # 0: não visitado, 1: visitando, 2: visitado

        def dfs(node: str) -> None:
            visitados[node] = 1
            for vizinho in self.etapas.get(node, DefinicaoEtapa(id=node)).needs:
                if vizinho not in self.etapas:
                    continue
                estado = visitados.get(vizinho, 0)
                if estado == 1:
                    raise ValueError(
                        f"Ciclo detectado no pipeline envolvendo '{node}' e '{vizinho}'"
                    )
                if estado == 0:
                    dfs(vizinho)
            visitados[node] = 2

        for node in self.etapas:
            if visitados.get(node, 0) == 0:
                dfs(node)

    def obter_prontas(self, concluidas: set[str], executando: set[str]) -> list[DefinicaoEtapa]:
        """Retorna etapas cujos pré-requisitos estão satisfeitos e não estão rodando."""
        prontas = []
        for etapa_id, def_etapa in self.etapas.items():
            if etapa_id in concluidas or etapa_id in executando:
                continue
            # Todos os 'needs' concluídos?
            if all(dep in concluidas for dep in def_etapa.needs if dep in self.etapas):
                prontas.append(def_etapa)
        return prontas

    def obter_dependentes(self, etapa_id: str) -> set[str]:
        """Retorna todas as etapas a jusante que dependem direta ou indiretamente de etapa_id."""
        dependentes: set[str] = set()

        def coletar(origem: str) -> None:
            for candidato_id, def_etapa in self.etapas.items():
                if origem in def_etapa.needs and candidato_id not in dependentes:
                    dependentes.add(candidato_id)
                    coletar(candidato_id)

        coletar(etapa_id)
        return dependentes


def calcular_hash_dados(dados: Any) -> str:
    """Calcula hash sha256 estável de qualquer estrutura de dados ou texto."""
    if isinstance(dados, Path):
        if dados.is_file():
            return hashlib.sha256(dados.read_bytes()).hexdigest()
        return hashlib.sha256(str(dados).encode("utf-8")).hexdigest()
    if isinstance(dados, str):
        return hashlib.sha256(dados.encode("utf-8")).hexdigest()
    conteudo = json.dumps(dados, sort_keys=True, default=str)
    return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()
