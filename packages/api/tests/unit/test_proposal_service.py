import uuid
from datetime import datetime, timezone, timedelta

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bounty import BountyStatus
from app.models.proposal import Proposal, ProposalStatus
from tests.conftest import create_test_agent, create_test_bounty, create_test_proposal


class TestProposalSubmission:
    @pytest.mark.asyncio
    async def test_submit_proposal_via_api(self, client: AsyncClient, db_session: AsyncSession):
        poster, poster_key = await create_test_agent(db_session, name="ps-poster1")
        solver, solver_key = await create_test_agent(db_session, name="ps-solver1")
        bounty = await create_test_bounty(db_session, poster)
        await db_session.commit()

        response = await client.post(
            f"/bounties/{bounty.id}/proposals",
            json={
                "proposed_price": 0.8,
                "proposed_deadline": (
                    datetime.now(timezone.utc) + timedelta(days=5)
                ).isoformat(),
                "approach_summary": "My approach to solving this bounty",
            },
            headers={"X-API-Key": solver_key},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["proposed_price"] == 0.8
        assert data["solver_id"] == str(solver.id)
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_submit_proposal_updates_bounty_status(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        poster, _ = await create_test_agent(db_session, name="ps-poster2")
        solver, solver_key = await create_test_agent(db_session, name="ps-solver2")
        bounty = await create_test_bounty(db_session, poster)
        await db_session.commit()

        await client.post(
            f"/bounties/{bounty.id}/proposals",
            json={
                "proposed_price": 0.8,
                "proposed_deadline": (
                    datetime.now(timezone.utc) + timedelta(days=5)
                ).isoformat(),
                "approach_summary": "Approach",
            },
            headers={"X-API-Key": solver_key},
        )

        # Check bounty status changed to proposed
        response = await client.get(f"/bounties/{bounty.id}")
        assert response.json()["status"] == "proposed"


class TestDuplicatePrevention:
    @pytest.mark.asyncio
    async def test_duplicate_proposal_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        poster, _ = await create_test_agent(db_session, name="ps-poster3")
        solver, solver_key = await create_test_agent(db_session, name="ps-solver3")
        bounty = await create_test_bounty(db_session, poster)
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
            f"/bounties/{bounty.id}/proposals",
            json=proposal_data,
            headers={"X-API-Key": solver_key},
        )
        assert r1.status_code == 201

        # Second proposal from same solver fails
        r2 = await client.post(
            f"/bounties/{bounty.id}/proposals",
            json=proposal_data,
            headers={"X-API-Key": solver_key},
        )
        assert r2.status_code == 409

    @pytest.mark.asyncio
    async def test_different_solvers_can_propose(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        poster, _ = await create_test_agent(db_session, name="ps-poster4")
        solver1, solver1_key = await create_test_agent(db_session, name="ps-solver4a")
        solver2, solver2_key = await create_test_agent(db_session, name="ps-solver4b")
        bounty = await create_test_bounty(db_session, poster)
        await db_session.commit()

        proposal_data = {
            "proposed_price": 0.8,
            "proposed_deadline": (
                datetime.now(timezone.utc) + timedelta(days=5)
            ).isoformat(),
            "approach_summary": "Approach",
        }

        r1 = await client.post(
            f"/bounties/{bounty.id}/proposals",
            json=proposal_data,
            headers={"X-API-Key": solver1_key},
        )
        assert r1.status_code == 201

        r2 = await client.post(
            f"/bounties/{bounty.id}/proposals",
            json=proposal_data,
            headers={"X-API-Key": solver2_key},
        )
        assert r2.status_code == 201


class TestOnlyOpenBountiesAcceptProposals:
    @pytest.mark.asyncio
    async def test_proposal_on_cancelled_bounty_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        poster, _ = await create_test_agent(db_session, name="ps-poster5")
        solver, solver_key = await create_test_agent(db_session, name="ps-solver5")
        bounty = await create_test_bounty(
            db_session, poster, status=BountyStatus.cancelled
        )
        await db_session.commit()

        response = await client.post(
            f"/bounties/{bounty.id}/proposals",
            json={
                "proposed_price": 0.8,
                "proposed_deadline": (
                    datetime.now(timezone.utc) + timedelta(days=5)
                ).isoformat(),
                "approach_summary": "Approach",
            },
            headers={"X-API-Key": solver_key},
        )
        assert response.status_code == 400
        assert "not open" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_proposal_on_nonexistent_bounty_404(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        solver, solver_key = await create_test_agent(db_session, name="ps-solver6")
        await db_session.commit()

        fake_id = uuid.uuid4()
        response = await client.post(
            f"/bounties/{fake_id}/proposals",
            json={
                "proposed_price": 0.8,
                "proposed_deadline": (
                    datetime.now(timezone.utc) + timedelta(days=5)
                ).isoformat(),
                "approach_summary": "Approach",
            },
            headers={"X-API-Key": solver_key},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_poster_cannot_self_propose(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        poster, poster_key = await create_test_agent(db_session, name="ps-poster7")
        bounty = await create_test_bounty(db_session, poster)
        await db_session.commit()

        response = await client.post(
            f"/bounties/{bounty.id}/proposals",
            json={
                "proposed_price": 0.8,
                "proposed_deadline": (
                    datetime.now(timezone.utc) + timedelta(days=5)
                ).isoformat(),
                "approach_summary": "Approach",
            },
            headers={"X-API-Key": poster_key},
        )
        assert response.status_code == 400
        assert "own bounty" in response.json()["detail"]


class TestListProposals:
    @pytest.mark.asyncio
    async def test_list_proposals_for_bounty(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        poster, _ = await create_test_agent(db_session, name="ps-poster8")
        solver, solver_key = await create_test_agent(db_session, name="ps-solver8")
        bounty = await create_test_bounty(db_session, poster)
        await create_test_proposal(db_session, bounty, solver)
        await db_session.commit()

        response = await client.get(f"/bounties/{bounty.id}/proposals")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
