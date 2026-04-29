"""Tests for stacktrace_filter.suppressor."""
from __future__ import annotations

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.suppressor import (
    SuppressorConfig,
    SuppressResult,
    suppress,
)


def _frame(module: str = "app.main", lineno: int = 10) -> Frame:
    return Frame(
        filename=f"/app/{module.replace('.', '/')}.py",
        lineno=lineno,
        function="run",
        module=module,
        context="raise ValueError",
    )


def _tb(
    exc_type: str = "ValueError",
    exc_value: str = "bad input",
    frames: int = 2,
) -> Traceback:
    return Traceback(
        frames=[_frame(lineno=i) for i in range(1, frames + 1)],
        exc_type=exc_type,
        exc_value=exc_value,
    )


# ---------------------------------------------------------------------------


def test_no_config_keeps_all():
    tbs = [_tb(), _tb(exc_type="KeyError")]
    result = suppress(tbs)
    assert len(result.kept) == 2
    assert result.suppressed_count == 0


def test_suppress_by_type():
    tbs = [_tb(exc_type="KeyError"), _tb(exc_type="ValueError")]
    cfg = SuppressorConfig(suppress_types={"KeyError"})
    result = suppress(tbs, cfg)
    assert len(result.kept) == 1
    assert result.kept[0].exc_type == "ValueError"
    assert result.suppressed_count == 1


def test_suppress_by_message_substring():
    tbs = [
        _tb(exc_value="connection refused"),
        _tb(exc_value="bad input"),
    ]
    cfg = SuppressorConfig(suppress_messages=["connection"])
    result = suppress(tbs, cfg)
    assert len(result.kept) == 1
    assert "bad input" in result.kept[0].exc_value


def test_suppress_by_message_case_insensitive():
    tbs = [_tb(exc_value="Connection Refused")]
    cfg = SuppressorConfig(suppress_messages=["connection refused"])
    result = suppress(tbs, cfg)
    assert result.suppressed_count == 1


def test_suppress_by_min_frames():
    tbs = [_tb(frames=1), _tb(frames=3)]
    cfg = SuppressorConfig(min_frames=2)
    result = suppress(tbs, cfg)
    assert len(result.kept) == 1
    assert len(result.kept[0].frames) == 3


def test_deduplicate_keeps_first():
    tbs = [_tb(), _tb(), _tb(exc_type="KeyError")]
    cfg = SuppressorConfig(deduplicate=True)
    result = suppress(tbs, cfg)
    assert len(result.kept) == 2  # first ValueError + KeyError
    assert result.suppressed_count == 1


def test_deduplicate_false_keeps_all_duplicates():
    tbs = [_tb(), _tb()]
    cfg = SuppressorConfig(deduplicate=False)
    result = suppress(tbs, cfg)
    assert len(result.kept) == 2


def test_total_property():
    tbs = [_tb(), _tb(exc_type="KeyError"), _tb(exc_type="TypeError")]
    cfg = SuppressorConfig(suppress_types={"KeyError"})
    result = suppress(tbs, cfg)
    assert result.total == 3
