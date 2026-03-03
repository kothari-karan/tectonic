import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProposalCreate(BaseModel):
    proposed_price: float = Field(..., gt=0)
    proposed_deadline: datetime
    approach_summary: str = Field(..., min_length=1)


class ProposalResponse(BaseModel):
    id: uuid.UUID
    bounty_id: uuid.UUID
    solver_id: uuid.UUID
    status: str
    proposed_price: float
    proposed_deadline: datetime
    approach_summary: str
    created_at: datetime

    model_config = {"from_attributes": True}
