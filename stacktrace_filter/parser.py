"""Parse raw Python tracebacks into structured frame objects."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

_FRAME_RE = re.compile(
    r'^\s*File "(?P<path>.+?)", line (?P<lineno>\d+), in (?P<func>.+)$'
)
_CODE_RE = re.compile(r'^\s{4}(?P<code>.+)$')
_EXC_RE = re.compile(r'^(?P<exc>[\w.]+(?:Error|Exception|Warning|KeyboardInterrupt|SystemExit)[\w.]*): (?P<msg>.*)$')


@dataclass
class Frame:
    path: str
    lineno: int
    func: str
    code: Optional[str] = None

    @property
    def is_stdlib(self) -> bool:
        return "/lib/python" in self.path or "\\lib\\python" in self.path

    @property
    def is_site_packages(self) -> bool:
        return "site-packages" in self.path


@dataclass
class Traceback:
    frames: List[Frame] = field(default_factory=list)
    exc_type: Optional[str] = None
    exc_msg: Optional[str] = None

    @property
    def origin(self) -> Optional[Frame]:
        return self.frames[-1] if self.frames else None


def parse(text: str) -> List[Traceback]:
    """Parse *text* and return a list of Traceback objects found within."""
    tracebacks: List[Traceback] = []
    current: Optional[Traceback] = None
    pending_frame: Optional[Frame] = None

    for line in text.splitlines():
        if line.strip() == "Traceback (most recent call last):"
            current = Traceback()
            tracebacks.append(current)
            pending_frame = None
            continue

        if current is None:
            continue

        frame_match = _FRAME_RE.match(line)
        if frame_match:
            pending_frame = Frame(
                path=frame_match.group("path"),
                lineno=int(frame_match.group("lineno")),
                func=frame_match.group("func"),
            )
            current.frames.append(pending_frame)
            continue

        code_match = _CODE_RE.match(line)
        if code_match and pending_frame is not None:
            pending_frame.code = code_match.group("code")
            pending_frame = None
            continue

        exc_match = _EXC_RE.match(line)
        if exc_match:
            current.exc_type = exc_match.group("exc")
            current.exc_msg = exc_match.group("msg")
            current = None
            pending_frame = None

    return tracebacks
