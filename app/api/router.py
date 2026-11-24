"""Top-level router.

Health and webhooks stay outside ``/api/v1``. Product routes are versioned.
"""

from fastapi import APIRouter

from app.api.v1 import health, webhooks
from app.api.v1.router import router as v1_router
from app.core.config import Settings


def build_api_router(settings: Settings) -> APIRouter:
    root = APIRouter()
    root.include_router(health.router)
    root.include_router(webhooks.router)
    root.include_router(v1_router, prefix=settings.api_v1_prefix)
    return root
