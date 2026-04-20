"""Tests for stacktrace_filter.profiler."""
from __future__ import annotations

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.profiler import (
    HotFrame,
    ProfileReport,
    profile,
    render_profile_report,
)


def _frame(file: str = "app.py", function: str = "run", lineno: int = 10) -> Frame:
    return Frame(file=file, lineno=lineno, function=function, context="pass")


def _tb(*frames: Frame, exc_type: str = "ValueError", exc_value: str = "oops") -> Traceback:
    return Traceback(frames=list(frames), exc_type=exc_type, exc_value=exc_value)


def test_profile_empty_input():
    report = profile([])
    assert report.total_tracebacks == 0
    assert report.total_frames == 0
    assert report.hotspots == []


def test_profile_single_traceback():
    tb = _tb(_frame("app.py", "main"), _frame("db.py", "query"))
    report = profile([tb])
    assert report.total_tracebacks == 1
    assert report.total_frames == 2


def test_profile_counts_repeated_frames():
    f = _frame("app.py", "run")
    tb1 = _tb(f)
    tb2 = _tb(f)
    report = profile([tb1, tb2])
    assert report.hotspots[0].hits == 2
    assert report.hotspots[0].file == "app.py"
    assert report.hotspots[0].function == "run"


def test_profile_top_n_limits_results():
    frames = [_frame(f"mod{i}.py", f"fn{i}") for i in range(20)]
    tb = _tb(*frames)
    report = profile([tb], top_n=5)
    assert len(report.hotspots) == 5


def test_profile_hotspots_sorted_by_hits():
    common = _frame("hot.py", "bottleneck")
    rare = _frame("cold.py", "rarely_called")
    tbs = [_tb(common) for _ in range(5)] + [_tb(rare)]
    report = profile(tbs)
    assert report.hotspots[0].hits >= report.hotspots[-1].hits


def test_profile_report_top_helper():
    report = ProfileReport(
        total_tracebacks=3,
        total_frames=6,
        hotspots=[HotFrame("a.py", "f", i) for i in range(10, 0, -1)],
    )
    assert len(report.top(3)) == 3
    assert report.top(3)[0].hits == 10


def test_render_contains_header():
    report = profile([])
    text = render_profile_report(report, use_color=False)
    assert "Frame Hotspot Profile" in text


def test_render_shows_tracebacks_count():
    tb = _tb(_frame())
    report = profile([tb])
    text = render_profile_report(report, use_color=False)
    assert "1" in text


def test_render_shows_hotspot_function():
    tb = _tb(_frame("app.py", "my_func"))
    report = profile([tb])
    text = render_profile_report(report, use_color=False)
    assert "my_func" in text
    assert "app.py" in text


def test_render_no_frames_message():
    report = ProfileReport(total_tracebacks=0, total_frames=0, hotspots=[])
    text = render_profile_report(report, use_color=False)
    assert "no frames" in text
