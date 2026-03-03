"""Integration test: full bounty lifecycle.

Tests: post bounty -> submit proposal -> negotiate -> agree -> verify DB state at each step.
"""

import pytest
from datetime import datetime, timedelta, timezone

from helpers import register_agent, auth_headers


@pytest.mark.asyncio
async def test_full_bounty_lifecycle(client):
    """End-to-end lifecycle: bounty -> proposal -> negotiation -> contract -> delivery -> settlement."""

    # 1. Register poster and solver
    poster, poster_key = await register_agent(client, "Poster1", "poster")
    solver, solver_key = await register_agent(
        client, "Solver1", "solver", capabilities=["python", "cli-tools"]
    )

    poster_headers = await auth_headers(poster_key)
    solver_headers = await auth_headers(solver_key)

    # 2. Post a bounty
    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    bounty_data = {
        "title": "Build a CSV to JSON converter",
        "description": "Python CLI tool that converts CSV files to JSON format",
        "acceptance_criteria": ["Handles standard CSV", "Supports custom delimiters", "90%+ coverage"],
        "category": "development",
        "reward_amount": 0.05,
        "deadline": deadline,
    }
    resp = await client.post("/bounties", json=bounty_data, headers=poster_headers)
    assert resp.status_code == 201
    bounty = resp.json()
    assert bounty["status"] == "open"
    assert bounty["title"] == "Build a CSV to JSON converter"
    bounty_id = bounty["id"]

    # 3. Verify bounty appears in list
    resp = await client.get("/bounties", params={"status": "open"})
    assert resp.status_code == 200
    bounties = resp.json()["bounties"]
    assert any(b["id"] == bounty_id for b in bounties)

    # 4. Solver submits proposal
    proposal_deadline = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    proposal_data = {
        "proposed_price": 0.04,
        "proposed_deadline": proposal_deadline,
        "approach_summary": "Will use Click for CLI, pytest for testing. Estimated 3 days.",
    }
    resp = await client.post(
        f"/bounties/{bounty_id}/proposals", json=proposal_data, headers=solver_headers
    )
    assert resp.status_code == 201
    proposal = resp.json()
    assert proposal["status"] == "pending"
    proposal_id = proposal["id"]

    # 5. Verify bounty status changed to proposed
    resp = await client.get(f"/bounties/{bounty_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "proposed"

    # 6. Poster starts negotiation
    neg_data = {"bounty_id": bounty_id, "proposal_id": proposal_id}
    resp = await client.post("/negotiations", json=neg_data, headers=poster_headers)
    assert resp.status_code == 201
    negotiation = resp.json()
    assert negotiation["status"] == "active"
    neg_id = negotiation["id"]

    # 7. Bounty status should be negotiating
    resp = await client.get(f"/bounties/{bounty_id}")
    assert resp.json()["status"] == "negotiating"

    # 8. Poster makes first offer (counter to the proposal)
    terms = {
        "price": 0.05,
        "deadline": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
        "deliverables": ["CLI tool", "README", "Tests"],
        "acceptance_criteria": ["90%+ coverage", "Custom delimiters", "Error handling"],
        "revision_rounds": 2,
    }
    turn_data = {
        "turn_type": "offer",
        "proposed_terms": terms,
        "message": "I'll pay full price if you guarantee 90% coverage",
    }
    resp = await client.post(f"/negotiations/{neg_id}/turns", json=turn_data, headers=poster_headers)
    assert resp.status_code == 201
    turn = resp.json()
    assert turn["turn_type"] == "offer"
    assert turn["sequence"] == 0

    # 9. Solver accepts
    accept_data = {
        "turn_type": "accept",
        "message": "Deal! I'll deliver within 5 days with comprehensive tests.",
    }
    resp = await client.post(f"/negotiations/{neg_id}/turns", json=accept_data, headers=solver_headers)
    assert resp.status_code == 201
    turn = resp.json()
    assert turn["turn_type"] == "accept"

    # 10. Negotiation should be agreed
    resp = await client.get(f"/negotiations/{neg_id}")
    assert resp.json()["status"] == "agreed"

    # 11. Bounty should be agreed
    resp = await client.get(f"/bounties/{bounty_id}")
    assert resp.json()["status"] == "agreed"

    # 12. Create contract
    contract_data = {"bounty_id": bounty_id, "negotiation_id": neg_id}
    resp = await client.post("/contracts", json=contract_data, headers=poster_headers)
    assert resp.status_code == 201
    contract = resp.json()
    assert contract["status"] == "pending_funding"
    contract_id = contract["id"]

    # 13. Fund contract
    fund_data = {
        "funding_tx_hash": "0x" + "ab" * 32,
        "escrow_contract_address": "0x" + "cd" * 20,
    }
    resp = await client.post(f"/contracts/{contract_id}/fund", json=fund_data, headers=poster_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "funded"

    # 14. Deliver
    deliver_data = {"deliverable_url": "https://github.com/solver/csv-to-json"}
    resp = await client.post(
        f"/contracts/{contract_id}/deliver", json=deliver_data, headers=solver_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "delivered"

    # 15. Verify (approve)
    verify_data = {"approved": True}
    resp = await client.post(
        f"/contracts/{contract_id}/verify", json=verify_data, headers=poster_headers
    )
    assert resp.status_code == 200
    contract_final = resp.json()
    assert contract_final["status"] == "settled"

    # 16. Check reputation
    resp = await client.get(f"/agents/{poster['id']}/reputation")
    assert resp.status_code == 200
    poster_rep = resp.json()
    assert poster_rep["reputation_score"] > 0

    resp = await client.get(f"/agents/{solver['id']}/reputation")
    assert resp.status_code == 200
    solver_rep = resp.json()
    assert solver_rep["reputation_score"] > 0


@pytest.mark.asyncio
async def test_bounty_listing_filters(client):
    """Test bounty listing with various filters."""
    poster, poster_key = await register_agent(client, "FilterPoster", "poster")
    headers = await auth_headers(poster_key)
    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    # Create bounties in different categories
    for i, category in enumerate(["development", "design", "data"]):
        await client.post(
            "/bounties",
            json={
                "title": f"Bounty {category} {i}",
                "description": f"A {category} bounty",
                "acceptance_criteria": ["Done well"],
                "category": category,
                "reward_amount": 0.01 * (i + 1),
                "deadline": deadline,
            },
            headers=headers,
        )

    # Filter by category
    resp = await client.get("/bounties", params={"category": "development"})
    assert resp.status_code == 200
    bounties = resp.json()["bounties"]
    assert all(b["category"] == "development" for b in bounties)

    # Filter by status
    resp = await client.get("/bounties", params={"status": "open"})
    assert resp.status_code == 200
    assert len(resp.json()["bounties"]) >= 3

    # Get all bounties
    resp = await client.get("/bounties")
    assert resp.status_code == 200
    assert len(resp.json()["bounties"]) >= 3
