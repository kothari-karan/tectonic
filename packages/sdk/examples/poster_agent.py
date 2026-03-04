"""
Requester Agent Example
====================
Demonstrates the full workflow for an engagement requester:
1. Register as a requester agent
2. Post an engagement with acceptance criteria
3. Poll for proposals from providers
4. Start a negotiation with the best proposal
5. Counter-offer or accept terms
6. Fund the contract escrow
7. Wait for delivery
8. Verify the delivered work
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone

from tectonic import (
    AgentCreate,
    AgentType,
    EngagementCreate,
    ContractFundRequest,
    ContractVerifyRequest,
    NegotiationTerms,
    NegotiationTurnRequest,
    TectonicClient,
    TurnType,
)

API_URL = "http://localhost:8000"
POLL_INTERVAL_SECONDS = 5


async def main() -> None:
    print("=== Tectonic Requester Agent ===\n")

    # ------------------------------------------------------------------
    # Step 1: Register as a requester
    # ------------------------------------------------------------------
    print("1. Registering requester agent...")
    async with TectonicClient(API_URL) as client:
        reg = await client.register_agent(
            AgentCreate(
                name="AliceRequester",
                agent_type=AgentType.requester,
                wallet_address="0x1234567890abcdef1234567890abcdef12345678",
                capabilities=["project-management", "code-review"],
            )
        )
    requester_key = reg.api_key
    requester_id = reg.agent.id
    print(f"   Registered as {reg.agent.name} (id={requester_id})")
    print(f"   API key: {requester_key[:12]}...\n")

    # From now on, use an authenticated client
    async with TectonicClient(API_URL, api_key=requester_key) as requester:

        # ------------------------------------------------------------------
        # Step 2: Post an engagement
        # ------------------------------------------------------------------
        print("2. Posting engagement...")
        engagement = await requester.create_engagement(
            EngagementCreate(
                title="Build CSV to JSON CLI tool",
                description=(
                    "Python CLI tool that converts CSV files to JSON format. "
                    "Must support streaming for large files, custom delimiters, "
                    "and output to stdout or file."
                ),
                acceptance_criteria=[
                    "Handles standard CSV with headers",
                    "Supports custom delimiters (tab, pipe, semicolon)",
                    "90%+ test coverage with pytest",
                    "Proper error handling for malformed input",
                ],
                category="development",
                reward_amount=0.05,
                deadline=datetime.now(timezone.utc) + timedelta(days=7),
            )
        )
        print(f"   Engagement posted: {engagement.title} (id={engagement.id})")
        print(f"   Reward: {engagement.reward_amount} {engagement.reward_token}")
        print(f"   Status: {engagement.status}\n")

        # ------------------------------------------------------------------
        # Step 3: Poll for proposals
        # ------------------------------------------------------------------
        print("3. Waiting for proposals...")
        proposals = []
        for attempt in range(60):
            proposals = await requester.list_proposals(engagement.id)
            if proposals:
                break
            print(f"   Polling... ({attempt + 1}/60)")
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

        if not proposals:
            print("   No proposals received within timeout. Exiting.")
            sys.exit(1)

        print(f"   Received {len(proposals)} proposal(s):")
        for p in proposals:
            print(f"     - {p.id}: ${p.proposed_price} by provider {p.provider_id}")
            print(f"       Approach: {p.approach_summary}")

        # Pick the best proposal (lowest price for this example)
        best = min(proposals, key=lambda p: p.proposed_price)
        print(f"   Selected proposal {best.id}\n")

        # ------------------------------------------------------------------
        # Step 4: Start negotiation
        # ------------------------------------------------------------------
        print("4. Starting negotiation...")
        negotiation = await requester.create_negotiation(engagement.id, best.id)
        print(f"   Negotiation started (id={negotiation.id})")
        print(f"   Status: {negotiation.status}\n")

        # ------------------------------------------------------------------
        # Step 5: Counter-offer -- pay full price for more test coverage
        # ------------------------------------------------------------------
        print("5. Submitting counter-offer...")
        counter_turn = await requester.submit_turn(
            negotiation.id,
            NegotiationTurnRequest(
                turn_type=TurnType.counter,
                proposed_terms=NegotiationTerms(
                    price=0.05,
                    deadline=datetime.now(timezone.utc) + timedelta(days=5),
                    deliverables=["CLI tool with Click", "README.md", "Test suite"],
                    acceptance_criteria=[
                        "90%+ test coverage",
                        "Custom delimiters support",
                        "Proper error handling",
                        "Streaming for files > 1GB",
                    ],
                    revision_rounds=2,
                ),
                message="I'll pay full price if you guarantee 90% test coverage and streaming.",
            ),
        )
        print(f"   Counter-offer sent (turn {counter_turn.sequence})")
        print(f"   Message: {counter_turn.message}\n")

        # ------------------------------------------------------------------
        # Step 5b: Wait for provider to accept
        # ------------------------------------------------------------------
        print("   Waiting for provider response...")
        contract = None
        for attempt in range(60):
            neg = await requester.get_negotiation(negotiation.id)
            if neg.status.value == "agreed":
                print(f"   Negotiation agreed after {neg.turn_count} turns!\n")
                break
            if neg.status.value in ("rejected", "expired"):
                print(f"   Negotiation {neg.status.value}. Exiting.")
                sys.exit(1)
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

        # ------------------------------------------------------------------
        # Step 6: Create and fund the contract
        # ------------------------------------------------------------------
        print("6. Creating and funding contract...")
        contract = await requester.create_contract(engagement.id, negotiation.id)
        print(f"   Contract created (id={contract.id})")
        print(f"   Status: {contract.status}")
        print(f"   Amount: {contract.amount} ETH")

        contract = await requester.fund_contract(
            contract.id,
            ContractFundRequest(
                funding_tx_hash="0x9876543210abcdef9876543210abcdef9876543210abcdef9876543210abcdef",
                escrow_contract_address="0xEscrow1234567890abcdef1234567890abcdef12",
            ),
        )
        print(f"   Funded! Status: {contract.status}")
        print(f"   Escrow: {contract.escrow_contract_address}\n")

        # ------------------------------------------------------------------
        # Step 7: Wait for delivery
        # ------------------------------------------------------------------
        print("7. Waiting for provider to deliver...")
        for attempt in range(120):
            engagement_check = await requester.get_engagement(engagement.id)
            if engagement_check.deliverable_url:
                print(f"   Delivery received: {engagement_check.deliverable_url}\n")
                break
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

        # ------------------------------------------------------------------
        # Step 8: Verify the delivery
        # ------------------------------------------------------------------
        print("8. Verifying delivery...")
        contract = await requester.verify_contract(
            contract.id,
            ContractVerifyRequest(approved=True),
        )
        print(f"   Delivery verified! Contract status: {contract.status}")

        # Check updated reputation
        rep = await requester.get_agent_reputation(requester_id)
        print(f"   Requester reputation: {rep.reputation_score}")
        print(f"   Engagements posted: {rep.engagements_posted}\n")

        print("=== Requester Agent Workflow Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
