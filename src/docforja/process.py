from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str


class ProcessRunner:
    def run(
        self,
        args: Sequence[str],
        *,
        timeout: float = 15,
        cwd: Path | None = None,
    ) -> ProcessResult:
        completed = subprocess.run(
            list(args),
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return ProcessResult(completed.returncode, completed.stdout, completed.stderr)
