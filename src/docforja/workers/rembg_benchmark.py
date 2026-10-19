"""Recorte de teste no ambiente externo do rembg."""

from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path


def main(request_file: Path) -> None:
    request = json.loads(request_file.read_text(encoding="utf-8"))
    from PIL import Image
    from rembg import new_session, remove

    source = Path(request["source"])
    target = Path(request["output"])
    started = time.perf_counter()
    session = new_session(request["model"], providers=["CPUExecutionProvider"])
    result = remove(source.read_bytes(), session=session)
    with Image.open(io.BytesIO(result)) as image:
        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A")
        minimum, maximum = alpha.getextrema()
        if minimum == maximum:
            raise ValueError("Recorte sem áreas transparentes e opacas")
        coverage = sum(value * count for value, count in enumerate(alpha.histogram())) / (
            255 * rgba.width * rgba.height
        )
        rgba.save(target)
        size = rgba.size
    target.with_suffix(".metrics.json").write_text(
        json.dumps(
            {
                "width": size[0],
                "height": size[1],
                "alpha_coverage": round(coverage, 4),
                "processing_seconds": round(time.perf_counter() - started, 3),
                "model": request["model"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main(Path(sys.argv[1]))
