"""Integration test: negotiation protocol.

Tests multi-turn negotiation between two agents, turn alternation, term evolution,
and final agreement.
"""

import pytest
from datetime import datetime, timedelta, timezone

from helpers import register_agent, auth_headers


@pytest.mark.asyncio
async def test_multi_turn_negotiation(client):
    """Full multi-turn negotiation with counter-offers."""
    poster, poster_key = await register_agent(client, "NegPoster", "poster")
    solver, solver_key = await register_agent(client, "NegSolver", "solver")
    poster_h = await auth_headers(poster_key)
    solver_h = await auth_headers(solver_key)

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    # Post bounty
    resp = await client.post(
        "/bounties",
        json={
            "title": "Negotiation test bounty",
            "description": "Test negotiation",
            "acceptance_criteria": ["Pass tests"],
            "category": "development",
            "reward_amount": 0.1,
            "deadline": deadline,
        },
        headers=poster_h,
    )
    bounty_id = resp.json()["id"]

    # Submit proposal
    resp = await client.post(
        f"/bounties/{bounty_id}/proposals",
        json={
            "proposed_price": 0.08,
            "proposed_deadline": deadline,
            "approach_summary": "I can do this",
        },
        headers=solver_h,
    )
    proposal_id = resp.json()["id"]

    # Start negotiation
    resp = await client.post(
        "/negotiations",
        json={"bounty_id": bounty_id, "proposal_id": proposal_id},
        headers=poster_h,
    )
    neg_id = resp.json()["id"]

    # Turn 0: Poster offers initial terms
    terms_v1 = {
        "price": 0.1,
        "deadline": deadline,
        "deliverables": ["Tool", "Docs"],
        "acceptance_criteria": ["All tests pass"],
        "revision_rounds": 1,
    }
    resp = await client.post(
        f"/negotiations/{neg_id}/turns",
        json={"turn_type": "offer", "proposed_terms": terms_v1, "message": "Here's my offer"},
        headers=poster_h,
    )
    assert resp.status_code == 201
    assert resp.json()["sequence"] == 0

    # Turn 1: Solver counters
    terms_v2 = {
        "price": 0.12,
        "deadline": deadline,
        "deliverables": ["Tool", "Docs", "Tests"],
        "acceptance_criteria": ["All tests pass", "Code review"],
        "revision_rounds": 2,
    }
    resp = await client.post(
        f"/negotiations/{neg_id}/turns",
        json={"turn_type": "counter", "proposed_terms": terms_v2, "message": "I need more for extra scope"},
        headers=solver_h,
    )
    assert resp.status_code == 201
    assert resp.json()["sequence"] == 1

    # Turn 2: Poster counters back
    terms_v3 = {
        "price": 0.11,
        "deadline": deadline,
        "deliverables": ["Tool", "Docs", "Tests"],
        "acceptance_criteria": ["All tests pass"],
        "revision_rounds": 1,
    }
    resp = await client.post(
        f"/negotiations/{neg_id}/turns",
        json={"turn_type": "counter", "proposed_terms": terms_v3, "message": "Meet in the middle?"},
        headers=poster_h,
    )
    assert resp.status_code == 201
    assert resp.json()["sequence"] == 2

    # Turn 3: Solver accepts
    resp = await client.post(
        f"/negotiations/{neg_id}/turns",
        json={"turn_type": "accept", "message": "Deal!"},
        headers=solver_h,
    )
    assert resp.status_code == 201
    assert resp.json()["sequence"] == 3

    # Verify final state
    resp = await client.get(f"/negotiations/{neg_id}")
    neg = resp.json()
    assert neg["status"] == "agreed"
    assert neg["turn_count"] == 4

    # Verify turns are recorded
    resp = await client.get(f"/negotiations/{neg_id}/turns")
    turns = resp.json()
    assert len(turns) == 4
    assert turns[0]["turn_type"] == "offer"
    assert turns[1]["turn_type"] == "counter"
    assert turns[2]["turn_type"] == "counter"
    assert turns[3]["turn_type"] == "accept"


@pytest.mark.asyncio
async def test_negotiation_rejection(client):
    """Test that rejection reverts bounty to open."""
    poster, poster_key = await register_agent(client, "RejectPoster", "poster")
    solver, solver_key = await register_agent(client, "RejectSolver", "solver")
    poster_h = await auth_headers(poster_key)
    solver_h = await auth_headers(solver_key)

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    resp = await client.post(
        "/bounties",
        json={
            "title": "Rejection test bounty",
            "description": "Will be rejected",
            "acceptance_criteria": ["N/A"],
            "category": "development",
            "reward_amount": 0.05,
            "deadline": deadline,
        },
        headers=poster_h,
    )
    bounty_id = resp.json()["id"]

    resp = await client.post(
        f"/bounties/{bounty_id}/proposals",
        json={"proposed_price": 0.04, "proposed_deadline": deadline, "approach_summary": "Quick job"},
        headers=solver_h,
    )
    proposal_id = resp.json()["id"]

    resp = await client.post(
        "/negotiations",
        json={"bounty_id": bounty_id, "proposal_id": proposal_id},
        headers=poster_h,
    )
    neg_id = resp.json()["id"]

    # Poster offers
    resp = await client.post(
        f"/negotiations/{neg_id}/turns",
        json={
            "turn_type": "offer",
            "proposed_terms": {
                "price": 0.05,
                "deadline": deadline,
                "deliverables": ["Tool"],
                "acceptance_criteria": ["Done"],
                "revision_rounds": 1,
            },
        },
        headers=poster_h,
    )
    assert resp.status_code == 201

    # Solver rejects
    resp = await client.post(
        f"/negotiations/{neg_id}/turns",
        json={"turn_type": "reject", "message": "Not worth my time"},
        headers=solver_h,
    )
    assert resp.status_code == 201

    # Negotiation rejected
    resp = await client.get(f"/negotiations/{neg_id}")
    assert resp.json()["status"] == "rejected"

    # Bounty back to open
    resp = await client.get(f"/bounties/{bounty_id}")
    assert resp.json()["status"] == "open"


@pytest.mark.asyncio
async def test_turn_alternation_enforced(client):
    """Test that the same agent cannot take two consecutive turns."""
    poster, poster_key = await register_agent(client, "AltPoster", "poster")
    solver, solver_key = await register_agent(client, "AltSolver", "solver")
    poster_h = await auth_headers(poster_key)
    solver_h = await auth_headers(solver_key)

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    resp = await client.post(
        "/bounties",
        json={
            "title": "Alternation test",
            "description": "Test turn alternation",
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
        json={"proposed_price": 0.01, "proposed_deadline": deadline, "approach_summary": "Easy"},
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

    # Poster makes first offer
    resp = await client.post(
        f"/negotiations/{neg_id}/turns",
        json={"turn_type": "offer", "proposed_terms": terms},
        headers=poster_h,
    )
    assert resp.status_code == 201

    # Poster tries to go again — should fail
    resp = await client.post(
        f"/negotiations/{neg_id}/turns",
        json={"turn_type": "counter", "proposed_terms": terms},
        headers=poster_h,
    )
    assert resp.status_code == 400
