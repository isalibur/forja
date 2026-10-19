from __future__ import annotations

import subprocess
from pathlib import Path

from docforja.audio.adaptadores.base import AdaptadorTTS


class AdaptadorKokoro(AdaptadorTTS):
    def __init__(self, python_path: Path | None = None) -> None:
        self.python_path = python_path or Path("D:/IA/audio_factory/.venv/Scripts/python.exe")
        self.worker_path = Path("src/docforja/workers/kokoro_worker.py")

    def disponivel(self) -> bool:
        return self.python_path.exists() and self.worker_path.exists()

    def gerar(
        self,
        texto: str,
        saida_wav: Path,
        voz: str | None = None,
        idioma: str = "pt-BR",
        velocidade: float = 1.0,
    ) -> Path:
        if not self.disponivel():
            raise RuntimeError(
                f"Kokoro não disponível: python={self.python_path} worker={self.worker_path}"
            )

        cmd = [
            str(self.python_path),
            str(self.worker_path),
            "--texto",
            texto,
            "--saida",
            str(saida_wav.resolve()),
            "--lang",
            idioma,
            "--speed",
            str(velocidade),
        ]
        if voz:
            cmd.extend(["--voz", voz])

        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if res.returncode != 0:
            raise RuntimeError(f"Falha ao sintetizar com Kokoro: {res.stderr}")

        if not saida_wav.exists():
            raise FileNotFoundError(
                f"Kokoro executou mas o arquivo de saída não foi criado: {saida_wav}"
            )

        return saida_wav
