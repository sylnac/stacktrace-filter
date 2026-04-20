"""Tests for stacktrace_filter.classifier_cli."""
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from stacktrace_filter.classifier_cli import build_classifier_parser, main


TRACEBACK_TEXT = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app/main.py", line 10, in run
        result = compute()
    ValueError: invalid input
""")


@pytest.fixture()
def log_file(tmp_path):
    p = tmp_path / "app.log"
    p.write_text(TRACEBACK_TEXT)
    return p


def test_build_parser_defaults():
    p = build_classifier_parser()
    args = p.parse_args([])
    assert args.min_severity == "info"
    assert args.no_collapse is False
    assert args.show_reasons is False


def test_main_missing_file_exits():
    with pytest.raises(SystemExit):
        main(["nonexistent_file.log"])


def test_main_reads_file(log_file, capsys):
    main([str(log_file)])
    out = capsys.readouterr().out
    assert "ValueError" in out


def test_main_severity_badge_present(log_file, capsys):
    main([str(log_file)])
    out = capsys.readouterr().out
    assert "ERROR" in out


def test_main_show_reasons(log_file, capsys):
    main([str(log_file), "--show-reasons"])
    out = capsys.readouterr().out
    assert "Reasons" in out or "reason" in out.lower() or "ValueError" in out


def test_main_min_severity_filters(log_file, capsys):
    # ValueError is ERROR severity; filtering to critical should hide it
    main([str(log_file), "--min-severity", "critical"])
    out = capsys.readouterr().out
    assert "ValueError" not in out or "No tracebacks" in out


def test_main_output_to_file(log_file, tmp_path):
    out_file = tmp_path / "out.txt"
    main([str(log_file), "-o", str(out_file)])
    assert out_file.exists()
    assert "ValueError" in out_file.read_text()
