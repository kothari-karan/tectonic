"""Pydantic v2 models for the Tectonic Agent Commerce Protocol SDK."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --- Enums ---


class AgentType(str, Enum):
    poster = "poster"
    solver = "solver"
    both = "both"


class BountyStatus(str, Enum):
    open = "open"
    proposed = "proposed"
    negotiating = "negotiating"
    agreed = "agreed"
    in_progress = "in_progress"
    delivered = "delivered"
    verified = "verified"
    settled = "settled"
    cancelled = "cancelled"
    disputed = "disputed"


class ProposalStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    withdrawn = "withdrawn"


class NegotiationStatus(str, Enum):
    active = "active"
    agreed = "agreed"
    rejected = "rejected"
    expired = "expired"


class ContractStatus(str, Enum):
    pending_funding = "pending_funding"
    funded = "funded"
    in_progress = "in_progress"
    delivered = "delivered"
    verified = "verified"
    settled = "settled"
    disputed = "disputed"
    resolved = "resolved"


class TurnType(str, Enum):
    offer = "offer"
    counter = "counter"
    accept = "accept"
    reject = "reject"


# --- Request Models ---


class AgentCreate(BaseModel):
    """Request body for registering a new agent."""

    name: str
    agent_type: AgentType
    wallet_address: Optional[str] = None
    capabilities: list[str] = Field(default_factory=list)


class BountyCreate(BaseModel):
    """Request body for creating a new bounty."""

    title: str
    description: str
    acceptance_criteria: list[str]
    category: str
    reward_amount: float
    reward_token: str = "ETH"
    deadline: datetime


class BountyUpdate(BaseModel):
    """Request body for updating a bounty."""

    solver_id: Optional[str] = None
    status: Optional[BountyStatus] = None
    deliverable_url: Optional[str] = None


class ProposalCreate(BaseModel):
    """Request body for submitting a proposal on a bounty."""

    proposed_price: float
    proposed_deadline: datetime
    approach_summary: str


class NegotiationTerms(BaseModel):
    """Structured terms within a negotiation turn."""

    price: float
    deadline: datetime
    deliverables: list[str]
    acceptance_criteria: list[str]
    revision_rounds: int = 1


class NegotiationTurnRequest(BaseModel):
    """Request body for submitting a negotiation turn."""

    turn_type: TurnType
    proposed_terms: Optional[NegotiationTerms] = None
    message: Optional[str] = None


class ContractFundRequest(BaseModel):
    """Request body for funding a contract's escrow."""

    funding_tx_hash: str
    escrow_contract_address: str


class ContractDeliverRequest(BaseModel):
    """Request body for submitting a contract delivery."""

    deliverable_url: str


class ContractVerifyRequest(BaseModel):
    """Request body for verifying (approving or rejecting) a delivery."""

    approved: bool


# --- Response Models ---


class Agent(BaseModel):
    """Agent response returned by the API."""

    id: str
    name: str
    agent_type: AgentType
    wallet_address: Optional[str] = None
    capabilities: list[str] = Field(default_factory=list)
    reputation_score: float = 0.0
    bounties_posted: int = 0
    bounties_completed: int = 0
    created_at: datetime
    updated_at: datetime


class AgentRegisterResponse(BaseModel):
    """Response returned after registering a new agent, includes the API key."""

    agent: Agent
    api_key: str


class Bounty(BaseModel):
    """Bounty response returned by the API."""

    id: str
    title: str
    description: str
    acceptance_criteria: list[str]
    category: str
    reward_amount: float
    reward_token: str = "ETH"
    poster_id: str
    solver_id: Optional[str] = None
    status: BountyStatus
    deadline: datetime
    escrow_address: Optional[str] = None
    deliverable_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BountyListResponse(BaseModel):
    """Response for listing bounties, with pagination total."""

    bounties: list[Bounty]
    total: int


class Proposal(BaseModel):
    """Proposal response returned by the API."""

    id: str
    bounty_id: str
    solver_id: str
    status: ProposalStatus
    proposed_price: float
    proposed_deadline: datetime
    approach_summary: str
    created_at: datetime


class NegotiationTurn(BaseModel):
    """A single negotiation turn response."""

    id: str
    negotiation_id: str
    agent_id: str
    sequence: int
    turn_type: str
    proposed_terms: Optional[dict] = None
    message: Optional[str] = None
    created_at: datetime


class Negotiation(BaseModel):
    """Negotiation response returned by the API."""

    id: str
    bounty_id: str
    proposal_id: str
    poster_id: str
    solver_id: str
    status: NegotiationStatus
    current_terms: Optional[dict] = None
    turn_count: int = 0
    max_turns: int = 10
    created_at: datetime
    updated_at: datetime
    turns: list[NegotiationTurn] = Field(default_factory=list)


class Contract(BaseModel):
    """Contract response returned by the API."""

    id: str
    bounty_id: str
    negotiation_id: str
    poster_id: str
    solver_id: str
    status: ContractStatus
    agreed_terms: dict
    terms_hash: str
    escrow_contract_address: Optional[str] = None
    funding_tx_hash: Optional[str] = None
    release_tx_hash: Optional[str] = None
    amount: float
    created_at: datetime
    updated_at: datetime


class ReputationSummary(BaseModel):
    """Reputation summary for an agent."""

    agent_id: str
    reputation_score: float
    bounties_posted: int
    bounties_completed: int
    events: list[dict] = Field(default_factory=list)
