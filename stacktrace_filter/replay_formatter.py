"""Helpers for rendering replay metadata alongside formatted output."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone


def _dim(text: str) -> str:
    return f"\x1b[2m{text}\x1b[0m"


def _bold(text: str) -> str:
    return f"\x1b[1m{text}\x1b[0m"


def render_replay_header(snapshot_path: Path, *, no_color: bool = False) -> str:
    """Return a header line describing the replay source."""
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    label = f"Replaying snapshot: {snapshot_path.name}  [{ts}]"
    if no_color:
        return label + "\n"
    return _bold("\u25ba ") + _dim(label) + "\n"


def render_replay_footer(tb_count: int, *, no_color: bool = False) -> str:
    """Return a summary footer line for a replay run."""
    label = f"{tb_count} traceback(s) replayed."
    if no_color:
        return label + "\n"
    return _dim(label) + "\n"


def wrap_with_replay_chrome(
    content: str,
    snapshot_path: Path,
    tb_count: int,
    *,
    no_color: bool = False,
) -> str:
    """Surround formatted content with replay header and footer."""
    header = render_replay_header(snapshot_path, no_color=no_color)
    footer = render_replay_footer(tb_count, no_color=no_color)
    return header + content + footer
