import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_key import get_current_agent
from app.database import get_db
from app.models.agent import Agent
from app.models.bounty import BountyStatus
from app.schemas.bounty import BountyCreate, BountyListResponse, BountyResponse, BountyUpdate
from app.services.bounty_service import create_bounty, get_bounty, list_bounties, update_bounty_status

router = APIRouter(prefix="/bounties", tags=["bounties"])


@router.post("", response_model=BountyResponse, status_code=201)
async def create_bounty_endpoint(
    bounty_data: BountyCreate,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Create a new bounty (requires authentication - poster)."""
    bounty = await create_bounty(bounty_data, agent, db)
    return BountyResponse.model_validate(bounty)


@router.get("", response_model=BountyListResponse)
async def list_bounties_endpoint(
    status: BountyStatus | None = Query(None),
    category: str | None = Query(None),
    poster_id: uuid.UUID | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List bounties with optional filters (public)."""
    bounties, total = await list_bounties(
        db, status_filter=status, category=category, poster_id=poster_id,
        skip=skip, limit=limit,
    )
    return BountyListResponse(
        bounties=[BountyResponse.model_validate(b) for b in bounties],
        total=total,
    )


@router.get("/{bounty_id}", response_model=BountyResponse)
async def get_bounty_endpoint(
    bounty_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a bounty by ID (public)."""
    bounty = await get_bounty(bounty_id, db)
    return BountyResponse.model_validate(bounty)


@router.patch("/{bounty_id}", response_model=BountyResponse)
async def update_bounty_endpoint(
    bounty_id: uuid.UUID,
    update_data: BountyUpdate,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Update a bounty (requires authentication - poster only)."""
    bounty = await update_bounty_status(bounty_id, update_data, agent, db)
    return BountyResponse.model_validate(bounty)
