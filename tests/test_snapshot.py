"""Tests for snapshot save/load/diff."""
import json
from pathlib import Path

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.snapshot import (
    Snapshot,
    diff_snapshots,
    load_snapshot,
    save_snapshot,
)


def _make_tb(exc_type: str = "ValueError", exc_msg: str = "bad") -> Traceback:
    frame = Frame(filename="app/main.py", lineno=10, name="run", text="run()")
    return Traceback(frames=[frame], exc_type=exc_type, exc_message=exc_msg, raw="")


def test_save_creates_file(tmp_path):
    snap = Snapshot(label="ci-run-1", tracebacks=[_make_tb()])
    out = tmp_path / "snap.json"
    save_snapshot(snap, out)
    assert out.exists()


def test_save_json_structure(tmp_path):
    snap = Snapshot(label="ci-run-1", tracebacks=[_make_tb()])
    out = tmp_path / "snap.json"
    save_snapshot(snap, out)
    data = json.loads(out.read_text())
    assert data["label"] == "ci-run-1"
    assert len(data["tracebacks"]) == 1


def test_roundtrip(tmp_path):
    tb = _make_tb("KeyError", "missing key")
    snap = Snapshot(label="run-42", tracebacks=[tb])
    out = tmp_path / "snap.json"
    save_snapshot(snap, out)
    loaded = load_snapshot(out)
    assert loaded.label == "run-42"
    assert len(loaded.tracebacks) == 1
    assert loaded.tracebacks[0].exc_type == "KeyError"
    assert loaded.tracebacks[0].exc_message == "missing key"


def test_roundtrip_frame_attributes(tmp_path):
    snap = Snapshot(label="x", tracebacks=[_make_tb()])
    out = tmp_path / "snap.json"
    save_snapshot(snap, out)
    loaded = load_snapshot(out)
    frame = loaded.tracebacks[0].frames[0]
    assert frame.filename == "app/main.py"
    assert frame.lineno == 10
    assert frame.name == "run"


def test_diff_added_removed():
    old = Snapshot("a", [_make_tb("ValueError"), _make_tb("KeyError")])
    new = Snapshot("b", [_make_tb("ValueError"), _make_tb("RuntimeError")])
    result = diff_snapshots(old, new)
    assert "KeyError" in result["removed"]
    assert "RuntimeError" in result["added"]
    assert "ValueError" in result["common"]


def test_diff_counts():
    old = Snapshot("a", [_make_tb(), _make_tb()])
    new = Snapshot("b", [_make_tb()])
    result = diff_snapshots(old, new)
    assert result["old_count"] == 2
    assert result["new_count"] == 1


def test_save_creates_parent_dirs(tmp_path):
    snap = Snapshot(label="x", tracebacks=[])
    out = tmp_path / "nested" / "deep" / "snap.json"
    save_snapshot(snap, out)
    assert out.exists()
