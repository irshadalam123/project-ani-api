"""Errors raised by the Instagram integration."""

from app.core.exceptions import ExternalAPIException, RateLimitException


class InstagramConfigError(ExternalAPIException):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="INSTAGRAM_NOT_CONFIGURED", transient=False, status_code=503)


class InstagramPermanentError(ExternalAPIException):
    def __init__(self, message: str, code: str = "INSTAGRAM_API_ERROR") -> None:
        super().__init__(message, code=code, transient=False, status_code=502)


class InstagramTransientError(ExternalAPIException):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="INSTAGRAM_TEMPORARY_ERROR", transient=True, status_code=503)


class InstagramRateLimitError(RateLimitException):
    def __init__(self, message: str = "Instagram rate limit reached", *, retry_after: float | None = None) -> None:
        super().__init__(message, code="INSTAGRAM_RATE_LIMITED")
        self.retry_after = retry_after
