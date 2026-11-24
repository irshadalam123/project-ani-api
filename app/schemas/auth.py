"""Authentication schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=200)
    workspace_name: str | None = Field(default=None, max_length=200)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "owner@example.com",
                    "password": "a-strong-password",
                    "full_name": "Avery Owner",
                    "workspace_name": "Avery Studio",
                }
            ]
        }
    }


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    model_config = {
        "json_schema_extra": {
            "examples": [{"email": "owner@example.com", "password": "a-strong-password"}]
        }
    }


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class WorkspaceCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class WorkspacePublic(BaseModel):
    id: str
    name: str
    owner_id: str
    created_at: datetime
    updated_at: datetime


class AuthData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublic
    workspace: WorkspacePublic


class AuthResponse(BaseModel):
    success: bool = True
    data: AuthData


class MeResponse(BaseModel):
    success: bool = True
    data: UserPublic
