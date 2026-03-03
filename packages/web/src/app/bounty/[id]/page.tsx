'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import Header from '@/components/Header';
import GlassCard from '@/components/GlassCard';
import StatusBadge from '@/components/StatusBadge';
import EthAmount from '@/components/EthAmount';
import ReputationBadge from '@/components/ReputationBadge';
import NegotiationTimeline from '@/components/NegotiationTimeline';
import ContractStatusTracker from '@/components/ContractStatusTracker';
import { useBounty, useProposals, useAgent } from '@/lib/hooks';
import {
  mockBounties,
  mockProposals,
  mockAgents,
  mockNegotiations,
  mockNegotiationTurns,
  mockContracts,
} from '@/lib/mock-data';

function shortenAddress(addr: string): string {
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

export default function BountyDetailPage() {
  const params = useParams();
  const bountyId = params.id as string;

  const { data: bounty } = useBounty(bountyId);
  const { data: proposals } = useProposals(bountyId);

  // Resolve data (with mock fallbacks)
  const resolvedBounty =
    bounty ?? mockBounties.find((b) => b.id === bountyId);
  const resolvedProposals =
    proposals?.length !== undefined
      ? proposals
      : mockProposals.filter((p) => p.bounty_id === bountyId);

  const poster = mockAgents.find((a) => a.id === resolvedBounty?.poster_id);
  const solver = resolvedBounty?.solver_id
    ? mockAgents.find((a) => a.id === resolvedBounty.solver_id)
    : null;

  // Find negotiation & contract for this bounty
  const negotiation = mockNegotiations.find(
    (n) => n.bounty_id === bountyId
  );
  const negotiationTurns = negotiation
    ? mockNegotiationTurns.filter(
        (t) => t.negotiation_id === negotiation.id
      )
    : [];
  const contract = mockContracts.find((c) => c.bounty_id === bountyId);

  if (!resolvedBounty) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="max-w-4xl mx-auto px-6 py-8">
          <GlassCard>
            <p className="text-white/40 text-center py-8">
              Bounty not found.
            </p>
            <div className="text-center">
              <Link
                href="/solver"
                className="text-accent hover:text-accent/80 text-sm transition-colors"
              >
                Back to Bounty Board
              </Link>
            </div>
          </GlassCard>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="max-w-4xl mx-auto px-6 py-8 space-y-6">
        {/* ── Back link ─────────────────────────────────────────── */}
        <Link
          href="/solver"
          className="text-white/40 hover:text-white/60 text-sm transition-colors inline-block"
        >
          &larr; Back to Bounty Board
        </Link>

        {/* ── Header ────────────────────────────────────────────── */}
        <GlassCard>
          <div className="flex items-start justify-between gap-4 mb-6">
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-white mb-2">
                {resolvedBounty.title}
              </h1>
              <div className="flex items-center gap-3 flex-wrap">
                <StatusBadge status={resolvedBounty.status} />
                <span className="text-white/30">|</span>
                <EthAmount
                  amount={resolvedBounty.reward_amount}
                  className="text-white text-lg"
                />
                <span className="text-white/30">|</span>
                <span className="text-white/40 text-sm">
                  Due{' '}
                  {new Date(resolvedBounty.deadline).toLocaleDateString(
                    undefined,
                    { month: 'long', day: 'numeric', year: 'numeric' }
                  )}
                </span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <h3 className="text-sm text-white/40 uppercase tracking-wider mb-2">
                Description
              </h3>
              <p className="text-white/70 leading-relaxed">
                {resolvedBounty.description}
              </p>
            </div>

            <div>
              <h3 className="text-sm text-white/40 uppercase tracking-wider mb-2">
                Acceptance Criteria
              </h3>
              <ul className="space-y-1.5">
                {resolvedBounty.acceptance_criteria.map((criterion, i) => (
                  <li key={i} className="flex items-start gap-2 text-white/60 text-sm">
                    <span className="text-accent mt-0.5 shrink-0">&#9679;</span>
                    <span>{criterion}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </GlassCard>

        {/* ── Poster Info ───────────────────────────────────────── */}
        {poster && (
          <GlassCard>
            <h3 className="text-sm text-white/40 uppercase tracking-wider mb-3">
              Posted By
            </h3>
            <div className="flex items-center gap-4">
              <ReputationBadge score={poster.reputation_score} size="md" />
              <div>
                <p className="text-white font-medium">{poster.name}</p>
                <p className="text-white/30 text-xs font-mono">
                  {shortenAddress(poster.wallet_address)}
                </p>
                <p className="text-white/40 text-xs mt-0.5">
                  {poster.bounties_posted} bounties posted
                </p>
              </div>
            </div>
          </GlassCard>
        )}

        {/* ── Solver Info (if assigned) ─────────────────────────── */}
        {solver && (
          <GlassCard>
            <h3 className="text-sm text-white/40 uppercase tracking-wider mb-3">
              Solver
            </h3>
            <div className="flex items-center gap-4">
              <ReputationBadge score={solver.reputation_score} size="md" />
              <div>
                <p className="text-white font-medium">{solver.name}</p>
                <p className="text-white/30 text-xs font-mono">
                  {shortenAddress(solver.wallet_address)}
                </p>
                <p className="text-white/40 text-xs mt-0.5">
                  {solver.bounties_completed} bounties completed
                </p>
              </div>
            </div>
          </GlassCard>
        )}

        {/* ── Proposals ─────────────────────────────────────────── */}
        {resolvedProposals.length > 0 && (
          <section>
            <h2 className="text-lg font-semibold text-white/80 mb-4">
              Proposals ({resolvedProposals.length})
            </h2>
            <div className="space-y-3">
              {resolvedProposals.map((proposal) => {
                const proposalSolver = mockAgents.find(
                  (a) => a.id === proposal.solver_id
                );
                return (
                  <GlassCard key={proposal.id}>
                    <div className="flex items-center justify-between gap-4 mb-3">
                      <div className="flex items-center gap-3">
                        {proposalSolver && (
                          <ReputationBadge
                            score={proposalSolver.reputation_score}
                            size="sm"
                          />
                        )}
                        <div>
                          <p className="text-white font-medium text-sm">
                            {proposalSolver?.name ?? 'Unknown'}
                          </p>
                          <p className="text-white/40 text-xs">
                            Proposed{' '}
                            <EthAmount amount={proposal.proposed_price} />{' '}
                            &middot; Due{' '}
                            {new Date(
                              proposal.proposed_deadline
                            ).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <StatusBadge status={proposal.status} />
                    </div>
                    <p className="text-white/50 text-sm leading-relaxed">
                      {proposal.approach_summary}
                    </p>
                  </GlassCard>
                );
              })}
            </div>
          </section>
        )}

        {/* ── Negotiation Timeline ──────────────────────────────── */}
        {negotiation && negotiationTurns.length > 0 && (
          <section>
            <h2 className="text-lg font-semibold text-white/80 mb-4">
              Negotiation
            </h2>
            <GlassCard>
              <div className="flex items-center gap-3 mb-4">
                <StatusBadge status={negotiation.status} />
                <span className="text-white/40 text-sm">
                  {negotiation.turn_count} turns
                </span>
              </div>
              <NegotiationTimeline turns={negotiationTurns} />
            </GlassCard>
          </section>
        )}

        {/* ── Contract Status ───────────────────────────────────── */}
        {contract && (
          <section>
            <h2 className="text-lg font-semibold text-white/80 mb-4">
              Contract
            </h2>
            <GlassCard>
              <div className="flex items-center justify-between gap-4 mb-6">
                <div>
                  <p className="text-white/40 text-sm">Contract Amount</p>
                  <EthAmount
                    amount={contract.amount}
                    className="text-xl text-white"
                  />
                </div>
                <StatusBadge status={contract.status} />
              </div>

              <ContractStatusTracker status={contract.status} />

              {/* Escrow info */}
              <div className="mt-6 pt-4 border-t border-white/5 space-y-2">
                {contract.escrow_contract_address && (
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-white/40">Escrow:</span>
                    <a
                      href={`https://etherscan.io/address/${contract.escrow_contract_address}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-accent hover:text-accent/80 font-mono text-xs transition-colors"
                    >
                      {shortenAddress(contract.escrow_contract_address)}
                    </a>
                  </div>
                )}
                {contract.funding_tx_hash && (
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-white/40">Funding Tx:</span>
                    <a
                      href={`https://etherscan.io/tx/${contract.funding_tx_hash}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-accent hover:text-accent/80 font-mono text-xs transition-colors"
                    >
                      {shortenAddress(contract.funding_tx_hash)}
                    </a>
                  </div>
                )}
                {contract.release_tx_hash && (
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-white/40">Release Tx:</span>
                    <a
                      href={`https://etherscan.io/tx/${contract.release_tx_hash}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-accent hover:text-accent/80 font-mono text-xs transition-colors"
                    >
                      {shortenAddress(contract.release_tx_hash)}
                    </a>
                  </div>
                )}
              </div>
            </GlassCard>
          </section>
        )}

        {/* ── Deliverable ───────────────────────────────────────── */}
        {resolvedBounty.deliverable_url && (
          <GlassCard>
            <h3 className="text-sm text-white/40 uppercase tracking-wider mb-2">
              Deliverable
            </h3>
            <a
              href={resolvedBounty.deliverable_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:text-accent/80 transition-colors underline underline-offset-2 text-sm"
            >
              {resolvedBounty.deliverable_url}
            </a>
          </GlassCard>
        )}
      </main>
    </div>
  );
}
