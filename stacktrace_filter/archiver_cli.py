"""CLI entry-point for the archiver sub-command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from stacktrace_filter.archiver import ArchiverConfig, archive, load_archive
from stacktrace_filter.parser import parse


def build_archiver_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    kwargs = dict(description="Archive tracebacks to rotating JSONL files.")
    if parent is not None:
        p = parent.add_parser("archive", **kwargs)
    else:
        p = argparse.ArgumentParser(**kwargs)
    sub = p.add_subparsers(dest="action", required=True)

    save = sub.add_parser("save", help="Append tracebacks from a log file to the archive.")
    save.add_argument("file", type=Path, help="Input log file.")
    save.add_argument("--dir", type=Path, default=Path(".archive"), dest="directory")
    save.add_argument("--label", default="archive")
    save.add_argument("--max-files", type=int, default=5)
    save.add_argument("--max-bytes", type=int, default=5 * 1024 * 1024)

    show = sub.add_parser("show", help="Print records from an archive file.")
    show.add_argument("file", type=Path, help="Archive JSONL file.")

    return p


def main(argv=None) -> None:
    p = build_archiver_parser()
    args = p.parse_args(argv)

    if args.action == "save":
        if not args.file.exists():
            print(f"error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        text = args.file.read_text(encoding="utf-8")
        tbs = parse(text)
        cfg = ArchiverConfig(
            directory=args.directory,
            label=args.label,
            max_files=args.max_files,
            max_bytes=args.max_bytes,
        )
        dest = archive(tbs, cfg)
        print(f"Archived {len(tbs)} traceback(s) → {dest}")

    elif args.action == "show":
        if not args.file.exists():
            print(f"error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        records = load_archive(args.file)
        for r in records:
            tb = r.get("traceback", {})
            print(f"[{r.get('ts', '?'):.3f}] {tb.get('exc_type', '?')}: {tb.get('exc_value', '')}")


if __name__ == "__main__":
    main()
