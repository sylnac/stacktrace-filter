"""High-level pipeline: parse → annotate → export → write."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .annotator import annotate
from .exporter import ExportOptions, export
from .parser import parse
from .writer import write_output


@dataclass
class PipelineOptions:
    export: ExportOptions = field(default_factory=ExportOptions)
    output_path: Optional[str] = None
    collapse_stdlib: bool = True
    collapse_site_packages: bool = False


def run_pipeline(text: str, options: PipelineOptions | None = None) -> str:
    """Parse *text*, annotate, export and optionally write to file.

    Returns the exported string.
    """
    if options is None:
        options = PipelineOptions()

    tracebacks = parse(text)
    if not tracebacks:
        write_output("", options.output_path)
        return ""

    hints_map: dict = {}
    for i, tb in enumerate(tracebacks):
        hints = annotate(tb)
        if hints:
            hints_map[i] = [h.message for h in hints]

    result = export(tracebacks, options.export, hints_map)
    write_output(result, options.output_path)
    return result
