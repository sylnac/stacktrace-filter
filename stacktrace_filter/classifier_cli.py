"""CLI entry-point for the classifier feature."""
from __future__ import annotations

import argparse
import sys

from .classifier import classify_all, Severity
from .classifier_formatter import render_classified_report
from .formatter import FormatOptions
from .parser import parse
from .writer import write_output


def build_classifier_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-classify",
        description="Classify tracebacks by severity.",
    )
    p.add_argument("file", nargs="?", help="Log file (defaults to stdin)")
    p.add_argument(
        "--min-severity",
        choices=[s.value for s in Severity],
        default="info",
        help="Only show tracebacks at or above this severity (default: info)",
    )
    p.add_argument(
        "--no-collapse", action="store_true", help="Show all frames"
    )
    p.add_argument(
        "--show-reasons", action="store_true", help="Show classification reasons"
    )
    p.add_argument("-o", "--output", help="Write output to file")
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_classifier_parser()
    args = parser.parse_args(argv)

    try:
        if args.file:
            with open(args.file) as fh:
                text = fh.read()
        else:
            text = sys.stdin.read()
    except FileNotFoundError:
        parser.error(f"File not found: {args.file}")
        return

    tracebacks = parse(text)
    classified = classify_all(tracebacks)

    order = [Severity.CRITICAL, Severity.ERROR, Severity.WARNING, Severity.INFO]
    min_idx = order.index(Severity(args.min_severity))
    classified = [c for c in classified if order.index(c.severity) <= min_idx]

    opts = FormatOptions(collapse_stdlib=not args.no_collapse)
    report = render_classified_report(
        classified, opts, show_reasons=args.show_reasons
    )
    write_output(report, args.output)


if __name__ == "__main__":
    main()
