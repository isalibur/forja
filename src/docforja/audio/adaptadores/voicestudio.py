"""Adaptador de síntese de voz (TTS) para o VoiceStudio com checagem de licença comercial."""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

import httpx

from docforja.audio.adaptadores.base import AdaptadorTTS

# Engines e modelos conhecidos no ecossistema de código aberto com licença restritiva (NC)
ENGINES_NAO_COMERCIAIS = {
    "f5-tts-nc",
    "xtts-v2-nc",
    "chatterbox-nc",
    "coqui-nc",
    "cosyvoice-nc",
}


class AdaptadorVoiceStudio(AdaptadorTTS):
    """Adaptador para a API local do VoiceStudio, protegido por portão de licença comercial."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        comercial_exigido: bool = True,
        timeout_s: float = 60.0,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.comercial_exigido = comercial_exigido
        self.timeout_s = timeout_s
        self.max_retries = max_retries

    def verificar_licenca_comercial(self, voz_ou_engine: str | None) -> None:
        """Bloqueia engines ou vozes NC quando o projeto for monetizado (AGENTS.md, Marco M7)."""
        if not self.comercial_exigido:
            return

        identificador = (voz_ou_engine or "").strip().lower()
        if not identificador:
            return

        if any(nc in identificador for nc in ("-nc", "_nc", "non-commercial", "cc-by-nc")):
            raise PermissionError(
                f"Bloqueio de licença comercial: a voz/engine '{voz_ou_engine}' no VoiceStudio "
                "possui licença não-comercial (NC), proibida para produções monetizadas."
            )

        if identificador in ENGINES_NAO_COMERCIAIS:
            raise PermissionError(
                f"Bloqueio de licença comercial: a engine '{voz_ou_engine}' no VoiceStudio "
                "não possui licença comercial aprovada para produção monetizada (AGENTS.md)."
            )

    def disponivel(self) -> bool:
        """Verifica se o endpoint do VoiceStudio está configurado."""
        return bool(self.base_url and self.base_url.startswith("http"))

    def gerar(
        self,
        texto: str,
        saida_wav: Path,
        voz: str | None = None,
        idioma: str = "pt-BR",
        velocidade: float = 1.0,
    ) -> Path:
        """Sintetiza áudio via VoiceStudio e padroniza para WAV 24 kHz mono."""
        # 1. Checagem obrigatória de licença comercial
        self.verificar_licenca_comercial(voz)

        if not self.disponivel():
            raise RuntimeError("URL base do serviço VoiceStudio não configurada.")

        endpoint = f"{self.base_url}/v1/synthesize"
        payload = {
            "text": texto,
            "voice": voz or "default",
            "language": idioma,
            "speed": velocidade,
            "output_format": "wav",
        }

        tentativas = 0
        ultimo_erro: Exception | None = None
        conteudo_audio: bytes | None = None

        with httpx.Client(timeout=self.timeout_s) as client:
            while tentativas < self.max_retries:
                tentativas += 1
                try:
                    resp = client.post(endpoint, json=payload)
                    resp.raise_for_status()
                    conteudo_audio = resp.content
                    break
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    ultimo_erro = e
                    if tentativas < self.max_retries:
                        time.sleep(0.5 * (2 ** (tentativas - 1)))

        if conteudo_audio is None:
            raise RuntimeError(
                f"Falha ao sintetizar com VoiceStudio após {tentativas} tentativas: {ultimo_erro}"
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
