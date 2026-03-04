import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.agreement import AgreementRateType, AgreementStatus


class AgreementCreate(BaseModel):
    provider_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=500)
    scope_description: str = Field(..., min_length=1)
    rate_type: AgreementRateType
    rate: float = Field(..., gt=0)
    max_tasks_per_period: int | None = None
    max_spend_per_period: float | None = None
    start_date: datetime
    end_date: datetime | None = None
    agreed_terms: dict | None = None


class AgreementUpdate(BaseModel):
    status: AgreementStatus | None = None
    max_tasks_per_period: int | None = None
    max_spend_per_period: float | None = None
    end_date: datetime | None = None


class AgreementTaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    reward_amount: float = Field(..., gt=0)


class AgreementResponse(BaseModel):
    id: uuid.UUID
    requester_id: uuid.UUID
    provider_id: uuid.UUID
    title: str
    scope_description: str
    rate_type: AgreementRateType
    rate: float
    max_tasks_per_period: int | None
    max_spend_per_period: float | None
    start_date: datetime
    end_date: datetime | None
    status: AgreementStatus
    agreed_terms: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgreementTaskResponse(BaseModel):
    id: uuid.UUID
    agreement_id: uuid.UUID
    engagement_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class AgreementListResponse(BaseModel):
    agreements: list[AgreementResponse]
    total: int
