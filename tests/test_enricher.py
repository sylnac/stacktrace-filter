"""Tests for stacktrace_filter.enricher."""
from unittest.mock import patch

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.enricher import (
    BlameInfo, EnrichedFrame, EnrichedTraceback,
    _git_blame, enrich, format_enriched,
)


def _frame(filename="app/main.py", lineno=42, name="run", context="x = 1"):
    return Frame(filename=filename, lineno=lineno, name=name, context=context)


def _tb():
    return Traceback(
        frames=[_frame(), _frame(filename="app/utils.py", lineno=10, name="helper")],
        exc_type="ValueError",
        exc_value="bad value",
    )


def test_enrich_returns_enriched_traceback():
    tb = _tb()
    with patch("stacktrace_filter.enricher._git_blame", return_value=None):
        et = enrich(tb)
    assert isinstance(et, EnrichedTraceback)
    assert et.tb is tb


def test_enrich_frame_count_matches():
    tb = _tb()
    with patch("stacktrace_filter.enricher._git_blame", return_value=None):
        et = enrich(tb)
    assert len(et.frames) == len(tb.frames)


def test_enrich_attaches_blame():
    blame = BlameInfo(commit="abc12345", author="Alice", summary="fix bug")
    tb = _tb()
    with patch("stacktrace_filter.enricher._git_blame", return_value=blame):
        et = enrich(tb)
    assert et.frames[0].blame == blame


def test_enrich_no_blame_when_disabled():
    tb = _tb()
    et = enrich(tb, use_git_blame=False)
    assert all(ef.blame is None for ef in et.frames)


def test_git_blame_returns_none_on_failure():
    with patch("subprocess.run", side_effect=FileNotFoundError):
        result = _git_blame("app/main.py", 42)
    assert result is None


def test_git_blame_returns_none_on_nonzero():
    import subprocess
    mock = patch("subprocess.run")
    with mock as m:
        m.return_value.returncode = 1
        m.return_value.stdout = ""
        result = _git_blame("app/main.py", 42)
    assert result is None


def test_format_enriched_contains_exception():
    tb = _tb()
    with patch("stacktrace_filter.enricher._git_blame", return_value=None):
        et = enrich(tb)
    out = format_enriched(et)
    assert "ValueError" in out
    assert "bad value" in out


def test_format_enriched_contains_blame():
    blame = BlameInfo(commit="deadbeef", author="Bob", summary="refactor")
    tb = _tb()
    with patch("stacktrace_filter.enricher._git_blame", return_value=blame):
        et = enrich(tb)
    out = format_enriched(et)
    assert "deadbeef" in out
    assert "Bob" in out


def test_format_enriched_no_blame_no_bracket():
    tb = _tb()
    et = enrich(tb, use_git_blame=False)
    out = format_enriched(et)
    assert "[" not in out
