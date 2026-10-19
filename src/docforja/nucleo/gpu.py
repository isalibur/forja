"""Semáforo de GPU com agrupamento inteligente por modelo e descarregamento."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable, Iterator
from contextlib import asynccontextmanager, contextmanager, suppress
from typing import Any

from docforja.nucleo.eventos import Evento, barramento_global


class SemaforoGPU:
    """Gerencia acesso exclusivo à GPU RTX 3060 (12 GB) e agrupamento de modelos."""

    def __init__(self) -> None:
        self._loop_locks: dict[asyncio.AbstractEventLoop, asyncio.Lock] = {}
        self._thread_lock = threading.Lock()
        self.modelo_atual: str | None = None
        self.tarefa_atual: str | None = None
        self.fila_pendente: list[str] = []
        self._descarregadores: dict[str, Callable[[], Any]] = {}

    def _get_async_lock(self) -> asyncio.Lock:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.Lock()
        if loop not in self._loop_locks:
            self._loop_locks[loop] = asyncio.Lock()
        return self._loop_locks[loop]

    def registrar_descarregador(self, modelo: str, callback: Callable[[], Any]) -> None:
        """Registra callback específico para liberar VRAM de um modelo."""
        self._descarregadores[modelo] = callback

    def _descarregar_se_necessario(self, novo_modelo: str | None) -> None:
        """Se o modelo solicitado for diferente do modelo carregado, descarrega o anterior."""
        if self.modelo_atual and novo_modelo and self.modelo_atual != novo_modelo:
            descarregador = self._descarregadores.get(self.modelo_atual)
            if descarregador:
                with suppress(Exception):
                    descarregador()
            self.modelo_atual = None

    @asynccontextmanager
    async def adquirir(
        self,
        modelo: str | None = None,
        tarefa: str = "",
        projeto: str = "sistema",
    ) -> Iterator[None]:
        """Adquire a GPU assincronamente com controle de modelo carregado."""
        if tarefa:
            self.fila_pendente.append(tarefa)
        try:
            async with self._get_async_lock():
                with self._thread_lock:
                    if tarefa in self.fila_pendente:
                        self.fila_pendente.remove(tarefa)
                    self._descarregar_se_necessario(modelo)
                    self.modelo_atual = modelo
                    self.tarefa_atual = tarefa
                    barramento_global.emitir(
                        Evento(
                            projeto=projeto,
                            tipo="gpu_status",
                            dados={"status": "ocupada", "modelo": modelo, "tarefa": tarefa},
                        )
                    )
                try:
                    yield
                finally:
                    with self._thread_lock:
                        self.tarefa_atual = None
                        barramento_global.emitir(
                            Evento(
                                projeto=projeto,
                                tipo="gpu_status",
                                dados={"status": "ociosa", "modelo": self.modelo_atual},
                            )
                        )
        finally:
            if tarefa in self.fila_pendente:
                self.fila_pendente.remove(tarefa)

    @contextmanager
    def adquirir_sync(
        self,
        modelo: str | None = None,
        tarefa: str = "",
        projeto: str = "sistema",
    ) -> Iterator[None]:
        """Versão síncrona para workers e scripts que não rodam em loop asyncio."""
        with self._thread_lock:
            self._descarregar_se_necessario(modelo)
            self.modelo_atual = modelo
            self.tarefa_atual = tarefa
            barramento_global.emitir(
                Evento(
                    projeto=projeto,
                    tipo="gpu_status",
                    dados={"status": "ocupada", "modelo": modelo, "tarefa": tarefa},
                )
            )
            try:
                yield
            finally:
                self.tarefa_atual = None
                barramento_global.emitir(
                    Evento(
                        projeto=projeto,
                        tipo="gpu_status",
                        dados={"status": "ociosa", "modelo": self.modelo_atual},
                    )
                )

    def obter_status(self) -> dict[str, Any]:
        with self._thread_lock:
            return {
                "ocupada": self.tarefa_atual is not None,
                "modelo_atual": self.modelo_atual,
                "tarefa_atual": self.tarefa_atual,
                "fila_tamanho": len(self.fila_pendente),
            }


# Instância global do semáforo da máquina
semaforo_gpu = SemaforoGPU()
