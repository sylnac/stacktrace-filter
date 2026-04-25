"""CLI entry-point for the correlator feature."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from stacktrace_filter.parser import parse
from stacktrace_filter.correlator import correlate
from stacktrace_filter.correlator_formatter import format_correlation
from stacktrace_filter.writer import write_output


def build_correlator_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-correlate",
        description="Correlate tracebacks from one or more log files.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Log files to correlate (use '-' for stdin).",
    )
    p.add_argument(
        "--top",
        type=int,
        default=0,
        metavar="N",
        help="Show only the top N groups (0 = all).",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output.",
    )
    p.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write output to FILE instead of stdout.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_correlator_parser()
    args = parser.parse_args(argv)

    all_tracebacks = []
    for path_str in args.files:
        if path_str == "-":
            text = sys.stdin.read()
            source = "stdin"
        else:
            p = Path(path_str)
            if not p.exists():
                print(f"error: file not found: {path_str}", file=sys.stderr)
                return 2
            text = p.read_text()
            source = p.name
        tbs = parse(text)
        for tb in tbs:
            tb.source = source  # type: ignore[attr-defined]
        all_tracebacks.extend(tbs)

    report = correlate(all_tracebacks)

    if args.top > 0:
        from stacktrace_filter.correlator import top_correlated
        report.groups = top_correlated(report, args.top)

    output = format_correlation(report, no_color=args.no_color)
    write_output(output, args.output)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
