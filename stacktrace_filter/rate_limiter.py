"""Rate limiter to suppress repeated identical alerts within a time window."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class RateLimiterConfig:
    window_seconds: float = 60.0
    max_alerts: int = 3


@dataclass
class _Bucket:
    count: int = 0
    window_start: float = field(default_factory=time.monotonic)


class RateLimiter:
    """Suppress duplicate traceback alerts within a sliding window."""

    def __init__(self, config: Optional[RateLimiterConfig] = None) -> None:
        self._config = config or RateLimiterConfig()
        self._buckets: Dict[str, _Bucket] = {}

    def _evict(self, key: str, now: float) -> None:
        bucket = self._buckets.get(key)
        if bucket and (now - bucket.window_start) >= self._config.window_seconds:
            del self._buckets[key]

    def is_allowed(self, key: str) -> bool:
        """Return True if the alert should be sent, False if it should be suppressed."""
        now = time.monotonic()
        self._evict(key, now)
        bucket = self._buckets.get(key)
        if bucket is None:
            self._buckets[key] = _Bucket(count=1, window_start=now)
            return True
        if bucket.count < self._config.max_alerts:
            bucket.count += 1
            return True
        return False

    def reset(self, key: str) -> None:
        """Manually clear the bucket for a key."""
        self._buckets.pop(key, None)

    def stats(self, key: str) -> Dict[str, object]:
        """Return current bucket stats for a key."""
        bucket = self._buckets.get(key)
        if bucket is None:
            return {"count": 0, "window_start": None}
        return {"count": bucket.count, "window_start": bucket.window_start}
