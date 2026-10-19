from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class CheckStatus(StrEnum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


class CheckResult(BaseModel):
    id: str
    label: str
    status: CheckStatus
    summary: str
    details: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    required: bool = True


class DoctorReport(BaseModel):
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    checks: list[CheckResult]

    @property
    def healthy(self) -> bool:
        return all(item.status not in {CheckStatus.ERROR} for item in self.checks if item.required)


class BenchmarkResult(BaseModel):
    id: str
    category: str
    candidate: str
    status: CheckStatus
    duration_seconds: float
    peak_vram_mb: int | None = None
    outputs: list[Path] = Field(default_factory=list)
    message: str = ""


class BenchmarkReport(BaseModel):
    schema_version: int = 1
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    results: list[BenchmarkResult]
