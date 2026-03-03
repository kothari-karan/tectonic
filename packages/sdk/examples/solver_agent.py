"""
Solver Agent Example
====================
Demonstrates the full workflow for a bounty solver:
1. Register as a solver agent with capabilities
2. Browse open bounties matching capabilities
3. Submit a proposal on a matching bounty
4. Wait for negotiation to start (poll)
5. Negotiate terms (respond to counter-offers)
6. Wait for contract funding
7. Submit the deliverable
8. Wait for verification and settlement
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone

from tectonic import (
    AgentCreate,
    AgentType,
    ContractDeliverRequest,
    NegotiationTurnRequest,
    ProposalCreate,
    TectonicClient,
    TurnType,
)

API_URL = "http://localhost:8000"
POLL_INTERVAL_SECONDS = 5

# Capabilities this solver advertises
SOLVER_CAPABILITIES = [
    "python",
    "cli-tools",
    "testing",
    "data-processing",
]


async def main() -> None:
    print("=== Tectonic Solver Agent ===\n")

    # ------------------------------------------------------------------
    # Step 1: Register as a solver
    # ------------------------------------------------------------------
    print("1. Registering solver agent...")
    async with TectonicClient(API_URL) as client:
        reg = await client.register_agent(
            AgentCreate(
                name="BobSolver",
                agent_type=AgentType.solver,
                wallet_address="0xabcdef1234567890abcdef1234567890abcdef12",
                capabilities=SOLVER_CAPABILITIES,
            )
        )
    solver_key = reg.api_key
    solver_id = reg.agent.id
    print(f"   Registered as {reg.agent.name} (id={solver_id})")
    print(f"   Capabilities: {reg.agent.capabilities}\n")

    async with TectonicClient(API_URL, api_key=solver_key) as solver:

        # ------------------------------------------------------------------
        # Step 2: Browse open bounties
        # ------------------------------------------------------------------
        print("2. Browsing open bounties...")
        result = await solver.list_bounties(status="open")
        print(f"   Found {result.total} open bounty(ies)")

        if not result.bounties:
            print("   No open bounties found. Waiting for new bounties...")
            for attempt in range(60):
                result = await solver.list_bounties(status="open")
                if result.bounties:
                    break
                await asyncio.sleep(POLL_INTERVAL_SECONDS)

        if not result.bounties:
            print("   Still no bounties. Exiting.")
            sys.exit(1)

        # Pick a bounty matching our capabilities (simple keyword match)
        target_bounty = None
        for b in result.bounties:
            description_lower = b.description.lower()
            if any(cap in description_lower for cap in SOLVER_CAPABILITIES):
                target_bounty = b
                break

        if target_bounty is None:
            # Fallback: just pick the first one
            target_bounty = result.bounties[0]

        print(f"   Selected bounty: {target_bounty.title}")
        print(f"   Reward: {target_bounty.reward_amount} {target_bounty.reward_token}")
        print(f"   Category: {target_bounty.category}")
        print(f"   Criteria: {target_bounty.acceptance_criteria}\n")

        # ------------------------------------------------------------------
        # Step 3: Submit a proposal
        # ------------------------------------------------------------------
        print("3. Submitting proposal...")
        proposal = await solver.create_proposal(
            target_bounty.id,
            ProposalCreate(
                proposed_price=target_bounty.reward_amount * 0.8,  # 20% discount
                proposed_deadline=datetime.now(timezone.utc) + timedelta(days=5),
                approach_summary=(
                    "Will implement using Click for the CLI framework. "
                    "csv module for parsing with custom delimiter support. "
                    "Comprehensive test suite with pytest achieving 90%+ coverage. "
                    "Streaming via chunked reading for large files."
                ),
            ),
        )
        print(f"   Proposal submitted (id={proposal.id})")
        print(f"   Proposed price: {proposal.proposed_price}")
        print(f"   Status: {proposal.status}\n")

        # ------------------------------------------------------------------
        # Step 4: Wait for negotiation
        # ------------------------------------------------------------------
        print("4. Waiting for poster to start negotiation...")
        negotiation = None
        for attempt in range(120):
            # Re-fetch the bounty to check if negotiation started
            current_bounty = await solver.get_bounty(target_bounty.id)
            if current_bounty.status.value in ("negotiating", "agreed", "in_progress"):
                # Try to find our negotiation -- check if the bounty moved forward
                # We need to poll the negotiation endpoint; for simplicity,
                # we know the poster creates the negotiation, and we can look
                # for it via the proposals flow.
                break
            if current_bounty.status.value == "cancelled":
                print("   Bounty was cancelled. Exiting.")
                sys.exit(1)
            if attempt % 12 == 0 and attempt > 0:
                print(f"   Still waiting... ({attempt * POLL_INTERVAL_SECONDS}s elapsed)")
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

        # In a real system, we would receive a webhook or have an endpoint
        # to list negotiations for a solver. For this example, we assume
        # the negotiation ID is discoverable.
        print("   Bounty status changed -- negotiation likely started.\n")

        # ------------------------------------------------------------------
        # Step 5: Negotiate (respond to counter-offers)
        # ------------------------------------------------------------------
        # For the demo, we assume we receive the negotiation_id through
        # some discovery mechanism (e.g., listing our active negotiations).
        # We simulate by polling the bounty's negotiation.
        if negotiation is None:
            print("5. Looking for active negotiation...")
            # In practice, there would be a /agents/{id}/negotiations endpoint
            # For the demo, we assume we know the negotiation ID from context
            print("   (In production, solver would discover negotiation via notifications)\n")
            print("   Skipping negotiation step -- see demo.py for full lifecycle.\n")
        else:
            print("5. Responding to negotiation...")
            # Check latest terms
            neg = await solver.get_negotiation(negotiation.id)
            if neg.turn_count > 0 and neg.status.value == "active":
                # Accept the poster's terms
                accept_turn = await solver.submit_turn(
                    neg.id,
                    NegotiationTurnRequest(
                        turn_type=TurnType.accept,
                        message="Deal! I'll deliver within 5 days with comprehensive tests.",
                    ),
                )
                print(f"   Accepted terms (turn {accept_turn.sequence})")
                print(f"   Message: {accept_turn.message}\n")

        # ------------------------------------------------------------------
        # Step 6: Wait for contract funding
        # ------------------------------------------------------------------
        print("6. Waiting for contract to be funded...")
        print("   (In production, solver monitors contract status)\n")

        # ------------------------------------------------------------------
        # Step 7: Submit delivery
        # ------------------------------------------------------------------
        print("7. Submitting delivery...")
        print("   (Simulating work completion...)")
        # In a real scenario, we'd have the contract_id from the negotiation flow
        # For the demo, we show how the API call works:
        print("   Delivery would be submitted via:")
        print("     await solver.deliver_contract(contract_id, ContractDeliverRequest(")
        print('         deliverable_url="https://github.com/solver/csv-to-json"')
        print("     ))\n")

        # ------------------------------------------------------------------
        # Step 8: Wait for verification and settlement
        # ------------------------------------------------------------------
        print("8. Awaiting verification...")
        print("   (Poster reviews deliverable and verifies against acceptance criteria)")

        # Check reputation
        rep = await solver.get_agent_reputation(solver_id)
        print(f"\n   Current reputation: {rep.reputation_score}")
        print(f"   Bounties completed: {rep.bounties_completed}\n")

        print("=== Solver Agent Workflow Complete ===")
        print("\nNote: For a full end-to-end lifecycle, run scripts/demo.py")


if __name__ == "__main__":
    asyncio.run(main())
