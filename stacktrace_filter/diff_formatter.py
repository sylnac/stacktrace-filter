"""Render a TracebackDiff as coloured text."""
from __future__ import annotations
from .differ import TracebackDiff, FrameDiff
from .formatter import _dim, _bold, _red, _label

_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RESET = "\033[0m"


def _green(s: str) -> str:
    return f"{_GREEN}{s}{_RESET}"


def _yellow(s: str) -> str:
    return f"{_YELLOW}{s}{_RESET}"


def _fmt_frame(f, prefix: str, colour_fn) -> str:
    loc = f"{f.filename}:{f.lineno}"
    return f"  {colour_fn(prefix)} {_bold(f.function)}  {_dim(loc)}"


def format_diff(diff: TracebackDiff, colour: bool = True) -> str:
    lines: list[str] = []

    def c(fn, s):
        return fn(s) if colour else s

    lines.append(_bold("=== Traceback Diff ===") if colour else "=== Traceback Diff ===")
    lines.append(f"  left : {diff.left.exc_type}: {diff.left.exc_message}")
    lines.append(f"  right: {diff.right.exc_type}: {diff.right.exc_message}")
    if diff.is_identical:
        lines.append(c(_green, "  Tracebacks are identical."))
        return "\n".join(lines)

    div = diff.divergence_index
    lines.append(f"  Diverges at frame index: {div}")
    lines.append("")

    for fd in diff.frame_diffs:
        if fd.status == "equal":
            lines.append(_fmt_frame(fd.left, "=", _dim if colour else str))
        elif fd.status == "changed":
            lines.append(_fmt_frame(fd.left, "-", _red if colour else str))
            lines.append(_fmt_frame(fd.right, "+", _green if colour else str))
        elif fd.status == "left_only":
            lines.append(_fmt_frame(fd.left, "-", _red if colour else str))
        else:
            lines.append(_fmt_frame(fd.right, "+", _green if colour else str))

    if not diff.same_exception:
        lines.append("")
        lines.append(c(_red, f"  - {diff.left.exc_type}: {diff.left.exc_message}"))
        lines.append(c(_green, f"  + {diff.right.exc_type}: {diff.right.exc_message}"))

    return "\n".join(lines)
