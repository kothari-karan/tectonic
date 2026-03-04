"""
Tectonic Protocol Demo
======================
Runs a complete engagement lifecycle end-to-end:

1. Register requester and provider agents
2. Requester posts an engagement
3. Provider discovers and submits proposal
4. Multi-turn negotiation
5. Contract creation and funding
6. Delivery and verification
7. Settlement and reputation update

Usage::

    # Start the API server first:
    #   cd packages/api && uvicorn app.main:app --reload

    python scripts/demo.py
    python scripts/demo.py --api-url http://my-server:8000
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone

from tectonic import (
    AgentCreate,
    AgentType,
    EngagementCreate,
    ContractDeliverRequest,
    ContractFundRequest,
    ContractVerifyRequest,
    NegotiationTerms,
    NegotiationTurnRequest,
    ProposalCreate,
    TectonicClient,
    TurnType,
)


def _ts() -> str:
    """Return a short timestamp for log lines."""
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def _separator(char: str = "-", width: int = 60) -> str:
    return char * width


async def run_demo(api_url: str) -> None:
    print(f"\n{_separator('=')}")
    print("  Tectonic Protocol Demo -- Full Engagement Lifecycle")
    print(f"{_separator('=')}\n")
    print(f"API URL: {api_url}\n")

    # =====================================================================
    # Step 1: Register both agents
    # =====================================================================
    print(f"[{_ts()}] STEP 1: Registering agents")
    print(_separator())

    async with TectonicClient(api_url) as anon_client:
        # Register requester
        requester_resp = await anon_client.register_agent(
            AgentCreate(
                name="AliceRequester",
                agent_type=AgentType.requester,
                wallet_address="0x1111111111111111111111111111111111111111",
                capabilities=["project-management", "code-review"],
            )
        )
        requester_id = requester_resp.agent.id
        requester_key = requester_resp.api_key
        print(f"  Requester registered: {requester_resp.agent.name}")
        print(f"    ID:  {requester_id}")
        print(f"    Key: {requester_key[:16]}...")

        # Register provider
        provider_resp = await anon_client.register_agent(
            AgentCreate(
                name="BobProvider",
                agent_type=AgentType.provider,
                wallet_address="0x2222222222222222222222222222222222222222",
                capabilities=["python", "cli-tools", "testing", "data-processing"],
            )
        )
        provider_id = provider_resp.agent.id
        provider_key = provider_resp.api_key
        print(f"  Provider registered: {provider_resp.agent.name}")
        print(f"    ID:  {provider_id}")
        print(f"    Key: {provider_key[:16]}...")

    # Create authenticated clients
    requester_client = TectonicClient(api_url, api_key=requester_key)
    provider_client = TectonicClient(api_url, api_key=provider_key)

    try:
        # =================================================================
        # Step 2: Requester creates an engagement
        # =================================================================
        print(f"\n[{_ts()}] STEP 2: Posting engagement")
        print(_separator())

        engagement = await requester_client.create_engagement(
            EngagementCreate(
                title="Build CSV to JSON CLI tool",
                description=(
                    "Python CLI tool that converts CSV files to JSON format. "
                    "Must support streaming for large files, custom delimiters, "
                    "and output to stdout or file. Should handle edge cases like "
                    "quoted fields, Unicode, and malformed input gracefully."
                ),
                acceptance_criteria=[
                    "Handles standard CSV with headers",
                    "Supports custom delimiters (tab, pipe, semicolon)",
                    "90%+ test coverage with pytest",
                    "Proper error handling for malformed input",
                    "Streaming support for files > 1GB",
                ],
                category="development",
                reward_amount=0.05,
                deadline=datetime.now(timezone.utc) + timedelta(days=7),
            )
        )
        print(f"  Engagement created: {engagement.title}")
        print(f"    ID:     {engagement.id}")
        print(f"    Reward: {engagement.reward_amount} {engagement.reward_token}")
        print(f"    Status: {engagement.status.value}")

        # =================================================================
        # Step 3: Provider discovers engagement and submits proposal
        # =================================================================
        print(f"\n[{_ts()}] STEP 3: Provider browsing and submitting proposal")
        print(_separator())

        # Provider browses open engagements
        engagement_list = await provider_client.list_engagements(status="open")
        print(f"  Found {engagement_list.total} open engagement(s)")

        target = None
        for b in engagement_list.engagements:
            if b.id == engagement.id:
                target = b
                break
        if target is None:
            print("  ERROR: Could not find the posted engagement!")
            sys.exit(1)

        print(f"  Matched engagement: {target.title}")

        # Submit proposal at 80% of asking price
        proposal = await provider_client.create_proposal(
            engagement.id,
            ProposalCreate(
                proposed_price=0.04,
                proposed_deadline=datetime.now(timezone.utc) + timedelta(days=5),
                approach_summary=(
                    "Will implement using Click for the CLI framework and the "
                    "built-in csv module for parsing. Custom delimiter support "
                    "via --delimiter flag. Comprehensive test suite targeting "
                    "95% coverage. Streaming via chunked line-by-line reading."
                ),
            ),
        )
        print(f"  Proposal submitted: {proposal.id}")
        print(f"    Price: {proposal.proposed_price} ETH (vs {engagement.reward_amount} asked)")
        print(f"    Status: {proposal.status.value}")

        # =================================================================
        # Step 4: Requester reviews proposals and starts negotiation
        # =================================================================
        print(f"\n[{_ts()}] STEP 4: Multi-turn negotiation")
        print(_separator())

        # Requester checks proposals
        proposals = await requester_client.list_proposals(engagement.id)
        print(f"  Requester sees {len(proposals)} proposal(s)")

        best_proposal = proposals[0]
        print(f"  Best proposal: {best_proposal.id} at {best_proposal.proposed_price} ETH")

        # Start negotiation
        negotiation = await requester_client.create_negotiation(engagement.id, best_proposal.id)
        print(f"  Negotiation started: {negotiation.id}")
        print(f"    Status: {negotiation.status.value}")

        # --  Turn 1: Requester counter-offers (full price for more features) --
        print(f"\n  Turn 1: Requester counter-offers...")
        turn1 = await requester_client.submit_turn(
            negotiation.id,
            NegotiationTurnRequest(
                turn_type=TurnType.counter,
                proposed_terms=NegotiationTerms(
                    price=0.05,
                    deadline=datetime.now(timezone.utc) + timedelta(days=5),
                    deliverables=[
                        "CLI tool with Click framework",
                        "README with usage examples",
                        "Comprehensive pytest test suite",
                    ],
                    acceptance_criteria=[
                        "90%+ test coverage",
                        "Custom delimiters (tab, pipe, semicolon)",
                        "Proper error handling for malformed CSV",
                        "Streaming for files > 1GB",
                    ],
                    revision_rounds=2,
                ),
                message=(
                    "I'll pay the full 0.05 ETH if you guarantee 90%+ test "
                    "coverage and include streaming support for large files."
                ),
            ),
        )
        print(f"    Turn {turn1.sequence}: {turn1.turn_type}")
        print(f"    Message: {turn1.message}")

        # -- Turn 2: Provider accepts --
        print(f"\n  Turn 2: Provider accepts...")
        turn2 = await provider_client.submit_turn(
            negotiation.id,
            NegotiationTurnRequest(
                turn_type=TurnType.accept,
                message=(
                    "Deal! I'll deliver within 5 days with comprehensive tests "
                    "and streaming support. 2 revision rounds works for me."
                ),
            ),
        )
        print(f"    Turn {turn2.sequence}: {turn2.turn_type}")
        print(f"    Message: {turn2.message}")

        # Check negotiation status
        negotiation = await requester_client.get_negotiation(negotiation.id)
        print(f"\n  Negotiation status: {negotiation.status.value}")
        print(f"  Total turns: {negotiation.turn_count}")

        # =================================================================
        # Step 5: Create and fund contract
        # =================================================================
        print(f"\n[{_ts()}] STEP 5: Contract creation and funding")
        print(_separator())

        contract = await requester_client.create_contract(engagement.id, negotiation.id)
        print(f"  Contract created: {contract.id}")
        print(f"    Status: {contract.status.value}")
        print(f"    Amount: {contract.amount} ETH")
        print(f"    Terms hash: {contract.terms_hash}")

        # Fund the escrow
        contract = await requester_client.fund_contract(
            contract.id,
            ContractFundRequest(
                funding_tx_hash="0xaabbccdd11223344aabbccdd11223344aabbccdd11223344aabbccdd11223344",
                escrow_contract_address="0xEscrow9999888877776666555544443333222211",
            ),
        )
        print(f"  Contract funded!")
        print(f"    Status: {contract.status.value}")
        print(f"    Escrow: {contract.escrow_contract_address}")
        print(f"    Tx hash: {contract.funding_tx_hash}")

        # =================================================================
        # Step 6: Provider delivers work
        # =================================================================
        print(f"\n[{_ts()}] STEP 6: Delivery")
        print(_separator())

        contract = await provider_client.deliver_contract(
            contract.id,
            ContractDeliverRequest(
                deliverable_url="https://github.com/bobprovider/csv-to-json-cli",
            ),
        )
        print(f"  Delivery submitted!")
        print(f"    Status: {contract.status.value}")

        # =================================================================
        # Step 7: Requester verifies and contract settles
        # =================================================================
        print(f"\n[{_ts()}] STEP 7: Verification and settlement")
        print(_separator())

        contract = await requester_client.verify_contract(
            contract.id,
            ContractVerifyRequest(approved=True),
        )
        print(f"  Delivery verified!")
        print(f"    Final status: {contract.status.value}")

        # =================================================================
        # Step 8: Check reputation updates
        # =================================================================
        print(f"\n[{_ts()}] STEP 8: Reputation check")
        print(_separator())

        requester_rep = await requester_client.get_agent_reputation(requester_id)
        provider_rep = await provider_client.get_agent_reputation(provider_id)

        print(f"  Requester ({requester_resp.agent.name}):")
        print(f"    Reputation score: {requester_rep.reputation_score}")
        print(f"    Engagements posted:  {requester_rep.engagements_posted}")

        print(f"  Provider ({provider_resp.agent.name}):")
        print(f"    Reputation score: {provider_rep.reputation_score}")
        print(f"    Engagements completed: {provider_rep.engagements_completed}")

        # =================================================================
        # Done
        # =================================================================
        print(f"\n{_separator('=')}")
        print("  Demo Complete!")
        print(f"{_separator('=')}")
        print(f"\nFull lifecycle executed:")
        print(f"  1. Registered 2 agents (requester + provider)")
        print(f"  2. Posted engagement: {engagement.title}")
        print(f"  3. Submitted proposal at {proposal.proposed_price} ETH")
        print(f"  4. Negotiated in {negotiation.turn_count} turns -> {negotiation.status.value}")
        print(f"  5. Created & funded contract ({contract.amount} ETH)")
        print(f"  6. Delivered work")
        print(f"  7. Verified delivery -> status: {contract.status.value}")
        print(f"  8. Reputation updated for both agents")
        print()

    finally:
        await requester_client.close()
        await provider_client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Tectonic Protocol Demo")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Tectonic API base URL (default: http://localhost:8000)",
    )
    args = parser.parse_args()

    asyncio.run(run_demo(args.api_url))


if __name__ == "__main__":
    main()
