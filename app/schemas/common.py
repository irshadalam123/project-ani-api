"""Shared response envelopes and pagination."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class Pagination(BaseModel):
    page: int
    page_size: int
    total: int


class APIErrorBody(BaseModel):
    code: str
    message: str
    request_id: str | None = None


class APIErrorResponse(BaseModel):
    success: bool = False
    error: APIErrorBody


class APISuccess(BaseModel, Generic[T]):
    success: bool = True
    data: T


class APIList(BaseModel, Generic[T]):
    success: bool = True
    data: list[T]
    pagination: Pagination
