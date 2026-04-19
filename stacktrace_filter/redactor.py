"""Redact sensitive values from tracebacks before export or display."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from stacktrace_filter.parser import Traceback, Frame

_BUILTIN_PATTERNS: List[str] = [
    r"(?i)(password|passwd|secret|token|api[_-]?key)\s*=\s*\S+",
    r"(?i)(authorization:\s*)\S+",
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
]

REDACTED = "<redacted>"


@dataclass
class RedactorConfig:
    extra_patterns: List[str] = field(default_factory=list)
    redact_locals: bool = True


def _compile(config: RedactorConfig) -> List[re.Pattern]:
    patterns = _BUILTIN_PATTERNS + config.extra_patterns
    return [re.compile(p) for p in patterns]


def _redact_text(text: str, compiled: List[re.Pattern]) -> str:
    for pat in compiled:
        text = pat.sub(REDACTED, text)
    return text


def _redact_frame(frame: Frame, compiled: List[re.Pattern], redact_locals: bool) -> Frame:
    new_context = (
        [_redact_text(line, compiled) for line in frame.context]
        if frame.context
        else frame.context
    )
    new_locals: dict | None = None
    if frame.locals is not None:
        if redact_locals:
            new_locals = {
                k: _redact_text(str(v), compiled) for k, v in frame.locals.items()
            }
        else:
            new_locals = frame.locals
    return Frame(
        filename=frame.filename,
        lineno=frame.lineno,
        name=frame.name,
        context=new_context,
        locals=new_locals,
    )


def redact(tb: Traceback, config: RedactorConfig | None = None) -> Traceback:
    """Return a new Traceback with sensitive data replaced by <redacted>."""
    if config is None:
        config = RedactorConfig()
    compiled = _compile(config)
    new_frames = [_redact_frame(f, compiled, config.redact_locals) for f in tb.frames]
    new_exc_value = _redact_text(tb.exc_value or "", compiled)
    return Traceback(
        frames=new_frames,
        exc_type=tb.exc_type,
        exc_value=new_exc_value,
    )
