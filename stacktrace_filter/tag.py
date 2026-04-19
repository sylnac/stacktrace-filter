"""Tag tracebacks with user-defined labels based on pattern matching."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Sequence
import re

from stacktrace_filter.parser import Traceback


@dataclass
class TagRule:
    tag: str
    exc_type_pattern: str = ""
    path_pattern: str = ""
    message_pattern: str = ""


@dataclass
class TaggedTraceback:
    traceback: Traceback
    tags: list[str] = field(default_factory=list)


def _matches_rule(tb: Traceback, rule: TagRule) -> bool:
    if rule.exc_type_pattern:
        if not re.search(rule.exc_type_pattern, tb.exc_type or ""):
            return False
    if rule.message_pattern:
        if not re.search(rule.message_pattern, tb.exc_message or ""):
            return False
    if rule.path_pattern:
        if not any(re.search(rule.path_pattern, f.path) for f in tb.frames):
            return False
    return True


def apply_tags(
    tracebacks: Sequence[Traceback],
    rules: Sequence[TagRule],
) -> list[TaggedTraceback]:
    result = []
    for tb in tracebacks:
        tags = [rule.tag for rule in rules if _matches_rule(tb, rule)]
        result.append(TaggedTraceback(traceback=tb, tags=tags))
    return result


def group_by_tag(
    tagged: Sequence[TaggedTraceback],
) -> dict[str, list[TaggedTraceback]]:
    groups: dict[str, list[TaggedTraceback]] = {}
    for item in tagged:
        for tag in item.tags:
            groups.setdefault(tag, []).append(item)
        if not item.tags:
            groups.setdefault("untagged", []).append(item)
    return groups
