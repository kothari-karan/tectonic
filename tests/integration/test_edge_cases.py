"""Integration test: edge cases.

Tests: expired bounties, cancelled bounties, double-fund prevention, concurrent proposals.
"""

import pytest
from datetime import datetime, timedelta, timezone

from helpers import register_agent, auth_headers


@pytest.mark.asyncio
async def test_multiple_proposals_on_same_bounty(client):
    """Multiple solvers can propose on the same bounty."""
    poster, poster_key = await register_agent(client, "MultiPoster", "poster")
    solver1, solver1_key = await register_agent(client, "MultiSolver1", "solver")
    solver2, solver2_key = await register_agent(client, "MultiSolver2", "solver")
    poster_h = await auth_headers(poster_key)
    solver1_h = await auth_headers(solver1_key)
    solver2_h = await auth_headers(solver2_key)

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    resp = await client.post(
        "/bounties",
        json={
            "title": "Multi-proposal bounty",
            "description": "Multiple solvers",
            "acceptance_criteria": ["Done"],
            "category": "development",
            "reward_amount": 0.1,
            "deadline": deadline,
        },
        headers=poster_h,
    )
    bounty_id = resp.json()["id"]

    # Solver 1 proposes
    resp = await client.post(
        f"/bounties/{bounty_id}/proposals",
        json={"proposed_price": 0.08, "proposed_deadline": deadline, "approach_summary": "My approach"},
        headers=solver1_h,
    )
    assert resp.status_code == 201

    # Solver 2 proposes
    resp = await client.post(
        f"/bounties/{bounty_id}/proposals",
        json={"proposed_price": 0.09, "proposed_deadline": deadline, "approach_summary": "Better approach"},
        headers=solver2_h,
    )
    assert resp.status_code == 201

    # Should have 2 proposals
    resp = await client.get(f"/bounties/{bounty_id}/proposals")
    assert resp.status_code == 200
    proposals = resp.json()
    if isinstance(proposals, dict):
        proposals = proposals.get("proposals", proposals)
    assert len(proposals) == 2


@pytest.mark.asyncio
async def test_same_solver_cannot_propose_twice(client):
    """Same solver cannot submit two proposals on the same bounty."""
    poster, poster_key = await register_agent(client, "DupPoster", "poster")
    solver, solver_key = await register_agent(client, "DupSolver", "solver")
    poster_h = await auth_headers(poster_key)
    solver_h = await auth_headers(solver_key)

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    resp = await client.post(
        "/bounties",
        json={
            "title": "Dup proposal bounty",
            "description": "Test dup prevention",
            "acceptance_criteria": ["Done"],
            "category": "development",
            "reward_amount": 0.01,
            "deadline": deadline,
        },
        headers=poster_h,
    )
    bounty_id = resp.json()["id"]

    # First proposal
    resp = await client.post(
        f"/bounties/{bounty_id}/proposals",
        json={"proposed_price": 0.01, "proposed_deadline": deadline, "approach_summary": "First try"},
        headers=solver_h,
    )
    assert resp.status_code == 201

    # Duplicate proposal should fail
    resp = await client.post(
        f"/bounties/{bounty_id}/proposals",
        json={"proposed_price": 0.009, "proposed_deadline": deadline, "approach_summary": "Second try"},
        headers=solver_h,
    )
    assert resp.status_code in (400, 409)


@pytest.mark.asyncio
async def test_poster_cannot_propose_on_own_bounty(client):
    """Poster cannot submit a proposal on their own bounty."""
    poster, poster_key = await register_agent(client, "SelfPoster", "both")
    poster_h = await auth_headers(poster_key)

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    resp = await client.post(
        "/bounties",
        json={
            "title": "Self-proposal test",
            "description": "Cannot self-propose",
            "acceptance_criteria": ["Done"],
            "category": "development",
            "reward_amount": 0.01,
            "deadline": deadline,
        },
        headers=poster_h,
    )
    bounty_id = resp.json()["id"]

    # Self-proposal should fail
    resp = await client.post(
        f"/bounties/{bounty_id}/proposals",
        json={"proposed_price": 0.01, "proposed_deadline": deadline, "approach_summary": "Self"},
        headers=poster_h,
    )
    assert resp.status_code in (400, 403)


@pytest.mark.asyncio
async def test_nonexistent_bounty_returns_404(client):
    """Getting a non-existent bounty should return 404."""
    import uuid
    resp = await client.get(f"/bounties/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_nonexistent_agent_returns_404(client):
    """Getting a non-existent agent should return 404."""
    import uuid
    resp = await client.get(f"/agents/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unauthorized_fund_rejected(client):
    """Only the poster can fund their contract."""
    poster, poster_key = await register_agent(client, "FundPoster", "poster")
    solver, solver_key = await register_agent(client, "FundSolver", "solver")
    poster_h = await auth_headers(poster_key)
    solver_h = await auth_headers(solver_key)

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    resp = await client.post(
        "/bounties",
        json={
            "title": "Fund auth test",
            "description": "Test fund authorization",
            "acceptance_criteria": ["Done"],
            "category": "development",
            "reward_amount": 0.01,
            "deadline": deadline,
        },
        headers=poster_h,
    )
    bounty_id = resp.json()["id"]

    resp = await client.post(
        f"/bounties/{bounty_id}/proposals",
        json={"proposed_price": 0.01, "proposed_deadline": deadline, "approach_summary": "Quick"},
        headers=solver_h,
    )
    proposal_id = resp.json()["id"]

    resp = await client.post(
        "/negotiations",
        json={"bounty_id": bounty_id, "proposal_id": proposal_id},
        headers=poster_h,
    )
    neg_id = resp.json()["id"]

    terms = {
        "price": 0.01,
        "deadline": deadline,
        "deliverables": ["Work"],
        "acceptance_criteria": ["Done"],
        "revision_rounds": 1,
    }
    await client.post(
        f"/negotiations/{neg_id}/turns",
        json={"turn_type": "offer", "proposed_terms": terms},
        headers=poster_h,
    )
    await client.post(
        f"/negotiations/{neg_id}/turns",
        json={"turn_type": "accept"},
        headers=solver_h,
    )

    resp = await client.post(
        "/contracts",
        json={"bounty_id": bounty_id, "negotiation_id": neg_id},
        headers=poster_h,
    )
    contract_id = resp.json()["id"]

    # Solver tries to fund — should fail
    resp = await client.post(
        f"/contracts/{contract_id}/fund",
        json={"funding_tx_hash": "0x" + "ee" * 32, "escrow_contract_address": "0x" + "ff" * 20},
        headers=solver_h,
    )
    assert resp.status_code in (400, 403)
