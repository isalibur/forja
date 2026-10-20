"""Histórico imutável das escolhas manuais de candidatas na interface M5."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel

from docforja.io import atomic_write_json
from docforja.nucleo.etapas import calcular_hash_dados
from docforja.nucleo.projeto import Projeto


class SelecaoCandidata(BaseModel):
    ativo_id: str
    candidata: str | None
    hash_resolvidos: str
    criada_em: str


def hash_resolvidos(projeto: Projeto) -> str | None:
    caminho = projeto.pastas.plano / "ativos_resolvidos.json"
    return calcular_hash_dados(caminho) if caminho.is_file() else None


def selecoes_atuais(projeto: Projeto) -> dict[str, SelecaoCandidata]:
    """Reconstrói escolhas do histórico, ignorando revisões de outro P7."""
    hash_atual = hash_resolvidos(projeto)
    if hash_atual is None:
        return {}
    pasta = projeto.pastas.midias / "selecoes_ui"
    if not pasta.is_dir():
        return {}
    atuais: dict[str, SelecaoCandidata] = {}
    for arquivo in sorted(pasta.glob("*.json")):
        try:
            selecao = SelecaoCandidata.model_validate_json(arquivo.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if selecao.hash_resolvidos == hash_atual:
            atuais[selecao.ativo_id] = selecao
    return atuais


def registrar_selecao(
    projeto: Projeto, ativo_id: str, candidata: str | None, hash_esperado: str
) -> SelecaoCandidata:
    """Grava uma nova revisão sem modificar mídia nem resultado original de P7."""
    if hash_resolvidos(projeto) != hash_esperado:
        raise ValueError("O plano mudou; recarregue antes de escolher uma imagem.")
    instante = datetime.now(UTC)
    selecao = SelecaoCandidata(
        ativo_id=ativo_id,
        candidata=candidata,
        hash_resolvidos=hash_esperado,
        criada_em=instante.isoformat(),
    )
    pasta = projeto.pastas.midias / "selecoes_ui"
    nome = f"{instante.strftime('%Y%m%dT%H%M%S%fZ')}-{uuid4().hex}.json"
    caminho = pasta / nome
    atomic_write_json(caminho, selecao.model_dump(mode="json"))
    return selecao
