import uuid
from datetime import datetime, timezone, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bounty import EngagementStatus
from app.models.negotiation import NegotiationStatus
from app.schemas.negotiation import NegotiationTerms, NegotiationTurnRequest
from app.services.negotiation_engine import validate_turn, process_turn
from tests.conftest import (
    create_test_agent,
    create_test_engagement,
    create_test_negotiation,
    create_test_proposal,
)


def make_terms() -> NegotiationTerms:
    """Helper to create valid negotiation terms."""
    return NegotiationTerms(
        price=1.0,
        deadline=datetime.now(timezone.utc) + timedelta(days=5),
        deliverables=["deliverable 1"],
        acceptance_criteria=["criterion 1"],
        revision_rounds=1,
    )


class TestValidateTurn:
    @pytest.mark.asyncio
    async def test_inactive_negotiation_rejected(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="requester", agent_type="requester")
        provider, _ = await create_test_agent(db_session, name="provider", agent_type="provider")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider,
            status=NegotiationStatus.agreed,
        )

        request = NegotiationTurnRequest(turn_type="offer", proposed_terms=make_terms())
        with pytest.raises(HTTPException) as exc_info:
            validate_turn(negotiation, request, requester.id)
        assert exc_info.value.status_code == 400
        assert "not active" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_non_participant_rejected(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="requester2")
        provider, _ = await create_test_agent(db_session, name="provider2")
        outsider, _ = await create_test_agent(db_session, name="outsider")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider,
        )

        request = NegotiationTurnRequest(turn_type="offer", proposed_terms=make_terms())
        with pytest.raises(HTTPException) as exc_info:
            validate_turn(negotiation, request, outsider.id)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_wrong_turn_requester(self, db_session: AsyncSession):
        """Provider tries to go when it's requester's turn (turn_count=0)."""
        requester, _ = await create_test_agent(db_session, name="requester3")
        provider, _ = await create_test_agent(db_session, name="provider3")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider, turn_count=0,
        )

        request = NegotiationTurnRequest(turn_type="offer", proposed_terms=make_terms())
        with pytest.raises(HTTPException) as exc_info:
            validate_turn(negotiation, request, provider.id)
        assert exc_info.value.status_code == 400
        assert "requester's turn" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_wrong_turn_provider(self, db_session: AsyncSession):
        """Requester tries to go when it's provider's turn (turn_count=1)."""
        requester, _ = await create_test_agent(db_session, name="requester4")
        provider, _ = await create_test_agent(db_session, name="provider4")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider, turn_count=1,
        )

        request = NegotiationTurnRequest(turn_type="counter", proposed_terms=make_terms())
        with pytest.raises(HTTPException) as exc_info:
            validate_turn(negotiation, request, requester.id)
        assert exc_info.value.status_code == 400
        assert "provider's turn" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_offer_without_terms_rejected(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="requester5")
        provider, _ = await create_test_agent(db_session, name="provider5")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider,
        )

        request = NegotiationTurnRequest(turn_type="offer")
        with pytest.raises(HTTPException) as exc_info:
            validate_turn(negotiation, request, requester.id)
        assert exc_info.value.status_code == 400
        assert "requires proposed_terms" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_counter_without_terms_rejected(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="requester6")
        provider, _ = await create_test_agent(db_session, name="provider6")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider, turn_count=1,
        )

        request = NegotiationTurnRequest(turn_type="counter")
        with pytest.raises(HTTPException) as exc_info:
            validate_turn(negotiation, request, provider.id)
        assert exc_info.value.status_code == 400
        assert "requires proposed_terms" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_accept_with_terms_rejected(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="requester7")
        provider, _ = await create_test_agent(db_session, name="provider7")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider, turn_count=1,
        )

        request = NegotiationTurnRequest(
            turn_type="accept", proposed_terms=make_terms()
        )
        with pytest.raises(HTTPException) as exc_info:
            validate_turn(negotiation, request, provider.id)
        assert exc_info.value.status_code == 400
        assert "must not include" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_max_turns_limit(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="requester8")
        provider, _ = await create_test_agent(db_session, name="provider8")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider, turn_count=10,
        )

        request = NegotiationTurnRequest(turn_type="offer", proposed_terms=make_terms())
        with pytest.raises(HTTPException) as exc_info:
            validate_turn(negotiation, request, requester.id)
        assert exc_info.value.status_code == 400
        assert "Maximum turns" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_first_turn_must_be_offer(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="requester9")
        provider, _ = await create_test_agent(db_session, name="provider9")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider, turn_count=0,
        )

        request = NegotiationTurnRequest(turn_type="accept")
        with pytest.raises(HTTPException) as exc_info:
            validate_turn(negotiation, request, requester.id)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_valid_offer_passes(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="requester10")
        provider, _ = await create_test_agent(db_session, name="provider10")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider,
        )

        request = NegotiationTurnRequest(turn_type="offer", proposed_terms=make_terms())
        # Should not raise
        validate_turn(negotiation, request, requester.id)

    @pytest.mark.asyncio
    async def test_valid_counter_passes(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="requester11")
        provider, _ = await create_test_agent(db_session, name="provider11")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider, turn_count=1,
        )

        request = NegotiationTurnRequest(turn_type="counter", proposed_terms=make_terms())
        validate_turn(negotiation, request, provider.id)

    @pytest.mark.asyncio
    async def test_valid_accept_passes(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="requester12")
        provider, _ = await create_test_agent(db_session, name="provider12")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider, turn_count=1,
        )

        request = NegotiationTurnRequest(turn_type="accept")
        validate_turn(negotiation, request, provider.id)

    @pytest.mark.asyncio
    async def test_valid_reject_passes(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="requester13")
        provider, _ = await create_test_agent(db_session, name="provider13")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider, turn_count=1,
        )

        request = NegotiationTurnRequest(turn_type="reject")
        validate_turn(negotiation, request, provider.id)


class TestProcessTurn:
    @pytest.mark.asyncio
    async def test_process_offer_creates_turn(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="pt-requester1")
        provider, _ = await create_test_agent(db_session, name="pt-provider1")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider,
        )

        request = NegotiationTurnRequest(turn_type="offer", proposed_terms=make_terms())
        turn = await process_turn(negotiation, request, requester.id, db_session)

        assert turn.sequence == 0
        assert turn.turn_type.value == "offer"
        assert turn.proposed_terms is not None
        assert negotiation.turn_count == 1
        assert negotiation.current_terms is not None

    @pytest.mark.asyncio
    async def test_process_counter_updates_terms(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="pt-requester2")
        provider, _ = await create_test_agent(db_session, name="pt-provider2")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider, turn_count=1,
            current_terms={"price": 1.0},
        )

        new_terms = make_terms()
        new_terms.price = 0.8
        request = NegotiationTurnRequest(turn_type="counter", proposed_terms=new_terms)
        turn = await process_turn(negotiation, request, provider.id, db_session)

        assert turn.sequence == 1
        assert negotiation.current_terms["price"] == 0.8

    @pytest.mark.asyncio
    async def test_process_accept_sets_agreed(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="pt-requester3")
        provider, _ = await create_test_agent(db_session, name="pt-provider3")
        engagement = await create_test_engagement(db_session, requester, status=EngagementStatus.negotiating)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider, turn_count=1,
            current_terms={"price": 1.0},
        )

        request = NegotiationTurnRequest(turn_type="accept")
        turn = await process_turn(negotiation, request, provider.id, db_session)

        assert negotiation.status == NegotiationStatus.agreed
        await db_session.refresh(engagement)
        assert engagement.status == EngagementStatus.agreed

    @pytest.mark.asyncio
    async def test_process_reject_sets_rejected(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="pt-requester4")
        provider, _ = await create_test_agent(db_session, name="pt-provider4")
        engagement = await create_test_engagement(db_session, requester, status=EngagementStatus.negotiating)
        engagement.provider_id = provider.id
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider, turn_count=1,
            current_terms={"price": 1.0},
        )

        request = NegotiationTurnRequest(turn_type="reject")
        turn = await process_turn(negotiation, request, provider.id, db_session)

        assert negotiation.status == NegotiationStatus.rejected
        await db_session.refresh(engagement)
        assert engagement.status == EngagementStatus.open
        assert engagement.provider_id is None

    @pytest.mark.asyncio
    async def test_alternating_turns(self, db_session: AsyncSession):
        """Test a full offer -> counter -> accept sequence."""
        requester, _ = await create_test_agent(db_session, name="pt-requester5")
        provider, _ = await create_test_agent(db_session, name="pt-provider5")
        engagement = await create_test_engagement(db_session, requester, status=EngagementStatus.negotiating)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider,
        )

        # Turn 0: Requester offers
        offer_req = NegotiationTurnRequest(turn_type="offer", proposed_terms=make_terms())
        turn0 = await process_turn(negotiation, offer_req, requester.id, db_session)
        assert turn0.sequence == 0
        assert negotiation.turn_count == 1

        # Turn 1: Provider counters
        counter_terms = make_terms()
        counter_terms.price = 0.75
        counter_req = NegotiationTurnRequest(turn_type="counter", proposed_terms=counter_terms)
        turn1 = await process_turn(negotiation, counter_req, provider.id, db_session)
        assert turn1.sequence == 1
        assert negotiation.turn_count == 2

        # Turn 2: Requester accepts
        accept_req = NegotiationTurnRequest(turn_type="accept")
        turn2 = await process_turn(negotiation, accept_req, requester.id, db_session)
        assert turn2.sequence == 2
        assert negotiation.status == NegotiationStatus.agreed
