"""Save and load Traceback snapshots to/from JSON."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from stacktrace_filter.parser import Frame, Traceback


@dataclass
class Snapshot:
    label: str
    tracebacks: List[Traceback] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def _dict_to_frame(d: dict) -> Frame:
    return Frame(
        filename=d["filename"],
        lineno=d["lineno"],
        name=d["name"],
        line=d.get("line", ""),
    )


def _dict_to_tb(d: dict) -> Traceback:
    return Traceback(
        frames=[_dict_to_frame(f) for f in d.get("frames", [])],
        exc_type=d["exc_type"],
        exc_message=d["exc_message"],
    )


def _frame_to_dict(f: Frame) -> dict:
    return {"filename": f.filename, "lineno": f.lineno, "name": f.name, "line": f.line}


def _tb_to_dict(tb: Traceback) -> dict:
    return {
        "frames": [_frame_to_dict(f) for f in tb.frames],
        "exc_type": tb.exc_type,
        "exc_message": tb.exc_message,
    }


def save_snapshot(tracebacks: List[Traceback], path: str | Path, label: str = "") -> Snapshot:
    snap = Snapshot(label=label, tracebacks=tracebacks)
    data = {
        "label": snap.label,
        "created_at": snap.created_at,
        "tracebacks": [_tb_to_dict(tb) for tb in snap.tracebacks],
    }
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))
    return snap


def load_snapshot(path: str | Path) -> Snapshot:
    data = json.loads(Path(path).read_text())
    return Snapshot(
        label=data.get("label", ""),
        created_at=data.get("created_at", ""),
        tracebacks=[_dict_to_tb(d) for d in data.get("tracebacks", [])],
    )
