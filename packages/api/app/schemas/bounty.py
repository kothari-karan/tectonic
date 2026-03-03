import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.bounty import BountyStatus


class BountyCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    acceptance_criteria: list[str] = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=100)
    reward_amount: float = Field(..., gt=0)
    reward_token: str = Field(default="ETH", max_length=20)
    deadline: datetime


class BountyUpdate(BaseModel):
    solver_id: uuid.UUID | None = None
    status: BountyStatus | None = None
    deliverable_url: str | None = None


class BountyResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    acceptance_criteria: list
    category: str
    reward_amount: float
    reward_token: str
    poster_id: uuid.UUID
    solver_id: uuid.UUID | None
    status: BountyStatus
    deadline: datetime
    escrow_address: str | None
    deliverable_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BountyListResponse(BaseModel):
    bounties: list[BountyResponse]
    total: int
