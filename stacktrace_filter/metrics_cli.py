"""CLI entry point for the metrics subcommand."""
from __future__ import annotations
import argparse
import sys
from stacktrace_filter.parser import parse
from stacktrace_filter.metrics import compute_metrics, render_metrics


def build_metrics_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(description="Show aggregate metrics for tracebacks in a log file.")
    if parent is not None:
        p = parent.add_parser("metrics", **kwargs)
    else:
        p = argparse.ArgumentParser(**kwargs)
    p.add_argument("file", help="Log file to analyse")
    p.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Emit metrics as JSON",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_metrics_parser()
    args = parser.parse_args(argv)

    try:
        text = open(args.file).read()
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    tracebacks = parse(text)
    report = compute_metrics(tracebacks)

    if args.json:
        import json
        print(json.dumps({
            "total": report.total,
            "avg_depth": report.avg_depth,
            "by_exception": report.by_exception,
            "by_module": report.by_module,
            "top_files": report.top_files,
        }, indent=2))
    else:
        print(render_metrics(report))


if __name__ == "__main__":
    main()
