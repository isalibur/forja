from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class AdaptadorTTS(ABC):
    """Interface abstrata para adaptadores de sintese de voz (TTS) do DocForja."""

    @abstractmethod
    def gerar(
        self,
        texto: str,
        saida_wav: Path,
        voz: str | None = None,
        idioma: str = "pt-BR",
        velocidade: float = 1.0,
    ) -> Path:
        """Sintetiza o texto em um arquivo de áudio WAV."""
        ...

    @abstractmethod
    def disponivel(self) -> bool:
        """Verifica se o motor está instalado e operacional."""
        ...
