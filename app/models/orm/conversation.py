"""ORM mapping for the Conversation domain model."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.orm.base import Base


class ConversationModel(Base):
    """Maps to the ``conversations`` table."""

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    instagram_account_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("instagram_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contact_id: Mapped[str] = mapped_column(
        String, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Stores ConversationStatus enum value, e.g. "OPEN" / "CLOSED"
    status: Mapped[str] = mapped_column(String, nullable=False, default="OPEN")
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
    instagram_account: Mapped["InstagramAccountModel"] = relationship(  # type: ignore[name-defined]
        "InstagramAccountModel", back_populates="conversations"
    )
    contact: Mapped["ContactModel"] = relationship(  # type: ignore[name-defined]
        "ContactModel", back_populates="conversations"
    )
    messages: Mapped[list["MessageModel"]] = relationship(  # type: ignore[name-defined]
        "MessageModel", back_populates="conversation", cascade="all, delete-orphan"
    )
