from __future__ import annotations

import importlib.util
import shutil
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

import yaml

from docforja.io import atomic_write_json
from docforja.models import BenchmarkReport, BenchmarkResult, CheckStatus
from docforja.process import ProcessRunner


class BenchmarkRunner:
    """Executa cargas pesadas sequencialmente para respeitar o limite da GPU."""

    def __init__(
        self,
        *,
        output_dir: Path,
        config_dir: Path = Path("config"),
        python_environments: dict[str, Path] | None = None,
        runner: ProcessRunner | None = None,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self.output_dir = output_dir
        self.config_dir = config_dir
        self.python_environments = python_environments or {}
        self.runner = runner or ProcessRunner()
        self.clock = clock

    def run(self) -> BenchmarkReport:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        results: list[BenchmarkResult] = []
        models = self._load_yaml(self.config_dir / "modelos.yaml")
        for item in models.get("imagem", {}).get("candidatos", []):
            results.append(self._availability_result("imagem", item["id"], "ComfyUI"))
        for item in models.get("tts", {}).get("candidatos", []):
            module = "chatterbox" if "chatterbox" in item["id"] else "kokoro"
            results.append(self._module_result("tts", item["id"], module, module))
        results.append(self._module_result("alinhamento", "whisperx", "whisperx", "whisperx"))
        results.append(self._module_result("parallax", "depthflow", "depthflow", "depthflow"))
        results.append(self._module_result("recorte", "birefnet", "rembg"))
        results.append(self._module_result("upscale", "real-esrgan", "realesrgan", "realesrgan"))
        results.extend(self._render_benchmarks())
        report = BenchmarkReport(results=results)
        atomic_write_json(self.config_dir / "benchmark.json", report.model_dump(mode="json"))
        return report

    @staticmethod
    def _load_yaml(path: Path) -> dict[str, object]:
        with path.open(encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def _availability_result(self, category: str, candidate: str, service: str) -> BenchmarkResult:
        return BenchmarkResult(
            id=f"{category}_{candidate}",
            category=category,
            candidate=candidate,
            status=CheckStatus.SKIPPED,
            duration_seconds=0,
            message=(
                f"{service}: adicione o workflow API e o arquivo .bindings.yaml em workflows/ "
                "para habilitar esta medição"
            ),
        )

    def _module_result(
        self,
        category: str,
        candidate: str,
        module: str,
        environment: str | None = None,
    ) -> BenchmarkResult:
        isolated_python = self.python_environments.get(environment or "")
        available = (
            importlib.util.find_spec(module) is not None
            or (isolated_python is not None and isolated_python.exists())
            or (module == "rembg" and shutil.which("rembg") is not None)
        )
        return BenchmarkResult(
            id=f"{category}_{candidate}",
            category=category,
            candidate=candidate,
            status=CheckStatus.SKIPPED if not available else CheckStatus.WARNING,
            duration_seconds=0,
            message=(
                "dependência ausente"
                if not available
                else "dependência disponível; adaptador de medição requer os modelos locais"
            ),
        )

    def _render_benchmarks(self) -> list[BenchmarkResult]:
        if not shutil.which("ffmpeg"):
            return [
                BenchmarkResult(
                    id="render_ffmpeg",
                    category="render",
                    candidate="ffmpeg-nvenc",
                    status=CheckStatus.SKIPPED,
                    duration_seconds=0,
                    message="FFmpeg ausente",
                )
            ]
        output: list[BenchmarkResult] = []
        for label, size in (("1080p", "1920x1080"), ("1440p", "2560x1440")):
            target = self.output_dir / f"render-{label}.mp4"
            started = self.clock()
            try:
                result = self.runner.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-f",
                        "lavfi",
                        "-i",
                        f"color=c=#18191c:s={size}:r=30:d=10",
                        "-c:v",
                        "h264_nvenc",
                        "-preset",
                        "p4",
                        "-pix_fmt",
                        "yuv420p",
                        str(target),
                    ],
                    timeout=180,
                )
                duration = max(0, self.clock() - started)
                success = result.returncode == 0 and target.exists()
                output.append(
                    BenchmarkResult(
                        id=f"render_{label}",
                        category="render",
                        candidate=f"nvenc-{label}",
                        status=CheckStatus.OK if success else CheckStatus.ERROR,
                        duration_seconds=round(duration, 3),
                        outputs=[target] if success else [],
                        message="render de referência concluído"
                        if success
                        else "FFmpeg/NVENC falhou",
                    )
                )
            except (OSError, TimeoutError, subprocess.TimeoutExpired):
                output.append(
                    BenchmarkResult(
                        id=f"render_{label}",
                        category="render",
                        candidate=f"nvenc-{label}",
                        status=CheckStatus.ERROR,
                        duration_seconds=max(0, self.clock() - started),
                        message="erro ou timeout ao executar FFmpeg",
                    )
                )
        return output
