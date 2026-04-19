"""Tests for stacktrace_filter.scorer."""
from __future__ import annotations

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.annotator import Hint
from stacktrace_filter.scorer import score, rank, ScoredTraceback


def _frame(path: str = "app/main.py", lineno: int = 10, name: str = "run") -> Frame:
    return Frame(
        filename=path,
        lineno=lineno,
        name=name,
        line="pass",
        is_stdlib=path.startswith("/usr/lib"),
        is_site_packages="site-packages" in path,
    )


def _tb(exc_type: str, frames=None) -> Traceback:
    return Traceback(
        frames=frames or [_frame()],
        exc_type=exc_type,
        exc_message="error",
    )


def test_score_returns_scored_traceback():
    result = score(_tb("ValueError"))
    assert isinstance(result, ScoredTraceback)


def test_high_severity_exception():
    result = score(_tb("MemoryError"))
    assert result.severity == "high"
    assert result.score >= 80


def test_medium_severity_exception():
    result = score(_tb("ValueError", frames=[]))
    assert result.severity == "medium"
    assert 40 <= result.score < 80


def test_low_severity_unknown_exception():
    result = score(_tb("CustomWeirdError", frames=[]))
    assert result.severity == "low"


def test_user_frames_increase_score():
    few = score(_tb("RuntimeError", frames=[_frame()]))
    many = score(_tb("RuntimeError", frames=[_frame()] * 5))
    assert many.score > few.score


def test_hints_increase_score():
    no_hints = score(_tb("ValueError"))
    with_hints = score(_tb("ValueError"), hints=[Hint(message="fix this", docs_url=None)])
    assert with_hints.score > no_hints.score


def test_stdlib_frames_do_not_increase_score():
    user = score(_tb("OSError", frames=[_frame("app/x.py")]))
    stdlib = score(_tb("OSError", frames=[_frame("/usr/lib/python3/foo.py")]))
    # stdlib frame should not add user-frame bonus
    assert user.score >= stdlib.score


def test_rank_orders_by_score_descending():
    tbs = [_tb("CustomError", frames=[]), _tb("MemoryError"), _tb("ValueError")]
    ranked = rank(tbs)
    scores = [r.score for r in ranked]
    assert scores == sorted(scores, reverse=True)


def test_rank_empty():
    assert rank([]) == []
