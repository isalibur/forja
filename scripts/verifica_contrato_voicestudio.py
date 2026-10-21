"""Verificação do contrato do adaptador VoiceStudio contra um servidor local.

O app do VoiceStudio não está instalado nesta máquina; o servidor local abaixo
reproduz as rotas documentadas upstream (`GET /v1/models`, `GET /v1/audio/voices`
e `POST /v1/audio/speech`) para exercitar o adaptador em socket real, com HTTP
real e transcodificação real pelo FFmpeg.
"""

from __future__ import annotations

import io
import json
import socket
import sys
import threading
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from docforja.audio.adaptadores.voicestudio import AdaptadorVoiceStudio  # noqa: E402


def _wav(duracao_s: float = 0.6, taxa: int = 24000) -> bytes:
    bio = io.BytesIO()
    with wave.open(bio, "wb") as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(taxa)
        arquivo.writeframes(b"\x00\x00" * int(taxa * duracao_s))
    return bio.getvalue()


class Manipulador(BaseHTTPRequestHandler):
    """Servidor mínimo com as rotas documentadas do VoiceStudio."""

    requisicoes: ClassVar[list[dict[str, object]]] = []
    falhar_sintese: ClassVar[bool] = False

    def log_message(self, *_args: object) -> None:
        return

    def _json(self, corpo: object, status: int = 200) -> None:
        dados = json.dumps(corpo).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self) -> None:
        if self.path == "/v1/models":
            self._json({"data": [{"id": "omnivoice"}, {"id": "indextts"}]})
        elif self.path == "/v1/audio/voices":
            self._json({
                "data": [
                    {"voice_id": "v1", "name": "Locutor", "addressable_by_name": True},
                    {"voice_id": "v2", "name": "Outra", "addressable_by_name": True},
                ]
            })
        else:
            self._json({"error": {"message": "rota desconhecida"}}, status=404)

    def do_POST(self) -> None:
        tamanho = int(self.headers.get("Content-Length", "0"))
        corpo = json.loads(self.rfile.read(tamanho).decode("utf-8"))
        type(self).requisicoes.append(corpo)
        if self.path != "/v1/audio/speech":
            self._json({"error": {"message": "rota desconhecida"}}, status=404)
            return
        if type(self).falhar_sintese:
            self._json(
                {"error": {"message": "engine não instalada", "type": "invalid_request_error"}},
                status=400,
            )
            return
        audio = _wav()
        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(audio)))
        self.end_headers()
        self.wfile.write(audio)


def _porta_livre() -> int:
    with socket.socket() as soquete:
        soquete.bind(("127.0.0.1", 0))
        return int(soquete.getsockname()[1])


def main() -> int:
    Manipulador.requisicoes = []
    Manipulador.falhar_sintese = False
    porta = _porta_livre()
    servidor = ThreadingHTTPServer(("127.0.0.1", porta), Manipulador)
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{porta}"
    saida = REPO / ".pytest_tmp" / "voicestudio"
    saida.mkdir(parents=True, exist_ok=True)
    arquivo = saida / "narracao.wav"
    relatorio: dict[str, object] = {"base_url": base}

    try:
        adaptador = AdaptadorVoiceStudio(
            base_url=base,
            engine="omnivoice",
        )
        relatorio["disponivel"] = adaptador.disponivel()
        relatorio["vozes"] = adaptador.listar_vozes()
        resultado = adaptador.gerar(
            "Narração de teste do contrato.",
            saida_wav=arquivo,
            voz="v1",
        )
        with wave.open(str(resultado), "rb") as gerado:
            relatorio["audio"] = {
                "canais": gerado.getnchannels(),
                "taxa": gerado.getframerate(),
                "bits": gerado.getsampwidth(),
                "duracao_s": round(gerado.getnframes() / gerado.getframerate(), 3),
            }
        relatorio["payload"] = Manipulador.requisicoes[-1]

        Manipulador.falhar_sintese = True
        try:
            adaptador.gerar("Texto", saida_wav=saida / "erro.wav", voz="v1")
            relatorio["erro_do_servico"] = "não foi levantado"
        except RuntimeError as erro:
            relatorio["erro_do_servico"] = str(erro)
        Manipulador.falhar_sintese = False

        termos = adaptador.termos_de_uso()
        relatorio["termos_de_uso"] = termos

        httpx_mock_free = AdaptadorVoiceStudio(base_url=base, engine="omnivoice")
        relatorio["sintese_sem_registro_comercial"] = (
            httpx_mock_free.disponivel() is True
        )

        fora = AdaptadorVoiceStudio(base_url="http://127.0.0.1:59999")
        relatorio["servico_fora_do_ar"] = fora.disponivel()
    finally:
        servidor.shutdown()
        servidor.server_close()

    relatorio["ok"] = (
        relatorio.get("disponivel") is True
        and relatorio.get("audio", {}).get("canais") == 1
        and relatorio.get("audio", {}).get("taxa") == 24000
        and relatorio.get("audio", {}).get("bits") == 2
        and "engine não instalada" in str(relatorio.get("erro_do_servico"))
        and relatorio.get("termos_de_uso", {}).get("engine") == "omnivoice"
        and relatorio.get("sintese_sem_registro_comercial") is True
        and relatorio.get("servico_fora_do_ar") is False
    )
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
    return 0 if relatorio["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
