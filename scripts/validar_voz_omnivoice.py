"""Validação real do motor OmniVoice com a voz clonada: síntese, WER e duração."""

from __future__ import annotations

import json
import subprocess
import sys
import time
import wave
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from docforja.audio.adaptadores.omnivoice import AdaptadorOmniVoice  # noqa: E402
from docforja.audio.alinhamento import AlinhadorWhisperX  # noqa: E402
from docforja.audio.metricas import calcular_wer  # noqa: E402
from docforja.settings import load_settings  # noqa: E402

TEXTO = (
    "Um rio pode mudar de nome. O mesmo curso de água nasce com um nome pequeno e "
    "recebe outros ao passar por cidades e vilarejos. Só quando chega ao mar ele "
    "ganha o nome que o mundo costuma conhecer."
)


def main() -> int:
    destino = Path(r"E:\05_PROJETOS\forja\estudos-voz\validacao-omnivoice")
    destino.mkdir(parents=True, exist_ok=True)
    settings = load_settings()
    adaptador = AdaptadorOmniVoice(
        python_path=settings.resolver_ambiente("omnivoice"),
        prompt=Path(r"D:\IA\audio_factory\voices\nova_ref_7s.pt"),
        modelo_repo=settings.omnivoice.modelo,
        cache=Path(settings.omnivoice.cache) if settings.omnivoice.cache else None,
        velocidade=settings.omnivoice.velocidade,
        passos=settings.omnivoice.passos,
    )
    relatorio: dict[str, object] = {"disponivel": adaptador.disponivel()}
    if not adaptador.disponivel():
        print(json.dumps(relatorio, ensure_ascii=False, indent=2))
        return 1

    inicio = time.monotonic()
    wav = adaptador.gerar(TEXTO, destino / "narracao.wav", voz="nova_ref_7s")
    relatorio["segundos_sintese"] = round(time.monotonic() - inicio, 1)
    with wave.open(str(wav), "rb") as gerado:
        relatorio["duracao_s"] = round(gerado.getnframes() / gerado.getframerate(), 2)
        relatorio["taxa"] = gerado.getframerate()
        relatorio["canais"] = gerado.getnchannels()

    alinhador = AlinhadorWhisperX(
        python_path=settings.resolver_ambiente("whisperx"),
        modelo=settings.alinhamento.modelo_asr,
        modelo_alinhador=settings.alinhamento.modelo_alinhador,
    )
    asr_segmentos = destino / "asr_segmentos.json"
    alinhador.alinhar(wav, destino / "asr_palavras.json", asr_segmentos, idioma="pt")
    transcricao = " ".join(
        str(item.get("texto", "")) for item in json.loads(asr_segmentos.read_text("utf-8"))
    )
    relatorio["transcricao"] = transcricao
    relatorio["wer"] = round(calcular_wer(TEXTO, transcricao, idioma="pt-BR"), 4)
    relatorio["limite_wer"] = 0.02
    relatorio["aprovado"] = bool(relatorio["wer"] <= 0.02)

    medicao = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(wav), "-af", "ebur128=peak=true:framelog=quiet",
         "-f", "null", "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    import re

    integrado = re.search(r"\bI:\s*(-?[\d.]+)\s*LUFS", medicao.stderr)
    relatorio["lufs"] = float(integrado.group(1)) if integrado else None
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
    return 0 if relatorio["aprovado"] else 1


if __name__ == "__main__":
    sys.exit(main())
