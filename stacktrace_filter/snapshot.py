"""Snapshot: save and load traceback sessions to/from JSON for later comparison."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from stacktrace_filter.exporter import _tb_to_dict
from stacktrace_filter.parser import Frame, Traceback


@dataclass
class Snapshot:
    label: str
    tracebacks: List[Traceback]


def _dict_to_frame(d: dict) -> Frame:
    return Frame(
        filename=d["filename"],
        lineno=d["lineno"],
        name=d["name"],
        text=d.get("text", ""),
    )


def _dict_to_tb(d: dict) -> Traceback:
    frames = [_dict_to_frame(f) for f in d.get("frames", [])]
    return Traceback(
        frames=frames,
        exc_type=d["exc_type"],
        exc_message=d["exc_message"],
        raw=d.get("raw", ""),
    )


def save_snapshot(snapshot: Snapshot, path: Path) -> None:
    """Persist a snapshot to a JSON file."""
    payload = {
        "label": snapshot.label,
        "tracebacks": [_tb_to_dict(tb) for tb in snapshot.tracebacks],
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def load_snapshot(path: Path) -> Snapshot:
    """Load a snapshot from a JSON file."""
    data = json.loads(Path(path).read_text())
    tracebacks = [_dict_to_tb(d) for d in data.get("tracebacks", [])]
    return Snapshot(label=data["label"], tracebacks=tracebacks)


def diff_snapshots(old: Snapshot, new: Snapshot) -> dict:
    """Return a simple summary dict comparing two snapshots."""
    old_types = {tb.exc_type for tb in old.tracebacks}
    new_types = {tb.exc_type for tb in new.tracebacks}
    return {
        "old_label": old.label,
        "new_label": new.label,
        "added": sorted(new_types - old_types),
        "removed": sorted(old_types - new_types),
        "common": sorted(old_types & new_types),
        "old_count": len(old.tracebacks),
        "new_count": len(new.tracebacks),
    }
