"""Normalize tracebacks by stripping volatile path prefixes and memory addresses."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_filter.parser import Frame, Traceback


@dataclass
class NormalizerConfig:
    """Configuration for the normalizer."""
    # Path prefixes to strip from file paths (e.g. project root or venv root)
    strip_prefixes: List[str] = field(default_factory=list)
    # Replace memory addresses like 0x7f3a1b2c with <addr>
    redact_addresses: bool = True
    # Collapse absolute paths inside site-packages to just the package-relative part
    collapse_site_packages: bool = True


_ADDRESS_RE = re.compile(r"0x[0-9a-fA-F]{4,}")
_SITE_PKG_RE = re.compile(r".*site-packages[\\/]")


def _normalize_path(path: str, cfg: NormalizerConfig) -> str:
    """Return a cleaned-up version of *path* according to *cfg*."""
    result = path
    for prefix in cfg.strip_prefixes:
        if result.startswith(prefix):
            result = result[len(prefix):].lstrip("/\\") 
            break
    if cfg.collapse_site_packages:
        result = _SITE_PKG_RE.sub("", result)
    return result


def _normalize_text(text: Optional[str], cfg: NormalizerConfig) -> Optional[str]:
    """Optionally redact memory addresses inside *text*."""
    if text is None:
        return None
    if cfg.redact_addresses:
        return _ADDRESS_RE.sub("<addr>", text)
    return text


def _normalize_frame(frame: Frame, cfg: NormalizerConfig) -> Frame:
    return Frame(
        filename=_normalize_path(frame.filename, cfg),
        lineno=frame.lineno,
        name=frame.name,
        context=_normalize_text(frame.context, cfg),
        is_stdlib=frame.is_stdlib,
        is_site_packages=frame.is_site_packages,
    )


def normalize(tb: Traceback, cfg: Optional[NormalizerConfig] = None) -> Traceback:
    """Return a new :class:`Traceback` with normalized paths and text."""
    if cfg is None:
        cfg = NormalizerConfig()
    normalized_frames = [_normalize_frame(f, cfg) for f in tb.frames]
    return Traceback(
        frames=normalized_frames,
        exc_type=tb.exc_type,
        exc_value=_normalize_text(tb.exc_value, cfg),
        raw=tb.raw,
    )


def normalize_all(
    tracebacks: List[Traceback],
    cfg: Optional[NormalizerConfig] = None,
) -> List[Traceback]:
    """Normalize a list of tracebacks."""
    return [normalize(tb, cfg) for tb in tracebacks]
