"""Adaptador de síntese de voz (TTS) para o VoiceStudio com checagem de licença comercial.

O VoiceStudio expõe a síntese em `POST {raiz}/v1/audio/speech`, no mesmo formato
do endpoint de fala da OpenAI: `model` é a engine instalada, `voice` é o perfil
de voz (id ou nome) e `input` é o texto. O serviço roda separado (app AGPL) e
jamais é embutido no DocForja.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

import httpx

from docforja.audio.adaptadores.base import AdaptadorTTS

CAMINHO_SINTESE = "/v1/audio/speech"
CAMINHO_MODELOS = "/v1/models"
CAMINHO_VOZES = "/v1/audio/voices"


class AdaptadorVoiceStudio(AdaptadorTTS):
    """Adaptador para a API local do VoiceStudio, com os termos da engine registrados."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:3900",
        engine: str = "omnivoice",
        api_key: str = "",
        instrucoes: str = "",
        timeout_s: float = 60.0,
        probe_timeout_s: float = 3.0,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.engine = engine
        self.api_key = api_key or os.environ.get("OMNIVOICE_API_KEY", "")
        self.instrucoes = instrucoes
        self.timeout_s = timeout_s
        self.probe_timeout_s = probe_timeout_s
        self.max_retries = max_retries

    def _cabecalhos(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    def termos_de_uso(self) -> dict[str, str]:
        """Registra a engine e a voz escolhidas; os termos vêm do app e do projeto."""
        return {
            "motor": "voicestudio",
            "engine": self.engine,
            "servidor": self.base_url,
            "origem_dos_pesos": (
                "baixados pelo app a partir do catálogo dele; os termos de uso do modelo e "
                "da saída são do upstream, não do DocForja"
            ),
        }

    def disponivel(self) -> bool:
        """Confere se o serviço local do VoiceStudio responde."""
        if not self.base_url.startswith("http"):
            return False
        try:
            resposta = httpx.get(
                f"{self.base_url}{CAMINHO_MODELOS}",
                timeout=self.probe_timeout_s,
                headers=self._cabecalhos(),
            )
        except httpx.HTTPError:
            return False
        return resposta.status_code < 500

    def listar_vozes(self) -> list[dict[str, object]]:
        """Lista os perfis de voz disponíveis no app (id, nome e endereçamento por nome)."""
        try:
            resposta = httpx.get(
                f"{self.base_url}{CAMINHO_VOZES}",
                timeout=self.timeout_s,
                headers=self._cabecalhos(),
            )
            resposta.raise_for_status()
            dados = resposta.json()
        except (httpx.HTTPError, ValueError) as erro:
            raise RuntimeError(f"Falha ao listar as vozes do VoiceStudio: {erro}") from erro
        vozes = dados.get("data", dados) if isinstance(dados, dict) else dados
        if not isinstance(vozes, list):
            raise RuntimeError("Resposta inesperada ao listar as vozes do VoiceStudio.")
        return [voz for voz in vozes if isinstance(voz, dict)]

    def _erro_formatado(self, resposta: httpx.Response) -> str:
        try:
            corpo = resposta.json()
        except ValueError:
            return resposta.text[:400] or f"HTTP {resposta.status_code}"
        if isinstance(corpo, dict):
            erro = corpo.get("error")
            if isinstance(erro, dict) and erro.get("message"):
                return str(erro["message"])
            if isinstance(erro, str):
                return erro
            if corpo.get("detail"):
                return str(corpo["detail"])
        return str(corpo)[:400]

    def gerar(
        self,
        texto: str,
        saida_wav: Path,
        voz: str | None = None,
        idioma: str = "pt-BR",
        velocidade: float = 1.0,
    ) -> Path:
        """Sintetiza áudio via VoiceStudio e padroniza para WAV 24 kHz mono."""
        if not self.disponivel():
            raise RuntimeError(
                f"O VoiceStudio não respondeu em {self.base_url}. Abra o app e tente de novo."
            )

        payload: dict[str, object] = {
            "model": self.engine,
            "voice": voz or "default",
            "input": texto,
            "response_format": "wav",
            "speed": velocidade,
        }
        if self.instrucoes:
            payload["instructions"] = self.instrucoes
        endpoint = f"{self.base_url}{CAMINHO_SINTESE}"

        tentativas = 0
        ultimo_erro: Exception | None = None
        conteudo_audio: bytes | None = None

        with httpx.Client(timeout=self.timeout_s) as cliente:
            while tentativas < self.max_retries:
                tentativas += 1
                try:
                    resp = cliente.post(
                        endpoint, json=payload, headers=self._cabecalhos()
                    )
                    if resp.status_code >= 400:
                        raise RuntimeError(
                            f"VoiceStudio recusou a síntese: {self._erro_formatado(resp)}"
                        )
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
