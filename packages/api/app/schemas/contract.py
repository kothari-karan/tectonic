import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ContractCreate(BaseModel):
    engagement_id: uuid.UUID
    negotiation_id: uuid.UUID


class ContractResponse(BaseModel):
    id: uuid.UUID
    engagement_id: uuid.UUID
    negotiation_id: uuid.UUID
    requester_id: uuid.UUID
    provider_id: uuid.UUID
    status: str
    agreed_terms: dict
    terms_hash: str
    escrow_contract_address: str | None
    funding_tx_hash: str | None
    release_tx_hash: str | None
    amount: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContractFundRequest(BaseModel):
    funding_tx_hash: str = Field(..., min_length=1)
    escrow_contract_address: str = Field(..., min_length=1)


class ContractDeliverRequest(BaseModel):
    deliverable_url: str = Field(..., min_length=1)


class ContractVerifyRequest(BaseModel):
    approved: bool
