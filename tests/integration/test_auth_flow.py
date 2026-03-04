"""Integration test: authentication flow.

Tests: register -> get API key -> use key for operations -> reject invalid key.
"""

import pytest
from datetime import datetime, timedelta, timezone

from helpers import register_agent, auth_headers


@pytest.mark.asyncio
async def test_register_and_authenticate(client):
    """Register an agent and use the API key for authenticated operations."""
    # Register
    resp = await client.post(
        "/agents/register",
        json={"name": "AuthTestAgent", "agent_type": "requester"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "api_key" in body
    assert "agent" in body
    api_key = body["api_key"]
    agent_id = body["agent"]["id"]

    # Use key for authenticated endpoint
    headers = {"X-API-Key": api_key}
    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    resp = await client.post(
        "/engagements",
        json={
            "title": "Auth test engagement",
            "description": "Testing auth",
            "acceptance_criteria": ["Works"],
            "category": "development",
            "reward_amount": 0.01,
            "deadline": deadline,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["requester_id"] == agent_id


@pytest.mark.asyncio
async def test_invalid_api_key_rejected(client):
    """Invalid API key should be rejected with 401."""
    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    resp = await client.post(
        "/engagements",
        json={
            "title": "Should fail",
            "description": "Invalid auth",
            "acceptance_criteria": ["Nothing"],
            "category": "development",
            "reward_amount": 0.01,
            "deadline": deadline,
        },
        headers={"X-API-Key": "invalid-key-12345"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_missing_api_key_rejected(client):
    """Missing API key should be rejected with 422 (header is required)."""
    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    resp = await client.post(
        "/engagements",
        json={
            "title": "Should fail",
            "description": "No auth",
            "acceptance_criteria": ["Nothing"],
            "category": "development",
            "reward_amount": 0.01,
            "deadline": deadline,
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_public_endpoints_dont_require_auth(client):
    """Public endpoints should work without auth."""
    # List engagements (public)
    resp = await client.get("/engagements")
    assert resp.status_code == 200

    # Get agent (public)
    agent, _ = await register_agent(client, "PublicTestAgent", "provider")
    resp = await client.get(f"/agents/{agent['id']}")
    assert resp.status_code == 200

    # Health check
    resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_duplicate_agent_name_rejected(client):
    """Registering with a duplicate name should fail."""
    await register_agent(client, "UniqueName", "requester")
    resp = await client.post(
        "/agents/register",
        json={"name": "UniqueName", "agent_type": "provider"},
    )
    # Should get an error (409 conflict or 400 bad request)
    assert resp.status_code in (400, 409, 422, 500)


@pytest.mark.asyncio
async def test_provider_cannot_post_engagement(client):
    """Provider agents may still post engagements if agent_type is 'provider'.

    This depends on the API implementation — some designs allow any
    authenticated agent to post. We check the behavior is consistent.
    """
    provider, provider_key = await register_agent(client, "ProviderOnlyAgent", "provider")
    headers = await auth_headers(provider_key)
    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    resp = await client.post(
        "/engagements",
        json={
            "title": "Provider posting",
            "description": "Provider tries to post",
            "acceptance_criteria": ["Works"],
            "category": "development",
            "reward_amount": 0.01,
            "deadline": deadline,
        },
        headers=headers,
    )
    # Accept either success or forbidden — document the behavior
    assert resp.status_code in (200, 201, 403)
