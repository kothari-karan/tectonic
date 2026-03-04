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
    requester, requester_key = await register_agent(client, "NegRequester", "requester")
    provider, provider_key = await register_agent(client, "NegProvider", "provider")
    requester_h = await auth_headers(requester_key)
    provider_h = await auth_headers(provider_key)

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    # Post engagement
    resp = await client.post(
        "/engagements",
        json={
            "title": "Negotiation test engagement",
            "description": "Test negotiation",
            "acceptance_criteria": ["Pass tests"],
            "category": "development",
            "reward_amount": 0.1,
            "deadline": deadline,
        },
        headers=requester_h,
    )
    engagement_id = resp.json()["id"]

    # Submit proposal
    resp = await client.post(
        f"/engagements/{engagement_id}/proposals",
        json={
            "proposed_price": 0.08,
            "proposed_deadline": deadline,
            "approach_summary": "I can do this",
        },
        headers=provider_h,
    )
    proposal_id = resp.json()["id"]

    # Start negotiation
    resp = await client.post(
        "/negotiations",
        json={"engagement_id": engagement_id, "proposal_id": proposal_id},
        headers=requester_h,
    )
    neg_id = resp.json()["id"]

    # Turn 0: Requester offers initial terms
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
        headers=requester_h,
    )
    assert resp.status_code == 201
    assert resp.json()["sequence"] == 0

    # Turn 1: Provider counters
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
        headers=provider_h,
    )
    assert resp.status_code == 201
    assert resp.json()["sequence"] == 1

    # Turn 2: Requester counters back
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
        headers=requester_h,
    )
    assert resp.status_code == 201
    assert resp.json()["sequence"] == 2

    # Turn 3: Provider accepts
    resp = await client.post(
        f"/negotiations/{neg_id}/turns",
        json={"turn_type": "accept", "message": "Deal!"},
        headers=provider_h,
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
    """Test that rejection reverts engagement to open."""
    requester, requester_key = await register_agent(client, "RejectRequester", "requester")
    provider, provider_key = await register_agent(client, "RejectProvider", "provider")
    requester_h = await auth_headers(requester_key)
    provider_h = await auth_headers(provider_key)

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    resp = await client.post(
        "/engagements",
        json={
            "title": "Rejection test engagement",
            "description": "Will be rejected",
            "acceptance_criteria": ["N/A"],
            "category": "development",
            "reward_amount": 0.05,
            "deadline": deadline,
        },
        headers=requester_h,
    )
    engagement_id = resp.json()["id"]

    resp = await client.post(
        f"/engagements/{engagement_id}/proposals",
        json={"proposed_price": 0.04, "proposed_deadline": deadline, "approach_summary": "Quick job"},
        headers=provider_h,
    )
    proposal_id = resp.json()["id"]

    resp = await client.post(
        "/negotiations",
        json={"engagement_id": engagement_id, "proposal_id": proposal_id},
        headers=requester_h,
    )
    neg_id = resp.json()["id"]

    # Requester offers
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
        headers=requester_h,
    )
    assert resp.status_code == 201

    # Provider rejects
    resp = await client.post(
        f"/negotiations/{neg_id}/turns",
        json={"turn_type": "reject", "message": "Not worth my time"},
        headers=provider_h,
    )
    assert resp.status_code == 201

    # Negotiation rejected
    resp = await client.get(f"/negotiations/{neg_id}")
    assert resp.json()["status"] == "rejected"

    # Engagement back to open
    resp = await client.get(f"/engagements/{engagement_id}")
    assert resp.json()["status"] == "open"


@pytest.mark.asyncio
async def test_turn_alternation_enforced(client):
    """Test that the same agent cannot take two consecutive turns."""
    requester, requester_key = await register_agent(client, "AltRequester", "requester")
    provider, provider_key = await register_agent(client, "AltProvider", "provider")
    requester_h = await auth_headers(requester_key)
    provider_h = await auth_headers(provider_key)

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    resp = await client.post(
        "/engagements",
        json={
            "title": "Alternation test",
            "description": "Test turn alternation",
            "acceptance_criteria": ["Done"],
            "category": "development",
            "reward_amount": 0.01,
            "deadline": deadline,
        },
        headers=requester_h,
    )
    engagement_id = resp.json()["id"]

    resp = await client.post(
        f"/engagements/{engagement_id}/proposals",
        json={"proposed_price": 0.01, "proposed_deadline": deadline, "approach_summary": "Easy"},
        headers=provider_h,
    )
    proposal_id = resp.json()["id"]

    resp = await client.post(
        "/negotiations",
        json={"engagement_id": engagement_id, "proposal_id": proposal_id},
        headers=requester_h,
    )
    neg_id = resp.json()["id"]

    terms = {
        "price": 0.01,
        "deadline": deadline,
        "deliverables": ["Work"],
        "acceptance_criteria": ["Done"],
        "revision_rounds": 1,
    }

    # Requester makes first offer
    resp = await client.post(
        f"/negotiations/{neg_id}/turns",
        json={"turn_type": "offer", "proposed_terms": terms},
        headers=requester_h,
    )
    assert resp.status_code == 201

    # Requester tries to go again — should fail
    resp = await client.post(
        f"/negotiations/{neg_id}/turns",
        json={"turn_type": "counter", "proposed_terms": terms},
        headers=requester_h,
    )
    assert resp.status_code == 400
