"""ORM mapping for the WebhookEvent domain model."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.orm.base import Base


class WebhookEventModel(Base):
    """Maps to the ``webhook_events`` table."""

    __tablename__ = "webhook_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    external_event_id: Mapped[str] = mapped_column(
        String, nullable=False, unique=True, index=True
    )
    # Stores WebhookEventType enum value: "COMMENT" / "LIVE_COMMENT" / "UNKNOWN"
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    workspace_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    instagram_account_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    # Raw webhook payload stored as JSONB
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # Stores WebhookEventStatus enum value
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="RECEIVED", index=True
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    executions: Mapped[list["ExecutionModel"]] = relationship(  # type: ignore[name-defined]
        "ExecutionModel", back_populates="webhook_event"
    )
