"""Frame-level hotspot profiler: counts how often each (file, function) pair
appears across a collection of Traceback objects and surfaces the top offenders."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, List, Tuple

from stacktrace_filter.parser import Traceback


@dataclass
class HotFrame:
    file: str
    function: str
    hits: int


@dataclass
class ProfileReport:
    total_tracebacks: int
    total_frames: int
    hotspots: List[HotFrame] = field(default_factory=list)

    def top(self, n: int = 5) -> List[HotFrame]:
        return self.hotspots[:n]


def _frame_key(file: str, function: str) -> Tuple[str, str]:
    return (file, function)


def profile(tracebacks: Iterable[Traceback], top_n: int = 10) -> ProfileReport:
    """Count (file, function) occurrences across all frames and return a report."""
    counter: Counter[Tuple[str, str]] = Counter()
    total_frames = 0
    total_tracebacks = 0

    for tb in tracebacks:
        total_tracebacks += 1
        for frame in tb.frames:
            key = _frame_key(frame.file, frame.function)
            counter[key] += 1
            total_frames += 1

    hotspots = [
        HotFrame(file=k[0], function=k[1], hits=v)
        for k, v in counter.most_common(top_n)
    ]

    return ProfileReport(
        total_tracebacks=total_tracebacks,
        total_frames=total_frames,
        hotspots=hotspots,
    )


def render_profile_report(report: ProfileReport, use_color: bool = True) -> str:
    """Render a ProfileReport as a human-readable string."""
    lines: List[str] = []

    header = "Frame Hotspot Profile"
    if use_color:
        header = f"\033[1m{header}\033[0m"
    lines.append(header)
    lines.append(
        f"  Tracebacks : {report.total_tracebacks}"
    )
    lines.append(f"  Frames     : {report.total_frames}")
    lines.append("")

    if not report.hotspots:
        lines.append("  (no frames found)")
        return "\n".join(lines)

    lines.append("  Top hotspots:")
    for rank, hf in enumerate(report.hotspots, 1):
        label = f"{hf.file}::{hf.function}"
        if use_color:
            label = f"\033[33m{label}\033[0m"
        lines.append(f"  {rank:>3}. {hf.hits:>4}x  {label}")

    return "\n".join(lines)
