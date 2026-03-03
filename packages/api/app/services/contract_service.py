import hashlib
import json
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bounty import Bounty, BountyStatus
from app.models.contract import Contract, ContractStatus
from app.models.negotiation import Negotiation, NegotiationStatus
from app.services.reputation_service import record_event


def compute_terms_hash(terms: dict) -> str:
    """Compute keccak256 hash of the agreed terms JSON."""
    # Use a deterministic JSON serialization
    terms_json = json.dumps(terms, sort_keys=True, default=str)
    # Use hashlib's sha3_256 (keccak256 equivalent available in Python)
    hash_bytes = hashlib.sha3_256(terms_json.encode("utf-8")).digest()
    return "0x" + hash_bytes.hex()


async def create_contract_from_negotiation(
    bounty_id: uuid.UUID,
    negotiation_id: uuid.UUID,
    agent_id: uuid.UUID,
    db: AsyncSession,
) -> Contract:
    """Create a contract from an agreed negotiation."""
    negotiation = await db.get(Negotiation, negotiation_id)
    if negotiation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Negotiation not found",
        )

    if negotiation.status != NegotiationStatus.agreed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Negotiation must be agreed before creating a contract",
        )

    if str(negotiation.bounty_id) != str(bounty_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Negotiation does not match the specified bounty",
        )

    # Verify the agent is a party to the negotiation
    agent_id_str = str(agent_id)
    if agent_id_str != str(negotiation.poster_id) and agent_id_str != str(negotiation.solver_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a party to this negotiation",
        )

    agreed_terms = negotiation.current_terms or {}
    terms_hash = compute_terms_hash(agreed_terms)

    # Get the amount from agreed terms or from the bounty
    amount = agreed_terms.get("price", 0.0)

    contract = Contract(
        bounty_id=bounty_id,
        negotiation_id=negotiation_id,
        poster_id=negotiation.poster_id,
        solver_id=negotiation.solver_id,
        status=ContractStatus.pending_funding,
        agreed_terms=agreed_terms,
        terms_hash=terms_hash,
        amount=amount,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(contract)

    # Update bounty status
    bounty = await db.get(Bounty, bounty_id)
    if bounty:
        bounty.status = BountyStatus.agreed
        bounty.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(contract)
    return contract


async def fund_contract(
    contract_id: uuid.UUID,
    funding_tx_hash: str,
    escrow_contract_address: str,
    agent_id: uuid.UUID,
    db: AsyncSession,
) -> Contract:
    """Fund a contract (poster only)."""
    contract = await db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )

    if str(contract.poster_id) != str(agent_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the poster can fund this contract",
        )

    if contract.status != ContractStatus.pending_funding:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Contract cannot be funded in status: {contract.status}",
        )

    contract.funding_tx_hash = funding_tx_hash
    contract.escrow_contract_address = escrow_contract_address
    contract.status = ContractStatus.funded
    contract.updated_at = datetime.now(timezone.utc)

    # Update bounty status to in_progress
    bounty = await db.get(Bounty, contract.bounty_id)
    if bounty:
        bounty.status = BountyStatus.in_progress
        bounty.escrow_address = escrow_contract_address
        bounty.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(contract)
    return contract


async def deliver_contract(
    contract_id: uuid.UUID,
    deliverable_url: str,
    agent_id: uuid.UUID,
    db: AsyncSession,
) -> Contract:
    """Mark contract as delivered (solver only)."""
    contract = await db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )

    if str(contract.solver_id) != str(agent_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the solver can deliver on this contract",
        )

    if contract.status not in (ContractStatus.funded, ContractStatus.in_progress):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Contract cannot be delivered in status: {contract.status}",
        )

    contract.status = ContractStatus.delivered
    contract.updated_at = datetime.now(timezone.utc)

    # Update bounty
    bounty = await db.get(Bounty, contract.bounty_id)
    if bounty:
        bounty.status = BountyStatus.delivered
        bounty.deliverable_url = deliverable_url
        bounty.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(contract)
    return contract


async def verify_contract(
    contract_id: uuid.UUID,
    approved: bool,
    agent_id: uuid.UUID,
    db: AsyncSession,
) -> Contract:
    """Verify delivery (poster only). If approved, triggers settlement + reputation."""
    contract = await db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )

    if str(contract.poster_id) != str(agent_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the poster can verify this contract",
        )

    if contract.status != ContractStatus.delivered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Contract cannot be verified in status: {contract.status}",
        )

    if approved:
        contract.status = ContractStatus.settled
        contract.updated_at = datetime.now(timezone.utc)

        # Update bounty
        bounty = await db.get(Bounty, contract.bounty_id)
        if bounty:
            bounty.status = BountyStatus.settled
            bounty.updated_at = datetime.now(timezone.utc)

        # Record reputation events
        from app.models.agent import Agent

        solver = await db.get(Agent, contract.solver_id)
        if solver:
            solver.bounties_completed += 1
            solver.updated_at = datetime.now(timezone.utc)

        await record_event(
            agent_id=contract.solver_id,
            event_type="bounty_completed",
            contract_id=contract.id,
            db=db,
        )
        await record_event(
            agent_id=contract.poster_id,
            event_type="bounty_posted",
            contract_id=contract.id,
            db=db,
        )
    else:
        contract.status = ContractStatus.disputed
        contract.updated_at = datetime.now(timezone.utc)

        bounty = await db.get(Bounty, contract.bounty_id)
        if bounty:
            bounty.status = BountyStatus.disputed
            bounty.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(contract)
    return contract


async def dispute_contract(
    contract_id: uuid.UUID,
    agent_id: uuid.UUID,
    db: AsyncSession,
) -> Contract:
    """Dispute a contract (either party)."""
    contract = await db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )

    agent_id_str = str(agent_id)
    if agent_id_str != str(contract.poster_id) and agent_id_str != str(contract.solver_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only contract parties can dispute",
        )

    if contract.status in (ContractStatus.settled, ContractStatus.resolved):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Contract cannot be disputed in status: {contract.status}",
        )

    contract.status = ContractStatus.disputed
    contract.updated_at = datetime.now(timezone.utc)

    bounty = await db.get(Bounty, contract.bounty_id)
    if bounty:
        bounty.status = BountyStatus.disputed
        bounty.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(contract)
    return contract
