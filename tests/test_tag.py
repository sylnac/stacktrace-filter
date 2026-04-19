"""Tests for stacktrace_filter.tag."""
import pytest
from stacktrace_filter.parser import Traceback, Frame
from stacktrace_filter.tag import TagRule, apply_tags, group_by_tag


def _frame(path="app/views.py", lineno=10, func="view"):
    return Frame(path=path, lineno=lineno, func=func, context="")


def _tb(exc_type="ValueError", exc_message="bad input", frames=None):
    return Traceback(
        exc_type=exc_type,
        exc_message=exc_message,
        frames=frames or [_frame()],
    )


def test_no_rules_returns_untagged():
    tbs = [_tb()]
    result = apply_tags(tbs, [])
    assert len(result) == 1
    assert result[0].tags == []


def test_exc_type_pattern_matches():
    rules = [TagRule(tag="value-err", exc_type_pattern="ValueError")]
    result = apply_tags([_tb("ValueError")], rules)
    assert "value-err" in result[0].tags


def test_exc_type_pattern_no_match():
    rules = [TagRule(tag="type-err", exc_type_pattern="TypeError")]
    result = apply_tags([_tb("ValueError")], rules)
    assert result[0].tags == []


def test_message_pattern_matches():
    rules = [TagRule(tag="auth", message_pattern="permission")]
    result = apply_tags([_tb(exc_message="permission denied")], rules)
    assert "auth" in result[0].tags


def test_path_pattern_matches():
    frames = [_frame(path="app/auth/login.py")]
    rules = [TagRule(tag="auth", path_pattern=r"auth/")]
    result = apply_tags([_tb(frames=frames)], rules)
    assert "auth" in result[0].tags


def test_multiple_rules_multiple_tags():
    rules = [
        TagRule(tag="value-err", exc_type_pattern="ValueError"),
        TagRule(tag="views", path_pattern="views"),
    ]
    result = apply_tags([_tb()], rules)
    assert set(result[0].tags) == {"value-err", "views"}


def test_group_by_tag_groups_correctly():
    rules = [TagRule(tag="db", exc_type_pattern="DatabaseError")]
    tbs = [_tb("DatabaseError"), _tb("ValueError")]
    tagged = apply_tags(tbs, rules)
    groups = group_by_tag(tagged)
    assert len(groups["db"]) == 1
    assert len(groups["untagged"]) == 1


def test_group_by_tag_empty():
    groups = group_by_tag([])
    assert groups == {}
