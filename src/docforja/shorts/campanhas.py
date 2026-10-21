"""Campanhas avulsas versionadas, ainda sem aprovação ou renderização."""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from docforja.io import atomic_write_json
from docforja.nucleo.etapas import calcular_hash_dados
from docforja.shorts.avulsos import PedidoShortAvulso
from docforja.shorts.modelos import FormulaShort


class CampanhaAvulsa(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str = Field(pattern=r"^[a-f0-9]{24}$")
    nome: str = Field(min_length=1, max_length=120)
    status: str = "aguardando_revisao"
    pedidos: list[PedidoShortAvulso] = Field(min_length=1)
    formulas: dict[str, FormulaShort]
    hash_conteudo: str


def salvar_campanha(
    raiz_projetos: Path,
    nome: str,
    pedidos: list[PedidoShortAvulso],
    formulas: dict[str, FormulaShort],
) -> CampanhaAvulsa:
    """Salva um snapshot imutável; repetir o mesmo pedido retorna a mesma campanha."""
    nome = nome.strip()
    if not nome or len(nome) > 120:
        raise ValueError("Informe um nome de campanha de até 120 caracteres.")
    usadas = {pedido.formula_id: formulas[pedido.formula_id] for pedido in pedidos}
    conteudo = {
        "nome": nome,
        "pedidos": [pedido.model_dump(mode="json") for pedido in pedidos],
        "formulas": {chave: valor.model_dump(mode="json") for chave, valor in usadas.items()},
    }
    hash_conteudo = calcular_hash_dados(conteudo)
    campanha = CampanhaAvulsa.model_validate(
        {"id": hash_conteudo[:24], "nome": nome, **conteudo, "hash_conteudo": hash_conteudo}
    )
    pasta = raiz_projetos / "_campanhas_avulsas"
    caminho = pasta / f"{campanha.id}.json"
    if caminho.is_file():
        existente = CampanhaAvulsa.model_validate_json(caminho.read_text(encoding="utf-8"))
        if existente.hash_conteudo != hash_conteudo:
            raise RuntimeError("Colisão de identificador de campanha; nada foi sobrescrito.")
        return existente
    pasta.mkdir(parents=True, exist_ok=True)
    atomic_write_json(caminho, campanha.model_dump(mode="json"))
    return campanha


def obter_campanha(raiz_projetos: Path, campanha_id: str) -> CampanhaAvulsa:
    if not re.fullmatch(r"[a-f0-9]{24}", campanha_id):
        raise ValueError("Identificador de campanha inválido.")
    caminho = raiz_projetos / "_campanhas_avulsas" / f"{campanha_id}.json"
    if not caminho.is_file():
        raise FileNotFoundError("Campanha não encontrada.")
    return CampanhaAvulsa.model_validate(json.loads(caminho.read_text(encoding="utf-8")))


def listar_campanhas(raiz_projetos: Path) -> list[CampanhaAvulsa]:
    pasta = raiz_projetos / "_campanhas_avulsas"
    if not pasta.is_dir():
        return []
    return [obter_campanha(raiz_projetos, caminho.stem) for caminho in sorted(pasta.glob("*.json"))]
