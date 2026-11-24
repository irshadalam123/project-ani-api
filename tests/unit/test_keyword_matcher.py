"""Keyword matching rules."""

from app.automation.matcher import CommentMatcher
from app.models.domain.automation import AnyCommentTrigger, KeywordTrigger, MatchType


def test_contains_matches_keyword_and_rejects_longer_word() -> None:
    matcher = CommentMatcher()
    trigger = KeywordTrigger(keywords=["guide"], match_type=MatchType.CONTAINS)
    assert matcher.matches("GUIDE", trigger)
    assert matcher.matches("guide", trigger)
    assert matcher.matches("AI GUIDE", trigger)
    assert matcher.matches("send me the guide", trigger)
    assert not matcher.matches("guidance", trigger)
    assert not matcher.matches("guidebook", trigger)


def test_exact_and_starts_with() -> None:
    matcher = CommentMatcher()
    exact = KeywordTrigger(keywords=["guide"], match_type=MatchType.EXACT)
    starts = KeywordTrigger(keywords=["guide"], match_type=MatchType.STARTS_WITH)
    assert matcher.matches("GUIDE", exact)
    assert not matcher.matches("AI GUIDE", exact)
    assert matcher.matches("guide please", starts)
    assert not matcher.matches("the guide", starts)


def test_any_comment_and_invalid_regex() -> None:
    matcher = CommentMatcher()
    assert matcher.matches("", AnyCommentTrigger())
    regex = KeywordTrigger(keywords=["["], match_type=MatchType.REGEX)
    assert not matcher.matches("guide", regex)
