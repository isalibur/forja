"""Barramento de eventos do DocForja com persistência JSONL e suporte a SSE."""

from __future__ import annotations

import asyncio
import contextlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class Evento(BaseModel):
    """Evento emitido pelo ciclo de vida do DocForja."""

    projeto: str
    tipo: str
    etapa_id: str | None = None
    subetapa_id: str | None = None
    dados: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class BarramentoEventos:
    """Gerenciador de eventos local e publicação para ouvintes assíncronos."""

    def __init__(self, caminho_jsonl: Path | None = None) -> None:
        self.caminho_jsonl = caminho_jsonl
        if self.caminho_jsonl:
            self.caminho_jsonl.parent.mkdir(parents=True, exist_ok=True)
        self._ouvintes: set[asyncio.Queue[Evento]] = set()

    def registrar_ouvinte(self) -> asyncio.Queue[Evento]:
        fila: asyncio.Queue[Evento] = asyncio.Queue(maxsize=100)
        self._ouvintes.add(fila)
        return fila

    def remover_ouvinte(self, fila: asyncio.Queue[Evento]) -> None:
        self._ouvintes.discard(fila)

    def emitir(self, evento: Evento) -> None:
        """Grava evento em eventos.jsonl e despacha aos ouvintes ativos."""
        if self.caminho_jsonl:
            linha = evento.model_dump_json() + "\n"
            with self.caminho_jsonl.open("a", encoding="utf-8") as handle:
                handle.write(linha)

        for fila in list(self._ouvintes):
            with contextlib.suppress(asyncio.QueueFull):
                fila.put_nowait(evento)


# Instância global para eventos de sistema e status de GPU
barramento_global = BarramentoEventos()
