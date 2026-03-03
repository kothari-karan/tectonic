import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_key import get_current_agent
from app.database import get_db
from app.models.agent import Agent
from app.models.bounty import Bounty, BountyStatus
from app.models.proposal import Proposal, ProposalStatus
from app.schemas.proposal import ProposalCreate, ProposalResponse

router = APIRouter(prefix="/bounties/{bounty_id}/proposals", tags=["proposals"])


@router.post("", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
async def create_proposal(
    bounty_id: uuid.UUID,
    proposal_data: ProposalCreate,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Submit a proposal for a bounty (requires authentication - solver)."""
    # Check bounty exists and is open
    bounty = await db.get(Bounty, bounty_id)
    if bounty is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bounty not found",
        )

    if bounty.status not in (BountyStatus.open, BountyStatus.proposed):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bounty is not open for proposals (status: {bounty.status})",
        )

    # Prevent poster from proposing on their own bounty
    if str(bounty.poster_id) == str(agent.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot submit a proposal on your own bounty",
        )

    # Check for duplicate proposal (same solver, same bounty)
    result = await db.execute(
        select(Proposal).where(
            Proposal.bounty_id == bounty_id,
            Proposal.solver_id == agent.id,
            Proposal.status == ProposalStatus.pending,
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a pending proposal for this bounty",
        )

    proposal = Proposal(
        bounty_id=bounty_id,
        solver_id=agent.id,
        proposed_price=proposal_data.proposed_price,
        proposed_deadline=proposal_data.proposed_deadline,
        approach_summary=proposal_data.approach_summary,
        status=ProposalStatus.pending,
        created_at=datetime.now(timezone.utc),
    )
    db.add(proposal)

    # Update bounty status to proposed
    bounty.status = BountyStatus.proposed
    bounty.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(proposal)
    return ProposalResponse.model_validate(proposal)


@router.get("", response_model=list[ProposalResponse])
async def list_proposals(
    bounty_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all proposals for a bounty."""
    bounty = await db.get(Bounty, bounty_id)
    if bounty is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bounty not found",
        )

    result = await db.execute(
        select(Proposal)
        .where(Proposal.bounty_id == bounty_id)
        .order_by(Proposal.created_at.desc())
    )
    proposals = result.scalars().all()
    return [ProposalResponse.model_validate(p) for p in proposals]
