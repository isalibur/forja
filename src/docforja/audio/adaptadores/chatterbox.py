from __future__ import annotations

import subprocess
from pathlib import Path

from docforja.audio.adaptadores.base import AdaptadorTTS


class AdaptadorChatterbox(AdaptadorTTS):
    """Adaptador para o Chatterbox TTS pt-BR, sem trocar de motor silenciosamente."""

    def __init__(self, python_path: Path | None = None) -> None:
        self.python_path = python_path

    def disponivel(self) -> bool:
        return self.python_path is not None and self.python_path.is_file()

    def gerar(
        self,
        texto: str,
        saida_wav: Path,
        voz: str | None = None,
        idioma: str = "pt-BR",
        velocidade: float = 1.0,
    ) -> Path:
        if not self.disponivel():
            raise RuntimeError("Chatterbox não disponível: configure o executável do ambiente.")

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
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if res.returncode != 0:
            raise RuntimeError(f"Falha ao sintetizar com Chatterbox: {res.stderr.strip()}")
        if not saida_wav.is_file():
            raise FileNotFoundError(
                f"Chatterbox executou mas não criou o arquivo de saída: {saida_wav}"
            )
        return saida_wav
