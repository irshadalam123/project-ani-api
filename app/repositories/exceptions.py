"""Persistence errors that are independent of HTTP.

Services translate these into ``AppException`` values. A future PostgreSQL
repository can raise the same errors for unique-constraint violations.
"""


class DuplicateRecordError(Exception):
    """Raised when a unique key already exists."""


class RecordNotFoundError(Exception):
    """Raised when an update targets a missing record."""
