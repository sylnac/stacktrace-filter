"""Render a short summary table of a TracebackGroup."""
from __future__ import annotations

from collections import Counter
from typing import List

from stacktrace_filter.grouper import TracebackGroup
from stacktrace_filter.formatter import _bold, _red, _dim


def _bar(count: int, total: int, width: int = 20) -> str:
    filled = round(width * count / total) if total else 0
    return "█" * filled + _dim("░" * (width - filled))


def render_summary(group: TracebackGroup, *, color: bool = True) -> str:
    """Return a human-readable summary string for *group*."""
    if group.count == 0:
        return "No tracebacks found.\n"

    lines: List[str] = []
    header = f"{'─' * 50}"
    title = "Traceback Summary"
    lines.append(header)
    lines.append((_bold(title) if color else title))
    lines.append(f"Total tracebacks : {group.count}")

    counter: Counter = Counter(group.exception_types)
    if counter:
        lines.append("")
        lines.append("Exception breakdown:")
        for exc_type, cnt in counter.most_common():
            label = (_red(exc_type) if color else exc_type)
            bar = _bar(cnt, group.count)
            lines.append(f"  {label:<40s} {bar}  {cnt}")

    lines.append(header)
    return "\n".join(lines) + "\n"
