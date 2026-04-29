"""CLI entry-point for the suppressor feature."""
from __future__ import annotations

import argparse
import sys
from typing import List

from stacktrace_filter.parser import parse
from stacktrace_filter.formatter import FormatOptions, format_tb
from stacktrace_filter.suppressor import SuppressorConfig, suppress
from stacktrace_filter.writer import write_output


def build_suppressor_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-suppress",
        description="Filter out low-value or duplicate tracebacks.",
    )
    p.add_argument("file", nargs="?", help="Log file to read (default: stdin)")
    p.add_argument(
        "--suppress-type",
        metavar="TYPE",
        action="append",
        dest="suppress_types",
        default=[],
        help="Suppress tracebacks of this exception type (repeatable)",
    )
    p.add_argument(
        "--suppress-message",
        metavar="TEXT",
        action="append",
        dest="suppress_messages",
        default=[],
        help="Suppress tracebacks whose message contains TEXT (repeatable)",
    )
    p.add_argument(
        "--min-frames",
        type=int,
        default=1,
        metavar="N",
        help="Suppress tracebacks with fewer than N frames (default: 1)",
    )
    p.add_argument(
        "--deduplicate",
        action="store_true",
        default=False,
        help="Suppress duplicate exception type+message pairs",
    )
    p.add_argument(
        "--no-collapse",
        action="store_true",
        default=False,
        help="Show all frames without collapsing stdlib/site-packages",
    )
    p.add_argument("-o", "--output", metavar="FILE", help="Write output to FILE")
    return p


def main(argv: List[str] | None = None) -> None:
    parser = build_suppressor_parser()
    args = parser.parse_args(argv)

    if args.file:
        try:
            text = open(args.file).read()
        except FileNotFoundError:
            parser.error(f"file not found: {args.file}")
    else:
        text = sys.stdin.read()

    tracebacks = parse(text)
    config = SuppressorConfig(
        suppress_types=set(args.suppress_types),
        suppress_messages=args.suppress_messages,
        min_frames=args.min_frames,
        deduplicate=args.deduplicate,
    )
    result = suppress(tracebacks, config)

    opts = FormatOptions(collapse=not args.no_collapse)
    lines = [format_tb(tb, opts) for tb in result.kept]
    lines.append(
        f"\n# suppressor: kept {len(result.kept)}, "
        f"suppressed {result.suppressed_count} of {result.total}"
    )
    write_output("\n".join(lines), args.output)


if __name__ == "__main__":  # pragma: no cover
    main()
