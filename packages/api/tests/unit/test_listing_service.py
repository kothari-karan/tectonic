"""Tests for Service Listing CRUD and engage-from-listing flow."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import ListingAvailability, RateType
from tests.conftest import create_test_agent


class TestCreateListing:
    @pytest.mark.asyncio
    async def test_create_listing_success(self, client: AsyncClient, db_session: AsyncSession):
        provider, key = await create_test_agent(db_session, name="ls-prov1")
        await db_session.commit()

        response = await client.post(
            "/listings",
            json={
                "title": "Full-stack development",
                "description": "I build web apps with React and Python",
                "capabilities": ["react", "python", "postgres"],
                "rate_type": "hourly",
                "rate_range_min": 50.0,
                "rate_range_max": 150.0,
                "response_time_hours": 4,
            },
            headers={"X-API-Key": key},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Full-stack development"
        assert data["rate_type"] == "hourly"
        assert data["availability"] == "available"
        assert data["provider_id"] == str(provider.id)
        assert len(data["capabilities"]) == 3

    @pytest.mark.asyncio
    async def test_create_listing_invalid_rate_range(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        provider, key = await create_test_agent(db_session, name="ls-prov2")
        await db_session.commit()

        response = await client.post(
            "/listings",
            json={
                "title": "Bad listing",
                "description": "Rate range is inverted",
                "capabilities": ["testing"],
                "rate_type": "fixed",
                "rate_range_min": 200.0,
                "rate_range_max": 100.0,
            },
            headers={"X-API-Key": key},
        )
        assert response.status_code == 400
        assert "rate_range_min" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_listing_requires_auth(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        response = await client.post(
            "/listings",
            json={
                "title": "Unauthorized",
                "description": "No API key",
                "capabilities": ["testing"],
                "rate_type": "fixed",
                "rate_range_min": 10.0,
                "rate_range_max": 20.0,
            },
        )
        assert response.status_code in (401, 422)


class TestListListings:
    @pytest.mark.asyncio
    async def test_list_all(self, client: AsyncClient, db_session: AsyncSession):
        p1, k1 = await create_test_agent(db_session, name="ls-prov3a")
        p2, k2 = await create_test_agent(db_session, name="ls-prov3b")
        await db_session.commit()

        await client.post(
            "/listings",
            json={
                "title": "Listing A",
                "description": "Desc A",
                "capabilities": ["react"],
                "rate_type": "hourly",
                "rate_range_min": 50.0,
                "rate_range_max": 100.0,
            },
            headers={"X-API-Key": k1},
        )
        await client.post(
            "/listings",
            json={
                "title": "Listing B",
                "description": "Desc B",
                "capabilities": ["python"],
                "rate_type": "fixed",
                "rate_range_min": 100.0,
                "rate_range_max": 500.0,
            },
            headers={"X-API-Key": k2},
        )

        response = await client.get("/listings")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["listings"]) == 2

    @pytest.mark.asyncio
    async def test_list_filter_by_availability(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        provider, key = await create_test_agent(db_session, name="ls-prov4")
        await db_session.commit()

        # Create a listing
        r = await client.post(
            "/listings",
            json={
                "title": "Available listing",
                "description": "Desc",
                "capabilities": ["testing"],
                "rate_type": "hourly",
                "rate_range_min": 10.0,
                "rate_range_max": 20.0,
            },
            headers={"X-API-Key": key},
        )
        listing_id = r.json()["id"]

        # Set to busy
        await client.patch(
            f"/listings/{listing_id}",
            json={"availability": "busy"},
            headers={"X-API-Key": key},
        )

        # Filter for available only
        response = await client.get("/listings?availability=available")
        assert response.json()["total"] == 0

        # Filter for busy
        response = await client.get("/listings?availability=busy")
        data = response.json()
        assert data["total"] == 1


class TestGetListing:
    @pytest.mark.asyncio
    async def test_get_listing_success(self, client: AsyncClient, db_session: AsyncSession):
        provider, key = await create_test_agent(db_session, name="ls-prov5")
        await db_session.commit()

        r = await client.post(
            "/listings",
            json={
                "title": "My Service",
                "description": "Expert service",
                "capabilities": ["design"],
                "rate_type": "per_deliverable",
                "rate_range_min": 200.0,
                "rate_range_max": 1000.0,
            },
            headers={"X-API-Key": key},
        )
        listing_id = r.json()["id"]

        response = await client.get(f"/listings/{listing_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "My Service"

    @pytest.mark.asyncio
    async def test_get_nonexistent_listing(self, client: AsyncClient, db_session: AsyncSession):
        fake_id = uuid.uuid4()
        response = await client.get(f"/listings/{fake_id}")
        assert response.status_code == 404


class TestUpdateListing:
    @pytest.mark.asyncio
    async def test_update_availability(self, client: AsyncClient, db_session: AsyncSession):
        provider, key = await create_test_agent(db_session, name="ls-prov6")
        await db_session.commit()

        r = await client.post(
            "/listings",
            json={
                "title": "Service",
                "description": "Desc",
                "capabilities": ["testing"],
                "rate_type": "hourly",
                "rate_range_min": 10.0,
                "rate_range_max": 20.0,
            },
            headers={"X-API-Key": key},
        )
        listing_id = r.json()["id"]

        response = await client.patch(
            f"/listings/{listing_id}",
            json={"availability": "unavailable"},
            headers={"X-API-Key": key},
        )
        assert response.status_code == 200
        assert response.json()["availability"] == "unavailable"

    @pytest.mark.asyncio
    async def test_non_owner_cannot_update(self, client: AsyncClient, db_session: AsyncSession):
        owner, owner_key = await create_test_agent(db_session, name="ls-prov7a")
        other, other_key = await create_test_agent(db_session, name="ls-prov7b")
        await db_session.commit()

        r = await client.post(
            "/listings",
            json={
                "title": "Owner's Service",
                "description": "Desc",
                "capabilities": ["testing"],
                "rate_type": "hourly",
                "rate_range_min": 10.0,
                "rate_range_max": 20.0,
            },
            headers={"X-API-Key": owner_key},
        )
        listing_id = r.json()["id"]

        response = await client.patch(
            f"/listings/{listing_id}",
            json={"availability": "unavailable"},
            headers={"X-API-Key": other_key},
        )
        assert response.status_code == 403


class TestEngageFromListing:
    @pytest.mark.asyncio
    async def test_engage_creates_direct_engagement(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        provider, prov_key = await create_test_agent(db_session, name="ls-prov8")
        requester, req_key = await create_test_agent(db_session, name="ls-req8")
        await db_session.commit()

        # Provider creates listing
        r = await client.post(
            "/listings",
            json={
                "title": "Logo Design",
                "description": "I design logos",
                "capabilities": ["design", "branding"],
                "rate_type": "fixed",
                "rate_range_min": 100.0,
                "rate_range_max": 500.0,
            },
            headers={"X-API-Key": prov_key},
        )
        listing_id = r.json()["id"]

        # Requester engages from listing
        response = await client.post(
            f"/listings/{listing_id}/engage?title=Need%20a%20logo&description=Company%20logo&reward_amount=300",
            headers={"X-API-Key": req_key},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["engagement_type"] == "direct"
        assert str(provider.id) in data["target_provider_ids"]
        assert data["requester_id"] == str(requester.id)
        assert data["reward_amount"] == 300.0

    @pytest.mark.asyncio
    async def test_engage_own_listing_fails(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        provider, key = await create_test_agent(db_session, name="ls-prov9")
        await db_session.commit()

        r = await client.post(
            "/listings",
            json={
                "title": "Service",
                "description": "Desc",
                "capabilities": ["testing"],
                "rate_type": "hourly",
                "rate_range_min": 10.0,
                "rate_range_max": 20.0,
            },
            headers={"X-API-Key": key},
        )
        listing_id = r.json()["id"]

        response = await client.post(
            f"/listings/{listing_id}/engage?title=Self&description=Self&reward_amount=100",
            headers={"X-API-Key": key},
        )
        assert response.status_code == 400
        assert "own listing" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_engage_unavailable_listing_fails(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        provider, prov_key = await create_test_agent(db_session, name="ls-prov10")
        requester, req_key = await create_test_agent(db_session, name="ls-req10")
        await db_session.commit()

        r = await client.post(
            "/listings",
            json={
                "title": "Service",
                "description": "Desc",
                "capabilities": ["testing"],
                "rate_type": "hourly",
                "rate_range_min": 10.0,
                "rate_range_max": 20.0,
            },
            headers={"X-API-Key": prov_key},
        )
        listing_id = r.json()["id"]

        # Set to unavailable
        await client.patch(
            f"/listings/{listing_id}",
            json={"availability": "unavailable"},
            headers={"X-API-Key": prov_key},
        )

        response = await client.post(
            f"/listings/{listing_id}/engage?title=Task&description=Desc&reward_amount=100",
            headers={"X-API-Key": req_key},
        )
        assert response.status_code == 400
        assert "not currently available" in response.json()["detail"]
