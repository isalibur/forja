import json

from docforja.io import atomic_write_json, atomic_write_text


def test_atomic_write_json_replaces_destination(tmp_path):
    destination = tmp_path / "nested" / "report.json"
    atomic_write_json(destination, {"value": 1})
    atomic_write_json(destination, {"value": 2})

    assert json.loads(destination.read_text(encoding="utf-8")) == {"value": 2}
    assert list(destination.parent.glob("*.tmp")) == []


def test_atomic_write_text_replaces_destination(tmp_path):
    destination = tmp_path / "nested" / "report.md"
    atomic_write_text(destination, "Primeiro\n")
    atomic_write_text(destination, "Segundo\n")

    assert destination.read_text(encoding="utf-8") == "Segundo\n"
    assert list(destination.parent.glob("*.tmp")) == []
