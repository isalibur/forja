import pytest

from docforja.doctor import Doctor, _version_tuple
from docforja.models import CheckStatus
from docforja.process import ProcessResult
from docforja.settings import AppSettings, PathSettings, ServiceSettings, VoiceStudioSettings


class FakeRunner:
    def run(self, args, *, timeout=15, cwd=None):
        command = " ".join(args)
        if "query-gpu" in command:
            return ProcessResult(0, "NVIDIA GeForce RTX 3060, 12288, 600.00\n", "")
        if "ffmpeg -version" in command:
            return ProcessResult(0, "ffmpeg version 8.0\n", "")
        if "ffmpeg -hide_banner -encoders" in command:
            return ProcessResult(0, " V....D h264_nvenc NVIDIA NVENC\n", "")
        if "node --version" in command:
            return ProcessResult(0, "v20.18.0\n", "")
        raise AssertionError(f"unexpected command: {command}")


@pytest.fixture
def settings(tmp_path):
    return AppSettings(
        minimum_free_disk_gb=0,
        paths=PathSettings(projects=tmp_path / "projects", global_assets=tmp_path / "global"),
        services=[
            ServiceSettings(name="Ollama", url="http://ollama/api/tags"),
            ServiceSettings(name="ComfyUI", url="http://comfy/system_stats"),
        ],
    )


def fake_http(url: str, timeout: float):
    if "ollama" in url:
        return 200, {"models": [{"name": "qwen3:8b"}, {"name": "qwen2.5vl:7b"}]}
    return 200, {"system": "ok"}


def test_version_tuple_handles_node_prefix():
    assert _version_tuple("v20.18.0") == (20, 18, 0)


def test_gpu_parser_never_exposes_environment_secrets(settings, monkeypatch):
    monkeypatch.setattr("docforja.doctor.shutil.which", lambda name: f"C:/{name}.exe")
    monkeypatch.setattr("docforja.doctor.importlib.util.find_spec", lambda name: object())
    doctor = Doctor(
        settings,
        runner=FakeRunner(),
        http_get=fake_http,
        environ={
            "NINEROUTER_COMBO": "combo-secret-name",
            "DOCFORJA_LOCAL_TOKEN": "super-secret-token",
        },
    )

    report = doctor.run()
    gpu = next(item for item in report.checks if item.id == "gpu")
    serialized = report.model_dump_json()

    assert gpu.status == CheckStatus.OK
    assert gpu.details["vram_mb"] == 12288
    assert "super-secret-token" not in serialized
    assert "combo-secret-name" not in serialized


def test_voicestudio_e_reportado_como_opcional(settings, monkeypatch):
    """O doctor mostra o estado do VoiceStudio e a engine registrada."""
    monkeypatch.setattr("docforja.doctor.shutil.which", lambda name: f"C:/{name}.exe")
    monkeypatch.setattr("docforja.doctor.importlib.util.find_spec", lambda name: object())
    configurado = settings.model_copy(
        update={
            "voicestudio": VoiceStudioSettings(
                engine="indextts", engines_comerciais=["indextts"]
            )
        }
    )

    doctor = Doctor(configurado, runner=FakeRunner(), http_get=fake_http, environ={})
    report = doctor.run()
    checagem = next(item for item in report.checks if item.id == "voicestudio")

    assert checagem.required is False
    assert checagem.status == CheckStatus.OK
    assert "engine registrada como comercial" in checagem.summary

    sem_registro = configurado.model_copy(
        update={"voicestudio": VoiceStudioSettings(engine="omnivoice")}
    )
    report_sem = Doctor(sem_registro, runner=FakeRunner(), http_get=fake_http, environ={}).run()
    checagem_sem = next(item for item in report_sem.checks if item.id == "voicestudio")

    assert "sem licença comercial registrada" in checagem_sem.summary


def test_ollama_reports_missing_models(settings, monkeypatch):
    monkeypatch.setattr("docforja.doctor.shutil.which", lambda name: f"C:/{name}.exe")
    monkeypatch.setattr("docforja.doctor.importlib.util.find_spec", lambda name: object())

    def missing_vision(url: str, timeout: float):
        if "ollama" in url:
            return 200, {"models": [{"name": "qwen3:8b"}]}
        return 200, {}

    report = Doctor(
        settings,
        runner=FakeRunner(),
        http_get=missing_vision,
        environ={"NINEROUTER_COMBO": "configured", "DOCFORJA_LOCAL_TOKEN": "configured"},
    ).run()

    models = next(item for item in report.checks if item.id == "ollama_models")
    assert models.status == CheckStatus.ERROR
    assert "qwen2.5vl" in models.summary


def test_service_timeout_becomes_diagnostic(settings, monkeypatch):
    monkeypatch.setattr("docforja.doctor.shutil.which", lambda name: f"C:/{name}.exe")
    monkeypatch.setattr("docforja.doctor.importlib.util.find_spec", lambda name: object())

    def timeout(url: str, seconds: float):
        raise TimeoutError

    report = Doctor(
        settings,
        runner=FakeRunner(),
        http_get=timeout,
        environ={},
    ).run()

    service = next(item for item in report.checks if item.id == "service_ollama")
    assert service.status == CheckStatus.ERROR
    assert service.summary == "offline ou inacessível"
