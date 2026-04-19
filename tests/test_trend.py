"""Tests for stacktrace_filter.trend."""
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from stacktrace_filter.trend import build_trend, render_trend, TrendReport


def _tb(exc_type: str):
    tb = MagicMock()
    tb.exception_type = exc_type
    return tb


NOW = datetime(2024, 1, 1, 12, 0, 0)
WINDOW = timedelta(hours=1)


def test_build_trend_counts_exceptions():
    tbs = [_tb("ValueError"), _tb("ValueError"), _tb("KeyError")]
    ts = [NOW, NOW, NOW]
    report = build_trend(tbs, ts, window=WINDOW)
    totals = report.totals()
    assert totals["ValueError"] == 2
    assert totals["KeyError"] == 1


def test_build_trend_excludes_old_entries():
    old = NOW - timedelta(hours=2)
    tbs = [_tb("ValueError"), _tb("KeyError")]
    ts = [old, NOW]
    report = build_trend(tbs, ts, window=WINDOW)
    totals = report.totals()
    assert "ValueError" not in totals
    assert totals["KeyError"] == 1


def test_build_trend_empty():
    report = build_trend([], [], window=WINDOW)
    assert report.totals() == {}


def test_build_trend_mismatched_lengths():
    with pytest.raises(ValueError):
        build_trend([_tb("E")], [], window=WINDOW)


def test_rising_returns_frequent_exceptions():
    tbs = [_tb("ValueError")] * 3 + [_tb("KeyError")]
    ts = [NOW] * 4
    report = build_trend(tbs, ts, window=WINDOW)
    rising = report.rising(threshold=2)
    assert "ValueError" in rising
    assert "KeyError" not in rising


def test_render_trend_contains_exception():
    tbs = [_tb("RuntimeError"), _tb("RuntimeError")]
    ts = [NOW, NOW]
    report = build_trend(tbs, ts, window=WINDOW)
    out = render_trend(report)
    assert "RuntimeError" in out
    assert "(2)" in out


def test_render_trend_empty():
    report = TrendReport(window=WINDOW)
    out = render_trend(report)
    assert "no data" in out
