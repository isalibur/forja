from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import httpx

from docforja.models import CheckResult, CheckStatus, DoctorReport
from docforja.process import ProcessRunner
from docforja.settings import AppSettings, ServiceSettings

HttpGetter = Callable[[str, float], tuple[int, object]]

REQUIRED_ENV = ("NINEROUTER_COMBO", "DOCFORJA_LOCAL_TOKEN")
OPTIONAL_ENV = (
    "NINEROUTER_API_KEY",
    "OPENROUTER_API_KEY",
    "PEXELS_API_KEY",
    "PIXABAY_API_KEY",
    "EUROPEANA_API_KEY",
    "SMITHSONIAN_API_KEY",
    "FREESOUND_CLIENT_ID",
    "FREESOUND_CLIENT_SECRET",
    "OPENTOPOGRAPHY_API_KEY",
    "COPERNICUS_USER",
    "COPERNICUS_PASSWORD",
    "WIKIMEDIA_USER_AGENT",
)


def _default_http_get(url: str, timeout: float) -> tuple[int, object]:
    response = httpx.get(url, timeout=timeout)
    try:
        body: object = response.json()
    except ValueError:
        body = response.text
    return response.status_code, body


def _version_tuple(value: str) -> tuple[int, ...]:
    match = re.search(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?", value)
    return tuple(int(part) for part in match.groups(default="0")) if match else ()


def _nearest_existing(path: Path) -> Path:
    candidate = path.resolve()
    while not candidate.exists() and candidate.parent != candidate:
        candidate = candidate.parent
    return candidate


class Doctor:
    def __init__(
        self,
        settings: AppSettings,
        *,
        runner: ProcessRunner | None = None,
        http_get: HttpGetter = _default_http_get,
        environ: dict[str, str] | None = None,
    ) -> None:
        self.settings = settings
        self.runner = runner or ProcessRunner()
        self.http_get = http_get
        self.environ = dict(os.environ if environ is None else environ)

    def run(self) -> DoctorReport:
        checks = [
            self._check_gpu(),
            self._check_ffmpeg(),
            self._check_node(),
            self._check_remotion_skills(),
            self._check_disk(),
        ]
        checks.extend(self._check_service(service) for service in self.settings.services)
        checks.append(self._check_voicestudio())
        checks.extend(
            [
                self._check_ollama_models(),
                self._check_python_tool("depthflow", "DepthFlow", required=True),
                self._check_python_tool("rembg", "rembg/BiRefNet", required=True),
                self._check_python_tool("whisperx", "WhisperX", required=True),
                self._check_python_tool("realesrgan", "Real-ESRGAN", required=True),
                self._check_env(),
            ]
        )
        return DoctorReport(checks=checks)

    def _check_gpu(self) -> CheckResult:
        if not shutil.which("nvidia-smi"):
            return CheckResult(
                id="gpu",
                label="GPU NVIDIA",
                status=CheckStatus.ERROR,
                summary="nvidia-smi não encontrado",
            )
        try:
            result = self.runner.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total,driver_version",
                    "--format=csv,noheader,nounits",
                ]
            )
        except (OSError, TimeoutError, subprocess.TimeoutExpired):
            return CheckResult(
                id="gpu",
                label="GPU NVIDIA",
                status=CheckStatus.ERROR,
                summary="não foi possível consultar a GPU",
            )
        if result.returncode != 0:
            return CheckResult(
                id="gpu",
                label="GPU NVIDIA",
                status=CheckStatus.ERROR,
                summary="nvidia-smi retornou erro",
            )
        parts = [part.strip() for part in result.stdout.splitlines()[0].split(",")]
        if len(parts) != 3:
            return CheckResult(
                id="gpu",
                label="GPU NVIDIA",
                status=CheckStatus.ERROR,
                summary="saída inesperada do nvidia-smi",
            )
        name, memory, driver = parts
        memory_mb = int(float(memory))
        status = CheckStatus.OK if memory_mb >= 12_000 else CheckStatus.WARNING
        return CheckResult(
            id="gpu",
            label="GPU NVIDIA",
            status=status,
            summary=f"{name} | {memory_mb} MiB | driver {driver}",
            details={"name": name, "vram_mb": memory_mb, "driver": driver},
        )

    def _check_ffmpeg(self) -> CheckResult:
        if not shutil.which("ffmpeg"):
            return CheckResult(
                id="ffmpeg",
                label="FFmpeg/NVENC",
                status=CheckStatus.ERROR,
                summary="FFmpeg não encontrado",
            )
        try:
            version = self.runner.run(["ffmpeg", "-version"])
            encoders = self.runner.run(["ffmpeg", "-hide_banner", "-encoders"])
        except (OSError, TimeoutError, subprocess.TimeoutExpired):
            return CheckResult(
                id="ffmpeg",
                label="FFmpeg/NVENC",
                status=CheckStatus.ERROR,
                summary="não foi possível executar o FFmpeg",
            )
        nvenc = "h264_nvenc" in encoders.stdout or "h264_nvenc" in encoders.stderr
        first_line = (version.stdout or version.stderr).splitlines()[0]
        return CheckResult(
            id="ffmpeg",
            label="FFmpeg/NVENC",
            status=CheckStatus.OK if version.returncode == 0 and nvenc else CheckStatus.ERROR,
            summary=f"{first_line} | NVENC {'disponível' if nvenc else 'ausente'}",
            details={"nvenc": nvenc},
        )

    def _check_node(self) -> CheckResult:
        if not shutil.which("node"):
            return CheckResult(
                id="node",
                label="Node.js",
                status=CheckStatus.ERROR,
                summary="Node.js não encontrado",
            )
        result = self.runner.run(["node", "--version"])
        version = result.stdout.strip()
        supported = _version_tuple(version) >= (20, 0, 0)
        return CheckResult(
            id="node",
            label="Node.js",
            status=CheckStatus.OK if supported else CheckStatus.ERROR,
            summary=f"{version or 'versão desconhecida'} | mínimo 20",
            details={"version": version},
        )

    def _check_remotion_skills(self) -> CheckResult:
        path = Path(".agents/skills")
        installed = path.exists() and any(path.iterdir())
        return CheckResult(
            id="remotion_skills",
            label="Remotion Agent Skills",
            status=CheckStatus.OK if installed else CheckStatus.WARNING,
            summary="instaladas" if installed else "ainda não instaladas",
            required=False,
        )

    def _check_disk(self) -> CheckResult:
        targets = {
            "projetos": self.settings.paths.projects,
            "global": self.settings.paths.global_assets,
        }
        free_values: list[int] = []
        details: dict[str, str | int] = {}
        for name, configured in targets.items():
            existing = _nearest_existing(configured)
            free_gb = int(shutil.disk_usage(existing).free / 1024**3)
            free_values.append(free_gb)
            details[f"{name}_path"] = str(configured)
            details[f"{name}_free_gb"] = free_gb
        minimum = min(free_values)
        return CheckResult(
            id="disk",
            label="Espaço em disco",
            status=CheckStatus.OK
            if minimum >= self.settings.minimum_free_disk_gb
            else CheckStatus.WARNING,
            summary=f"{minimum} GB livres | recomendado >= {self.settings.minimum_free_disk_gb} GB",
            details=details,
        )

    def _check_service(self, service: ServiceSettings) -> CheckResult:
        try:
            status_code, _ = self.http_get(service.url, service.timeout_seconds)
            online = 200 <= status_code < 500
            return CheckResult(
                id=f"service_{service.name.lower()}",
                label=service.name,
                status=CheckStatus.OK if online else CheckStatus.ERROR,
                summary=f"online | HTTP {status_code}"
                if online
                else f"respondeu HTTP {status_code}",
                required=service.required,
            )
        except (httpx.HTTPError, OSError, TimeoutError):
            return CheckResult(
                id=f"service_{service.name.lower()}",
                label=service.name,
                status=CheckStatus.ERROR if service.required else CheckStatus.WARNING,
                summary="offline ou inacessível",
                required=service.required,
            )

    def _check_voicestudio(self) -> CheckResult:
        """Confere o serviço local do VoiceStudio (opcional) e a engine em uso."""
        base_url = self.settings.voicestudio.base_url.rstrip("/")
        url = f"{base_url}/v1/models"
        try:
            status_code, _ = self.http_get(url, 3.0)
            online = status_code < 500
            resumo = f"online | HTTP {status_code}" if online else f"respondeu HTTP {status_code}"
        except (httpx.HTTPError, OSError, TimeoutError):
            online = False
            resumo = "offline ou inacessível"
        return CheckResult(
            id="voicestudio",
            label="VoiceStudio (opcional)",
            status=CheckStatus.OK if online else CheckStatus.SKIPPED,
            summary=f"{resumo} | engine: {self.settings.voicestudio.engine}",
            required=False,
        )

    def _check_ollama_models(self) -> CheckResult:
        service = next((item for item in self.settings.services if item.name == "Ollama"), None)
        if service is None:
            return CheckResult(
                id="ollama_models",
                label="Modelos Ollama",
                status=CheckStatus.SKIPPED,
                summary="serviço Ollama não configurado",
            )
        try:
            status_code, body = self.http_get(service.url, service.timeout_seconds)
        except (httpx.HTTPError, OSError, TimeoutError):
            return CheckResult(
                id="ollama_models",
                label="Modelos Ollama",
                status=CheckStatus.ERROR,
                summary="não foi possível consultar os modelos",
            )
        model_items = body.get("models", []) if isinstance(body, dict) else []
        names = {
            str(item.get("name", "")).split(":")[0]
            for item in model_items
            if isinstance(item, dict)
        }
        required = {"qwen3", "qwen2.5vl"}
        missing = sorted(required - names)
        return CheckResult(
            id="ollama_models",
            label="Modelos Ollama",
            status=CheckStatus.OK if status_code == 200 and not missing else CheckStatus.ERROR,
            summary="modelos necessários disponíveis"
            if not missing
            else f"faltando: {', '.join(missing)}",
            details={"installed": ", ".join(sorted(names))},
        )

    def _check_python_tool(self, module: str, label: str, *, required: bool) -> CheckResult:
        executable = shutil.which(module)
        environment_python = self.settings.python_environments.get(module)
        external_available = False
        if environment_python and environment_python.exists():
            try:
                probe = self.runner.run(
                    [
                        str(environment_python),
                        "-c",
                        f"import {module}",
                    ],
                    timeout=60,
                )
                external_available = probe.returncode == 0
            except (OSError, TimeoutError, subprocess.TimeoutExpired):
                external_available = False
        available = (
            importlib.util.find_spec(module) is not None
            or executable is not None
            or external_available
        )
        return CheckResult(
            id=f"python_{module}",
            label=label,
            status=CheckStatus.OK if available else CheckStatus.ERROR,
            summary=(
                f"disponível como ferramenta externa: {executable}"
                if executable
                else f"disponível no ambiente isolado: {environment_python}"
                if external_available
                else "disponível neste ambiente"
                if available
                else "pacote não instalado neste ambiente"
            ),
            required=required,
        )

    def _check_env(self) -> CheckResult:
        required_missing = [key for key in REQUIRED_ENV if not self.environ.get(key, "").strip()]
        optional_count = sum(bool(self.environ.get(key, "").strip()) for key in OPTIONAL_ENV)
        summary = (
            f"obrigatórias configuradas | {optional_count}/{len(OPTIONAL_ENV)} opcionais"
            if not required_missing
            else f"faltando: {', '.join(required_missing)}"
        )
        return CheckResult(
            id="environment",
            label="Configuração .env",
            status=CheckStatus.OK if not required_missing else CheckStatus.ERROR,
            summary=summary,
            details={
                "required_configured": len(REQUIRED_ENV) - len(required_missing),
                "optional_configured": optional_count,
            },
        )
