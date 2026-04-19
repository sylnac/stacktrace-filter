"""Throttle: suppress repeated identical tracebacks within a time window."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List

from stacktrace_filter.parser import Traceback


@dataclass
class ThrottleConfig:
    window_seconds: float = 60.0
    max_per_window: int = 3


@dataclass
class ThrottleState:
    config: ThrottleConfig = field(default_factory=ThrottleConfig)
    _buckets: Dict[str, List[float]] = field(default_factory=dict, repr=False)

    def _key(self, tb: Traceback) -> str:
        loc = f"{tb.frames[-1].filename}:{tb.frames[-1].lineno}" if tb.frames else "?"
        return f"{tb.exc_type}@{loc}"

    def _evict(self, key: str, now: float) -> None:
        cutoff = now - self.config.window_seconds
        self._buckets[key] = [t for t in self._buckets.get(key, []) if t >= cutoff]

    def should_emit(self, tb: Traceback) -> bool:
        key = self._key(tb)
        now = time.monotonic()
        self._evict(key, now)
        bucket = self._buckets.setdefault(key, [])
        if len(bucket) < self.config.max_per_window:
            bucket.append(now)
            return True
        return False

    def apply(self, tracebacks: List[Traceback]) -> List[Traceback]:
        return [tb for tb in tracebacks if self.should_emit(tb)]
