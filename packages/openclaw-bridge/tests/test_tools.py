"""Tests for the OpenClaw bridge tool functions.

Each test mocks the TectonicClient to verify that:
- The correct SDK method is called with proper arguments.
- The response is formatted as an LLM-friendly dict.
- Errors are caught and returned gracefully.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tectonic.types import (
    Bounty,
    BountyListResponse,
    BountyStatus,
    Contract,
    ContractStatus,
    Negotiation,
    NegotiationStatus,
    NegotiationTurn,
    Proposal,
    ProposalStatus,
    ReputationSummary,
)

from tectonic_tools import tools

NOW = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_bounty(**overrides) -> Bounty:
    defaults = dict(
        id="b-1",
        title="Build CLI",
        description="A CLI tool for CSV to JSON",
        acceptance_criteria=["Tests pass"],
        category="development",
        reward_amount=0.05,
        reward_token="ETH",
        poster_id="p-1",
        solver_id=None,
        status=BountyStatus.open,
        deadline=NOW,
        escrow_address=None,
        deliverable_url=None,
        created_at=NOW,
        updated_at=NOW,
    )
    defaults.update(overrides)
    return Bounty(**defaults)


def _make_proposal(**overrides) -> Proposal:
    defaults = dict(
        id="pr-1",
        bounty_id="b-1",
        solver_id="s-1",
        status=ProposalStatus.pending,
        proposed_price=0.04,
        proposed_deadline=NOW,
        approach_summary="Will use Python",
        created_at=NOW,
    )
    defaults.update(overrides)
    return Proposal(**defaults)


def _make_negotiation(**overrides) -> Negotiation:
    defaults = dict(
        id="n-1",
        bounty_id="b-1",
        proposal_id="pr-1",
        poster_id="p-1",
        solver_id="s-1",
        status=NegotiationStatus.active,
        current_terms=None,
        turn_count=0,
        max_turns=10,
        created_at=NOW,
        updated_at=NOW,
        turns=[],
    )
    defaults.update(overrides)
    return Negotiation(**defaults)


def _make_turn(**overrides) -> NegotiationTurn:
    defaults = dict(
        id="t-1",
        negotiation_id="n-1",
        agent_id="p-1",
        sequence=1,
        turn_type="counter",
        proposed_terms={"price": 0.05},
        message="Counter offer",
        created_at=NOW,
    )
    defaults.update(overrides)
    return NegotiationTurn(**defaults)


def _make_contract(**overrides) -> Contract:
    defaults = dict(
        id="c-1",
        bounty_id="b-1",
        negotiation_id="n-1",
        poster_id="p-1",
        solver_id="s-1",
        status=ContractStatus.pending_funding,
        agreed_terms={"price": 0.05},
        terms_hash="0xhash",
        escrow_contract_address=None,
        funding_tx_hash=None,
        release_tx_hash=None,
        amount=0.05,
        created_at=NOW,
        updated_at=NOW,
    )
    defaults.update(overrides)
    return Contract(**defaults)


def _make_reputation(**overrides) -> ReputationSummary:
    defaults = dict(
        agent_id="p-1",
        reputation_score=4.5,
        bounties_posted=10,
        bounties_completed=8,
        events=[{"event_type": "bounty_completed", "score_delta": 0.5}],
    )
    defaults.update(overrides)
    return ReputationSummary(**defaults)


def _mock_client():
    """Return a mock TectonicClient that supports async context manager."""
    mock = AsyncMock()
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=None)
    return mock


# ---------------------------------------------------------------------------
# tectonic_post_bounty
# ---------------------------------------------------------------------------


class TestPostBounty:
    @patch.object(tools, "_client")
    async def test_success(self, mock_client_fn):
        client = _mock_client()
        client.create_bounty = AsyncMock(return_value=_make_bounty())
        mock_client_fn.return_value = client

        result = await tools.tectonic_post_bounty(
            title="Build CLI",
            description="A CLI tool",
            criteria=["Tests pass"],
            category="development",
            reward=0.05,
            deadline="2025-12-31T00:00:00Z",
        )

        assert result["bounty_id"] == "b-1"
        assert result["status"] == "open"
        assert result["reward_amount"] == 0.05
        client.create_bounty.assert_called_once()

    @patch.object(tools, "_client")
    async def test_error_handling(self, mock_client_fn):
        client = _mock_client()
        client.create_bounty = AsyncMock(side_effect=Exception("Connection refused"))
        mock_client_fn.return_value = client

        result = await tools.tectonic_post_bounty(
            title="Test",
            description="Test",
            criteria=["Test"],
            category="test",
            reward=0.01,
            deadline="2025-12-31T00:00:00Z",
        )

        assert "error" in result
        assert "Connection refused" in result["error"]


# ---------------------------------------------------------------------------
# tectonic_list_proposals
# ---------------------------------------------------------------------------


class TestListProposals:
    @patch.object(tools, "_client")
    async def test_success(self, mock_client_fn):
        client = _mock_client()
        client.list_proposals = AsyncMock(
            return_value=[_make_proposal(), _make_proposal(id="pr-2", proposed_price=0.03)]
        )
        mock_client_fn.return_value = client

        result = await tools.tectonic_list_proposals("b-1")

        assert result["count"] == 2
        assert len(result["proposals"]) == 2
        assert result["proposals"][0]["proposal_id"] == "pr-1"

    @patch.object(tools, "_client")
    async def test_empty(self, mock_client_fn):
        client = _mock_client()
        client.list_proposals = AsyncMock(return_value=[])
        mock_client_fn.return_value = client

        result = await tools.tectonic_list_proposals("b-1")

        assert result["count"] == 0
        assert result["proposals"] == []

    @patch.object(tools, "_client")
    async def test_error(self, mock_client_fn):
        client = _mock_client()
        client.list_proposals = AsyncMock(side_effect=Exception("Not found"))
        mock_client_fn.return_value = client

        result = await tools.tectonic_list_proposals("bad-id")

        assert "error" in result


# ---------------------------------------------------------------------------
# tectonic_start_negotiation
# ---------------------------------------------------------------------------


class TestStartNegotiation:
    @patch.object(tools, "_client")
    async def test_success(self, mock_client_fn):
        client = _mock_client()
        client.create_negotiation = AsyncMock(return_value=_make_negotiation())
        mock_client_fn.return_value = client

        result = await tools.tectonic_start_negotiation("b-1", "pr-1")

        assert result["negotiation_id"] == "n-1"
        assert result["status"] == "active"
        client.create_negotiation.assert_called_once_with("b-1", "pr-1")

    @patch.object(tools, "_client")
    async def test_error(self, mock_client_fn):
        client = _mock_client()
        client.create_negotiation = AsyncMock(side_effect=Exception("Forbidden"))
        mock_client_fn.return_value = client

        result = await tools.tectonic_start_negotiation("b-1", "pr-1")

        assert "error" in result


# ---------------------------------------------------------------------------
# tectonic_negotiate
# ---------------------------------------------------------------------------


class TestNegotiate:
    @patch.object(tools, "_client")
    async def test_counter(self, mock_client_fn):
        client = _mock_client()
        client.submit_turn = AsyncMock(return_value=_make_turn())
        mock_client_fn.return_value = client

        result = await tools.tectonic_negotiate(
            negotiation_id="n-1",
            action="counter",
            price=0.05,
            deadline="2025-12-31T00:00:00Z",
            deliverables=["CLI tool"],
            message="Counter offer",
        )

        assert result["turn_id"] == "t-1"
        assert result["turn_type"] == "counter"

    @patch.object(tools, "_client")
    async def test_accept(self, mock_client_fn):
        client = _mock_client()
        accept_turn = _make_turn(turn_type="accept", proposed_terms=None)
        client.submit_turn = AsyncMock(return_value=accept_turn)
        mock_client_fn.return_value = client

        result = await tools.tectonic_negotiate(
            negotiation_id="n-1",
            action="accept",
            message="Deal!",
        )

        assert result["turn_type"] == "accept"

    @patch.object(tools, "_client")
    async def test_reject(self, mock_client_fn):
        client = _mock_client()
        reject_turn = _make_turn(turn_type="reject", proposed_terms=None, message="No deal")
        client.submit_turn = AsyncMock(return_value=reject_turn)
        mock_client_fn.return_value = client

        result = await tools.tectonic_negotiate(
            negotiation_id="n-1",
            action="reject",
            message="No deal",
        )

        assert result["turn_type"] == "reject"

    async def test_counter_missing_required_fields(self):
        result = await tools.tectonic_negotiate(
            negotiation_id="n-1",
            action="counter",
            price=None,
            deadline=None,
            deliverables=None,
        )

        assert "error" in result
        assert "required" in result["error"].lower()

    @patch.object(tools, "_client")
    async def test_invalid_action(self, mock_client_fn):
        result = await tools.tectonic_negotiate(
            negotiation_id="n-1",
            action="invalid_action",
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# tectonic_fund_escrow
# ---------------------------------------------------------------------------


class TestFundEscrow:
    @patch.object(tools, "_client")
    async def test_success(self, mock_client_fn):
        client = _mock_client()
        funded = _make_contract(
            status=ContractStatus.funded,
            funding_tx_hash="0xtx",
            escrow_contract_address="0xescrow",
        )
        client.fund_contract = AsyncMock(return_value=funded)
        mock_client_fn.return_value = client

        result = await tools.tectonic_fund_escrow("c-1", "0xtx", "0xescrow")

        assert result["status"] == "funded"
        assert result["funding_tx_hash"] == "0xtx"

    @patch.object(tools, "_client")
    async def test_error(self, mock_client_fn):
        client = _mock_client()
        client.fund_contract = AsyncMock(side_effect=Exception("Bad request"))
        mock_client_fn.return_value = client

        result = await tools.tectonic_fund_escrow("c-1", "0xtx", "0xescrow")

        assert "error" in result


# ---------------------------------------------------------------------------
# tectonic_review_delivery
# ---------------------------------------------------------------------------


class TestReviewDelivery:
    @patch.object(tools, "_client")
    async def test_success(self, mock_client_fn):
        client = _mock_client()
        delivered_bounty = _make_bounty(
            status=BountyStatus.delivered,
            deliverable_url="https://github.com/test/repo",
        )
        client.list_bounties = AsyncMock(
            return_value=BountyListResponse(bounties=[delivered_bounty], total=1)
        )
        mock_client_fn.return_value = client

        result = await tools.tectonic_review_delivery("c-1")

        assert result["deliverable_url"] == "https://github.com/test/repo"

    @patch.object(tools, "_client")
    async def test_no_delivery(self, mock_client_fn):
        client = _mock_client()
        client.list_bounties = AsyncMock(
            return_value=BountyListResponse(bounties=[], total=0)
        )
        mock_client_fn.return_value = client

        result = await tools.tectonic_review_delivery("c-1")

        assert "message" in result
        assert "not have been submitted" in result["message"]


# ---------------------------------------------------------------------------
# tectonic_verify_delivery
# ---------------------------------------------------------------------------


class TestVerifyDelivery:
    @patch.object(tools, "_client")
    async def test_approved(self, mock_client_fn):
        client = _mock_client()
        verified = _make_contract(status=ContractStatus.verified)
        client.verify_contract = AsyncMock(return_value=verified)
        mock_client_fn.return_value = client

        result = await tools.tectonic_verify_delivery("c-1", approved=True)

        assert result["status"] == "verified"
        assert result["approved"] is True

    @patch.object(tools, "_client")
    async def test_rejected(self, mock_client_fn):
        client = _mock_client()
        disputed = _make_contract(status=ContractStatus.disputed)
        client.verify_contract = AsyncMock(return_value=disputed)
        mock_client_fn.return_value = client

        result = await tools.tectonic_verify_delivery("c-1", approved=False)

        assert result["status"] == "disputed"
        assert result["approved"] is False


# ---------------------------------------------------------------------------
# tectonic_my_bounties
# ---------------------------------------------------------------------------


class TestMyBounties:
    @patch.object(tools, "_client")
    async def test_success(self, mock_client_fn):
        client = _mock_client()
        client.list_bounties = AsyncMock(
            return_value=BountyListResponse(
                bounties=[_make_bounty(), _make_bounty(id="b-2", title="Design logo")],
                total=2,
            )
        )
        mock_client_fn.return_value = client

        result = await tools.tectonic_my_bounties()

        assert result["total"] == 2
        assert len(result["bounties"]) == 2

    @patch.object(tools, "_client")
    async def test_empty(self, mock_client_fn):
        client = _mock_client()
        client.list_bounties = AsyncMock(
            return_value=BountyListResponse(bounties=[], total=0)
        )
        mock_client_fn.return_value = client

        result = await tools.tectonic_my_bounties()

        assert result["total"] == 0


# ---------------------------------------------------------------------------
# tectonic_my_reputation
# ---------------------------------------------------------------------------


class TestMyReputation:
    @patch.object(tools, "_client")
    @patch.object(tools, "get_config")
    async def test_success(self, mock_config, mock_client_fn):
        cfg = MagicMock()
        cfg.agent_id = "p-1"
        cfg.api_url = "http://localhost:8000"
        cfg.api_key = "tec_key"
        mock_config.return_value = cfg

        client = _mock_client()
        client.get_agent_reputation = AsyncMock(return_value=_make_reputation())
        mock_client_fn.return_value = client

        result = await tools.tectonic_my_reputation()

        assert result["reputation_score"] == 4.5
        assert result["bounties_completed"] == 8

    @patch.object(tools, "get_config")
    async def test_missing_agent_id(self, mock_config):
        cfg = MagicMock()
        cfg.agent_id = ""
        mock_config.return_value = cfg

        result = await tools.tectonic_my_reputation()

        assert "error" in result
        assert "TECTONIC_AGENT_ID" in result["error"]


# ---------------------------------------------------------------------------
# tectonic_browse_bounties
# ---------------------------------------------------------------------------


class TestBrowseBounties:
    @patch.object(tools, "_client")
    async def test_no_filters(self, mock_client_fn):
        client = _mock_client()
        client.list_bounties = AsyncMock(
            return_value=BountyListResponse(bounties=[_make_bounty()], total=1)
        )
        mock_client_fn.return_value = client

        result = await tools.tectonic_browse_bounties()

        assert result["total"] == 1
        client.list_bounties.assert_called_once_with(status="open", category=None)

    @patch.object(tools, "_client")
    async def test_category_filter(self, mock_client_fn):
        client = _mock_client()
        client.list_bounties = AsyncMock(
            return_value=BountyListResponse(bounties=[_make_bounty()], total=1)
        )
        mock_client_fn.return_value = client

        result = await tools.tectonic_browse_bounties(category="development")

        client.list_bounties.assert_called_once_with(status="open", category="development")

    @patch.object(tools, "_client")
    async def test_min_reward_filter(self, mock_client_fn):
        client = _mock_client()
        cheap = _make_bounty(id="b-cheap", reward_amount=0.01)
        expensive = _make_bounty(id="b-exp", reward_amount=0.10)
        client.list_bounties = AsyncMock(
            return_value=BountyListResponse(bounties=[cheap, expensive], total=2)
        )
        mock_client_fn.return_value = client

        result = await tools.tectonic_browse_bounties(min_reward=0.05)

        assert result["total"] == 1
        assert result["bounties"][0]["bounty_id"] == "b-exp"

    @patch.object(tools, "_client")
    async def test_description_truncated(self, mock_client_fn):
        client = _mock_client()
        long_desc = "A" * 500
        bounty = _make_bounty(description=long_desc)
        client.list_bounties = AsyncMock(
            return_value=BountyListResponse(bounties=[bounty], total=1)
        )
        mock_client_fn.return_value = client

        result = await tools.tectonic_browse_bounties()

        assert len(result["bounties"][0]["description"]) == 200


# ---------------------------------------------------------------------------
# tectonic_submit_proposal
# ---------------------------------------------------------------------------


class TestSubmitProposal:
    @patch.object(tools, "_client")
    async def test_success(self, mock_client_fn):
        client = _mock_client()
        client.create_proposal = AsyncMock(return_value=_make_proposal())
        mock_client_fn.return_value = client

        result = await tools.tectonic_submit_proposal(
            bounty_id="b-1",
            price=0.04,
            deadline="2025-12-31T00:00:00Z",
            approach="Will use Python",
        )

        assert result["proposal_id"] == "pr-1"
        assert result["status"] == "pending"
        client.create_proposal.assert_called_once()

    @patch.object(tools, "_client")
    async def test_error(self, mock_client_fn):
        client = _mock_client()
        client.create_proposal = AsyncMock(side_effect=Exception("Bounty not found"))
        mock_client_fn.return_value = client

        result = await tools.tectonic_submit_proposal(
            bounty_id="bad-id",
            price=0.04,
            deadline="2025-12-31T00:00:00Z",
            approach="Will use Python",
        )

        assert "error" in result


# ---------------------------------------------------------------------------
# tectonic_submit_delivery
# ---------------------------------------------------------------------------


class TestSubmitDelivery:
    @patch.object(tools, "_client")
    async def test_success(self, mock_client_fn):
        client = _mock_client()
        delivered = _make_contract(status=ContractStatus.delivered)
        client.deliver_contract = AsyncMock(return_value=delivered)
        mock_client_fn.return_value = client

        result = await tools.tectonic_submit_delivery(
            contract_id="c-1",
            deliverable_url="https://github.com/test/repo",
        )

        assert result["status"] == "delivered"
        client.deliver_contract.assert_called_once()

    @patch.object(tools, "_client")
    async def test_error(self, mock_client_fn):
        client = _mock_client()
        client.deliver_contract = AsyncMock(side_effect=Exception("Not authorized"))
        mock_client_fn.return_value = client

        result = await tools.tectonic_submit_delivery(
            contract_id="c-1",
            deliverable_url="https://github.com/test/repo",
        )

        assert "error" in result
