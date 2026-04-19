"""Sub-command: diff two log files and print a traceback diff."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from .parser import parse
from .differ import diff_tracebacks
from .diff_formatter import format_diff


def build_diff_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-filter diff",
        description="Diff the first traceback found in two log files.",
    )
    p.add_argument("left", type=Path, help="First log file")
    p.add_argument("right", type=Path, help="Second log file")
    p.add_argument(
        "--no-colour", action="store_true", help="Disable ANSI colour output"
    )
    p.add_argument(
        "--index",
        type=int,
        default=0,
        help="Which traceback index to compare (default: 0)",
    )
    return p


def _read_file(path: Path) -> str | None:
    """Read text from *path*, printing an error and returning None on failure."""
    try:
        return path.read_text()
    except FileNotFoundError:
        print(f"error: file not found: {path}", file=sys.stderr)
        return None
    except OSError as exc:
        print(f"error: could not read {path}: {exc}", file=sys.stderr)
        return None


def main(argv: list[str] | None = None) -> int:
    parser = build_diff_parser()
    args = parser.parse_args(argv)

    left_text = _read_file(args.left)
    if left_text is None:
        return 2

    right_text = _read_file(args.right)
    if right_text is None:
        return 2

    left_tbs = parse(left_text)
    right_tbs = parse(right_text)

    idx = args.index
    if idx >= len(left_tbs):
        print(f"error: left file has no traceback at index {idx}", file=sys.stderr)
        return 1
    if idx >= len(right_tbs):
        print(f"error: right file has no traceback at index {idx}", file=sys.stderr)
        return 1

    diff = diff_tracebacks(left_tbs[idx], right_tbs[idx])
    print(format_diff(diff, colour=not args.no_colour))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
