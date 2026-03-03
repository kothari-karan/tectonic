"""
Tectonic Protocol Demo
======================
Runs a complete bounty lifecycle end-to-end:

1. Register poster and solver agents
2. Poster posts a bounty
3. Solver discovers and submits proposal
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
    BountyCreate,
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
    print("  Tectonic Protocol Demo -- Full Bounty Lifecycle")
    print(f"{_separator('=')}\n")
    print(f"API URL: {api_url}\n")

    # =====================================================================
    # Step 1: Register both agents
    # =====================================================================
    print(f"[{_ts()}] STEP 1: Registering agents")
    print(_separator())

    async with TectonicClient(api_url) as anon_client:
        # Register poster
        poster_resp = await anon_client.register_agent(
            AgentCreate(
                name="AlicePoster",
                agent_type=AgentType.poster,
                wallet_address="0x1111111111111111111111111111111111111111",
                capabilities=["project-management", "code-review"],
            )
        )
        poster_id = poster_resp.agent.id
        poster_key = poster_resp.api_key
        print(f"  Poster registered: {poster_resp.agent.name}")
        print(f"    ID:  {poster_id}")
        print(f"    Key: {poster_key[:16]}...")

        # Register solver
        solver_resp = await anon_client.register_agent(
            AgentCreate(
                name="BobSolver",
                agent_type=AgentType.solver,
                wallet_address="0x2222222222222222222222222222222222222222",
                capabilities=["python", "cli-tools", "testing", "data-processing"],
            )
        )
        solver_id = solver_resp.agent.id
        solver_key = solver_resp.api_key
        print(f"  Solver registered: {solver_resp.agent.name}")
        print(f"    ID:  {solver_id}")
        print(f"    Key: {solver_key[:16]}...")

    # Create authenticated clients
    poster_client = TectonicClient(api_url, api_key=poster_key)
    solver_client = TectonicClient(api_url, api_key=solver_key)

    try:
        # =================================================================
        # Step 2: Poster creates a bounty
        # =================================================================
        print(f"\n[{_ts()}] STEP 2: Posting bounty")
        print(_separator())

        bounty = await poster_client.create_bounty(
            BountyCreate(
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
        print(f"  Bounty created: {bounty.title}")
        print(f"    ID:     {bounty.id}")
        print(f"    Reward: {bounty.reward_amount} {bounty.reward_token}")
        print(f"    Status: {bounty.status.value}")

        # =================================================================
        # Step 3: Solver discovers bounty and submits proposal
        # =================================================================
        print(f"\n[{_ts()}] STEP 3: Solver browsing and submitting proposal")
        print(_separator())

        # Solver browses open bounties
        bounty_list = await solver_client.list_bounties(status="open")
        print(f"  Found {bounty_list.total} open bounty(ies)")

        target = None
        for b in bounty_list.bounties:
            if b.id == bounty.id:
                target = b
                break
        if target is None:
            print("  ERROR: Could not find the posted bounty!")
            sys.exit(1)

        print(f"  Matched bounty: {target.title}")

        # Submit proposal at 80% of asking price
        proposal = await solver_client.create_proposal(
            bounty.id,
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
        print(f"    Price: {proposal.proposed_price} ETH (vs {bounty.reward_amount} asked)")
        print(f"    Status: {proposal.status.value}")

        # =================================================================
        # Step 4: Poster reviews proposals and starts negotiation
        # =================================================================
        print(f"\n[{_ts()}] STEP 4: Multi-turn negotiation")
        print(_separator())

        # Poster checks proposals
        proposals = await poster_client.list_proposals(bounty.id)
        print(f"  Poster sees {len(proposals)} proposal(s)")

        best_proposal = proposals[0]
        print(f"  Best proposal: {best_proposal.id} at {best_proposal.proposed_price} ETH")

        # Start negotiation
        negotiation = await poster_client.create_negotiation(bounty.id, best_proposal.id)
        print(f"  Negotiation started: {negotiation.id}")
        print(f"    Status: {negotiation.status.value}")

        # --  Turn 1: Poster counter-offers (full price for more features) --
        print(f"\n  Turn 1: Poster counter-offers...")
        turn1 = await poster_client.submit_turn(
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

        # -- Turn 2: Solver accepts --
        print(f"\n  Turn 2: Solver accepts...")
        turn2 = await solver_client.submit_turn(
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
        negotiation = await poster_client.get_negotiation(negotiation.id)
        print(f"\n  Negotiation status: {negotiation.status.value}")
        print(f"  Total turns: {negotiation.turn_count}")

        # =================================================================
        # Step 5: Create and fund contract
        # =================================================================
        print(f"\n[{_ts()}] STEP 5: Contract creation and funding")
        print(_separator())

        contract = await poster_client.create_contract(bounty.id, negotiation.id)
        print(f"  Contract created: {contract.id}")
        print(f"    Status: {contract.status.value}")
        print(f"    Amount: {contract.amount} ETH")
        print(f"    Terms hash: {contract.terms_hash}")

        # Fund the escrow
        contract = await poster_client.fund_contract(
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
        # Step 6: Solver delivers work
        # =================================================================
        print(f"\n[{_ts()}] STEP 6: Delivery")
        print(_separator())

        contract = await solver_client.deliver_contract(
            contract.id,
            ContractDeliverRequest(
                deliverable_url="https://github.com/bobsolver/csv-to-json-cli",
            ),
        )
        print(f"  Delivery submitted!")
        print(f"    Status: {contract.status.value}")

        # =================================================================
        # Step 7: Poster verifies and contract settles
        # =================================================================
        print(f"\n[{_ts()}] STEP 7: Verification and settlement")
        print(_separator())

        contract = await poster_client.verify_contract(
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

        poster_rep = await poster_client.get_agent_reputation(poster_id)
        solver_rep = await solver_client.get_agent_reputation(solver_id)

        print(f"  Poster ({poster_resp.agent.name}):")
        print(f"    Reputation score: {poster_rep.reputation_score}")
        print(f"    Bounties posted:  {poster_rep.bounties_posted}")

        print(f"  Solver ({solver_resp.agent.name}):")
        print(f"    Reputation score: {solver_rep.reputation_score}")
        print(f"    Bounties completed: {solver_rep.bounties_completed}")

        # =================================================================
        # Done
        # =================================================================
        print(f"\n{_separator('=')}")
        print("  Demo Complete!")
        print(f"{_separator('=')}")
        print(f"\nFull lifecycle executed:")
        print(f"  1. Registered 2 agents (poster + solver)")
        print(f"  2. Posted bounty: {bounty.title}")
        print(f"  3. Submitted proposal at {proposal.proposed_price} ETH")
        print(f"  4. Negotiated in {negotiation.turn_count} turns -> {negotiation.status.value}")
        print(f"  5. Created & funded contract ({contract.amount} ETH)")
        print(f"  6. Delivered work")
        print(f"  7. Verified delivery -> status: {contract.status.value}")
        print(f"  8. Reputation updated for both agents")
        print()

    finally:
        await poster_client.close()
        await solver_client.close()


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
