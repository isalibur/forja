"""Leitura e planejamento revisável de shorts avulsos em lote CSV."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from docforja.shorts.afiliados import (
    ProdutoAfiliado,
    ler_planilha_produtos,
    roteiro_sugerido,
)
from docforja.shorts.formulas import carregar_formulas
from docforja.shorts.modelos import FormulaShort

ObjetivoAvulso = Literal[
    "vendas",
    "promocao_canal",
    "engajamento",
    "educativo",
    "anuncio",
    "bastidores",
    "autoridade",
    "outro",
]
OrigemRoteiro = Literal["proprio", "formula", "gemini_manual"]
DuracaoAvulso = Literal[15, 30, 45, 60, 90]

COLUNAS = {
    "tema",
    "objetivo",
    "duracao_s",
    "formula",
    "origem_roteiro",
    "roteiro",
    "cta",
    "opcao_a",
    "opcao_b",
}


class PedidoShortAvulso(BaseModel):
    """Pedido importado; ainda depende de roteiro e aprovação antes de produzir."""

    model_config = ConfigDict(extra="forbid", strict=True)

    id: str = Field(min_length=1)
    tema: str = Field(min_length=1)
    objetivo: ObjetivoAvulso
    duracao_s: DuracaoAvulso
    formula_id: str = Field(min_length=1)
    origem_roteiro: OrigemRoteiro
    roteiro: str | None = None
    cta: str | None = None
    opcao_a: str | None = None
    opcao_b: str | None = None
    produto: ProdutoAfiliado | None = None
    roteiro_sugerido: str | None = None
    pendencias: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validar_roteiro(self) -> PedidoShortAvulso:
        if self.origem_roteiro == "proprio" and not (self.roteiro or "").strip():
            raise ValueError("Roteiro próprio exige texto fornecido pelo usuário.")
        if self.origem_roteiro != "proprio" and (self.roteiro or "").strip():
            raise ValueError("Texto de roteiro exige origem_roteiro=proprio.")
        if self.formula_id == "pergunta_comentarios":
            if self.objetivo != "engajamento":
                raise ValueError("A fórmula de pergunta exige objetivo engajamento.")
            opcoes = [self.opcao_a or "", self.opcao_b or ""]
            if any(opcoes) and any(not opcao or len(opcao.split()) != 1 for opcao in opcoes):
                raise ValueError("Engajamento exige opções A/B de uma palavra cada no CSV.")
            if all(opcoes) and opcoes[0].casefold() == opcoes[1].casefold():
                raise ValueError("As opções A/B devem ser diferentes.")
        elif self.opcao_a or self.opcao_b:
            raise ValueError("Opções A/B são aceitas apenas na fórmula pergunta_comentarios.")
        return self


def _escolher_formula(
    formulas: dict[str, FormulaShort],
    objetivo: ObjetivoAvulso,
    duracao: DuracaoAvulso,
    selecionada: str,
) -> FormulaShort:
    if selecionada:
        formula = formulas.get(selecionada)
        if formula is None:
            raise ValueError(f"Fórmula inexistente: {selecionada}.")
        candidatas = [formula]
    else:
        candidatas = [formulas[id_] for id_ in sorted(formulas)]
    for formula in candidatas:
        if (
            objetivo in formula.objetivos or (objetivo == "outro" and selecionada)
        ) and formula.duracao_min_s <= duracao <= formula.duracao_max_s:
            return formula
    raise ValueError(f"Nenhuma fórmula compatível com objetivo {objetivo} e duração {duracao} s.")


PASTA_FORMULAS_PADRAO = Path(__file__).resolve().parents[3] / "global" / "formulas_shorts"


def _ler_lote(
    leitor: csv.DictReader[str], formulas: dict[str, FormulaShort]
) -> list[PedidoShortAvulso]:
    pedidos: list[PedidoShortAvulso] = []
    cabecalho = leitor.fieldnames or []
    if len(cabecalho) != len(set(cabecalho)):
        raise ValueError("Cabeçalho CSV contém colunas duplicadas.")
    obrigatorias = {"tema", "objetivo", "duracao_s"}
    if obrigatorias - set(cabecalho):
        raise ValueError("CSV exige as colunas tema, objetivo e duracao_s.")
    if set(cabecalho) - COLUNAS:
        raise ValueError(f"Colunas CSV desconhecidas: {sorted(set(cabecalho) - COLUNAS)}")
    for numero_linha, linha in enumerate(leitor, start=2):
        if None in linha:
            raise ValueError(f"Linha {numero_linha} do CSV tem mais valores que colunas.")
        if all(not (valor or "").strip() for valor in linha.values()):
            continue
        try:
            tema = (linha.get("tema") or "").strip()
            objetivo = (linha.get("objetivo") or "").strip()
            duracao = int((linha.get("duracao_s") or "").strip())
            origem = (linha.get("origem_roteiro") or "").strip() or (
                "proprio" if (linha.get("roteiro") or "").strip() else "formula"
            )
            formula = _escolher_formula(
                formulas, objetivo, duracao, (linha.get("formula") or "").strip()
            )
            if formula.id == "pergunta_comentarios" and not (
                (linha.get("opcao_a") or "").strip() and (linha.get("opcao_b") or "").strip()
            ):
                raise ValueError("Engajamento exige opções A/B de uma palavra cada no CSV.")
            pendencias = ["aprovar roteiro", "aprovar mídias e licenças"]
            if formula.regras or formula.exige_prova_real or formula.exige_fonte_preco:
                pendencias.append("comprovar alegações exigidas pela fórmula")
            pedidos.append(
                PedidoShortAvulso.model_validate(
                    {
                        "id": f"A{len(pedidos) + 1:03d}",
                        "tema": tema,
                        "objetivo": objetivo,
                        "duracao_s": duracao,
                        "formula_id": formula.id,
                        "origem_roteiro": origem,
                        "roteiro": linha.get("roteiro") or None,
                        "cta": (linha.get("cta") or "").strip() or None,
                        "opcao_a": (linha.get("opcao_a") or "").strip() or None,
                        "opcao_b": (linha.get("opcao_b") or "").strip() or None,
                        "pendencias": pendencias,
                    }
                )
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Linha {numero_linha} do CSV: {exc}") from exc
    if not pedidos:
        raise ValueError("CSV não contém pedidos de shorts avulsos.")
    return pedidos


def ler_lote_avulsos(
    caminho_csv: Path, pasta_formulas: Path = PASTA_FORMULAS_PADRAO
) -> list[PedidoShortAvulso]:
    """Importa CSV local sem criar projetos, gerar afirmações ou acessar a rede."""
    formulas = carregar_formulas(pasta_formulas)
    with caminho_csv.open("r", encoding="utf-8-sig", newline="") as arquivo:
        return _ler_lote(csv.DictReader(arquivo), formulas)


def ler_lote_avulsos_texto(
    texto_csv: str, pasta_formulas: Path = PASTA_FORMULAS_PADRAO
) -> list[PedidoShortAvulso]:
    """Valida CSV colado na interface, sem gravar o conteúdo recebido."""
    formulas = carregar_formulas(pasta_formulas)
    return _ler_lote(csv.DictReader(io.StringIO(texto_csv.lstrip("\ufeff"))), formulas)


def ler_lote_afiliados(
    texto_csv: str, pasta_formulas: Path = PASTA_FORMULAS_PADRAO
) -> list[PedidoShortAvulso]:
    """Converte a planilha de produtos em um pedido de short de afiliado por linha."""
    formulas = carregar_formulas(pasta_formulas)
    formula = formulas.get("produto_afiliado")
    if formula is None:
        raise ValueError("A fórmula produto_afiliado não está no catálogo.")
    produtos = ler_planilha_produtos(texto_csv)
    pedidos: list[PedidoShortAvulso] = []
    for indice, produto in enumerate(produtos, start=1):
        pendencias = [
            "aprovar roteiro",
            "aprovar mídias e licenças",
            "comprovar alegações exigidas pela fórmula",
        ]
        pedidos.append(
            PedidoShortAvulso.model_validate(
                {
                    "id": f"A{indice:03d}",
                    "tema": produto.nome,
                    "objetivo": "vendas",
                    "duracao_s": produto.duracao_s,
                    "formula_id": formula.id,
                    "origem_roteiro": "formula",
                    "roteiro": None,
                    "cta": produto.cta,
                    "produto": produto.model_dump(mode="json"),
                    "roteiro_sugerido": roteiro_sugerido(produto),
                    "pendencias": pendencias,
                }
            )
        )
    return pedidos
