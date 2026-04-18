"""Group multiple tracebacks from a single log stream."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from stacktrace_filter.parser import Traceback, parse


@dataclass
class TracebackGroup:
    """A collection of tracebacks parsed from a single input."""

    tracebacks: List[Traceback] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.tracebacks)

    @property
    def exception_types(self) -> List[str]:
        return [tb.exc_type for tb in self.tracebacks if tb.exc_type]

    def unique_exceptions(self) -> List[str]:
        seen: set = set()
        result = []
        for exc in self.exception_types:
            if exc not in seen:
                seen.add(exc)
                result.append(exc)
        return result

    def filter_by_exception(self, exc_type: str) -> "TracebackGroup":
        matched = [tb for tb in self.tracebacks if tb.exc_type == exc_type]
        return TracebackGroup(tracebacks=matched)


def group(text: str) -> TracebackGroup:
    """Parse *text* and return all tracebacks wrapped in a TracebackGroup."""
    tracebacks = parse(text)
    return TracebackGroup(tracebacks=tracebacks)
