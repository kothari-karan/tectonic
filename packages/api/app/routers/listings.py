import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_key import get_current_agent
from app.database import get_db
from app.models.agent import Agent
from app.models.bounty import Engagement, EngagementStatus, EngagementType
from app.models.listing import ListingAvailability
from app.schemas.bounty import EngagementResponse
from app.schemas.listing import (
    ListingCreate,
    ListingListResponse,
    ListingResponse,
    ListingUpdate,
)
from app.services.listing_service import (
    create_listing,
    get_listing,
    list_listings,
    update_listing,
)

router = APIRouter(prefix="/listings", tags=["listings"])


@router.post("", response_model=ListingResponse, status_code=201)
async def create_listing_endpoint(
    data: ListingCreate,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Create a new service listing (provider advertises capabilities)."""
    listing = await create_listing(data, agent, db)
    return ListingResponse.model_validate(listing)


@router.get("", response_model=ListingListResponse)
async def list_listings_endpoint(
    availability: ListingAvailability | None = Query(None),
    capability: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Browse available service listings (public)."""
    listings, total = await list_listings(
        db, availability=availability, capability=capability, skip=skip, limit=limit,
    )
    return ListingListResponse(
        listings=[ListingResponse.model_validate(l) for l in listings],
        total=total,
    )


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing_endpoint(
    listing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a service listing by ID (public)."""
    listing = await get_listing(listing_id, db)
    return ListingResponse.model_validate(listing)


@router.patch("/{listing_id}", response_model=ListingResponse)
async def update_listing_endpoint(
    listing_id: uuid.UUID,
    data: ListingUpdate,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Update a service listing (owner only)."""
    listing = await update_listing(listing_id, data, agent, db)
    return ListingResponse.model_validate(listing)


@router.post("/{listing_id}/engage", response_model=EngagementResponse, status_code=201)
async def engage_listing_endpoint(
    listing_id: uuid.UUID,
    title: str = Query(..., min_length=1),
    description: str = Query(..., min_length=1),
    reward_amount: float = Query(..., gt=0),
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Create a direct engagement from a service listing.

    The requester engages a provider through their listing, automatically
    creating a direct-type engagement targeted at the listing's provider.
    """
    listing = await get_listing(listing_id, db)

    if listing.availability != ListingAvailability.available:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Provider is not currently available",
        )

    if str(listing.provider_id) == str(agent.id):
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Cannot engage your own listing",
        )

    engagement = Engagement(
        title=title,
        description=description,
        acceptance_criteria=[],
        category="service_listing",
        reward_amount=reward_amount,
        reward_token="ETH",
        engagement_type=EngagementType.direct,
        target_provider_ids=[str(listing.provider_id)],
        requester_id=agent.id,
        deadline=datetime.now(timezone.utc) + timedelta(days=30),
        status=EngagementStatus.open,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(engagement)
    await db.flush()
    await db.refresh(engagement)
    return EngagementResponse.model_validate(engagement)
