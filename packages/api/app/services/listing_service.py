import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.listing import ListingAvailability, ServiceListing
from app.schemas.listing import ListingCreate, ListingUpdate


async def create_listing(
    data: ListingCreate,
    provider: Agent,
    db: AsyncSession,
) -> ServiceListing:
    """Create a new service listing."""
    if data.rate_range_min > data.rate_range_max:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="rate_range_min must not exceed rate_range_max",
        )

    listing = ServiceListing(
        provider_id=provider.id,
        title=data.title,
        description=data.description,
        capabilities=data.capabilities,
        rate_type=data.rate_type,
        rate_range_min=data.rate_range_min,
        rate_range_max=data.rate_range_max,
        response_time_hours=data.response_time_hours,
        availability=ListingAvailability.available,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(listing)
    await db.flush()
    await db.refresh(listing)
    return listing


async def get_listing(listing_id: uuid.UUID, db: AsyncSession) -> ServiceListing:
    """Get a service listing by ID."""
    listing = await db.get(ServiceListing, listing_id)
    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )
    return listing


async def list_listings(
    db: AsyncSession,
    availability: ListingAvailability | None = None,
    capability: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[ServiceListing], int]:
    """List service listings with optional filters."""
    query = select(ServiceListing)
    count_query = select(func.count()).select_from(ServiceListing)

    if availability is not None:
        query = query.where(ServiceListing.availability == availability)
        count_query = count_query.where(ServiceListing.availability == availability)

    query = query.order_by(ServiceListing.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    listings = list(result.scalars().all())

    # Filter by capability in Python (JSON array containment varies by DB)
    if capability is not None:
        listings = [
            l for l in listings
            if l.capabilities and capability in l.capabilities
        ]

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()
    if capability is not None:
        total = len(listings)

    return listings, total


async def update_listing(
    listing_id: uuid.UUID,
    data: ListingUpdate,
    agent: Agent,
    db: AsyncSession,
) -> ServiceListing:
    """Update a service listing (owner only)."""
    listing = await get_listing(listing_id, db)

    if str(listing.provider_id) != str(agent.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the listing owner can update it",
        )

    if data.title is not None:
        listing.title = data.title
    if data.description is not None:
        listing.description = data.description
    if data.capabilities is not None:
        listing.capabilities = data.capabilities
    if data.availability is not None:
        listing.availability = data.availability
    if data.rate_range_min is not None:
        listing.rate_range_min = data.rate_range_min
    if data.rate_range_max is not None:
        listing.rate_range_max = data.rate_range_max
    if data.response_time_hours is not None:
        listing.response_time_hours = data.response_time_hours

    listing.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(listing)
    return listing
