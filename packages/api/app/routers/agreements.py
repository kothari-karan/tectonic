import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_key import get_current_agent
from app.database import get_db
from app.models.agent import Agent
from app.models.agreement import AgreementStatus
from app.schemas.agreement import (
    AgreementCreate,
    AgreementListResponse,
    AgreementResponse,
    AgreementTaskCreate,
    AgreementTaskResponse,
    AgreementUpdate,
)
from app.services.agreement_service import (
    create_agreement,
    dispatch_task,
    get_agreement,
    list_agreements,
    update_agreement,
)

router = APIRouter(prefix="/agreements", tags=["agreements"])


@router.post("", response_model=AgreementResponse, status_code=201)
async def create_agreement_endpoint(
    data: AgreementCreate,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Create a new standing agreement (requester proposes)."""
    agreement = await create_agreement(data, agent, db)
    return AgreementResponse.model_validate(agreement)


@router.get("", response_model=AgreementListResponse)
async def list_agreements_endpoint(
    agent_id: uuid.UUID | None = Query(None),
    status: AgreementStatus | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List standing agreements with optional filters."""
    agreements, total = await list_agreements(
        db,
        agent_id=agent_id,
        status_filter=status,
        skip=skip,
        limit=limit,
    )
    return AgreementListResponse(
        agreements=[AgreementResponse.model_validate(a) for a in agreements],
        total=total,
    )


@router.get("/{agreement_id}", response_model=AgreementResponse)
async def get_agreement_endpoint(
    agreement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a standing agreement by ID."""
    agreement = await get_agreement(agreement_id, db)
    return AgreementResponse.model_validate(agreement)


@router.patch("/{agreement_id}", response_model=AgreementResponse)
async def update_agreement_endpoint(
    agreement_id: uuid.UUID,
    data: AgreementUpdate,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Update a standing agreement (pause/terminate)."""
    agreement = await update_agreement(agreement_id, data, agent, db)
    return AgreementResponse.model_validate(agreement)


@router.post("/{agreement_id}/tasks", response_model=AgreementTaskResponse, status_code=201)
async def dispatch_task_endpoint(
    agreement_id: uuid.UUID,
    data: AgreementTaskCreate,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Dispatch a task under a standing agreement.

    Creates a direct engagement that skips negotiation (terms pre-agreed).
    """
    task = await dispatch_task(agreement_id, data, agent, db)
    return AgreementTaskResponse.model_validate(task)
