"""Tests for stacktrace_filter.archiver."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from stacktrace_filter.archiver import ArchiverConfig, archive, load_archive
from stacktrace_filter.parser import Frame, Traceback


def _make_tb(exc_type: str = "ValueError") -> Traceback:
    frame = Frame(
        filename="app/main.py",
        lineno=10,
        function="run",
        context="raise ValueError('oops')",
    )
    return Traceback(frames=[frame], exc_type=exc_type, exc_value="oops")


def test_archive_creates_file(tmp_path):
    cfg = ArchiverConfig(directory=tmp_path / "arc")
    dest = archive([_make_tb()], cfg)
    assert dest.exists()


def test_archive_writes_jsonl(tmp_path):
    cfg = ArchiverConfig(directory=tmp_path / "arc")
    archive([_make_tb(), _make_tb("KeyError")], cfg)
    files = list((tmp_path / "arc").glob("archive-*.jsonl"))
    assert len(files) == 1
    lines = files[0].read_text().strip().splitlines()
    assert len(lines) == 2
    record = json.loads(lines[0])
    assert "ts" in record
    assert record["traceback"]["exc_type"] == "ValueError"


def test_archive_appends_to_existing(tmp_path):
    cfg = ArchiverConfig(directory=tmp_path / "arc")
    archive([_make_tb()], cfg)
    archive([_make_tb("KeyError")], cfg)
    files = list((tmp_path / "arc").glob("archive-*.jsonl"))
    assert len(files) == 1
    lines = files[0].read_text().strip().splitlines()
    assert len(lines) == 2


def test_archive_rotates_when_size_exceeded(tmp_path):
    cfg = ArchiverConfig(directory=tmp_path / "arc", max_bytes=1)  # force rotation
    dest1 = archive([_make_tb()], cfg)
    time.sleep(0.01)
    dest2 = archive([_make_tb("KeyError")], cfg)
    assert dest1 != dest2


def test_archive_prunes_old_files(tmp_path):
    arc_dir = tmp_path / "arc"
    arc_dir.mkdir()
    # pre-create max_files old archives
    for i in range(5):
        (arc_dir / f"archive-{i:013d}.jsonl").write_text("{}", encoding="utf-8")
    cfg = ArchiverConfig(directory=arc_dir, max_files=5, max_bytes=1)
    archive([_make_tb()], cfg)
    remaining = list(arc_dir.glob("archive-*.jsonl"))
    assert len(remaining) <= 5


def test_load_archive_roundtrip(tmp_path):
    cfg = ArchiverConfig(directory=tmp_path / "arc")
    dest = archive([_make_tb("RuntimeError")], cfg)
    records = load_archive(dest)
    assert len(records) == 1
    assert records[0]["traceback"]["exc_type"] == "RuntimeError"


def test_archive_empty_list(tmp_path):
    cfg = ArchiverConfig(directory=tmp_path / "arc")
    dest = archive([], cfg)
    assert dest.exists()
    assert dest.read_text() == ""
