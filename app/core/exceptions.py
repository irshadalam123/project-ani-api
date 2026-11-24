"""Application exceptions mapped to a consistent API error envelope."""

from __future__ import annotations


class AppException(Exception):
    """Base error that API handlers know how to serialize."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        *,
        transient: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.transient = transient


class ValidationException(AppException):
    def __init__(self, message: str, code: str = "VALIDATION_ERROR") -> None:
        super().__init__(code=code, message=message, status_code=422)


class AuthenticationException(AppException):
    def __init__(self, message: str = "Authentication required", code: str = "NOT_AUTHENTICATED") -> None:
        super().__init__(code=code, message=message, status_code=401)


class AuthorizationException(AppException):
    def __init__(self, message: str = "You do not have access to this workspace", code: str = "FORBIDDEN") -> None:
        super().__init__(code=code, message=message, status_code=403)


class NotFoundException(AppException):
    def __init__(self, message: str, code: str = "NOT_FOUND") -> None:
        super().__init__(code=code, message=message, status_code=404)


class ConflictException(AppException):
    def __init__(self, message: str, code: str = "CONFLICT") -> None:
        super().__init__(code=code, message=message, status_code=409)


class ExternalAPIException(AppException):
    def __init__(
        self,
        message: str,
        code: str = "EXTERNAL_API_ERROR",
        *,
        transient: bool = False,
        status_code: int = 502,
    ) -> None:
        super().__init__(code=code, message=message, status_code=status_code, transient=transient)


class RateLimitException(AppException):
    def __init__(self, message: str = "Too many requests", code: str = "RATE_LIMITED") -> None:
        super().__init__(code=code, message=message, status_code=429, transient=True)


class WebhookVerificationException(AppException):
    def __init__(self, message: str = "Webhook verification failed", code: str = "WEBHOOK_VERIFICATION_FAILED") -> None:
        super().__init__(code=code, message=message, status_code=403)
