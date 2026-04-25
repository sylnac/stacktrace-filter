"""Format a CorrelationReport for terminal output."""
from __future__ import annotations

from stacktrace_filter.correlator import CorrelationGroup, CorrelationReport


def _bold(text: str) -> str:
    return f"\033[1m{text}\033[0m"


def _cyan(text: str) -> str:
    return f"\033[36m{text}\033[0m"


def _dim(text: str) -> str:
    return f"\033[2m{text}\033[0m"


def _fmt_group(group: CorrelationGroup, index: int) -> str:
    lines: list[str] = []
    header = _bold(f"[{index}] {group.signature}")
    count_label = _cyan(f"  occurrences : {group.count}")
    sources = ", ".join(group.sources) if group.sources else _dim("(no source)")
    source_label = _dim(f"  sources     : {sources}")
    lines.extend([header, count_label, source_label])
    return "\n".join(lines)


def format_correlation(report: CorrelationReport, *, no_color: bool = False) -> str:
    if not report.groups:
        return "No correlated tracebacks found.\n"

    parts: list[str] = []
    title = "=== Correlation Report ==="
    parts.append(_bold(title) if not no_color else title)
    parts.append(f"Total groups : {report.total_groups}")
    cross = len(report.cross_source_groups)
    parts.append(f"Cross-source : {cross}")
    parts.append("")

    for i, group in enumerate(report.groups, start=1):
        parts.append(_fmt_group(group, i) if not no_color else _fmt_group.__wrapped__(group, i)  # type: ignore[attr-defined]
                     if hasattr(_fmt_group, '__wrapped__') else _fmt_group(group, i))

    return "\n".join(parts) + "\n"
