"""Classify tracebacks into severity tiers based on exception type and origin."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from .parser import Traceback


class Severity(str, Enum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


_CRITICAL_TYPES = {
    "SystemExit", "MemoryError", "RecursionError", "KeyboardInterrupt",
    "SegmentationFault", "OSError", "IOError",
}

_WARNING_TYPES = {
    "DeprecationWarning", "UserWarning", "ResourceWarning",
    "FutureWarning", "PendingDeprecationWarning",
}


@dataclass
class ClassifiedTraceback:
    traceback: Traceback
    severity: Severity
    reasons: List[str] = field(default_factory=list)


def _classify_severity(tb: Traceback) -> tuple[Severity, list[str]]:
    reasons: list[str] = []
    exc_type = tb.exc_type or ""

    if exc_type in _CRITICAL_TYPES:
        reasons.append(f"{exc_type} is a critical exception type")
        return Severity.CRITICAL, reasons

    if exc_type in _WARNING_TYPES:
        reasons.append(f"{exc_type} is a warning-level exception")
        return Severity.WARNING, reasons

    if exc_type.endswith("Error") or exc_type.endswith("Exception"):
        reasons.append(f"{exc_type} matches error/exception pattern")
        return Severity.ERROR, reasons

    if exc_type.endswith("Warning"):
        reasons.append(f"{exc_type} matches warning pattern")
        return Severity.WARNING, reasons

    reasons.append("No specific severity rule matched")
    return Severity.INFO, reasons


def classify(tb: Traceback) -> ClassifiedTraceback:
    """Classify a single traceback into a severity tier."""
    severity, reasons = _classify_severity(tb)
    return ClassifiedTraceback(traceback=tb, severity=severity, reasons=reasons)


def classify_all(tracebacks: list[Traceback]) -> list[ClassifiedTraceback]:
    """Classify a list of tracebacks, sorted by severity (critical first)."""
    order = [Severity.CRITICAL, Severity.ERROR, Severity.WARNING, Severity.INFO]
    classified = [classify(tb) for tb in tracebacks]
    classified.sort(key=lambda c: order.index(c.severity))
    return classified
