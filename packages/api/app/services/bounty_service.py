import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.bounty import Engagement, EngagementStatus, EngagementType
from app.schemas.bounty import EngagementCreate, EngagementUpdate


async def create_engagement(
    engagement_data: EngagementCreate,
    requester: Agent,
    db: AsyncSession,
) -> Engagement:
    """Create a new engagement."""
    # Validate target_provider_ids for direct/invited types
    if engagement_data.engagement_type in (EngagementType.direct, EngagementType.invited):
        if not engagement_data.target_provider_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{engagement_data.engagement_type.value} engagements require target_provider_ids",
            )

    engagement = Engagement(
        title=engagement_data.title,
        description=engagement_data.description,
        acceptance_criteria=engagement_data.acceptance_criteria,
        category=engagement_data.category,
        reward_amount=engagement_data.reward_amount,
        reward_token=engagement_data.reward_token,
        engagement_type=engagement_data.engagement_type,
        target_provider_ids=[str(pid) for pid in engagement_data.target_provider_ids]
        if engagement_data.target_provider_ids
        else None,
        requester_id=requester.id,
        deadline=engagement_data.deadline,
        status=EngagementStatus.open,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(engagement)

    # Increment requester's engagements_posted
    requester.engagements_posted += 1
    requester.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(engagement)
    return engagement


async def get_engagement(engagement_id: uuid.UUID, db: AsyncSession) -> Engagement:
    """Get an engagement by ID."""
    engagement = await db.get(Engagement, engagement_id)
    if engagement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engagement not found",
        )
    return engagement


async def list_engagements(
    db: AsyncSession,
    status_filter: EngagementStatus | None = None,
    category: str | None = None,
    requester_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[Engagement], int]:
    """List public (open-type) engagements with optional filters.

    Direct and invited engagements are excluded from public listing.
    Use ``get_provider_inbox`` to retrieve targeted engagements.
    """
    query = select(Engagement).where(Engagement.engagement_type == EngagementType.open)
    count_query = (
        select(func.count())
        .select_from(Engagement)
        .where(Engagement.engagement_type == EngagementType.open)
    )

    if status_filter is not None:
        query = query.where(Engagement.status == status_filter)
        count_query = count_query.where(Engagement.status == status_filter)
    if category is not None:
        query = query.where(Engagement.category == category)
        count_query = count_query.where(Engagement.category == category)
    if requester_id is not None:
        query = query.where(Engagement.requester_id == requester_id)
        count_query = count_query.where(Engagement.requester_id == requester_id)

    query = query.order_by(Engagement.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    engagements = list(result.scalars().all())

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    return engagements, total


async def get_provider_inbox(
    agent_id: uuid.UUID,
    db: AsyncSession,
    status_filter: EngagementStatus | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[Engagement], int]:
    """Get engagements targeted at a specific provider (direct/invited).

    Returns engagements where the agent's ID appears in ``target_provider_ids``.
    """
    agent_id_str = str(agent_id)

    # Load all non-open engagements and filter by target_provider_ids in Python,
    # since JSON array containment varies across DB backends (SQLite vs Postgres).
    query = select(Engagement).where(
        Engagement.engagement_type.in_([EngagementType.direct, EngagementType.invited])
    )
    if status_filter is not None:
        query = query.where(Engagement.status == status_filter)

    query = query.order_by(Engagement.created_at.desc())
    result = await db.execute(query)
    all_targeted = list(result.scalars().all())

    # Filter to engagements targeting this agent
    matching = [
        e for e in all_targeted if e.target_provider_ids and agent_id_str in e.target_provider_ids
    ]

    total = len(matching)
    paged = matching[skip : skip + limit]
    return paged, total


async def update_engagement_status(
    engagement_id: uuid.UUID,
    update_data: EngagementUpdate,
    agent: Agent,
    db: AsyncSession,
) -> Engagement:
    """Update engagement fields (requester only)."""
    engagement = await get_engagement(engagement_id, db)

    if str(engagement.requester_id) != str(agent.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the requester can update this engagement",
        )

    if update_data.status is not None:
        engagement.status = update_data.status
    if update_data.provider_id is not None:
        engagement.provider_id = update_data.provider_id
    if update_data.deliverable_url is not None:
        engagement.deliverable_url = update_data.deliverable_url

    engagement.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(engagement)
    return engagement
