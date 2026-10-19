from __future__ import annotations

import json
import subprocess
from pathlib import Path


class AlinhadorWhisperX:
    """Orquestrador do alinhamento fonetico palavra a palavra via WhisperX."""

    def __init__(self, python_path: Path | None = None, modelo: str = "base") -> None:
        self.python_path = python_path or Path("envs/align/Scripts/python.exe")
        self.worker_path = Path("src/docforja/workers/whisperx_worker.py")
        self.modelo = modelo

    def disponivel(self) -> bool:
        return self.python_path.exists() and self.worker_path.exists()

    def alinhar(
        self,
        audio_wav: Path,
        saida_palavras: Path,
        saida_segmentos: Path,
        segmentos_info: list[dict] | None = None,
        idioma: str = "pt",
        device: str | None = None,
        modelo: str | None = None,
        timeout: float = 300,
    ) -> tuple[Path, Path]:
        if not self.disponivel():
            raise RuntimeError(
                f"WhisperX não disponível: python={self.python_path} worker={self.worker_path}"
            )

        modelo_efetivo = modelo or self.modelo
        cmd = [
            str(self.python_path),
            str(self.worker_path),
            "--audio",
            str(audio_wav.resolve()),
            "--saida-palavras",
            str(saida_palavras.resolve()),
            "--saida-segmentos",
            str(saida_segmentos.resolve()),
            "--lang",
            idioma,
        ]

        if modelo_efetivo:
            cmd.extend(["--model", modelo_efetivo])

        if device:
            cmd.extend(["--device", device])

        arquivo_segmentos_temp: Path | None = None
        if segmentos_info:
            arquivo_segmentos_temp = saida_segmentos.with_suffix(".tmp.json")
            with open(arquivo_segmentos_temp, "w", encoding="utf-8") as f:
                json.dump(segmentos_info, f, ensure_ascii=False)
            cmd.extend(["--segmentos", str(arquivo_segmentos_temp.resolve())])

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if res.returncode != 0:
                raise RuntimeError(f"Erro ao executar alinhamento com WhisperX: {res.stderr}")
        finally:
            if arquivo_segmentos_temp and arquivo_segmentos_temp.exists():
                arquivo_segmentos_temp.unlink()

        if not saida_palavras.exists() or not saida_segmentos.exists():
            raise FileNotFoundError(
                "WhisperX executou mas palavras.json ou segmentos.json não foram gerados."
            )

        return saida_palavras, saida_segmentos
