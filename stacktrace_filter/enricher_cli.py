"""CLI entry point for traceback enrichment with git blame."""
from __future__ import annotations

import argparse
import sys

from .parser import parse
from .enricher import enrich, format_enriched
from .writer import write_output


def build_enricher_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-enrich",
        description="Annotate tracebacks with git blame metadata.",
    )
    p.add_argument("file", nargs="?", help="Log file to read (default: stdin)")
    p.add_argument(
        "--no-blame",
        action="store_true",
        default=False,
        help="Skip git blame lookups",
    )
    p.add_argument("-o", "--output", default=None, help="Write output to file")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_enricher_parser()
    args = parser.parse_args(argv)

    if args.file:
        try:
            text = open(args.file).read()
        except FileNotFoundError:
            print(f"error: file not found: {args.file}", file=sys.stderr)
            return 1
    else:
        text = sys.stdin.read()

    tracebacks = parse(text)
    if not tracebacks:
        print("No tracebacks found.", file=sys.stderr)
        return 0

    parts = []
    for tb in tracebacks:
        et = enrich(tb, use_git_blame=not args.no_blame)
        parts.append(format_enriched(et))

    output = "\n\n".join(parts)
    write_output(output, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
