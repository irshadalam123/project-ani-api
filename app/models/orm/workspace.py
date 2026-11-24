"""ORM mapping for the Workspace domain model."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.orm.base import Base


class WorkspaceModel(Base):
    """Maps to the ``workspaces`` table."""

    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    owner_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    members: Mapped[list["WorkspaceMemberModel"]] = relationship(  # type: ignore[name-defined]
        "WorkspaceMemberModel", back_populates="workspace", cascade="all, delete-orphan"
    )
    instagram_accounts: Mapped[list["InstagramAccountModel"]] = relationship(  # type: ignore[name-defined]
        "InstagramAccountModel", back_populates="workspace", cascade="all, delete-orphan"
    )
    automations: Mapped[list["AutomationModel"]] = relationship(  # type: ignore[name-defined]
        "AutomationModel", back_populates="workspace", cascade="all, delete-orphan"
    )
