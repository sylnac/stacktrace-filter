"""Annotate tracebacks with hints based on common exception patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from .parser import Traceback


@dataclass
class Hint:
    pattern: re.Pattern
    message: str


_HINTS: list[Hint] = [
    Hint(
        re.compile(r"ModuleNotFoundError: No module named '(?P<mod>[^']+)'"),
        "Run `pip install {mod}` or check your virtualenv.",
    ),
    Hint(
        re.compile(r"AttributeError: '(?P<tp>[^']+)' object has no attribute '(?P<attr>[^']+)'"),
        "'{tp}' has no '{attr}' — check for typos or API version mismatch.",
    ),
    Hint(
        re.compile(r"KeyError: (?P<key>.+)"),
        "Missing key {key} — guard with .get() or verify input data.",
    ),
    Hint(
        re.compile(r"TypeError: (?P<msg>.+)"),
        "Type mismatch: {msg}",
    ),
    Hint(
        re.compile(r"FileNotFoundError: \[Errno 2\] No such file or directory: '(?P<path>[^']+)'"),
        "File '{path}' not found — check CWD and path construction.",
    ),
    Hint(
        re.compile(r"RecursionError"),
        "Recursion limit hit — look for missing base case or circular references.",
    ),
]


def annotate(tb: Traceback) -> Optional[str]:
    """Return a human-readable hint for *tb*, or None if no pattern matches."""
    exc_line = f"{tb.exc_type}: {tb.exc_message}"
    for hint in _HINTS:
        m = hint.pattern.search(exc_line)
        if m:
            try:
                return hint.message.format(**m.groupdict())
            except KeyError:
                return hint.message
    return None
