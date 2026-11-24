"""ORM mapping for the Execution domain model.

``action_results`` is a ``list[ActionResult]`` stored as JSONB.
Repositories must serialise/deserialise it using the domain model.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.orm.base import Base


class ExecutionModel(Base):
    """Maps to the ``executions`` table."""

    __tablename__ = "executions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    instagram_account_id: Mapped[str] = mapped_column(
        String, nullable=False, index=True
    )
    automation_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("automations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    webhook_event_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("webhook_events.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )
    comment_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # Stores ExecutionStatus enum value
    status: Mapped[str] = mapped_column(String, nullable=False, default="PENDING", index=True)
    # list[ActionResult] serialised as JSONB
    action_results: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    automation: Mapped["AutomationModel"] = relationship(  # type: ignore[name-defined]
        "AutomationModel", back_populates="executions"
    )
    webhook_event: Mapped["WebhookEventModel"] = relationship(  # type: ignore[name-defined]
        "WebhookEventModel", back_populates="executions"
    )
