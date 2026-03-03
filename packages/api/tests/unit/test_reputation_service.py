import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reputation import ReputationEvent, ReputationEventType
from app.services.reputation_service import (
    SCORE_WEIGHTS,
    calculate_score,
    calculate_score_delta,
    get_agent_reputation,
    record_event,
)
from tests.conftest import create_test_agent


class TestScoreCalculation:
    def test_bounty_completed_weight(self):
        assert calculate_score_delta("bounty_completed") == 10.0

    def test_bounty_posted_weight(self):
        assert calculate_score_delta("bounty_posted") == 2.0

    def test_dispute_won_weight(self):
        assert calculate_score_delta("dispute_won") == 5.0

    def test_dispute_lost_weight(self):
        assert calculate_score_delta("dispute_lost") == -10.0

    def test_unknown_event_type_returns_zero(self):
        assert calculate_score_delta("unknown_event") == 0.0


class TestRecordEvent:
    @pytest.mark.asyncio
    async def test_record_bounty_completed_event(self, db_session: AsyncSession):
        agent, _ = await create_test_agent(db_session, name="rep-agent1")

        event = await record_event(
            agent_id=agent.id,
            event_type="bounty_completed",
            db=db_session,
        )

        assert event.event_type == ReputationEventType.bounty_completed
        assert event.score_delta == 10.0
        assert event.agent_id == agent.id

        await db_session.refresh(agent)
        assert agent.reputation_score == 10.0

    @pytest.mark.asyncio
    async def test_record_bounty_posted_event(self, db_session: AsyncSession):
        agent, _ = await create_test_agent(db_session, name="rep-agent2")

        event = await record_event(
            agent_id=agent.id,
            event_type="bounty_posted",
            db=db_session,
        )

        assert event.score_delta == 2.0
        await db_session.refresh(agent)
        assert agent.reputation_score == 2.0

    @pytest.mark.asyncio
    async def test_record_dispute_lost_event(self, db_session: AsyncSession):
        agent, _ = await create_test_agent(db_session, name="rep-agent3")

        event = await record_event(
            agent_id=agent.id,
            event_type="dispute_lost",
            db=db_session,
        )

        assert event.score_delta == -10.0
        await db_session.refresh(agent)
        assert agent.reputation_score == -10.0

    @pytest.mark.asyncio
    async def test_record_event_with_contract_id(self, db_session: AsyncSession):
        agent, _ = await create_test_agent(db_session, name="rep-agent4")
        contract_id = uuid.uuid4()

        event = await record_event(
            agent_id=agent.id,
            event_type="bounty_completed",
            contract_id=contract_id,
            db=db_session,
        )

        # contract_id might not have FK constraint satisfied in test, but the field is set
        assert event.contract_id == contract_id

    @pytest.mark.asyncio
    async def test_multiple_events_accumulate(self, db_session: AsyncSession):
        agent, _ = await create_test_agent(db_session, name="rep-agent5")

        await record_event(agent_id=agent.id, event_type="bounty_completed", db=db_session)
        await record_event(agent_id=agent.id, event_type="bounty_posted", db=db_session)
        await record_event(agent_id=agent.id, event_type="dispute_lost", db=db_session)

        await db_session.refresh(agent)
        # 10 + 2 + (-10) = 2.0
        assert agent.reputation_score == pytest.approx(2.0)


class TestCalculateScore:
    @pytest.mark.asyncio
    async def test_calculate_score_from_events(self, db_session: AsyncSession):
        agent, _ = await create_test_agent(db_session, name="rep-agent6")

        await record_event(agent_id=agent.id, event_type="bounty_completed", db=db_session)
        await record_event(agent_id=agent.id, event_type="bounty_posted", db=db_session)

        score = await calculate_score(agent.id, db_session)
        assert score == pytest.approx(12.0)  # 10 + 2

    @pytest.mark.asyncio
    async def test_calculate_score_no_events(self, db_session: AsyncSession):
        agent, _ = await create_test_agent(db_session, name="rep-agent7")

        score = await calculate_score(agent.id, db_session)
        assert score == 0.0


class TestGetAgentReputation:
    @pytest.mark.asyncio
    async def test_get_reputation_details(self, db_session: AsyncSession):
        agent, _ = await create_test_agent(db_session, name="rep-agent8")
        await record_event(agent_id=agent.id, event_type="bounty_completed", db=db_session)

        result = await get_agent_reputation(agent.id, db_session)

        assert result["agent_id"] == str(agent.id)
        assert result["reputation_score"] == 10.0
        assert result["total_events"] == 1
        assert len(result["recent_events"]) == 1
        assert result["recent_events"][0]["event_type"] == "bounty_completed"

    @pytest.mark.asyncio
    async def test_get_reputation_nonexistent_agent(self, db_session: AsyncSession):
        result = await get_agent_reputation(uuid.uuid4(), db_session)
        assert "error" in result
