"""ORM mapping for the Message domain model."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.orm.base import Base


class MessageModel(Base):
    """Maps to the ``messages`` table."""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[str] = mapped_column(
        String, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Stores MessageDirection enum value: "INBOUND" / "OUTBOUND"
    direction: Mapped[str] = mapped_column(String, nullable=False)
    # Stores MessageType enum value: "TEXT" / "BUTTON" / "SYSTEM"
    message_type: Mapped[str] = mapped_column(String, nullable=False, default="TEXT")
    text: Mapped[str] = mapped_column(Text, nullable=False)
    external_message_id: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    conversation: Mapped["ConversationModel"] = relationship(  # type: ignore[name-defined]
        "ConversationModel", back_populates="messages"
    )
