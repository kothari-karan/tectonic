"""Shared test helper functions."""

from httpx import AsyncClient


async def register_agent(client: AsyncClient, name: str, agent_type: str = "requester", **kwargs):
    """Helper to register an agent and return (agent_data, api_key)."""
    data = {"name": name, "agent_type": agent_type, **kwargs}
    resp = await client.post("/agents/register", json=data)
    assert resp.status_code in (200, 201), f"Registration failed: {resp.text}"
    body = resp.json()
    return body["agent"], body["api_key"]


async def auth_headers(api_key: str) -> dict:
    return {"X-API-Key": api_key}
