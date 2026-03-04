import uuid
from datetime import datetime, timezone, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bounty import EngagementStatus
from app.models.contract import Contract, ContractStatus
from app.models.negotiation import NegotiationStatus
from app.services.contract_service import (
    compute_terms_hash,
    create_contract_from_negotiation,
    deliver_contract,
    dispute_contract,
    fund_contract,
    verify_contract,
)
from tests.conftest import (
    create_test_agent,
    create_test_engagement,
    create_test_negotiation,
    create_test_proposal,
)


class TestComputeTermsHash:
    def test_hash_is_deterministic(self):
        terms = {"price": 1.0, "deadline": "2099-01-01"}
        hash1 = compute_terms_hash(terms)
        hash2 = compute_terms_hash(terms)
        assert hash1 == hash2

    def test_hash_starts_with_0x(self):
        terms = {"price": 1.0}
        h = compute_terms_hash(terms)
        assert h.startswith("0x")

    def test_different_terms_different_hash(self):
        h1 = compute_terms_hash({"price": 1.0})
        h2 = compute_terms_hash({"price": 2.0})
        assert h1 != h2

    def test_hash_is_hex(self):
        h = compute_terms_hash({"foo": "bar"})
        # Remove 0x prefix and validate hex
        hex_part = h[2:]
        int(hex_part, 16)  # Should not raise


class TestCreateContractFromNegotiation:
    @pytest.mark.asyncio
    async def test_create_contract_success(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="cs-requester1")
        provider, _ = await create_test_agent(db_session, name="cs-provider1")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        current_terms = {"price": 0.8, "deadline": "2099-01-01"}
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider,
            status=NegotiationStatus.agreed,
            current_terms=current_terms,
        )

        contract = await create_contract_from_negotiation(
            engagement.id, negotiation.id, requester.id, db_session,
        )

        assert contract.status == ContractStatus.pending_funding
        assert contract.requester_id == requester.id
        assert contract.provider_id == provider.id
        assert contract.amount == 0.8
        assert contract.terms_hash.startswith("0x")
        assert contract.agreed_terms == current_terms

    @pytest.mark.asyncio
    async def test_create_contract_non_agreed_negotiation_fails(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="cs-requester2")
        provider, _ = await create_test_agent(db_session, name="cs-provider2")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider,
            status=NegotiationStatus.active,
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_contract_from_negotiation(
                engagement.id, negotiation.id, requester.id, db_session,
            )
        assert exc_info.value.status_code == 400
        assert "agreed" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_contract_nonexistent_negotiation(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="cs-requester3")
        engagement = await create_test_engagement(db_session, requester)

        with pytest.raises(HTTPException) as exc_info:
            await create_contract_from_negotiation(
                engagement.id, uuid.uuid4(), requester.id, db_session,
            )
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_contract_non_party_fails(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="cs-requester4")
        provider, _ = await create_test_agent(db_session, name="cs-provider4")
        outsider, _ = await create_test_agent(db_session, name="cs-outsider4")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider,
            status=NegotiationStatus.agreed,
            current_terms={"price": 1.0},
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_contract_from_negotiation(
                engagement.id, negotiation.id, outsider.id, db_session,
            )
        assert exc_info.value.status_code == 403


class TestFundContract:
    @pytest.mark.asyncio
    async def test_fund_contract_success(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="cs-requester5")
        provider, _ = await create_test_agent(db_session, name="cs-provider5")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider,
            status=NegotiationStatus.agreed,
            current_terms={"price": 1.0},
        )
        contract = await create_contract_from_negotiation(
            engagement.id, negotiation.id, requester.id, db_session,
        )

        funded = await fund_contract(
            contract.id, "0x" + "a" * 64, "0x" + "b" * 40, requester.id, db_session,
        )
        assert funded.status == ContractStatus.funded
        assert funded.funding_tx_hash == "0x" + "a" * 64

    @pytest.mark.asyncio
    async def test_fund_contract_by_provider_fails(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="cs-requester6")
        provider, _ = await create_test_agent(db_session, name="cs-provider6")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider,
            status=NegotiationStatus.agreed,
            current_terms={"price": 1.0},
        )
        contract = await create_contract_from_negotiation(
            engagement.id, negotiation.id, requester.id, db_session,
        )

        with pytest.raises(HTTPException) as exc_info:
            await fund_contract(
                contract.id, "0x" + "a" * 64, "0x" + "b" * 40, provider.id, db_session,
            )
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_fund_already_funded_contract_fails(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="cs-requester7")
        provider, _ = await create_test_agent(db_session, name="cs-provider7")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider,
            status=NegotiationStatus.agreed,
            current_terms={"price": 1.0},
        )
        contract = await create_contract_from_negotiation(
            engagement.id, negotiation.id, requester.id, db_session,
        )
        await fund_contract(
            contract.id, "0x" + "a" * 64, "0x" + "b" * 40, requester.id, db_session,
        )

        with pytest.raises(HTTPException) as exc_info:
            await fund_contract(
                contract.id, "0x" + "c" * 64, "0x" + "d" * 40, requester.id, db_session,
            )
        assert exc_info.value.status_code == 400


class TestDeliverContract:
    @pytest.mark.asyncio
    async def test_deliver_contract_success(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="cs-requester8")
        provider, _ = await create_test_agent(db_session, name="cs-provider8")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider,
            status=NegotiationStatus.agreed,
            current_terms={"price": 1.0},
        )
        contract = await create_contract_from_negotiation(
            engagement.id, negotiation.id, requester.id, db_session,
        )
        await fund_contract(
            contract.id, "0x" + "a" * 64, "0x" + "b" * 40, requester.id, db_session,
        )

        delivered = await deliver_contract(
            contract.id, "https://example.com/result", provider.id, db_session,
        )
        assert delivered.status == ContractStatus.delivered

    @pytest.mark.asyncio
    async def test_deliver_by_requester_fails(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="cs-requester9")
        provider, _ = await create_test_agent(db_session, name="cs-provider9")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider,
            status=NegotiationStatus.agreed,
            current_terms={"price": 1.0},
        )
        contract = await create_contract_from_negotiation(
            engagement.id, negotiation.id, requester.id, db_session,
        )
        await fund_contract(
            contract.id, "0x" + "a" * 64, "0x" + "b" * 40, requester.id, db_session,
        )

        with pytest.raises(HTTPException) as exc_info:
            await deliver_contract(
                contract.id, "https://example.com/result", requester.id, db_session,
            )
        assert exc_info.value.status_code == 403


class TestVerifyContract:
    @pytest.mark.asyncio
    async def test_verify_approved_settles_contract(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="cs-requester10")
        provider, _ = await create_test_agent(db_session, name="cs-provider10")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider,
            status=NegotiationStatus.agreed,
            current_terms={"price": 1.0},
        )
        contract = await create_contract_from_negotiation(
            engagement.id, negotiation.id, requester.id, db_session,
        )
        await fund_contract(
            contract.id, "0x" + "a" * 64, "0x" + "b" * 40, requester.id, db_session,
        )
        await deliver_contract(
            contract.id, "https://example.com/result", provider.id, db_session,
        )

        settled = await verify_contract(contract.id, True, requester.id, db_session)
        assert settled.status == ContractStatus.settled

        # Provider's engagements_completed should be incremented
        await db_session.refresh(provider)
        assert provider.engagements_completed == 1

    @pytest.mark.asyncio
    async def test_verify_rejected_disputes_contract(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="cs-requester11")
        provider, _ = await create_test_agent(db_session, name="cs-provider11")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider,
            status=NegotiationStatus.agreed,
            current_terms={"price": 1.0},
        )
        contract = await create_contract_from_negotiation(
            engagement.id, negotiation.id, requester.id, db_session,
        )
        await fund_contract(
            contract.id, "0x" + "a" * 64, "0x" + "b" * 40, requester.id, db_session,
        )
        await deliver_contract(
            contract.id, "https://example.com/result", provider.id, db_session,
        )

        disputed = await verify_contract(contract.id, False, requester.id, db_session)
        assert disputed.status == ContractStatus.disputed


class TestDisputeContract:
    @pytest.mark.asyncio
    async def test_dispute_by_requester(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="cs-requester12")
        provider, _ = await create_test_agent(db_session, name="cs-provider12")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider,
            status=NegotiationStatus.agreed,
            current_terms={"price": 1.0},
        )
        contract = await create_contract_from_negotiation(
            engagement.id, negotiation.id, requester.id, db_session,
        )
        await fund_contract(
            contract.id, "0x" + "a" * 64, "0x" + "b" * 40, requester.id, db_session,
        )

        disputed = await dispute_contract(contract.id, requester.id, db_session)
        assert disputed.status == ContractStatus.disputed

    @pytest.mark.asyncio
    async def test_dispute_by_provider(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="cs-requester13")
        provider, _ = await create_test_agent(db_session, name="cs-provider13")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider,
            status=NegotiationStatus.agreed,
            current_terms={"price": 1.0},
        )
        contract = await create_contract_from_negotiation(
            engagement.id, negotiation.id, requester.id, db_session,
        )
        await fund_contract(
            contract.id, "0x" + "a" * 64, "0x" + "b" * 40, requester.id, db_session,
        )

        disputed = await dispute_contract(contract.id, provider.id, db_session)
        assert disputed.status == ContractStatus.disputed

    @pytest.mark.asyncio
    async def test_dispute_by_outsider_fails(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="cs-requester14")
        provider, _ = await create_test_agent(db_session, name="cs-provider14")
        outsider, _ = await create_test_agent(db_session, name="cs-outsider14")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider,
            status=NegotiationStatus.agreed,
            current_terms={"price": 1.0},
        )
        contract = await create_contract_from_negotiation(
            engagement.id, negotiation.id, requester.id, db_session,
        )

        with pytest.raises(HTTPException) as exc_info:
            await dispute_contract(contract.id, outsider.id, db_session)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_dispute_settled_contract_fails(self, db_session: AsyncSession):
        requester, _ = await create_test_agent(db_session, name="cs-requester15")
        provider, _ = await create_test_agent(db_session, name="cs-provider15")
        engagement = await create_test_engagement(db_session, requester)
        proposal = await create_test_proposal(db_session, engagement, provider)
        negotiation = await create_test_negotiation(
            db_session, engagement, proposal, requester, provider,
            status=NegotiationStatus.agreed,
            current_terms={"price": 1.0},
        )
        contract = await create_contract_from_negotiation(
            engagement.id, negotiation.id, requester.id, db_session,
        )
        await fund_contract(
            contract.id, "0x" + "a" * 64, "0x" + "b" * 40, requester.id, db_session,
        )
        await deliver_contract(
            contract.id, "https://example.com/result", provider.id, db_session,
        )
        await verify_contract(contract.id, True, requester.id, db_session)

        with pytest.raises(HTTPException) as exc_info:
            await dispute_contract(contract.id, requester.id, db_session)
        assert exc_info.value.status_code == 400
