"""CLI entry point for throttle: filter a log file suppressing repeated tracebacks."""
from __future__ import annotations

import argparse
import sys

from stacktrace_filter.parser import parse
from stacktrace_filter.formatter import FormatOptions, format_traceback
from stacktrace_filter.throttle import ThrottleConfig, ThrottleState
from stacktrace_filter.writer import write_output


def build_throttle_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-throttle",
        description="Suppress repeated identical tracebacks within a sliding window.",
    )
    p.add_argument("file", nargs="?", help="Log file to read (default: stdin)")
    p.add_argument("--window", type=float, default=60.0, metavar="SECS",
                   help="Time window in seconds (default: 60)")
    p.add_argument("--max", type=int, default=3, dest="max_per_window",
                   metavar="N", help="Max emissions per window (default: 3)")
    p.add_argument("--no-collapse", action="store_true",
                   help="Show all frames including stdlib")
    p.add_argument("--output", "-o", default=None, help="Output file (default: stdout)")
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_throttle_parser()
    args = parser.parse_args(argv)

    if args.file:
        try:
            text = open(args.file).read()
        except FileNotFoundError:
            print(f"error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
    else:
        text = sys.stdin.read()

    tracebacks = parse(text)
    config = ThrottleConfig(window_seconds=args.window, max_per_window=args.max_per_window)
    state = ThrottleState(config)
    filtered = state.apply(tracebacks)

    opts = FormatOptions(collapse_stdlib=not args.no_collapse)
    lines = []
    for tb in filtered:
        lines.append(format_traceback(tb, opts))

    output = "\n".join(lines)
    write_output(output, args.output)
