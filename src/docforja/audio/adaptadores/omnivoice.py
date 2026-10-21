"""Adaptador de síntese de voz (TTS) para o OmniVoice com voz clonada do usuário.

O OmniVoice (`k2-fsa/OmniVoice`, 613M) sintetiza a partir de um prompt de
clonagem já salvo pelo usuário (`.pt` com os tokens da referência). O motor e os
pesos são do upstream; o DocForja registra a origem e não bloqueia a produção.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from docforja.audio.adaptadores.base import AdaptadorTTS

WORKER = Path(__file__).resolve().parents[2] / "workers" / "omnivoice_worker.py"


class AdaptadorOmniVoice(AdaptadorTTS):
    """Síntese com voz clonada, chamando o worker OmniVoice no ambiente isolado."""

    def __init__(
        self,
        python_path: Path | None = None,
        prompt: Path | None = None,
        modelo_repo: str = "k2-fsa/OmniVoice",
        cache: Path | None = None,
        velocidade: float = 0.92,
        passos: int = 64,
        timeout_s: float = 900.0,
    ) -> None:
        self.python_path = python_path
        self.prompt = prompt
        self.modelo_repo = modelo_repo
        self.cache = cache
        self.velocidade = velocidade
        self.passos = passos
        self.timeout_s = timeout_s

    def disponivel(self) -> bool:
        """Só há motor quando o ambiente e o prompt de clonagem existem."""
        return bool(
            self.python_path
            and self.python_path.is_file()
            and self.prompt
            and self.prompt.is_file()
        )

    def termos_de_uso(self) -> dict[str, str]:
        """Registra a origem da voz (motor, prompt e referência do usuário)."""
        return {
            "motor": "omnivoice",
            "modelo": self.modelo_repo,
            "prompt_de_clonagem": str(self.prompt or ""),
            "origem": (
                "voz clonada a partir de uma referência do próprio usuário, com o consentimento "
                "do dono da voz guardado no kit"
            ),
        }

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
                "OmniVoice indisponível: configure o ambiente e o prompt de clonagem da voz."
            )
        comando = [
            str(self.python_path),
            str(WORKER),
            "--texto",
            texto,
            "--saida",
            str(saida_wav.resolve()),
            "--voz",
            str(self.prompt),
            "--modelo",
            self.modelo_repo,
            "--velocidade",
            str(self.velocidade),
            "--passos",
            str(self.passos),
        ]
        if self.cache:
            comando.extend(["--cache", str(self.cache)])
        resultado = subprocess.run(
            comando, capture_output=True, text=True, timeout=self.timeout_s, check=False
        )
        if resultado.returncode != 0:
            raise RuntimeError(
                f"Falha ao sintetizar com OmniVoice: {(resultado.stderr or '').strip()[-600:]}"
            )
        if not saida_wav.is_file():
            raise FileNotFoundError(
                f"OmniVoice executou mas não criou o arquivo de saída: {saida_wav}"
            )
        return saida_wav
