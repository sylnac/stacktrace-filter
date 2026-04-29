"""Suppress duplicate or low-value tracebacks based on configurable rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Set

from stacktrace_filter.parser import Traceback


@dataclass
class SuppressorConfig:
    """Rules that determine which tracebacks to suppress."""
    # Suppress if exception type is in this set
    suppress_types: Set[str] = field(default_factory=set)
    # Suppress if the exception message contains any of these substrings
    suppress_messages: List[str] = field(default_factory=list)
    # Suppress if the traceback has fewer frames than this threshold
    min_frames: int = 1
    # Suppress if the traceback has already been seen (exact exception key)
    deduplicate: bool = False


@dataclass
class SuppressResult:
    kept: List[Traceback]
    suppressed: List[Traceback]

    @property
    def total(self) -> int:
        return len(self.kept) + len(self.suppressed)

    @property
    def suppressed_count(self) -> int:
        return len(self.suppressed)


def _exc_key(tb: Traceback) -> str:
    return f"{tb.exc_type}:{tb.exc_value}"


def _should_suppress(
    tb: Traceback,
    config: SuppressorConfig,
    seen: Set[str],
) -> bool:
    if tb.exc_type in config.suppress_types:
        return True

    exc_value_lower = (tb.exc_value or "").lower()
    for phrase in config.suppress_messages:
        if phrase.lower() in exc_value_lower:
            return True

    if len(tb.frames) < config.min_frames:
        return True

    if config.deduplicate:
        key = _exc_key(tb)
        if key in seen:
            return True
        seen.add(key)

    return False


def suppress(
    tracebacks: List[Traceback],
    config: Optional[SuppressorConfig] = None,
) -> SuppressResult:
    """Filter *tracebacks* according to *config*, returning a SuppressResult."""
    if config is None:
        config = SuppressorConfig()

    seen: Set[str] = set()
    kept: List[Traceback] = []
    suppressed: List[Traceback] = []

    for tb in tracebacks:
        if _should_suppress(tb, config, seen):
            suppressed.append(tb)
        else:
            kept.append(tb)

    return SuppressResult(kept=kept, suppressed=suppressed)
