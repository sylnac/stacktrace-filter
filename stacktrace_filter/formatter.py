"""Formatter module: renders parsed Traceback objects into annotated, collapsed output."""

from dataclasses import dataclass
from typing import List

from .parser import Traceback, Frame, is_stdlib, is_site_packages

ANSI_RED = "\033[31m"
ANSI_YELLOW = "\033[33m"
ANSI_DIM = "\033[2m"
ANSI_BOLD = "\033[1m"
ANSI_RESET = "\033[0m"


@dataclass
class FormatOptions:
    color: bool = True
    collapse_stdlib: bool = True
    collapse_site_packages: bool = False
    max_collapsed_label: int = 3


def _label(frame: Frame) -> str:
    if is_stdlib(frame):
        return "stdlib"
    if is_site_packages(frame):
        return "site-packages"
    return "app"


def _dim(text: str, opts: FormatOptions) -> str:
    return f"{ANSI_DIM}{text}{ANSI_RESET}" if opts.color else text


def _bold(text: str, opts: FormatOptions) -> str:
    return f"{ANSI_BOLD}{text}{ANSI_RESET}" if opts.color else text


def _red(text: str, opts: FormatOptions) -> str:
    return f"{ANSI_RED}{text}{ANSI_RESET}" if opts.color else text


def _should_collapse(frame: Frame, opts: FormatOptions) -> bool:
    if opts.collapse_stdlib and is_stdlib(frame):
        return True
    if opts.collapse_site_packages and is_site_packages(frame):
        return True
    return False


def format_traceback(tb: Traceback, opts: FormatOptions | None = None) -> str:
    if opts is None:
        opts = FormatOptions()

    lines: List[str] = []
    lines.append(_bold("Traceback (most recent call last):", opts))

    i = 0
    frames = tb.frames
    while i < len(frames):
        frame = frames[i]
        if _should_collapse(frame, opts):
            group = []
            while i < len(frames) and _should_collapse(frames[i], opts):
                group.append(frames[i])
                i += 1
            tag = _label(group[0])
            count = len(group)
            summary = f"  [{count} {tag} frame{'s' if count != 1 else ''} collapsed]"
            lines.append(_dim(summary, opts))
        else:
            loc = f"  File \"{frame.filename}\", line {frame.lineno}, in {frame.name}"
            lines.append(loc)
            if frame.line:
                lines.append(f"    {frame.line}")
            i += 1

    exc_line = tb.exc_type
    if tb.exc_message:
        exc_line += f": {tb.exc_message}"
    lines.append(_red(exc_line, opts))

    if tb.origin:
        origin = tb.origin
        note = f"  ^ origin: {origin.filename}:{origin.lineno} in {origin.name}"
        lines.append(_dim(note, opts))

    return "\n".join(lines)
