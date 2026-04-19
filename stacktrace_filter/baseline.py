"""Baseline comparison: compare current tracebacks against a saved snapshot."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from stacktrace_filter.parser import Traceback
from stacktrace_filter.snapshot import Snapshot


@dataclass
class BaselineResult:
    new: List[Traceback] = field(default_factory=list)
    resolved: List[Traceback] = field(default_factory=list)
    recurring: List[Traceback] = field(default_factory=list)

    @property
    def has_regressions(self) -> bool:
        return len(self.new) > 0


def _exc_key(tb: Traceback) -> str:
    last = tb.frames[-1] if tb.frames else None
    loc = f"{last.filename}:{last.lineno}" if last else "unknown"
    return f"{tb.exc_type}@{loc}"


def compare(current: List[Traceback], baseline: Snapshot) -> BaselineResult:
    """Compare *current* tracebacks against those stored in *baseline*."""
    baseline_keys = {_exc_key(tb) for tb in baseline.tracebacks}
    current_keys = {_exc_key(tb) for tb in current}

    result = BaselineResult()
    for tb in current:
        if _exc_key(tb) in baseline_keys:
            result.recurring.append(tb)
        else:
            result.new.append(tb)

    for tb in baseline.tracebacks:
        if _exc_key(tb) not in current_keys:
            result.resolved.append(tb)

    return result


def render_baseline_report(result: BaselineResult) -> str:
    lines: List[str] = []
    lines.append(f"Baseline comparison")
    lines.append(f"  New (regressions) : {len(result.new)}")
    lines.append(f"  Recurring         : {len(result.recurring)}")
    lines.append(f"  Resolved          : {len(result.resolved)}")
    if result.new:
        lines.append("\nNew exceptions:")
        for tb in result.new:
            lines.append(f"  - {tb.exc_type}: {tb.exc_message}")
    if result.resolved:
        lines.append("\nResolved exceptions:")
        for tb in result.resolved:
            lines.append(f"  - {tb.exc_type}: {tb.exc_message}")
    return "\n".join(lines)
