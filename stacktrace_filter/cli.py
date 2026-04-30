"""CLI entry point for stacktrace-filter."""

import argparse
import sys

from stacktrace_filter.formatter import FormatOptions, format_traceback
from stacktrace_filter.parser import parse
from stacktrace_filter.redactor import redact


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-filter",
        description="Collapse and annotate Python tracebacks for faster debugging.",
    )
    p.add_argument(
        "file",
        nargs="?",
        help="Path to a log file. Reads from stdin if omitted.",
    )
    p.add_argument(
        "--no-collapse",
        action="store_true",
        default=False,
        help="Show all frames, including stdlib and site-packages.",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI color output.",
    )
    p.add_argument(
        "--show-locals",
        action="store_true",
        default=False,
        help="Include local variable annotations (if present).",
    )
    p.add_argument(
        "--redact",
        action="store_true",
        default=False,
        help="Mask sensitive values in exception text, code context, and local variables.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.file:
        try:
            text = open(args.file, encoding="utf-8").read()
        except OSError as exc:
            print(f"stacktrace-filter: error: {exc}", file=sys.stderr)
            return 1
    else:
        text = sys.stdin.read()

    tracebacks = parse(text)

    if not tracebacks:
        print(text, end="")
        return 0

    opts = FormatOptions(
        collapse_stdlib=not args.no_collapse,
        color=not args.no_color,
        show_locals=args.show_locals,
    )

    for tb in tracebacks:
        if args.redact:
            tb = redact(tb)
        print(format_traceback(tb, opts))

    return 0


if __name__ == "__main__":
    sys.exit(main())
