"""MCP-style tool functions for the Tectonic protocol.

Each function takes simple primitive arguments (suitable for LLM invocation),
calls the Tectonic SDK, and returns a plain ``dict`` result.  Errors are
caught and returned as ``{"error": "..."}`` so they can be surfaced to the
calling agent without raising exceptions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from tectonic import (
    BountyCreate,
    ContractDeliverRequest,
    ContractFundRequest,
    ContractVerifyRequest,
    NegotiationTerms,
    NegotiationTurnRequest,
    ProposalCreate,
    TectonicClient,
    TurnType,
)

from .config import get_config


def _parse_deadline(deadline: str) -> datetime:
    """Parse an ISO-8601 datetime string into a timezone-aware datetime.

    Handles the ``Z`` UTC suffix which ``datetime.fromisoformat`` does not
    support in Python < 3.11.
    """
    # Normalise trailing Z to +00:00 for compatibility with Python 3.9+
    if deadline.endswith("Z"):
        deadline = deadline[:-1] + "+00:00"
    dt = datetime.fromisoformat(deadline)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _client() -> TectonicClient:
    """Build a TectonicClient from environment configuration."""
    cfg = get_config()
    return TectonicClient(base_url=cfg.api_url, api_key=cfg.api_key)


# ------------------------------------------------------------------
# Poster-side tools
# ------------------------------------------------------------------


async def tectonic_post_bounty(
    title: str,
    description: str,
    criteria: list[str],
    category: str,
    reward: float,
    deadline: str,
) -> dict:
    """Post a new bounty to Tectonic.

    Args:
        title: Short title of the bounty.
        description: Detailed description of the work required.
        criteria: List of acceptance criteria.
        category: Category tag (e.g. "development", "design").
        reward: Reward amount in ETH (or the default token).
        deadline: ISO-8601 deadline string.

    Returns:
        A dict with bounty details or an error message.
    """
    try:
        async with _client() as client:
            bounty = await client.create_bounty(
                BountyCreate(
                    title=title,
                    description=description,
                    acceptance_criteria=criteria,
                    category=category,
                    reward_amount=reward,
                    deadline=_parse_deadline(deadline),
                )
            )
            return {
                "bounty_id": bounty.id,
                "title": bounty.title,
                "status": bounty.status.value,
                "reward_amount": bounty.reward_amount,
                "reward_token": bounty.reward_token,
                "deadline": bounty.deadline.isoformat(),
            }
    except Exception as exc:
        return {"error": str(exc)}


async def tectonic_list_proposals(bounty_id: str) -> dict:
    """List all proposals for a bounty.

    Args:
        bounty_id: The bounty ID to list proposals for.

    Returns:
        A dict with proposals list or an error message.
    """
    try:
        async with _client() as client:
            proposals = await client.list_proposals(bounty_id)
            return {
                "bounty_id": bounty_id,
                "count": len(proposals),
                "proposals": [
                    {
                        "proposal_id": p.id,
                        "solver_id": p.solver_id,
                        "proposed_price": p.proposed_price,
                        "proposed_deadline": p.proposed_deadline.isoformat(),
                        "approach_summary": p.approach_summary,
                        "status": p.status.value,
                    }
                    for p in proposals
                ],
            }
    except Exception as exc:
        return {"error": str(exc)}


async def tectonic_start_negotiation(bounty_id: str, proposal_id: str) -> dict:
    """Start negotiation with a solver.

    Args:
        bounty_id: The bounty ID.
        proposal_id: The proposal ID to negotiate on.

    Returns:
        A dict with negotiation details or an error message.
    """
    try:
        async with _client() as client:
            neg = await client.create_negotiation(bounty_id, proposal_id)
            return {
                "negotiation_id": neg.id,
                "bounty_id": neg.bounty_id,
                "poster_id": neg.poster_id,
                "solver_id": neg.solver_id,
                "status": neg.status.value,
                "max_turns": neg.max_turns,
            }
    except Exception as exc:
        return {"error": str(exc)}


async def tectonic_negotiate(
    negotiation_id: str,
    action: str,
    price: Optional[float] = None,
    deadline: Optional[str] = None,
    deliverables: Optional[list[str]] = None,
    message: Optional[str] = None,
) -> dict:
    """Send a negotiation turn (counter/accept/reject).

    Args:
        negotiation_id: The negotiation ID.
        action: One of "counter", "accept", "reject".
        price: Proposed price (required for counter).
        deadline: Proposed deadline ISO-8601 string (required for counter).
        deliverables: List of deliverables (required for counter).
        message: Optional message to include.

    Returns:
        A dict with turn details or an error message.
    """
    try:
        turn_type = TurnType(action)

        proposed_terms = None
        if turn_type == TurnType.counter:
            if price is None or deadline is None or deliverables is None:
                return {
                    "error": "price, deadline, and deliverables are required for counter-offers"
                }
            proposed_terms = NegotiationTerms(
                price=price,
                deadline=_parse_deadline(deadline),
                deliverables=deliverables,
                acceptance_criteria=deliverables,  # default to deliverables
                revision_rounds=1,
            )

        async with _client() as client:
            turn = await client.submit_turn(
                negotiation_id,
                NegotiationTurnRequest(
                    turn_type=turn_type,
                    proposed_terms=proposed_terms,
                    message=message,
                ),
            )
            return {
                "turn_id": turn.id,
                "negotiation_id": turn.negotiation_id,
                "sequence": turn.sequence,
                "turn_type": turn.turn_type,
                "message": turn.message,
            }
    except Exception as exc:
        return {"error": str(exc)}


async def tectonic_fund_escrow(
    contract_id: str,
    tx_hash: str,
    escrow_address: str,
) -> dict:
    """Fund the escrow for a contract.

    Args:
        contract_id: The contract ID.
        tx_hash: The on-chain transaction hash for funding.
        escrow_address: The escrow smart-contract address.

    Returns:
        A dict with updated contract details or an error message.
    """
    try:
        async with _client() as client:
            contract = await client.fund_contract(
                contract_id,
                ContractFundRequest(
                    funding_tx_hash=tx_hash,
                    escrow_contract_address=escrow_address,
                ),
            )
            return {
                "contract_id": contract.id,
                "status": contract.status.value,
                "amount": contract.amount,
                "escrow_contract_address": contract.escrow_contract_address,
                "funding_tx_hash": contract.funding_tx_hash,
            }
    except Exception as exc:
        return {"error": str(exc)}


async def tectonic_review_delivery(contract_id: str) -> dict:
    """Get delivery details for review.

    Fetches the bounty associated with the contract to get the
    deliverable URL and other details for the poster to review.

    Args:
        contract_id: The contract ID.

    Returns:
        A dict with delivery information or an error message.
    """
    try:
        async with _client() as client:
            # Fetch the bounty to get deliverable_url
            # We need to go through the contract -> bounty path
            # Since we don't have a get_contract endpoint yet,
            # we use the bounty endpoint
            bounty_result = await client.list_bounties(status="delivered")
            matching = [
                b for b in bounty_result.bounties if b.deliverable_url is not None
            ]
            if not matching:
                return {
                    "contract_id": contract_id,
                    "message": "No delivered bounties found. Delivery may not have been submitted yet.",
                }
            # Return the first matching delivery
            bounty = matching[0]
            return {
                "contract_id": contract_id,
                "bounty_id": bounty.id,
                "title": bounty.title,
                "deliverable_url": bounty.deliverable_url,
                "acceptance_criteria": bounty.acceptance_criteria,
                "status": bounty.status.value,
            }
    except Exception as exc:
        return {"error": str(exc)}


async def tectonic_verify_delivery(contract_id: str, approved: bool) -> dict:
    """Verify or dispute a delivery.

    Args:
        contract_id: The contract ID.
        approved: True to approve, False to reject/dispute.

    Returns:
        A dict with updated contract status or an error message.
    """
    try:
        async with _client() as client:
            contract = await client.verify_contract(
                contract_id,
                ContractVerifyRequest(approved=approved),
            )
            return {
                "contract_id": contract.id,
                "status": contract.status.value,
                "approved": approved,
                "amount": contract.amount,
            }
    except Exception as exc:
        return {"error": str(exc)}


async def tectonic_my_bounties() -> dict:
    """Get all bounties posted by the current agent.

    Returns:
        A dict with bounties list or an error message.
    """
    try:
        async with _client() as client:
            result = await client.list_bounties()
            return {
                "total": result.total,
                "bounties": [
                    {
                        "bounty_id": b.id,
                        "title": b.title,
                        "status": b.status.value,
                        "reward_amount": b.reward_amount,
                        "reward_token": b.reward_token,
                    }
                    for b in result.bounties
                ],
            }
    except Exception as exc:
        return {"error": str(exc)}


async def tectonic_my_reputation() -> dict:
    """Get reputation summary for the current agent.

    Returns:
        A dict with reputation details or an error message.
    """
    try:
        cfg = get_config()
        if not cfg.agent_id:
            return {"error": "TECTONIC_AGENT_ID not configured"}
        async with _client() as client:
            rep = await client.get_agent_reputation(cfg.agent_id)
            return {
                "agent_id": rep.agent_id,
                "reputation_score": rep.reputation_score,
                "bounties_posted": rep.bounties_posted,
                "bounties_completed": rep.bounties_completed,
                "recent_events": rep.events[:5],
            }
    except Exception as exc:
        return {"error": str(exc)}


# ------------------------------------------------------------------
# Solver-side tools
# ------------------------------------------------------------------


async def tectonic_browse_bounties(
    category: Optional[str] = None,
    min_reward: Optional[float] = None,
) -> dict:
    """Browse open bounties (solver perspective).

    Args:
        category: Optional category filter.
        min_reward: Optional minimum reward filter (client-side).

    Returns:
        A dict with matching bounties or an error message.
    """
    try:
        async with _client() as client:
            result = await client.list_bounties(status="open", category=category)
            bounties = result.bounties
            if min_reward is not None:
                bounties = [b for b in bounties if b.reward_amount >= min_reward]
            return {
                "total": len(bounties),
                "bounties": [
                    {
                        "bounty_id": b.id,
                        "title": b.title,
                        "description": b.description[:200],
                        "category": b.category,
                        "reward_amount": b.reward_amount,
                        "reward_token": b.reward_token,
                        "deadline": b.deadline.isoformat(),
                        "acceptance_criteria": b.acceptance_criteria,
                    }
                    for b in bounties
                ],
            }
    except Exception as exc:
        return {"error": str(exc)}


async def tectonic_submit_proposal(
    bounty_id: str,
    price: float,
    deadline: str,
    approach: str,
) -> dict:
    """Submit a proposal for a bounty.

    Args:
        bounty_id: The bounty to bid on.
        price: Proposed price.
        deadline: Proposed deadline as ISO-8601 string.
        approach: Summary of the approach / plan.

    Returns:
        A dict with proposal details or an error message.
    """
    try:
        async with _client() as client:
            proposal = await client.create_proposal(
                bounty_id,
                ProposalCreate(
                    proposed_price=price,
                    proposed_deadline=_parse_deadline(deadline),
                    approach_summary=approach,
                ),
            )
            return {
                "proposal_id": proposal.id,
                "bounty_id": proposal.bounty_id,
                "status": proposal.status.value,
                "proposed_price": proposal.proposed_price,
                "proposed_deadline": proposal.proposed_deadline.isoformat(),
            }
    except Exception as exc:
        return {"error": str(exc)}


async def tectonic_submit_delivery(
    contract_id: str,
    deliverable_url: str,
) -> dict:
    """Submit delivery for a contract.

    Args:
        contract_id: The contract ID.
        deliverable_url: URL to the deliverable (e.g. GitHub repo).

    Returns:
        A dict with updated contract details or an error message.
    """
    try:
        async with _client() as client:
            contract = await client.deliver_contract(
                contract_id,
                ContractDeliverRequest(deliverable_url=deliverable_url),
            )
            return {
                "contract_id": contract.id,
                "status": contract.status.value,
                "amount": contract.amount,
            }
    except Exception as exc:
        return {"error": str(exc)}
