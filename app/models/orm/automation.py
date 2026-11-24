"""ORM mapping for the Automation domain model.

The polymorphic ``trigger`` and ``actions`` fields are stored as JSONB so
that the ORM layer remains simple and schema-less for these nested structures.
Repositories translate them to/from the typed Pydantic models.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.orm.base import Base


class AutomationModel(Base):
    """Maps to the ``automations`` table."""

    __tablename__ = "automations"

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
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    # Stores AutomationStatus enum value: "DRAFT" / "ACTIVE" / "PAUSED" / "ARCHIVED"
    status: Mapped[str] = mapped_column(String, nullable=False, default="DRAFT", index=True)
    # Discriminated union (KeywordTrigger | AnyCommentTrigger) serialised as JSONB
    trigger: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # list[PublicReplyAction | PrivateReplyAction] serialised as JSONB
    actions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
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
        "WorkspaceModel", back_populates="automations"
    )
    instagram_account: Mapped["InstagramAccountModel"] = relationship(  # type: ignore[name-defined]
        "InstagramAccountModel", back_populates="automations"
    )
    executions: Mapped[list["ExecutionModel"]] = relationship(  # type: ignore[name-defined]
        "ExecutionModel", back_populates="automation", cascade="all, delete-orphan"
    )
