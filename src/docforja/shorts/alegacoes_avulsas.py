"""Registro versionado de fontes e declarações comerciais dos shorts avulsos."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from docforja.io import atomic_write_json
from docforja.nucleo.etapas import calcular_hash_dados
from docforja.shorts.campanhas import obter_aprovacao_roteiro, obter_campanha
from docforja.shorts.midias_avulsas import obter_selecao_midias, selecao_vigente


class FonteAlegacao(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    alegacao: str = Field(min_length=1, max_length=500)
    fonte: str = Field(min_length=1, max_length=1000)


class DadosAlegacoes(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    fontes: list[FonteAlegacao] = Field(default_factory=list, max_length=30)
    sem_alegacoes_verificaveis: bool = False
    prova_real: FonteAlegacao | None = None
    fonte_preco: str | None = Field(default=None, max_length=1000)
    condicao_urgencia: str | None = Field(default=None, max_length=1000)
    relacao_comercial: Literal[
        "nenhuma", "produto_proprio", "afiliado", "parceria_paga"
    ] = "nenhuma"
    marca: str | None = Field(default=None, max_length=200)
    aviso_publicidade: bool = False
    revisado_pelo_usuario: bool = False

    @model_validator(mode="after")
    def validar_declaracoes(self) -> DadosAlegacoes:
        if self.sem_alegacoes_verificaveis and self.fontes:
            raise ValueError("Não declare ausência de alegações e forneça fontes ao mesmo tempo.")
        if not self.sem_alegacoes_verificaveis and not self.fontes:
            raise ValueError("Informe fontes ou declare ausência de alegações verificáveis.")
        if not self.revisado_pelo_usuario:
            raise ValueError("Confirme a revisão humana das alegações.")
        if self.relacao_comercial in {"afiliado", "parceria_paga"} and not self.aviso_publicidade:
            raise ValueError("Afiliado ou parceria exige aviso de publicidade.")
        if self.relacao_comercial == "parceria_paga" and not (self.marca or "").strip():
            raise ValueError("Parceria paga exige identificar a marca.")
        return self


class DocumentacaoAlegacoes(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    campanha_id: str
    pedido_id: str
    hash_campanha: str
    revisao_roteiro: str
    revisao_midias: str
    revisao: str
    dados: DadosAlegacoes
    status: str = "documentacao_registrada_sem_verificacao_externa"


def _pasta_documentacao(raiz_projetos: Path, campanha_id: str, pedido_id: str) -> Path:
    if not re.fullmatch(r"[a-f0-9]{24}", campanha_id) or not re.fullmatch(
        r"A[0-9]{3,}", pedido_id
    ):
        raise ValueError("Identificador de documentação inválido.")
    return raiz_projetos / "_campanhas_avulsas" / campanha_id / "alegacoes" / pedido_id


def obter_documentacao(
    raiz_projetos: Path, campanha_id: str, pedido_id: str
) -> DocumentacaoAlegacoes | None:
    pasta = _pasta_documentacao(raiz_projetos, campanha_id, pedido_id)
    ponteiro = pasta / "atual.json"
    if not ponteiro.is_file():
        return None
    revisao = json.loads(ponteiro.read_text(encoding="utf-8"))["revisao"]
    if not isinstance(revisao, str) or not re.fullmatch(r"[a-f0-9]{64}", revisao):
        raise ValueError("Ponteiro de documentação inválido.")
    return DocumentacaoAlegacoes.model_validate_json(
        (pasta / "revisoes" / f"{revisao}.json").read_text(encoding="utf-8")
    )


def documentacao_vigente(
    documentacao: DocumentacaoAlegacoes, revisao_roteiro: str, revisao_midias: str
) -> bool:
    return (
        documentacao.revisao_roteiro == revisao_roteiro
        and documentacao.revisao_midias == revisao_midias
    )


def _validar_formula(
    formula_id: str, exige_prova_real: bool, exige_fonte_preco: bool,
    regras: list[str], texto_roteiro: str, dados: DadosAlegacoes,
) -> None:
    if exige_prova_real and dados.prova_real is None:
        raise ValueError(f"A fórmula {formula_id} exige prova real fornecida pelo usuário.")
    if "comparacao_documentada" in regras and not dados.fontes:
        raise ValueError("A comparação antes/depois exige uma fonte documentada.")
    if "afirmacoes_devem_ter_fonte" in regras and not dados.fontes:
        raise ValueError("Esta fórmula exige fonte para as afirmações.")
    if formula_id in {"oferta", "produto_afiliado"} and not dados.fontes:
        raise ValueError("Benefícios e ofertas exigem fontes verificáveis.")
    menciona_preco = bool(re.search(
        r"R\$|US\$|€|£|\bdesconto\b|\d+\s*%|"
        r"\d+(?:[.,]\d{2})?\s*(?:reais|real|dólares|dolares|euros)\b",
        texto_roteiro,
        flags=re.IGNORECASE,
    ))
    if exige_fonte_preco and menciona_preco and not (dados.fonte_preco or "").strip():
        raise ValueError("Preço/condição comercial exige fonte documentada.")
    if "urgencia_com_data_ou_condicao_real" in regras and re.search(
        r"\b(hoje|amanhã|últim[oa]s?|só agora|até\s+\w+|tempo limitado)\b",
        texto_roteiro,
        flags=re.IGNORECASE,
    ) and not (dados.condicao_urgencia or "").strip():
        raise ValueError("Urgência no roteiro exige data ou condição real documentada.")
    if formula_id == "produto_afiliado" and dados.relacao_comercial != "afiliado":
        raise ValueError("Produto de afiliado exige declaração de relação de afiliado.")


def registrar_documentacao(
    raiz_projetos: Path,
    raiz_global: Path,
    campanha_id: str,
    pedido_id: str,
    hash_campanha: str,
    revisao_roteiro: str,
    revisao_midias: str,
    dados: DadosAlegacoes,
) -> DocumentacaoAlegacoes:
    campanha = obter_campanha(raiz_projetos, campanha_id)
    pedido = next((item for item in campanha.pedidos if item.id == pedido_id), None)
    if campanha.hash_conteudo != hash_campanha or pedido is None:
        raise ValueError("Campanha ou pedido desatualizado.")
    aprovacao = obter_aprovacao_roteiro(raiz_projetos, campanha_id, pedido_id)
    if aprovacao is None or aprovacao.revisao != revisao_roteiro:
        raise ValueError("Roteiro aprovado mudou; recarregue a campanha.")
    selecao = obter_selecao_midias(raiz_projetos, campanha_id, pedido_id)
    if (
        selecao is None
        or selecao.revisao != revisao_midias
        or not selecao_vigente(raiz_global, selecao, revisao_roteiro)
    ):
        raise ValueError("Seleção de imagens mudou; confirme-a novamente.")
    formula = campanha.formulas[pedido.formula_id]
    _validar_formula(
        formula.id, formula.exige_prova_real, formula.exige_fonte_preco,
        formula.regras, aprovacao.texto, dados,
    )
    revisao = calcular_hash_dados({
        "campanha": hash_campanha,
        "pedido": pedido_id,
        "roteiro": revisao_roteiro,
        "midias": revisao_midias,
        "dados": dados.model_dump(mode="json"),
    })
    documentacao = DocumentacaoAlegacoes(
        campanha_id=campanha_id,
        pedido_id=pedido_id,
        hash_campanha=hash_campanha,
        revisao_roteiro=revisao_roteiro,
        revisao_midias=revisao_midias,
        revisao=revisao,
        dados=dados,
    )
    pasta = _pasta_documentacao(raiz_projetos, campanha_id, pedido_id)
    arquivo = pasta / "revisoes" / f"{revisao}.json"
    if arquivo.is_file():
        existente = DocumentacaoAlegacoes.model_validate_json(arquivo.read_text(encoding="utf-8"))
        if existente != documentacao:
            raise RuntimeError("Colisão de revisão de documentação; nada foi sobrescrito.")
    else:
        atomic_write_json(arquivo, documentacao.model_dump(mode="json"))
    atomic_write_json(pasta / "atual.json", {"revisao": revisao})
    return documentacao
