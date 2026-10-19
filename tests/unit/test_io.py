import json

from docforja.io import atomic_write_json


def test_atomic_write_json_replaces_destination(tmp_path):
    destination = tmp_path / "nested" / "report.json"
    atomic_write_json(destination, {"value": 1})
    atomic_write_json(destination, {"value": 2})

    assert json.loads(destination.read_text(encoding="utf-8")) == {"value": 2}
    assert list(destination.parent.glob("*.tmp")) == []
