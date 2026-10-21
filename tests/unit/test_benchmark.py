import json
from pathlib import Path

import yaml

from docforja.benchmark import BenchmarkRunner
from docforja.models import CheckStatus
from docforja.process import ProcessResult


class FakeRunner:
    def __init__(self):
        self.calls = []

    def run(self, args, *, timeout=15, cwd=None):
        self.calls.append(list(args))
        Path(args[-1]).write_bytes(b"video")
        return ProcessResult(0, "", "")


def test_benchmark_runs_renders_sequentially_and_writes_report(tmp_path, monkeypatch):
    config = tmp_path / "config"
    config.mkdir()
    (config / "modelos.yaml").write_text(
        yaml.safe_dump(
            {
                "imagem": {"candidatos": [{"id": "image-a"}]},
                "tts": {"candidatos": [{"id": "kokoro-82m"}]},
            }
        ),
        encoding="utf-8",
    )
    runner = FakeRunner()
    ticks = iter([0.0, 1.0, 2.0, 4.5])
    monkeypatch.setattr("docforja.benchmark.shutil.which", lambda name: f"C:/{name}.exe")
    monkeypatch.setattr("docforja.benchmark.importlib.util.find_spec", lambda name: None)

    report = BenchmarkRunner(
        output_dir=tmp_path / "out",
        config_dir=config,
        runner=runner,
        clock=lambda: next(ticks),
    ).run()

    renders = [item for item in report.results if item.category == "render"]
    saved = json.loads((config / "benchmark.json").read_text(encoding="utf-8"))
    assert [item.status for item in renders] == [CheckStatus.OK, CheckStatus.OK]
    assert [item.duration_seconds for item in renders] == [1.0, 2.5]
    assert len(runner.calls) == 2
    assert saved["schema_version"] == 1


def test_benchmark_trata_voicestudio_como_servico_local(tmp_path, monkeypatch):
    config = tmp_path / "config"
    config.mkdir()
    (config / "modelos.yaml").write_text(
        yaml.safe_dump(
            {
                "tts": {
                    "candidatos": [
                        {
                            "id": "voicestudio-omnivoice",
                            "adaptador": "voicestudio",
                            "benchmark": {"base_url": "http://127.0.0.1:3900"},
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("docforja.benchmark.shutil.which", lambda name: None)
    monkeypatch.setattr("docforja.benchmark.importlib.util.find_spec", lambda name: None)

    class Resposta:
        status_code = 200

    monkeypatch.setattr("docforja.benchmark.httpx.get", lambda url, timeout: Resposta())

    report = BenchmarkRunner(output_dir=tmp_path / "out", config_dir=config).run()
    item = next(i for i in report.results if i.candidate == "voicestudio-omnivoice")

    assert item.category == "tts"
    assert item.status == CheckStatus.WARNING
    assert "online" in item.message


def test_benchmark_recognizes_configured_isolated_environment(tmp_path, monkeypatch):
    config = tmp_path / "config"
    config.mkdir()
    (config / "modelos.yaml").write_text("imagem: {}\ntts: {}\n", encoding="utf-8")
    isolated_python = tmp_path / "envs" / "align" / "python.exe"
    isolated_python.parent.mkdir(parents=True)
    isolated_python.touch()
    monkeypatch.setattr("docforja.benchmark.shutil.which", lambda name: None)
    monkeypatch.setattr("docforja.benchmark.importlib.util.find_spec", lambda name: None)

    report = BenchmarkRunner(
        output_dir=tmp_path / "out",
        config_dir=config,
        python_environments={"whisperx": isolated_python},
    ).run()

    whisperx = next(item for item in report.results if item.candidate == "whisperx")
    assert whisperx.status == CheckStatus.WARNING
    assert "disponível" in whisperx.message
