"""Versioned API router."""

from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    auth,
    automations,
    contacts,
    conversations,
    executions,
    instagram,
    workspaces,
)

router = APIRouter()
router.include_router(auth.router)
router.include_router(workspaces.router)
router.include_router(instagram.router)
router.include_router(automations.router)
router.include_router(contacts.router)
router.include_router(conversations.router)
router.include_router(executions.router)
router.include_router(analytics.router)
