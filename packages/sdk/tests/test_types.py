"""Tests for all Pydantic models in tectonic.types."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from tectonic.types import (
    Agent,
    AgentCreate,
    AgentRegisterResponse,
    AgentType,
    Bounty,
    BountyCreate,
    BountyListResponse,
    BountyStatus,
    BountyUpdate,
    Contract,
    ContractDeliverRequest,
    ContractFundRequest,
    ContractStatus,
    ContractVerifyRequest,
    Negotiation,
    NegotiationStatus,
    NegotiationTerms,
    NegotiationTurn,
    NegotiationTurnRequest,
    Proposal,
    ProposalCreate,
    ProposalStatus,
    ReputationSummary,
    TurnType,
)

NOW = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------


class TestEnums:
    def test_agent_type_values(self):
        assert AgentType.poster.value == "poster"
        assert AgentType.solver.value == "solver"
        assert AgentType.both.value == "both"

    def test_bounty_status_values(self):
        assert BountyStatus.open.value == "open"
        assert BountyStatus.settled.value == "settled"
        assert BountyStatus.disputed.value == "disputed"

    def test_proposal_status_values(self):
        assert ProposalStatus.pending.value == "pending"
        assert ProposalStatus.accepted.value == "accepted"
        assert ProposalStatus.rejected.value == "rejected"
        assert ProposalStatus.withdrawn.value == "withdrawn"

    def test_negotiation_status_values(self):
        assert NegotiationStatus.active.value == "active"
        assert NegotiationStatus.agreed.value == "agreed"

    def test_contract_status_values(self):
        assert ContractStatus.pending_funding.value == "pending_funding"
        assert ContractStatus.settled.value == "settled"
        assert ContractStatus.resolved.value == "resolved"

    def test_turn_type_values(self):
        assert TurnType.offer.value == "offer"
        assert TurnType.counter.value == "counter"
        assert TurnType.accept.value == "accept"
        assert TurnType.reject.value == "reject"

    def test_invalid_enum_value(self):
        with pytest.raises(ValueError):
            AgentType("invalid")


# ---------------------------------------------------------------------------
# Request model tests
# ---------------------------------------------------------------------------


class TestAgentCreate:
    def test_valid(self):
        obj = AgentCreate(
            name="Alice",
            agent_type=AgentType.poster,
            wallet_address="0x123",
            capabilities=["dev"],
        )
        assert obj.name == "Alice"
        assert obj.agent_type == AgentType.poster
        assert obj.wallet_address == "0x123"
        assert obj.capabilities == ["dev"]

    def test_defaults(self):
        obj = AgentCreate(name="Bob", agent_type=AgentType.solver)
        assert obj.wallet_address is None
        assert obj.capabilities == []

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            AgentCreate(name="Alice")  # type: ignore[call-arg]

    def test_invalid_agent_type(self):
        with pytest.raises(ValidationError):
            AgentCreate(name="Alice", agent_type="invalid")  # type: ignore[arg-type]

    def test_serialization_round_trip(self):
        obj = AgentCreate(name="Alice", agent_type=AgentType.poster)
        data = obj.model_dump(mode="json")
        assert data["agent_type"] == "poster"
        restored = AgentCreate.model_validate(data)
        assert restored == obj


class TestBountyCreate:
    def test_valid(self):
        obj = BountyCreate(
            title="Build CLI",
            description="A CLI tool",
            acceptance_criteria=["Works"],
            category="development",
            reward_amount=0.05,
            deadline=NOW,
        )
        assert obj.reward_token == "ETH"

    def test_custom_reward_token(self):
        obj = BountyCreate(
            title="Build CLI",
            description="A CLI tool",
            acceptance_criteria=["Works"],
            category="development",
            reward_amount=100.0,
            reward_token="USDC",
            deadline=NOW,
        )
        assert obj.reward_token == "USDC"

    def test_missing_title(self):
        with pytest.raises(ValidationError):
            BountyCreate(
                description="A CLI tool",
                acceptance_criteria=["Works"],
                category="development",
                reward_amount=0.05,
                deadline=NOW,
            )  # type: ignore[call-arg]


class TestBountyUpdate:
    def test_all_none_defaults(self):
        obj = BountyUpdate()
        assert obj.solver_id is None
        assert obj.status is None
        assert obj.deliverable_url is None

    def test_partial_update(self):
        obj = BountyUpdate(status=BountyStatus.in_progress)
        assert obj.status == BountyStatus.in_progress
        dumped = obj.model_dump(exclude_none=True)
        assert "solver_id" not in dumped


class TestProposalCreate:
    def test_valid(self):
        obj = ProposalCreate(
            proposed_price=0.04,
            proposed_deadline=NOW,
            approach_summary="Will use Python",
        )
        assert obj.proposed_price == 0.04

    def test_missing_approach(self):
        with pytest.raises(ValidationError):
            ProposalCreate(proposed_price=0.04, proposed_deadline=NOW)  # type: ignore[call-arg]


class TestNegotiationTerms:
    def test_valid(self):
        terms = NegotiationTerms(
            price=0.05,
            deadline=NOW,
            deliverables=["CLI tool"],
            acceptance_criteria=["Tests pass"],
            revision_rounds=2,
        )
        assert terms.revision_rounds == 2

    def test_default_revision_rounds(self):
        terms = NegotiationTerms(
            price=0.05,
            deadline=NOW,
            deliverables=["CLI tool"],
            acceptance_criteria=["Tests pass"],
        )
        assert terms.revision_rounds == 1


class TestNegotiationTurnRequest:
    def test_accept_without_terms(self):
        req = NegotiationTurnRequest(
            turn_type=TurnType.accept,
            message="Deal!",
        )
        assert req.proposed_terms is None

    def test_counter_with_terms(self):
        terms = NegotiationTerms(
            price=0.05,
            deadline=NOW,
            deliverables=["Tool"],
            acceptance_criteria=["Works"],
        )
        req = NegotiationTurnRequest(
            turn_type=TurnType.counter,
            proposed_terms=terms,
            message="Counter offer",
        )
        assert req.proposed_terms is not None
        assert req.proposed_terms.price == 0.05

    def test_invalid_turn_type(self):
        with pytest.raises(ValidationError):
            NegotiationTurnRequest(turn_type="invalid")  # type: ignore[arg-type]


class TestContractRequests:
    def test_fund_request(self):
        obj = ContractFundRequest(
            funding_tx_hash="0xabc",
            escrow_contract_address="0xdef",
        )
        assert obj.funding_tx_hash == "0xabc"

    def test_deliver_request(self):
        obj = ContractDeliverRequest(deliverable_url="https://example.com")
        assert obj.deliverable_url == "https://example.com"

    def test_verify_request_approved(self):
        obj = ContractVerifyRequest(approved=True)
        assert obj.approved is True

    def test_verify_request_rejected(self):
        obj = ContractVerifyRequest(approved=False)
        assert obj.approved is False

    def test_fund_request_missing_fields(self):
        with pytest.raises(ValidationError):
            ContractFundRequest(funding_tx_hash="0xabc")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Response model tests
# ---------------------------------------------------------------------------


class TestAgentResponse:
    def test_valid(self):
        agent = Agent(
            id="abc-123",
            name="Alice",
            agent_type=AgentType.poster,
            wallet_address="0x1",
            capabilities=["dev"],
            reputation_score=4.5,
            bounties_posted=10,
            bounties_completed=5,
            created_at=NOW,
            updated_at=NOW,
        )
        assert agent.id == "abc-123"
        assert agent.agent_type == AgentType.poster

    def test_defaults(self):
        agent = Agent(
            id="abc-123",
            name="Bob",
            agent_type=AgentType.solver,
            created_at=NOW,
            updated_at=NOW,
        )
        assert agent.wallet_address is None
        assert agent.capabilities == []
        assert agent.reputation_score == 0.0
        assert agent.bounties_posted == 0
        assert agent.bounties_completed == 0

    def test_missing_id(self):
        with pytest.raises(ValidationError):
            Agent(
                name="Bob",
                agent_type=AgentType.solver,
                created_at=NOW,
                updated_at=NOW,
            )  # type: ignore[call-arg]


class TestAgentRegisterResponse:
    def test_valid(self):
        resp = AgentRegisterResponse(
            agent=Agent(
                id="abc-123",
                name="Alice",
                agent_type=AgentType.poster,
                created_at=NOW,
                updated_at=NOW,
            ),
            api_key="tec_testkey",
        )
        assert resp.api_key == "tec_testkey"
        assert resp.agent.name == "Alice"


class TestBountyResponse:
    def test_valid(self):
        bounty = Bounty(
            id="b-1",
            title="Build CLI",
            description="A tool",
            acceptance_criteria=["Works"],
            category="dev",
            reward_amount=0.05,
            reward_token="ETH",
            poster_id="p-1",
            status=BountyStatus.open,
            deadline=NOW,
            created_at=NOW,
            updated_at=NOW,
        )
        assert bounty.solver_id is None
        assert bounty.escrow_address is None

    def test_full(self):
        bounty = Bounty(
            id="b-1",
            title="Build CLI",
            description="A tool",
            acceptance_criteria=["Works"],
            category="dev",
            reward_amount=0.05,
            reward_token="ETH",
            poster_id="p-1",
            solver_id="s-1",
            status=BountyStatus.in_progress,
            deadline=NOW,
            escrow_address="0xescrow",
            deliverable_url="https://github.com/test",
            created_at=NOW,
            updated_at=NOW,
        )
        assert bounty.solver_id == "s-1"
        assert bounty.escrow_address == "0xescrow"


class TestBountyListResponse:
    def test_valid(self):
        resp = BountyListResponse(
            bounties=[
                Bounty(
                    id="b-1",
                    title="Build CLI",
                    description="A tool",
                    acceptance_criteria=["Works"],
                    category="dev",
                    reward_amount=0.05,
                    poster_id="p-1",
                    status=BountyStatus.open,
                    deadline=NOW,
                    created_at=NOW,
                    updated_at=NOW,
                )
            ],
            total=1,
        )
        assert resp.total == 1
        assert len(resp.bounties) == 1

    def test_empty(self):
        resp = BountyListResponse(bounties=[], total=0)
        assert resp.total == 0


class TestProposalResponse:
    def test_valid(self):
        proposal = Proposal(
            id="pr-1",
            bounty_id="b-1",
            solver_id="s-1",
            status=ProposalStatus.pending,
            proposed_price=0.04,
            proposed_deadline=NOW,
            approach_summary="Use Python",
            created_at=NOW,
        )
        assert proposal.status == ProposalStatus.pending


class TestNegotiationTurnResponse:
    def test_valid(self):
        turn = NegotiationTurn(
            id="t-1",
            negotiation_id="n-1",
            agent_id="a-1",
            sequence=1,
            turn_type="counter",
            proposed_terms={"price": 0.05},
            message="Counter offer",
            created_at=NOW,
        )
        assert turn.sequence == 1
        assert turn.proposed_terms == {"price": 0.05}

    def test_minimal(self):
        turn = NegotiationTurn(
            id="t-1",
            negotiation_id="n-1",
            agent_id="a-1",
            sequence=0,
            turn_type="accept",
            created_at=NOW,
        )
        assert turn.proposed_terms is None
        assert turn.message is None


class TestNegotiationResponse:
    def test_valid(self):
        neg = Negotiation(
            id="n-1",
            bounty_id="b-1",
            proposal_id="pr-1",
            poster_id="p-1",
            solver_id="s-1",
            status=NegotiationStatus.active,
            created_at=NOW,
            updated_at=NOW,
        )
        assert neg.turn_count == 0
        assert neg.max_turns == 10
        assert neg.turns == []

    def test_with_turns(self):
        turn = NegotiationTurn(
            id="t-1",
            negotiation_id="n-1",
            agent_id="p-1",
            sequence=1,
            turn_type="offer",
            created_at=NOW,
        )
        neg = Negotiation(
            id="n-1",
            bounty_id="b-1",
            proposal_id="pr-1",
            poster_id="p-1",
            solver_id="s-1",
            status=NegotiationStatus.active,
            turns=[turn],
            turn_count=1,
            created_at=NOW,
            updated_at=NOW,
        )
        assert len(neg.turns) == 1


class TestContractResponse:
    def test_valid(self):
        contract = Contract(
            id="c-1",
            bounty_id="b-1",
            negotiation_id="n-1",
            poster_id="p-1",
            solver_id="s-1",
            status=ContractStatus.pending_funding,
            agreed_terms={"price": 0.05},
            terms_hash="0xhash",
            amount=0.05,
            created_at=NOW,
            updated_at=NOW,
        )
        assert contract.escrow_contract_address is None
        assert contract.funding_tx_hash is None
        assert contract.release_tx_hash is None

    def test_funded(self):
        contract = Contract(
            id="c-1",
            bounty_id="b-1",
            negotiation_id="n-1",
            poster_id="p-1",
            solver_id="s-1",
            status=ContractStatus.funded,
            agreed_terms={"price": 0.05},
            terms_hash="0xhash",
            escrow_contract_address="0xescrow",
            funding_tx_hash="0xtx",
            amount=0.05,
            created_at=NOW,
            updated_at=NOW,
        )
        assert contract.escrow_contract_address == "0xescrow"


class TestReputationSummary:
    def test_valid(self):
        rep = ReputationSummary(
            agent_id="a-1",
            reputation_score=4.5,
            bounties_posted=10,
            bounties_completed=8,
            events=[{"event_type": "bounty_completed", "score_delta": 0.5}],
        )
        assert rep.reputation_score == 4.5
        assert len(rep.events) == 1

    def test_defaults(self):
        rep = ReputationSummary(
            agent_id="a-1",
            reputation_score=0.0,
            bounties_posted=0,
            bounties_completed=0,
        )
        assert rep.events == []


# ---------------------------------------------------------------------------
# JSON serialization tests
# ---------------------------------------------------------------------------


class TestJsonSerialization:
    def test_bounty_create_json(self):
        obj = BountyCreate(
            title="Build CLI",
            description="A tool",
            acceptance_criteria=["Works"],
            category="dev",
            reward_amount=0.05,
            deadline=NOW,
        )
        data = obj.model_dump(mode="json")
        assert isinstance(data["deadline"], str)
        restored = BountyCreate.model_validate(data)
        assert restored.title == "Build CLI"

    def test_negotiation_terms_json(self):
        terms = NegotiationTerms(
            price=0.05,
            deadline=NOW,
            deliverables=["Tool", "Docs"],
            acceptance_criteria=["Tests pass"],
            revision_rounds=2,
        )
        data = terms.model_dump(mode="json")
        assert isinstance(data["deadline"], str)
        assert data["revision_rounds"] == 2

    def test_agent_from_api_response(self):
        """Simulate parsing a UUID-based API response into SDK string-id model."""
        api_data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Alice",
            "agent_type": "poster",
            "wallet_address": None,
            "capabilities": [],
            "reputation_score": 0.0,
            "bounties_posted": 0,
            "bounties_completed": 0,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
        }
        agent = Agent.model_validate(api_data)
        assert agent.id == "550e8400-e29b-41d4-a716-446655440000"
        assert agent.agent_type == AgentType.poster
