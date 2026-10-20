"""Adaptador de síntese de voz (TTS) compatível com a API OpenAI (/v1/audio/speech)."""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

import httpx

from docforja.audio.adaptadores.base import AdaptadorTTS


class AdaptadorOpenAITTS(AdaptadorTTS):
    """Adaptador TTS que consome qualquer endpoint HTTP compatível com /v1/audio/speech."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:20128/v1",
        modelo: str = "default",
        api_key: str = "EMPTY",
        timeout_s: float = 60.0,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.modelo = modelo
        self.api_key = api_key
        self.timeout_s = timeout_s
        self.max_retries = max_retries

    def disponivel(self) -> bool:
        """Verifica se a URL base está configurada."""
        return bool(self.base_url and self.base_url.startswith("http"))

    def gerar(
        self,
        texto: str,
        saida_wav: Path,
        voz: str | None = None,
        idioma: str = "pt-BR",
        velocidade: float = 1.0,
    ) -> Path:
        """Sintetiza áudio via HTTP /v1/audio/speech e padroniza para WAV 24 kHz mono."""
        if not self.disponivel():
            raise RuntimeError("URL base do serviço OpenAI TTS não configurada.")

        endpoint = f"{self.base_url}/audio/speech"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.modelo,
            "input": texto,
            "voice": voz or "alloy",
            "speed": velocidade,
            "response_format": "wav",
        }

        tentativas = 0
        ultimo_erro: Exception | None = None
        conteudo_audio: bytes | None = None

        with httpx.Client(timeout=self.timeout_s) as client:
            while tentativas < self.max_retries:
                tentativas += 1
                try:
                    resp = client.post(endpoint, headers=headers, json=payload)
                    resp.raise_for_status()
                    conteudo_audio = resp.content
                    break
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    ultimo_erro = e
                    if tentativas < self.max_retries:
                        time.sleep(0.5 * (2 ** (tentativas - 1)))

        if conteudo_audio is None:
            raise RuntimeError(
                f"Falha ao sintetizar com OpenAI TTS após {tentativas} tentativas: {ultimo_erro}"
            )

        saida_wav.parent.mkdir(parents=True, exist_ok=True)
        temp_audio = saida_wav.with_suffix(".tmp.audio")
        temp_audio.write_bytes(conteudo_audio)

        # Transcodifica para padrão WAV mono 24 kHz 16-bit com FFmpeg
        ffmpeg_bin = shutil.which("ffmpeg")
        if ffmpeg_bin:
            cmd = [
                ffmpeg_bin,
                "-y",
                "-i",
                str(temp_audio),
                "-ar",
                "24000",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                str(saida_wav),
            ]
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0 and saida_wav.is_file() and saida_wav.stat().st_size > 0:
                temp_audio.unlink(missing_ok=True)
                return saida_wav

        shutil.move(temp_audio, saida_wav)
        return saida_wav
