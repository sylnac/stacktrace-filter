"""Watch a log file and stream new tracebacks as they appear."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Iterator

from stacktrace_filter.parser import Traceback, parse


def _tail_lines(path: Path, last_pos: int) -> tuple[str, int]:
    with path.open("r", errors="replace") as fh:
        fh.seek(last_pos)
        chunk = fh.read()
        return chunk, fh.tell()


def watch(
    path: Path,
    callback: Callable[[Traceback], None],
    poll_interval: float = 0.5,
    max_iterations: int | None = None,
) -> None:
    """Poll *path* and invoke *callback* for every new Traceback found."""
    pos = path.stat().st_size if path.exists() else 0
    iterations = 0
    seen: set[int] = set()

    while True:
        if path.exists():
            chunk, pos = _tail_lines(path, pos)
            if chunk:
                for tb in parse(chunk):
                    sig = hash((tb.exc_type, tb.exc_message, len(tb.frames)))
                    if sig not in seen:
                        seen.add(sig)
                        callback(tb)

        iterations += 1
        if max_iterations is not None and iterations >= max_iterations:
            break
        time.sleep(poll_interval)


def iter_watch(
    path: Path,
    poll_interval: float = 0.5,
    max_iterations: int | None = None,
) -> Iterator[Traceback]:
    """Generator version of :func:`watch`."""
    buf: list[Traceback] = []

    def _collect(tb: Traceback) -> None:
        buf.append(tb)

    pos = path.stat().st_size if path.exists() else 0
    iterations = 0
    seen: set[int] = set()

    while True:
        if path.exists():
            chunk, pos = _tail_lines(path, pos)
            if chunk:
                for tb in parse(chunk):
                    sig = hash((tb.exc_type, tb.exc_message, len(tb.frames)))
                    if sig not in seen:
                        seen.add(sig)
                        yield tb

        iterations += 1
        if max_iterations is not None and iterations >= max_iterations:
            break
        time.sleep(poll_interval)
