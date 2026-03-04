import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_key import get_current_agent, get_current_agent_optional
from app.database import get_db
from app.models.agent import Agent
from app.models.bounty import EngagementStatus, EngagementType
from app.schemas.bounty import (
    EngagementCreate,
    EngagementListResponse,
    EngagementResponse,
    EngagementUpdate,
)
from app.services.bounty_service import (
    create_engagement,
    get_engagement,
    get_provider_inbox,
    list_engagements,
    update_engagement_status,
)

router = APIRouter(prefix="/engagements", tags=["engagements"])


@router.post("", response_model=EngagementResponse, status_code=201)
async def create_engagement_endpoint(
    engagement_data: EngagementCreate,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Create a new engagement (requires authentication - requester)."""
    engagement = await create_engagement(engagement_data, agent, db)
    return EngagementResponse.model_validate(engagement)


@router.get("", response_model=EngagementListResponse)
async def list_engagements_endpoint(
    status: EngagementStatus | None = Query(None),
    category: str | None = Query(None),
    requester_id: uuid.UUID | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List public (open-type) engagements with optional filters.

    Direct and invited engagements are excluded from this listing.
    Use GET /agents/{id}/inbox to retrieve targeted engagements.
    """
    engagements, total = await list_engagements(
        db, status_filter=status, category=category, requester_id=requester_id,
        skip=skip, limit=limit,
    )
    return EngagementListResponse(
        engagements=[EngagementResponse.model_validate(e) for e in engagements],
        total=total,
    )


@router.get("/{engagement_id}", response_model=EngagementResponse)
async def get_engagement_endpoint(
    engagement_id: uuid.UUID,
    agent: Optional[Agent] = Depends(get_current_agent_optional),
    db: AsyncSession = Depends(get_db),
):
    """Get an engagement by ID.

    Open engagements are publicly accessible. Direct and invited engagements
    require the caller to be the requester or a target provider.
    """
    engagement = await get_engagement(engagement_id, db)

    # Open engagements are public
    if engagement.engagement_type == EngagementType.open:
        return EngagementResponse.model_validate(engagement)

    # Direct/invited engagements require authorization
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication required to view this engagement",
        )

    agent_id_str = str(agent.id)
    is_requester = str(engagement.requester_id) == agent_id_str
    is_target = (
        engagement.target_provider_ids
        and agent_id_str in engagement.target_provider_ids
    )

    if not is_requester and not is_target:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this engagement",
        )

    return EngagementResponse.model_validate(engagement)


@router.patch("/{engagement_id}", response_model=EngagementResponse)
async def update_engagement_endpoint(
    engagement_id: uuid.UUID,
    update_data: EngagementUpdate,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Update an engagement (requires authentication - requester only)."""
    engagement = await update_engagement_status(engagement_id, update_data, agent, db)
    return EngagementResponse.model_validate(engagement)
