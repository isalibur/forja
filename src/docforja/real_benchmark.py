"""Ensaios reais do M0; dependências de IA ficam em processos externos."""

from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

import httpx
import yaml

from docforja.io import atomic_write_json
from docforja.models import BenchmarkReport, BenchmarkResult, CheckStatus
from docforja.settings import AppSettings


@contextmanager
def benchmark_lock(path: Path):
    """Impede dois benchmarks locais de disputarem a GPU; libera após falhas."""
    import os

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            def lock():
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)

            def unlock():
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            def lock():
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)

            def unlock():
                fcntl.flock(handle, fcntl.LOCK_UN)

        try:
            lock()
        except OSError as exc:
            raise RuntimeError("Outro benchmark está usando a GPU") from exc
        try:
            yield
        finally:
            handle.seek(0)
            unlock()


def bind_workflow(template: dict, bindings: dict, values: dict) -> dict:
    result = copy.deepcopy(template)
    for key, target in bindings.items():
        if key not in values:
            raise ValueError(f"Parâmetro ausente: {key}")
        node, field = target.split(".", 1)
        if field not in result[node]["inputs"]:
            raise ValueError(f"Binding inválido: {target}")
        result[node]["inputs"][field] = values[key]
    return result


class VramSampler:
    """Pico amostrado da GPU inteira, incluindo desktop e outros processos."""

    def __init__(self) -> None:
        self.peak: int | None = None
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._sample, daemon=True)

    def _sample(self) -> None:
        while not self.stop.is_set():
            try:
                output = subprocess.run(
                    [
                        "nvidia-smi",
                        "--id=0",
                        "--query-gpu=memory.used",
                        "--format=csv,noheader,nounits",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=4,
                    check=True,
                ).stdout.strip()
                value = int(output)
                self.peak = max(self.peak or 0, value)
            except (OSError, ValueError, subprocess.SubprocessError):
                pass
            self.stop.wait(0.5)

    def __enter__(self) -> VramSampler:
        self.thread.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.stop.set()
        self.thread.join(timeout=5)


class RealBenchmarkRunner:
    def __init__(self, settings: AppSettings, config_dir: Path = Path("config")) -> None:
        self.settings = settings
        self.config_dir = config_dir.resolve()
        self.root = self.config_dir.parent
        run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
        self.output = (settings.paths.benchmark_output / run_id).resolve()

    def _read(self, path: Path) -> dict:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def run(self, categories: list[str]) -> BenchmarkReport:
        available = {
            "imagem",
            "tts",
            "alinhamento",
            "parallax",
            "recorte",
            "upscale",
            "render",
        }
        if not categories or set(categories) - available:
            raise ValueError(
                "Categorias reais disponíveis: imagem, tts, alinhamento, parallax, recorte, "
                "upscale, render"
            )
        with benchmark_lock(self.root / ".benchmark-gpu.lock"):
            return self._run(list(dict.fromkeys(categories)))

    def _run(self, categories: list[str]) -> BenchmarkReport:
        self.output.mkdir(parents=True, exist_ok=False)
        models = self._read(self.config_dir / "modelos.yaml")
        spec = self._read(self.config_dir / "benchmark.yaml")
        latest_file = self.config_dir / "benchmark.json"
        previous = []
        if latest_file.exists():
            previous = BenchmarkReport.model_validate_json(
                latest_file.read_text(encoding="utf-8")
            ).results
        results: list[BenchmarkResult] = []
        for category in categories:
            for candidate in models.get(category, {}).get("candidatos", []):
                if "benchmark" not in candidate:
                    results.append(
                        BenchmarkResult(
                            id=f"{category}_{candidate['id']}",
                            category=category,
                            candidate=candidate["id"],
                            status=CheckStatus.SKIPPED,
                            duration_seconds=0,
                            message="ensaio real ainda não configurado",
                        )
                    )
                    continue
                if category == "imagem":
                    results.extend(self._images(candidate, spec["prompts_imagem"]))
                elif category == "tts":
                    results.extend(self._speech(candidate, spec["tts"]["textos"]))
                elif category == "alinhamento":
                    results.append(self._alignment(candidate, spec, previous + results))
                elif category == "parallax":
                    results.append(self._parallax(candidate, spec, previous + results))
                elif category == "recorte":
                    results.append(self._cutout(candidate, previous + results))
                elif category == "upscale":
                    results.append(self._upscale(candidate, previous + results))
                elif category == "render":
                    results.append(self._render(candidate, spec))
                atomic_write_json(
                    self.output / "report.json",
                    BenchmarkReport(results=results).model_dump(mode="json"),
                )
        report = BenchmarkReport(results=results)
        for result in report.results:
            result.metrics["run_id"] = self.output.name
            result.metrics["measured_at"] = report.generated_at.isoformat()
        atomic_write_json(self.output / "report.json", report.model_dump(mode="json"))
        combined = [item for item in previous if item.category not in categories] + results
        atomic_write_json(latest_file, BenchmarkReport(results=combined).model_dump(mode="json"))
        return report

    def _images(self, candidate: dict, prompts: list[dict]) -> list[BenchmarkResult]:
        cfg = candidate["benchmark"]
        template = json.loads((self.root / cfg["workflow"]).read_text(encoding="utf-8"))
        bindings = self._read(self.root / cfg["bindings"])
        base = next(s.url for s in self.settings.services if s.name == "ComfyUI").removesuffix(
            "/system_stats"
        )
        results = []
        with httpx.Client(base_url=base, timeout=30) as client:
            queue = client.get("/queue")
            queue.raise_for_status()
            if queue.json().get("queue_running") or queue.json().get("queue_pending"):
                raise RuntimeError(
                    "ComfyUI tem trabalhos em andamento; execute quando a fila estiver vazia"
                )
            for index, prompt in enumerate(prompts):
                identifier = f"imagem_{candidate['id']}_{prompt['id']}"
                values = dict(
                    cfg["parameters"],
                    prompt=prompt["texto"],
                    seed=cfg["seed"] + index,
                    output_prefix=f"docforja/{self.output.name}/{identifier}",
                )
                workflow = bind_workflow(template, bindings, values)
                atomic_write_json(self.output / f"{identifier}.prompt.json", workflow)
                started = time.perf_counter()
                with VramSampler() as sampler:
                    response = client.post(
                        "/prompt", json={"prompt": workflow, "client_id": self.output.name}
                    )
                    response.raise_for_status()
                    prompt_id = response.json()["prompt_id"]
                    while True:
                        response = client.get(f"/history/{prompt_id}")
                        response.raise_for_status()
                        history = response.json().get(prompt_id)
                        if history:
                            break
                        if time.perf_counter() - started > cfg.get("timeout_seconds", 900):
                            raise TimeoutError(
                                f"ComfyUI pode estar processando {prompt_id}; verifique a fila"
                            )
                        time.sleep(1)
                elapsed = time.perf_counter() - started
                atomic_write_json(self.output / f"{identifier}.history.json", history)
                outputs = []
                for node_output in history.get("outputs", {}).values():
                    for item in node_output.get("images", []):
                        response = client.get("/view", params=item)
                        response.raise_for_status()
                        target = self.output / f"{identifier}-{len(outputs)}.png"
                        target.write_bytes(response.content)
                        outputs.append(target)
                success = bool(outputs) and history.get("status", {}).get("status_str") == "success"
                results.append(
                    BenchmarkResult(
                        id=identifier,
                        category="imagem",
                        candidate=candidate["id"],
                        status=CheckStatus.OK if success else CheckStatus.ERROR,
                        duration_seconds=round(elapsed, 3),
                        peak_vram_mb=sampler.peak,
                        outputs=outputs,
                        message="imagem gerada" if success else "falha; consulte history.json",
                        metrics={
                            "seed": values["seed"],
                            "width": values["width"],
                            "height": values["height"],
                            "vram_scope": "GPU inteira; amostragem 0,5 s",
                            "first_in_batch": index == 0,
                        },
                    )
                )
                if not success:
                    break
            # Libera somente com fila vazia; não interrompe trabalhos externos.
            queue = client.get("/queue").json()
            if not queue.get("queue_running") and not queue.get("queue_pending"):
                client.post(
                    "/free", json={"unload_models": True, "free_memory": True}
                ).raise_for_status()
        return results

    def _alignment(
        self, candidate: dict, spec: dict, known_results: list[BenchmarkResult]
    ) -> BenchmarkResult:
        cfg = candidate["benchmark"]
        source = next(
            (
                result.outputs[0]
                for result in reversed(known_results)
                if result.id == cfg["source_result_id"]
                and result.status == CheckStatus.OK
                and result.outputs
                and result.outputs[0].is_file()
            ),
            None,
        )
        if source is None:
            raise FileNotFoundError(f"Áudio do benchmark ausente: {cfg['source_result_id']}")
        identifier = f"alinhamento_{candidate['id']}"
        target = self.output / f"{identifier}.wav"
        python = (self.root / self.settings.python_environments[candidate["adaptador"]]).resolve()
        request = {
            "source": str(source),
            "output": str(target),
            "text": spec["tts"]["textos"][cfg["language"]],
            "language": cfg["language"],
            "model": cfg["model"],
            "repetitions": cfg["repetitions"],
            "duration_seconds": spec["alinhamento"]["duracao_alvo_segundos"],
        }
        request_file = self.output / f"{identifier}.request.json"
        atomic_write_json(request_file, request)
        started = time.perf_counter()
        with VramSampler() as sampler:
            try:
                completed = subprocess.run(
                    [
                        str(python),
                        str(Path(__file__).parent / "workers" / "whisperx_align_benchmark.py"),
                        str(request_file),
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=600,
                    check=False,
                )
                log = completed.stdout + completed.stderr
                exit_code = completed.returncode
            except (OSError, subprocess.TimeoutExpired) as exc:
                log = str(exc)
                exit_code = -1
        elapsed = time.perf_counter() - started
        (self.output / f"{identifier}.log").write_text(log, encoding="utf-8")
        words = target.with_suffix(".words.json")
        metrics_file = target.with_suffix(".metrics.json")
        success = exit_code == 0 and target.is_file() and words.is_file() and metrics_file.is_file()
        metrics = json.loads(metrics_file.read_text(encoding="utf-8")) if success else {}
        metrics["vram_scope"] = "GPU inteira; amostragem 0,5 s"
        return BenchmarkResult(
            id=identifier,
            category="alinhamento",
            candidate=candidate["id"],
            status=CheckStatus.OK if success else CheckStatus.ERROR,
            duration_seconds=round(elapsed, 3),
            peak_vram_mb=sampler.peak,
            outputs=[target, words] if success else [],
            message="60 s alinhados a texto conhecido" if success else "falha; consulte o log",
            metrics=metrics,
        )

    def _parallax(
        self, candidate: dict, spec: dict, known_results: list[BenchmarkResult]
    ) -> BenchmarkResult:
        cfg = candidate["benchmark"]
        source = next(
            (
                result.outputs[0]
                for result in reversed(known_results)
                if result.id == cfg["source_result_id"]
                and result.status == CheckStatus.OK
                and result.outputs
                and result.outputs[0].is_file()
            ),
            None,
        )
        if source is None:
            raise FileNotFoundError(f"Imagem do benchmark ausente: {cfg['source_result_id']}")
        identifier = f"parallax_{candidate['id']}"
        target = self.output / f"{identifier}.mp4"
        python = (self.root / self.settings.python_environments[candidate["adaptador"]]).resolve()
        duration = spec["parallax"]["duracao_segundos"]
        worker = Path(__file__).parent / "workers" / "depthflow_benchmark.py"
        args = [
            str(python),
            str(worker),
            "da2",
            "--model",
            cfg["model"],
            "input",
            str(source),
            "main",
            "--output",
            str(target),
            "--time",
            str(duration),
            "--fps",
            str(cfg["fps"]),
            "--width",
            str(cfg["width"]),
            "--height",
            str(cfg["height"]),
        ]
        env = dict(os.environ, PYTHONIOENCODING="utf-8", HF_HUB_OFFLINE="1")
        started = time.perf_counter()
        with VramSampler() as sampler:
            try:
                completed = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=300,
                    check=False,
                    env=env,
                )
                log = completed.stdout + completed.stderr
                exit_code = completed.returncode
            except (OSError, subprocess.TimeoutExpired) as exc:
                log = str(exc)
                exit_code = -1
        elapsed = time.perf_counter() - started
        (self.output / f"{identifier}.log").write_text(log, encoding="utf-8")
        metrics = {"source": str(source), "vram_scope": "GPU inteira; amostragem 0,5 s"}
        success = exit_code == 0 and target.is_file() and target.stat().st_size > 0
        if success:
            probe = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "stream=width,height,nb_frames",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "json",
                    str(target),
                ],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if probe.returncode == 0:
                info = json.loads(probe.stdout)
                stream = info["streams"][0]
                metrics.update(
                    width=int(stream["width"]),
                    height=int(stream["height"]),
                    frames=int(stream["nb_frames"]),
                    video_seconds=float(info["format"]["duration"]),
                )
                success = (
                    metrics["width"] == cfg["width"]
                    and metrics["height"] == cfg["height"]
                    and metrics["frames"] == round(duration * cfg["fps"])
                    and abs(metrics["video_seconds"] - duration) < 0.1
                )
            else:
                success = False
        return BenchmarkResult(
            id=identifier,
            category="parallax",
            candidate=candidate["id"],
            status=CheckStatus.OK if success else CheckStatus.ERROR,
            duration_seconds=round(elapsed, 3),
            peak_vram_mb=sampler.peak,
            outputs=[target] if success else [],
            message="vídeo de 5 s gerado" if success else "falha; consulte o log",
            metrics=metrics,
        )

    def _cutout(self, candidate: dict, known_results: list[BenchmarkResult]) -> BenchmarkResult:
        cfg = candidate["benchmark"]
        source = next(
            (
                result.outputs[0]
                for result in reversed(known_results)
                if result.id == cfg["source_result_id"]
                and result.status == CheckStatus.OK
                and result.outputs
                and result.outputs[0].is_file()
            ),
            None,
        )
        if source is None:
            raise FileNotFoundError(f"Imagem do benchmark ausente: {cfg['source_result_id']}")
        identifier = f"recorte_{candidate['id']}"
        target = self.output / f"{identifier}.png"
        request = {"source": str(source), "output": str(target), "model": cfg["model"]}
        request_file = self.output / f"{identifier}.request.json"
        atomic_write_json(request_file, request)
        python = (self.root / self.settings.python_environments[candidate["adaptador"]]).resolve()
        env = dict(os.environ, REMBG_HOME=cfg["model_home"])
        started = time.perf_counter()
        with VramSampler() as sampler:
            try:
                completed = subprocess.run(
                    [
                        str(python),
                        str(Path(__file__).parent / "workers" / "rembg_benchmark.py"),
                        str(request_file),
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=300,
                    check=False,
                    env=env,
                )
                log = completed.stdout + completed.stderr
                exit_code = completed.returncode
            except (OSError, subprocess.TimeoutExpired) as exc:
                log = str(exc)
                exit_code = -1
        elapsed = time.perf_counter() - started
        (self.output / f"{identifier}.log").write_text(log, encoding="utf-8")
        metrics_file = target.with_suffix(".metrics.json")
        success = exit_code == 0 and target.is_file() and metrics_file.is_file()
        metrics = json.loads(metrics_file.read_text(encoding="utf-8")) if success else {}
        metrics["source"] = str(source)
        metrics["vram_scope"] = "GPU inteira; amostragem 0,5 s"
        return BenchmarkResult(
            id=identifier,
            category="recorte",
            candidate=candidate["id"],
            status=CheckStatus.OK if success else CheckStatus.ERROR,
            duration_seconds=round(elapsed, 3),
            peak_vram_mb=sampler.peak,
            outputs=[target] if success else [],
            message="recorte PNG gerado" if success else "falha; consulte o log",
            metrics=metrics,
        )

    def _upscale(self, candidate: dict, known_results: list[BenchmarkResult]) -> BenchmarkResult:
        cfg = candidate["benchmark"]
        source = next(
            (
                result.outputs[0]
                for result in reversed(known_results)
                if result.id == cfg["source_result_id"]
                and result.status == CheckStatus.OK
                and result.outputs
                and result.outputs[0].is_file()
            ),
            None,
        )
        if source is None:
            raise FileNotFoundError(f"Imagem do benchmark ausente: {cfg['source_result_id']}")
        identifier = f"upscale_{candidate['id']}"
        target = self.output / f"{identifier}.png"
        request = {
            "source": str(source),
            "output": str(target),
            "weights": cfg["weights"],
            "scale": cfg["scale"],
            "tile": cfg["tile"],
        }
        request_file = self.output / f"{identifier}.request.json"
        atomic_write_json(request_file, request)
        python = (self.root / self.settings.python_environments[candidate["adaptador"]]).resolve()
        started = time.perf_counter()
        with VramSampler() as sampler:
            try:
                completed = subprocess.run(
                    [
                        str(python),
                        str(Path(__file__).parent / "workers" / "realesrgan_benchmark.py"),
                        str(request_file),
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=600,
                    check=False,
                )
                log = completed.stdout + completed.stderr
                exit_code = completed.returncode
            except (OSError, subprocess.TimeoutExpired) as exc:
                log = str(exc)
                exit_code = -1
        elapsed = time.perf_counter() - started
        (self.output / f"{identifier}.log").write_text(log, encoding="utf-8")
        metrics_file = target.with_suffix(".metrics.json")
        success = exit_code == 0 and target.is_file() and metrics_file.is_file()
        metrics = json.loads(metrics_file.read_text(encoding="utf-8")) if success else {}
        metrics["source"] = str(source)
        metrics["vram_scope"] = "GPU inteira; amostragem 0,5 s"
        return BenchmarkResult(
            id=identifier,
            category="upscale",
            candidate=candidate["id"],
            status=CheckStatus.OK if success else CheckStatus.ERROR,
            duration_seconds=round(elapsed, 3),
            peak_vram_mb=sampler.peak,
            outputs=[target] if success else [],
            message="PNG ampliado" if success else "falha; consulte o log",
            metrics=metrics,
        )

    def _speech(self, candidate: dict, texts: dict[str, str]) -> list[BenchmarkResult]:
        cfg = candidate["benchmark"]
        python = (self.root / self.settings.python_environments[candidate["adaptador"]]).resolve()
        workers = {"kokoro": "kokoro_benchmark.py"}
        worker = Path(__file__).parent / "workers" / workers[candidate["adaptador"]]
        results = []
        for voice in cfg["voices"]:
            identifier = f"tts_{candidate['id']}_{voice['id']}_{voice['language']}"
            target = self.output / f"{identifier}.wav"
            request = dict(
                cfg["model_files"], **voice, text=texts[voice["language"]], output=str(target)
            )
            request_file = self.output / f"{identifier}.request.json"
            atomic_write_json(request_file, request)
            started = time.perf_counter()
            with VramSampler() as sampler:
                completed = subprocess.run(
                    [str(python), str(worker), str(request_file)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=300,
                    check=False,
                )
            elapsed = time.perf_counter() - started
            (self.output / f"{identifier}.log").write_text(
                completed.stdout + completed.stderr, encoding="utf-8"
            )
            metrics_file = target.with_suffix(".metrics.json")
            success = completed.returncode == 0 and target.exists() and metrics_file.exists()
            metrics = json.loads(metrics_file.read_text(encoding="utf-8")) if success else {}
            metrics["vram_scope"] = "GPU inteira; amostragem 0,5 s"
            results.append(
                BenchmarkResult(
                    id=identifier,
                    category="tts",
                    candidate=candidate["id"],
                    status=CheckStatus.OK if success else CheckStatus.ERROR,
                    duration_seconds=round(elapsed, 3),
                    peak_vram_mb=sampler.peak,
                    outputs=[target] if success else [],
                    metrics=metrics,
                    message="voz gerada; tempo inclui carga do processo/modelo"
                    if success
                    else "falha; consulte o log da amostra",
                )
            )
        return results

    def _render(self, candidate: dict, spec: dict) -> BenchmarkResult:
        cfg = candidate["benchmark"]
        identifier = f"render_{cfg['resolution']}"
        target = self.output / f"{identifier}.mp4"
        remotion_dir = (self.root / "benchmarks" / "remotion").resolve()
        composition = cfg["composition"]
        npx_bin = shutil.which("npx") or ("npx.cmd" if os.name == "nt" else "npx")
        args = [
            npx_bin,
            "remotion",
            "render",
            "src/index.ts",
            composition,
            str(target),
            "--log=error",
        ]
        started = time.perf_counter()
        with VramSampler() as sampler:
            try:
                completed = subprocess.run(
                    args,
                    cwd=str(remotion_dir),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=300,
                    check=False,
                )
                log = completed.stdout + completed.stderr
                exit_code = completed.returncode
            except (OSError, subprocess.TimeoutExpired) as exc:
                log = str(exc)
                exit_code = -1
        elapsed = time.perf_counter() - started
        (self.output / f"{identifier}.log").write_text(log, encoding="utf-8")
        metrics = {
            "resolution": cfg["resolution"],
            "width": cfg["width"],
            "height": cfg["height"],
            "fps": cfg["fps"],
            "duration_seconds": cfg["duration_seconds"],
            "vram_scope": "GPU inteira; amostragem 0,5 s",
        }
        success = exit_code == 0 and target.is_file() and target.stat().st_size > 0
        if success:
            probe = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "stream=width,height,nb_frames",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "json",
                    str(target),
                ],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if probe.returncode == 0:
                info = json.loads(probe.stdout)
                stream = info["streams"][0]
                metrics.update(
                    actual_width=int(stream["width"]),
                    actual_height=int(stream["height"]),
                    frames=int(
                        stream.get("nb_frames") or round(cfg["duration_seconds"] * cfg["fps"])
                    ),
                    video_seconds=float(info["format"]["duration"]),
                )
                success = (
                    metrics["actual_width"] == cfg["width"]
                    and metrics["actual_height"] == cfg["height"]
                    and abs(metrics["video_seconds"] - cfg["duration_seconds"]) < 0.2
                )
            else:
                success = False
        return BenchmarkResult(
            id=identifier,
            category="render",
            candidate=candidate["id"],
            status=CheckStatus.OK if success else CheckStatus.ERROR,
            duration_seconds=round(elapsed, 3),
            peak_vram_mb=sampler.peak,
            outputs=[target] if success else [],
            message=f"render Remotion {cfg['resolution']} concluído"
            if success
            else "falha; consulte o log",
            metrics=metrics,
        )
