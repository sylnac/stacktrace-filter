"""CLI entry-point for the watchdog feature."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from stacktrace_filter.formatter import FormatOptions, format_traceback
from stacktrace_filter.watchdog import iter_watch


def build_watchdog_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-watch",
        description="Watch a log file and print new tracebacks as they appear.",
    )
    p.add_argument("file", type=Path, help="Log file to watch")
    p.add_argument(
        "--poll",
        type=float,
        default=0.5,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 0.5)",
    )
    p.add_argument(
        "--no-collapse",
        action="store_true",
        help="Show all frames including stdlib/site-packages",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color output",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_watchdog_parser()
    args = parser.parse_args(argv)

    if not args.file.exists():
        print(f"error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    opts = FormatOptions(
        collapse=not args.no_collapse,
        color=not args.no_color,
    )

    try:
        for tb in iter_watch(args.file, poll_interval=args.poll):
            print(format_traceback(tb, opts))
            print(flush=True)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
