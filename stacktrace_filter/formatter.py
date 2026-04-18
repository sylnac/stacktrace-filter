"""Format parsed tracebacks for terminal or plain-text output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .parser import Frame, Traceback, is_stdlib, is_site_packages
from .annotator import annotate


@dataclass
class FormatOptions:
    collapse_stdlib: bool = True
    collapse_site_packages: bool = False
    color: bool = True
    show_hints: bool = True


def _label(text: str, color: bool) -> str:
    return f"\033[1;34m{text}\033[0m" if color else text


def _dim(text: str, color: bool) -> str:
    return f"\033[2m{text}\033[0m" if color else text


def _bold(text: str, color: bool) -> str:
    return f"\033[1m{text}\033[0m" if color else text


def _red(text: str, color: bool) -> str:
    return f"\033[31m{text}\033[0m" if color else text


def _yellow(text: str, color: bool) -> str:
    return f"\033[33m{text}\033[0m" if color else text


def _should_collapse(frame: Frame, opts: FormatOptions) -> bool:
    if opts.collapse_stdlib and is_stdlib(frame):
        return True
    if opts.collapse_site_packages and is_site_packages(frame):
        return True
    return False


def format_traceback(tb: Traceback, opts: Optional[FormatOptions] = None) -> str:
    if opts is None:
        opts = FormatOptions()

    lines: list[str] = []
    lines.append(_label("Traceback (most recent call last):", opts.color))

    collapsed = 0
    for frame in tb.frames:
        if _should_collapse(frame, opts):
            collapsed += 1
            continue
        if collapsed:
            lines.append(_dim(f"  ... {collapsed} frame(s) from stdlib/site-packages collapsed ...", opts.color))
            collapsed = 0
        loc = f"  File \"{frame.filename}\", line {frame.lineno}, in {frame.module}"
        lines.append(loc)
        if frame.context:
            lines.append(f"    {frame.context}")

    if collapsed:
        lines.append(_dim(f"  ... {collapsed} frame(s) from stdlib/site-packages collapsed ...", opts.color))

    exc_line = _red(f"{tb.exc_type}: {tb.exc_message}", opts.color)
    lines.append(_bold(exc_line, opts.color))

    if opts.show_hints:
        hint = annotate(tb)
        if hint:
            lines.append(_yellow(f"  Hint: {hint}", opts.color))

    return "\n".join(lines)
