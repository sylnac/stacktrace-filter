"""Extract surrounding source lines for each frame in a traceback."""
from __future__ import annotations

import linecache
from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_filter.parser import Frame, Traceback


@dataclass
class AnnotatedFrame:
    frame: Frame
    context_lines: List[str] = field(default_factory=list)
    error_line: Optional[str] = None
    start_lineno: int = 0


@dataclass
class AnnotatedTraceback:
    traceback: Traceback
    frames: List[AnnotatedFrame] = field(default_factory=list)


def _extract_context(
    filename: str, lineno: int, radius: int = 2
) -> tuple[list[str], Optional[str], int]:
    """Return (context_lines, error_line, start_lineno)."""
    start = max(1, lineno - radius)
    lines: list[str] = []
    error_line: Optional[str] = None
    for ln in range(start, lineno + radius + 1):
        raw = linecache.getline(filename, ln)
        if not raw:
            continue
        text = raw.rstrip()
        lines.append(text)
        if ln == lineno:
            error_line = text
    return lines, error_line, start


def extract(tb: Traceback, radius: int = 2) -> AnnotatedTraceback:
    """Attach source context to every frame in *tb*."""
    annotated_frames: list[AnnotatedFrame] = []
    for frame in tb.frames:
        context, error_line, start = _extract_context(
            frame.filename, frame.lineno, radius
        )
        annotated_frames.append(
            AnnotatedFrame(
                frame=frame,
                context_lines=context,
                error_line=error_line,
                start_lineno=start,
            )
        )
    return AnnotatedTraceback(traceback=tb, frames=annotated_frames)
