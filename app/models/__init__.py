"""Domain models.

These Pydantic models are the application's persistence-agnostic records.
SQLAlchemy ORM mappings live under ``app/models/orm`` and are translated
at the repository boundary. Do not import ORM types into services or routes.
"""
