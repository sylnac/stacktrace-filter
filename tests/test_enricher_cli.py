"""Tests for stacktrace_filter.enricher_cli."""
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from stacktrace_filter.enricher_cli import build_enricher_parser, main


TRACEBACK = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app/main.py", line 10, in run
        result = helper()
    ValueError: bad value
""")


@pytest.fixture
def log_file(tmp_path):
    f = tmp_path / "app.log"
    f.write_text(TRACEBACK)
    return f


def test_build_parser_defaults():
    p = build_enricher_parser()
    args = p.parse_args([])
    assert args.no_blame is False
    assert args.output is None


def test_main_missing_file_exits():
    rc = main(["nonexistent_file.log"])
    assert rc == 1


def test_main_reads_file(log_file):
    with patch("stacktrace_filter.enricher._git_blame", return_value=None):
        rc = main([str(log_file)])
    assert rc == 0


def test_main_no_blame_flag(log_file):
    with patch("stacktrace_filter.enricher._git_blame") as mock_blame:
        rc = main(["--no-blame", str(log_file)])
    mock_blame.assert_not_called()
    assert rc == 0


def test_main_writes_output_file(log_file, tmp_path):
    out = tmp_path / "out.txt"
    with patch("stacktrace_filter.enricher._git_blame", return_value=None):
        rc = main([str(log_file), "-o", str(out)])
    assert rc == 0
    assert out.exists()
    assert "ValueError" in out.read_text()


def test_main_no_tracebacks(tmp_path):
    f = tmp_path / "empty.log"
    f.write_text("nothing here\n")
    rc = main([str(f)])
    assert rc == 0
