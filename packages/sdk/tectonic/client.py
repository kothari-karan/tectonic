"""Async HTTP client for the Tectonic Agent Commerce Protocol API."""

from __future__ import annotations

import httpx

from .types import (
    Agent,
    AgentCreate,
    AgentRegisterResponse,
    Bounty,
    BountyCreate,
    BountyListResponse,
    BountyUpdate,
    Contract,
    ContractDeliverRequest,
    ContractFundRequest,
    ContractVerifyRequest,
    Negotiation,
    NegotiationTurn,
    NegotiationTurnRequest,
    Proposal,
    ProposalCreate,
    ReputationSummary,
)


class TectonicClient:
    """Async HTTP client wrapping the Tectonic API.

    Usage::

        async with TectonicClient("http://localhost:8000", api_key="tec_...") as client:
            bounty = await client.create_bounty(BountyCreate(...))
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

    # ------------------------------------------------------------------
    # Bounties
    # ------------------------------------------------------------------

    async def create_bounty(self, data: BountyCreate) -> Bounty:
        """Create a new bounty."""
        resp = await self._client.post(
            "/bounties",
            json=data.model_dump(mode="json"),
        )
        resp.raise_for_status()
        return Bounty.model_validate(resp.json())

    async def list_bounties(
        self,
        status: str | None = None,
        category: str | None = None,
    ) -> BountyListResponse:
        """List bounties, optionally filtered by status and/or category."""
        params: dict[str, str] = {}
        if status is not None:
            params["status"] = status
        if category is not None:
            params["category"] = category
        resp = await self._client.get("/bounties", params=params)
        resp.raise_for_status()
        return BountyListResponse.model_validate(resp.json())

    async def get_bounty(self, bounty_id: str) -> Bounty:
        """Retrieve a single bounty by ID."""
        resp = await self._client.get(f"/bounties/{bounty_id}")
        resp.raise_for_status()
        return Bounty.model_validate(resp.json())

    async def update_bounty(self, bounty_id: str, data: BountyUpdate) -> Bounty:
        """Update an existing bounty."""
        resp = await self._client.patch(
            f"/bounties/{bounty_id}",
            json=data.model_dump(mode="json", exclude_none=True),
        )
        resp.raise_for_status()
        return Bounty.model_validate(resp.json())

    # ------------------------------------------------------------------
    # Proposals
    # ------------------------------------------------------------------

    async def create_proposal(
        self,
        bounty_id: str,
        data: ProposalCreate,
    ) -> Proposal:
        """Submit a proposal on a bounty."""
        resp = await self._client.post(
            f"/bounties/{bounty_id}/proposals",
            json=data.model_dump(mode="json"),
        )
        resp.raise_for_status()
        return Proposal.model_validate(resp.json())

    async def list_proposals(self, bounty_id: str) -> list[Proposal]:
        """List all proposals for a bounty."""
        resp = await self._client.get(f"/bounties/{bounty_id}/proposals")
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
        bounty_id: str,
        proposal_id: str,
    ) -> Negotiation:
        """Start a negotiation between poster and solver."""
        resp = await self._client.post(
            "/negotiations",
            json={"bounty_id": bounty_id, "proposal_id": proposal_id},
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
        bounty_id: str,
        negotiation_id: str,
    ) -> Contract:
        """Create a contract from an agreed negotiation."""
        resp = await self._client.post(
            "/contracts",
            json={"bounty_id": bounty_id, "negotiation_id": negotiation_id},
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
