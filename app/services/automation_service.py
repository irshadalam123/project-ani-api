"""Create and manage workspace automations."""

from __future__ import annotations

import re

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.domain.automation import (
    Action,
    Automation,
    AutomationStatus,
    KeywordTrigger,
    MatchType,
    Trigger,
)
from app.repositories.interfaces.automation_repository import AutomationRepository
from app.repositories.interfaces.instagram_repository import InstagramRepository
from app.utils.datetime import utcnow
from app.utils.ids import new_id

_MAX_REGEX = 200


class AutomationService:
    def __init__(self, automations: AutomationRepository, accounts: InstagramRepository) -> None:
        self._automations = automations
        self._accounts = accounts

    async def create(
        self,
        workspace_id: str,
        *,
        name: str,
        description: str | None,
        instagram_account_id: str,
        trigger: Trigger,
        actions: list[Action],
        status: AutomationStatus = AutomationStatus.DRAFT,
    ) -> Automation:
        await self._require_account(workspace_id, instagram_account_id)
        self._validate_trigger(trigger)
        if status == AutomationStatus.ARCHIVED:
            raise ValidationException("Create the automation before archiving it")
        now = utcnow()
        automation = Automation(
            id=new_id(),
            workspace_id=workspace_id,
            instagram_account_id=instagram_account_id,
            name=name.strip(),
            description=description,
            status=status,
            trigger=trigger,
            actions=actions,
            created_at=now,
            updated_at=now,
        )
        return await self._automations.add(automation)

    async def list_automations(
        self, workspace_id: str, *, page: int, page_size: int
    ) -> tuple[list[Automation], int]:
        return await self._automations.list_by_workspace(workspace_id, page=page, page_size=page_size)

    async def get(self, workspace_id: str, automation_id: str) -> Automation:
        return await self._require(workspace_id, automation_id)

    async def update(
        self,
        workspace_id: str,
        automation_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        trigger: Trigger | None = None,
        actions: list[Action] | None = None,
        instagram_account_id: str | None = None,
        description_set: bool = False,
    ) -> Automation:
        automation = await self._require(workspace_id, automation_id)
        if instagram_account_id is not None:
            await self._require_account(workspace_id, instagram_account_id)
            automation.instagram_account_id = instagram_account_id
        if name is not None:
            automation.name = name.strip()
        if description_set:
            automation.description = description
        if trigger is not None:
            self._validate_trigger(trigger)
            automation.trigger = trigger
        if actions is not None:
            automation.actions = actions
        automation.updated_at = utcnow()
        return await self._automations.update(automation)

    async def delete(self, workspace_id: str, automation_id: str) -> None:
        deleted = await self._automations.delete(workspace_id, automation_id)
        if not deleted:
            raise NotFoundException("Automation not found", code="AUTOMATION_NOT_FOUND")

    async def activate(self, workspace_id: str, automation_id: str) -> Automation:
        automation = await self._require(workspace_id, automation_id)
        if automation.status == AutomationStatus.ARCHIVED:
            raise ConflictException("Archived automations cannot be activated", code="AUTOMATION_ARCHIVED")
        automation.status = AutomationStatus.ACTIVE
        automation.updated_at = utcnow()
        return await self._automations.update(automation)

    async def pause(self, workspace_id: str, automation_id: str) -> Automation:
        automation = await self._require(workspace_id, automation_id)
        if automation.status != AutomationStatus.ACTIVE:
            raise ConflictException("Only an active automation can be paused", code="AUTOMATION_NOT_ACTIVE")
        automation.status = AutomationStatus.PAUSED
        automation.updated_at = utcnow()
        return await self._automations.update(automation)

    async def _require(self, workspace_id: str, automation_id: str) -> Automation:
        automation = await self._automations.get_by_id(automation_id)
        if automation is None or automation.workspace_id != workspace_id:
            raise NotFoundException("Automation not found", code="AUTOMATION_NOT_FOUND")
        return automation

    async def _require_account(self, workspace_id: str, account_id: str) -> None:
        account = await self._accounts.get_by_id(account_id)
        if account is None or account.workspace_id != workspace_id:
            raise NotFoundException("Instagram account not found", code="INSTAGRAM_ACCOUNT_NOT_FOUND")

    def _validate_trigger(self, trigger: Trigger) -> None:
        if isinstance(trigger, KeywordTrigger):
            cleaned = [keyword.strip() for keyword in trigger.keywords if keyword.strip()]
            if not cleaned:
                raise ValidationException("At least one keyword is required", code="INVALID_TRIGGER")
            trigger.keywords = cleaned
            if trigger.match_type == MatchType.REGEX:
                for pattern in cleaned:
                    if len(pattern) > _MAX_REGEX:
                        raise ValidationException("Regex patterns must be 200 characters or fewer")
                    try:
                        re.compile(pattern)
                    except re.error as exc:
                        raise ValidationException(f"Invalid regex: {exc}") from exc
