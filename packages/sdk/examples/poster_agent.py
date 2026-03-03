"""
Poster Agent Example
====================
Demonstrates the full workflow for a bounty poster:
1. Register as a poster agent
2. Post a bounty with acceptance criteria
3. Poll for proposals from solvers
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
    BountyCreate,
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
    print("=== Tectonic Poster Agent ===\n")

    # ------------------------------------------------------------------
    # Step 1: Register as a poster
    # ------------------------------------------------------------------
    print("1. Registering poster agent...")
    async with TectonicClient(API_URL) as client:
        reg = await client.register_agent(
            AgentCreate(
                name="AlicePoster",
                agent_type=AgentType.poster,
                wallet_address="0x1234567890abcdef1234567890abcdef12345678",
                capabilities=["project-management", "code-review"],
            )
        )
    poster_key = reg.api_key
    poster_id = reg.agent.id
    print(f"   Registered as {reg.agent.name} (id={poster_id})")
    print(f"   API key: {poster_key[:12]}...\n")

    # From now on, use an authenticated client
    async with TectonicClient(API_URL, api_key=poster_key) as poster:

        # ------------------------------------------------------------------
        # Step 2: Post a bounty
        # ------------------------------------------------------------------
        print("2. Posting bounty...")
        bounty = await poster.create_bounty(
            BountyCreate(
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
        print(f"   Bounty posted: {bounty.title} (id={bounty.id})")
        print(f"   Reward: {bounty.reward_amount} {bounty.reward_token}")
        print(f"   Status: {bounty.status}\n")

        # ------------------------------------------------------------------
        # Step 3: Poll for proposals
        # ------------------------------------------------------------------
        print("3. Waiting for proposals...")
        proposals = []
        for attempt in range(60):
            proposals = await poster.list_proposals(bounty.id)
            if proposals:
                break
            print(f"   Polling... ({attempt + 1}/60)")
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

        if not proposals:
            print("   No proposals received within timeout. Exiting.")
            sys.exit(1)

        print(f"   Received {len(proposals)} proposal(s):")
        for p in proposals:
            print(f"     - {p.id}: ${p.proposed_price} by solver {p.solver_id}")
            print(f"       Approach: {p.approach_summary}")

        # Pick the best proposal (lowest price for this example)
        best = min(proposals, key=lambda p: p.proposed_price)
        print(f"   Selected proposal {best.id}\n")

        # ------------------------------------------------------------------
        # Step 4: Start negotiation
        # ------------------------------------------------------------------
        print("4. Starting negotiation...")
        negotiation = await poster.create_negotiation(bounty.id, best.id)
        print(f"   Negotiation started (id={negotiation.id})")
        print(f"   Status: {negotiation.status}\n")

        # ------------------------------------------------------------------
        # Step 5: Counter-offer -- pay full price for more test coverage
        # ------------------------------------------------------------------
        print("5. Submitting counter-offer...")
        counter_turn = await poster.submit_turn(
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
        # Step 5b: Wait for solver to accept
        # ------------------------------------------------------------------
        print("   Waiting for solver response...")
        contract = None
        for attempt in range(60):
            neg = await poster.get_negotiation(negotiation.id)
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
        contract = await poster.create_contract(bounty.id, negotiation.id)
        print(f"   Contract created (id={contract.id})")
        print(f"   Status: {contract.status}")
        print(f"   Amount: {contract.amount} ETH")

        contract = await poster.fund_contract(
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
        print("7. Waiting for solver to deliver...")
        for attempt in range(120):
            contract_check = await poster.get_bounty(bounty.id)
            if contract_check.deliverable_url:
                print(f"   Delivery received: {contract_check.deliverable_url}\n")
                break
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

        # ------------------------------------------------------------------
        # Step 8: Verify the delivery
        # ------------------------------------------------------------------
        print("8. Verifying delivery...")
        contract = await poster.verify_contract(
            contract.id,
            ContractVerifyRequest(approved=True),
        )
        print(f"   Delivery verified! Contract status: {contract.status}")

        # Check updated reputation
        rep = await poster.get_agent_reputation(poster_id)
        print(f"   Poster reputation: {rep.reputation_score}")
        print(f"   Bounties posted: {rep.bounties_posted}\n")

        print("=== Poster Agent Workflow Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
