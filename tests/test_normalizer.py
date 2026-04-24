"""Tests for stacktrace_filter.normalizer."""
from __future__ import annotations

import pytest

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.normalizer import (
    NormalizerConfig,
    normalize,
    normalize_all,
    _normalize_path,
    _normalize_text,
)


def _frame(
    filename: str = "/home/user/project/app/views.py",
    lineno: int = 42,
    name: str = "handle",
    context: str = "return render(request)",
    is_stdlib: bool = False,
    is_site_packages: bool = False,
) -> Frame:
    return Frame(
        filename=filename,
        lineno=lineno,
        name=name,
        context=context,
        is_stdlib=is_stdlib,
        is_site_packages=is_site_packages,
    )


def _tb(frames=None, exc_type="ValueError", exc_value="bad input") -> Traceback:
    return Traceback(
        frames=frames or [_frame()],
        exc_type=exc_type,
        exc_value=exc_value,
        raw="",
    )


# ---------------------------------------------------------------------------
# _normalize_path
# ---------------------------------------------------------------------------

def test_strip_prefix_removes_leading_path():
    cfg = NormalizerConfig(strip_prefixes=["/home/user/project/"])
    assert _normalize_path("/home/user/project/app/views.py", cfg) == "app/views.py"


def test_strip_prefix_no_match_unchanged():
    cfg = NormalizerConfig(strip_prefixes=["/other/path/"])
    result = _normalize_path("/home/user/project/app/views.py", cfg)
    assert result == "/home/user/project/app/views.py"


def test_collapse_site_packages():
    cfg = NormalizerConfig(collapse_site_packages=True)
    path = "/usr/lib/python3.11/site-packages/requests/adapters.py"
    assert _normalize_path(path, cfg) == "requests/adapters.py"


def test_no_collapse_site_packages_when_disabled():
    cfg = NormalizerConfig(collapse_site_packages=False)
    path = "/usr/lib/python3.11/site-packages/requests/adapters.py"
    assert "site-packages" in _normalize_path(path, cfg)


# ---------------------------------------------------------------------------
# _normalize_text
# ---------------------------------------------------------------------------

def test_redact_address_in_text():
    cfg = NormalizerConfig(redact_addresses=True)
    assert _normalize_text("object at 0x7f3a1b2c", cfg) == "object at <addr>"


def test_no_redact_when_disabled():
    cfg = NormalizerConfig(redact_addresses=False)
    assert _normalize_text("object at 0x7f3a1b2c", cfg) == "object at 0x7f3a1b2c"


def test_normalize_text_none_returns_none():
    cfg = NormalizerConfig()
    assert _normalize_text(None, cfg) is None


# ---------------------------------------------------------------------------
# normalize
# ---------------------------------------------------------------------------

def test_normalize_returns_new_traceback():
    tb = _tb()
    result = normalize(tb)
    assert isinstance(result, Traceback)
    assert result is not tb


def test_normalize_strips_frame_prefix():
    cfg = NormalizerConfig(strip_prefixes=["/home/user/project/"])
    tb = _tb(frames=[_frame(filename="/home/user/project/app/views.py")])
    result = normalize(tb, cfg)
    assert result.frames[0].filename == "app/views.py"


def test_normalize_redacts_exc_value():
    cfg = NormalizerConfig(redact_addresses=True)
    tb = _tb(exc_value="Error at 0xDEADBEEF occurred")
    result = normalize(tb, cfg)
    assert "<addr>" in result.exc_value


def test_normalize_preserves_exc_type():
    tb = _tb(exc_type="KeyError")
    result = normalize(tb)
    assert result.exc_type == "KeyError"


def test_normalize_all_applies_to_each():
    cfg = NormalizerConfig(strip_prefixes=["/home/user/project/"])
    tbs = [
        _tb(frames=[_frame(filename="/home/user/project/a.py")]),
        _tb(frames=[_frame(filename="/home/user/project/b.py")]),
    ]
    results = normalize_all(tbs, cfg)
    assert results[0].frames[0].filename == "a.py"
    assert results[1].frames[0].filename == "b.py"


def test_normalize_default_config_does_not_crash():
    tb = _tb()
    result = normalize(tb)
    assert result.frames[0].filename == _frame().filename
