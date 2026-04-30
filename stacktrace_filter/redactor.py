"""Redact sensitive values from tracebacks before export or display."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, List

from stacktrace_filter.parser import Frame, Traceback

_BUILTIN_PATTERNS: List[str] = [
    r"(?i)(password|passwd|secret|token|api[_-]?key)\s*=\s*\S+",
    r"(?i)(authorization:\s*)\S+(?:\s+\S+)?",
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
]
_SECRET_NAME_RE = re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key)")

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


def _redact_local(name: str, value: Any, compiled: List[re.Pattern]) -> str:
    value_text = str(value)
    if _SECRET_NAME_RE.search(name):
        return REDACTED
    return _redact_text(value_text, compiled)


def _redact_frame(frame: Frame, compiled: List[re.Pattern], redact_locals: bool) -> Frame:
    new_code = _redact_text(frame.code, compiled) if frame.code is not None else None
    new_locals: dict[str, Any] | None = None
    if frame.locals is not None:
        if redact_locals:
            new_locals = {
                key: _redact_local(key, value, compiled)
                for key, value in frame.locals.items()
            }
        else:
            new_locals = dict(frame.locals)
    return Frame(
        path=frame.path,
        lineno=frame.lineno,
        func=frame.func,
        code=new_code,
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
        exc_msg=new_exc_value,
    )
