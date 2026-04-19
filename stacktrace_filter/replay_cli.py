"""CLI entry point for the replay subcommand."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from stacktrace_filter.replay import ReplayOptions, replay_to_output


def build_replay_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(description="Replay a saved snapshot through the formatting pipeline.")
    if parent is not None:
        parser = parent.add_parser("replay", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="stacktrace-replay", **kwargs)

    parser.add_argument("snapshot", type=Path, help="Path to snapshot JSON file")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Write output to file")
    parser.add_argument("--no-collapse", action="store_true", help="Show all frames")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    parser.add_argument(
        "--format",
        dest="export_format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_replay_parser()
    args = parser.parse_args(argv)

    if not args.snapshot.exists():
        print(f"error: snapshot file not found: {args.snapshot}", file=sys.stderr)
        sys.exit(1)

    opts = ReplayOptions(
        snapshot_path=args.snapshot,
        output_path=args.output,
        no_collapse=args.no_collapse,
        no_color=args.no_color,
        export_format=args.export_format,
    )
    replay_to_output(opts)


if __name__ == "__main__":
    main()
