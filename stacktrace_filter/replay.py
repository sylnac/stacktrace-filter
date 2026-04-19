"""Replay saved snapshots through the formatting pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from stacktrace_filter.snapshot import load
from stacktrace_filter.pipeline import PipelineOptions, run_pipeline
from stacktrace_filter.writer import write_output


@dataclass
class ReplayOptions:
    snapshot_path: Path
    output_path: Path | None = None
    no_collapse: bool = False
    no_color: bool = False
    export_format: str = "text"  # text | json | markdown


def replay(opts: ReplayOptions) -> str:
    """Load a snapshot and re-run it through the pipeline, returning output."""
    tracebacks = load(opts.snapshot_path)
    if not tracebacks:
        return "(snapshot is empty)\n"

    pipeline_opts = PipelineOptions(
        no_collapse=opts.no_collapse,
        no_color=opts.no_color,
        export_format=opts.export_format,
    )
    return run_pipeline(tracebacks, pipeline_opts)


def replay_to_output(opts: ReplayOptions) -> None:
    """Replay a snapshot and write results to file or stdout."""
    result = replay(opts)
    write_output(result, opts.output_path)
