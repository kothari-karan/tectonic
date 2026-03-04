"""Tests for Standing Agreement CRUD and task dispatch."""

import uuid
from datetime import datetime, timezone, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_agent


def _future_date(days: int = 30) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


class TestCreateAgreement:
    @pytest.mark.asyncio
    async def test_create_agreement_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, req_key = await create_test_agent(db_session, name="ag-req1")
        provider, _ = await create_test_agent(db_session, name="ag-prov1")
        await db_session.commit()

        response = await client.post(
            "/agreements",
            json={
                "provider_id": str(provider.id),
                "title": "Monthly retainer",
                "scope_description": "Frontend development work",
                "rate_type": "retainer_monthly",
                "rate": 5000.0,
                "max_tasks_per_period": 10,
                "start_date": _future_date(1),
            },
            headers={"X-API-Key": req_key},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Monthly retainer"
        assert data["status"] == "active"
        assert data["requester_id"] == str(requester.id)
        assert data["provider_id"] == str(provider.id)
        assert data["rate"] == 5000.0

    @pytest.mark.asyncio
    async def test_self_agreement_fails(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        agent, key = await create_test_agent(db_session, name="ag-self1")
        await db_session.commit()

        response = await client.post(
            "/agreements",
            json={
                "provider_id": str(agent.id),
                "title": "Self agreement",
                "scope_description": "Nope",
                "rate_type": "per_task",
                "rate": 100.0,
                "start_date": _future_date(1),
            },
            headers={"X-API-Key": key},
        )
        assert response.status_code == 400
        assert "yourself" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_nonexistent_provider_fails(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        requester, key = await create_test_agent(db_session, name="ag-req2")
        await db_session.commit()

        response = await client.post(
            "/agreements",
            json={
                "provider_id": str(uuid.uuid4()),
                "title": "Bad agreement",
                "scope_description": "Provider doesn't exist",
                "rate_type": "hourly",
                "rate": 50.0,
                "start_date": _future_date(1),
            },
            headers={"X-API-Key": key},
        )
        assert response.status_code == 404


class TestListAgreements:
    @pytest.mark.asyncio
    async def test_list_all(self, client: AsyncClient, db_session: AsyncSession):
        req, req_key = await create_test_agent(db_session, name="ag-req3")
        prov, _ = await create_test_agent(db_session, name="ag-prov3")
        await db_session.commit()

        await client.post(
            "/agreements",
            json={
                "provider_id": str(prov.id),
                "title": "Agreement 1",
                "scope_description": "Scope 1",
                "rate_type": "per_task",
                "rate": 100.0,
                "start_date": _future_date(1),
            },
            headers={"X-API-Key": req_key},
        )
        await client.post(
            "/agreements",
            json={
                "provider_id": str(prov.id),
                "title": "Agreement 2",
                "scope_description": "Scope 2",
                "rate_type": "hourly",
                "rate": 50.0,
                "start_date": _future_date(1),
            },
            headers={"X-API-Key": req_key},
        )

        response = await client.get("/agreements")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_list_by_agent(self, client: AsyncClient, db_session: AsyncSession):
        req1, req1_key = await create_test_agent(db_session, name="ag-req4a")
        req2, req2_key = await create_test_agent(db_session, name="ag-req4b")
        prov, _ = await create_test_agent(db_session, name="ag-prov4")
        await db_session.commit()

        await client.post(
            "/agreements",
            json={
                "provider_id": str(prov.id),
                "title": "Req1 agreement",
                "scope_description": "Scope",
                "rate_type": "per_task",
                "rate": 100.0,
                "start_date": _future_date(1),
            },
            headers={"X-API-Key": req1_key},
        )
        await client.post(
            "/agreements",
            json={
                "provider_id": str(prov.id),
                "title": "Req2 agreement",
                "scope_description": "Scope",
                "rate_type": "per_task",
                "rate": 200.0,
                "start_date": _future_date(1),
            },
            headers={"X-API-Key": req2_key},
        )

        # Filter by req1
        response = await client.get(f"/agreements?agent_id={req1.id}")
        assert response.json()["total"] == 1


class TestUpdateAgreement:
    @pytest.mark.asyncio
    async def test_pause_agreement(self, client: AsyncClient, db_session: AsyncSession):
        req, req_key = await create_test_agent(db_session, name="ag-req5")
        prov, _ = await create_test_agent(db_session, name="ag-prov5")
        await db_session.commit()

        r = await client.post(
            "/agreements",
            json={
                "provider_id": str(prov.id),
                "title": "Pausable",
                "scope_description": "Scope",
                "rate_type": "retainer_monthly",
                "rate": 3000.0,
                "start_date": _future_date(1),
            },
            headers={"X-API-Key": req_key},
        )
        agreement_id = r.json()["id"]

        response = await client.patch(
            f"/agreements/{agreement_id}",
            json={"status": "paused"},
            headers={"X-API-Key": req_key},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "paused"

    @pytest.mark.asyncio
    async def test_outsider_cannot_update(self, client: AsyncClient, db_session: AsyncSession):
        req, req_key = await create_test_agent(db_session, name="ag-req6")
        prov, _ = await create_test_agent(db_session, name="ag-prov6")
        outsider, outsider_key = await create_test_agent(db_session, name="ag-out6")
        await db_session.commit()

        r = await client.post(
            "/agreements",
            json={
                "provider_id": str(prov.id),
                "title": "Private",
                "scope_description": "Scope",
                "rate_type": "per_task",
                "rate": 100.0,
                "start_date": _future_date(1),
            },
            headers={"X-API-Key": req_key},
        )
        agreement_id = r.json()["id"]

        response = await client.patch(
            f"/agreements/{agreement_id}",
            json={"status": "terminated"},
            headers={"X-API-Key": outsider_key},
        )
        assert response.status_code == 403


class TestDispatchTask:
    @pytest.mark.asyncio
    async def test_dispatch_creates_engagement(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        req, req_key = await create_test_agent(db_session, name="ag-req7")
        prov, _ = await create_test_agent(db_session, name="ag-prov7")
        await db_session.commit()

        r = await client.post(
            "/agreements",
            json={
                "provider_id": str(prov.id),
                "title": "Dev retainer",
                "scope_description": "Frontend work",
                "rate_type": "per_task",
                "rate": 500.0,
                "start_date": _future_date(1),
            },
            headers={"X-API-Key": req_key},
        )
        agreement_id = r.json()["id"]

        response = await client.post(
            f"/agreements/{agreement_id}/tasks",
            json={
                "title": "Fix login bug",
                "description": "Login form doesn't validate email",
                "reward_amount": 200.0,
            },
            headers={"X-API-Key": req_key},
        )
        assert response.status_code == 201
        task = response.json()
        assert task["agreement_id"] == agreement_id
        assert task["engagement_id"] is not None

        # Verify the engagement was created as in_progress (skips negotiation)
        eng_response = await client.get(
            f"/engagements/{task['engagement_id']}",
            headers={"X-API-Key": req_key},
        )
        assert eng_response.status_code == 200
        eng = eng_response.json()
        assert eng["status"] == "in_progress"
        assert eng["engagement_type"] == "direct"
        assert str(prov.id) in eng["target_provider_ids"]

    @pytest.mark.asyncio
    async def test_provider_cannot_dispatch(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        req, req_key = await create_test_agent(db_session, name="ag-req8")
        prov, prov_key = await create_test_agent(db_session, name="ag-prov8")
        await db_session.commit()

        r = await client.post(
            "/agreements",
            json={
                "provider_id": str(prov.id),
                "title": "Retainer",
                "scope_description": "Scope",
                "rate_type": "per_task",
                "rate": 100.0,
                "start_date": _future_date(1),
            },
            headers={"X-API-Key": req_key},
        )
        agreement_id = r.json()["id"]

        response = await client.post(
            f"/agreements/{agreement_id}/tasks",
            json={
                "title": "Task",
                "description": "Desc",
                "reward_amount": 50.0,
            },
            headers={"X-API-Key": prov_key},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_dispatch_on_paused_agreement_fails(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        req, req_key = await create_test_agent(db_session, name="ag-req9")
        prov, _ = await create_test_agent(db_session, name="ag-prov9")
        await db_session.commit()

        r = await client.post(
            "/agreements",
            json={
                "provider_id": str(prov.id),
                "title": "Paused retainer",
                "scope_description": "Scope",
                "rate_type": "per_task",
                "rate": 100.0,
                "start_date": _future_date(1),
            },
            headers={"X-API-Key": req_key},
        )
        agreement_id = r.json()["id"]

        # Pause it
        await client.patch(
            f"/agreements/{agreement_id}",
            json={"status": "paused"},
            headers={"X-API-Key": req_key},
        )

        response = await client.post(
            f"/agreements/{agreement_id}/tasks",
            json={
                "title": "Task",
                "description": "Desc",
                "reward_amount": 50.0,
            },
            headers={"X-API-Key": req_key},
        )
        assert response.status_code == 400
        assert "not active" in response.json()["detail"]
