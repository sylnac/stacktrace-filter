"""Tests for stacktrace_filter.parser."""

import textwrap

import pytest

from stacktrace_filter.parser import Frame, Traceback, parse

SIMPLE_TB = textwrap.dedent("""\
    Traceback (most recent call last):
      File "/home/user/project/app.py", line 42, in main
        result = compute(x)
      File "/home/user/project/utils.py", line 17, in compute
        return 1 / value
    ZeroDivisionError: division by zero
""")

STDLIB_TB = textwrap.dedent("""\
    Traceback (most recent call last):
      File "/home/user/project/app.py", line 10, in run
        json.loads(data)
      File "/usr/lib/python3.11/json/__init__.py", line 346, in loads
        return _default_decoder.decode(s)
    json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
""")


def test_parse_returns_one_traceback():
    result = parse(SIMPLE_TB)
    assert len(result) == 1


def test_parse_frame_count():
    tb = parse(SIMPLE_TB)[0]
    assert len(tb.frames) == 2


def test_parse_frame_attributes():
    frame = parse(SIMPLE_TB)[0].frames[0]
    assert frame.path == "/home/user/project/app.py"
    assert frame.lineno == 42
    assert frame.func == "main"
    assert frame.code == "result = compute(x)"


def test_parse_exception_info():
    tb = parse(SIMPLE_TB)[0]
    assert tb.exc_type == "ZeroDivisionError"
    assert tb.exc_msg == "division by zero"


def test_origin_is_last_frame():
    tb = parse(SIMPLE_TB)[0]
    assert tb.origin is not None
    assert tb.origin.func == "compute"


def test_stdlib_detection():
    tb = parse(STDLIB_TB)[0]
    stdlib_frame = tb.frames[1]
    assert stdlib_frame.is_stdlib is True
    assert tb.frames[0].is_stdlib is False


def test_site_packages_detection():
    text = textwrap.dedent("""\
        Traceback (most recent call last):
          File "/usr/local/lib/python3.11/site-packages/requests/api.py", line 73, in get
            return request('get', url, params=params, **kwargs)
        RuntimeError: connection failed
    """)
    tb = parse(text)[0]
    assert tb.frames[0].is_site_packages is True


def test_multiple_tracebacks():
    combined = SIMPLE_TB + "\n" + STDLIB_TB
    result = parse(combined)
    assert len(result) == 2


def test_empty_input():
    assert parse("") == []
