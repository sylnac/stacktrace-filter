"""Utilities for querying and summarising archived tracebacks."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from stacktrace_filter.archiver import load_archive


@dataclass
class ArchiveSummary:
    total: int
    by_exception: dict[str, int]
    files_scanned: int


def scan_directory(directory: Path, label: str = "archive") -> List[dict]:
    """Load all records from every archive file in *directory*."""
    records: List[dict] = []
    for path in sorted(directory.glob(f"{label}-*.jsonl")):
        records.extend(load_archive(path))
    return records


def summarise(records: List[dict]) -> ArchiveSummary:
    """Return aggregate statistics over a list of archive records."""
    counter: Counter[str] = Counter()
    for r in records:
        exc_type = r.get("traceback", {}).get("exc_type", "Unknown")
        counter[exc_type] += 1
    return ArchiveSummary(
        total=len(records),
        by_exception=dict(counter.most_common()),
        files_scanned=0,  # caller may fill this
    )


def render_archive_summary(summary: ArchiveSummary) -> str:
    lines = [
        f"Archive summary  ({summary.total} total)",
        "-" * 36,
    ]
    for exc, count in summary.by_exception.items():
        bar = "#" * min(count, 20)
        lines.append(f"  {exc:<30} {bar} {count}")
    if not summary.by_exception:
        lines.append("  (no records)")
    return "\n".join(lines)
