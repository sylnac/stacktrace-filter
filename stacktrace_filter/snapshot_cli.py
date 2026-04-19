"""CLI entry-point for snapshot save/diff operations."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from stacktrace_filter.parser import parse
from stacktrace_filter.snapshot import Snapshot, diff_snapshots, load_snapshot, save_snapshot


def build_snapshot_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-snapshot",
        description="Save or diff traceback snapshots.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    save_p = sub.add_parser("save", help="Parse a log file and save a snapshot.")
    save_p.add_argument("log", type=Path, help="Input log file")
    save_p.add_argument("output", type=Path, help="Output snapshot JSON")
    save_p.add_argument("--label", default="", help="Human-readable label")

    diff_p = sub.add_parser("diff", help="Diff two snapshot files.")
    diff_p.add_argument("old", type=Path, help="Older snapshot JSON")
    diff_p.add_argument("new", type=Path, help="Newer snapshot JSON")

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_snapshot_parser()
    args = parser.parse_args(argv)

    if args.command == "save":
        if not args.log.exists():
            print(f"error: file not found: {args.log}", file=sys.stderr)
            sys.exit(1)
        text = args.log.read_text()
        tracebacks = parse(text)
        label = args.label or args.log.name
        snap = Snapshot(label=label, tracebacks=tracebacks)
        save_snapshot(snap, args.output)
        print(f"Saved {len(tracebacks)} traceback(s) to {args.output}")

    elif args.command == "diff":
        for p in (args.old, args.new):
            if not p.exists():
                print(f"error: file not found: {p}", file=sys.stderr)
                sys.exit(1)
        old = load_snapshot(args.old)
        new = load_snapshot(args.new)
        result = diff_snapshots(old, new)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
