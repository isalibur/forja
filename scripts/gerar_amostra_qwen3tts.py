"""Gera amostras do Qwen3-TTS 12Hz 1.7B (Base): voz de catálogo e voz clonada do usuário.

Precisa do ambiente `envs/tts-qwen` (Python 3.11 com `qwen-tts` e torch CUDA).
Os pesos podem vir do cache já existente (`--cache`).
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


def _salvar(destino: Path, nome: str, ondas: list, taxa: int) -> Path:
    import soundfile as sf

    destino.mkdir(parents=True, exist_ok=True)
    caminho = destino / f"{nome}.wav"
    sf.write(str(caminho), ondas[0], taxa)
    return caminho


def main() -> int:
    analisador = argparse.ArgumentParser(description=__doc__)
    analisador.add_argument(
        "--destino",
        type=Path,
        default=Path(r"E:\05_PROJETOS\forja\estudos-voz"),
    )
    analisador.add_argument(
        "--cache",
        type=Path,
        default=Path(r"D:\IA\audio_factory\models\voice_clone"),
        help="Raiz do cache de modelos (HF_HOME); o hub fica em <cache>/hub.",
    )
    analisador.add_argument(
        "--referencia",
        type=Path,
        default=Path(r"D:\IA\audio_factory\voices\minha_voz_corte_7s.wav"),
        help="Áudio de referência para a clonagem (a sua voz).",
    )
    analisador.add_argument(
        "--voz-catalogo",
        default="",
        help="Nome de uma voz de catálogo (em branco: usa a primeira disponível).",
    )
    analisador.add_argument("--idioma", default="Portuguese")
    analisador.add_argument(
        "--ref-texto",
        default="",
        help="Transcrição da referência (em branco: lê o .json ao lado do áudio).",
    )
    analisador.add_argument(
        "--modelo",
        default="Qwen/Qwen3-TTS-12Hz-1.7B-Base",
    )
    argumentos = analisador.parse_args()

    argumentos.cache.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(argumentos.cache)

    import soundfile as sf
    from qwen_tts import Qwen3TTSModel

    inicio = time.monotonic()
    print("Carregando o Qwen3-TTS na GPU...", flush=True)
    modelo = Qwen3TTSModel.from_pretrained(argumentos.modelo, device_map="cuda:0")
    print("Modelo carregado.", flush=True)

    resultados: list[dict[str, object]] = []
    brutos = argumentos.destino / "brutos"

    vozes = modelo.get_supported_speakers()
    print(f"Vozes de catálogo no modelo Base: {len(vozes)}", flush=True)
    if argumentos.referencia.is_file():
        print("Clonando a sua voz...", flush=True)
        audio, taxa_ref = sf.read(str(argumentos.referencia), dtype="float32")
        ref_text = argumentos.ref_texto
        if not ref_text:
            lado = argumentos.referencia.with_suffix(".json")
            if lado.is_file():
                ref_text = str(json.loads(lado.read_text(encoding="utf-8")).get("ref_text", ""))
        ondas, taxa = modelo.generate_voice_clone(
            text=TEXTO,
            language=argumentos.idioma,
            ref_audio=(audio, taxa_ref),
            ref_text=ref_text or None,
        )
        caminho = _salvar(brutos, "qwen3tts-voz-clonada", ondas, taxa)
        resultados.append(
            {
                "voz": "qwen3tts-voz-clonada",
                "idioma": "p",
                "descricao": "Português (BR) · sua voz clonada (Qwen3-TTS)",
                "motor": "Qwen3-TTS 12Hz 1.7B Base (clonagem a partir da sua referência)",
                "referencia": str(argumentos.referencia),
                "arquivo": caminho.name,
                "duracao_s": round(len(ondas[0]) / taxa, 2),
            }
        )
        print(json.dumps(resultados[-1], ensure_ascii=False), flush=True)
    else:
        print(f"Referência ausente, pulando a clonagem: {argumentos.referencia}", flush=True)

    for registro in resultados:
        (brutos / f"{registro['voz']}.json").write_text(
            json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(f"Tempo total: {round(time.monotonic() - inicio, 1)} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
