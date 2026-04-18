"""Tests for stacktrace_filter.exporter."""
import json
import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.exporter import (
    ExportOptions,
    export,
    export_json,
    export_markdown,
    export_text,
)


@pytest.fixture()
def tb():
    frames = [
        Frame("/app/main.py", 10, "run", "result = compute()"),
        Frame("/app/compute.py", 42, "compute", "return 1 / x"),
    ]
    return Traceback(frames=frames, exc_type="ZeroDivisionError", exc_message="division by zero")


def test_export_text_contains_exception(tb):
    out = export_text([tb])
    assert "ZeroDivisionError" in out
    assert "division by zero" in out


def test_export_text_contains_frames(tb):
    out = export_text([tb])
    assert "/app/main.py" in out
    assert "/app/compute.py" in out


def test_export_text_includes_hints(tb):
    out = export_text([tb], hints_map={0: ["Check divisor is non-zero"]})
    assert "Hint: Check divisor is non-zero" in out


def test_export_json_valid(tb):
    raw = export_json([tb])
    data = json.loads(raw)
    assert isinstance(data, list)
    assert data[0]["exception_type"] == "ZeroDivisionError"
    assert len(data[0]["frames"]) == 2


def test_export_json_hints(tb):
    raw = export_json([tb], hints_map={0: ["some hint"]})
    data = json.loads(raw)
    assert data[0]["hints"] == ["some hint"]


def test_export_markdown_header(tb):
    out = export_markdown([tb])
    assert "## `ZeroDivisionError`" in out


def test_export_markdown_code_block(tb):
    out = export_markdown([tb])
    assert "```" in out
    assert "return 1 / x" in out


def test_export_markdown_hints(tb):
    out = export_markdown([tb], hints_map={0: ["Check divisor"]})
    assert "**Hints:**" in out
    assert "- Check divisor" in out


def test_export_dispatch_json(tb):
    opts = ExportOptions(fmt="json")
    out = export([tb], opts)
    json.loads(out)  # should not raise


def test_export_dispatch_markdown(tb):
    opts = ExportOptions(fmt="markdown")
    out = export([tb], opts)
    assert "##" in out


def test_export_dispatch_text_default(tb):
    opts = ExportOptions(fmt="text")
    out = export([tb], opts)
    assert "ZeroDivisionError" in out
