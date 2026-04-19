"""Diff two tracebacks to highlight diverging frames."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
from .parser import Traceback, Frame


@dataclass
class FrameDiff:
    index: int
    left: Frame | None
    right: Frame | None
    status: str  # 'equal' | 'left_only' | 'right_only' | 'changed'


@dataclass
class TracebackDiff:
    left: Traceback
    right: Traceback
    frame_diffs: List[FrameDiff]
    same_exception: bool

    @property
    def divergence_index(self) -> int | None:
        for d in self.frame_diffs:
            if d.status != "equal":
                return d.index
        return None

    @property
    def is_identical(self) -> bool:
        return all(d.status == "equal" for d in self.frame_diffs) and self.same_exception


def _frame_key(f: Frame) -> Tuple[str, str, int]:
    return (f.filename, f.function, f.lineno)


def diff_tracebacks(left: Traceback, right: Traceback) -> TracebackDiff:
    """Align frames from two tracebacks and classify each position."""
    lf = left.frames
    rf = right.frames
    length = max(len(lf), len(rf))
    diffs: List[FrameDiff] = []
    for i in range(length):
        l = lf[i] if i < len(lf) else None
        r = rf[i] if i < len(rf) else None
        if l is None:
            status = "right_only"
        elif r is None:
            status = "left_only"
        elif _frame_key(l) == _frame_key(r):
            status = "equal"
        else:
            status = "changed"
        diffs.append(FrameDiff(index=i, left=l, right=r, status=status))
    same_exc = (
        left.exc_type == right.exc_type and left.exc_message == right.exc_message
    )
    return TracebackDiff(left=left, right=right, frame_diffs=diffs, same_exception=same_exc)
