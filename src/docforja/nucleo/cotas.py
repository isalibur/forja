"""Gerenciamento de cotas de LLM com fallback automático para Ollama."""

from __future__ import annotations

import threading
from datetime import UTC, datetime, timedelta
from typing import Any

from docforja.nucleo.eventos import Evento, barramento_global


class GerenciadorCotas:
    """Rastreia consumo de requisições/tokens e gerencia fallback para o Ollama local."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.esgotados_ate: dict[str, datetime] = {}
        self.requisicoes_hoje: dict[str, int] = {}
        self.tokens_hoje: dict[str, int] = {}
        self.limites_diarios: dict[str, int] = {
            "openai_compat": 500,  # 9Router
            "openrouter": 200,
            "ollama": 100000,
        }

    def registrar_sucesso(self, provedor: str, tokens: int = 0) -> None:
        with self._lock:
            self.requisicoes_hoje[provedor] = self.requisicoes_hoje.get(provedor, 0) + 1
            self.tokens_hoje[provedor] = self.tokens_hoje.get(provedor, 0) + tokens
            barramento_global.emitir(
                Evento(
                    projeto="sistema",
                    tipo="cota_status",
                    dados={
                        "provedor": provedor,
                        "requisicoes": self.requisicoes_hoje[provedor],
                        "limite": self.limites_diarios.get(provedor, 0),
                        "fallback_ativo": False,
                    },
                )
            )

    def registrar_esgotamento(self, provedor: str, duracao_minutos: int = 60) -> None:
        """Marca provedor como esgotado temporariamente para acionar fallback."""
        with self._lock:
            expira = datetime.now(UTC) + timedelta(minutes=duracao_minutos)
            self.esgotados_ate[provedor] = expira
            barramento_global.emitir(
                Evento(
                    projeto="sistema",
                    tipo="cota_status",
                    dados={
                        "provedor": provedor,
                        "status": "esgotado",
                        "fallback_ativo": True,
                        "retorno_em": expira.isoformat(),
                    },
                )
            )

    def esta_disponivel(self, provedor: str) -> bool:
        with self._lock:
            expira = self.esgotados_ate.get(provedor)
            if expira:
                if datetime.now(UTC) < expira:
                    return False
                del self.esgotados_ate[provedor]
            limite = self.limites_diarios.get(provedor, 0)
            return not (limite and self.requisicoes_hoje.get(provedor, 0) >= limite)

    def selecionar_ativo(self, preferencial: str = "openai_compat") -> tuple[str, bool]:
        """Retorna o provedor a ser utilizado e se o fallback para Ollama está ativo."""
        if self.esta_disponivel(preferencial):
            return preferencial, False
        return "ollama", True

    def obter_resumo(self) -> dict[str, Any]:
        with self._lock:
            return {
                "requisicoes": dict(self.requisicoes_hoje),
                "tokens": dict(self.tokens_hoje),
                "limites": dict(self.limites_diarios),
                "esgotados": {k: v.isoformat() for k, v in self.esgotados_ate.items()},
            }


# Instância global de cotas
gerenciador_cotas = GerenciadorCotas()
