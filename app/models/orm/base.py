"""Shared declarative base and registry used by all ORM models."""

from sqlalchemy.orm import DeclarativeBase, registry


class Base(DeclarativeBase):
    """Common declarative base.

    All ORM models must inherit from this class so that
    ``Base.metadata`` contains every table for Alembic migrations.
    """


#: Convenience alias – repositories can use either ``Base`` or this.
mapper_registry: registry = Base.registry
