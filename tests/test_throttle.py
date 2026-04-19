"""Tests for stacktrace_filter.throttle."""
from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.throttle import ThrottleConfig, ThrottleState


def _frame(filename="app.py", lineno=10):
    return Frame(filename=filename, lineno=lineno, function="fn", context="pass")


def _tb(exc_type="ValueError", filename="app.py", lineno=10):
    return Traceback(
        frames=[_frame(filename, lineno)],
        exc_type=exc_type,
        exc_value="oops",
    )


def test_first_emit_allowed():
    state = ThrottleState(ThrottleConfig(max_per_window=2))
    assert state.should_emit(_tb()) is True


def test_within_limit_allowed():
    state = ThrottleState(ThrottleConfig(max_per_window=3))
    tb = _tb()
    assert state.should_emit(tb) is True
    assert state.should_emit(tb) is True
    assert state.should_emit(tb) is True


def test_beyond_limit_suppressed():
    state = ThrottleState(ThrottleConfig(max_per_window=2))
    tb = _tb()
    state.should_emit(tb)
    state.should_emit(tb)
    assert state.should_emit(tb) is False


def test_different_exc_types_independent():
    state = ThrottleState(ThrottleConfig(max_per_window=1))
    assert state.should_emit(_tb("ValueError")) is True
    assert state.should_emit(_tb("KeyError")) is True


def test_window_expiry_resets_bucket():
    state = ThrottleState(ThrottleConfig(window_seconds=1.0, max_per_window=1))
    tb = _tb()
    state.should_emit(tb)  # fills bucket
    assert state.should_emit(tb) is False
    with patch("stacktrace_filter.throttle.time.monotonic", return_value=time.monotonic() + 2.0):
        assert state.should_emit(tb) is True


def test_apply_filters_list():
    state = ThrottleState(ThrottleConfig(max_per_window=1))
    tb = _tb()
    result = state.apply([tb, tb, tb])
    assert len(result) == 1


def test_apply_empty():
    state = ThrottleState()
    assert state.apply([]) == []
