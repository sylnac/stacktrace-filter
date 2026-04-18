"""Deduplication of tracebacks based on structural similarity."""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import md5
from typing import List

from stacktrace_filter.parser import Traceback


def _frame_sig(tb: Traceback) -> str:
    """Produce a hashable signature from a traceback's frames and exception."""
    parts = [f"{f.filename}:{f.lineno}:{f.name}" for f in tb.frames]
    parts.append(tb.exc_type)
    return md5("|".join(parts).encode()).hexdigest()


@dataclass
class DeduplicatedGroup:
    representative: Traceback
    count: int = 1
    fingerprint: str = ""

    def __post_init__(self) -> None:
        if not self.fingerprint:
            self.fingerprint = _frame_sig(self.representative)


@dataclass
class DeduplicationResult:
    groups: List[DeduplicatedGroup] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(g.count for g in self.groups)

    @property
    def unique(self) -> int:
        return len(self.groups)

    @property
    def duplicate_count(self) -> int:
        return self.total - self.unique


def deduplicate(tracebacks: List[Traceback]) -> DeduplicationResult:
    """Group tracebacks by structural fingerprint, keeping one representative each."""
    seen: dict[str, DeduplicatedGroup] = {}
    for tb in tracebacks:
        fp = _frame_sig(tb)
        if fp in seen:
            seen[fp].count += 1
        else:
            seen[fp] = DeduplicatedGroup(representative=tb, count=1, fingerprint=fp)
    return DeduplicationResult(groups=list(seen.values()))
