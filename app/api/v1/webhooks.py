"""Instagram webhook verification and intake.

The route returns as soon as the event is stored and queued.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from fastapi.responses import PlainTextResponse

from app.core.dependencies import get_webhook_service, rate_limit
from app.schemas.webhook import WebhookIngestData, WebhookIngestResponse
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get("/instagram", summary="Meta webhook verification", response_class=PlainTextResponse)
async def verify_instagram_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
    service: WebhookService = Depends(get_webhook_service),
) -> PlainTextResponse:
    challenge = service.verify(hub_mode, hub_verify_token, hub_challenge)
    return PlainTextResponse(content=challenge)


@router.post(
    "/instagram",
    response_model=WebhookIngestResponse,
    summary="Receive Instagram webhook events",
    dependencies=[Depends(rate_limit("webhook"))],
)
async def receive_instagram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    service: WebhookService = Depends(get_webhook_service),
) -> WebhookIngestResponse:
    body = await request.body()
    signature = request.headers.get("x-hub-signature-256")
    result = await service.ingest(body, signature, background_tasks)
    return WebhookIngestResponse(
        data=WebhookIngestData(
            accepted=result.accepted,
            event_ids=result.event_ids,
            duplicate_event_ids=result.duplicate_event_ids,
        )
    )
