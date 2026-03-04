import uuid
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.agreement import AgreementStatus, AgreementTask, StandingAgreement
from app.models.bounty import Engagement, EngagementStatus, EngagementType
from app.schemas.agreement import AgreementCreate, AgreementTaskCreate, AgreementUpdate


async def create_agreement(
    data: AgreementCreate,
    requester: Agent,
    db: AsyncSession,
) -> StandingAgreement:
    """Create a new standing agreement."""
    if str(data.provider_id) == str(requester.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create an agreement with yourself",
        )

    # Verify provider exists
    provider = await db.get(Agent, data.provider_id)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found",
        )

    agreement = StandingAgreement(
        requester_id=requester.id,
        provider_id=data.provider_id,
        title=data.title,
        scope_description=data.scope_description,
        rate_type=data.rate_type,
        rate=data.rate,
        max_tasks_per_period=data.max_tasks_per_period,
        max_spend_per_period=data.max_spend_per_period,
        start_date=data.start_date,
        end_date=data.end_date,
        agreed_terms=data.agreed_terms,
        status=AgreementStatus.active,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(agreement)
    await db.flush()
    await db.refresh(agreement)
    return agreement


async def get_agreement(agreement_id: uuid.UUID, db: AsyncSession) -> StandingAgreement:
    """Get a standing agreement by ID."""
    agreement = await db.get(StandingAgreement, agreement_id)
    if agreement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agreement not found",
        )
    return agreement


async def list_agreements(
    db: AsyncSession,
    agent_id: uuid.UUID | None = None,
    status_filter: AgreementStatus | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[StandingAgreement], int]:
    """List standing agreements with optional filters."""
    query = select(StandingAgreement)
    count_query = select(func.count()).select_from(StandingAgreement)

    if agent_id is not None:
        condition = (
            (StandingAgreement.requester_id == agent_id)
            | (StandingAgreement.provider_id == agent_id)
        )
        query = query.where(condition)
        count_query = count_query.where(condition)

    if status_filter is not None:
        query = query.where(StandingAgreement.status == status_filter)
        count_query = count_query.where(StandingAgreement.status == status_filter)

    query = query.order_by(StandingAgreement.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    agreements = list(result.scalars().all())

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    return agreements, total


async def update_agreement(
    agreement_id: uuid.UUID,
    data: AgreementUpdate,
    agent: Agent,
    db: AsyncSession,
) -> StandingAgreement:
    """Update a standing agreement (parties only)."""
    agreement = await get_agreement(agreement_id, db)

    agent_id_str = str(agent.id)
    if agent_id_str not in (str(agreement.requester_id), str(agreement.provider_id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only agreement parties can update it",
        )

    if data.status is not None:
        agreement.status = data.status
    if data.max_tasks_per_period is not None:
        agreement.max_tasks_per_period = data.max_tasks_per_period
    if data.max_spend_per_period is not None:
        agreement.max_spend_per_period = data.max_spend_per_period
    if data.end_date is not None:
        agreement.end_date = data.end_date

    agreement.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(agreement)
    return agreement


async def dispatch_task(
    agreement_id: uuid.UUID,
    data: AgreementTaskCreate,
    agent: Agent,
    db: AsyncSession,
) -> AgreementTask:
    """Dispatch a task under a standing agreement.

    Creates a direct engagement that skips negotiation (terms are pre-agreed).
    Only the requester can dispatch tasks.
    """
    agreement = await get_agreement(agreement_id, db)

    if str(agent.id) != str(agreement.requester_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the requester can dispatch tasks",
        )

    if agreement.status != AgreementStatus.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agreement is not active",
        )

    # Create a direct engagement for the provider
    engagement = Engagement(
        title=data.title,
        description=data.description,
        acceptance_criteria=[],
        category="standing_agreement",
        reward_amount=data.reward_amount,
        reward_token="ETH",
        engagement_type=EngagementType.direct,
        target_provider_ids=[str(agreement.provider_id)],
        requester_id=agreement.requester_id,
        provider_id=agreement.provider_id,
        deadline=datetime.now(timezone.utc) + timedelta(days=30),
        status=EngagementStatus.in_progress,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(engagement)
    await db.flush()
    await db.refresh(engagement)

    # Link to agreement
    task = AgreementTask(
        agreement_id=agreement.id,
        engagement_id=engagement.id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task
