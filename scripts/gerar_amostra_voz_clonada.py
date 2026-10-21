"""Gera uma amostra da voz clonada do usuário com OmniVoice (OmniVoice-613M).

Usa o prompt de clonagem já salvo pelo app de áudio (`.pt` com os tokens da
referência) e grava o WAV bruto na pasta de estudos, para entrar na mesma
comparação das vozes Kokoro. Precisa do ambiente Python do app de áudio
(Python 3.10 com `omnivoice` instalado).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

TEXTO = (
    "A primeira hipótese estava errada. O que eles achavam que era um acidente "
    "era, na verdade, o começo de uma descoberta. E tudo por causa de uma "
    "rachadura na parede."
)


def main() -> int:
    analisador = argparse.ArgumentParser(description=__doc__)
    analisador.add_argument(
        "--prompt",
        type=Path,
        default=Path(r"D:\IA\audio_factory\voices\nova_ref_7s.pt"),
        help="Prompt de clonagem salvo (.pt do OmniVoice).",
    )
    analisador.add_argument(
        "--destino",
        type=Path,
        default=Path(r"E:\05_PROJETOS\forja\estudos-voz"),
    )
    analisador.add_argument(
        "--cache",
        type=Path,
        default=Path(r"D:\IA\audio_factory\models\voice_clone\hub"),
        help="Cache de modelos (HF_HOME) já usado pelo app de áudio.",
    )
    analisador.add_argument("--velocidade", type=float, default=0.92)
    analisador.add_argument("--passos", type=int, default=64)
    argumentos = analisador.parse_args()

    if not argumentos.prompt.is_file():
        raise SystemExit(f"Prompt de clonagem ausente: {argumentos.prompt}")
    argumentos.cache.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(argumentos.cache)

    import numpy as np
    import soundfile as sf
    import torch
    from omnivoice import OmniVoice, VoiceClonePrompt

    inicio = time.monotonic()
    print("Carregando OmniVoice na GPU (float16)...", flush=True)
    modelo = OmniVoice.from_pretrained(
        "k2-fsa/OmniVoice",
        device_map="cuda:0" if torch.cuda.is_available() else "cpu",
        dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    )
    print("Carregando o prompt de clonagem...", flush=True)
    prompt = VoiceClonePrompt.load(str(argumentos.prompt))
    print("Sintetizando a amostra...", flush=True)
    with torch.no_grad():
        audio = modelo.generate(
            text=TEXTO,
            voice_clone_prompt=prompt,
            speed=argumentos.velocidade,
            num_step=argumentos.passos,
            postprocess_output=False,
            fade_duration=0.005,
            pad_duration=0.01,
        )
    onda = audio[0] if isinstance(audio, list) else audio
    if hasattr(onda, "cpu"):
        onda = onda.squeeze().cpu().numpy()
    amostras = np.array(onda, dtype=np.float32)

    destino = argumentos.destino / "brutos"
    destino.mkdir(parents=True, exist_ok=True)
    saida = destino / "voz-clonada-omnivoice.wav"
    sf.write(str(saida), amostras, 24000)
    duracao = round(len(amostras) / 24000, 2)
    registro = {
        "voz": "voz-clonada-omnivoice",
        "idioma": "p",
        "descricao": "Português (BR) · voz clonada do usuário (OmniVoice)",
        "motor": "OmniVoice-613M (k2-fsa/OmniVoice, clonagem com a sua voz)",
        "prompt": str(argumentos.prompt),
        "velocidade": argumentos.velocidade,
        "passos": argumentos.passos,
        "duracao_s": duracao,
        "arquivo": saida.name,
        "segundos": round(time.monotonic() - inicio, 1),
    }
    (destino / "voz-clonada-omnivoice.json").write_text(
        json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(registro, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
