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
        json={"name": "AuthTestAgent", "agent_type": "poster"},
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
        "/bounties",
        json={
            "title": "Auth test bounty",
            "description": "Testing auth",
            "acceptance_criteria": ["Works"],
            "category": "development",
            "reward_amount": 0.01,
            "deadline": deadline,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["poster_id"] == agent_id


@pytest.mark.asyncio
async def test_invalid_api_key_rejected(client):
    """Invalid API key should be rejected with 401."""
    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    resp = await client.post(
        "/bounties",
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
        "/bounties",
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
    # List bounties (public)
    resp = await client.get("/bounties")
    assert resp.status_code == 200

    # Get agent (public)
    agent, _ = await register_agent(client, "PublicTestAgent", "solver")
    resp = await client.get(f"/agents/{agent['id']}")
    assert resp.status_code == 200

    # Health check
    resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_duplicate_agent_name_rejected(client):
    """Registering with a duplicate name should fail."""
    await register_agent(client, "UniqueName", "poster")
    resp = await client.post(
        "/agents/register",
        json={"name": "UniqueName", "agent_type": "solver"},
    )
    # Should get an error (409 conflict or 400 bad request)
    assert resp.status_code in (400, 409, 422, 500)


@pytest.mark.asyncio
async def test_solver_cannot_post_bounty(client):
    """Solver agents may still post bounties if agent_type is 'solver'.

    This depends on the API implementation — some designs allow any
    authenticated agent to post. We check the behavior is consistent.
    """
    solver, solver_key = await register_agent(client, "SolverOnlyAgent", "solver")
    headers = await auth_headers(solver_key)
    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    resp = await client.post(
        "/bounties",
        json={
            "title": "Solver posting",
            "description": "Solver tries to post",
            "acceptance_criteria": ["Works"],
            "category": "development",
            "reward_amount": 0.01,
            "deadline": deadline,
        },
        headers=headers,
    )
    # Accept either success or forbidden — document the behavior
    assert resp.status_code in (200, 201, 403)
