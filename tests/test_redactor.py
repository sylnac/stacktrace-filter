"""Tests for stacktrace_filter.redactor."""
import pytest
from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.redactor import RedactorConfig, redact, REDACTED


def _frame(context: list[str] | None = None, locals_: dict | None = None) -> Frame:
    return Frame(
        filename="app/main.py",
        lineno=10,
        name="handler",
        context=context,
        locals=locals_,
    )


def _tb(exc_value: str = "", frames=None) -> Traceback:
    return Traceback(
        frames=frames or [_frame()],
        exc_type="ValueError",
        exc_value=exc_value,
    )


def test_redact_password_in_context():
    frame = _frame(context=["db.connect(password=secret123)"])
    result = redact(_tb(frames=[frame]))
    assert "secret123" not in result.frames[0].context[0]
    assert REDACTED in result.frames[0].context[0]


def test_redact_token_in_exc_value():
    tb = _tb(exc_value="Invalid token=abc123xyz")
    result = redact(tb)
    assert "abc123xyz" not in result.exc_value
    assert REDACTED in result.exc_value


def test_redact_email_in_context():
    frame = _frame(context=["user = user@example.com"])
    result = redact(_tb(frames=[frame]))
    assert "user@example.com" not in result.frames[0].context[0]


def test_redact_locals_by_default():
    frame = _frame(locals_={"api_key": "supersecret"})
    result = redact(_tb(frames=[frame]))
    assert "supersecret" not in result.frames[0].locals["api_key"]


def test_no_redact_locals_when_disabled():
    frame = _frame(locals_={"api_key": "supersecret"})
    config = RedactorConfig(redact_locals=False)
    result = redact(_tb(frames=[frame]), config)
    assert result.frames[0].locals["api_key"] == "supersecret"


def test_extra_pattern_redacted():
    frame = _frame(context=["ssn=123-45-6789"])
    config = RedactorConfig(extra_patterns=[r"ssn=\S+"])
    result = redact(_tb(frames=[frame]), config)
    assert "123-45-6789" not in result.frames[0].context[0]


def test_clean_text_unchanged():
    frame = _frame(context=["x = 1 + 2"])
    result = redact(_tb(frames=[frame]))
    assert result.frames[0].context[0] == "x = 1 + 2"


def test_exc_type_preserved():
    tb = _tb(exc_value="token=abc")
    result = redact(tb)
    assert result.exc_type == "ValueError"
