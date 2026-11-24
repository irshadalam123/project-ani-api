"""FastAPI application factory."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.router import build_api_router
from app.core.config import Settings, get_settings, validate_settings
from app.core.container import build_container, set_container
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestIdMiddleware, SecurityHeadersMiddleware

logger = get_logger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime = settings or get_settings()
    validate_settings(runtime)
    configure_logging(runtime)
    container = build_container(runtime)
    set_container(container)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if runtime.seed_demo_data:
            from scripts.seed_demo_data import seed

            summary = await seed(container)
            logger.info("demo_data_seeded", users=summary["users"], automations=summary["automations"])
        logger.info(
            "application_started",
            app_env=runtime.app_env,
            mock_external_services=runtime.mock_external_services,
            task_execution_mode=runtime.task_execution_mode,
        )
        yield
        await container.redis.close()
        await container.instagram.aclose()

    app = FastAPI(
        title=runtime.app_name,
        version="0.1.0",
        description=(
            "Instagram comment-to-DM automation API. "
            "Business data is in-memory until PostgreSQL repositories are connected."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    app.state.settings = runtime
    app.state.container = container

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)
    if runtime.trusted_host_list:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=runtime.trusted_host_list)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=runtime.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Workspace-Id", "X-Request-ID", "X-Hub-Signature-256"],
    )
    register_exception_handlers(app)
    app.include_router(build_api_router(runtime))
    return app


app = create_app()
