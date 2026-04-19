"""Tests for stacktrace_filter.pattern_filter."""
import pytest
from unittest.mock import MagicMock

from stacktrace_filter.pattern_filter import PatternFilterConfig, apply_filter


def _tb(exc_type: str, exc_message: str):
    tb = MagicMock()
    tb.exc_type = exc_type
    tb.exc_message = exc_message
    return tb


@pytest.fixture()
def tracebacks():
    return [
        _tb("ValueError", "invalid literal for int"),
        _tb("KeyError", "'missing_key'"),
        _tb("AttributeError", "'NoneType' object has no attribute 'foo'"),
        _tb("ValueError", "too many values to unpack"),
    ]


def test_no_config_returns_all(tracebacks):
    assert apply_filter(tracebacks) == tracebacks


def test_include_type_filters(tracebacks):
    cfg = PatternFilterConfig(include_types=["ValueError"])
    result = apply_filter(tracebacks, cfg)
    assert len(result) == 2
    assert all(tb.exc_type == "ValueError" for tb in result)


def test_exclude_type_filters(tracebacks):
    cfg = PatternFilterConfig(exclude_types=["ValueError"])
    result = apply_filter(tracebacks, cfg)
    assert all(tb.exc_type != "ValueError" for tb in result)
    assert len(result) == 2


def test_include_message_filters(tracebacks):
    cfg = PatternFilterConfig(include_messages=["NoneType"])
    result = apply_filter(tracebacks, cfg)
    assert len(result) == 1
    assert "NoneType" in result[0].exc_message


def test_exclude_message_filters(tracebacks):
    cfg = PatternFilterConfig(exclude_messages=["missing_key"])
    result = apply_filter(tracebacks, cfg)
    assert all("missing_key" not in tb.exc_message for tb in result)


def test_combined_include_type_and_message(tracebacks):
    cfg = PatternFilterConfig(
        include_types=["ValueError"],
        include_messages=["too many"],
    )
    result = apply_filter(tracebacks, cfg)
    assert len(result) == 1
    assert "too many" in result[0].exc_message


def test_empty_tracebacks():
    cfg = PatternFilterConfig(include_types=["ValueError"])
    assert apply_filter([], cfg) == []


def test_regex_pattern(tracebacks):
    cfg = PatternFilterConfig(include_types=["Value|Key"])
    result = apply_filter(tracebacks, cfg)
    assert len(result) == 3
