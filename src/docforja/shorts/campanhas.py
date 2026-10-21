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


class AprovacaoRoteiroAvulso(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    campanha_id: str = Field(pattern=r"^[a-f0-9]{24}$")
    pedido_id: str = Field(pattern=r"^A[0-9]{3,}$")
    texto: str = Field(min_length=1, max_length=20000)
    hash_campanha: str
    revisao: str
    status: str = "roteiro_aprovado"


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


def _pasta_roteiro(raiz_projetos: Path, campanha_id: str, pedido_id: str) -> Path:
    if not re.fullmatch(r"[a-f0-9]{24}", campanha_id) or not re.fullmatch(
        r"A[0-9]{3,}", pedido_id
    ):
        raise ValueError("Identificador de roteiro inválido.")
    return raiz_projetos / "_campanhas_avulsas" / campanha_id / "roteiros" / pedido_id


def obter_aprovacao_roteiro(
    raiz_projetos: Path, campanha_id: str, pedido_id: str
) -> AprovacaoRoteiroAvulso | None:
    pasta = _pasta_roteiro(raiz_projetos, campanha_id, pedido_id)
    ponteiro = pasta / "atual.json"
    if not ponteiro.is_file():
        return None
    revisao = json.loads(ponteiro.read_text(encoding="utf-8"))["revisao"]
    if not isinstance(revisao, str) or not re.fullmatch(r"[a-f0-9]{64}", revisao):
        raise ValueError("Ponteiro de aprovação inválido.")
    return AprovacaoRoteiroAvulso.model_validate_json(
        (pasta / "revisoes" / f"{revisao}.json").read_text(encoding="utf-8")
    )


def aprovar_roteiro(
    raiz_projetos: Path,
    campanha_id: str,
    pedido_id: str,
    texto: str,
    hash_campanha: str,
) -> AprovacaoRoteiroAvulso:
    """Aprova texto explícito sem alterar o pedido original nem liberar produção."""
    campanha = obter_campanha(raiz_projetos, campanha_id)
    if campanha.hash_conteudo != hash_campanha:
        raise ValueError("A campanha mudou; recarregue antes de aprovar.")
    if not any(pedido.id == pedido_id for pedido in campanha.pedidos):
        raise ValueError("Pedido não pertence à campanha.")
    if not texto.strip() or len(texto) > 20000:
        raise ValueError("Roteiro deve conter de 1 a 20000 caracteres.")
    pasta = _pasta_roteiro(raiz_projetos, campanha_id, pedido_id)
    revisao = calcular_hash_dados(
        {"campanha": campanha.hash_conteudo, "pedido": pedido_id, "texto": texto}
    )
    aprovacao = AprovacaoRoteiroAvulso(
        campanha_id=campanha_id,
        pedido_id=pedido_id,
        texto=texto,
        hash_campanha=campanha.hash_conteudo,
        revisao=revisao,
    )
    arquivo = pasta / "revisoes" / f"{revisao}.json"
    if arquivo.is_file():
        existente = AprovacaoRoteiroAvulso.model_validate_json(arquivo.read_text(encoding="utf-8"))
        if existente != aprovacao:
            raise RuntimeError("Colisão de revisão de roteiro; nada foi sobrescrito.")
    else:
        atomic_write_json(arquivo, aprovacao.model_dump(mode="json"))
    atomic_write_json(pasta / "atual.json", {"revisao": revisao})
    return aprovacao


def aprovacoes_da_campanha(
    raiz_projetos: Path, campanha: CampanhaAvulsa
) -> dict[str, AprovacaoRoteiroAvulso]:
    aprovacoes: dict[str, AprovacaoRoteiroAvulso] = {}
    for pedido in campanha.pedidos:
        aprovacao = obter_aprovacao_roteiro(raiz_projetos, campanha.id, pedido.id)
        if aprovacao is not None and aprovacao.hash_campanha == campanha.hash_conteudo:
            aprovacoes[pedido.id] = aprovacao
    return aprovacoes
