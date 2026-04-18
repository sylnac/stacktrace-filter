"""Tests for stacktrace_filter.writer."""
import io
import pytest
from pathlib import Path

from stacktrace_filter.writer import write_output, _write_stream


def test_write_stream_adds_newline():
    buf = io.StringIO()
    _write_stream("hello", buf)
    assert buf.getvalue() == "hello\n"


def test_write_stream_no_double_newline():
    buf = io.StringIO()
    _write_stream("hello\n", buf)
    assert buf.getvalue() == "hello\n"


def test_write_output_stdout(capsys):
    write_output("some output")
    captured = capsys.readouterr()
    assert "some output" in captured.out


def test_write_output_to_file(tmp_path):
    out_file = tmp_path / "result.txt"
    write_output("traceback info", str(out_file))
    assert out_file.read_text() == "traceback info"


def test_write_output_creates_parent_dirs(tmp_path):
    out_file = tmp_path / "nested" / "dir" / "out.txt"
    write_output("data", str(out_file))
    assert out_file.exists()
    assert out_file.read_text() == "data"
