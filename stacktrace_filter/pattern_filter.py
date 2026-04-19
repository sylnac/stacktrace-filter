"""Filter tracebacks by matching exception type or message patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_filter.parser import Traceback


@dataclass
class PatternFilterConfig:
    include_types: List[str] = field(default_factory=list)
    exclude_types: List[str] = field(default_factory=list)
    include_messages: List[str] = field(default_factory=list)
    exclude_messages: List[str] = field(default_factory=list)


def _matches_any(text: str, patterns: List[str]) -> bool:
    return any(re.search(p, text) for p in patterns)


def _keep(tb: Traceback, cfg: PatternFilterConfig) -> bool:
    exc_type = tb.exc_type or ""
    exc_msg = tb.exc_message or ""

    if cfg.include_types and not _matches_any(exc_type, cfg.include_types):
        return False
    if cfg.exclude_types and _matches_any(exc_type, cfg.exclude_types):
        return False
    if cfg.include_messages and not _matches_any(exc_msg, cfg.include_messages):
        return False
    if cfg.exclude_messages and _matches_any(exc_msg, cfg.exclude_messages):
        return False
    return True


def apply_filter(
    tracebacks: List[Traceback],
    cfg: Optional[PatternFilterConfig] = None,
) -> List[Traceback]:
    """Return only tracebacks that pass all pattern filters."""
    if cfg is None:
        return list(tracebacks)
    return [tb for tb in tracebacks if _keep(tb, cfg)]
