"""Workspace (tenant) model."""

from datetime import datetime

from pydantic import BaseModel


class Workspace(BaseModel):
    id: str
    name: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
