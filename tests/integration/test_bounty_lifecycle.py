"""Integration test: full engagement lifecycle.

Tests: post engagement -> submit proposal -> negotiate -> agree -> verify DB state at each step.
"""

import pytest
from datetime import datetime, timedelta, timezone

from helpers import register_agent, auth_headers


@pytest.mark.asyncio
async def test_full_engagement_lifecycle(client):
    """End-to-end lifecycle: engagement -> proposal -> negotiation -> contract -> delivery -> settlement."""

    # 1. Register requester and provider
    requester, requester_key = await register_agent(client, "Requester1", "requester")
    provider, provider_key = await register_agent(
        client, "Provider1", "provider", capabilities=["python", "cli-tools"]
    )

    requester_headers = await auth_headers(requester_key)
    provider_headers = await auth_headers(provider_key)

    # 2. Post an engagement
    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    engagement_data = {
        "title": "Build a CSV to JSON converter",
        "description": "Python CLI tool that converts CSV files to JSON format",
        "acceptance_criteria": ["Handles standard CSV", "Supports custom delimiters", "90%+ coverage"],
        "category": "development",
        "reward_amount": 0.05,
        "deadline": deadline,
    }
    resp = await client.post("/engagements", json=engagement_data, headers=requester_headers)
    assert resp.status_code == 201
    engagement = resp.json()
    assert engagement["status"] == "open"
    assert engagement["title"] == "Build a CSV to JSON converter"
    engagement_id = engagement["id"]

    # 3. Verify engagement appears in list
    resp = await client.get("/engagements", params={"status": "open"})
    assert resp.status_code == 200
    engagements = resp.json()["engagements"]
    assert any(b["id"] == engagement_id for b in engagements)

    # 4. Provider submits proposal
    proposal_deadline = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    proposal_data = {
        "proposed_price": 0.04,
        "proposed_deadline": proposal_deadline,
        "approach_summary": "Will use Click for CLI, pytest for testing. Estimated 3 days.",
    }
    resp = await client.post(
        f"/engagements/{engagement_id}/proposals", json=proposal_data, headers=provider_headers
    )
    assert resp.status_code == 201
    proposal = resp.json()
    assert proposal["status"] == "pending"
    proposal_id = proposal["id"]

    # 5. Verify engagement status changed to proposed
    resp = await client.get(f"/engagements/{engagement_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "proposed"

    # 6. Requester starts negotiation
    neg_data = {"engagement_id": engagement_id, "proposal_id": proposal_id}
    resp = await client.post("/negotiations", json=neg_data, headers=requester_headers)
    assert resp.status_code == 201
    negotiation = resp.json()
    assert negotiation["status"] == "active"
    neg_id = negotiation["id"]

    # 7. Engagement status should be negotiating
    resp = await client.get(f"/engagements/{engagement_id}")
    assert resp.json()["status"] == "negotiating"

    # 8. Requester makes first offer (counter to the proposal)
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
    resp = await client.post(f"/negotiations/{neg_id}/turns", json=turn_data, headers=requester_headers)
    assert resp.status_code == 201
    turn = resp.json()
    assert turn["turn_type"] == "offer"
    assert turn["sequence"] == 0

    # 9. Provider accepts
    accept_data = {
        "turn_type": "accept",
        "message": "Deal! I'll deliver within 5 days with comprehensive tests.",
    }
    resp = await client.post(f"/negotiations/{neg_id}/turns", json=accept_data, headers=provider_headers)
    assert resp.status_code == 201
    turn = resp.json()
    assert turn["turn_type"] == "accept"

    # 10. Negotiation should be agreed
    resp = await client.get(f"/negotiations/{neg_id}")
    assert resp.json()["status"] == "agreed"

    # 11. Engagement should be agreed
    resp = await client.get(f"/engagements/{engagement_id}")
    assert resp.json()["status"] == "agreed"

    # 12. Create contract
    contract_data = {"engagement_id": engagement_id, "negotiation_id": neg_id}
    resp = await client.post("/contracts", json=contract_data, headers=requester_headers)
    assert resp.status_code == 201
    contract = resp.json()
    assert contract["status"] == "pending_funding"
    contract_id = contract["id"]

    # 13. Fund contract
    fund_data = {
        "funding_tx_hash": "0x" + "ab" * 32,
        "escrow_contract_address": "0x" + "cd" * 20,
    }
    resp = await client.post(f"/contracts/{contract_id}/fund", json=fund_data, headers=requester_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "funded"

    # 14. Deliver
    deliver_data = {"deliverable_url": "https://github.com/provider/csv-to-json"}
    resp = await client.post(
        f"/contracts/{contract_id}/deliver", json=deliver_data, headers=provider_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "delivered"

    # 15. Verify (approve)
    verify_data = {"approved": True}
    resp = await client.post(
        f"/contracts/{contract_id}/verify", json=verify_data, headers=requester_headers
    )
    assert resp.status_code == 200
    contract_final = resp.json()
    assert contract_final["status"] == "settled"

    # 16. Check reputation
    resp = await client.get(f"/agents/{requester['id']}/reputation")
    assert resp.status_code == 200
    requester_rep = resp.json()
    assert requester_rep["reputation_score"] > 0

    resp = await client.get(f"/agents/{provider['id']}/reputation")
    assert resp.status_code == 200
    provider_rep = resp.json()
    assert provider_rep["reputation_score"] > 0


@pytest.mark.asyncio
async def test_engagement_listing_filters(client):
    """Test engagement listing with various filters."""
    requester, requester_key = await register_agent(client, "FilterRequester", "requester")
    headers = await auth_headers(requester_key)
    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    # Create engagements in different categories
    for i, category in enumerate(["development", "design", "data"]):
        await client.post(
            "/engagements",
            json={
                "title": f"Engagement {category} {i}",
                "description": f"A {category} engagement",
                "acceptance_criteria": ["Done well"],
                "category": category,
                "reward_amount": 0.01 * (i + 1),
                "deadline": deadline,
            },
            headers=headers,
        )

    # Filter by category
    resp = await client.get("/engagements", params={"category": "development"})
    assert resp.status_code == 200
    engagements = resp.json()["engagements"]
    assert all(b["category"] == "development" for b in engagements)

    # Filter by status
    resp = await client.get("/engagements", params={"status": "open"})
    assert resp.status_code == 200
    assert len(resp.json()["engagements"]) >= 3

    # Get all engagements
    resp = await client.get("/engagements")
    assert resp.status_code == 200
    assert len(resp.json()["engagements"]) >= 3
