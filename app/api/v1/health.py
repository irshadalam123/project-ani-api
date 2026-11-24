"""Liveness and readiness."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
async def health() -> dict[str, str]:
    """The process is running. This check does not call Redis or a database."""
    return {"status": "ok"}


@router.get("/health/ready", summary="Readiness probe")
async def readiness(request: Request) -> JSONResponse:
    """Report application and Redis health. Database is not checked yet."""
    redis_ok = await request.app.state.container.redis.ping()
    checks = {"application": "ok", "redis": "ok" if redis_ok else "unavailable"}
    status = "ok" if redis_ok else "unavailable"
    return JSONResponse(
        status_code=200 if redis_ok else 503,
        content={"status": status, "checks": checks},
    )
