from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

RAIZ_REPO = Path(__file__).resolve().parents[2]


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


class AlignmentSettings(BaseModel):
    modelo_asr: str = "base"
    modelo_alinhador: str | None = None


class VoiceStudioSettings(BaseModel):
    """Serviço local do VoiceStudio (app AGPL separado, API compatível com OpenAI)."""

    base_url: str = "http://127.0.0.1:3900"
    engine: str = "omnivoice"
    instrucoes: str = ""
    api_key: str = ""
    timeout_seconds: float = 60.0
    probe_timeout_seconds: float = 3.0


class OmniVoiceSettings(BaseModel):
    """OmniVoice local (clonagem de voz a partir de uma referência do usuário)."""

    modelo: str = "k2-fsa/OmniVoice"
    cache: str = ""
    velocidade: float = 0.92
    passos: int = 64


class AppSettings(BaseModel):
    minimum_free_disk_gb: int = 200
    paths: PathSettings = Field(default_factory=PathSettings)
    services: list[ServiceSettings] = Field(default_factory=list)
    python_environments: dict[str, Path] = Field(default_factory=dict)
    llm: dict[str, LlmSettings] = Field(default_factory=dict)
    alinhamento: AlignmentSettings = Field(default_factory=AlignmentSettings)
    voicestudio: VoiceStudioSettings = Field(default_factory=VoiceStudioSettings)
    omnivoice: OmniVoiceSettings = Field(default_factory=OmniVoiceSettings)

    def resolver_ambiente(self, nome: str) -> Path | None:
        """Resolve o interpretador do ambiente; caminhos relativos partem da raiz do repositório."""
        caminho = self.python_environments.get(nome)
        if caminho is None:
            return None
        if caminho.is_absolute():
            return caminho
        return RAIZ_REPO / caminho


def load_settings(path: Path = Path("config/adaptadores.yaml")) -> AppSettings:
    if not path.exists():
        return AppSettings()
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle) or {}
    return AppSettings.model_validate(value)
