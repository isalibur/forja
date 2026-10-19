"""Roteador de chamadas LLM com 9Router (principal), fallback Ollama e reparo de JSON."""

from __future__ import annotations

import os
from typing import Any, TypeVar

import litellm
from pydantic import BaseModel

from docforja.llm.reparo import validar_ou_reparar
from docforja.nucleo.cotas import gerenciador_cotas
from docforja.settings import AppSettings, load_settings

T = TypeVar("T", bound=BaseModel)

# Desabilita telemetria e ruído do litellm
litellm.telemetry = False
litellm.suppress_debug_info = True


class RoteadorLLM:
    """Roteador inteligente de requisições de linguagem."""

    def __init__(self, settings: AppSettings | None = None) -> None:
        self.settings = settings or load_settings()

    def _obter_config_tier(self, tier: str) -> tuple[str, str, str, str]:
        """Retorna (provedor, model_name_litellm, base_url, api_key)."""
        cfg = self.settings.llm.get(tier)
        provedor = cfg.provedor if cfg else ("ollama" if tier == "local" else "openai_compat")
        base_url = (
            cfg.base_url
            if cfg
            else ("http://127.0.0.1:11434" if provedor == "ollama" else "http://127.0.0.1:20128/v1")
        )
        modelo_base = cfg.modelo if cfg else ("qwen3:8b" if provedor == "ollama" else "default")

        # Lê variáveis de ambiente se disponíveis
        api_key = os.getenv("NINEROUTER_API_KEY", "dummy")
        if provedor == "openai_compat":
            combo = os.getenv("NINEROUTER_COMBO")
            modelo = combo if combo else modelo_base
            base_url = os.getenv("NINEROUTER_BASE_URL", base_url)
            model_litellm = f"openai/{modelo}"
        elif provedor == "ollama":
            model_litellm = f"ollama/{modelo_base}"
            api_key = "ollama"
        else:
            model_litellm = f"{provedor}/{modelo_base}"

        return provedor, model_litellm, base_url, api_key

    def completar_texto(
        self,
        prompt: str,
        sistema: str = "",
        tier: str = "structured",
        temperature: float = 0.2,
    ) -> str:
        """Executa geração de texto com fallback automático entre 9Router e Ollama."""
        _provedor_escolhido, fallback_ativo = gerenciador_cotas.selecionar_ativo(
            preferencial="openai_compat" if tier == "structured" else "ollama"
        )

        tier_efetivo = "local" if (fallback_ativo or tier == "local") else tier
        provedor, model_name, base_url, api_key = self._obter_config_tier(tier_efetivo)

        messages = []
        if sistema:
            messages.append({"role": "system", "content": sistema})
        messages.append({"role": "user", "content": prompt})

        try:
            response = litellm.completion(
                model=model_name,
                messages=messages,
                api_base=base_url,
                api_key=api_key,
                temperature=temperature,
                timeout=90.0,
            )
            conteudo = response.choices[0].message.content or ""
            tokens = getattr(getattr(response, "usage", None), "total_tokens", 0)
            gerenciador_cotas.registrar_sucesso(provedor, tokens=tokens)
            return conteudo
        except Exception as exc:
            # Se falhou no 9Router / OpenAI compatível, registra esgotamento e tenta Ollama local
            if tier_efetivo == "structured":
                gerenciador_cotas.registrar_esgotamento(provedor, duracao_minutos=30)
                _, fallback_model, fallback_base, fallback_key = self._obter_config_tier("local")
                fb_resp = litellm.completion(
                    model=fallback_model,
                    messages=messages,
                    api_base=fallback_base,
                    api_key=fallback_key,
                    temperature=temperature,
                    timeout=120.0,
                )
                gerenciador_cotas.registrar_sucesso("ollama")
                return fb_resp.choices[0].message.content or ""
            raise exc

    def completar_estruturado(
        self,
        prompt: str,
        schema: type[T],
        sistema: str = "",
        tier: str = "structured",
        exemplos: dict[str, Any] | None = None,
    ) -> T:
        """Gera resposta e valida estritamente contra o esquema Pydantic com suporte a reparo."""
        schema_json_desc = schema.model_json_schema()
        instrucao_formato = (
            f"\n\nResponda ESTRITAMENTE em formato JSON que obedeça a este esquema:\n"
            f"{schema_json_desc}\n"
            f"Não inclua nenhuma explicação antes ou depois do JSON."
        )
        prompt_completo = prompt + instrucao_formato

        def _reparo_via_ollama(prompt_reparo: str, schema_name: str) -> str:
            return self.completar_texto(
                prompt=prompt_reparo,
                sistema="Validador de JSON. Retorne apenas JSON puro sem markdown ou texto extra.",
                tier="local",
                temperature=0.0,
            )

        resposta = self.completar_texto(
            prompt=prompt_completo,
            sistema=sistema,
            tier=tier,
            temperature=0.1,
        )

        return validar_ou_reparar(
            conteudo=resposta,
            modelo_schema=schema,
            funcao_reparo_llm=_reparo_via_ollama,
        )
