"""ORM mapping for the InstagramAccount domain model."""

from datetime import datetime

from sqlalchemy import ARRAY, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.orm.base import Base


class InstagramAccountModel(Base):
    """Maps to the ``instagram_accounts`` table."""

    __tablename__ = "instagram_accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    instagram_user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    account_type: Mapped[str | None] = mapped_column(String, nullable=True)
    profile_picture_url: Mapped[str | None] = mapped_column(String, nullable=True)
    webhook_subscribed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # PostgreSQL native array; stores list[str] (OAuth scopes)
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
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
    workspace: Mapped["WorkspaceModel"] = relationship(  # type: ignore[name-defined]
        "WorkspaceModel", back_populates="instagram_accounts"
    )
    contacts: Mapped[list["ContactModel"]] = relationship(  # type: ignore[name-defined]
        "ContactModel", back_populates="instagram_account", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["ConversationModel"]] = relationship(  # type: ignore[name-defined]
        "ConversationModel", back_populates="instagram_account", cascade="all, delete-orphan"
    )
    automations: Mapped[list["AutomationModel"]] = relationship(  # type: ignore[name-defined]
        "AutomationModel", back_populates="instagram_account", cascade="all, delete-orphan"
    )
