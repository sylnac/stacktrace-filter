"""Tests for stacktrace_filter.metrics."""
from __future__ import annotations
import json
from pathlib import Path
import pytest
from stacktrace_filter.parser import Traceback, Frame
from stacktrace_filter.metrics import compute_metrics, render_metrics


def _frame(filename="app/foo.py", lineno=10, module="app.foo", func="bar", context="x = 1"):
    return Frame(filename=filename, lineno=lineno, module=module, func=func, context=context)


def _tb(exc_type="ValueError", exc_value="bad", frames=None):
    return Traceback(
        exc_type=exc_type,
        exc_value=exc_value,
        frames=frames or [_frame()],
    )


def test_empty_input():
    report = compute_metrics([])
    assert report.total == 0
    assert report.avg_depth == 0.0
    assert report.by_exception == {}


def test_total_count():
    tbs = [_tb(), _tb(), _tb(exc_type="KeyError")]
    report = compute_metrics(tbs)
    assert report.total == 3


def test_by_exception_counts():
    tbs = [_tb("ValueError"), _tb("ValueError"), _tb("KeyError")]
    report = compute_metrics(tbs)
    assert report.by_exception["ValueError"] == 2
    assert report.by_exception["KeyError"] == 1


def test_avg_depth():
    f2 = [_frame(), _frame(lineno=20)]
    tbs = [_tb(frames=[_frame()]), _tb(frames=f2)]
    report = compute_metrics(tbs)
    assert report.avg_depth == 1.5


def test_by_module_top_level():
    frames = [_frame(module="django.db.models"), _frame(module="django.http")]
    tbs = [_tb(frames=frames)]
    report = compute_metrics(tbs)
    assert report.by_module.get("django", 0) == 2


def test_top_files_length():
    frames = [_frame(filename=f"app/f{i}.py", module=f"app.f{i}") for i in range(6)]
    tbs = [_tb(frames=frames)]
    report = compute_metrics(tbs)
    assert len(report.top_files) <= 5


def test_render_contains_total():
    tbs = [_tb()]
    report = compute_metrics(tbs)
    rendered = render_metrics(report)
    assert "Total tracebacks" in rendered
    assert "1" in rendered


def test_render_contains_exception_type():
    tbs = [_tb("RuntimeError")]
    report = compute_metrics(tbs)
    rendered = render_metrics(report)
    assert "RuntimeError" in rendered


def test_metrics_cli_json(tmp_path):
    log = tmp_path / "app.log"
    log.write_text(
        "Traceback (most recent call last):\n"
        '  File "app/foo.py", line 5, in run\n'
        "    foo()\n"
        "ValueError: oops\n"
    )
    from stacktrace_filter.metrics_cli import main
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        main([str(log), "--json"])
    data = json.loads(buf.getvalue())
    assert data["total"] >= 1
    assert "ValueError" in data["by_exception"]
