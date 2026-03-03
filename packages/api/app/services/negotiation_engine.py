import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bounty import Bounty, BountyStatus
from app.models.negotiation import Negotiation, NegotiationStatus, NegotiationTurn, TurnType
from app.schemas.negotiation import NegotiationTurnRequest


def validate_turn(
    negotiation: Negotiation,
    turn_request: NegotiationTurnRequest,
    agent_id: uuid.UUID,
) -> None:
    """
    Validate that a negotiation turn is valid.

    Rules:
    - Negotiation must be active.
    - It must be the agent's turn (poster goes on even turns, solver on odd turns).
    - Turn type must be valid for the current state.
    - counter/offer must include proposed_terms.
    - accept must NOT include new terms.
    - Turn count must be < max_turns.
    """
    # Check negotiation is active
    if negotiation.status != NegotiationStatus.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Negotiation is not active (status: {negotiation.status})",
        )

    # Check it's the agent's turn
    # Poster starts (turn_count 0 = poster), then alternates
    agent_id_str = str(agent_id)
    poster_id_str = str(negotiation.poster_id)
    solver_id_str = str(negotiation.solver_id)

    if agent_id_str != poster_id_str and agent_id_str != solver_id_str:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this negotiation",
        )

    is_poster_turn = negotiation.turn_count % 2 == 0
    if is_poster_turn and agent_id_str != poster_id_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="It is the poster's turn",
        )
    if not is_poster_turn and agent_id_str != solver_id_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="It is the solver's turn",
        )

    # Validate turn type
    turn_type = turn_request.turn_type
    if turn_type in ("offer", "counter") and turn_request.proposed_terms is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Turn type '{turn_type}' requires proposed_terms",
        )
    if turn_type == "accept" and turn_request.proposed_terms is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Accept turn must not include new proposed_terms",
        )

    # Check turn count limit
    if negotiation.turn_count >= negotiation.max_turns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum turns ({negotiation.max_turns}) reached",
        )

    # Validate first turn must be offer
    if negotiation.turn_count == 0 and turn_type not in ("offer",):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="First turn must be an offer",
        )

    # Can only accept/reject if there are existing terms (turn_count > 0)
    if turn_type in ("accept", "reject") and negotiation.turn_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot accept or reject without prior terms",
        )


async def process_turn(
    negotiation: Negotiation,
    turn_request: NegotiationTurnRequest,
    agent_id: uuid.UUID,
    db: AsyncSession,
) -> NegotiationTurn:
    """
    Process a negotiation turn: create the turn record, update negotiation state.
    """
    validate_turn(negotiation, turn_request, agent_id)

    # Create the turn
    terms_dict = None
    if turn_request.proposed_terms is not None:
        terms_dict = turn_request.proposed_terms.model_dump(mode="json")

    turn = NegotiationTurn(
        negotiation_id=negotiation.id,
        agent_id=agent_id,
        sequence=negotiation.turn_count,
        turn_type=TurnType(turn_request.turn_type),
        proposed_terms=terms_dict,
        message=turn_request.message,
        created_at=datetime.now(timezone.utc),
    )
    db.add(turn)

    # Update negotiation state
    negotiation.turn_count += 1
    negotiation.updated_at = datetime.now(timezone.utc)

    if turn_request.turn_type in ("offer", "counter"):
        negotiation.current_terms = terms_dict
    elif turn_request.turn_type == "accept":
        negotiation.status = NegotiationStatus.agreed
        # Update the bounty status to agreed
        bounty = await db.get(Bounty, negotiation.bounty_id)
        if bounty:
            bounty.status = BountyStatus.agreed
            bounty.updated_at = datetime.now(timezone.utc)
    elif turn_request.turn_type == "reject":
        negotiation.status = NegotiationStatus.rejected
        # Revert bounty to open
        bounty = await db.get(Bounty, negotiation.bounty_id)
        if bounty:
            bounty.status = BountyStatus.open
            bounty.solver_id = None
            bounty.updated_at = datetime.now(timezone.utc)

    await db.flush()
    return turn
