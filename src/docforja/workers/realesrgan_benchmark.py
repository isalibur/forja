"""Ampliação Real-ESRGAN em processo separado."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path


def main(request_file: Path) -> None:
    request = json.loads(request_file.read_text(encoding="utf-8"))
    import cv2
    import torch
    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer

    source = Path(request["source"])
    target = Path(request["output"])
    image = cv2.imread(str(source), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Imagem de entrada ilegível")
    scale = int(request["scale"])
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    network = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
    upsampler = RealESRGANer(
        scale=4,
        model_path=request["weights"],
        model=network,
        tile=int(request["tile"]),
        tile_pad=10,
        pre_pad=0,
        half=torch.cuda.is_available(),
        gpu_id=0 if torch.cuda.is_available() else None,
    )
    output, _ = upsampler.enhance(image, outscale=scale)
    if output.shape[:2] != (image.shape[0] * scale, image.shape[1] * scale):
        raise ValueError("Dimensões da ampliação incorretas")
    if not cv2.imwrite(str(target), output):
        raise OSError("Não foi possível gravar o PNG ampliado")
    target.with_suffix(".metrics.json").write_text(
        json.dumps(
            {
                "input_width": image.shape[1],
                "input_height": image.shape[0],
                "width": output.shape[1],
                "height": output.shape[0],
                "scale": scale,
                "processing_seconds": round(time.perf_counter() - started, 3),
                "torch_peak_allocated_mb": round(torch.cuda.max_memory_allocated() / 1024**2)
                if torch.cuda.is_available()
                else None,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main(Path(sys.argv[1]))
