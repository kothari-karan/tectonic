import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_key import get_current_agent
from app.database import get_db
from app.models.agent import Agent
from app.models.bounty import Engagement, EngagementStatus
from app.models.negotiation import Negotiation, NegotiationStatus, NegotiationTurn
from app.models.proposal import Proposal, ProposalStatus
from app.schemas.negotiation import (
    NegotiationCreate,
    NegotiationResponse,
    NegotiationTurnRequest,
    NegotiationTurnResponse,
)
from app.services.negotiation_engine import process_turn

router = APIRouter(prefix="/negotiations", tags=["negotiations"])


@router.post("", response_model=NegotiationResponse, status_code=status.HTTP_201_CREATED)
async def create_negotiation(
    negotiation_data: NegotiationCreate,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Create a negotiation from a proposal (requires authentication)."""
    # Validate proposal exists
    proposal = await db.get(Proposal, negotiation_data.proposal_id)
    if proposal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found",
        )

    if str(proposal.engagement_id) != str(negotiation_data.engagement_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proposal does not belong to the specified engagement",
        )

    # Validate engagement
    engagement = await db.get(Engagement, negotiation_data.engagement_id)
    if engagement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engagement not found",
        )

    # The requester should initiate the negotiation
    if str(engagement.requester_id) != str(agent.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the engagement requester can initiate a negotiation",
        )

    # Mark proposal as accepted
    proposal.status = ProposalStatus.accepted

    # Update engagement status
    engagement.status = EngagementStatus.negotiating
    engagement.provider_id = proposal.provider_id
    engagement.updated_at = datetime.now(timezone.utc)

    negotiation = Negotiation(
        engagement_id=negotiation_data.engagement_id,
        proposal_id=negotiation_data.proposal_id,
        requester_id=engagement.requester_id,
        provider_id=proposal.provider_id,
        status=NegotiationStatus.active,
        turn_count=0,
        max_turns=10,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(negotiation)
    await db.flush()
    await db.refresh(negotiation)

    response = NegotiationResponse(
        id=negotiation.id,
        engagement_id=negotiation.engagement_id,
        proposal_id=negotiation.proposal_id,
        requester_id=negotiation.requester_id,
        provider_id=negotiation.provider_id,
        status=negotiation.status.value if hasattr(negotiation.status, "value") else str(negotiation.status),
        current_terms=negotiation.current_terms,
        turn_count=negotiation.turn_count,
        max_turns=negotiation.max_turns,
        created_at=negotiation.created_at,
        updated_at=negotiation.updated_at,
        turns=[],
    )
    return response


@router.get("/{negotiation_id}", response_model=NegotiationResponse)
async def get_negotiation(
    negotiation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a negotiation by ID."""
    negotiation = await db.get(Negotiation, negotiation_id)
    if negotiation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Negotiation not found",
        )

    # Load turns
    result = await db.execute(
        select(NegotiationTurn)
        .where(NegotiationTurn.negotiation_id == negotiation_id)
        .order_by(NegotiationTurn.sequence)
    )
    turns = result.scalars().all()

    response = NegotiationResponse(
        id=negotiation.id,
        engagement_id=negotiation.engagement_id,
        proposal_id=negotiation.proposal_id,
        requester_id=negotiation.requester_id,
        provider_id=negotiation.provider_id,
        status=negotiation.status.value if hasattr(negotiation.status, "value") else str(negotiation.status),
        current_terms=negotiation.current_terms,
        turn_count=negotiation.turn_count,
        max_turns=negotiation.max_turns,
        created_at=negotiation.created_at,
        updated_at=negotiation.updated_at,
        turns=[NegotiationTurnResponse.model_validate(t) for t in turns],
    )
    return response


@router.post(
    "/{negotiation_id}/turns",
    response_model=NegotiationTurnResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_turn(
    negotiation_id: uuid.UUID,
    turn_request: NegotiationTurnRequest,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Submit a negotiation turn (requires authentication - validates it's the agent's turn)."""
    negotiation = await db.get(Negotiation, negotiation_id)
    if negotiation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Negotiation not found",
        )

    turn = await process_turn(negotiation, turn_request, agent.id, db)
    return NegotiationTurnResponse.model_validate(turn)


@router.get("/{negotiation_id}/turns", response_model=list[NegotiationTurnResponse])
async def list_turns(
    negotiation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all turns for a negotiation."""
    negotiation = await db.get(Negotiation, negotiation_id)
    if negotiation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Negotiation not found",
        )

    result = await db.execute(
        select(NegotiationTurn)
        .where(NegotiationTurn.negotiation_id == negotiation_id)
        .order_by(NegotiationTurn.sequence)
    )
    turns = result.scalars().all()
    return [NegotiationTurnResponse.model_validate(t) for t in turns]
