import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.bounty import EngagementStatus, EngagementType


class EngagementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    acceptance_criteria: list[str] = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=100)
    reward_amount: float = Field(..., gt=0)
    reward_token: str = Field(default="ETH", max_length=20)
    deadline: datetime
    engagement_type: EngagementType = EngagementType.open
    target_provider_ids: list[uuid.UUID] | None = None


class EngagementUpdate(BaseModel):
    provider_id: uuid.UUID | None = None
    status: EngagementStatus | None = None
    deliverable_url: str | None = None


class EngagementResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    acceptance_criteria: list
    category: str
    reward_amount: float
    reward_token: str
    engagement_type: EngagementType
    target_provider_ids: list | None
    requester_id: uuid.UUID
    provider_id: uuid.UUID | None
    status: EngagementStatus
    deadline: datetime
    escrow_address: str | None
    deliverable_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EngagementListResponse(BaseModel):
    engagements: list[EngagementResponse]
    total: int
