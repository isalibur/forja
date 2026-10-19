import json
import wave

import pytest
import yaml

from docforja.models import BenchmarkReport, BenchmarkResult, CheckStatus
from docforja.real_benchmark import RealBenchmarkRunner, benchmark_lock, bind_workflow
from docforja.settings import AppSettings, PathSettings, ServiceSettings
from docforja.workers.whisperx_align_benchmark import prepare_audio


def test_binding_does_not_modify_template():
    template = {"1": {"inputs": {"text": "original"}}}
    assert (
        bind_workflow(template, {"prompt": "1.text"}, {"prompt": "changed"})["1"]["inputs"]["text"]
        == "changed"
    )
    assert template["1"]["inputs"]["text"] == "original"
    with pytest.raises(ValueError, match="ausente"):
        bind_workflow(template, {"prompt": "1.text"}, {})


def test_image_failure_not_reported_as_success(tmp_path, httpx_mock, monkeypatch):
    (tmp_path / "config").mkdir()
    (tmp_path / "workflow.json").write_text(json.dumps({"1": {"inputs": {"text": ""}}}))
    (tmp_path / "bindings.yaml").write_text(yaml.safe_dump({"prompt": "1.text"}))
    settings = AppSettings(
        paths=PathSettings(benchmark_output=tmp_path / "out"),
        services=[ServiceSettings(name="ComfyUI", url="http://comfy/system_stats")],
    )
    runner = RealBenchmarkRunner(settings, tmp_path / "config")
    runner.output.mkdir(parents=True)
    monkeypatch.setattr("docforja.real_benchmark.VramSampler._sample", lambda self: None)
    httpx_mock.add_response(
        url="http://comfy/queue", json={"queue_running": [], "queue_pending": []}, is_reusable=True
    )
    httpx_mock.add_response(url="http://comfy/prompt", method="POST", json={"prompt_id": "123"})
    httpx_mock.add_response(
        url="http://comfy/history/123",
        json={"123": {"status": {"status_str": "error"}, "outputs": {}}},
    )
    httpx_mock.add_response(url="http://comfy/free", method="POST", json={})
    candidate = {
        "id": "test",
        "benchmark": {
            "workflow": "workflow.json",
            "bindings": "bindings.yaml",
            "seed": 1,
            "parameters": {"width": 32, "height": 32},
        },
    }
    result = runner._images(candidate, [{"id": "a", "texto": "hello"}])[0]
    assert result.status == "error"
    assert result.outputs == []


def test_busy_comfy_queue_is_not_modified(tmp_path, httpx_mock):
    (tmp_path / "w.json").write_text("{}")
    (tmp_path / "b.yaml").write_text("{}")
    runner = RealBenchmarkRunner(
        AppSettings(services=[ServiceSettings(name="ComfyUI", url="http://comfy/system_stats")]),
        tmp_path / "config",
    )
    httpx_mock.add_response(
        url="http://comfy/queue", json={"queue_running": [[1]], "queue_pending": []}
    )
    with pytest.raises(RuntimeError, match="andamento"):
        runner._images({"benchmark": {"workflow": "w.json", "bindings": "b.yaml"}}, [])


def test_benchmark_lock_is_exclusive_and_released(tmp_path):
    path = tmp_path / "gpu.lock"
    with (
        benchmark_lock(path),
        pytest.raises(RuntimeError, match="Outro benchmark"),
        benchmark_lock(path),
    ):
        pytest.fail("dois benchmarks adquiriram o mesmo lock")
    with benchmark_lock(path):
        pass


def test_partial_run_preserves_other_categories(tmp_path):
    config = tmp_path / "config"
    config.mkdir()
    (config / "modelos.yaml").write_text("imagem:\n  candidatos:\n    - id: pending\n")
    (config / "benchmark.yaml").write_text("{}")
    previous = BenchmarkReport(
        results=[
            BenchmarkResult(
                id="voice",
                category="tts",
                candidate="voice",
                status=CheckStatus.OK,
                duration_seconds=2,
            )
        ]
    )
    (config / "benchmark.json").write_text(previous.model_dump_json())
    runner = RealBenchmarkRunner(
        AppSettings(paths=PathSettings(benchmark_output=tmp_path / "out")),
        config,
    )
    runner.run(["imagem"])
    report = BenchmarkReport.model_validate_json((config / "benchmark.json").read_text())
    assert [item.category for item in report.results] == ["tts", "imagem"]
    assert report.results[1].status == CheckStatus.SKIPPED
    assert (runner.output / "report.json").is_file()


def test_alignment_audio_repeats_without_changing_source(tmp_path):
    source = tmp_path / "source.wav"
    target = tmp_path / "minute.wav"
    with wave.open(str(source), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(10)
        output.writeframes(b"\x01\x00" * 19)
    original = source.read_bytes()
    assert prepare_audio(source, target, 3, 6) == 1.9
    with wave.open(str(target), "rb") as output:
        assert output.getnframes() == 60
        assert output.readframes(57) == b"\x01\x00" * 57
        assert output.readframes(3) == b"\x00" * 6
    assert source.read_bytes() == original


def test_render_benchmark_mocked_success(tmp_path, monkeypatch):
    import subprocess

    config = tmp_path / "config"
    config.mkdir()
    (config / "modelos.yaml").write_text(yaml.safe_dump({"render": {"candidatos": []}}))
    (config / "benchmark.yaml").write_text(yaml.safe_dump({"render": {}}))
    runner = RealBenchmarkRunner(
        AppSettings(paths=PathSettings(benchmark_output=tmp_path / "out")),
        config,
    )
    runner.output.mkdir(parents=True)
    monkeypatch.setattr("docforja.real_benchmark.VramSampler._sample", lambda self: None)

    target_video = runner.output / "render_1080p.mp4"

    def mock_subprocess_run(args, **kwargs):
        if "remotion" in args:
            target_video.write_bytes(b"fake_mp4_content")
            return subprocess.CompletedProcess(args, 0, stdout="Rendered", stderr="")
        if "ffprobe" in args:
            probe_out = json.dumps(
                {
                    "streams": [{"width": 1920, "height": 1080, "nb_frames": 300}],
                    "format": {"duration": "10.0"},
                }
            )
            return subprocess.CompletedProcess(args, 0, stdout=probe_out, stderr="")
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", mock_subprocess_run)

    candidate = {
        "id": "remotion-1080p",
        "benchmark": {
            "composition": "benchmark-1080p",
            "resolution": "1080p",
            "width": 1920,
            "height": 1080,
            "fps": 30,
            "duration_seconds": 10,
        },
    }
    result = runner._render(candidate, {})
    assert result.status == CheckStatus.OK
    assert result.outputs == [target_video]
    assert result.metrics["actual_width"] == 1920
    assert result.metrics["video_seconds"] == 10.0


def test_parallax_benchmark_mocked_success(tmp_path, monkeypatch):
    import subprocess
    from pathlib import Path

    config = tmp_path / "config"
    config.mkdir()
    (config / "modelos.yaml").write_text(yaml.safe_dump({"parallax": {"candidatos": []}}))
    (config / "benchmark.yaml").write_text(yaml.safe_dump({"parallax": {"duracao_segundos": 5}}))
    settings = AppSettings(
        paths=PathSettings(benchmark_output=tmp_path / "out"),
        python_environments={"depthflow": Path("fake/python.exe")},
    )
    runner = RealBenchmarkRunner(settings, config)
    runner.output.mkdir(parents=True)
    monkeypatch.setattr("docforja.real_benchmark.VramSampler._sample", lambda self: None)

    source_img = tmp_path / "source.png"
    source_img.write_bytes(b"fake_image")
    known_results = [
        BenchmarkResult(
            id="source_id",
            category="imagem",
            candidate="flux",
            status=CheckStatus.OK,
            outputs=[source_img],
            duration_seconds=1.0,
        )
    ]

    target_video = runner.output / "parallax_depthflow-small.mp4"

    def mock_subprocess_run(args, **kwargs):
        if "depthflow_benchmark.py" in str(args[1]):
            target_video.write_bytes(b"fake_mp4_content")
            return subprocess.CompletedProcess(args, 0, stdout="Success", stderr="")
        if "ffprobe" in args:
            probe_out = json.dumps(
                {
                    "streams": [{"width": 1024, "height": 576, "nb_frames": 120}],
                    "format": {"duration": "5.0"},
                }
            )
            return subprocess.CompletedProcess(args, 0, stdout=probe_out, stderr="")
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", mock_subprocess_run)

    candidate = {
        "id": "depthflow-small",
        "adaptador": "depthflow",
        "benchmark": {
            "source_result_id": "source_id",
            "model": "small",
            "fps": 24,
            "width": 1024,
            "height": 576,
        },
    }
    result = runner._parallax(candidate, {"parallax": {"duracao_segundos": 5}}, known_results)
    assert result.status == CheckStatus.OK
    assert result.outputs == [target_video]
    assert result.metrics["width"] == 1024
    assert result.metrics["height"] == 576
    assert result.metrics["frames"] == 120
    assert result.metrics["video_seconds"] == 5.0


