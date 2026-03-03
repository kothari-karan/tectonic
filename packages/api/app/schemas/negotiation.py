import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class NegotiationTerms(BaseModel):
    price: float = Field(..., gt=0)
    deadline: datetime
    deliverables: list[str] = Field(..., min_length=1)
    acceptance_criteria: list[str] = Field(..., min_length=1)
    revision_rounds: int = Field(default=1, ge=1)


class NegotiationCreate(BaseModel):
    bounty_id: uuid.UUID
    proposal_id: uuid.UUID


class NegotiationTurnRequest(BaseModel):
    turn_type: Literal["offer", "counter", "accept", "reject"]
    proposed_terms: NegotiationTerms | None = None
    message: str | None = None


class NegotiationTurnResponse(BaseModel):
    id: uuid.UUID
    negotiation_id: uuid.UUID
    agent_id: uuid.UUID
    sequence: int
    turn_type: str
    proposed_terms: dict | None
    message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NegotiationResponse(BaseModel):
    id: uuid.UUID
    bounty_id: uuid.UUID
    proposal_id: uuid.UUID
    poster_id: uuid.UUID
    solver_id: uuid.UUID
    status: str
    current_terms: dict | None
    turn_count: int
    max_turns: int
    created_at: datetime
    updated_at: datetime
    turns: list[NegotiationTurnResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}
