"""Tests for stacktrace_filter.sampler."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.sampler import SamplerConfig, SamplerState, sample


def _tb(exc_type: str = "ValueError") -> Traceback:
    f = Frame(filename="app.py", lineno=1, name="main", context="x = 1")
    return Traceback(frames=[f], exc_type=exc_type, exc_value="err", raw="")


def _tbs(exc_type: str = "ValueError", n: int = 5) -> List[Traceback]:
    return [_tb(exc_type) for _ in range(n)]


def test_rate_1_keeps_all():
    tbs = _tbs(n=10)
    result = sample(tbs, SamplerConfig(rate=1.0, seed=0))
    assert len(result) == 10


def test_rate_0_drops_all():
    tbs = _tbs(n=10)
    result = sample(tbs, SamplerConfig(rate=0.0, seed=0))
    assert len(result) == 0


def test_rate_half_approx():
    tbs = _tbs(n=1000)
    result = sample(tbs, SamplerConfig(rate=0.5, seed=42))
    assert 400 < len(result) < 600


def test_max_per_type_limits():
    tbs = _tbs(exc_type="KeyError", n=20)
    result = sample(tbs, SamplerConfig(rate=1.0, max_per_type=5, seed=0))
    assert len(result) == 5


def test_max_per_type_independent_per_type():
    tbs = _tbs("KeyError", 10) + _tbs("ValueError", 10)
    result = sample(tbs, SamplerConfig(rate=1.0, max_per_type=3, seed=0))
    assert len(result) == 6


def test_max_per_type_zero_means_unlimited():
    tbs = _tbs(n=50)
    result = sample(tbs, SamplerConfig(rate=1.0, max_per_type=0, seed=0))
    assert len(result) == 50


def test_state_reset_clears_counts():
    state = SamplerState(config=SamplerConfig(rate=1.0, max_per_type=2, seed=0))
    tb = _tb("TypeError")
    state.should_keep(tb)
    state.should_keep(tb)
    assert not state.should_keep(tb)
    state.reset()
    assert state.should_keep(tb)


def test_seed_reproducible():
    tbs = _tbs(n=20)
    r1 = sample(tbs, SamplerConfig(rate=0.5, seed=7))
    r2 = sample(tbs, SamplerConfig(rate=0.5, seed=7))
    assert len(r1) == len(r2)
