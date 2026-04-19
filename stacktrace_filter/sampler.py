"""Probabilistic and rate-based traceback sampler."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List

from stacktrace_filter.parser import Traceback


@dataclass
class SamplerConfig:
    rate: float = 1.0  # fraction 0.0–1.0 to keep
    max_per_type: int = 0  # 0 = unlimited
    seed: int | None = None


@dataclass
class SamplerState:
    config: SamplerConfig
    _rng: random.Random = field(init=False)
    _counts: dict[str, int] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.config.seed)

    def _exc_type(self, tb: Traceback) -> str:
        return tb.exc_type or "Unknown"

    def should_keep(self, tb: Traceback) -> bool:
        if self._rng.random() > self.config.rate:
            return False
        if self.config.max_per_type > 0:
            key = self._exc_type(tb)
            count = self._counts.get(key, 0)
            if count >= self.config.max_per_type:
                return False
            self._counts[key] = count + 1
        return True

    def reset(self) -> None:
        self._counts.clear()


def sample(tracebacks: List[Traceback], config: SamplerConfig) -> List[Traceback]:
    """Return a filtered list of tracebacks according to sampling config."""
    state = SamplerState(config=config)
    return [tb for tb in tracebacks if state.should_keep(tb)]
