import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.agent import AgentType


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    agent_type: AgentType
    wallet_address: str | None = None
    capabilities: list[str] = Field(default_factory=list)


class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    agent_type: AgentType
    wallet_address: str | None
    capabilities: list
    reputation_score: float
    engagements_posted: int
    engagements_completed: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentRegisterResponse(BaseModel):
    agent: AgentResponse
    api_key: str

    model_config = {"from_attributes": True}
