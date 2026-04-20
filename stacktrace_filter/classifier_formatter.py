"""Render classified tracebacks with severity badges."""
from __future__ import annotations

from typing import List

from .classifier import ClassifiedTraceback, Severity
from .formatter import FormatOptions, format_traceback


_SEVERITY_COLORS = {
    Severity.CRITICAL: "\033[1;31m",  # bold red
    Severity.ERROR: "\033[31m",        # red
    Severity.WARNING: "\033[33m",      # yellow
    Severity.INFO: "\033[36m",         # cyan
}
_RESET = "\033[0m"


def _badge(severity: Severity, *, color: bool = True) -> str:
    label = f"[{severity.value.upper()}]"
    if not color:
        return label
    code = _SEVERITY_COLORS.get(severity, "")
    return f"{code}{label}{_RESET}"


def format_classified(
    classified: ClassifiedTraceback,
    options: FormatOptions | None = None,
    *,
    color: bool = True,
    show_reasons: bool = False,
) -> str:
    opts = options or FormatOptions()
    badge = _badge(classified.severity, color=color)
    header = f"{badge} "
    body = format_traceback(classified.traceback, opts)
    lines = [header + body.splitlines()[0]] + body.splitlines()[1:]
    if show_reasons and classified.reasons:
        lines.append("  Reasons:")
        for reason in classified.reasons:
            lines.append(f"    - {reason}")
    return "\n".join(lines)


def render_classified_report(
    classified_list: List[ClassifiedTraceback],
    options: FormatOptions | None = None,
    *,
    color: bool = True,
    show_reasons: bool = False,
) -> str:
    if not classified_list:
        return "No tracebacks to classify."
    sections = [
        format_classified(c, options, color=color, show_reasons=show_reasons)
        for c in classified_list
    ]
    return "\n\n".join(sections)
