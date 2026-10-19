from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class ServiceSettings(BaseModel):
    name: str
    url: str
    required: bool = True
    timeout_seconds: float = 2.0


class PathSettings(BaseModel):
    projects: Path = Path("D:/DocForja/projetos")
    global_assets: Path = Path("D:/DocForja/global")
    comfyui: Path = Path("D:/DocForja/ComfyUI")
    benchmark_output: Path = Path("benchmark_out")


class LlmSettings(BaseModel):
    provedor: str = "openai_compat"
    base_url: str = "http://127.0.0.1:20128/v1"
    modelo: str = "default"


class AppSettings(BaseModel):
    minimum_free_disk_gb: int = 200
    paths: PathSettings = Field(default_factory=PathSettings)
    services: list[ServiceSettings] = Field(default_factory=list)
    python_environments: dict[str, Path] = Field(default_factory=dict)
    llm: dict[str, LlmSettings] = Field(default_factory=dict)


def load_settings(path: Path = Path("config/adaptadores.yaml")) -> AppSettings:
    if not path.exists():
        return AppSettings()
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle) or {}
    return AppSettings.model_validate(value)
