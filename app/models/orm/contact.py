"""ORM mapping for the Contact domain model."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.orm.base import Base


class ContactModel(Base):
    """Maps to the ``contacts`` table."""

    __tablename__ = "contacts"

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
    instagram_user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    first_name: Mapped[str | None] = mapped_column(String, nullable=True)
    last_name: Mapped[str | None] = mapped_column(String, nullable=True)
    # dict[str, str] stored as JSONB for flexible metadata fields
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
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
    instagram_account: Mapped["InstagramAccountModel"] = relationship(  # type: ignore[name-defined]
        "InstagramAccountModel", back_populates="contacts"
    )
    conversations: Mapped[list["ConversationModel"]] = relationship(  # type: ignore[name-defined]
        "ConversationModel", back_populates="contact"
    )
