"""Aggregate metrics from a list of tracebacks."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import Counter
from typing import List, Dict
from stacktrace_filter.parser import Traceback


@dataclass
class MetricsReport:
    total: int
    by_exception: Dict[str, int]
    by_module: Dict[str, int]
    top_files: List[tuple]
    avg_depth: float


def compute_metrics(tracebacks: List[Traceback]) -> MetricsReport:
    if not tracebacks:
        return MetricsReport(
            total=0, by_exception={}, by_module={}, top_files=[], avg_depth=0.0
        )

    exc_counter: Counter = Counter()
    module_counter: Counter = Counter()
    file_counter: Counter = Counter()
    depth_total = 0

    for tb in tracebacks:
        exc_counter[tb.exc_type] += 1
        depth_total += len(tb.frames)
        for frame in tb.frames:
            parts = frame.module.split(".")
            module_counter[parts[0]] += 1
            file_counter[frame.filename] += 1

    return MetricsReport(
        total=len(tracebacks),
        by_exception=dict(exc_counter.most_common()),
        by_module=dict(module_counter.most_common()),
        top_files=file_counter.most_common(5),
        avg_depth=depth_total / len(tracebacks),
    )


def render_metrics(report: MetricsReport) -> str:
    lines = [
        f"Total tracebacks : {report.total}",
        f"Average depth    : {report.avg_depth:.1f}",
        "",
        "Exception types:",
    ]
    for exc, count in report.by_exception.items():
        lines.append(f"  {exc:<40} {count}")
    lines.append("")
    lines.append("Top modules:")
    for mod, count in list(report.by_module.items())[:5]:
        lines.append(f"  {mod:<40} {count}")
    lines.append("")
    lines.append("Top files:")
    for fname, count in report.top_files:
        lines.append(f"  {fname:<60} {count}")
    return "\n".join(lines)
