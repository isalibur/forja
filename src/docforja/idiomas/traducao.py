"""Importação segura de roteiros traduzidos com IDs estáveis."""

from __future__ import annotations

import hashlib
import re

import yaml
from pydantic import BaseModel

from docforja.io import atomic_write_json, atomic_write_text
from docforja.nucleo.projeto import Projeto
from docforja.planejamento.leitura import ler_roteiro_formatado


class SegmentoTraduzido(BaseModel):
    id: str
    bloco: str
    texto_original: str
    texto_limpo: str


class RoteiroTraduzido(BaseModel):
    idioma: str
    hash_roteiro_origem: str
    hash_traducao: str
    segmentos: list[SegmentoTraduzido]


def _ids_declarados(texto: str) -> list[str]:
    return re.findall(r"(?m)^\s*\*\*(B\d+-S\d+)(?:[^*]*)\*\*", texto)


def _marcas_tecnicas(texto: str) -> list[str]:
    marcas = re.findall(r"\[PAUSA-[CML]\]|\[SILÊNCIO[^\]]*\]|>>VISUAL:.*?<<", texto, re.I | re.S)
    return [marca.upper() if not marca.upper().startswith(">>VISUAL:") else ">>VISUAL<<"
            for marca in marcas]


def validar_traducao(roteiro_origem: str, traducao: str, idioma: str) -> RoteiroTraduzido:
    """Exige os mesmos IDs, uma só vez e na mesma ordem; não reescreve o texto."""
    origem = ler_roteiro_formatado(roteiro_origem)
    blocos = ler_roteiro_formatado(traducao)
    ids_esperados = [segmento.id for bloco in origem for segmento in bloco.segmentos]
    ids_declarados = _ids_declarados(traducao)
    ids_lidos = [segmento.id for bloco in blocos for segmento in bloco.segmentos]
    estrutura_origem = [
        (bloco.id, segmento.id) for bloco in origem for segmento in bloco.segmentos
    ]
    estrutura_traducao = [
        (bloco.id, segmento.id) for bloco in blocos for segmento in bloco.segmentos
    ]
    if not ids_esperados:
        raise ValueError("Roteiro de origem sem segmentos identificados.")
    if (
        ids_declarados != ids_esperados
        or ids_lidos != ids_esperados
        or estrutura_traducao != estrutura_origem
    ):
        raise ValueError("A tradução deve manter todos os IDs exatamente uma vez e na mesma ordem.")
    segmentos = [
        SegmentoTraduzido(
            id=segmento.id,
            bloco=bloco.id,
            texto_original=segmento.texto_original,
            texto_limpo=segmento.texto_limpo,
        )
        for bloco in blocos for segmento in bloco.segmentos
    ]
    if any(not item.texto_limpo.strip() for item in segmentos):
        raise ValueError("A tradução contém segmento sem texto narrável.")
    for bloco_origem, bloco_traduzido in zip(origem, blocos, strict=True):
        for segmento_origem, segmento_traduzido in zip(
            bloco_origem.segmentos, bloco_traduzido.segmentos, strict=True
        ):
            if _marcas_tecnicas(segmento_origem.texto_original) != _marcas_tecnicas(
                segmento_traduzido.texto_original
            ):
                raise ValueError(
                    f"A tradução alterou pausas, silêncios ou VISUAL em {segmento_origem.id}."
                )
    return RoteiroTraduzido(
        idioma=idioma,
        hash_roteiro_origem=hashlib.sha256(roteiro_origem.encode("utf-8")).hexdigest(),
        hash_traducao=hashlib.sha256(traducao.encode("utf-8")).hexdigest(),
        segmentos=segmentos,
    )


def executar_traducao_projeto(projeto: Projeto) -> dict[str, RoteiroTraduzido]:
    """Exporta modelos manuais e importa arquivos existentes, sem tocar na entrada."""
    opcoes = projeto.obter_opcoes()
    extras = opcoes.get("idiomas", {}).get("extras", [])
    if not extras:
        return {}
    modos = opcoes.get("traducao", {}).get("modos", {})
    roteiro_origem = projeto.obter_roteiro()
    glossario_path = projeto.pastas.entrada / "glossario.yaml"
    glossario = yaml.safe_load(glossario_path.read_text(encoding="utf-8")) or {}
    pasta_saida = projeto.pastas.plano / "idiomas"
    resultados: dict[str, RoteiroTraduzido] = {}
    pendentes: list[str] = []
    for idioma in extras:
        if not re.fullmatch(r"[a-z]{2}(?:-[A-Z]{2})?", idioma):
            raise ValueError(f"Código de idioma inválido: {idioma}")
        modo = modos.get(idioma, "gemini_manual")
        if modo == "automatico":
            raise NotImplementedError("Tradução automática ainda não configurada no M7.")
        if modo not in {"gemini_manual", "arquivo"}:
            raise ValueError(f"Modo de tradução desconhecido para {idioma}: {modo}")
        entrada = projeto.pastas.entrada / f"traducao_{idioma}.md"
        if modo == "gemini_manual":
            hash_curto = hashlib.sha256(roteiro_origem.encode("utf-8")).hexdigest()[:12]
            modelo = pasta_saida / f"modelo_{idioma}_{hash_curto}.md"
            if not modelo.exists():
                guia = (
                    f"Traduza para {idioma}, mantendo exatamente os IDs, a ordem, blocos, "
                    "marcações de pausa, silêncio e VISUAL. Não acrescente segmentos.\n\n"
                    f"Glossário:\n```yaml\n{yaml.safe_dump(glossario, allow_unicode=True)}```\n\n"
                )
                atomic_write_text(modelo, guia + roteiro_origem)
        if not entrada.is_file():
            pendentes.append(f"{idioma}: coloque traducao_{idioma}.md em 00_entrada/")
            continue
        traduzido = validar_traducao(
            roteiro_origem, entrada.read_text(encoding="utf-8"), idioma
        )
        destino = pasta_saida / idioma
        versao = f"roteiro_{traduzido.hash_traducao[:16]}.json"
        if not (destino / versao).is_file():
            atomic_write_json(destino / versao, traduzido.model_dump(mode="json"))
        atomic_write_json(destino / "atual.json", {"versao": versao})
        resultados[idioma] = traduzido
    if pendentes:
        raise FileNotFoundError("Traduções pendentes: " + "; ".join(pendentes))
    return resultados
