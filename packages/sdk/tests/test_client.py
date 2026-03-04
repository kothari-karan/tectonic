"""Comprehensive tests for TectonicClient using respx (httpx mock)."""

from datetime import datetime, timezone

import httpx
import pytest
import respx

from tectonic.client import TectonicClient
from tectonic.types import (
    AgentCreate,
    AgentType,
    EngagementCreate,
    EngagementStatus,
    ContractDeliverRequest,
    ContractFundRequest,
    ContractStatus,
    ContractVerifyRequest,
    NegotiationStatus,
    NegotiationTerms,
    NegotiationTurnRequest,
    ProposalCreate,
    ProposalStatus,
    TurnType,
)

BASE_URL = "http://testserver"
NOW = datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _agent_json(agent_id: str = "agent-1") -> dict:
    return {
        "id": agent_id,
        "name": "Alice",
        "agent_type": "requester",
        "wallet_address": "0x123",
        "capabilities": ["dev"],
        "reputation_score": 4.5,
        "engagements_posted": 10,
        "engagements_completed": 5,
        "created_at": NOW,
        "updated_at": NOW,
    }


def _engagement_json(engagement_id: str = "engagement-1") -> dict:
    return {
        "id": engagement_id,
        "title": "Build CLI",
        "description": "A CLI tool",
        "acceptance_criteria": ["Works"],
        "category": "development",
        "reward_amount": 0.05,
        "reward_token": "ETH",
        "requester_id": "agent-1",
        "provider_id": None,
        "status": "open",
        "deadline": NOW,
        "escrow_address": None,
        "deliverable_url": None,
        "created_at": NOW,
        "updated_at": NOW,
    }


def _proposal_json(proposal_id: str = "proposal-1") -> dict:
    return {
        "id": proposal_id,
        "engagement_id": "engagement-1",
        "provider_id": "agent-2",
        "status": "pending",
        "proposed_price": 0.04,
        "proposed_deadline": NOW,
        "approach_summary": "Will use Python",
        "created_at": NOW,
    }


def _negotiation_json(negotiation_id: str = "neg-1") -> dict:
    return {
        "id": negotiation_id,
        "engagement_id": "engagement-1",
        "proposal_id": "proposal-1",
        "requester_id": "agent-1",
        "provider_id": "agent-2",
        "status": "active",
        "current_terms": None,
        "turn_count": 0,
        "max_turns": 10,
        "created_at": NOW,
        "updated_at": NOW,
        "turns": [],
    }


def _turn_json(turn_id: str = "turn-1") -> dict:
    return {
        "id": turn_id,
        "negotiation_id": "neg-1",
        "agent_id": "agent-1",
        "sequence": 1,
        "turn_type": "counter",
        "proposed_terms": {"price": 0.05},
        "message": "Counter offer",
        "created_at": NOW,
    }


def _contract_json(contract_id: str = "contract-1") -> dict:
    return {
        "id": contract_id,
        "engagement_id": "engagement-1",
        "negotiation_id": "neg-1",
        "requester_id": "agent-1",
        "provider_id": "agent-2",
        "status": "pending_funding",
        "agreed_terms": {"price": 0.05},
        "terms_hash": "0xhash123",
        "escrow_contract_address": None,
        "funding_tx_hash": None,
        "release_tx_hash": None,
        "amount": 0.05,
        "created_at": NOW,
        "updated_at": NOW,
    }


def _reputation_json(agent_id: str = "agent-1") -> dict:
    return {
        "agent_id": agent_id,
        "reputation_score": 4.5,
        "engagements_posted": 10,
        "engagements_completed": 8,
        "events": [{"event_type": "engagement_completed", "score_delta": 0.5}],
    }


# ---------------------------------------------------------------------------
# Auth header tests
# ---------------------------------------------------------------------------


class TestAuth:
    @respx.mock
    async def test_api_key_header_included(self):
        route = respx.get(f"{BASE_URL}/agents/agent-1").mock(
            return_value=httpx.Response(200, json=_agent_json())
        )
        async with TectonicClient(BASE_URL, api_key="tec_secret") as client:
            await client.get_agent("agent-1")
        assert route.called
        request = route.calls[0].request
        assert request.headers["X-API-Key"] == "tec_secret"

    @respx.mock
    async def test_no_api_key_header_when_not_set(self):
        route = respx.get(f"{BASE_URL}/agents/agent-1").mock(
            return_value=httpx.Response(200, json=_agent_json())
        )
        async with TectonicClient(BASE_URL) as client:
            await client.get_agent("agent-1")
        request = route.calls[0].request
        assert "X-API-Key" not in request.headers


class TestContextManager:
    @respx.mock
    async def test_async_with(self):
        respx.get(f"{BASE_URL}/agents/agent-1").mock(
            return_value=httpx.Response(200, json=_agent_json())
        )
        async with TectonicClient(BASE_URL) as client:
            agent = await client.get_agent("agent-1")
            assert agent.id == "agent-1"


# ---------------------------------------------------------------------------
# Agent endpoint tests
# ---------------------------------------------------------------------------


class TestAgentEndpoints:
    @respx.mock
    async def test_register_agent(self):
        resp_json = {"agent": _agent_json(), "api_key": "tec_newkey123"}
        route = respx.post(f"{BASE_URL}/agents/register").mock(
            return_value=httpx.Response(200, json=resp_json)
        )
        async with TectonicClient(BASE_URL) as client:
            result = await client.register_agent(
                AgentCreate(
                    name="Alice",
                    agent_type=AgentType.requester,
                    wallet_address="0x123",
                    capabilities=["dev"],
                )
            )
        assert result.api_key == "tec_newkey123"
        assert result.agent.name == "Alice"
        assert route.called
        # Verify request body
        request_body = route.calls[0].request.content
        import json

        body = json.loads(request_body)
        assert body["name"] == "Alice"
        assert body["agent_type"] == "requester"

    @respx.mock
    async def test_get_agent(self):
        respx.get(f"{BASE_URL}/agents/agent-1").mock(
            return_value=httpx.Response(200, json=_agent_json())
        )
        async with TectonicClient(BASE_URL) as client:
            agent = await client.get_agent("agent-1")
        assert agent.id == "agent-1"
        assert agent.name == "Alice"
        assert agent.agent_type == AgentType.requester

    @respx.mock
    async def test_get_agent_reputation(self):
        respx.get(f"{BASE_URL}/agents/agent-1/reputation").mock(
            return_value=httpx.Response(200, json=_reputation_json())
        )
        async with TectonicClient(BASE_URL) as client:
            rep = await client.get_agent_reputation("agent-1")
        assert rep.reputation_score == 4.5
        assert rep.engagements_completed == 8
        assert len(rep.events) == 1


# ---------------------------------------------------------------------------
# Engagement endpoint tests
# ---------------------------------------------------------------------------


class TestEngagementEndpoints:
    @respx.mock
    async def test_create_engagement(self):
        route = respx.post(f"{BASE_URL}/engagements").mock(
            return_value=httpx.Response(200, json=_engagement_json())
        )
        async with TectonicClient(BASE_URL, api_key="tec_key") as client:
            engagement = await client.create_engagement(
                EngagementCreate(
                    title="Build CLI",
                    description="A CLI tool",
                    acceptance_criteria=["Works"],
                    category="development",
                    reward_amount=0.05,
                    deadline=datetime.now(timezone.utc),
                )
            )
        assert engagement.id == "engagement-1"
        assert engagement.status == EngagementStatus.open
        assert route.called

    @respx.mock
    async def test_list_engagements_no_filter(self):
        resp_json = {"engagements": [_engagement_json()], "total": 1}
        route = respx.get(f"{BASE_URL}/engagements").mock(
            return_value=httpx.Response(200, json=resp_json)
        )
        async with TectonicClient(BASE_URL) as client:
            result = await client.list_engagements()
        assert result.total == 1
        assert len(result.engagements) == 1
        assert route.called

    @respx.mock
    async def test_list_engagements_with_filters(self):
        resp_json = {"engagements": [], "total": 0}
        route = respx.get(f"{BASE_URL}/engagements").mock(
            return_value=httpx.Response(200, json=resp_json)
        )
        async with TectonicClient(BASE_URL) as client:
            result = await client.list_engagements(status="open", category="dev")
        assert result.total == 0
        request = route.calls[0].request
        assert "status=open" in str(request.url)
        assert "category=dev" in str(request.url)

    @respx.mock
    async def test_get_engagement(self):
        respx.get(f"{BASE_URL}/engagements/engagement-1").mock(
            return_value=httpx.Response(200, json=_engagement_json())
        )
        async with TectonicClient(BASE_URL) as client:
            engagement = await client.get_engagement("engagement-1")
        assert engagement.title == "Build CLI"

    @respx.mock
    async def test_update_engagement(self):
        from tectonic.types import EngagementUpdate

        updated_json = _engagement_json()
        updated_json["status"] = "in_progress"
        route = respx.patch(f"{BASE_URL}/engagements/engagement-1").mock(
            return_value=httpx.Response(200, json=updated_json)
        )
        async with TectonicClient(BASE_URL, api_key="tec_key") as client:
            engagement = await client.update_engagement(
                "engagement-1",
                EngagementUpdate(status=EngagementStatus.in_progress),
            )
        assert engagement.status == EngagementStatus.in_progress
        assert route.called


# ---------------------------------------------------------------------------
# Proposal endpoint tests
# ---------------------------------------------------------------------------


class TestProposalEndpoints:
    @respx.mock
    async def test_create_proposal(self):
        route = respx.post(f"{BASE_URL}/engagements/engagement-1/proposals").mock(
            return_value=httpx.Response(200, json=_proposal_json())
        )
        async with TectonicClient(BASE_URL, api_key="tec_key") as client:
            proposal = await client.create_proposal(
                "engagement-1",
                ProposalCreate(
                    proposed_price=0.04,
                    proposed_deadline=datetime.now(timezone.utc),
                    approach_summary="Will use Python",
                ),
            )
        assert proposal.id == "proposal-1"
        assert proposal.status == ProposalStatus.pending
        assert route.called

    @respx.mock
    async def test_list_proposals_bare_list(self):
        """API returns a bare JSON array."""
        respx.get(f"{BASE_URL}/engagements/engagement-1/proposals").mock(
            return_value=httpx.Response(200, json=[_proposal_json()])
        )
        async with TectonicClient(BASE_URL) as client:
            proposals = await client.list_proposals("engagement-1")
        assert len(proposals) == 1
        assert proposals[0].provider_id == "agent-2"

    @respx.mock
    async def test_list_proposals_wrapped(self):
        """API returns proposals wrapped in an object."""
        respx.get(f"{BASE_URL}/engagements/engagement-1/proposals").mock(
            return_value=httpx.Response(
                200, json={"proposals": [_proposal_json()]}
            )
        )
        async with TectonicClient(BASE_URL) as client:
            proposals = await client.list_proposals("engagement-1")
        assert len(proposals) == 1


# ---------------------------------------------------------------------------
# Negotiation endpoint tests
# ---------------------------------------------------------------------------


class TestNegotiationEndpoints:
    @respx.mock
    async def test_create_negotiation(self):
        route = respx.post(f"{BASE_URL}/negotiations").mock(
            return_value=httpx.Response(200, json=_negotiation_json())
        )
        async with TectonicClient(BASE_URL, api_key="tec_key") as client:
            neg = await client.create_negotiation("engagement-1", "proposal-1")
        assert neg.id == "neg-1"
        assert neg.status == NegotiationStatus.active
        import json

        body = json.loads(route.calls[0].request.content)
        assert body["engagement_id"] == "engagement-1"
        assert body["proposal_id"] == "proposal-1"

    @respx.mock
    async def test_get_negotiation(self):
        respx.get(f"{BASE_URL}/negotiations/neg-1").mock(
            return_value=httpx.Response(200, json=_negotiation_json())
        )
        async with TectonicClient(BASE_URL) as client:
            neg = await client.get_negotiation("neg-1")
        assert neg.requester_id == "agent-1"
        assert neg.provider_id == "agent-2"

    @respx.mock
    async def test_submit_turn_counter(self):
        route = respx.post(f"{BASE_URL}/negotiations/neg-1/turns").mock(
            return_value=httpx.Response(200, json=_turn_json())
        )
        terms = NegotiationTerms(
            price=0.05,
            deadline=datetime.now(timezone.utc),
            deliverables=["CLI tool"],
            acceptance_criteria=["Tests pass"],
            revision_rounds=2,
        )
        async with TectonicClient(BASE_URL, api_key="tec_key") as client:
            turn = await client.submit_turn(
                "neg-1",
                NegotiationTurnRequest(
                    turn_type=TurnType.counter,
                    proposed_terms=terms,
                    message="Counter offer",
                ),
            )
        assert turn.id == "turn-1"
        assert turn.turn_type == "counter"
        assert route.called

    @respx.mock
    async def test_submit_turn_accept(self):
        accept_turn = _turn_json()
        accept_turn["turn_type"] = "accept"
        accept_turn["proposed_terms"] = None
        respx.post(f"{BASE_URL}/negotiations/neg-1/turns").mock(
            return_value=httpx.Response(200, json=accept_turn)
        )
        async with TectonicClient(BASE_URL, api_key="tec_key") as client:
            turn = await client.submit_turn(
                "neg-1",
                NegotiationTurnRequest(
                    turn_type=TurnType.accept,
                    message="Deal!",
                ),
            )
        assert turn.turn_type == "accept"

    @respx.mock
    async def test_list_turns_bare_list(self):
        respx.get(f"{BASE_URL}/negotiations/neg-1/turns").mock(
            return_value=httpx.Response(200, json=[_turn_json()])
        )
        async with TectonicClient(BASE_URL) as client:
            turns = await client.list_turns("neg-1")
        assert len(turns) == 1

    @respx.mock
    async def test_list_turns_wrapped(self):
        respx.get(f"{BASE_URL}/negotiations/neg-1/turns").mock(
            return_value=httpx.Response(
                200, json={"turns": [_turn_json(), _turn_json("turn-2")]}
            )
        )
        async with TectonicClient(BASE_URL) as client:
            turns = await client.list_turns("neg-1")
        assert len(turns) == 2


# ---------------------------------------------------------------------------
# Contract endpoint tests
# ---------------------------------------------------------------------------


class TestContractEndpoints:
    @respx.mock
    async def test_create_contract(self):
        route = respx.post(f"{BASE_URL}/contracts").mock(
            return_value=httpx.Response(200, json=_contract_json())
        )
        async with TectonicClient(BASE_URL, api_key="tec_key") as client:
            contract = await client.create_contract("engagement-1", "neg-1")
        assert contract.id == "contract-1"
        assert contract.status == ContractStatus.pending_funding
        import json

        body = json.loads(route.calls[0].request.content)
        assert body["engagement_id"] == "engagement-1"
        assert body["negotiation_id"] == "neg-1"

    @respx.mock
    async def test_fund_contract(self):
        funded = _contract_json()
        funded["status"] = "funded"
        funded["funding_tx_hash"] = "0xtx"
        funded["escrow_contract_address"] = "0xescrow"
        route = respx.post(f"{BASE_URL}/contracts/contract-1/fund").mock(
            return_value=httpx.Response(200, json=funded)
        )
        async with TectonicClient(BASE_URL, api_key="tec_key") as client:
            contract = await client.fund_contract(
                "contract-1",
                ContractFundRequest(
                    funding_tx_hash="0xtx",
                    escrow_contract_address="0xescrow",
                ),
            )
        assert contract.status == ContractStatus.funded
        assert contract.funding_tx_hash == "0xtx"
        assert route.called

    @respx.mock
    async def test_deliver_contract(self):
        delivered = _contract_json()
        delivered["status"] = "delivered"
        delivered["deliverable_url"] = "https://github.com/test"
        respx.post(f"{BASE_URL}/contracts/contract-1/deliver").mock(
            return_value=httpx.Response(200, json=delivered)
        )
        async with TectonicClient(BASE_URL, api_key="tec_key") as client:
            contract = await client.deliver_contract(
                "contract-1",
                ContractDeliverRequest(deliverable_url="https://github.com/test"),
            )
        assert contract.status == ContractStatus.delivered

    @respx.mock
    async def test_verify_contract_approved(self):
        verified = _contract_json()
        verified["status"] = "verified"
        respx.post(f"{BASE_URL}/contracts/contract-1/verify").mock(
            return_value=httpx.Response(200, json=verified)
        )
        async with TectonicClient(BASE_URL, api_key="tec_key") as client:
            contract = await client.verify_contract(
                "contract-1",
                ContractVerifyRequest(approved=True),
            )
        assert contract.status == ContractStatus.verified

    @respx.mock
    async def test_verify_contract_rejected(self):
        disputed = _contract_json()
        disputed["status"] = "disputed"
        respx.post(f"{BASE_URL}/contracts/contract-1/verify").mock(
            return_value=httpx.Response(200, json=disputed)
        )
        async with TectonicClient(BASE_URL, api_key="tec_key") as client:
            contract = await client.verify_contract(
                "contract-1",
                ContractVerifyRequest(approved=False),
            )
        assert contract.status == ContractStatus.disputed

    @respx.mock
    async def test_dispute_contract(self):
        disputed = _contract_json()
        disputed["status"] = "disputed"
        respx.post(f"{BASE_URL}/contracts/contract-1/dispute").mock(
            return_value=httpx.Response(200, json=disputed)
        )
        async with TectonicClient(BASE_URL, api_key="tec_key") as client:
            contract = await client.dispute_contract("contract-1")
        assert contract.status == ContractStatus.disputed


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------


class TestErrorHandling:
    @respx.mock
    async def test_401_unauthorized(self):
        respx.get(f"{BASE_URL}/agents/agent-1").mock(
            return_value=httpx.Response(
                401, json={"detail": "Invalid or missing API key"}
            )
        )
        async with TectonicClient(BASE_URL) as client:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await client.get_agent("agent-1")
            assert exc_info.value.response.status_code == 401

    @respx.mock
    async def test_404_not_found(self):
        respx.get(f"{BASE_URL}/agents/nonexistent").mock(
            return_value=httpx.Response(404, json={"detail": "Not found"})
        )
        async with TectonicClient(BASE_URL) as client:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await client.get_agent("nonexistent")
            assert exc_info.value.response.status_code == 404

    @respx.mock
    async def test_422_validation_error(self):
        respx.post(f"{BASE_URL}/engagements").mock(
            return_value=httpx.Response(422, json={"detail": "Validation error"})
        )
        async with TectonicClient(BASE_URL, api_key="tec_key") as client:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await client.create_engagement(
                    EngagementCreate(
                        title="",
                        description="",
                        acceptance_criteria=[],
                        category="",
                        reward_amount=0.05,
                        deadline=datetime.now(timezone.utc),
                    )
                )
            assert exc_info.value.response.status_code == 422

    @respx.mock
    async def test_500_server_error(self):
        respx.get(f"{BASE_URL}/engagements").mock(
            return_value=httpx.Response(500, json={"detail": "Internal server error"})
        )
        async with TectonicClient(BASE_URL) as client:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await client.list_engagements()
            assert exc_info.value.response.status_code == 500


# ---------------------------------------------------------------------------
# URL and method verification
# ---------------------------------------------------------------------------


class TestRequestDetails:
    @respx.mock
    async def test_register_uses_post(self):
        route = respx.post(f"{BASE_URL}/agents/register").mock(
            return_value=httpx.Response(
                200, json={"agent": _agent_json(), "api_key": "tec_key"}
            )
        )
        async with TectonicClient(BASE_URL) as client:
            await client.register_agent(
                AgentCreate(name="Alice", agent_type=AgentType.requester)
            )
        assert route.calls[0].request.method == "POST"

    @respx.mock
    async def test_get_engagement_uses_get(self):
        route = respx.get(f"{BASE_URL}/engagements/e-1").mock(
            return_value=httpx.Response(200, json=_engagement_json())
        )
        async with TectonicClient(BASE_URL) as client:
            await client.get_engagement("e-1")
        assert route.calls[0].request.method == "GET"

    @respx.mock
    async def test_update_engagement_uses_patch(self):
        from tectonic.types import EngagementUpdate

        route = respx.patch(f"{BASE_URL}/engagements/e-1").mock(
            return_value=httpx.Response(200, json=_engagement_json())
        )
        async with TectonicClient(BASE_URL) as client:
            await client.update_engagement("e-1", EngagementUpdate())
        assert route.calls[0].request.method == "PATCH"

    @respx.mock
    async def test_dispute_uses_post(self):
        disputed = _contract_json()
        disputed["status"] = "disputed"
        route = respx.post(f"{BASE_URL}/contracts/c-1/dispute").mock(
            return_value=httpx.Response(200, json=disputed)
        )
        async with TectonicClient(BASE_URL) as client:
            await client.dispute_contract("c-1")
        assert route.calls[0].request.method == "POST"

    @respx.mock
    async def test_base_url_trailing_slash_stripped(self):
        respx.get(f"{BASE_URL}/agents/a-1").mock(
            return_value=httpx.Response(200, json=_agent_json())
        )
        async with TectonicClient(BASE_URL + "/") as client:
            assert client.base_url == BASE_URL
            agent = await client.get_agent("a-1")
            assert agent.id == "agent-1"


class TestInbox:
    @respx.mock
    async def test_get_inbox(self):
        inbox_data = {
            "engagements": [_engagement_json()],
            "total": 1,
        }
        route = respx.get(f"{BASE_URL}/agents/agent-1/inbox").mock(
            return_value=httpx.Response(200, json=inbox_data)
        )
        async with TectonicClient(BASE_URL) as client:
            result = await client.get_inbox("agent-1")
        assert result.total == 1
        assert len(result.engagements) == 1
        assert result.engagements[0].id == "engagement-1"

    @respx.mock
    async def test_get_inbox_with_status_filter(self):
        inbox_data = {"engagements": [], "total": 0}
        route = respx.get(f"{BASE_URL}/agents/agent-1/inbox").mock(
            return_value=httpx.Response(200, json=inbox_data)
        )
        async with TectonicClient(BASE_URL) as client:
            result = await client.get_inbox("agent-1", status="open")
        assert result.total == 0
        assert "status" in str(route.calls[0].request.url)

    @respx.mock
    async def test_get_inbox_empty(self):
        inbox_data = {"engagements": [], "total": 0}
        respx.get(f"{BASE_URL}/agents/agent-1/inbox").mock(
            return_value=httpx.Response(200, json=inbox_data)
        )
        async with TectonicClient(BASE_URL) as client:
            result = await client.get_inbox("agent-1")
        assert result.total == 0
        assert result.engagements == []
