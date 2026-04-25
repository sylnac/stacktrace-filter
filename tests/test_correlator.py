"""Tests for stacktrace_filter.correlator."""
from __future__ import annotations

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.correlator import (
    CorrelationGroup,
    CorrelationReport,
    _frame_signature,
    correlate,
    top_correlated,
)


def _frame(filename: str = "app.py", lineno: int = 10, name: str = "fn") -> Frame:
    return Frame(filename=filename, lineno=lineno, name=name, context="pass")


def _tb(
    exc_type: str = "ValueError",
    frames: list[Frame] | None = None,
    source: str = "",
) -> Traceback:
    f = frames or [_frame()]
    tb = Traceback(frames=f, exc_type=exc_type, exc_value="oops")
    tb.source = source  # type: ignore[attr-defined]
    return tb


# ---------------------------------------------------------------------------
# _frame_signature
# ---------------------------------------------------------------------------

def test_frame_signature_includes_exc_type():
    tb = _tb(exc_type="KeyError")
    sig = _frame_signature(tb)
    assert "KeyError" in sig


def test_frame_signature_includes_location():
    tb = _tb(frames=[_frame(filename="mod.py", lineno=42)])
    sig = _frame_signature(tb)
    assert "mod.py:42" in sig


def test_frame_signature_no_frames():
    tb = Traceback(frames=[], exc_type="RuntimeError", exc_value="")
    tb.source = ""  # type: ignore[attr-defined]
    sig = _frame_signature(tb)
    assert "RuntimeError" in sig
    assert "unknown" in sig


# ---------------------------------------------------------------------------
# correlate
# ---------------------------------------------------------------------------

def test_correlate_empty():
    report = correlate([])
    assert report.total_groups == 0
    assert report.groups == []


def test_correlate_single_traceback():
    report = correlate([_tb()])
    assert report.total_groups == 1
    assert report.groups[0].count == 1


def test_correlate_groups_identical_signatures():
    tb1 = _tb(exc_type="ValueError", frames=[_frame("a.py", 1)])
    tb2 = _tb(exc_type="ValueError", frames=[_frame("a.py", 1)])
    report = correlate([tb1, tb2])
    assert report.total_groups == 1
    assert report.groups[0].count == 2


def test_correlate_separates_different_signatures():
    tb1 = _tb(exc_type="ValueError", frames=[_frame("a.py", 1)])
    tb2 = _tb(exc_type="TypeError", frames=[_frame("b.py", 2)])
    report = correlate([tb1, tb2])
    assert report.total_groups == 2


def test_correlate_sorted_by_count_descending():
    single = _tb(exc_type="TypeError", frames=[_frame("b.py", 99)])
    repeated = _tb(exc_type="ValueError", frames=[_frame("a.py", 1)])
    report = correlate([single, repeated, repeated])
    assert report.groups[0].count >= report.groups[1].count


# ---------------------------------------------------------------------------
# cross_source_groups
# ---------------------------------------------------------------------------

def test_cross_source_groups_detected():
    tb1 = _tb(exc_type="ValueError", frames=[_frame("a.py", 1)], source="svc-a")
    tb2 = _tb(exc_type="ValueError", frames=[_frame("a.py", 1)], source="svc-b")
    report = correlate([tb1, tb2])
    assert len(report.cross_source_groups) == 1


def test_single_source_not_cross_source():
    tb1 = _tb(source="svc-a")
    tb2 = _tb(source="svc-a")
    report = correlate([tb1, tb2])
    assert len(report.cross_source_groups) == 0


# ---------------------------------------------------------------------------
# top_correlated
# ---------------------------------------------------------------------------

def test_top_correlated_limits_results():
    tbs = [
        _tb(exc_type=f"Error{i}", frames=[_frame("f.py", i)])
        for i in range(10)
    ]
    report = correlate(tbs)
    top = top_correlated(report, n=3)
    assert len(top) == 3
