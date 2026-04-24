"""CLI entry-point for the flamegraph sub-command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from stacktrace_filter.parser import parse
from stacktrace_filter.flamegraph import build_flamegraph, render_flamegraph
from stacktrace_filter.writer import write_output


def build_flamegraph_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-flamegraph",
        description="Emit folded-stack lines for use with flamegraph.pl",
    )
    p.add_argument(
        "file",
        nargs="?",
        help="Log file to read (default: stdin)",
    )
    p.add_argument(
        "-o",
        "--output",
        default=None,
        help="Write folded stacks to this file (default: stdout)",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_flamegraph_parser()
    args = parser.parse_args(argv)

    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        text = path.read_text()
    else:
        text = sys.stdin.read()

    tracebacks = parse(text)
    stacks = build_flamegraph(tracebacks)
    output = render_flamegraph(stacks)

    write_output(output, args.output)


if __name__ == "__main__":  # pragma: no cover
    main()
