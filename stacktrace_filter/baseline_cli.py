"""CLI entry-point for baseline comparison."""
from __future__ import annotations

import argparse
import sys

from stacktrace_filter.parser import parse
from stacktrace_filter.snapshot import load_snapshot
from stacktrace_filter.baseline import compare, render_baseline_report


def build_baseline_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-baseline",
        description="Compare a log file against a saved baseline snapshot.",
    )
    p.add_argument("snapshot", help="Path to baseline snapshot JSON file")
    p.add_argument(
        "logfile",
        nargs="?",
        help="Log file to analyse (default: stdin)",
    )
    p.add_argument(
        "--fail-on-regression",
        action="store_true",
        default=False,
        help="Exit with code 1 when new exceptions are found",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_baseline_parser()
    args = parser.parse_args(argv)

    try:
        baseline = load_snapshot(args.snapshot)
    except FileNotFoundError:
        print(f"error: snapshot file not found: {args.snapshot}", file=sys.stderr)
        sys.exit(1)

    if args.logfile:
        try:
            text = open(args.logfile).read()
        except FileNotFoundError:
            print(f"error: log file not found: {args.logfile}", file=sys.stderr)
            sys.exit(1)
    else:
        text = sys.stdin.read()

    tracebacks = parse(text)
    result = compare(tracebacks, baseline)
    print(render_baseline_report(result))

    if args.fail_on_regression and result.has_regressions:
        sys.exit(1)


if __name__ == "__main__":
    main()
