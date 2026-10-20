from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
import whisperx
from whisperx_mapping import montar_saida_alinhamento


def processar_alinhamento(
    audio_path: Path,
    segmentos_path: Path | None,
    saida_palavras: Path,
    saida_segmentos: Path,
    idioma: str = "pt",
    device: str | None = None,
    model_name: str = "base",
    align_model_name: str | None = None,
) -> None:
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    audio = whisperx.load_audio(str(audio_path))
    duracao_total = len(audio) / 16000.0

    # Carrega segmentos se fornecidos
    segmentos_input = []
    if segmentos_path and segmentos_path.exists():
        with open(segmentos_path, encoding="utf-8") as f:
            segmentos_input = json.load(f)

    if not segmentos_input:
        # Modo transcricao completa + alinhamento
        compute_type = "float16" if device == "cuda" else "int8"
        model = whisperx.load_model(
            model_name, device=device, compute_type=compute_type, language=idioma
        )
        result = model.transcribe(audio, batch_size=16)
        segments = result.get("segments", [])
    else:
        # Prepara formato compativel para o alinhador do WhisperX
        segments = []
        for s in segmentos_input:
            segments.append(
                {
                    "text": s.get("texto", s.get("text", "")),
                    "start": float(s.get("inicio_s", s.get("start", 0.0))),
                    "end": float(s.get("fim_s", s.get("end", duracao_total))),
                    "id": s.get("id", ""),
                }
            )

    # Alinhamento fonetico com modelo de fonemas por idioma
    try:
        kwargs: dict[str, str] = {"language_code": idioma, "device": device}
        if align_model_name:
            kwargs["model_name"] = align_model_name
        model_a, metadata = whisperx.load_align_model(**kwargs)
        aligned = whisperx.align(
            segments, model_a, metadata, audio, device, return_char_alignments=False
        )
        aligned_segments = aligned.get("segments", segments)
    except Exception as e:
        print(f"Aviso no alinhamento fonético, usando segmentos diretos: {e}", file=sys.stderr)
        aligned_segments = segments

    palavras_lista, segmentos_lista = montar_saida_alinhamento(
        aligned_segments, segments if segmentos_input else None
    )

    saida_palavras.parent.mkdir(parents=True, exist_ok=True)
    with open(saida_palavras, "w", encoding="utf-8") as f:
        json.dump(palavras_lista, f, ensure_ascii=False, indent=2)

    saida_segmentos.parent.mkdir(parents=True, exist_ok=True)
    with open(saida_segmentos, "w", encoding="utf-8") as f:
        json.dump(segmentos_lista, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Worker WhisperX para alinhamento palavra por palavra"
    )
    parser.add_argument("--audio", required=True, help="Caminho do áudio WAV")
    parser.add_argument(
        "--segmentos", default=None, help="Caminho do JSON com segmentos conhecidos"
    )
    parser.add_argument("--saida-palavras", required=True, help="Caminho para palavras.json")
    parser.add_argument("--saida-segmentos", required=True, help="Caminho para segmentos.json")
    parser.add_argument("--lang", default="pt", help="Código do idioma")
    parser.add_argument("--device", default=None, help="Dispositivo (cuda ou cpu)")
    parser.add_argument(
        "--model", default="base", help="Modelo Whisper ASR (ex: base, large-v3)"
    )
    parser.add_argument(
        "--align-model",
        default=None,
        help="Modelo de alinhamento fonético (ex: jonatasgrosman/wav2vec2)",
    )

    args = parser.parse_args()
    try:
        processar_alinhamento(
            audio_path=Path(args.audio),
            segmentos_path=Path(args.segmentos) if args.segmentos else None,
            saida_palavras=Path(args.saida_palavras),
            saida_segmentos=Path(args.saida_segmentos),
            idioma=args.lang,
            device=args.device,
            model_name=args.model,
            align_model_name=args.align_model,
        )
        sys.exit(0)
    except Exception as e:
        print(f"Erro no WhisperX: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
