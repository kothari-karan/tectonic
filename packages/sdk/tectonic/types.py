"""Pydantic v2 models for the Tectonic Agent Commerce Protocol SDK."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --- Enums ---


class AgentType(str, Enum):
    requester = "requester"
    provider = "provider"
    both = "both"


class EngagementStatus(str, Enum):
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


class EngagementType(str, Enum):
    open = "open"
    direct = "direct"
    invited = "invited"


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


class EngagementCreate(BaseModel):
    """Request body for creating a new engagement."""

    title: str
    description: str
    acceptance_criteria: list[str]
    category: str
    reward_amount: float
    reward_token: str = "ETH"
    deadline: datetime
    engagement_type: EngagementType = EngagementType.open
    target_provider_ids: list[str] = Field(default_factory=list)


class EngagementUpdate(BaseModel):
    """Request body for updating an engagement."""

    provider_id: Optional[str] = None
    status: Optional[EngagementStatus] = None
    deliverable_url: Optional[str] = None


class ProposalCreate(BaseModel):
    """Request body for submitting a proposal on an engagement."""

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
    engagements_posted: int = 0
    engagements_completed: int = 0
    created_at: datetime
    updated_at: datetime


class AgentRegisterResponse(BaseModel):
    """Response returned after registering a new agent, includes the API key."""

    agent: Agent
    api_key: str


class Engagement(BaseModel):
    """Engagement response returned by the API."""

    id: str
    title: str
    description: str
    acceptance_criteria: list[str]
    category: str
    reward_amount: float
    reward_token: str = "ETH"
    requester_id: str
    provider_id: Optional[str] = None
    status: EngagementStatus
    deadline: datetime
    escrow_address: Optional[str] = None
    deliverable_url: Optional[str] = None
    engagement_type: EngagementType = EngagementType.open
    target_provider_ids: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class EngagementListResponse(BaseModel):
    """Response for listing engagements, with pagination total."""

    engagements: list[Engagement]
    total: int


class Proposal(BaseModel):
    """Proposal response returned by the API."""

    id: str
    engagement_id: str
    provider_id: str
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
    engagement_id: str
    proposal_id: str
    requester_id: str
    provider_id: str
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
    engagement_id: str
    negotiation_id: str
    requester_id: str
    provider_id: str
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
    engagements_posted: int
    engagements_completed: int
    events: list[dict] = Field(default_factory=list)


# --- Service Listing Models ---


class RateType(str, Enum):
    fixed = "fixed"
    hourly = "hourly"
    per_deliverable = "per_deliverable"


class ListingAvailability(str, Enum):
    available = "available"
    busy = "busy"
    unavailable = "unavailable"


class ListingCreate(BaseModel):
    """Request body for creating a service listing."""

    title: str
    description: str
    capabilities: list[str]
    rate_type: RateType
    rate_range_min: float
    rate_range_max: float
    response_time_hours: int = 24


class ListingUpdate(BaseModel):
    """Request body for updating a service listing."""

    title: Optional[str] = None
    description: Optional[str] = None
    capabilities: Optional[list[str]] = None
    availability: Optional[ListingAvailability] = None
    rate_range_min: Optional[float] = None
    rate_range_max: Optional[float] = None
    response_time_hours: Optional[int] = None


class ServiceListing(BaseModel):
    """Service listing response returned by the API."""

    id: str
    provider_id: str
    title: str
    description: str
    capabilities: list[str] = Field(default_factory=list)
    rate_type: RateType
    rate_range_min: float
    rate_range_max: float
    availability: ListingAvailability
    response_time_hours: int
    created_at: datetime
    updated_at: datetime


class ListingListResponse(BaseModel):
    """Response for listing service listings, with pagination total."""

    listings: list[ServiceListing]
    total: int


# --- Standing Agreement Models ---


class AgreementStatus(str, Enum):
    active = "active"
    paused = "paused"
    terminated = "terminated"


class AgreementRateType(str, Enum):
    retainer_monthly = "retainer_monthly"
    per_task = "per_task"
    hourly = "hourly"


class AgreementCreate(BaseModel):
    """Request body for creating a standing agreement."""

    provider_id: str
    title: str
    scope_description: str
    rate_type: AgreementRateType
    rate: float
    max_tasks_per_period: Optional[int] = None
    max_spend_per_period: Optional[float] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    agreed_terms: Optional[dict] = None


class AgreementUpdate(BaseModel):
    """Request body for updating a standing agreement."""

    status: Optional[AgreementStatus] = None
    max_tasks_per_period: Optional[int] = None
    max_spend_per_period: Optional[float] = None
    end_date: Optional[datetime] = None


class AgreementTaskCreate(BaseModel):
    """Request body for dispatching a task under an agreement."""

    title: str
    description: str
    reward_amount: float


class StandingAgreement(BaseModel):
    """Standing agreement response returned by the API."""

    id: str
    requester_id: str
    provider_id: str
    title: str
    scope_description: str
    rate_type: AgreementRateType
    rate: float
    max_tasks_per_period: Optional[int] = None
    max_spend_per_period: Optional[float] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    status: AgreementStatus
    agreed_terms: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


class AgreementTask(BaseModel):
    """Agreement task response returned by the API."""

    id: str
    agreement_id: str
    engagement_id: str
    created_at: datetime


class AgreementListResponse(BaseModel):
    """Response for listing standing agreements."""

    agreements: list[StandingAgreement]
    total: int
