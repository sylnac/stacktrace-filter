"""Archive tracebacks to a rotating set of JSONL files for long-term storage."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from stacktrace_filter.exporter import _tb_to_dict
from stacktrace_filter.parser import Traceback


@dataclass
class ArchiverConfig:
    directory: Path
    max_files: int = 5
    max_bytes: int = 5 * 1024 * 1024  # 5 MB per file
    label: str = "archive"


def _current_file(cfg: ArchiverConfig) -> Path:
    cfg.directory.mkdir(parents=True, exist_ok=True)
    files = sorted(cfg.directory.glob(f"{cfg.label}-*.jsonl"))
    if not files:
        return _new_file(cfg)
    latest = files[-1]
    if latest.stat().st_size >= cfg.max_bytes:
        _rotate(cfg, files)
        return _new_file(cfg)
    return latest


def _new_file(cfg: ArchiverConfig) -> Path:
    ts = int(time.time() * 1000)
    return cfg.directory / f"{cfg.label}-{ts}.jsonl"


def _rotate(cfg: ArchiverConfig, files: list) -> None:
    while len(files) >= cfg.max_files:
        oldest = files.pop(0)
        oldest.unlink(missing_ok=True)


def archive(tracebacks: List[Traceback], cfg: ArchiverConfig) -> Path:
    """Append tracebacks to the current archive file; return the file path."""
    target = _current_file(cfg)
    with target.open("a", encoding="utf-8") as fh:
        for tb in tracebacks:
            record = {"ts": time.time(), "traceback": _tb_to_dict(tb)}
            fh.write(json.dumps(record) + "\n")
    return target


def load_archive(path: Path) -> List[dict]:
    """Load all records from a JSONL archive file."""
    records: List[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records
