"""Process-local repositories.

These stores are not shared across API and Celery worker processes. Replace
them with PostgreSQL repositories before relying on a separate worker.
"""
