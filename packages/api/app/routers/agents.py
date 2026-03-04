import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_key import generate_api_key, hash_api_key
from app.database import get_db
from app.models.agent import Agent
from app.models.bounty import EngagementStatus
from app.schemas.agent import AgentCreate, AgentRegisterResponse, AgentResponse
from app.schemas.bounty import EngagementListResponse, EngagementResponse
from app.services.bounty_service import get_provider_inbox
from app.services.reputation_service import get_agent_reputation

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post(
    "/register", response_model=AgentRegisterResponse, status_code=http_status.HTTP_201_CREATED
)
async def register_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new agent and return an API key."""
    # Check for duplicate name
    result = await db.execute(select(Agent).where(Agent.name == agent_data.name))
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"Agent with name '{agent_data.name}' already exists",
        )

    api_key = generate_api_key()
    api_key_hashed = hash_api_key(api_key)

    agent = Agent(
        name=agent_data.name,
        agent_type=agent_data.agent_type,
        wallet_address=agent_data.wallet_address,
        api_key_hash=api_key_hashed,
        capabilities=agent_data.capabilities,
    )
    db.add(agent)
    await db.flush()
    await db.refresh(agent)

    return AgentRegisterResponse(
        agent=AgentResponse.model_validate(agent),
        api_key=api_key,
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get agent details by ID."""
    agent = await db.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    return AgentResponse.model_validate(agent)


@router.get("/{agent_id}/reputation")
async def get_reputation(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get agent reputation details."""
    agent = await db.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    return await get_agent_reputation(agent_id, db)


@router.get("/{agent_id}/inbox", response_model=EngagementListResponse)
async def get_inbox(
    agent_id: uuid.UUID,
    status: EngagementStatus | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get engagements targeted at this provider (direct/invited).

    Returns engagements where the agent appears in ``target_provider_ids``.
    """
    agent = await db.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    engagements, total = await get_provider_inbox(
        agent_id,
        db,
        status_filter=status,
        skip=skip,
        limit=limit,
    )
    return EngagementListResponse(
        engagements=[EngagementResponse.model_validate(e) for e in engagements],
        total=total,
    )
