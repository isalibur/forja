"""Seleção versionada de imagens globais para campanhas de shorts avulsos."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from docforja.io import atomic_write_json
from docforja.midia.licenca import classificar_licenca, detectar_patrimonio_restrito
from docforja.nucleo.etapas import calcular_hash_dados
from docforja.shorts.campanhas import obter_aprovacao_roteiro, obter_campanha

CATEGORIAS_IMAGEM = ("imagens", "personagens", "mapas")
CATEGORIA_CLIPE = "loops"
EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".webp"}
ID_SEGURO = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}")


class MidiaGlobalAvulsa(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id_global: str
    descricao: str
    licenca: str
    credito: str = ""
    hash_arquivo: str
    hash_ficha: str
    tipo: Literal["imagem", "clipe"] = "imagem"


class SelecaoMidiasAvulsa(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    campanha_id: str
    pedido_id: str
    hash_campanha: str
    revisao_roteiro: str
    revisao: str
    midias: list[MidiaGlobalAvulsa] = Field(min_length=1, max_length=20)
    status: str = "midias_selecionadas"


def resolver_midia_global(raiz_global: Path, id_global: str) -> tuple[Path, MidiaGlobalAvulsa]:
    partes = id_global.split(":")
    if (
        len(partes) != 3
        or partes[0] != "global"
        or partes[1] not in (*CATEGORIAS_IMAGEM, CATEGORIA_CLIPE)
        or not ID_SEGURO.fullmatch(partes[2])
        or ".." in partes[2]
    ):
        raise ValueError("Identificador de mídia global inválido.")
    categoria, item_id = partes[1], partes[2]
    tipo: Literal["imagem", "clipe"] = "clipe" if categoria == CATEGORIA_CLIPE else "imagem"
    subpasta = raiz_global / categoria
    if subpasta.resolve().parent != raiz_global.resolve():
        raise ValueError("Categoria global fora da pasta autorizada.")
    ficha_path = subpasta / f"{item_id}.json"
    if not ficha_path.is_file() or ficha_path.is_symlink():
        raise ValueError("Mídia sem ficha global verificável.")
    try:
        ficha = json.loads(ficha_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("Ficha global inválida.") from exc
    if not isinstance(ficha, dict):
        raise ValueError("Ficha global inválida.")
    nome_arquivo = ficha.get("arquivo")
    if (
        not isinstance(nome_arquivo, str)
        or not nome_arquivo
        or Path(nome_arquivo).name != nome_arquivo
        or "/" in nome_arquivo
        or "\\" in nome_arquivo
    ):
        raise ValueError("Ficha global não aponta para arquivo seguro.")
    arquivo = subpasta / nome_arquivo
    extensoes = {".mp4"} if tipo == "clipe" else EXTENSOES_IMAGEM
    if arquivo.suffix.lower() not in extensoes or not arquivo.is_file():
        raise ValueError("Arquivo de mídia global ausente ou incompatível.")
    if arquivo.is_symlink() or arquivo.resolve().parent != subpasta.resolve():
        raise ValueError("Mídia global fora da pasta autorizada.")
    licenca = str(ficha.get("licenca", ""))
    comercial, _ = classificar_licenca(licenca)
    descricao = str(ficha.get("descricao", ""))
    if (
        ficha.get("comercial") is not True
        or not comercial
        or ficha.get("patrimonio_restrito") is True
        or detectar_patrimonio_restrito(descricao)
        or ficha.get("publicacao_permitida") is False
        or ficha.get("restricao_editorial")
    ):
        raise ValueError("Mídia global sem liberação comercial/editorial para este short.")
    hash_arquivo = calcular_hash_dados(arquivo)
    if ficha.get("sha256") and ficha["sha256"] != hash_arquivo:
        raise ValueError("Hash da imagem diverge da ficha global.")
    return arquivo, MidiaGlobalAvulsa(
        id_global=id_global,
        descricao=descricao,
        licenca=licenca,
        credito=str(ficha.get("credito") or ficha.get("autor") or ""),
        hash_arquivo=hash_arquivo,
        hash_ficha=calcular_hash_dados(ficha_path),
        tipo=tipo,
    )


def resolver_imagem_global(raiz_global: Path, id_global: str) -> tuple[Path, MidiaGlobalAvulsa]:
    arquivo, midia = resolver_midia_global(raiz_global, id_global)
    if midia.tipo != "imagem":
        raise ValueError("O ativo selecionado não é uma imagem.")
    return arquivo, midia


def listar_imagens_globais(raiz_global: Path) -> list[MidiaGlobalAvulsa]:
    imagens: list[MidiaGlobalAvulsa] = []
    for categoria in CATEGORIAS_IMAGEM:
        for ficha in sorted((raiz_global / categoria).glob("*.json")):
            if ficha.stem.endswith(".licenca"):
                continue
            try:
                _, imagem = resolver_imagem_global(raiz_global, f"global:{categoria}:{ficha.stem}")
            except ValueError:
                continue
            imagens.append(imagem)
    return imagens


def listar_midias_globais(raiz_global: Path) -> list[MidiaGlobalAvulsa]:
    midias = listar_imagens_globais(raiz_global)
    for ficha in sorted((raiz_global / CATEGORIA_CLIPE).glob("*.json")):
        if ficha.stem.endswith(".licenca"):
            continue
        try:
            _, clipe = resolver_midia_global(raiz_global, f"global:loops:{ficha.stem}")
        except ValueError:
            continue
        midias.append(clipe)
    return midias


def _pasta_selecao(raiz_projetos: Path, campanha_id: str, pedido_id: str) -> Path:
    if not re.fullmatch(r"[a-f0-9]{24}", campanha_id) or not re.fullmatch(r"A[0-9]{3,}", pedido_id):
        raise ValueError("Identificador de seleção inválido.")
    return raiz_projetos / "_campanhas_avulsas" / campanha_id / "midias" / pedido_id


def obter_selecao_midias(
    raiz_projetos: Path, campanha_id: str, pedido_id: str
) -> SelecaoMidiasAvulsa | None:
    pasta = _pasta_selecao(raiz_projetos, campanha_id, pedido_id)
    ponteiro = pasta / "atual.json"
    if not ponteiro.is_file():
        return None
    revisao = json.loads(ponteiro.read_text(encoding="utf-8"))["revisao"]
    if not isinstance(revisao, str) or not re.fullmatch(r"[a-f0-9]{64}", revisao):
        raise ValueError("Ponteiro de mídia inválido.")
    return SelecaoMidiasAvulsa.model_validate_json(
        (pasta / "revisoes" / f"{revisao}.json").read_text(encoding="utf-8")
    )


def selecao_vigente(raiz_global: Path, selecao: SelecaoMidiasAvulsa, revisao_roteiro: str) -> bool:
    if selecao.revisao_roteiro != revisao_roteiro:
        return False
    for midia in selecao.midias:
        try:
            _, atual = resolver_midia_global(raiz_global, midia.id_global)
        except ValueError:
            return False
        if atual != midia:
            return False
    return True


def selecionar_midias(
    raiz_projetos: Path,
    raiz_global: Path,
    campanha_id: str,
    pedido_id: str,
    ids_globais: list[str],
    hash_campanha: str,
    revisao_roteiro: str,
) -> SelecaoMidiasAvulsa:
    campanha = obter_campanha(raiz_projetos, campanha_id)
    if campanha.hash_conteudo != hash_campanha or not any(
        pedido.id == pedido_id for pedido in campanha.pedidos
    ):
        raise ValueError("Campanha ou pedido desatualizado.")
    aprovacao = obter_aprovacao_roteiro(raiz_projetos, campanha_id, pedido_id)
    if aprovacao is None or aprovacao.revisao != revisao_roteiro:
        raise ValueError("Aprove o roteiro atual antes de selecionar mídias.")
    if not 1 <= len(ids_globais) <= 20 or len(ids_globais) != len(set(ids_globais)):
        raise ValueError("Selecione de 1 a 20 mídias distintas.")
    midias = [resolver_midia_global(raiz_global, item)[1] for item in ids_globais]
    pedido = next(item for item in campanha.pedidos if item.id == pedido_id)
    imagens = [item for item in midias if item.tipo == "imagem"]
    clipes = [item for item in midias if item.tipo == "clipe"]
    if not imagens:
        raise ValueError("Selecione ao menos uma imagem para gancho e capa.")
    if pedido.objetivo == "bastidores":
        if len(clipes) != 3 or len({item.hash_arquivo for item in clipes}) != 3:
            raise ValueError("Bastidores exige três clipes distintos e licenciados.")
    elif clipes:
        raise ValueError("Clipes são aceitos somente em bastidores.")
    revisao = calcular_hash_dados(
        {
            "campanha": hash_campanha,
            "pedido": pedido_id,
            "roteiro": revisao_roteiro,
            "midias": [midia.model_dump(mode="json") for midia in midias],
        }
    )
    selecao = SelecaoMidiasAvulsa(
        campanha_id=campanha_id,
        pedido_id=pedido_id,
        hash_campanha=hash_campanha,
        revisao_roteiro=revisao_roteiro,
        revisao=revisao,
        midias=midias,
    )
    pasta = _pasta_selecao(raiz_projetos, campanha_id, pedido_id)
    arquivo = pasta / "revisoes" / f"{revisao}.json"
    if arquivo.is_file():
        existente = SelecaoMidiasAvulsa.model_validate_json(arquivo.read_text(encoding="utf-8"))
        if existente != selecao:
            raise RuntimeError("Colisão de revisão de mídia; nada foi sobrescrito.")
    else:
        atomic_write_json(arquivo, selecao.model_dump(mode="json"))
    atomic_write_json(pasta / "atual.json", {"revisao": revisao})
    return selecao
