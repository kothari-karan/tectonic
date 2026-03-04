import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_key import get_current_agent
from app.database import get_db
from app.models.agent import Agent
from app.models.bounty import Engagement, EngagementStatus, EngagementType
from app.models.proposal import Proposal, ProposalStatus
from app.schemas.proposal import ProposalCreate, ProposalResponse

router = APIRouter(prefix="/engagements/{engagement_id}/proposals", tags=["proposals"])


@router.post("", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
async def create_proposal(
    engagement_id: uuid.UUID,
    proposal_data: ProposalCreate,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Submit a proposal for an engagement (requires authentication - provider)."""
    # Check engagement exists and is open
    engagement = await db.get(Engagement, engagement_id)
    if engagement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engagement not found",
        )

    if engagement.status not in (EngagementStatus.open, EngagementStatus.proposed):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Engagement is not open for proposals (status: {engagement.status})",
        )

    # Prevent requester from proposing on their own engagement
    if str(engagement.requester_id) == str(agent.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot submit a proposal on your own engagement",
        )

    # For direct/invited engagements, check provider is in target list
    if engagement.engagement_type in (EngagementType.direct, EngagementType.invited):
        agent_id_str = str(agent.id)
        if not engagement.target_provider_ids or agent_id_str not in engagement.target_provider_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to propose on this engagement",
            )

    # Check for duplicate proposal (same provider, same engagement)
    result = await db.execute(
        select(Proposal).where(
            Proposal.engagement_id == engagement_id,
            Proposal.provider_id == agent.id,
            Proposal.status == ProposalStatus.pending,
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a pending proposal for this engagement",
        )

    proposal = Proposal(
        engagement_id=engagement_id,
        provider_id=agent.id,
        proposed_price=proposal_data.proposed_price,
        proposed_deadline=proposal_data.proposed_deadline,
        approach_summary=proposal_data.approach_summary,
        status=ProposalStatus.pending,
        created_at=datetime.now(timezone.utc),
    )
    db.add(proposal)

    # Update engagement status to proposed
    engagement.status = EngagementStatus.proposed
    engagement.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(proposal)
    return ProposalResponse.model_validate(proposal)


@router.get("", response_model=list[ProposalResponse])
async def list_proposals(
    engagement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all proposals for an engagement."""
    engagement = await db.get(Engagement, engagement_id)
    if engagement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engagement not found",
        )

    result = await db.execute(
        select(Proposal)
        .where(Proposal.engagement_id == engagement_id)
        .order_by(Proposal.created_at.desc())
    )
    proposals = result.scalars().all()
    return [ProposalResponse.model_validate(p) for p in proposals]
