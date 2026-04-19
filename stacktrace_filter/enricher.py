"""Enrich tracebacks with git blame metadata."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Optional

from .parser import Frame, Traceback


@dataclass
class BlameInfo:
    commit: str
    author: str
    summary: str


@dataclass
class EnrichedFrame:
    frame: Frame
    blame: Optional[BlameInfo] = None


@dataclass
class EnrichedTraceback:
    tb: Traceback
    frames: list[EnrichedFrame] = field(default_factory=list)


def _git_blame(path: str, lineno: int) -> Optional[BlameInfo]:
    try:
        result = subprocess.run(
            ["git", "blame", "-L", f"{lineno},{lineno}", "--porcelain", path],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return None
        lines = result.stdout.splitlines()
        if not lines:
            return None
        commit = lines[0].split()[0]
        author = next((l[7:] for l in lines if l.startswith("author ")), "unknown")
        summary = next((l[8:] for l in lines if l.startswith("summary ")), "")
        return BlameInfo(commit=commit[:8], author=author, summary=summary)
    except Exception:
        return None


def enrich(tb: Traceback, use_git_blame: bool = True) -> EnrichedTraceback:
    enriched_frames = []
    for frame in tb.frames:
        blame = _git_blame(frame.filename, frame.lineno) if use_git_blame else None
        enriched_frames.append(EnrichedFrame(frame=frame, blame=blame))
    return EnrichedTraceback(tb=tb, frames=enriched_frames)


def format_enriched(et: EnrichedTraceback) -> str:
    lines = [f"Exception: {et.tb.exc_type}: {et.tb.exc_value}"]
    for ef in et.frames:
        f = ef.frame
        line = f"  File \"{f.filename}\", line {f.lineno}, in {f.name}"
        if ef.blame:
            line += f"  # [{ef.blame.commit}] {ef.blame.author}: {ef.blame.summary}"
        lines.append(line)
    return "\n".join(lines)
