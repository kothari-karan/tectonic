import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api_key import get_current_agent
from app.database import get_db
from app.models.agent import Agent
from app.schemas.contract import (
    ContractCreate,
    ContractDeliverRequest,
    ContractFundRequest,
    ContractResponse,
    ContractVerifyRequest,
)
from app.services.contract_service import (
    create_contract_from_negotiation,
    deliver_contract,
    dispute_contract,
    fund_contract,
    verify_contract,
)

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    contract_data: ContractCreate,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Create a contract from an agreed negotiation (requires authentication)."""
    contract = await create_contract_from_negotiation(
        engagement_id=contract_data.engagement_id,
        negotiation_id=contract_data.negotiation_id,
        agent_id=agent.id,
        db=db,
    )
    return ContractResponse.model_validate(contract)


@router.post("/{contract_id}/fund", response_model=ContractResponse)
async def fund_contract_endpoint(
    contract_id: uuid.UUID,
    fund_data: ContractFundRequest,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Fund a contract (requires authentication - requester only)."""
    contract = await fund_contract(
        contract_id=contract_id,
        funding_tx_hash=fund_data.funding_tx_hash,
        escrow_contract_address=fund_data.escrow_contract_address,
        agent_id=agent.id,
        db=db,
    )
    return ContractResponse.model_validate(contract)


@router.post("/{contract_id}/deliver", response_model=ContractResponse)
async def deliver_contract_endpoint(
    contract_id: uuid.UUID,
    deliver_data: ContractDeliverRequest,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Mark contract as delivered (requires authentication - provider only)."""
    contract = await deliver_contract(
        contract_id=contract_id,
        deliverable_url=deliver_data.deliverable_url,
        agent_id=agent.id,
        db=db,
    )
    return ContractResponse.model_validate(contract)


@router.post("/{contract_id}/verify", response_model=ContractResponse)
async def verify_contract_endpoint(
    contract_id: uuid.UUID,
    verify_data: ContractVerifyRequest,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Verify contract delivery (requires authentication - requester only)."""
    contract = await verify_contract(
        contract_id=contract_id,
        approved=verify_data.approved,
        agent_id=agent.id,
        db=db,
    )
    return ContractResponse.model_validate(contract)


@router.post("/{contract_id}/dispute", response_model=ContractResponse)
async def dispute_contract_endpoint(
    contract_id: uuid.UUID,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Dispute a contract (requires authentication - either party)."""
    contract = await dispute_contract(
        contract_id=contract_id,
        agent_id=agent.id,
        db=db,
    )
    return ContractResponse.model_validate(contract)
