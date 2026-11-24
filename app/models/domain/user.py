"""User account."""

from datetime import datetime

from pydantic import BaseModel, Field


class User(BaseModel):
    id: str
    email: str
    password_hash: str
    full_name: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    def public_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class WorkspaceRole(str):
    """Membership role stored as a plain string for simple persistence."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class WorkspaceMember(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    role: str = Field(default=WorkspaceRole.MEMBER)
    created_at: datetime
