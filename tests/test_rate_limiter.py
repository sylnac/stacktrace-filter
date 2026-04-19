"""Tests for stacktrace_filter.rate_limiter."""

import time
import pytest
from stacktrace_filter.rate_limiter import RateLimiter, RateLimiterConfig


@pytest.fixture
def limiter():
    return RateLimiter(RateLimiterConfig(window_seconds=60.0, max_alerts=3))


def test_first_alert_allowed(limiter):
    assert limiter.is_allowed("KeyError") is True


def test_alerts_within_limit_allowed(limiter):
    for _ in range(3):
        assert limiter.is_allowed("KeyError") is True


def test_alert_beyond_limit_suppressed(limiter):
    for _ in range(3):
        limiter.is_allowed("KeyError")
    assert limiter.is_allowed("KeyError") is False


def test_different_keys_independent(limiter):
    for _ in range(3):
        limiter.is_allowed("KeyError")
    assert limiter.is_allowed("ValueError") is True


def test_reset_clears_bucket(limiter):
    for _ in range(3):
        limiter.is_allowed("KeyError")
    limiter.reset("KeyError")
    assert limiter.is_allowed("KeyError") is True


def test_window_expiry_allows_again():
    limiter = RateLimiter(RateLimiterConfig(window_seconds=0.05, max_alerts=1))
    limiter.is_allowed("KeyError")
    assert limiter.is_allowed("KeyError") is False
    time.sleep(0.1)
    assert limiter.is_allowed("KeyError") is True


def test_stats_returns_count(limiter):
    limiter.is_allowed("KeyError")
    limiter.is_allowed("KeyError")
    stats = limiter.stats("KeyError")
    assert stats["count"] == 2
    assert stats["window_start"] is not None


def test_stats_missing_key(limiter):
    stats = limiter.stats("unknown")
    assert stats["count"] == 0
    assert stats["window_start"] is None
