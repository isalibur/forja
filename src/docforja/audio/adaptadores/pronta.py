from __future__ import annotations

import subprocess
from pathlib import Path

from docforja.audio.adaptadores.base import AdaptadorTTS


class AdaptadorNarracaoPronta(AdaptadorTTS):
    """Adaptador para narracao pronta gravada pelo usuario."""

    def __init__(self, arquivo_origem: Path) -> None:
        self.arquivo_origem = Path(arquivo_origem)

    def disponivel(self) -> bool:
        return self.arquivo_origem.exists()

    def gerar(
        self,
        texto: str,
        saida_wav: Path,
        voz: str | None = None,
        idioma: str = "pt-BR",
        velocidade: float = 1.0,
    ) -> Path:
        if not self.disponivel():
            raise FileNotFoundError(
                f"Arquivo de narração pronta não encontrado: {self.arquivo_origem}"
            )

        saida_wav.parent.mkdir(parents=True, exist_ok=True)

        # Padroniza a narracao fornecida para WAV mono 24kHz 16-bit
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(self.arquivo_origem),
            "-ar",
            "24000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(saida_wav),
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Erro ao processar narração pronta com FFmpeg: {res.stderr}")

        return saida_wav
