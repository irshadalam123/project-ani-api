"""Keyword matching.

``CONTAINS`` matches a whole keyword, so "guide" matches "AI GUIDE" and does
not match "guidance". Matching is case-insensitive.

``REGEX`` is available for later use. Patterns are length-limited. Invalid
patterns do not match and do not raise.
"""

from __future__ import annotations

import re

from app.models.domain.automation import (
    AnyCommentTrigger,
    KeywordTrigger,
    MatchType,
    Trigger,
)

_MAX_PATTERN_LENGTH = 200
_MAX_TEXT_LENGTH = 2200


class CommentMatcher:
    def matches(self, text: str, trigger: Trigger) -> bool:
        if isinstance(trigger, AnyCommentTrigger):
            return True
        if isinstance(trigger, KeywordTrigger):
            return any(self.keyword_matches(text, keyword, trigger.match_type) for keyword in trigger.keywords)
        return False

    def keyword_matches(self, text: str, keyword: str, match_type: MatchType) -> bool:
        haystack = text[:_MAX_TEXT_LENGTH]
        needle = keyword.strip()
        if not needle:
            return False
        if match_type == MatchType.EXACT:
            return haystack.strip().casefold() == needle.casefold()
        if match_type == MatchType.STARTS_WITH:
            return haystack.strip().casefold().startswith(needle.casefold())
        if match_type == MatchType.REGEX:
            return self._regex_matches(haystack, needle)
        return self._contains_word(haystack, needle)

    def _contains_word(self, text: str, keyword: str) -> bool:
        pattern = rf"(?<!\w){re.escape(keyword)}(?!\w)"
        return re.search(pattern, text, flags=re.IGNORECASE) is not None

    def _regex_matches(self, text: str, pattern: str) -> bool:
        if len(pattern) > _MAX_PATTERN_LENGTH:
            return False
        try:
            compiled = re.compile(pattern, flags=re.IGNORECASE)
        except re.error:
            return False
        return compiled.search(text) is not None
