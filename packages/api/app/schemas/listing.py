import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.listing import ListingAvailability, RateType


class ListingCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    capabilities: list[str] = Field(..., min_length=1)
    rate_type: RateType
    rate_range_min: float = Field(..., gt=0)
    rate_range_max: float = Field(..., gt=0)
    response_time_hours: int = Field(default=24, gt=0)


class ListingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    capabilities: list[str] | None = None
    availability: ListingAvailability | None = None
    rate_range_min: float | None = None
    rate_range_max: float | None = None
    response_time_hours: int | None = None


class ListingResponse(BaseModel):
    id: uuid.UUID
    provider_id: uuid.UUID
    title: str
    description: str
    capabilities: list
    rate_type: RateType
    rate_range_min: float
    rate_range_max: float
    availability: ListingAvailability
    response_time_hours: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ListingListResponse(BaseModel):
    listings: list[ListingResponse]
    total: int
