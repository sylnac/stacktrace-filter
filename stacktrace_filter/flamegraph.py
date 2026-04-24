"""Convert profiler output to a Flame Graph compatible folded-stack format."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from stacktrace_filter.parser import Traceback
from stacktrace_filter.profiler import ProfileReport, profile


@dataclass
class FoldedStack:
    """A single line in the folded-stack format: 'frame1;frame2;... count'."""

    frames: List[str]
    count: int

    def render(self) -> str:
        return ";".join(self.frames) + f" {self.count}"


def _traceback_to_folded(tb: Traceback) -> FoldedStack:
    """Convert one traceback into a folded stack entry (count=1)."""
    labels = [
        f"{f.filename}:{f.name}:{f.lineno}" for f in tb.frames
    ]
    return FoldedStack(frames=labels, count=1)


def build_flamegraph(tracebacks: Iterable[Traceback]) -> List[FoldedStack]:
    """Aggregate tracebacks into folded stacks suitable for flamegraph.pl."""
    tbs = list(tracebacks)
    counts: dict[tuple[str, ...], int] = {}
    for tb in tbs:
        key = tuple(
            f"{f.filename}:{f.name}:{f.lineno}" for f in tb.frames
        )
        counts[key] = counts.get(key, 0) + 1
    return [
        FoldedStack(frames=list(frames), count=n)
        for frames, n in sorted(counts.items())
    ]


def render_flamegraph(stacks: List[FoldedStack]) -> str:
    """Render folded stacks as a newline-separated string."""
    return "\n".join(s.render() for s in stacks)
