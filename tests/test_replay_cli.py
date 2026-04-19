"""Tests for stacktrace_filter.replay_cli."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from stacktrace_filter.replay_cli import build_replay_parser, main


@pytest.fixture()
def snapshot_file(tmp_path: Path) -> Path:
    frame = {"filename": "app/views.py", "lineno": 5, "name": "index", "line": "return render()"}
    data = [{"frames": [frame], "exc_type": "ValueError", "exc_value": "bad input", "label": None}]
    p = tmp_path / "snap.json"
    p.write_text(json.dumps(data))
    return p


def test_build_parser_defaults() -> None:
    parser = build_replay_parser()
    args = parser.parse_args(["snap.json"])
    assert args.export_format == "text"
    assert args.no_collapse is False
    assert args.no_color is False
    assert args.output is None


def test_main_missing_file_exits(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        main([str(tmp_path / "missing.json")])
    assert exc.value.code == 1


def test_main_outputs_exception(snapshot_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    main([str(snapshot_file)])
    captured = capsys.readouterr()
    assert "ValueError" in captured.out


def test_main_json_format(snapshot_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    main([str(snapshot_file), "--format", "json"])
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed[0]["exc_type"] == "ValueError"


def test_main_writes_output_file(snapshot_file: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.txt"
    main([str(snapshot_file), "-o", str(out)])
    assert out.exists()
    assert "ValueError" in out.read_text()
