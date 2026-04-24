"""Tests for stacktrace_filter.flamegraph and flamegraph_cli."""
from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.flamegraph import (
    FoldedStack,
    _traceback_to_folded,
    build_flamegraph,
    render_flamegraph,
)
from stacktrace_filter.flamegraph_cli import build_flamegraph_parser, main


def _frame(filename="app/main.py", name="run", lineno=10) -> Frame:
    return Frame(filename=filename, name=name, lineno=lineno, context=None)


def _tb(exc_type="ValueError", exc_value="bad", frames=None) -> Traceback:
    if frames is None:
        frames = [_frame()]
    return Traceback(exc_type=exc_type, exc_value=exc_value, frames=frames)


# --- unit tests ---

def test_folded_stack_render():
    fs = FoldedStack(frames=["a.py:foo:1", "b.py:bar:2"], count=3)
    assert fs.render() == "a.py:foo:1;b.py:bar:2 3"


def test_traceback_to_folded_single_frame():
    tb = _tb(frames=[_frame("app/main.py", "run", 10)])
    fs = _traceback_to_folded(tb)
    assert fs.count == 1
    assert fs.frames == ["app/main.py:run:10"]


def test_build_flamegraph_aggregates_identical():
    tb = _tb(frames=[_frame()])
    stacks = build_flamegraph([tb, tb, tb])
    assert len(stacks) == 1
    assert stacks[0].count == 3


def test_build_flamegraph_distinct_stacks():
    tb1 = _tb(frames=[_frame(lineno=1)])
    tb2 = _tb(frames=[_frame(lineno=2)])
    stacks = build_flamegraph([tb1, tb2])
    assert len(stacks) == 2


def test_build_flamegraph_empty():
    assert build_flamegraph([]) == []


def test_render_flamegraph_newline_separated():
    stacks = [
        FoldedStack(["a.py:f:1"], 2),
        FoldedStack(["b.py:g:3"], 1),
    ]
    result = render_flamegraph(stacks)
    lines = result.splitlines()
    assert len(lines) == 2
    assert lines[0].endswith(" 2")
    assert lines[1].endswith(" 1")


# --- CLI tests ---

@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        Traceback (most recent call last):
          File "app/main.py", line 10, in run
            result = compute()
        ValueError: bad input
    """)
    p = tmp_path / "app.log"
    p.write_text(content)
    return p


def test_build_parser_defaults():
    p = build_flamegraph_parser()
    args = p.parse_args([])
    assert args.file is None
    assert args.output is None


def test_main_missing_file_exits():
    with pytest.raises(SystemExit) as exc_info:
        main(["nonexistent_file.log"])
    assert exc_info.value.code == 1


def test_main_reads_file(log_file: Path, capsys):
    main([str(log_file)])
    out = capsys.readouterr().out
    assert "app/main.py" in out


def test_main_reads_stdin(log_file: Path, capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", log_file.open())
    main([])
    out = capsys.readouterr().out
    assert "app/main.py" in out


def test_main_writes_output_file(log_file: Path, tmp_path: Path):
    out_file = tmp_path / "stacks.txt"
    main([str(log_file), "-o", str(out_file)])
    assert out_file.exists()
    assert "app/main.py" in out_file.read_text()
