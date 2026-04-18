"""Tests for stacktrace_filter.deduplicator."""
from __future__ import annotations

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.deduplicator import (
    DeduplicatedGroup,
    DeduplicationResult,
    deduplicate,
    _frame_sig,
)


def _make_tb(exc_type: str = "ValueError", lineno: int = 10) -> Traceback:
    frames = [
        Frame(filename="app/main.py", lineno=lineno, name="run", line="run()"),
        Frame(filename="app/utils.py", lineno=42, name="helper", line="helper()"),
    ]
    return Traceback(frames=frames, exc_type=exc_type, exc_message="oops")


def test_frame_sig_same_structure():
    tb1 = _make_tb()
    tb2 = _make_tb()
    assert _frame_sig(tb1) == _frame_sig(tb2)


def test_frame_sig_different_lineno():
    tb1 = _make_tb(lineno=10)
    tb2 = _make_tb(lineno=99)
    assert _frame_sig(tb1) != _frame_sig(tb2)


def test_frame_sig_different_exc_type():
    tb1 = _make_tb(exc_type="ValueError")
    tb2 = _make_tb(exc_type="KeyError")
    assert _frame_sig(tb1) != _frame_sig(tb2)


def test_deduplicate_empty():
    result = deduplicate([])
    assert result.total == 0
    assert result.unique == 0
    assert result.duplicate_count == 0


def test_deduplicate_no_duplicates():
    tbs = [_make_tb(lineno=i) for i in range(5)]
    result = deduplicate(tbs)
    assert result.unique == 5
    assert result.total == 5
    assert result.duplicate_count == 0


def test_deduplicate_all_same():
    tbs = [_make_tb() for _ in range(4)]
    result = deduplicate(tbs)
    assert result.unique == 1
    assert result.total == 4
    assert result.duplicate_count == 3


def test_deduplicate_mixed():
    tbs = [_make_tb(lineno=1), _make_tb(lineno=1), _make_tb(lineno=2)]
    result = deduplicate(tbs)
    assert result.unique == 2
    assert result.total == 3
    counts = sorted(g.count for g in result.groups)
    assert counts == [1, 2]


def test_deduplicated_group_fingerprint_set():
    tb = _make_tb()
    group = DeduplicatedGroup(representative=tb)
    assert group.fingerprint == _frame_sig(tb)


def test_representative_is_first_occurrence():
    tb1 = _make_tb()
    tb2 = _make_tb()
    result = deduplicate([tb1, tb2])
    assert result.groups[0].representative is tb1
