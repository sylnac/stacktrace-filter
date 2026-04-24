"""Export tracebacks to various output formats (JSON, Markdown, plain text)."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import List

from .parser import Traceback


@dataclass
class ExportOptions:
    fmt: str = "text"  # "text" | "json" | "markdown"
    include_hints: bool = True
    include_summary: bool = False


def _frame_to_dict(frame) -> dict:
    return {
        "file": frame.filename,
        "line": frame.lineno,
        "function": frame.function,
        "source": frame.source,
    }


def _tb_to_dict(tb: Traceback, hints: List[str] | None = None) -> dict:
    return {
        "exception_type": tb.exc_type,
        "exception_message": tb.exc_message,
        "frames": [_frame_to_dict(f) for f in tb.frames],
        "hints": hints or [],
    }


def export_json(tracebacks: List[Traceback], hints_map: dict | None = None) -> str:
    hints_map = hints_map or {}
    data = [_tb_to_dict(tb, hints_map.get(i)) for i, tb in enumerate(tracebacks)]
    return json.dumps(data, indent=2)


def export_markdown(tracebacks: List[Traceback], hints_map: dict | None = None) -> str:
    hints_map = hints_map or {}
    lines = []
    for i, tb in enumerate(tracebacks):
        lines.append(f"## `{tb.exc_type}`: {tb.exc_message}")
        lines.append("")
        lines.append("```")
        for f in tb.frames:
            lines.append(f"  File \"{f.filename}\", line {f.lineno}, in {f.function}")
            if f.source:
                lines.append(f"    {f.source}")
        lines.append("```")
        hints = hints_map.get(i, [])
        if hints:
            lines.append("")
            lines.append("**Hints:**")
            for h in hints:
                lines.append(f"- {h}")
        lines.append("")
    return "\n".join(lines)


def export_text(tracebacks: List[Traceback], hints_map: dict | None = None) -> str:
    hints_map = hints_map or {}
    lines = []
    for i, tb in enumerate(tracebacks):
        lines.append(f"{tb.exc_type}: {tb.exc_message}")
        for f in tb.frames:
            lines.append(f"  File \"{f.filename}\", line {f.lineno}, in {f.function}")
            if f.source:
                lines.append(f"    {f.source}")
        for h in hints_map.get(i, []):
            lines.append(f"  Hint: {h}")
        lines.append("")
    return "\n".join(lines)


def export(tracebacks: List[Traceback], options: ExportOptions, hints_map: dict | None = None) -> str:
    """Export tracebacks using the given options.

    Args:
        tracebacks: List of parsed Traceback objects to export.
        options: ExportOptions controlling format and output behaviour.
        hints_map: Optional mapping of traceback index to a list of hint strings.

    Returns:
        A formatted string in the requested output format.

    Raises:
        ValueError: If ``options.fmt`` is not a recognised format.
    """
    _SUPPORTED_FORMATS = ("text", "json", "markdown")
    if options.fmt not in _SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported export format {options.fmt!r}. "
            f"Choose one of: {', '.join(_SUPPORTED_FORMATS)}"
        )
    if options.fmt == "json":
        return export_json(tracebacks, hints_map)
    if options.fmt == "markdown":
        return export_markdown(tracebacks, hints_map)
    return export_text(tracebacks, hints_map)
