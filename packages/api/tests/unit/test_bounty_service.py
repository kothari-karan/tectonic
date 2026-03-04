import uuid
from datetime import datetime, timezone, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import AgentType
from app.models.bounty import EngagementStatus
from app.schemas.bounty import EngagementCreate, EngagementUpdate
from app.services.bounty_service import (
    create_engagement,
    get_engagement,
    list_engagements,
    update_engagement_status,
)
from tests.conftest import create_test_agent, create_test_engagement


class TestCreateEngagement:
    @pytest.mark.asyncio
    async def test_create_engagement_success(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="bs-requester1")
        data = EngagementCreate(
            title="Test Engagement",
            description="Description for test",
            acceptance_criteria=["c1", "c2"],
            category="ai",
            reward_amount=2.5,
            deadline=datetime.now(timezone.utc) + timedelta(days=7),
        )
        engagement = await create_engagement(data, requester, db_session)

        assert engagement.title == "Test Engagement"
        assert engagement.requester_id == requester.id
        assert engagement.status == EngagementStatus.open
        assert engagement.reward_token == "ETH"
        assert engagement.reward_amount == 2.5

    @pytest.mark.asyncio
    async def test_create_engagement_increments_posted_count(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="bs-requester2")
        assert requester.engagements_posted == 0

        data = EngagementCreate(
            title="Engagement 1",
            description="Description",
            acceptance_criteria=["c1"],
            category="web3",
            reward_amount=1.0,
            deadline=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await create_engagement(data, requester, db_session)
        await db_session.refresh(requester)
        assert requester.engagements_posted == 1


class TestGetEngagement:
    @pytest.mark.asyncio
    async def test_get_existing_engagement(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="bs-requester3")
        engagement = await create_test_engagement(db_session, requester, title="Findable Engagement")

        found = await get_engagement(engagement.id, db_session)
        assert found.id == engagement.id
        assert found.title == "Findable Engagement"

    @pytest.mark.asyncio
    async def test_get_nonexistent_engagement_raises_404(self, db_session: AsyncSession):
        with pytest.raises(HTTPException) as exc_info:
            await get_engagement(uuid.uuid4(), db_session)
        assert exc_info.value.status_code == 404


class TestListEngagements:
    @pytest.mark.asyncio
    async def test_list_all_engagements(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="bs-requester4")
        await create_test_engagement(db_session, requester, title="E1")
        await create_test_engagement(db_session, requester, title="E2")

        engagements, total = await list_engagements(db_session)
        assert total == 2
        assert len(engagements) == 2

    @pytest.mark.asyncio
    async def test_list_engagements_filter_by_status(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="bs-requester5")
        await create_test_engagement(db_session, requester, title="Open E", status=EngagementStatus.open)
        await create_test_engagement(
            db_session, requester, title="Cancelled E", status=EngagementStatus.cancelled
        )

        engagements, total = await list_engagements(
            db_session, status_filter=EngagementStatus.open
        )
        assert total == 1
        assert engagements[0].title == "Open E"

    @pytest.mark.asyncio
    async def test_list_engagements_filter_by_category(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="bs-requester6")
        await create_test_engagement(db_session, requester, title="AI Engagement", category="ai")
        await create_test_engagement(db_session, requester, title="Web3 Engagement", category="web3")

        engagements, total = await list_engagements(db_session, category="ai")
        assert total == 1
        assert engagements[0].category == "ai"

    @pytest.mark.asyncio
    async def test_list_engagements_filter_by_requester(self, db_session: AsyncSession):
        requester1, _ = await create_test_agent(db_session, name="bs-requester7a")
        requester2, _ = await create_test_agent(db_session, name="bs-requester7b")
        await create_test_engagement(db_session, requester1, title="R1 Engagement")
        await create_test_engagement(db_session, requester2, title="R2 Engagement")

        engagements, total = await list_engagements(db_session, requester_id=requester1.id)
        assert total == 1

    @pytest.mark.asyncio
    async def test_list_engagements_pagination(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="bs-requester8")
        for i in range(5):
            await create_test_engagement(db_session, requester, title=f"Engagement {i}")

        engagements, total = await list_engagements(db_session, skip=0, limit=2)
        assert total == 5
        assert len(engagements) == 2


class TestUpdateEngagementStatus:
    @pytest.mark.asyncio
    async def test_update_status(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="bs-requester9")
        engagement = await create_test_engagement(db_session, requester)

        update_data = EngagementUpdate(status=EngagementStatus.cancelled)
        updated = await update_engagement_status(engagement.id, update_data, requester, db_session)
        assert updated.status == EngagementStatus.cancelled

    @pytest.mark.asyncio
    async def test_update_by_non_requester_raises_403(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="bs-requester10")
        other, _ = await create_test_agent(db_session, name="bs-other10")
        engagement = await create_test_engagement(db_session, requester)

        update_data = EngagementUpdate(status=EngagementStatus.cancelled)
        with pytest.raises(HTTPException) as exc_info:
            await update_engagement_status(engagement.id, update_data, other, db_session)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_update_deliverable_url(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="bs-requester11")
        engagement = await create_test_engagement(db_session, requester)

        update_data = EngagementUpdate(deliverable_url="https://example.com/result")
        updated = await update_engagement_status(engagement.id, update_data, requester, db_session)
        assert updated.deliverable_url == "https://example.com/result"

    @pytest.mark.asyncio
    async def test_update_nonexistent_engagement_raises_404(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="bs-requester12")
        update_data = EngagementUpdate(status=EngagementStatus.cancelled)
        with pytest.raises(HTTPException) as exc_info:
            await update_engagement_status(uuid.uuid4(), update_data, requester, db_session)
        assert exc_info.value.status_code == 404
