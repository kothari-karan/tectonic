"""Tests for engagement types (open, direct, invited) and provider inbox."""

import uuid
from datetime import datetime, timezone, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bounty import EngagementStatus, EngagementType
from tests.conftest import create_test_agent, create_test_engagement


class TestCreateEngagementTypes:
    @pytest.mark.asyncio
    async def test_create_open_engagement(self, client: AsyncClient, db_session: AsyncSession):
        requester, key = await create_test_agent(db_session, name="et-req1")
        await db_session.commit()

        response = await client.post(
            "/engagements",
            json={
                "title": "Open task",
                "description": "Public task",
                "acceptance_criteria": ["Done"],
                "category": "dev",
                "reward_amount": 1.0,
                "deadline": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
                "engagement_type": "open",
            },
            headers={"X-API-Key": key},
        )
        assert response.status_code == 201
        assert response.json()["engagement_type"] == "open"
        assert response.json()["target_provider_ids"] is None

    @pytest.mark.asyncio
    async def test_create_direct_engagement(self, client: AsyncClient, db_session: AsyncSession):
        requester, key = await create_test_agent(db_session, name="et-req2")
        provider, _ = await create_test_agent(db_session, name="et-prov2")
        await db_session.commit()

        response = await client.post(
            "/engagements",
            json={
                "title": "Direct task",
                "description": "Private task for specific provider",
                "acceptance_criteria": ["Done"],
                "category": "dev",
                "reward_amount": 1.0,
                "deadline": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
                "engagement_type": "direct",
                "target_provider_ids": [str(provider.id)],
            },
            headers={"X-API-Key": key},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["engagement_type"] == "direct"
        assert str(provider.id) in data["target_provider_ids"]

    @pytest.mark.asyncio
    async def test_create_invited_engagement(self, client: AsyncClient, db_session: AsyncSession):
        requester, key = await create_test_agent(db_session, name="et-req3")
        p1, _ = await create_test_agent(db_session, name="et-prov3a")
        p2, _ = await create_test_agent(db_session, name="et-prov3b")
        await db_session.commit()

        response = await client.post(
            "/engagements",
            json={
                "title": "Invited task",
                "description": "Curated RFP",
                "acceptance_criteria": ["Done"],
                "category": "design",
                "reward_amount": 2.0,
                "deadline": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
                "engagement_type": "invited",
                "target_provider_ids": [str(p1.id), str(p2.id)],
            },
            headers={"X-API-Key": key},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["engagement_type"] == "invited"
        assert len(data["target_provider_ids"]) == 2

    @pytest.mark.asyncio
    async def test_direct_without_target_ids_fails(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, key = await create_test_agent(db_session, name="et-req4")
        await db_session.commit()

        response = await client.post(
            "/engagements",
            json={
                "title": "Bad direct",
                "description": "Missing targets",
                "acceptance_criteria": ["Done"],
                "category": "dev",
                "reward_amount": 1.0,
                "deadline": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
                "engagement_type": "direct",
            },
            headers={"X-API-Key": key},
        )
        assert response.status_code == 400
        assert "target_provider_ids" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_invited_without_target_ids_fails(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, key = await create_test_agent(db_session, name="et-req5")
        await db_session.commit()

        response = await client.post(
            "/engagements",
            json={
                "title": "Bad invited",
                "description": "Missing targets",
                "acceptance_criteria": ["Done"],
                "category": "dev",
                "reward_amount": 1.0,
                "deadline": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
                "engagement_type": "invited",
            },
            headers={"X-API-Key": key},
        )
        assert response.status_code == 400
        assert "target_provider_ids" in response.json()["detail"]


class TestPublicListingFilters:
    @pytest.mark.asyncio
    async def test_public_listing_excludes_direct(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, key = await create_test_agent(db_session, name="et-req6")
        provider, _ = await create_test_agent(db_session, name="et-prov6")

        # Create one open and one direct engagement
        await create_test_engagement(db_session, requester, title="Public task")
        await create_test_engagement(
            db_session, requester, title="Private task",
            engagement_type=EngagementType.direct,
            target_provider_ids=[str(provider.id)],
        )
        await db_session.commit()

        response = await client.get("/engagements")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["engagements"][0]["title"] == "Public task"

    @pytest.mark.asyncio
    async def test_public_listing_excludes_invited(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, key = await create_test_agent(db_session, name="et-req7")
        provider, _ = await create_test_agent(db_session, name="et-prov7")

        await create_test_engagement(db_session, requester, title="Open task")
        await create_test_engagement(
            db_session, requester, title="Invited task",
            engagement_type=EngagementType.invited,
            target_provider_ids=[str(provider.id)],
        )
        await db_session.commit()

        response = await client.get("/engagements")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["engagements"][0]["title"] == "Open task"


class TestEngagementDetailAccessControl:
    @pytest.mark.asyncio
    async def test_open_engagement_public(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, _ = await create_test_agent(db_session, name="et-req8")
        engagement = await create_test_engagement(db_session, requester)
        await db_session.commit()

        response = await client.get(f"/engagements/{engagement.id}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_direct_visible_to_requester(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, req_key = await create_test_agent(db_session, name="et-req9")
        provider, _ = await create_test_agent(db_session, name="et-prov9")
        engagement = await create_test_engagement(
            db_session, requester,
            engagement_type=EngagementType.direct,
            target_provider_ids=[str(provider.id)],
        )
        await db_session.commit()

        response = await client.get(
            f"/engagements/{engagement.id}",
            headers={"X-API-Key": req_key},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_direct_visible_to_target_provider(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, _ = await create_test_agent(db_session, name="et-req10")
        provider, prov_key = await create_test_agent(db_session, name="et-prov10")
        engagement = await create_test_engagement(
            db_session, requester,
            engagement_type=EngagementType.direct,
            target_provider_ids=[str(provider.id)],
        )
        await db_session.commit()

        response = await client.get(
            f"/engagements/{engagement.id}",
            headers={"X-API-Key": prov_key},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_direct_hidden_from_outsider(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, _ = await create_test_agent(db_session, name="et-req11")
        provider, _ = await create_test_agent(db_session, name="et-prov11")
        outsider, outsider_key = await create_test_agent(db_session, name="et-outsider11")
        engagement = await create_test_engagement(
            db_session, requester,
            engagement_type=EngagementType.direct,
            target_provider_ids=[str(provider.id)],
        )
        await db_session.commit()

        response = await client.get(
            f"/engagements/{engagement.id}",
            headers={"X-API-Key": outsider_key},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_direct_hidden_without_auth(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, _ = await create_test_agent(db_session, name="et-req12")
        provider, _ = await create_test_agent(db_session, name="et-prov12")
        engagement = await create_test_engagement(
            db_session, requester,
            engagement_type=EngagementType.direct,
            target_provider_ids=[str(provider.id)],
        )
        await db_session.commit()

        response = await client.get(f"/engagements/{engagement.id}")
        assert response.status_code == 403


class TestProposalAccessControl:
    @pytest.mark.asyncio
    async def test_target_provider_can_propose_on_direct(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, _ = await create_test_agent(db_session, name="et-req13")
        provider, prov_key = await create_test_agent(db_session, name="et-prov13")
        engagement = await create_test_engagement(
            db_session, requester,
            engagement_type=EngagementType.direct,
            target_provider_ids=[str(provider.id)],
        )
        await db_session.commit()

        response = await client.post(
            f"/engagements/{engagement.id}/proposals",
            json={
                "proposed_price": 0.8,
                "proposed_deadline": (
                    datetime.now(timezone.utc) + timedelta(days=5)
                ).isoformat(),
                "approach_summary": "My approach",
            },
            headers={"X-API-Key": prov_key},
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_non_target_cannot_propose_on_direct(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, _ = await create_test_agent(db_session, name="et-req14")
        target, _ = await create_test_agent(db_session, name="et-target14")
        outsider, outsider_key = await create_test_agent(db_session, name="et-outsider14")
        engagement = await create_test_engagement(
            db_session, requester,
            engagement_type=EngagementType.direct,
            target_provider_ids=[str(target.id)],
        )
        await db_session.commit()

        response = await client.post(
            f"/engagements/{engagement.id}/proposals",
            json={
                "proposed_price": 0.8,
                "proposed_deadline": (
                    datetime.now(timezone.utc) + timedelta(days=5)
                ).isoformat(),
                "approach_summary": "My approach",
            },
            headers={"X-API-Key": outsider_key},
        )
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_invited_provider_can_propose(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, _ = await create_test_agent(db_session, name="et-req15")
        p1, p1_key = await create_test_agent(db_session, name="et-prov15a")
        p2, p2_key = await create_test_agent(db_session, name="et-prov15b")
        engagement = await create_test_engagement(
            db_session, requester,
            engagement_type=EngagementType.invited,
            target_provider_ids=[str(p1.id), str(p2.id)],
        )
        await db_session.commit()

        # Both invited providers can propose
        r1 = await client.post(
            f"/engagements/{engagement.id}/proposals",
            json={
                "proposed_price": 0.8,
                "proposed_deadline": (
                    datetime.now(timezone.utc) + timedelta(days=5)
                ).isoformat(),
                "approach_summary": "P1 approach",
            },
            headers={"X-API-Key": p1_key},
        )
        assert r1.status_code == 201

        r2 = await client.post(
            f"/engagements/{engagement.id}/proposals",
            json={
                "proposed_price": 0.9,
                "proposed_deadline": (
                    datetime.now(timezone.utc) + timedelta(days=5)
                ).isoformat(),
                "approach_summary": "P2 approach",
            },
            headers={"X-API-Key": p2_key},
        )
        assert r2.status_code == 201

    @pytest.mark.asyncio
    async def test_uninvited_cannot_propose_on_invited(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, _ = await create_test_agent(db_session, name="et-req16")
        invited, _ = await create_test_agent(db_session, name="et-invited16")
        uninvited, uninvited_key = await create_test_agent(db_session, name="et-uninvited16")
        engagement = await create_test_engagement(
            db_session, requester,
            engagement_type=EngagementType.invited,
            target_provider_ids=[str(invited.id)],
        )
        await db_session.commit()

        response = await client.post(
            f"/engagements/{engagement.id}/proposals",
            json={
                "proposed_price": 0.8,
                "proposed_deadline": (
                    datetime.now(timezone.utc) + timedelta(days=5)
                ).isoformat(),
                "approach_summary": "My approach",
            },
            headers={"X-API-Key": uninvited_key},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_anyone_can_propose_on_open(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, _ = await create_test_agent(db_session, name="et-req17")
        provider, prov_key = await create_test_agent(db_session, name="et-prov17")
        engagement = await create_test_engagement(db_session, requester)
        await db_session.commit()

        response = await client.post(
            f"/engagements/{engagement.id}/proposals",
            json={
                "proposed_price": 0.8,
                "proposed_deadline": (
                    datetime.now(timezone.utc) + timedelta(days=5)
                ).isoformat(),
                "approach_summary": "My approach",
            },
            headers={"X-API-Key": prov_key},
        )
        assert response.status_code == 201


class TestProviderInbox:
    @pytest.mark.asyncio
    async def test_inbox_returns_direct_engagements(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, _ = await create_test_agent(db_session, name="et-req18")
        provider, _ = await create_test_agent(db_session, name="et-prov18")

        await create_test_engagement(
            db_session, requester, title="Direct for you",
            engagement_type=EngagementType.direct,
            target_provider_ids=[str(provider.id)],
        )
        await create_test_engagement(
            db_session, requester, title="Open task",
        )
        await db_session.commit()

        response = await client.get(f"/agents/{provider.id}/inbox")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["engagements"][0]["title"] == "Direct for you"

    @pytest.mark.asyncio
    async def test_inbox_returns_invited_engagements(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, _ = await create_test_agent(db_session, name="et-req19")
        p1, _ = await create_test_agent(db_session, name="et-prov19a")
        p2, _ = await create_test_agent(db_session, name="et-prov19b")

        await create_test_engagement(
            db_session, requester, title="Invited RFP",
            engagement_type=EngagementType.invited,
            target_provider_ids=[str(p1.id), str(p2.id)],
        )
        await db_session.commit()

        # Both providers see it in their inbox
        r1 = await client.get(f"/agents/{p1.id}/inbox")
        assert r1.json()["total"] == 1

        r2 = await client.get(f"/agents/{p2.id}/inbox")
        assert r2.json()["total"] == 1

    @pytest.mark.asyncio
    async def test_inbox_empty_for_non_target(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, _ = await create_test_agent(db_session, name="et-req20")
        target, _ = await create_test_agent(db_session, name="et-target20")
        other, _ = await create_test_agent(db_session, name="et-other20")

        await create_test_engagement(
            db_session, requester, title="Direct task",
            engagement_type=EngagementType.direct,
            target_provider_ids=[str(target.id)],
        )
        await db_session.commit()

        response = await client.get(f"/agents/{other.id}/inbox")
        assert response.status_code == 200
        assert response.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_inbox_nonexistent_agent_404(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        fake_id = uuid.uuid4()
        response = await client.get(f"/agents/{fake_id}/inbox")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_inbox_status_filter(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, _ = await create_test_agent(db_session, name="et-req21")
        provider, _ = await create_test_agent(db_session, name="et-prov21")

        await create_test_engagement(
            db_session, requester, title="Open direct",
            engagement_type=EngagementType.direct,
            target_provider_ids=[str(provider.id)],
            status=EngagementStatus.open,
        )
        await create_test_engagement(
            db_session, requester, title="Cancelled direct",
            engagement_type=EngagementType.direct,
            target_provider_ids=[str(provider.id)],
            status=EngagementStatus.cancelled,
        )
        await db_session.commit()

        # All inbox items
        r_all = await client.get(f"/agents/{provider.id}/inbox")
        assert r_all.json()["total"] == 2

        # Only open
        r_open = await client.get(f"/agents/{provider.id}/inbox?status=open")
        assert r_open.json()["total"] == 1
        assert r_open.json()["engagements"][0]["title"] == "Open direct"
