"""Render TrendReport as a human-readable table or sparkline."""
from __future__ import annotations

from stacktrace_filter.trend import TrendReport

_SPARK = " ▁▂▃▄▅▆▇█"


def _sparkline(values: list[int]) -> str:
    if not values:
        return ""
    max_v = max(values) or 1
    return "".join(_SPARK[min(int(v / max_v * 8), 8)] for v in values)


def _bar_label(label: str, width: int = 30) -> str:
    return label[:width].ljust(width)


def format_trend(report: TrendReport, *, color: bool = True) -> str:
    lines: list[str] = []

    def _bold(s: str) -> str:
        return f"\033[1m{s}\033[0m" if color else s

    def _red(s: str) -> str:
        return f"\033[31m{s}\033[0m" if color else s

    def _yellow(s: str) -> str:
        return f"\033[33m{s}\033[0m" if color else s

    lines.append(_bold("Exception Trend Report"))
    lines.append(f"Windows: {len(report.points)}  "
                 f"Total errors: {report.totals()}")
    lines.append("")

    if not report.rising():
        lines.append("No rising exception types detected.")
    else:
        lines.append(_bold(f"{'Exception Type':<40} {'Spark':<12} {'Last':>6}"))
        lines.append("-" * 62)
        for exc_type, counts in sorted(
            report.rising().items(), key=lambda kv: -kv[1][-1]
        ):
            spark = _sparkline(counts)
            last = counts[-1] if counts else 0
            label = _bar_label(exc_type, 40)
            trend_str = f"{label} {spark:<12} {last:>6}"
            lines.append(_red(trend_str) if last > 5 else _yellow(trend_str))

    lines.append("")
    lines.append(_bold("All tracked exceptions:"))
    lines.append(_bold(f"{'Exception Type':<40} {'Spark':<12} {'Total':>6}"))
    lines.append("-" * 62)
    for exc_type, counts in sorted(
        report.by_type.items(), key=lambda kv: -sum(kv[1])
    ):
        spark = _sparkline(counts)
        total = sum(counts)
        lines.append(f"{_bar_label(exc_type, 40)} {spark:<12} {total:>6}")

    return "\n".join(lines)
