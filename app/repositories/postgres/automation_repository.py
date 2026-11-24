"""PostgreSQL implementation of AutomationRepository."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain.automation import (
    Action,
    Automation,
    AutomationStatus,
    Trigger,
)
from app.models.orm.automation import AutomationModel
from app.repositories.exceptions import DuplicateRecordError, RecordNotFoundError
from app.repositories.interfaces.automation_repository import AutomationRepository


def _to_domain(row: AutomationModel) -> Automation:
    # Deserialise JSONB → typed Pydantic discriminated unions
    from pydantic import TypeAdapter

    trigger_adapter: TypeAdapter[Trigger] = TypeAdapter(Trigger)
    action_adapter: TypeAdapter[Action] = TypeAdapter(Action)

    trigger = trigger_adapter.validate_python(row.trigger)
    actions = [action_adapter.validate_python(a) for a in row.actions]

    return Automation(
        id=row.id,
        workspace_id=row.workspace_id,
        instagram_account_id=row.instagram_account_id,
        name=row.name,
        description=row.description,
        status=AutomationStatus(row.status),
        trigger=trigger,
        actions=actions,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _to_orm(automation: Automation) -> AutomationModel:
    return AutomationModel(
        id=automation.id,
        workspace_id=automation.workspace_id,
        instagram_account_id=automation.instagram_account_id,
        name=automation.name,
        description=automation.description,
        status=automation.status.value,
        trigger=automation.trigger.model_dump(mode="json"),
        actions=[a.model_dump(mode="json") for a in automation.actions],
        created_at=automation.created_at,
        updated_at=automation.updated_at,
    )


class PostgresAutomationRepository(AutomationRepository):
    """SQLAlchemy async implementation of :class:`AutomationRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, automation: Automation) -> Automation:
        row = _to_orm(automation)
        self._session.add(row)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise DuplicateRecordError("automation") from exc
        await self._session.refresh(row)
        return _to_domain(row)

    async def get_by_id(self, automation_id: str) -> Automation | None:
        row = await self._session.get(AutomationModel, automation_id)
        return _to_domain(row) if row else None

    async def list_by_workspace(
        self,
        workspace_id: str,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Automation], int]:
        base_q = select(AutomationModel).where(
            AutomationModel.workspace_id == workspace_id
        )
        count_result = await self._session.execute(
            select(func.count()).select_from(base_q.subquery())
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            base_q.order_by(AutomationModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = result.scalars().all()
        return [_to_domain(r) for r in rows], total

    async def list_active_for_account(
        self,
        workspace_id: str,
        instagram_account_id: str,
    ) -> list[Automation]:
        result = await self._session.execute(
            select(AutomationModel).where(
                AutomationModel.workspace_id == workspace_id,
                AutomationModel.instagram_account_id == instagram_account_id,
                AutomationModel.status == AutomationStatus.ACTIVE.value,
            )
        )
        return [_to_domain(r) for r in result.scalars().all()]

    async def update(self, automation: Automation) -> Automation:
        row = await self._session.get(AutomationModel, automation.id)
        if row is None:
            raise RecordNotFoundError(automation.id)
        row.name = automation.name
        row.description = automation.description
        row.status = automation.status.value
        row.trigger = automation.trigger.model_dump(mode="json")
        row.actions = [a.model_dump(mode="json") for a in automation.actions]
        row.updated_at = automation.updated_at
        await self._session.flush()
        await self._session.refresh(row)
        return _to_domain(row)

    async def delete(self, workspace_id: str, automation_id: str) -> bool:
        row = await self._session.get(AutomationModel, automation_id)
        if row is None or row.workspace_id != workspace_id:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True
