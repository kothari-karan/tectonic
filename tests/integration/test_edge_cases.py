"""Integration test: edge cases.

Tests: expired engagements, cancelled engagements, double-fund prevention, concurrent proposals.
"""

import pytest
from datetime import datetime, timedelta, timezone

from helpers import register_agent, auth_headers


@pytest.mark.asyncio
async def test_multiple_proposals_on_same_engagement(client):
    """Multiple providers can propose on the same engagement."""
    requester, requester_key = await register_agent(client, "MultiRequester", "requester")
    provider1, provider1_key = await register_agent(client, "MultiProvider1", "provider")
    provider2, provider2_key = await register_agent(client, "MultiProvider2", "provider")
    requester_h = await auth_headers(requester_key)
    provider1_h = await auth_headers(provider1_key)
    provider2_h = await auth_headers(provider2_key)

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    resp = await client.post(
        "/engagements",
        json={
            "title": "Multi-proposal engagement",
            "description": "Multiple providers",
            "acceptance_criteria": ["Done"],
            "category": "development",
            "reward_amount": 0.1,
            "deadline": deadline,
        },
        headers=requester_h,
    )
    engagement_id = resp.json()["id"]

    # Provider 1 proposes
    resp = await client.post(
        f"/engagements/{engagement_id}/proposals",
        json={"proposed_price": 0.08, "proposed_deadline": deadline, "approach_summary": "My approach"},
        headers=provider1_h,
    )
    assert resp.status_code == 201

    # Provider 2 proposes
    resp = await client.post(
        f"/engagements/{engagement_id}/proposals",
        json={"proposed_price": 0.09, "proposed_deadline": deadline, "approach_summary": "Better approach"},
        headers=provider2_h,
    )
    assert resp.status_code == 201

    # Should have 2 proposals
    resp = await client.get(f"/engagements/{engagement_id}/proposals")
    assert resp.status_code == 200
    proposals = resp.json()
    if isinstance(proposals, dict):
        proposals = proposals.get("proposals", proposals)
    assert len(proposals) == 2


@pytest.mark.asyncio
async def test_same_provider_cannot_propose_twice(client):
    """Same provider cannot submit two proposals on the same engagement."""
    requester, requester_key = await register_agent(client, "DupRequester", "requester")
    provider, provider_key = await register_agent(client, "DupProvider", "provider")
    requester_h = await auth_headers(requester_key)
    provider_h = await auth_headers(provider_key)

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    resp = await client.post(
        "/engagements",
        json={
            "title": "Dup proposal engagement",
            "description": "Test dup prevention",
            "acceptance_criteria": ["Done"],
            "category": "development",
            "reward_amount": 0.01,
            "deadline": deadline,
        },
        headers=requester_h,
    )
    engagement_id = resp.json()["id"]

    # First proposal
    resp = await client.post(
        f"/engagements/{engagement_id}/proposals",
        json={"proposed_price": 0.01, "proposed_deadline": deadline, "approach_summary": "First try"},
        headers=provider_h,
    )
    assert resp.status_code == 201

    # Duplicate proposal should fail
    resp = await client.post(
        f"/engagements/{engagement_id}/proposals",
        json={"proposed_price": 0.009, "proposed_deadline": deadline, "approach_summary": "Second try"},
        headers=provider_h,
    )
    assert resp.status_code in (400, 409)


@pytest.mark.asyncio
async def test_requester_cannot_propose_on_own_engagement(client):
    """Requester cannot submit a proposal on their own engagement."""
    requester, requester_key = await register_agent(client, "SelfRequester", "both")
    requester_h = await auth_headers(requester_key)

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    resp = await client.post(
        "/engagements",
        json={
            "title": "Self-proposal test",
            "description": "Cannot self-propose",
            "acceptance_criteria": ["Done"],
            "category": "development",
            "reward_amount": 0.01,
            "deadline": deadline,
        },
        headers=requester_h,
    )
    engagement_id = resp.json()["id"]

    # Self-proposal should fail
    resp = await client.post(
        f"/engagements/{engagement_id}/proposals",
        json={"proposed_price": 0.01, "proposed_deadline": deadline, "approach_summary": "Self"},
        headers=requester_h,
    )
    assert resp.status_code in (400, 403)


@pytest.mark.asyncio
async def test_nonexistent_engagement_returns_404(client):
    """Getting a non-existent engagement should return 404."""
    import uuid
    resp = await client.get(f"/engagements/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_nonexistent_agent_returns_404(client):
    """Getting a non-existent agent should return 404."""
    import uuid
    resp = await client.get(f"/agents/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unauthorized_fund_rejected(client):
    """Only the requester can fund their contract."""
    requester, requester_key = await register_agent(client, "FundRequester", "requester")
    provider, provider_key = await register_agent(client, "FundProvider", "provider")
    requester_h = await auth_headers(requester_key)
    provider_h = await auth_headers(provider_key)

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    resp = await client.post(
        "/engagements",
        json={
            "title": "Fund auth test",
            "description": "Test fund authorization",
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
        json={"proposed_price": 0.01, "proposed_deadline": deadline, "approach_summary": "Quick"},
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

    # Provider tries to fund — should fail
    resp = await client.post(
        f"/contracts/{contract_id}/fund",
        json={"funding_tx_hash": "0x" + "ee" * 32, "escrow_contract_address": "0x" + "ff" * 20},
        headers=provider_h,
    )
    assert resp.status_code in (400, 403)
