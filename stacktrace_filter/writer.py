"""Write exported content to file or stdout."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import TextIO


def write_output(content: str, output_path: str | None = None) -> None:
    """Write *content* to *output_path* or stdout if path is None."""
    if output_path is None:
        _write_stream(content, sys.stdout)
    else:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _write_stream(content: str, stream: TextIO) -> None:
    stream.write(content)
    if not content.endswith("\n"):
        stream.write("\n")
