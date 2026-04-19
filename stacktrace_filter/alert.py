"""Simple alerting hooks triggered by the watchdog."""
from __future__ import annotations

import smtplib
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import Callable

from stacktrace_filter.parser import Traceback


@dataclass
class AlertConfig:
    smtp_host: str = "localhost"
    smtp_port: int = 25
    sender: str = "stacktrace-filter@localhost"
    recipients: list[str] = field(default_factory=list)
    subject_prefix: str = "[stacktrace-filter]"
    min_score: float = 0.0  # only alert when scorer >= this value


def _build_email(tb: Traceback, cfg: AlertConfig) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = cfg.sender
    msg["To"] = ", ".join(cfg.recipients)
    msg["Subject"] = f"{cfg.subject_prefix} {tb.exc_type}: {tb.exc_message[:80]}"
    lines = [f"{tb.exc_type}: {tb.exc_message}", ""]
    for f in tb.frames:
        lines.append(f"  File {f.filename!r}, line {f.lineno}, in {f.name}")
        if f.line:
            lines.append(f"    {f.line}")
    msg.set_content("\n".join(lines))
    return msg


def send_email_alert(tb: Traceback, cfg: AlertConfig) -> None:
    """Send a single e-mail alert for *tb* using *cfg*."""
    if not cfg.recipients:
        return
    msg = _build_email(tb, cfg)
    with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port) as smtp:
        smtp.send_message(msg)


def make_alert_callback(
    cfg: AlertConfig,
    extra: Callable[[Traceback], None] | None = None,
) -> Callable[[Traceback], None]:
    """Return a callback suitable for :func:`~stacktrace_filter.watchdog.watch`."""

    def _callback(tb: Traceback) -> None:
        send_email_alert(tb, cfg)
        if extra is not None:
            extra(tb)

    return _callback
