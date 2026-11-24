"""PostgreSQL implementation of ExecutionRepository."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain.execution import (
    ActionResult,
    ActionResultStatus,
    Execution,
    ExecutionStatus,
)
from app.models.orm.execution import ExecutionModel
from app.repositories.exceptions import DuplicateRecordError, RecordNotFoundError
from app.repositories.interfaces.execution_repository import ExecutionRepository
from app.utils.datetime import utcnow


def _to_domain(row: ExecutionModel) -> Execution:
    from pydantic import TypeAdapter

    ar_adapter: TypeAdapter[ActionResult] = TypeAdapter(ActionResult)
    action_results = [ar_adapter.validate_python(ar) for ar in row.action_results]

    return Execution(
        id=row.id,
        workspace_id=row.workspace_id,
        instagram_account_id=row.instagram_account_id,
        automation_id=row.automation_id,
        webhook_event_id=row.webhook_event_id,
        comment_id=row.comment_id,
        status=ExecutionStatus(row.status),
        action_results=action_results,
        error=row.error,
        created_at=row.created_at,
        updated_at=row.updated_at,
        completed_at=row.completed_at,
    )


def _to_orm(execution: Execution) -> ExecutionModel:
    return ExecutionModel(
        id=execution.id,
        workspace_id=execution.workspace_id,
        instagram_account_id=execution.instagram_account_id,
        automation_id=execution.automation_id,
        webhook_event_id=execution.webhook_event_id,
        comment_id=execution.comment_id,
        status=execution.status.value,
        action_results=[ar.model_dump(mode="json") for ar in execution.action_results],
        error=execution.error,
        created_at=execution.created_at,
        updated_at=execution.updated_at,
        completed_at=execution.completed_at,
    )


class PostgresExecutionRepository(ExecutionRepository):
    """SQLAlchemy async implementation of :class:`ExecutionRepository`.

    ``create_if_absent`` uses a ``SELECT … FOR UPDATE`` optimistic lock so
    that concurrent inserts for the same (automation_id, comment_id) pair
    are handled at the database level.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_if_absent(self, execution: Execution) -> tuple[Execution, bool]:
        # Try to find an existing record first (SELECT FOR UPDATE to serialise)
        result = await self._session.execute(
            select(ExecutionModel)
            .where(
                ExecutionModel.automation_id == execution.automation_id,
                ExecutionModel.comment_id == execution.comment_id,
            )
            .with_for_update()
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            return _to_domain(existing), False

        row = _to_orm(execution)
        self._session.add(row)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise DuplicateRecordError("execution") from exc
        await self._session.refresh(row)
        return _to_domain(row), True

    async def get_by_id(self, execution_id: str) -> Execution | None:
        row = await self._session.get(ExecutionModel, execution_id)
        return _to_domain(row) if row else None

    async def get_by_automation_and_comment(
        self,
        automation_id: str,
        comment_id: str,
    ) -> Execution | None:
        result = await self._session.execute(
            select(ExecutionModel).where(
                ExecutionModel.automation_id == automation_id,
                ExecutionModel.comment_id == comment_id,
            )
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def save_action_result(
        self, execution_id: str, result: ActionResult
    ) -> Execution:
        row = await self._session.get(ExecutionModel, execution_id)
        if row is None:
            raise RecordNotFoundError(execution_id)

        # Rebuild the action_results list, replacing or appending
        updated: list[dict] = []
        replaced = False
        for ar in row.action_results:
            if ar.get("action_index") == result.action_index:
                updated.append(result.model_dump(mode="json"))
                replaced = True
            else:
                updated.append(ar)
        if not replaced:
            updated.append(result.model_dump(mode="json"))
        updated.sort(key=lambda x: x["action_index"])

        # Derive new overall status from individual results
        statuses = [ar["status"] for ar in updated]
        if any(s == ActionResultStatus.PENDING for s in statuses):
            new_status = ExecutionStatus.RUNNING
            completed_at = None
        elif any(s == ActionResultStatus.FAILED for s in statuses):
            new_status = ExecutionStatus.FAILED
            completed_at = utcnow()
        else:
            new_status = ExecutionStatus.SUCCEEDED
            completed_at = utcnow()

        row.action_results = updated
        row.status = new_status.value
        row.updated_at = utcnow()
        row.completed_at = completed_at

        await self._session.flush()
        await self._session.refresh(row)
        return _to_domain(row)

    async def update(self, execution: Execution) -> Execution:
        row = await self._session.get(ExecutionModel, execution.id)
        if row is None:
            raise RecordNotFoundError(execution.id)
        row.status = execution.status.value
        row.action_results = [ar.model_dump(mode="json") for ar in execution.action_results]
        row.error = execution.error
        row.updated_at = execution.updated_at
        row.completed_at = execution.completed_at
        await self._session.flush()
        await self._session.refresh(row)
        return _to_domain(row)

    async def list_by_workspace(
        self,
        workspace_id: str,
        *,
        page: int,
        page_size: int,
        automation_id: str | None = None,
    ) -> tuple[list[Execution], int]:
        base_q = select(ExecutionModel).where(
            ExecutionModel.workspace_id == workspace_id
        )
        if automation_id is not None:
            base_q = base_q.where(ExecutionModel.automation_id == automation_id)

        count_result = await self._session.execute(
            select(func.count()).select_from(base_q.subquery())
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            base_q.order_by(ExecutionModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [_to_domain(r) for r in result.scalars().all()], total

    async def list_for_event(self, webhook_event_id: str) -> list[Execution]:
        result = await self._session.execute(
            select(ExecutionModel).where(
                ExecutionModel.webhook_event_id == webhook_event_id
            )
        )
        return [_to_domain(r) for r in result.scalars().all()]
