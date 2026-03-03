import uuid
from datetime import datetime, timezone, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.agent import AgentCreate, AgentResponse
from app.schemas.bounty import BountyCreate, BountyUpdate, BountyResponse
from app.schemas.proposal import ProposalCreate, ProposalResponse
from app.schemas.negotiation import (
    NegotiationTerms,
    NegotiationCreate,
    NegotiationTurnRequest,
)
from app.schemas.contract import (
    ContractCreate,
    ContractFundRequest,
    ContractDeliverRequest,
    ContractVerifyRequest,
)


class TestAgentSchemas:
    def test_agent_create_valid(self):
        data = AgentCreate(name="test", agent_type="poster")
        assert data.name == "test"
        assert data.agent_type == "poster"
        assert data.wallet_address is None
        assert data.capabilities == []

    def test_agent_create_with_all_fields(self):
        data = AgentCreate(
            name="test",
            agent_type="both",
            wallet_address="0xabc",
            capabilities=["ai", "web3"],
        )
        assert data.wallet_address == "0xabc"
        assert data.capabilities == ["ai", "web3"]

    def test_agent_create_missing_name(self):
        with pytest.raises(ValidationError):
            AgentCreate(agent_type="poster")

    def test_agent_create_missing_agent_type(self):
        with pytest.raises(ValidationError):
            AgentCreate(name="test")

    def test_agent_create_invalid_agent_type(self):
        with pytest.raises(ValidationError):
            AgentCreate(name="test", agent_type="invalid")

    def test_agent_create_empty_name(self):
        with pytest.raises(ValidationError):
            AgentCreate(name="", agent_type="poster")

    def test_agent_response_from_attributes(self):
        now = datetime.now(timezone.utc)
        data = AgentResponse(
            id=uuid.uuid4(),
            name="test",
            agent_type="solver",
            wallet_address=None,
            capabilities=[],
            reputation_score=0.0,
            bounties_posted=0,
            bounties_completed=0,
            created_at=now,
            updated_at=now,
        )
        assert data.name == "test"


class TestBountySchemas:
    def test_bounty_create_valid(self):
        data = BountyCreate(
            title="Test Bounty",
            description="Description",
            acceptance_criteria=["criterion 1"],
            category="ai",
            reward_amount=1.5,
            deadline=datetime.now(timezone.utc) + timedelta(days=7),
        )
        assert data.title == "Test Bounty"
        assert data.reward_token == "ETH"

    def test_bounty_create_missing_title(self):
        with pytest.raises(ValidationError):
            BountyCreate(
                description="Description",
                acceptance_criteria=["criterion 1"],
                category="ai",
                reward_amount=1.5,
                deadline=datetime.now(timezone.utc) + timedelta(days=7),
            )

    def test_bounty_create_empty_acceptance_criteria(self):
        with pytest.raises(ValidationError):
            BountyCreate(
                title="Test",
                description="Description",
                acceptance_criteria=[],
                category="ai",
                reward_amount=1.5,
                deadline=datetime.now(timezone.utc) + timedelta(days=7),
            )

    def test_bounty_create_negative_reward(self):
        with pytest.raises(ValidationError):
            BountyCreate(
                title="Test",
                description="Description",
                acceptance_criteria=["criterion"],
                category="ai",
                reward_amount=-1.0,
                deadline=datetime.now(timezone.utc) + timedelta(days=7),
            )

    def test_bounty_create_zero_reward(self):
        with pytest.raises(ValidationError):
            BountyCreate(
                title="Test",
                description="Description",
                acceptance_criteria=["criterion"],
                category="ai",
                reward_amount=0.0,
                deadline=datetime.now(timezone.utc) + timedelta(days=7),
            )

    def test_bounty_update_all_optional(self):
        data = BountyUpdate()
        assert data.solver_id is None
        assert data.status is None
        assert data.deliverable_url is None

    def test_bounty_update_with_status(self):
        data = BountyUpdate(status="cancelled")
        assert data.status == "cancelled"

    def test_bounty_update_invalid_status(self):
        with pytest.raises(ValidationError):
            BountyUpdate(status="invalid_status")


class TestProposalSchemas:
    def test_proposal_create_valid(self):
        data = ProposalCreate(
            proposed_price=0.5,
            proposed_deadline=datetime.now(timezone.utc) + timedelta(days=3),
            approach_summary="My approach",
        )
        assert data.proposed_price == 0.5

    def test_proposal_create_missing_price(self):
        with pytest.raises(ValidationError):
            ProposalCreate(
                proposed_deadline=datetime.now(timezone.utc) + timedelta(days=3),
                approach_summary="My approach",
            )

    def test_proposal_create_negative_price(self):
        with pytest.raises(ValidationError):
            ProposalCreate(
                proposed_price=-1.0,
                proposed_deadline=datetime.now(timezone.utc) + timedelta(days=3),
                approach_summary="My approach",
            )

    def test_proposal_create_empty_summary(self):
        with pytest.raises(ValidationError):
            ProposalCreate(
                proposed_price=1.0,
                proposed_deadline=datetime.now(timezone.utc) + timedelta(days=3),
                approach_summary="",
            )


class TestNegotiationSchemas:
    def test_negotiation_terms_valid(self):
        data = NegotiationTerms(
            price=1.0,
            deadline=datetime.now(timezone.utc) + timedelta(days=5),
            deliverables=["item 1"],
            acceptance_criteria=["criterion 1"],
        )
        assert data.price == 1.0
        assert data.revision_rounds == 1

    def test_negotiation_terms_custom_revision_rounds(self):
        data = NegotiationTerms(
            price=1.0,
            deadline=datetime.now(timezone.utc) + timedelta(days=5),
            deliverables=["item 1"],
            acceptance_criteria=["criterion 1"],
            revision_rounds=3,
        )
        assert data.revision_rounds == 3

    def test_negotiation_terms_empty_deliverables(self):
        with pytest.raises(ValidationError):
            NegotiationTerms(
                price=1.0,
                deadline=datetime.now(timezone.utc) + timedelta(days=5),
                deliverables=[],
                acceptance_criteria=["criterion 1"],
            )

    def test_negotiation_terms_zero_price(self):
        with pytest.raises(ValidationError):
            NegotiationTerms(
                price=0.0,
                deadline=datetime.now(timezone.utc) + timedelta(days=5),
                deliverables=["item"],
                acceptance_criteria=["criterion"],
            )

    def test_negotiation_create_valid(self):
        data = NegotiationCreate(
            bounty_id=uuid.uuid4(),
            proposal_id=uuid.uuid4(),
        )
        assert data.bounty_id is not None

    def test_negotiation_turn_request_offer(self):
        data = NegotiationTurnRequest(
            turn_type="offer",
            proposed_terms=NegotiationTerms(
                price=1.0,
                deadline=datetime.now(timezone.utc) + timedelta(days=5),
                deliverables=["item"],
                acceptance_criteria=["criterion"],
            ),
        )
        assert data.turn_type == "offer"

    def test_negotiation_turn_request_accept(self):
        data = NegotiationTurnRequest(turn_type="accept")
        assert data.turn_type == "accept"
        assert data.proposed_terms is None

    def test_negotiation_turn_request_invalid_type(self):
        with pytest.raises(ValidationError):
            NegotiationTurnRequest(turn_type="invalid")

    def test_negotiation_turn_request_with_message(self):
        data = NegotiationTurnRequest(
            turn_type="reject",
            message="Not suitable",
        )
        assert data.message == "Not suitable"


class TestContractSchemas:
    def test_contract_create_valid(self):
        data = ContractCreate(
            bounty_id=uuid.uuid4(),
            negotiation_id=uuid.uuid4(),
        )
        assert data.bounty_id is not None

    def test_contract_fund_request_valid(self):
        data = ContractFundRequest(
            funding_tx_hash="0xabc123",
            escrow_contract_address="0xdef456",
        )
        assert data.funding_tx_hash == "0xabc123"

    def test_contract_fund_request_empty_hash(self):
        with pytest.raises(ValidationError):
            ContractFundRequest(
                funding_tx_hash="",
                escrow_contract_address="0xdef456",
            )

    def test_contract_deliver_request_valid(self):
        data = ContractDeliverRequest(deliverable_url="https://example.com/result")
        assert data.deliverable_url == "https://example.com/result"

    def test_contract_deliver_request_empty_url(self):
        with pytest.raises(ValidationError):
            ContractDeliverRequest(deliverable_url="")

    def test_contract_verify_request_approved(self):
        data = ContractVerifyRequest(approved=True)
        assert data.approved is True

    def test_contract_verify_request_rejected(self):
        data = ContractVerifyRequest(approved=False)
        assert data.approved is False

    def test_contract_verify_request_missing_approved(self):
        with pytest.raises(ValidationError):
            ContractVerifyRequest()
