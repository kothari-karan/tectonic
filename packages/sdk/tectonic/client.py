"""Async HTTP client for the Tectonic Agent Commerce Protocol API."""

from __future__ import annotations

import httpx

from .types import (
    Agent,
    AgentCreate,
    AgentRegisterResponse,
    AgreementCreate,
    AgreementListResponse,
    AgreementTask,
    AgreementTaskCreate,
    AgreementUpdate,
    Engagement,
    EngagementCreate,
    EngagementListResponse,
    EngagementUpdate,
    Contract,
    ContractDeliverRequest,
    ContractFundRequest,
    ContractVerifyRequest,
    ListingCreate,
    ListingListResponse,
    ListingUpdate,
    Negotiation,
    NegotiationTurn,
    NegotiationTurnRequest,
    Proposal,
    ProposalCreate,
    ReputationSummary,
    ServiceListing,
    StandingAgreement,
)


class TectonicClient:
    """Async HTTP client wrapping the Tectonic API.

    Usage::

        async with TectonicClient("http://localhost:8000", api_key="tec_...") as client:
            engagement = await client.create_engagement(EngagementCreate(...))
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._build_default_headers(api_key),
            timeout=30.0,
        )

    @staticmethod
    def _build_default_headers(api_key: str | None) -> dict[str, str]:
        if api_key:
            return {"X-API-Key": api_key}
        return {}

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> TectonicClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    def _auth_headers(self, api_key: str | None = None) -> dict[str, str]:
        """Return auth headers, preferring the explicitly-passed key."""
        key = api_key or self.api_key
        if key:
            return {"X-API-Key": key}
        return {}

    # ------------------------------------------------------------------
    # Agents
    # ------------------------------------------------------------------

    async def register_agent(self, data: AgentCreate) -> AgentRegisterResponse:
        """Register a new agent and receive an API key."""
        resp = await self._client.post(
            "/agents/register",
            json=data.model_dump(mode="json"),
        )
        resp.raise_for_status()
        return AgentRegisterResponse.model_validate(resp.json())

    async def get_agent(self, agent_id: str) -> Agent:
        """Retrieve an agent by its ID."""
        resp = await self._client.get(f"/agents/{agent_id}")
        resp.raise_for_status()
        return Agent.model_validate(resp.json())

    async def get_agent_reputation(self, agent_id: str) -> ReputationSummary:
        """Retrieve the reputation summary for an agent."""
        resp = await self._client.get(f"/agents/{agent_id}/reputation")
        resp.raise_for_status()
        return ReputationSummary.model_validate(resp.json())

    async def get_inbox(
        self,
        agent_id: str,
        status: str | None = None,
    ) -> EngagementListResponse:
        """Get engagements targeted at a provider (direct/invited)."""
        params: dict[str, str] = {}
        if status is not None:
            params["status"] = status
        resp = await self._client.get(f"/agents/{agent_id}/inbox", params=params)
        resp.raise_for_status()
        return EngagementListResponse.model_validate(resp.json())

    # ------------------------------------------------------------------
    # Engagements
    # ------------------------------------------------------------------

    async def create_engagement(self, data: EngagementCreate) -> Engagement:
        """Create a new engagement."""
        resp = await self._client.post(
            "/engagements",
            json=data.model_dump(mode="json"),
        )
        resp.raise_for_status()
        return Engagement.model_validate(resp.json())

    async def list_engagements(
        self,
        status: str | None = None,
        category: str | None = None,
    ) -> EngagementListResponse:
        """List engagements, optionally filtered by status and/or category."""
        params: dict[str, str] = {}
        if status is not None:
            params["status"] = status
        if category is not None:
            params["category"] = category
        resp = await self._client.get("/engagements", params=params)
        resp.raise_for_status()
        return EngagementListResponse.model_validate(resp.json())

    async def get_engagement(self, engagement_id: str) -> Engagement:
        """Retrieve a single engagement by ID."""
        resp = await self._client.get(f"/engagements/{engagement_id}")
        resp.raise_for_status()
        return Engagement.model_validate(resp.json())

    async def update_engagement(self, engagement_id: str, data: EngagementUpdate) -> Engagement:
        """Update an existing engagement."""
        resp = await self._client.patch(
            f"/engagements/{engagement_id}",
            json=data.model_dump(mode="json", exclude_none=True),
        )
        resp.raise_for_status()
        return Engagement.model_validate(resp.json())

    # ------------------------------------------------------------------
    # Proposals
    # ------------------------------------------------------------------

    async def create_proposal(
        self,
        engagement_id: str,
        data: ProposalCreate,
    ) -> Proposal:
        """Submit a proposal on an engagement."""
        resp = await self._client.post(
            f"/engagements/{engagement_id}/proposals",
            json=data.model_dump(mode="json"),
        )
        resp.raise_for_status()
        return Proposal.model_validate(resp.json())

    async def list_proposals(self, engagement_id: str) -> list[Proposal]:
        """List all proposals for an engagement."""
        resp = await self._client.get(f"/engagements/{engagement_id}/proposals")
        resp.raise_for_status()
        raw = resp.json()
        # The API may return either a bare list or an object with a
        # ``proposals`` key.  Handle both for robustness.
        items = raw if isinstance(raw, list) else raw.get("proposals", raw)
        return [Proposal.model_validate(item) for item in items]

    # ------------------------------------------------------------------
    # Negotiations
    # ------------------------------------------------------------------

    async def create_negotiation(
        self,
        engagement_id: str,
        proposal_id: str,
    ) -> Negotiation:
        """Start a negotiation between requester and provider."""
        resp = await self._client.post(
            "/negotiations",
            json={"engagement_id": engagement_id, "proposal_id": proposal_id},
        )
        resp.raise_for_status()
        return Negotiation.model_validate(resp.json())

    async def get_negotiation(self, negotiation_id: str) -> Negotiation:
        """Retrieve a negotiation by ID."""
        resp = await self._client.get(f"/negotiations/{negotiation_id}")
        resp.raise_for_status()
        return Negotiation.model_validate(resp.json())

    async def submit_turn(
        self,
        negotiation_id: str,
        data: NegotiationTurnRequest,
    ) -> NegotiationTurn:
        """Submit a negotiation turn (offer, counter, accept, reject)."""
        resp = await self._client.post(
            f"/negotiations/{negotiation_id}/turns",
            json=data.model_dump(mode="json", exclude_none=True),
        )
        resp.raise_for_status()
        return NegotiationTurn.model_validate(resp.json())

    async def list_turns(self, negotiation_id: str) -> list[NegotiationTurn]:
        """List all turns in a negotiation."""
        resp = await self._client.get(f"/negotiations/{negotiation_id}/turns")
        resp.raise_for_status()
        raw = resp.json()
        items = raw if isinstance(raw, list) else raw.get("turns", raw)
        return [NegotiationTurn.model_validate(item) for item in items]

    # ------------------------------------------------------------------
    # Contracts
    # ------------------------------------------------------------------

    async def create_contract(
        self,
        engagement_id: str,
        negotiation_id: str,
    ) -> Contract:
        """Create a contract from an agreed negotiation."""
        resp = await self._client.post(
            "/contracts",
            json={"engagement_id": engagement_id, "negotiation_id": negotiation_id},
        )
        resp.raise_for_status()
        return Contract.model_validate(resp.json())

    async def fund_contract(
        self,
        contract_id: str,
        data: ContractFundRequest,
    ) -> Contract:
        """Record escrow funding for a contract."""
        resp = await self._client.post(
            f"/contracts/{contract_id}/fund",
            json=data.model_dump(mode="json"),
        )
        resp.raise_for_status()
        return Contract.model_validate(resp.json())

    async def deliver_contract(
        self,
        contract_id: str,
        data: ContractDeliverRequest,
    ) -> Contract:
        """Submit a deliverable for a contract."""
        resp = await self._client.post(
            f"/contracts/{contract_id}/deliver",
            json=data.model_dump(mode="json"),
        )
        resp.raise_for_status()
        return Contract.model_validate(resp.json())

    async def verify_contract(
        self,
        contract_id: str,
        data: ContractVerifyRequest,
    ) -> Contract:
        """Verify (approve or reject) a contract delivery."""
        resp = await self._client.post(
            f"/contracts/{contract_id}/verify",
            json=data.model_dump(mode="json"),
        )
        resp.raise_for_status()
        return Contract.model_validate(resp.json())

    async def dispute_contract(self, contract_id: str) -> Contract:
        """Raise a dispute on a contract."""
        resp = await self._client.post(f"/contracts/{contract_id}/dispute")
        resp.raise_for_status()
        return Contract.model_validate(resp.json())

    # ------------------------------------------------------------------
    # Service Listings
    # ------------------------------------------------------------------

    async def create_listing(self, data: ListingCreate) -> ServiceListing:
        """Create a new service listing."""
        resp = await self._client.post(
            "/listings",
            json=data.model_dump(mode="json"),
        )
        resp.raise_for_status()
        return ServiceListing.model_validate(resp.json())

    async def list_listings(
        self,
        availability: str | None = None,
        capability: str | None = None,
    ) -> ListingListResponse:
        """List service listings with optional filters."""
        params: dict[str, str] = {}
        if availability is not None:
            params["availability"] = availability
        if capability is not None:
            params["capability"] = capability
        resp = await self._client.get("/listings", params=params)
        resp.raise_for_status()
        return ListingListResponse.model_validate(resp.json())

    async def get_listing(self, listing_id: str) -> ServiceListing:
        """Get a service listing by ID."""
        resp = await self._client.get(f"/listings/{listing_id}")
        resp.raise_for_status()
        return ServiceListing.model_validate(resp.json())

    async def update_listing(self, listing_id: str, data: ListingUpdate) -> ServiceListing:
        """Update a service listing."""
        resp = await self._client.patch(
            f"/listings/{listing_id}",
            json=data.model_dump(mode="json", exclude_none=True),
        )
        resp.raise_for_status()
        return ServiceListing.model_validate(resp.json())

    async def engage_listing(
        self,
        listing_id: str,
        title: str,
        description: str,
        reward_amount: float,
    ) -> Engagement:
        """Create a direct engagement from a service listing."""
        resp = await self._client.post(
            f"/listings/{listing_id}/engage",
            params={
                "title": title,
                "description": description,
                "reward_amount": str(reward_amount),
            },
        )
        resp.raise_for_status()
        return Engagement.model_validate(resp.json())

    # ------------------------------------------------------------------
    # Standing Agreements
    # ------------------------------------------------------------------

    async def create_agreement(self, data: AgreementCreate) -> StandingAgreement:
        """Create a new standing agreement."""
        resp = await self._client.post(
            "/agreements",
            json=data.model_dump(mode="json"),
        )
        resp.raise_for_status()
        return StandingAgreement.model_validate(resp.json())

    async def list_agreements(
        self,
        agent_id: str | None = None,
        status: str | None = None,
    ) -> AgreementListResponse:
        """List standing agreements with optional filters."""
        params: dict[str, str] = {}
        if agent_id is not None:
            params["agent_id"] = agent_id
        if status is not None:
            params["status"] = status
        resp = await self._client.get("/agreements", params=params)
        resp.raise_for_status()
        return AgreementListResponse.model_validate(resp.json())

    async def get_agreement(self, agreement_id: str) -> StandingAgreement:
        """Get a standing agreement by ID."""
        resp = await self._client.get(f"/agreements/{agreement_id}")
        resp.raise_for_status()
        return StandingAgreement.model_validate(resp.json())

    async def update_agreement(
        self,
        agreement_id: str,
        data: AgreementUpdate,
    ) -> StandingAgreement:
        """Update a standing agreement (pause/terminate)."""
        resp = await self._client.patch(
            f"/agreements/{agreement_id}",
            json=data.model_dump(mode="json", exclude_none=True),
        )
        resp.raise_for_status()
        return StandingAgreement.model_validate(resp.json())

    async def dispatch_task(
        self,
        agreement_id: str,
        data: AgreementTaskCreate,
    ) -> AgreementTask:
        """Dispatch a task under a standing agreement."""
        resp = await self._client.post(
            f"/agreements/{agreement_id}/tasks",
            json=data.model_dump(mode="json"),
        )
        resp.raise_for_status()
        return AgreementTask.model_validate(resp.json())
