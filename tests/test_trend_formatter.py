"""Tests for trend_formatter."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from stacktrace_filter.trend import TrendPoint, TrendReport
from stacktrace_filter.trend_formatter import _sparkline, format_trend


def _report(by_type: dict[str, list[int]]) -> TrendReport:
    now = datetime.utcnow()
    points = [
        TrendPoint(timestamp=now - timedelta(minutes=i), counts={})
        for i in range(max(len(v) for v in by_type.values()) if by_type else 1)
    ]
    return TrendReport(points=points, by_type=by_type)


def test_sparkline_empty():
    assert _sparkline([]) == ""


def test_sparkline_uniform():
    result = _sparkline([3, 3, 3])
    assert len(result) == 3
    assert len(set(result)) == 1


def test_sparkline_rising():
    result = _sparkline([0, 4, 8])
    assert result[2] >= result[1] >= result[0]


def test_format_trend_contains_header():
    report = _report({"ValueError": [1, 2, 3]})
    output = format_trend(report, color=False)
    assert "Exception Trend Report" in output


def test_format_trend_shows_exception_type():
    report = _report({"TypeError": [1, 2, 3]})
    output = format_trend(report, color=False)
    assert "TypeError" in output


def test_format_trend_no_rising_message():
    report = _report({})
    output = format_trend(report, color=False)
    assert "No rising exception types detected" in output


def test_format_trend_rising_shown():
    report = _report({"RuntimeError": [1, 2, 10]})
    output = format_trend(report, color=False)
    assert "RuntimeError" in output


def test_format_trend_totals_line():
    report = _report({"KeyError": [2, 3]})
    output = format_trend(report, color=False)
    assert "Total errors" in output


def test_format_trend_color_off_no_escape():
    report = _report({"ValueError": [1, 2, 3]})
    output = format_trend(report, color=False)
    assert "\033[" not in output


def test_format_trend_color_on_has_escape():
    report = _report({"ValueError": [1, 2, 10]})
    output = format_trend(report, color=True)
    assert "\033[" in output
