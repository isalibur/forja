from __future__ import annotations

import subprocess
from pathlib import Path

from docforja.audio.adaptadores.base import AdaptadorTTS
from docforja.audio.adaptadores.kokoro import AdaptadorKokoro


class AdaptadorChatterbox(AdaptadorTTS):
    """Adaptador para o Chatterbox TTS pt-BR com fallback transparente para Kokoro."""

    def __init__(self, python_path: Path | None = None) -> None:
        self.python_path = python_path
        self._fallback = AdaptadorKokoro()

    def disponivel(self) -> bool:
        if self.python_path and self.python_path.exists():
            return True
        return self._fallback.disponivel()

    def gerar(
        self,
        texto: str,
        saida_wav: Path,
        voz: str | None = None,
        idioma: str = "pt-BR",
        velocidade: float = 1.0,
    ) -> Path:
        # Se nao houver ambiente exclusivo configurado para o Chatterbox, redireciona para o Kokoro
        if not (self.python_path and self.python_path.exists()):
            return self._fallback.gerar(texto, saida_wav, voz, idioma, velocidade)

        # Se houver comando chatterbox configurado
        cmd = [
            str(self.python_path),
            "-m",
            "chatterbox",
            "--text",
            texto,
            "--output",
            str(saida_wav.resolve()),
        ]
        res = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120
        )
        if res.returncode != 0:
            # Fallback para Kokoro em caso de erro no Chatterbox
            return self._fallback.gerar(texto, saida_wav, voz, idioma, velocidade)
        return saida_wav
