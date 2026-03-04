import pytest
from httpx import AsyncClient

from app.auth.api_key import generate_api_key, hash_api_key, verify_api_key
from tests.conftest import create_test_agent


class TestAPIKeyGeneration:
    def test_generate_api_key_returns_string(self):
        key = generate_api_key()
        assert isinstance(key, str)
        assert len(key) > 0

    def test_generate_api_key_has_prefix(self):
        key = generate_api_key()
        assert key.startswith("tec_")

    def test_generate_api_key_unique(self):
        keys = {generate_api_key() for _ in range(100)}
        assert len(keys) == 100


class TestAPIKeyHashing:
    def test_hash_api_key_returns_hex_string(self):
        key = generate_api_key()
        hashed = hash_api_key(key)
        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA-256 hex digest

    def test_hash_api_key_deterministic(self):
        key = generate_api_key()
        hash1 = hash_api_key(key)
        hash2 = hash_api_key(key)
        assert hash1 == hash2

    def test_different_keys_different_hashes(self):
        key1 = generate_api_key()
        key2 = generate_api_key()
        assert hash_api_key(key1) != hash_api_key(key2)


class TestAPIKeyVerification:
    def test_verify_valid_key(self):
        key = generate_api_key()
        hashed = hash_api_key(key)
        assert verify_api_key(key, hashed) is True

    def test_verify_invalid_key(self):
        key = generate_api_key()
        hashed = hash_api_key(key)
        assert verify_api_key("wrong_key", hashed) is False

    def test_verify_wrong_hash(self):
        key = generate_api_key()
        assert verify_api_key(key, "wrong_hash") is False


class TestAPIKeyMiddleware:
    @pytest.mark.asyncio
    async def test_request_without_api_key_returns_422(self, client: AsyncClient):
        """Request without X-API-Key header should fail with 422 (missing header)."""
        response = await client.post("/engagements", json={
            "title": "Test",
            "description": "Test desc",
            "acceptance_criteria": ["criterion"],
            "category": "test",
            "reward_amount": 1.0,
            "deadline": "2099-01-01T00:00:00Z",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_request_with_invalid_api_key_returns_401(self, client: AsyncClient):
        """Request with invalid X-API-Key should return 401."""
        response = await client.post(
            "/engagements",
            json={
                "title": "Test",
                "description": "Test desc",
                "acceptance_criteria": ["criterion"],
                "category": "test",
                "reward_amount": 1.0,
                "deadline": "2099-01-01T00:00:00Z",
            },
            headers={"X-API-Key": "invalid_key_here"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_request_with_valid_api_key_succeeds(self, client: AsyncClient, db_session):
        """Request with valid X-API-Key should succeed."""
        agent, api_key = await create_test_agent(db_session, name="auth-test-agent")
        await db_session.commit()

        response = await client.post(
            "/engagements",
            json={
                "title": "Test Engagement",
                "description": "Test description",
                "acceptance_criteria": ["criterion"],
                "category": "test",
                "reward_amount": 1.0,
                "deadline": "2099-01-01T00:00:00Z",
            },
            headers={"X-API-Key": api_key},
        )
        assert response.status_code == 201
