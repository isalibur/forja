from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline

LANG_MAP = {
    "pt-br": "p",
    "pt": "p",
    "p": "p",
    "en": "a",
    "en-us": "a",
    "a": "a",
    "en-gb": "b",
    "b": "b",
    "es": "e",
    "e": "e",
    "fr": "f",
    "f": "f",
    "it": "i",
    "i": "i",
}

VOZ_PADRAO = {
    "p": "pm_alex",
    "a": "af_heart",
    "b": "bf_emma",
    "e": "ef_dora",
}


def sintetizar(
    texto: str,
    saida_wav: Path,
    lang_code: str = "p",
    voice: str | None = None,
    speed: float = 1.0,
) -> None:
    code = LANG_MAP.get(lang_code.lower(), "p")
    selected_voice = voice or VOZ_PADRAO.get(code, "pm_alex")

    pipeline = KPipeline(lang_code=code)
    generator = pipeline(texto, voice=selected_voice, speed=speed)

    chunks = []
    for _, _, audio in generator:
        if audio is not None and len(audio) > 0:
            chunks.append(audio)

    if not chunks:
        # Gera silencio de fallback caso o texto seja vazio ou pontuacao pura
        audio_final = np.zeros(int(24000 * 0.5), dtype=np.float32)
    else:
        audio_final = np.concatenate(chunks)

    saida_wav.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(saida_wav), audio_final, 24000)


def main() -> None:
    parser = argparse.ArgumentParser(description="Worker Kokoro TTS para DocForja")
    parser.add_argument("--texto", required=True, help="Texto para sintetizar")
    parser.add_argument("--saida", required=True, help="Caminho do arquivo WAV de saída")
    parser.add_argument("--lang", default="p", help="Código do idioma (p para pt-br)")
    parser.add_argument("--voz", default=None, help="Nome da voz")
    parser.add_argument("--speed", type=float, default=1.0, help="Velocidade de reprodução")

    args = parser.parse_args()
    try:
        sintetizar(
            texto=args.texto,
            saida_wav=Path(args.saida),
            lang_code=args.lang,
            voice=args.voz,
            speed=args.speed,
        )
        sys.exit(0)
    except Exception as e:
        print(f"Erro no Kokoro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
