import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.bounty import Bounty, BountyStatus
from app.schemas.bounty import BountyCreate, BountyUpdate


async def create_bounty(
    bounty_data: BountyCreate,
    poster: Agent,
    db: AsyncSession,
) -> Bounty:
    """Create a new bounty."""
    bounty = Bounty(
        title=bounty_data.title,
        description=bounty_data.description,
        acceptance_criteria=bounty_data.acceptance_criteria,
        category=bounty_data.category,
        reward_amount=bounty_data.reward_amount,
        reward_token=bounty_data.reward_token,
        poster_id=poster.id,
        deadline=bounty_data.deadline,
        status=BountyStatus.open,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(bounty)

    # Increment poster's bounties_posted
    poster.bounties_posted += 1
    poster.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(bounty)
    return bounty


async def get_bounty(bounty_id: uuid.UUID, db: AsyncSession) -> Bounty:
    """Get a bounty by ID."""
    bounty = await db.get(Bounty, bounty_id)
    if bounty is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bounty not found",
        )
    return bounty


async def list_bounties(
    db: AsyncSession,
    status_filter: BountyStatus | None = None,
    category: str | None = None,
    poster_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[Bounty], int]:
    """List bounties with optional filters."""
    query = select(Bounty)
    count_query = select(func.count()).select_from(Bounty)

    if status_filter is not None:
        query = query.where(Bounty.status == status_filter)
        count_query = count_query.where(Bounty.status == status_filter)
    if category is not None:
        query = query.where(Bounty.category == category)
        count_query = count_query.where(Bounty.category == category)
    if poster_id is not None:
        query = query.where(Bounty.poster_id == poster_id)
        count_query = count_query.where(Bounty.poster_id == poster_id)

    query = query.order_by(Bounty.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    bounties = list(result.scalars().all())

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    return bounties, total


async def update_bounty_status(
    bounty_id: uuid.UUID,
    update_data: BountyUpdate,
    agent: Agent,
    db: AsyncSession,
) -> Bounty:
    """Update bounty fields (poster only)."""
    bounty = await get_bounty(bounty_id, db)

    if str(bounty.poster_id) != str(agent.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the poster can update this bounty",
        )

    if update_data.status is not None:
        bounty.status = update_data.status
    if update_data.solver_id is not None:
        bounty.solver_id = update_data.solver_id
    if update_data.deliverable_url is not None:
        bounty.deliverable_url = update_data.deliverable_url

    bounty.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(bounty)
    return bounty
