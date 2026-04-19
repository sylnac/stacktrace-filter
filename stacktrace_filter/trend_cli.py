"""CLI entry point for exception trend analysis."""
from __future__ import annotations
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

from stacktrace_filter.parser import parse
from stacktrace_filter.trend import build_trend, render_trend


def build_trend_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-trend",
        description="Show exception frequency trends from a log file.",
    )
    p.add_argument("file", help="Log file to analyse")
    p.add_argument(
        "--window",
        type=int,
        default=60,
        metavar="MINUTES",
        help="Time window in minutes (default: 60)",
    )
    p.add_argument(
        "--threshold",
        type=int,
        default=2,
        help="Minimum count to flag as rising (default: 2)",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_trend_parser()
    args = parser.parse_args(argv)

    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    text = path.read_text()
    tracebacks = parse(text)

    # Assign current timestamp to all tracebacks (no embedded timestamps).
    now = datetime.utcnow()
    timestamps = [now] * len(tracebacks)

    window = timedelta(minutes=args.window)
    report = build_trend(tracebacks, timestamps, window=window)

    print(render_trend(report))

    rising = report.rising(threshold=args.threshold)
    if rising:
        print("\nRising exceptions:")
        for exc in rising:
            print(f"  ! {exc}")


if __name__ == "__main__":
    main()
