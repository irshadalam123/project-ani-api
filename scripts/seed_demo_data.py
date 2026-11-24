"""Load demonstration records into the in-memory repositories.

The data lives only in the process that calls ``seed``. Start the API with
``SEED_DEMO_DATA=true`` to load it into the running server. Running this file
directly seeds a throwaway container and prints the ids.
"""

from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.core.container import AppContainer, build_container
from app.core.security import hash_password
from app.integrations.instagram.types import StoredToken
from app.models.domain.automation import (
    AnyCommentTrigger,
    Automation,
    AutomationStatus,
    KeywordTrigger,
    MatchType,
    PrivateReplyAction,
    PublicReplyAction,
)
from app.models.domain.contact import Contact
from app.models.domain.conversation import Conversation, ConversationStatus
from app.models.domain.instagram_account import InstagramAccount
from app.models.domain.message import Message, MessageDirection, MessageType
from app.models.domain.user import User, WorkspaceMember, WorkspaceRole
from app.models.domain.workspace import Workspace
from app.utils.datetime import utcnow


async def seed(container: AppContainer) -> dict[str, int]:
    now = utcnow()
    user = User(
        id="00000000-0000-4000-8000-000000000001",
        email="demo@example.com",
        password_hash=hash_password("DemoPassword123!"),
        full_name="Demo Owner",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    existing = await container.users.get_by_email(user.email)
    if existing is not None:
        return {"users": 1, "workspaces": 1, "instagram_accounts": 1, "automations": 2, "contacts": 3}
    await container.users.add(user)
    workspace = Workspace(
        id="00000000-0000-4000-8000-000000000010",
        name="Demo Workspace",
        owner_id=user.id,
        created_at=now,
        updated_at=now,
    )
    await container.workspaces.add(workspace)
    await container.workspaces.add_member(
        WorkspaceMember(
            id="00000000-0000-4000-8000-000000000011",
            workspace_id=workspace.id,
            user_id=user.id,
            role=WorkspaceRole.OWNER,
            created_at=now,
        )
    )
    account = InstagramAccount(
        id="00000000-0000-4000-8000-000000000020",
        workspace_id=workspace.id,
        instagram_user_id="mock-ig-user-demo",
        username="demo_brand",
        name="Demo Brand",
        account_type="BUSINESS",
        webhook_subscribed=True,
        scopes=["instagram_business_basic", "instagram_business_manage_comments"],
        connected_at=now,
        created_at=now,
        updated_at=now,
    )
    await container.instagram_accounts.add(account)
    await container.tokens.store_token(account.id, StoredToken(access_token="mock-long-lived-token", expires_in=5184000))
    roadmap = Automation(
        id="00000000-0000-4000-8000-000000000030",
        workspace_id=workspace.id,
        instagram_account_id=account.id,
        name="AI Roadmap",
        description="Reply when a comment mentions the guide",
        status=AutomationStatus.ACTIVE,
        trigger=KeywordTrigger(keywords=["guide", "ai guide"], match_type=MatchType.CONTAINS),
        actions=[
            PublicReplyAction(text="I've sent you a DM 🚀"),
            PrivateReplyAction(text="Hey {{first_name}}, here's your AI roadmap!"),
        ],
        created_at=now,
        updated_at=now,
    )
    welcome = Automation(
        id="00000000-0000-4000-8000-000000000031",
        workspace_id=workspace.id,
        instagram_account_id=account.id,
        name="Welcome",
        description="Draft reply for every comment",
        status=AutomationStatus.DRAFT,
        trigger=AnyCommentTrigger(),
        actions=[PublicReplyAction(text="Thanks for commenting!")],
        created_at=now,
        updated_at=now,
    )
    await container.automations.add(roadmap)
    await container.automations.add(welcome)
    contacts: list[Contact] = []
    for index, (ig_id, username, first_name) in enumerate(
        (
            ("ig_user_alpha", "alpha", "Ava"),
            ("ig_user_bravo", "bravo", "Ben"),
            ("ig_user_casey", "casey", "Casey"),
        ),
        start=1,
    ):
        contact = Contact(
            id=f"00000000-0000-4000-8000-00000000004{index}",
            workspace_id=workspace.id,
            instagram_account_id=account.id,
            instagram_user_id=ig_id,
            username=username,
            first_name=first_name,
            created_at=now,
            updated_at=now,
        )
        await container.contacts.add(contact)
        contacts.append(contact)
    conversation = Conversation(
        id="00000000-0000-4000-8000-000000000050",
        workspace_id=workspace.id,
        instagram_account_id=account.id,
        contact_id=contacts[0].id,
        status=ConversationStatus.OPEN,
        created_at=now,
        updated_at=now,
    )
    await container.conversations.add(conversation)
    await container.conversations.add_message(
        Message(
            id="00000000-0000-4000-8000-000000000060",
            conversation_id=conversation.id,
            workspace_id=workspace.id,
            direction=MessageDirection.INBOUND,
            message_type=MessageType.TEXT,
            text="Can I get the guide?",
            external_message_id="mock_inbound_1",
            created_at=now,
        )
    )
    await container.conversations.add_message(
        Message(
            id="00000000-0000-4000-8000-000000000061",
            conversation_id=conversation.id,
            workspace_id=workspace.id,
            direction=MessageDirection.OUTBOUND,
            message_type=MessageType.TEXT,
            text="Hey Ava, here's your AI roadmap!",
            external_message_id="mock_message_demo",
            created_at=now,
        )
    )
    return {
        "users": 1,
        "workspaces": 1,
        "instagram_accounts": 1,
        "automations": 2,
        "contacts": 3,
        "conversations": 1,
        "messages": 2,
    }


def main() -> None:
    container = build_container(get_settings())
    summary = asyncio.run(seed(container))
    print("Seeded in-memory demo data for this process only:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print("Login: demo@example.com / DemoPassword123!")
    print("Start the API with SEED_DEMO_DATA=true to load the same records into the server.")


if __name__ == "__main__":
    main()
