"""Tests for stacktrace_filter.classifier."""
import pytest
from stacktrace_filter.classifier import (
    Severity,
    classify,
    classify_all,
    ClassifiedTraceback,
)
from stacktrace_filter.parser import Frame, Traceback


def _frame(module="app.main", lineno=10):
    return Frame(
        filename="app/main.py",
        lineno=lineno,
        function="run",
        module=module,
        context="x = 1",
    )


def _tb(exc_type="ValueError", exc_value="bad value"):
    return Traceback(
        frames=[_frame()],
        exc_type=exc_type,
        exc_value=exc_value,
    )


def test_classify_returns_classified_traceback():
    result = classify(_tb())
    assert isinstance(result, ClassifiedTraceback)
    assert result.traceback is not None


def test_error_suffix_gives_error_severity():
    result = classify(_tb(exc_type="ValueError"))
    assert result.severity == Severity.ERROR


def test_exception_suffix_gives_error_severity():
    result = classify(_tb(exc_type="RuntimeException"))
    assert result.severity == Severity.ERROR


def test_critical_type_gives_critical_severity():
    result = classify(_tb(exc_type="MemoryError"))
    assert result.severity == Severity.CRITICAL


def test_warning_type_gives_warning_severity():
    result = classify(_tb(exc_type="DeprecationWarning"))
    assert result.severity == Severity.WARNING


def test_warning_suffix_gives_warning_severity():
    result = classify(_tb(exc_type="MyCustomWarning"))
    assert result.severity == Severity.WARNING


def test_unknown_type_gives_info_severity():
    result = classify(_tb(exc_type="Timeout"))
    assert result.severity == Severity.INFO


def test_classify_has_reasons():
    result = classify(_tb(exc_type="OSError"))
    assert len(result.reasons) > 0


def test_classify_all_sorted_critical_first():
    tbs = [
        _tb(exc_type="UserWarning"),
        _tb(exc_type="MemoryError"),
        _tb(exc_type="ValueError"),
    ]
    results = classify_all(tbs)
    severities = [r.severity for r in results]
    assert severities[0] == Severity.CRITICAL
    assert severities[-1] == Severity.WARNING


def test_classify_all_empty():
    assert classify_all([]) == []
