import uuid
from datetime import datetime, timezone, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bounty import BountyStatus
from app.models.negotiation import NegotiationStatus
from app.schemas.negotiation import NegotiationTerms, NegotiationTurnRequest
from app.services.negotiation_engine import validate_turn, process_turn
from tests.conftest import (
    create_test_agent,
    create_test_bounty,
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
        poster, _ = await create_test_agent(db_session, name="poster", agent_type="poster")
        solver, _ = await create_test_agent(db_session, name="solver", agent_type="solver")
        bounty = await create_test_bounty(db_session, poster)
        proposal = await create_test_proposal(db_session, bounty, solver)
        negotiation = await create_test_negotiation(
            db_session, bounty, proposal, poster, solver,
            status=NegotiationStatus.agreed,
        )

        request = NegotiationTurnRequest(turn_type="offer", proposed_terms=make_terms())
        with pytest.raises(HTTPException) as exc_info:
            validate_turn(negotiation, request, poster.id)
        assert exc_info.value.status_code == 400
        assert "not active" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_non_participant_rejected(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="poster2")
        solver, _ = await create_test_agent(db_session, name="solver2")
        outsider, _ = await create_test_agent(db_session, name="outsider")
        bounty = await create_test_bounty(db_session, poster)
        proposal = await create_test_proposal(db_session, bounty, solver)
        negotiation = await create_test_negotiation(
            db_session, bounty, proposal, poster, solver,
        )

        request = NegotiationTurnRequest(turn_type="offer", proposed_terms=make_terms())
        with pytest.raises(HTTPException) as exc_info:
            validate_turn(negotiation, request, outsider.id)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_wrong_turn_poster(self, db_session: AsyncSession):
        """Solver tries to go when it's poster's turn (turn_count=0)."""
        poster, _ = await create_test_agent(db_session, name="poster3")
        solver, _ = await create_test_agent(db_session, name="solver3")
        bounty = await create_test_bounty(db_session, poster)
        proposal = await create_test_proposal(db_session, bounty, solver)
        negotiation = await create_test_negotiation(
            db_session, bounty, proposal, poster, solver, turn_count=0,
        )

        request = NegotiationTurnRequest(turn_type="offer", proposed_terms=make_terms())
        with pytest.raises(HTTPException) as exc_info:
            validate_turn(negotiation, request, solver.id)
        assert exc_info.value.status_code == 400
        assert "poster's turn" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_wrong_turn_solver(self, db_session: AsyncSession):
        """Poster tries to go when it's solver's turn (turn_count=1)."""
        poster, _ = await create_test_agent(db_session, name="poster4")
        solver, _ = await create_test_agent(db_session, name="solver4")
        bounty = await create_test_bounty(db_session, poster)
        proposal = await create_test_proposal(db_session, bounty, solver)
        negotiation = await create_test_negotiation(
            db_session, bounty, proposal, poster, solver, turn_count=1,
        )

        request = NegotiationTurnRequest(turn_type="counter", proposed_terms=make_terms())
        with pytest.raises(HTTPException) as exc_info:
            validate_turn(negotiation, request, poster.id)
        assert exc_info.value.status_code == 400
        assert "solver's turn" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_offer_without_terms_rejected(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="poster5")
        solver, _ = await create_test_agent(db_session, name="solver5")
        bounty = await create_test_bounty(db_session, poster)
        proposal = await create_test_proposal(db_session, bounty, solver)
        negotiation = await create_test_negotiation(
            db_session, bounty, proposal, poster, solver,
        )

        request = NegotiationTurnRequest(turn_type="offer")
        with pytest.raises(HTTPException) as exc_info:
            validate_turn(negotiation, request, poster.id)
        assert exc_info.value.status_code == 400
        assert "requires proposed_terms" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_counter_without_terms_rejected(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="poster6")
        solver, _ = await create_test_agent(db_session, name="solver6")
        bounty = await create_test_bounty(db_session, poster)
        proposal = await create_test_proposal(db_session, bounty, solver)
        negotiation = await create_test_negotiation(
            db_session, bounty, proposal, poster, solver, turn_count=1,
        )

        request = NegotiationTurnRequest(turn_type="counter")
        with pytest.raises(HTTPException) as exc_info:
            validate_turn(negotiation, request, solver.id)
        assert exc_info.value.status_code == 400
        assert "requires proposed_terms" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_accept_with_terms_rejected(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="poster7")
        solver, _ = await create_test_agent(db_session, name="solver7")
        bounty = await create_test_bounty(db_session, poster)
        proposal = await create_test_proposal(db_session, bounty, solver)
        negotiation = await create_test_negotiation(
            db_session, bounty, proposal, poster, solver, turn_count=1,
        )

        request = NegotiationTurnRequest(
            turn_type="accept", proposed_terms=make_terms()
        )
        with pytest.raises(HTTPException) as exc_info:
            validate_turn(negotiation, request, solver.id)
        assert exc_info.value.status_code == 400
        assert "must not include" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_max_turns_limit(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="poster8")
        solver, _ = await create_test_agent(db_session, name="solver8")
        bounty = await create_test_bounty(db_session, poster)
        proposal = await create_test_proposal(db_session, bounty, solver)
        negotiation = await create_test_negotiation(
            db_session, bounty, proposal, poster, solver, turn_count=10,
        )

        request = NegotiationTurnRequest(turn_type="offer", proposed_terms=make_terms())
        with pytest.raises(HTTPException) as exc_info:
            validate_turn(negotiation, request, poster.id)
        assert exc_info.value.status_code == 400
        assert "Maximum turns" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_first_turn_must_be_offer(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="poster9")
        solver, _ = await create_test_agent(db_session, name="solver9")
        bounty = await create_test_bounty(db_session, poster)
        proposal = await create_test_proposal(db_session, bounty, solver)
        negotiation = await create_test_negotiation(
            db_session, bounty, proposal, poster, solver, turn_count=0,
        )

        request = NegotiationTurnRequest(turn_type="accept")
        with pytest.raises(HTTPException) as exc_info:
            validate_turn(negotiation, request, poster.id)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_valid_offer_passes(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="poster10")
        solver, _ = await create_test_agent(db_session, name="solver10")
        bounty = await create_test_bounty(db_session, poster)
        proposal = await create_test_proposal(db_session, bounty, solver)
        negotiation = await create_test_negotiation(
            db_session, bounty, proposal, poster, solver,
        )

        request = NegotiationTurnRequest(turn_type="offer", proposed_terms=make_terms())
        # Should not raise
        validate_turn(negotiation, request, poster.id)

    @pytest.mark.asyncio
    async def test_valid_counter_passes(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="poster11")
        solver, _ = await create_test_agent(db_session, name="solver11")
        bounty = await create_test_bounty(db_session, poster)
        proposal = await create_test_proposal(db_session, bounty, solver)
        negotiation = await create_test_negotiation(
            db_session, bounty, proposal, poster, solver, turn_count=1,
        )

        request = NegotiationTurnRequest(turn_type="counter", proposed_terms=make_terms())
        validate_turn(negotiation, request, solver.id)

    @pytest.mark.asyncio
    async def test_valid_accept_passes(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="poster12")
        solver, _ = await create_test_agent(db_session, name="solver12")
        bounty = await create_test_bounty(db_session, poster)
        proposal = await create_test_proposal(db_session, bounty, solver)
        negotiation = await create_test_negotiation(
            db_session, bounty, proposal, poster, solver, turn_count=1,
        )

        request = NegotiationTurnRequest(turn_type="accept")
        validate_turn(negotiation, request, solver.id)

    @pytest.mark.asyncio
    async def test_valid_reject_passes(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="poster13")
        solver, _ = await create_test_agent(db_session, name="solver13")
        bounty = await create_test_bounty(db_session, poster)
        proposal = await create_test_proposal(db_session, bounty, solver)
        negotiation = await create_test_negotiation(
            db_session, bounty, proposal, poster, solver, turn_count=1,
        )

        request = NegotiationTurnRequest(turn_type="reject")
        validate_turn(negotiation, request, solver.id)


class TestProcessTurn:
    @pytest.mark.asyncio
    async def test_process_offer_creates_turn(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="pt-poster1")
        solver, _ = await create_test_agent(db_session, name="pt-solver1")
        bounty = await create_test_bounty(db_session, poster)
        proposal = await create_test_proposal(db_session, bounty, solver)
        negotiation = await create_test_negotiation(
            db_session, bounty, proposal, poster, solver,
        )

        request = NegotiationTurnRequest(turn_type="offer", proposed_terms=make_terms())
        turn = await process_turn(negotiation, request, poster.id, db_session)

        assert turn.sequence == 0
        assert turn.turn_type.value == "offer"
        assert turn.proposed_terms is not None
        assert negotiation.turn_count == 1
        assert negotiation.current_terms is not None

    @pytest.mark.asyncio
    async def test_process_counter_updates_terms(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="pt-poster2")
        solver, _ = await create_test_agent(db_session, name="pt-solver2")
        bounty = await create_test_bounty(db_session, poster)
        proposal = await create_test_proposal(db_session, bounty, solver)
        negotiation = await create_test_negotiation(
            db_session, bounty, proposal, poster, solver, turn_count=1,
            current_terms={"price": 1.0},
        )

        new_terms = make_terms()
        new_terms.price = 0.8
        request = NegotiationTurnRequest(turn_type="counter", proposed_terms=new_terms)
        turn = await process_turn(negotiation, request, solver.id, db_session)

        assert turn.sequence == 1
        assert negotiation.current_terms["price"] == 0.8

    @pytest.mark.asyncio
    async def test_process_accept_sets_agreed(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="pt-poster3")
        solver, _ = await create_test_agent(db_session, name="pt-solver3")
        bounty = await create_test_bounty(db_session, poster, status=BountyStatus.negotiating)
        proposal = await create_test_proposal(db_session, bounty, solver)
        negotiation = await create_test_negotiation(
            db_session, bounty, proposal, poster, solver, turn_count=1,
            current_terms={"price": 1.0},
        )

        request = NegotiationTurnRequest(turn_type="accept")
        turn = await process_turn(negotiation, request, solver.id, db_session)

        assert negotiation.status == NegotiationStatus.agreed
        await db_session.refresh(bounty)
        assert bounty.status == BountyStatus.agreed

    @pytest.mark.asyncio
    async def test_process_reject_sets_rejected(self, db_session: AsyncSession):
        poster, _ = await create_test_agent(db_session, name="pt-poster4")
        solver, _ = await create_test_agent(db_session, name="pt-solver4")
        bounty = await create_test_bounty(db_session, poster, status=BountyStatus.negotiating)
        bounty.solver_id = solver.id
        proposal = await create_test_proposal(db_session, bounty, solver)
        negotiation = await create_test_negotiation(
            db_session, bounty, proposal, poster, solver, turn_count=1,
            current_terms={"price": 1.0},
        )

        request = NegotiationTurnRequest(turn_type="reject")
        turn = await process_turn(negotiation, request, solver.id, db_session)

        assert negotiation.status == NegotiationStatus.rejected
        await db_session.refresh(bounty)
        assert bounty.status == BountyStatus.open
        assert bounty.solver_id is None

    @pytest.mark.asyncio
    async def test_alternating_turns(self, db_session: AsyncSession):
        """Test a full offer -> counter -> accept sequence."""
        poster, _ = await create_test_agent(db_session, name="pt-poster5")
        solver, _ = await create_test_agent(db_session, name="pt-solver5")
        bounty = await create_test_bounty(db_session, poster, status=BountyStatus.negotiating)
        proposal = await create_test_proposal(db_session, bounty, solver)
        negotiation = await create_test_negotiation(
            db_session, bounty, proposal, poster, solver,
        )

        # Turn 0: Poster offers
        offer_req = NegotiationTurnRequest(turn_type="offer", proposed_terms=make_terms())
        turn0 = await process_turn(negotiation, offer_req, poster.id, db_session)
        assert turn0.sequence == 0
        assert negotiation.turn_count == 1

        # Turn 1: Solver counters
        counter_terms = make_terms()
        counter_terms.price = 0.75
        counter_req = NegotiationTurnRequest(turn_type="counter", proposed_terms=counter_terms)
        turn1 = await process_turn(negotiation, counter_req, solver.id, db_session)
        assert turn1.sequence == 1
        assert negotiation.turn_count == 2

        # Turn 2: Poster accepts
        accept_req = NegotiationTurnRequest(turn_type="accept")
        turn2 = await process_turn(negotiation, accept_req, poster.id, db_session)
        assert turn2.sequence == 2
        assert negotiation.status == NegotiationStatus.agreed
