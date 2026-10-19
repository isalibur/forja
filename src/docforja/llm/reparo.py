"""Extração, validação e reparo de JSON para esquemas Pydantic."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


def extrair_bloco_json(texto: str) -> str:
    """Extrai o bloco JSON mais provável de uma resposta com markdown ou texto livre."""
    texto = texto.strip()

    # Bloco markdown ```json ... ```
    match_codeblock = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", texto, re.IGNORECASE)
    if match_codeblock:
        candidato = match_codeblock.group(1).strip()
        if (candidato.startswith("{") and candidato.endswith("}")) or (
            candidato.startswith("[") and candidato.endswith("]")
        ):
            return candidato

    # Busca delimitadores externos { ... } ou [ ... ]
    match_obj = re.search(r"(\{[\s\S]*\})", texto)
    if match_obj:
        return match_obj.group(1).strip()

    match_arr = re.search(r"(\[[\s\S]*\])", texto)
    if match_arr:
        return match_arr.group(1).strip()

    return texto


def sanitizar_json_leniente(texto_json: str) -> str:
    """Aplica correções comuns em JSONs malformados por LLMs."""
    # Remove vírgulas sobressalentes antes de fechamento de objeto ou lista: , } -> }
    s = re.sub(r",\s*(\}|\])", r"\1", texto_json)
    # Substitui aspas simples soltas se parecer chave de dicionário
    s = re.sub(r"\'(\w+)\'\s*:", r'"\1":', s)
    return s


def validar_ou_reparar(
    conteudo: str,
    modelo_schema: type[T],
    funcao_reparo_llm: Callable[[str, str], str] | None = None,
) -> T:
    """Valida o conteúdo gerado contra o modelo Pydantic, com sanitização e reparo se necessário."""
    bloco = extrair_bloco_json(conteudo)

    # 1ª tentativa: JSON direto
    try:
        return modelo_schema.model_validate_json(bloco)
    except (ValidationError, ValueError) as prim_erro:
        erro_desc = str(prim_erro)

    # 2ª tentativa: Sanitização leniente
    try:
        sanitizado = sanitizar_json_leniente(bloco)
        return modelo_schema.model_validate_json(sanitizado)
    except (ValidationError, ValueError):
        pass

    # 3ª tentativa: Reparo via LLM local (Ollama) se função de reparo estiver disponível
    if funcao_reparo_llm:
        prompt_reparo = (
            f"O JSON abaixo deveria seguir o schema '{modelo_schema.__name__}', "
            f"mas gerou o erro:\n{erro_desc}\n\n"
            f"JSON QUEBRADO:\n{bloco}\n\n"
            f"Corrija os erros e retorne APENAS o JSON corrigido, sem explicações."
        )
        resposta_reparo = funcao_reparo_llm(prompt_reparo, modelo_schema.__name__)
        bloco_reparado = extrair_bloco_json(resposta_reparo)
        return modelo_schema.model_validate_json(bloco_reparado)

    raise ValueError(f"Não foi possível validar JSON contra {modelo_schema.__name__}: {erro_desc}")
