"""Correlate tracebacks across multiple log sources by shared frame signatures."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

from stacktrace_filter.parser import Traceback


@dataclass
class CorrelationGroup:
    """A set of tracebacks that share a common root frame signature."""
    signature: str
    tracebacks: List[Traceback] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.tracebacks)

    @property
    def sources(self) -> List[str]:
        """Distinct source labels attached to each traceback."""
        return list({tb.source for tb in self.tracebacks if tb.source})


@dataclass
class CorrelationReport:
    groups: List[CorrelationGroup]

    @property
    def total_groups(self) -> int:
        return len(self.groups)

    @property
    def cross_source_groups(self) -> List[CorrelationGroup]:
        """Groups that appear in more than one source."""
        return [g for g in self.groups if len(g.sources) > 1]


def _frame_signature(tb: Traceback) -> str:
    """Build a signature from the exception type and the origin (last) frame."""
    origin = tb.origin
    location = f"{origin.filename}:{origin.lineno}" if origin else "unknown"
    return f"{tb.exc_type}@{location}"


def correlate(tracebacks: Sequence[Traceback]) -> CorrelationReport:
    """Group tracebacks by shared frame signature."""
    buckets: Dict[str, CorrelationGroup] = {}
    for tb in tracebacks:
        sig = _frame_signature(tb)
        if sig not in buckets:
            buckets[sig] = CorrelationGroup(signature=sig)
        buckets[sig].tracebacks.append(tb)

    groups = sorted(buckets.values(), key=lambda g: g.count, reverse=True)
    return CorrelationReport(groups=groups)


def top_correlated(report: CorrelationReport, n: int = 5) -> List[CorrelationGroup]:
    """Return the top-n groups by traceback count."""
    return report.groups[:n]
