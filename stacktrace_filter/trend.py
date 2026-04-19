"""Track exception frequency over time windows."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

from stacktrace_filter.parser import Traceback


@dataclass
class TrendPoint:
    timestamp: datetime
    exception_type: str
    count: int


@dataclass
class TrendReport:
    window: timedelta
    points: List[TrendPoint] = field(default_factory=list)

    def totals(self) -> Dict[str, int]:
        totals: Dict[str, int] = defaultdict(int)
        for p in self.points:
            totals[p.exception_type] += p.count
        return dict(totals)

    def rising(self, threshold: int = 2) -> List[str]:
        """Return exception types whose count exceeds threshold."""
        return [exc for exc, cnt in self.totals().items() if cnt >= threshold]


def build_trend(
    tracebacks: List[Traceback],
    timestamps: List[datetime],
    window: timedelta = timedelta(hours=1),
) -> TrendReport:
    """Aggregate tracebacks into a TrendReport within the given window."""
    if len(tracebacks) != len(timestamps):
        raise ValueError("tracebacks and timestamps must have equal length")

    now = max(timestamps) if timestamps else datetime.utcnow()
    cutoff = now - window
    report = TrendReport(window=window)

    counts: Dict[str, int] = defaultdict(int)
    bucket_time: Dict[str, datetime] = {}

    for tb, ts in zip(tracebacks, timestamps):
        if ts < cutoff:
            continue
        exc = tb.exception_type or "Unknown"
        counts[exc] += 1
        bucket_time[exc] = ts

    for exc, cnt in counts.items():
        report.points.append(TrendPoint(
            timestamp=bucket_time[exc],
            exception_type=exc,
            count=cnt,
        ))

    return report


def render_trend(report: TrendReport) -> str:
    lines = [f"Trend window: {report.window}"]
    totals = report.totals()
    if not totals:
        lines.append("  (no data)")
        return "\n".join(lines)
    for exc, cnt in sorted(totals.items(), key=lambda x: -x[1]):
        bar = "#" * min(cnt, 40)
        lines.append(f"  {exc:<40} {bar} ({cnt})")
    return "\n".join(lines)
