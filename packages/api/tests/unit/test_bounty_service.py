import uuid
from datetime import datetime, timezone, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import AgentType
from app.models.bounty import BountyStatus
from app.schemas.bounty import BountyCreate, BountyUpdate
from app.services.bounty_service import (
    create_bounty,
    get_bounty,
    list_bounties,
    update_bounty_status,
)
from tests.conftest import create_test_agent, create_test_bounty


class TestCreateBounty:
    @pytest.mark.asyncio
    async def test_create_bounty_success(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="bs-poster1")
        data = BountyCreate(
            title="Test Bounty",
            description="Description for test",
            acceptance_criteria=["c1", "c2"],
            category="ai",
            reward_amount=2.5,
            deadline=datetime.now(timezone.utc) + timedelta(days=7),
        )
        bounty = await create_bounty(data, poster, db_session)

        assert bounty.title == "Test Bounty"
        assert bounty.poster_id == poster.id
        assert bounty.status == BountyStatus.open
        assert bounty.reward_token == "ETH"
        assert bounty.reward_amount == 2.5

    @pytest.mark.asyncio
    async def test_create_bounty_increments_posted_count(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="bs-poster2")
        assert poster.bounties_posted == 0

        data = BountyCreate(
            title="Bounty 1",
            description="Description",
            acceptance_criteria=["c1"],
            category="web3",
            reward_amount=1.0,
            deadline=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await create_bounty(data, poster, db_session)
        await db_session.refresh(poster)
        assert poster.bounties_posted == 1


class TestGetBounty:
    @pytest.mark.asyncio
    async def test_get_existing_bounty(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="bs-poster3")
        bounty = await create_test_bounty(db_session, poster, title="Findable Bounty")

        found = await get_bounty(bounty.id, db_session)
        assert found.id == bounty.id
        assert found.title == "Findable Bounty"

    @pytest.mark.asyncio
    async def test_get_nonexistent_bounty_raises_404(self, db_session: AsyncSession):
        with pytest.raises(HTTPException) as exc_info:
            await get_bounty(uuid.uuid4(), db_session)
        assert exc_info.value.status_code == 404


class TestListBounties:
    @pytest.mark.asyncio
    async def test_list_all_bounties(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="bs-poster4")
        await create_test_bounty(db_session, poster, title="B1")
        await create_test_bounty(db_session, poster, title="B2")

        bounties, total = await list_bounties(db_session)
        assert total == 2
        assert len(bounties) == 2

    @pytest.mark.asyncio
    async def test_list_bounties_filter_by_status(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="bs-poster5")
        await create_test_bounty(db_session, poster, title="Open B", status=BountyStatus.open)
        await create_test_bounty(
            db_session, poster, title="Cancelled B", status=BountyStatus.cancelled
        )

        bounties, total = await list_bounties(
            db_session, status_filter=BountyStatus.open
        )
        assert total == 1
        assert bounties[0].title == "Open B"

    @pytest.mark.asyncio
    async def test_list_bounties_filter_by_category(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="bs-poster6")
        await create_test_bounty(db_session, poster, title="AI Bounty", category="ai")
        await create_test_bounty(db_session, poster, title="Web3 Bounty", category="web3")

        bounties, total = await list_bounties(db_session, category="ai")
        assert total == 1
        assert bounties[0].category == "ai"

    @pytest.mark.asyncio
    async def test_list_bounties_filter_by_poster(self, db_session: AsyncSession):
        poster1, _ = await create_test_agent(db_session, name="bs-poster7a")
        poster2, _ = await create_test_agent(db_session, name="bs-poster7b")
        await create_test_bounty(db_session, poster1, title="P1 Bounty")
        await create_test_bounty(db_session, poster2, title="P2 Bounty")

        bounties, total = await list_bounties(db_session, poster_id=poster1.id)
        assert total == 1

    @pytest.mark.asyncio
    async def test_list_bounties_pagination(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="bs-poster8")
        for i in range(5):
            await create_test_bounty(db_session, poster, title=f"Bounty {i}")

        bounties, total = await list_bounties(db_session, skip=0, limit=2)
        assert total == 5
        assert len(bounties) == 2


class TestUpdateBountyStatus:
    @pytest.mark.asyncio
    async def test_update_status(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="bs-poster9")
        bounty = await create_test_bounty(db_session, poster)

        update_data = BountyUpdate(status=BountyStatus.cancelled)
        updated = await update_bounty_status(bounty.id, update_data, poster, db_session)
        assert updated.status == BountyStatus.cancelled

    @pytest.mark.asyncio
    async def test_update_by_non_poster_raises_403(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="bs-poster10")
        other, _ = await create_test_agent(db_session, name="bs-other10")
        bounty = await create_test_bounty(db_session, poster)

        update_data = BountyUpdate(status=BountyStatus.cancelled)
        with pytest.raises(HTTPException) as exc_info:
            await update_bounty_status(bounty.id, update_data, other, db_session)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_update_deliverable_url(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="bs-poster11")
        bounty = await create_test_bounty(db_session, poster)

        update_data = BountyUpdate(deliverable_url="https://example.com/result")
        updated = await update_bounty_status(bounty.id, update_data, poster, db_session)
        assert updated.deliverable_url == "https://example.com/result"

    @pytest.mark.asyncio
    async def test_update_nonexistent_bounty_raises_404(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="bs-poster12")
        update_data = BountyUpdate(status=BountyStatus.cancelled)
        with pytest.raises(HTTPException) as exc_info:
            await update_bounty_status(uuid.uuid4(), update_data, poster, db_session)
        assert exc_info.value.status_code == 404
