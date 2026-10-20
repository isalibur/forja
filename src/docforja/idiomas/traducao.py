"""Importação segura de roteiros traduzidos com IDs estáveis."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Protocol

import yaml
from pydantic import BaseModel

from docforja.io import atomic_write_json, atomic_write_text
from docforja.llm.roteador import RoteadorLLM
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


class SegmentoTraducaoLLM(BaseModel):
    id: str
    texto: str


class BlocoTraducaoLLM(BaseModel):
    bloco_id: str
    titulo: str
    segmentos: list[SegmentoTraducaoLLM]


class TradutorEstruturado(Protocol):
    def completar_estruturado(
        self, prompt: str, schema: type[BlocoTraducaoLLM], sistema: str = "", **kwargs: object
    ) -> BlocoTraducaoLLM: ...


def _ids_declarados(texto: str) -> list[str]:
    return re.findall(r"(?m)^\s*\*\*(B\d+-S\d+)(?:[^*]*)\*\*", texto)


def _marcas_tecnicas(texto: str) -> list[str]:
    padrao = r"\[PAUSA-[CML]\]|\[SILÊNCIO[^\]]*\]|>>VISUAL:.*?<<|(?<!\*)\*[^*\n]+\*(?!\*)"
    marcas = re.findall(padrao, texto, re.I | re.S)
    normalizadas: list[str] = []
    for marca in marcas:
        if marca.upper().startswith(">>VISUAL:"):
            normalizadas.append(">>VISUAL<<")
        elif marca.startswith("*"):
            normalizadas.append("*ÊNFASE*")
        else:
            normalizadas.append(marca.upper())
    return normalizadas


def _carregar_prompt_traducao() -> str:
    caminho = Path(__file__).resolve().parents[3] / "prompts" / "traducao.md.j2"
    return caminho.read_text(encoding="utf-8")


def _renderizar_prompt(template: str, valores: dict[str, str]) -> str:
    prompt = template
    for chave, valor in valores.items():
        prompt = prompt.replace("{{ " + chave + " }}", valor)
    return prompt


def _traduzir_automaticamente(
    roteiro_origem: str,
    idioma_origem: str,
    idioma_destino: str,
    glossario: object,
    roteador: TradutorEstruturado,
) -> str:
    template = _carregar_prompt_traducao()
    partes: list[str] = []
    for bloco in ler_roteiro_formatado(roteiro_origem):
        dados_bloco = {
            "bloco_id": bloco.id,
            "titulo": bloco.nome,
            "segmentos": [
                {"id": segmento.id, "texto": segmento.texto_original}
                for segmento in bloco.segmentos
            ],
        }
        prompt = _renderizar_prompt(
            template,
            {
                "idioma_origem": idioma_origem,
                "idioma_destino": idioma_destino,
                "glossario": yaml.safe_dump(glossario, allow_unicode=True, sort_keys=True),
                "bloco_json": json.dumps(dados_bloco, ensure_ascii=False, indent=2),
            },
        )
        resposta = roteador.completar_estruturado(
            prompt=prompt,
            schema=BlocoTraducaoLLM,
            sistema="Tradutor profissional de documentários. Retorne somente dados estruturados.",
            tier="structured",
        )
        ids_esperados = [segmento.id for segmento in bloco.segmentos]
        if resposta.bloco_id != bloco.id or [s.id for s in resposta.segmentos] != ids_esperados:
            raise ValueError(f"A tradução automática alterou os IDs do bloco {bloco.id}.")
        titulo = re.sub(r"[\r\n]+", " ", resposta.titulo).strip() or bloco.nome
        partes.append(f"## {bloco.id} — {titulo}")
        for segmento in resposta.segmentos:
            partes.append(f"**{segmento.id}** {segmento.texto.strip()}")
        partes.append("")
    traducao = "\n".join(partes).strip() + "\n"
    validar_traducao(roteiro_origem, traducao, idioma_destino)
    return traducao


def _resultado_em_cache(
    pasta_saida: Path, idioma: str, hash_entrada: str
) -> RoteiroTraduzido | None:
    indice = pasta_saida / idioma / "atual.json"
    if not indice.is_file():
        return None
    dados_indice = json.loads(indice.read_text(encoding="utf-8"))
    if dados_indice.get("hash_entrada") != hash_entrada:
        return None
    nome_versao = str(dados_indice.get("versao", ""))
    if not re.fullmatch(r"roteiro_[0-9a-f]{16}\.json", nome_versao):
        return None
    versao = pasta_saida / idioma / nome_versao
    if not versao.is_file():
        return None
    return RoteiroTraduzido.model_validate_json(versao.read_text(encoding="utf-8"))


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
                    "A tradução alterou pausas, silêncios, ênfases ou VISUAL em "
                    f"{segmento_origem.id}."
                )
    return RoteiroTraduzido(
        idioma=idioma,
        hash_roteiro_origem=hashlib.sha256(roteiro_origem.encode("utf-8")).hexdigest(),
        hash_traducao=hashlib.sha256(traducao.encode("utf-8")).hexdigest(),
        segmentos=segmentos,
    )


def executar_traducao_projeto(
    projeto: Projeto, roteador: TradutorEstruturado | None = None
) -> dict[str, RoteiroTraduzido]:
    """Exporta modelos manuais e importa arquivos existentes, sem tocar na entrada."""
    opcoes = projeto.obter_opcoes()
    extras = opcoes.get("idiomas", {}).get("extras", [])
    if not extras:
        return {}
    modos = opcoes.get("traducao", {}).get("modos", {})
    roteiro_origem = projeto.obter_roteiro()
    idioma_origem = opcoes.get("idiomas", {}).get("principal", "pt-BR")
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
            hash_entrada = hashlib.sha256(
                json.dumps(
                    {
                        "roteiro": roteiro_origem,
                        "idioma_origem": idioma_origem,
                        "idioma_destino": idioma,
                        "glossario": glossario,
                        "prompt": _carregar_prompt_traducao(),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ).encode("utf-8")
            ).hexdigest()
            em_cache = _resultado_em_cache(pasta_saida, idioma, hash_entrada)
            if em_cache is not None:
                resultados[idioma] = em_cache
                continue
            tradutor = roteador or RoteadorLLM()
            texto_traduzido = _traduzir_automaticamente(
                roteiro_origem, idioma_origem, idioma, glossario, tradutor
            )
            traduzido = validar_traducao(roteiro_origem, texto_traduzido, idioma)
            destino = pasta_saida / idioma
            versao = f"roteiro_{traduzido.hash_traducao[:16]}.json"
            if not (destino / versao).is_file():
                atomic_write_json(destino / versao, traduzido.model_dump(mode="json"))
            atomic_write_json(
                destino / "atual.json", {"versao": versao, "hash_entrada": hash_entrada}
            )
            resultados[idioma] = traduzido
            continue
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
        atomic_write_json(destino / "atual.json", {"versao": versao, "modo": modo})
        resultados[idioma] = traduzido
    if pendentes:
        raise FileNotFoundError("Traduções pendentes: " + "; ".join(pendentes))
    return resultados
