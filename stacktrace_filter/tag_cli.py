"""CLI entry point for tagging tracebacks from a log file."""
from __future__ import annotations
import argparse
import json
import sys

from stacktrace_filter.parser import parse
from stacktrace_filter.tag import TagRule, apply_tags, group_by_tag


def build_tag_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="stacktrace-tag",
        description="Tag tracebacks in a log file using JSON rules.",
    )
    p.add_argument("file", help="Log file to read (use - for stdin)")
    p.add_argument(
        "--rules",
        required=True,
        metavar="RULES_JSON",
        help='JSON file containing list of tag rules: [{"tag", "exc_type_pattern", ...}]',
    )
    p.add_argument(
        "--group",
        action="store_true",
        help="Group output by tag",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_tag_parser()
    args = parser.parse_args(argv)

    try:
        with open(args.rules) as fh:
            raw_rules = json.load(fh)
    except FileNotFoundError:
        parser.error(f"Rules file not found: {args.rules}")

    rules = [
        TagRule(
            tag=r["tag"],
            exc_type_pattern=r.get("exc_type_pattern", ""),
            path_pattern=r.get("path_pattern", ""),
            message_pattern=r.get("message_pattern", ""),
        )
        for r in raw_rules
    ]

    if args.file == "-":
        text = sys.stdin.read()
    else:
        try:
            with open(args.file) as fh:
                text = fh.read()
        except FileNotFoundError:
            parser.error(f"Log file not found: {args.file}")

    tracebacks = parse(text)
    tagged = apply_tags(tracebacks, rules)

    if args.group:
        groups = group_by_tag(tagged)
        for tag, items in groups.items():
            print(f"\n[{tag}] ({len(items)} traceback(s))")
            for item in items:
                print(f"  {item.traceback.exc_type}: {item.traceback.exc_message}")
    else:
        for item in tagged:
            tag_str = ", ".join(item.tags) if item.tags else "untagged"
            print(f"[{tag_str}] {item.traceback.exc_type}: {item.traceback.exc_message}")
