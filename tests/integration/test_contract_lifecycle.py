"""Integration test: contract lifecycle.

Tests: agreed negotiation -> contract creation -> fund -> deliver -> verify -> settle -> reputation.
"""

import pytest
from datetime import datetime, timedelta, timezone

from helpers import register_agent, auth_headers


async def setup_agreed_negotiation(client):
    """Helper: set up an engagement with agreed negotiation, return all IDs and headers."""
    requester, requester_key = await register_agent(
        client, f"ContRequester{id(client)}", "requester"
    )
    provider, provider_key = await register_agent(
        client, f"ContProvider{id(client)}", "provider"
    )
    requester_h = await auth_headers(requester_key)
    provider_h = await auth_headers(provider_key)

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    resp = await client.post(
        "/engagements",
        json={
            "title": "Contract lifecycle engagement",
            "description": "For contract testing",
            "acceptance_criteria": ["Passes"],
            "category": "development",
            "reward_amount": 0.05,
            "deadline": deadline,
        },
        headers=requester_h,
    )
    engagement_id = resp.json()["id"]

    resp = await client.post(
        f"/engagements/{engagement_id}/proposals",
        json={"proposed_price": 0.05, "proposed_deadline": deadline, "approach_summary": "Will do"},
        headers=provider_h,
    )
    proposal_id = resp.json()["id"]

    resp = await client.post(
        "/negotiations",
        json={"engagement_id": engagement_id, "proposal_id": proposal_id},
        headers=requester_h,
    )
    neg_id = resp.json()["id"]

    # Quick offer + accept
    terms = {
        "price": 0.05,
        "deadline": deadline,
        "deliverables": ["Tool"],
        "acceptance_criteria": ["Passes"],
        "revision_rounds": 1,
    }
    await client.post(
        f"/negotiations/{neg_id}/turns",
        json={"turn_type": "offer", "proposed_terms": terms},
        headers=requester_h,
    )
    await client.post(
        f"/negotiations/{neg_id}/turns",
        json={"turn_type": "accept", "message": "Agreed"},
        headers=provider_h,
    )

    return {
        "requester": requester,
        "provider": provider,
        "requester_h": requester_h,
        "provider_h": provider_h,
        "engagement_id": engagement_id,
        "neg_id": neg_id,
    }


@pytest.mark.asyncio
async def test_contract_full_lifecycle(client):
    """Test full contract lifecycle: create -> fund -> deliver -> verify -> settle."""
    ctx = await setup_agreed_negotiation(client)

    # Create contract
    resp = await client.post(
        "/contracts",
        json={"engagement_id": ctx["engagement_id"], "negotiation_id": ctx["neg_id"]},
        headers=ctx["requester_h"],
    )
    assert resp.status_code == 201
    contract = resp.json()
    assert contract["status"] == "pending_funding"
    assert contract["terms_hash"]  # Should have computed hash
    contract_id = contract["id"]

    # Fund
    resp = await client.post(
        f"/contracts/{contract_id}/fund",
        json={"funding_tx_hash": "0x" + "11" * 32, "escrow_contract_address": "0x" + "22" * 20},
        headers=ctx["requester_h"],
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "funded"

    # Deliver
    resp = await client.post(
        f"/contracts/{contract_id}/deliver",
        json={"deliverable_url": "https://github.com/provider/work"},
        headers=ctx["provider_h"],
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "delivered"

    # Verify (approve)
    resp = await client.post(
        f"/contracts/{contract_id}/verify",
        json={"approved": True},
        headers=ctx["requester_h"],
    )
    assert resp.status_code == 200
    contract_final = resp.json()
    assert contract_final["status"] == "settled"

    # Check reputation updated
    resp = await client.get(f"/agents/{ctx['provider']['id']}/reputation")
    assert resp.status_code == 200
    rep = resp.json()
    assert rep["reputation_score"] > 0


@pytest.mark.asyncio
async def test_contract_dispute_flow(client):
    """Test dispute: create -> fund -> deliver -> dispute."""
    requester, requester_key = await register_agent(client, "DispRequester", "requester")
    provider, provider_key = await register_agent(client, "DispProvider", "provider")
    requester_h = await auth_headers(requester_key)
    provider_h = await auth_headers(provider_key)

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    resp = await client.post(
        "/engagements",
        json={
            "title": "Dispute engagement",
            "description": "Will be disputed",
            "acceptance_criteria": ["Quality"],
            "category": "design",
            "reward_amount": 0.03,
            "deadline": deadline,
        },
        headers=requester_h,
    )
    engagement_id = resp.json()["id"]

    resp = await client.post(
        f"/engagements/{engagement_id}/proposals",
        json={"proposed_price": 0.03, "proposed_deadline": deadline, "approach_summary": "Design work"},
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
        "price": 0.03,
        "deadline": deadline,
        "deliverables": ["Design"],
        "acceptance_criteria": ["Quality"],
        "revision_rounds": 1,
    }
    await client.post(
        f"/negotiations/{neg_id}/turns",
        json={"turn_type": "offer", "proposed_terms": terms},
        headers=requester_h,
    )
    await client.post(
        f"/negotiations/{neg_id}/turns",
        json={"turn_type": "accept"},
        headers=provider_h,
    )

    resp = await client.post(
        "/contracts",
        json={"engagement_id": engagement_id, "negotiation_id": neg_id},
        headers=requester_h,
    )
    contract_id = resp.json()["id"]

    await client.post(
        f"/contracts/{contract_id}/fund",
        json={"funding_tx_hash": "0x" + "aa" * 32, "escrow_contract_address": "0x" + "bb" * 20},
        headers=requester_h,
    )

    await client.post(
        f"/contracts/{contract_id}/deliver",
        json={"deliverable_url": "https://github.com/provider/bad-work"},
        headers=provider_h,
    )

    # Requester disputes
    resp = await client.post(f"/contracts/{contract_id}/dispute", headers=requester_h)
    assert resp.status_code == 200
    assert resp.json()["status"] == "disputed"


@pytest.mark.asyncio
async def test_contract_verify_reject_triggers_dispute(client):
    """Test that verifying with approved=False triggers dispute."""
    requester, requester_key = await register_agent(client, "RejectVerRequester", "requester")
    provider, provider_key = await register_agent(client, "RejectVerProvider", "provider")
    requester_h = await auth_headers(requester_key)
    provider_h = await auth_headers(provider_key)

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    resp = await client.post(
        "/engagements",
        json={
            "title": "Reject verify engagement",
            "description": "Verify will be rejected",
            "acceptance_criteria": ["High quality"],
            "category": "development",
            "reward_amount": 0.02,
            "deadline": deadline,
        },
        headers=requester_h,
    )
    engagement_id = resp.json()["id"]

    resp = await client.post(
        f"/engagements/{engagement_id}/proposals",
        json={"proposed_price": 0.02, "proposed_deadline": deadline, "approach_summary": "Quick"},
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
        "price": 0.02,
        "deadline": deadline,
        "deliverables": ["Code"],
        "acceptance_criteria": ["Quality"],
        "revision_rounds": 1,
    }
    await client.post(
        f"/negotiations/{neg_id}/turns",
        json={"turn_type": "offer", "proposed_terms": terms},
        headers=requester_h,
    )
    await client.post(
        f"/negotiations/{neg_id}/turns",
        json={"turn_type": "accept"},
        headers=provider_h,
    )

    resp = await client.post(
        "/contracts",
        json={"engagement_id": engagement_id, "negotiation_id": neg_id},
        headers=requester_h,
    )
    contract_id = resp.json()["id"]

    await client.post(
        f"/contracts/{contract_id}/fund",
        json={"funding_tx_hash": "0x" + "cc" * 32, "escrow_contract_address": "0x" + "dd" * 20},
        headers=requester_h,
    )
    await client.post(
        f"/contracts/{contract_id}/deliver",
        json={"deliverable_url": "https://example.com/bad"},
        headers=provider_h,
    )

    # Reject verification
    resp = await client.post(
        f"/contracts/{contract_id}/verify",
        json={"approved": False},
        headers=requester_h,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "disputed"
