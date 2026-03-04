import uuid
from datetime import datetime, timezone, timedelta

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bounty import EngagementStatus
from app.models.proposal import Proposal, ProposalStatus
from tests.conftest import create_test_agent, create_test_engagement, create_test_proposal


class TestProposalSubmission:
    @pytest.mark.asyncio
    async def test_submit_proposal_via_api(self, client: AsyncClient, db_session: AsyncSession):
        requester, requester_key = await create_test_agent(db_session, name="ps-requester1")
        provider, provider_key = await create_test_agent(db_session, name="ps-provider1")
        engagement = await create_test_engagement(db_session, requester)
        await db_session.commit()

        response = await client.post(
            f"/engagements/{engagement.id}/proposals",
            json={
                "proposed_price": 0.8,
                "proposed_deadline": (
                    datetime.now(timezone.utc) + timedelta(days=5)
                ).isoformat(),
                "approach_summary": "My approach to completing this engagement",
            },
            headers={"X-API-Key": provider_key},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["proposed_price"] == 0.8
        assert data["provider_id"] == str(provider.id)
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_submit_proposal_updates_engagement_status(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, _ = await create_test_agent(db_session, name="ps-requester2")
        provider, provider_key = await create_test_agent(db_session, name="ps-provider2")
        engagement = await create_test_engagement(db_session, requester)
        await db_session.commit()

        await client.post(
            f"/engagements/{engagement.id}/proposals",
            json={
                "proposed_price": 0.8,
                "proposed_deadline": (
                    datetime.now(timezone.utc) + timedelta(days=5)
                ).isoformat(),
                "approach_summary": "Approach",
            },
            headers={"X-API-Key": provider_key},
        )

        # Check engagement status changed to proposed
        response = await client.get(f"/engagements/{engagement.id}")
        assert response.json()["status"] == "proposed"


class TestDuplicatePrevention:
    @pytest.mark.asyncio
    async def test_duplicate_proposal_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, _ = await create_test_agent(db_session, name="ps-requester3")
        provider, provider_key = await create_test_agent(db_session, name="ps-provider3")
        engagement = await create_test_engagement(db_session, requester)
        await db_session.commit()

        proposal_data = {
            "proposed_price": 0.8,
            "proposed_deadline": (
                datetime.now(timezone.utc) + timedelta(days=5)
            ).isoformat(),
            "approach_summary": "Approach",
        }

        # First proposal succeeds
        r1 = await client.post(
            f"/engagements/{engagement.id}/proposals",
            json=proposal_data,
            headers={"X-API-Key": provider_key},
        )
        assert r1.status_code == 201

        # Second proposal from same provider fails
        r2 = await client.post(
            f"/engagements/{engagement.id}/proposals",
            json=proposal_data,
            headers={"X-API-Key": provider_key},
        )
        assert r2.status_code == 409

    @pytest.mark.asyncio
    async def test_different_providers_can_propose(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, _ = await create_test_agent(db_session, name="ps-requester4")
        provider1, provider1_key = await create_test_agent(db_session, name="ps-provider4a")
        provider2, provider2_key = await create_test_agent(db_session, name="ps-provider4b")
        engagement = await create_test_engagement(db_session, requester)
        await db_session.commit()

        proposal_data = {
            "proposed_price": 0.8,
            "proposed_deadline": (
                datetime.now(timezone.utc) + timedelta(days=5)
            ).isoformat(),
            "approach_summary": "Approach",
        }

        r1 = await client.post(
            f"/engagements/{engagement.id}/proposals",
            json=proposal_data,
            headers={"X-API-Key": provider1_key},
        )
        assert r1.status_code == 201

        r2 = await client.post(
            f"/engagements/{engagement.id}/proposals",
            json=proposal_data,
            headers={"X-API-Key": provider2_key},
        )
        assert r2.status_code == 201


class TestOnlyOpenEngagementsAcceptProposals:
    @pytest.mark.asyncio
    async def test_proposal_on_cancelled_engagement_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, _ = await create_test_agent(db_session, name="ps-requester5")
        provider, provider_key = await create_test_agent(db_session, name="ps-provider5")
        engagement = await create_test_engagement(
            db_session, requester, status=EngagementStatus.cancelled
        )
        await db_session.commit()

        response = await client.post(
            f"/engagements/{engagement.id}/proposals",
            json={
                "proposed_price": 0.8,
                "proposed_deadline": (
                    datetime.now(timezone.utc) + timedelta(days=5)
                ).isoformat(),
                "approach_summary": "Approach",
            },
            headers={"X-API-Key": provider_key},
        )
        assert response.status_code == 400
        assert "not open" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_proposal_on_nonexistent_engagement_404(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        provider, provider_key = await create_test_agent(db_session, name="ps-provider6")
        await db_session.commit()

        fake_id = uuid.uuid4()
        response = await client.post(
            f"/engagements/{fake_id}/proposals",
            json={
                "proposed_price": 0.8,
                "proposed_deadline": (
                    datetime.now(timezone.utc) + timedelta(days=5)
                ).isoformat(),
                "approach_summary": "Approach",
            },
            headers={"X-API-Key": provider_key},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_requester_cannot_self_propose(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, requester_key = await create_test_agent(db_session, name="ps-requester7")
        engagement = await create_test_engagement(db_session, requester)
        await db_session.commit()

        response = await client.post(
            f"/engagements/{engagement.id}/proposals",
            json={
                "proposed_price": 0.8,
                "proposed_deadline": (
                    datetime.now(timezone.utc) + timedelta(days=5)
                ).isoformat(),
                "approach_summary": "Approach",
            },
            headers={"X-API-Key": requester_key},
        )
        assert response.status_code == 400
        assert "own engagement" in response.json()["detail"]


class TestListProposals:
    @pytest.mark.asyncio
    async def test_list_proposals_for_engagement(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, _ = await create_test_agent(db_session, name="ps-requester8")
        provider, provider_key = await create_test_agent(db_session, name="ps-provider8")
        engagement = await create_test_engagement(db_session, requester)
        await create_test_proposal(db_session, engagement, provider)
        await db_session.commit()

        response = await client.get(f"/engagements/{engagement.id}/proposals")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
