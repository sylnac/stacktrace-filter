"""aggregator.py — aggregate tracebacks across multiple log sources.

Provides utilities to merge, deduplicate, and rank tracebacks collected
from several files or streams into a single unified report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Sequence

from stacktrace_filter.parser import Traceback, parse
from stacktrace_filter.deduplicator import deduplicate, DeduplicationResult
from stacktrace_filter.scorer import ScoredTraceback, rank
from stacktrace_filter.classifier import ClassifiedTraceback, classify_all


@dataclass
class AggregationSource:
    """A named source of raw log text."""

    label: str
    text: str


@dataclass
class AggregatedReport:
    """Result of aggregating tracebacks from one or more sources."""

    sources: List[str]                        # labels of contributing sources
    total_raw: int                            # total tracebacks before dedup
    dedup_result: DeduplicationResult
    ranked: List[ScoredTraceback]
    classified: List[ClassifiedTraceback]

    @property
    def unique_count(self) -> int:
        return len(self.dedup_result.groups)

    @property
    def top(self) -> ScoredTraceback | None:
        return self.ranked[0] if self.ranked else None


def _parse_source(source: AggregationSource) -> List[Traceback]:
    """Parse tracebacks from a single source, ignoring parse errors."""
    try:
        return parse(source.text)
    except Exception:
        return []


def aggregate(sources: Sequence[AggregationSource]) -> AggregatedReport:
    """Aggregate tracebacks from multiple sources into a unified report.

    Steps:
      1. Parse each source independently.
      2. Combine all tracebacks into a flat list.
      3. Deduplicate using structural fingerprints.
      4. Rank deduplicated representatives by severity score.
      5. Classify each ranked traceback.

    Args:
        sources: Sequence of :class:`AggregationSource` objects.

    Returns:
        An :class:`AggregatedReport` with deduplication and ranking results.
    """
    all_tracebacks: List[Traceback] = []
    for source in sources:
        all_tracebacks.extend(_parse_source(source))

    total_raw = len(all_tracebacks)
    dedup_result = deduplicate(all_tracebacks)

    # Extract one representative per deduplicated group for ranking.
    representatives = [g.representative for g in dedup_result.groups]
    ranked = rank(representatives)
    classified = classify_all(representatives)

    return AggregatedReport(
        sources=[s.label for s in sources],
        total_raw=total_raw,
        dedup_result=dedup_result,
        ranked=ranked,
        classified=classified,
    )


def aggregate_files(paths: Iterable[Path]) -> AggregatedReport:
    """Convenience wrapper: read files from disk and aggregate.

    Files that cannot be read are silently skipped.

    Args:
        paths: Iterable of :class:`~pathlib.Path` objects.

    Returns:
        An :class:`AggregatedReport`.
    """
    sources: List[AggregationSource] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            sources.append(AggregationSource(label=str(path), text=text))
        except OSError:
            pass
    return aggregate(sources)


def render_aggregation_report(report: AggregatedReport) -> str:
    """Render a human-readable summary of an :class:`AggregatedReport`.

    Args:
        report: The aggregated report to render.

    Returns:
        A multi-line string suitable for terminal output.
    """
    lines: List[str] = []
    lines.append("=" * 60)
    lines.append("Aggregation Report")
    lines.append("=" * 60)
    lines.append(f"Sources   : {', '.join(report.sources) or '(none)'}")
    lines.append(f"Total     : {report.total_raw} traceback(s) across all sources")
    lines.append(f"Unique    : {report.unique_count} after deduplication")
    lines.append("")

    if not report.ranked:
        lines.append("No tracebacks found.")
        return "\n".join(lines)

    lines.append("Top issues (by severity score):")
    for i, scored in enumerate(report.ranked[:10], start=1):
        tb = scored.traceback
        exc = f"{tb.exc_type}: {tb.exc_value}" if tb.exc_value else tb.exc_type
        lines.append(f"  {i:>2}. [score={scored.score:.1f}] {exc}")
        if tb.origin:
            lines.append(
                f"       at {tb.origin.filename}:{tb.origin.lineno} in {tb.origin.name}"
            )

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)
