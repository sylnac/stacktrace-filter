"""Tests for stacktrace_filter.context_extractor."""
from __future__ import annotations

import textwrap
import tempfile
import os
import linecache

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.context_extractor import extract, _extract_context


def _write_tmp(content: str) -> str:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False
    )
    f.write(textwrap.dedent(content))
    f.flush()
    f.close()
    linecache.clearcache()
    return f.name


def _frame(filename: str, lineno: int) -> Frame:
    return Frame(
        filename=filename,
        lineno=lineno,
        function="dummy",
        source_line="x = 1",
    )


def _tb(frames: list) -> Traceback:
    return Traceback(
        frames=frames,
        exc_type="ValueError",
        exc_value="bad value",
        raw_lines=[],
    )


def test_extract_returns_annotated_traceback():
    path = _write_tmp("a = 1\nb = 2\nc = 3\nd = 4\ne = 5\n")
    tb = _tb([_frame(path, 3)])
    result = extract(tb)
    assert result.traceback is tb
    assert len(result.frames) == 1
    os.unlink(path)


def test_extract_error_line_matches():
    path = _write_tmp("x = 0\nraise ValueError\ny = 1\n")
    tb = _tb([_frame(path, 2)])
    result = extract(tb)
    af = result.frames[0]
    assert af.error_line is not None
    assert "raise" in af.error_line
    os.unlink(path)


def test_extract_context_radius():
    path = _write_tmp("\n".join(f"line{i}" for i in range(1, 11)) + "\n")
    ctx, _, start = _extract_context(path, 5, radius=2)
    assert start == 3
    assert len(ctx) == 5  # lines 3-7
    os.unlink(path)


def test_extract_clamps_at_start_of_file():
    path = _write_tmp("first\nsecond\nthird\n")
    ctx, error_line, start = _extract_context(path, 1, radius=3)
    assert start == 1
    assert error_line == "first"
    os.unlink(path)


def test_extract_missing_file_returns_empty():
    ctx, error_line, start = _extract_context("/no/such/file.py", 5, radius=2)
    assert ctx == []
    assert error_line is None


def test_extract_multiple_frames():
    path = _write_tmp("a\nb\nc\nd\ne\n")
    frames = [_frame(path, 1), _frame(path, 3), _frame(path, 5)]
    tb = _tb(frames)
    result = extract(tb)
    assert len(result.frames) == 3
    assert result.frames[1].error_line == "c"
    os.unlink(path)
