"""Parse raw Python tracebacks into structured frame objects."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, List, Optional

_FRAME_RE = re.compile(
    r'^\s*File "(?P<path>.+?)", line (?P<lineno>\d+), in (?P<func>.+)$'
)
_CODE_RE = re.compile(r'^\s{4}(?P<code>.+)$')
_EXC_RE = re.compile(
    r'^(?P<exc>[\w.]+(?:Error|Exception|Warning|KeyboardInterrupt|SystemExit)[\w.]*): (?P<msg>.*)$'
)
_LOCAL_HEADER_RE = re.compile(r"^\s*Local variables:\s*$", re.IGNORECASE)
_LOCAL_RE = re.compile(r"^\s{4,}(?P<name>[A-Za-z_]\w*)\s*=\s*(?P<value>.*)$")


@dataclass(init=False)
class Frame:
    path: str
    lineno: int
    func: str
    code: Optional[str] = None
    locals: Optional[dict[str, Any]] = None

    def __init__(
        self,
        path: str | None = None,
        lineno: int = 0,
        func: str | None = None,
        code: Optional[str] = None,
        locals: Optional[dict[str, Any]] = None,
        *,
        filename: str | None = None,
        name: str | None = None,
        module: str | None = None,
        context: list[str] | str | None = None,
    ) -> None:
        self.path = path if path is not None else (filename or "")
        self.lineno = lineno
        self.func = func if func is not None else (name or module or "")
        if code is None and context:
            code = context[0] if isinstance(context, list) else context
        self.code = code
        self.locals = locals

    @property
    def filename(self) -> str:
        return self.path

    @property
    def name(self) -> str:
        return self.func

    @property
    def module(self) -> str:
        return self.func

    @property
    def context(self) -> list[str]:
        return [] if self.code is None else [self.code]

    @property
    def is_stdlib(self) -> bool:
        return "/lib/python" in self.path or "\\lib\\python" in self.path

    @property
    def is_site_packages(self) -> bool:
        return "site-packages" in self.path


@dataclass(init=False)
class Traceback:
    frames: List[Frame] = field(default_factory=list)
    exc_type: Optional[str] = None
    exc_msg: Optional[str] = None

    def __init__(
        self,
        frames: Optional[List[Frame]] = None,
        exc_type: Optional[str] = None,
        exc_msg: Optional[str] = None,
        *,
        exc_value: Optional[str] = None,
    ) -> None:
        self.frames = frames or []
        self.exc_type = exc_type
        self.exc_msg = exc_msg if exc_msg is not None else exc_value

    @property
    def exc_message(self) -> Optional[str]:
        return self.exc_msg

    @property
    def exc_value(self) -> Optional[str]:
        return self.exc_msg

    @property
    def origin(self) -> Optional[Frame]:
        return self.frames[-1] if self.frames else None


def is_stdlib(frame: Frame) -> bool:
    return frame.is_stdlib


def is_site_packages(frame: Frame) -> bool:
    return frame.is_site_packages


def parse(text: str) -> List[Traceback]:
    """Parse *text* and return a list of Traceback objects found within."""
    tracebacks: List[Traceback] = []
    current: Optional[Traceback] = None
    pending_frame: Optional[Frame] = None
    last_frame: Optional[Frame] = None
    in_locals = False

    for line in text.splitlines():
        if line.strip() == "Traceback (most recent call last):":
            current = Traceback()
            tracebacks.append(current)
            pending_frame = None
            last_frame = None
            in_locals = False
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
            last_frame = pending_frame
            in_locals = False
            continue

        code_match = _CODE_RE.match(line)
        if code_match and pending_frame is not None:
            pending_frame.code = code_match.group("code")
            last_frame = pending_frame
            pending_frame = None
            continue

        if _LOCAL_HEADER_RE.match(line):
            in_locals = True
            if last_frame is not None and last_frame.locals is None:
                last_frame.locals = {}
            continue

        local_match = _LOCAL_RE.match(line)
        if in_locals and local_match and last_frame is not None:
            if last_frame.locals is None:
                last_frame.locals = {}
            last_frame.locals[local_match.group("name")] = local_match.group("value")
            continue

        exc_match = _EXC_RE.match(line)
        if exc_match:
            current.exc_type = exc_match.group("exc")
            current.exc_msg = exc_match.group("msg")
            current = None
            pending_frame = None
            last_frame = None
            in_locals = False

    return tracebacks
