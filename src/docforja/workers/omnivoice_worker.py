"""Worker OmniVoice para clonagem de voz (OmniVoice-613M).

Roda no ambiente Python que tenha o pacote `omnivoice` e carrega o prompt de
clonagem (`.pt` com os tokens da referência) já salvo pelo usuário.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def sintetizar(
    texto: str,
    saida_wav: Path,
    voz: Path,
    modelo_repo: str = "k2-fsa/OmniVoice",
    cache: str = "",
    velocidade: float = 0.92,
    passos: int = 64,
    semente: int = 42,
) -> None:
    """Gera a fala clonada e grava um WAV de 24 kHz."""
    if cache:
        os.environ["HF_HOME"] = cache
    import numpy as np
    import soundfile as sf
    import torch
    from omnivoice import OmniVoice, VoiceClonePrompt

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device.startswith("cuda") else torch.float32
    model = OmniVoice.from_pretrained(modelo_repo, device_map=device, dtype=dtype)
    prompt = VoiceClonePrompt.load(str(voz))
    # Semente fixa: o mesmo texto gera sempre o mesmo áudio, e a retomada do
    # pipeline reaproveita a caché em vez de produzir uma voz diferente.
    torch.manual_seed(semente)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(semente)
    with torch.no_grad():
        audio = model.generate(
            text=texto,
            voice_clone_prompt=prompt,
            speed=velocidade,
            num_step=passos,
            postprocess_output=False,
            fade_duration=0.005,
            pad_duration=0.01,
        )
    onda = audio[0] if isinstance(audio, list) else audio
    if hasattr(onda, "cpu"):
        onda = onda.squeeze().cpu().numpy()
    saida_wav.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(saida_wav), np.array(onda, dtype=np.float32), 24000)


def main() -> None:
    parser = argparse.ArgumentParser(description="Worker OmniVoice para o DocForja")
    parser.add_argument("--texto", required=True)
    parser.add_argument("--saida", required=True)
    parser.add_argument("--voz", required=True, help="Prompt de clonagem (.pt) do perfil")
    parser.add_argument("--modelo", default="k2-fsa/OmniVoice")
    parser.add_argument("--cache", default="", help="Raiz do cache de modelos (HF_HOME)")
    parser.add_argument("--velocidade", type=float, default=0.92)
    parser.add_argument("--passos", type=int, default=64)
    parser.add_argument("--semente", type=int, default=42)
    args = parser.parse_args()

    voz = Path(args.voz)
    if not voz.is_file():
        print(f"Prompt de clonagem ausente: {voz}", file=sys.stderr)
        sys.exit(1)
    try:
        sintetizar(
            texto=args.texto,
            saida_wav=Path(args.saida),
            voz=voz,
            modelo_repo=args.modelo,
            cache=args.cache,
            velocidade=args.velocidade,
            passos=args.passos,
            semente=args.semente,
        )
    except Exception as erro:
        print(f"Erro no OmniVoice: {erro}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
