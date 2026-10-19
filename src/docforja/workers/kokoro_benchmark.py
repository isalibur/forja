"""Executado pelo Python externo do Kokoro, sem importar o núcleo DocForja."""

import json
import os
import sys
import time
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"


def main():
    import numpy as np
    import soundfile as sf
    import torch
    from kokoro import KModel, KPipeline

    request = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    torch.manual_seed(42)
    torch.cuda.reset_peak_memory_stats()
    model = (
        KModel(repo_id=request["repo_id"], config=request["config"], model=request["weights"])
        .to("cuda")
        .eval()
    )
    pipe = KPipeline(lang_code=request["lang_code"], repo_id=request["repo_id"], model=model)
    torch.cuda.synchronize()
    started = time.perf_counter()
    chunks = [
        audio.cpu().numpy()
        for _, _, audio in pipe(request["text"], voice=request["path"], speed=1.0)
    ]
    if not chunks:
        raise RuntimeError("O motor não gerou áudio")
    audio = np.concatenate(chunks)
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - started
    if not np.isfinite(audio).all() or float(np.max(np.abs(audio))) == 0:
        raise RuntimeError("Áudio inválido ou silencioso")
    target = Path(request["output"])
    sf.write(str(target), audio, 24000, subtype="PCM_16")
    metrics = {
        "audio_seconds": round(len(audio) / 24000, 3),
        "inference_seconds": round(elapsed, 3),
        "torch_peak_allocated_mb": round(torch.cuda.max_memory_allocated() / 1024**2),
        "sample_rate": 24000,
        "voice": request["id"],
        "language": request["language"],
    }
    target.with_suffix(".metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics))


if __name__ == "__main__":
    main()
