"""Score tracebacks by estimated severity for prioritized output."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .parser import Traceback
from .annotator import Hint

# Exception types considered high severity
_HIGH_SEVERITY: set[str] = {
    "SystemExit",
    "MemoryError",
    "RecursionError",
    "KeyboardInterrupt",
    "SegmentationFault",
    "OSError",
    "IOError",
    "DatabaseError",
    "OperationalError",
}

_MEDIUM_SEVERITY: set[str] = {
    "ValueError",
    "TypeError",
    "AttributeError",
    "ImportError",
    "ModuleNotFoundError",
    "RuntimeError",
    "NotImplementedError",
}


@dataclass
class ScoredTraceback:
    traceback: Traceback
    score: int
    severity: str  # "high", "medium", "low"
    hints: List[Hint]


def _base_score(exc_type: str) -> int:
    if exc_type in _HIGH_SEVERITY:
        return 100
    if exc_type in _MEDIUM_SEVERITY:
        return 50
    return 20


def score(tb: Traceback, hints: List[Hint] | None = None) -> ScoredTraceback:
    """Compute a severity score for a traceback."""
    hints = hints or []
    exc_type = tb.exc_type or ""

    points = _base_score(exc_type)

    # More user frames → more relevant
    user_frames = [
        f for f in tb.frames
        if not f.is_stdlib and not f.is_site_packages
    ]
    points += len(user_frames) * 5

    # Hints indicate known actionable issues
    points += len(hints) * 10

    if points >= 80:
        severity = "high"
    elif points >= 40:
        severity = "medium"
    else:
        severity = "low"

    return ScoredTraceback(
        traceback=tb,
        score=points,
        severity=severity,
        hints=hints,
    )


def rank(tracebacks: List[Traceback]) -> List[ScoredTraceback]:
    """Return tracebacks sorted by descending score."""
    scored = [score(tb) for tb in tracebacks]
    return sorted(scored, key=lambda s: s.score, reverse=True)
