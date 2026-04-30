"""Tests for the CLI entry point."""

import textwrap
from unittest.mock import patch

import pytest

from stacktrace_filter.cli import main

SAMPLE_TRACEBACK = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app/main.py", line 10, in run
        result = compute()
      File "/usr/lib/python3.11/functools.py", line 75, in wrapper
        return func(*args)
      File "app/compute.py", line 42, in compute
        raise ValueError("bad input")
    ValueError: bad input
""")

TRACEBACK_WITH_LOCALS = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app/main.py", line 10, in run
        raise RuntimeError("boom")
        Local variables:
          api_key = ghp_fakeSecret123
          user = user@example.com
    RuntimeError: token=fakeToken
""")


@pytest.fixture()
def log_file(tmp_path):
    f = tmp_path / "app.log"
    f.write_text(SAMPLE_TRACEBACK)
    return str(f)


def test_main_reads_file(log_file, capsys):
    rc = main(["--no-color", log_file])
    assert rc == 0
    out = capsys.readouterr().out
    assert "ValueError" in out


def test_main_missing_file(capsys):
    rc = main(["nonexistent_file_xyz.log"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "error" in err


def test_main_reads_stdin(capsys):
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.read.return_value = SAMPLE_TRACEBACK
        rc = main(["--no-color"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "ValueError" in out


def test_no_collapse_flag(log_file, capsys):
    rc = main(["--no-color", "--no-collapse", log_file])
    assert rc == 0
    out = capsys.readouterr().out
    # stdlib frame should appear when collapse is disabled
    assert "functools" in out


def test_no_traceback_passthrough(tmp_path, capsys):
    plain = tmp_path / "plain.log"
    plain.write_text("everything is fine\n")
    rc = main(["--no-color", str(plain)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "everything is fine" in out


def test_redact_masks_local_variables_and_exception_text(capsys):
    with patch("sys.stdin") as mock_stdin:
        mock_stdin.read.return_value = TRACEBACK_WITH_LOCALS
        rc = main(["--no-color", "--show-locals", "--redact"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "ghp_fakeSecret123" not in out
    assert "fakeToken" not in out
    assert "user@example.com" not in out
    assert "<redacted>" in out
