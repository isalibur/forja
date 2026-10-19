"""Ensaio isolado de alinhamento WhisperX com texto de referência conhecido."""

from __future__ import annotations

import json
import math
import sys
import time
import wave
from pathlib import Path


def prepare_audio(source: Path, target: Path, repetitions: int, duration: float) -> float:
    """Repete PCM de teste e completa a duração com silêncio."""
    with wave.open(str(source), "rb") as input_file:
        if input_file.getnchannels() != 1 or input_file.getsampwidth() != 2:
            raise ValueError("A amostra deve ser WAV mono PCM16")
        sample_rate = input_file.getframerate()
        frame_count = input_file.getnframes()
        frames = input_file.readframes(frame_count)
    speech_duration = frame_count * repetitions / sample_rate
    if repetitions < 1 or not 0.9 * duration <= speech_duration <= duration:
        raise ValueError("A narração repetida deve ocupar pelo menos 90% dos 60 segundos")
    target_frames = round(duration * sample_rate)
    padding = target_frames - frame_count * repetitions
    with wave.open(str(target), "wb") as output_file:
        output_file.setnchannels(1)
        output_file.setsampwidth(2)
        output_file.setframerate(sample_rate)
        output_file.writeframes(frames * repetitions + bytes(padding * 2))
    return frame_count / sample_rate


def main(request_file: Path) -> None:
    request = json.loads(request_file.read_text(encoding="utf-8"))
    target = Path(request["output"])
    duration = float(request["duration_seconds"])
    repetitions = int(request["repetitions"])
    clip_seconds = prepare_audio(Path(request["source"]), target, repetitions, duration)

    import torch
    import whisperx

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    model, metadata = whisperx.load_align_model(
        language_code=request["language"], device=device, model_name=request["model"]
    )
    text = request["text"]
    segments = [
        {"start": clip_seconds * index, "end": clip_seconds * (index + 1), "text": text}
        for index in range(repetitions)
    ]
    aligned = whisperx.align(segments, model, metadata, str(target), device)
    words = aligned["word_segments"]
    valid = [
        word
        for word in words
        if isinstance(word.get("start"), (int, float))
        and isinstance(word.get("end"), (int, float))
        and math.isfinite(word["start"])
        and math.isfinite(word["end"])
        and 0 <= word["start"] <= word["end"] <= duration
    ]
    if len(valid) < len(text.split()) * repetitions * 0.9:
        raise ValueError("Menos de 90% das palavras receberam tempos válidos")
    target.with_suffix(".words.json").write_text(
        json.dumps({"segments": aligned["segments"], "words": words}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    metrics = {
        "audio_seconds": duration,
        "spoken_seconds": round(clip_seconds * repetitions, 3),
        "alignment_seconds": round(time.perf_counter() - started, 3),
        "word_count": len(words),
        "valid_word_count": len(valid),
        "language": request["language"],
        "alignment_model": request["model"],
        "torch_peak_allocated_mb": round(torch.cuda.max_memory_allocated() / 1024**2)
        if device == "cuda"
        else None,
    }
    target.with_suffix(".metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main(Path(sys.argv[1]))
