"""Tests for stacktrace_filter.annotator."""

from __future__ import annotations

import pytest

from stacktrace_filter.annotator import annotate
from stacktrace_filter.parser import Traceback, Frame


def _tb(exc_type: str, exc_message: str) -> Traceback:
    frame = Frame(filename="app.py", lineno=1, module="app", context="pass")
    return Traceback(frames=[frame], exc_type=exc_type, exc_message=exc_message)


def test_module_not_found():
    hint = annotate(_tb("ModuleNotFoundError", "No module named 'requests'"))
    assert hint is not None
    assert "requests" in hint
    assert "pip install" in hint


def test_attribute_error():
    hint = annotate(_tb("AttributeError", "'NoneType' object has no attribute 'split'"))
    assert hint is not None
    assert "NoneType" in hint
    assert "split" in hint


def test_key_error():
    hint = annotate(_tb("KeyError", "'user_id'"))
    assert hint is not None
    assert "user_id" in hint


def test_file_not_found():
    hint = annotate(
        _tb("FileNotFoundError", "[Errno 2] No such file or directory: '/tmp/x.txt'")
    )
    assert hint is not None
    assert "/tmp/x.txt" in hint


def test_recursion_error():
    hint = annotate(_tb("RecursionError", "maximum recursion depth exceeded"))
    assert hint is not None
    assert "base case" in hint


def test_no_match_returns_none():
    hint = annotate(_tb("ValueError", "something totally custom"))
    assert hint is None


def test_type_error():
    hint = annotate(_tb("TypeError", "unsupported operand type(s) for +: 'int' and 'str'"))
    assert hint is not None
    assert "int" in hint
