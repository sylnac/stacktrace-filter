"""Tests for stacktrace_filter.replay."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.replay import ReplayOptions, replay


def _make_tb() -> Traceback:
    frame = Frame(
        filename="app/main.py",
        lineno=10,
        name="run",
        line="result = compute()",
    )
    return Traceback(
        frames=[frame],
        exc_type="RuntimeError",
        exc_value="something went wrong",
    )


def _write_snapshot(path: Path, tb: Traceback) -> None:
    data = [
        {
            "frames": [
                {
                    "filename": f.filename,
                    "lineno": f.lineno,
                    "name": f.name,
                    "line": f.line,
                }
                for f in tb.frames
            ],
            "exc_type": tb.exc_type,
            "exc_value": tb.exc_value,
            "label": None,
        }
    ]
    path.write_text(json.dumps(data))


def test_replay_contains_exception(tmp_path: Path) -> None:
    snap = tmp_path / "snap.json"
    _write_snapshot(snap, _make_tb())
    result = replay(ReplayOptions(snapshot_path=snap))
    assert "RuntimeError" in result


def test_replay_empty_snapshot(tmp_path: Path) -> None:
    snap = tmp_path / "empty.json"
    snap.write_text("[]")
    result = replay(ReplayOptions(snapshot_path=snap))
    assert "empty" in result


def test_replay_no_collapse_shows_frame(tmp_path: Path) -> None:
    snap = tmp_path / "snap.json"
    _write_snapshot(snap, _make_tb())
    result = replay(ReplayOptions(snapshot_path=snap, no_collapse=True))
    assert "app/main.py" in result


def test_replay_json_format(tmp_path: Path) -> None:
    snap = tmp_path / "snap.json"
    _write_snapshot(snap, _make_tb())
    result = replay(ReplayOptions(snapshot_path=snap, export_format="json"))
    parsed = json.loads(result)
    assert isinstance(parsed, list)
    assert parsed[0]["exc_type"] == "RuntimeError"
