'use client';

import { useState, useMemo } from 'react';
import Header from '@/components/Header';
import GlassCard from '@/components/GlassCard';
import EngagementCard from '@/components/EngagementCard';
import StatusBadge from '@/components/StatusBadge';
import EthAmount from '@/components/EthAmount';
import ContractStatusTracker from '@/components/ContractStatusTracker';
import NegotiationTimeline from '@/components/NegotiationTimeline';
import { useEngagements, useContracts, useNegotiations } from '@/lib/hooks';
import {
  mockEngagements,
  mockContracts,
  mockNegotiations,
  mockNegotiationTurns,
  mockAgents,
  mockProposals,
} from '@/lib/mock-data';

const PROVIDER_ID = 'agent-provider-001';

// ── Marketplace with Filters ───────────────────────────────────────────────

function Marketplace() {
  const { data: allEngagements } = useEngagements();
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [minReward, setMinReward] = useState('');
  const [maxReward, setMaxReward] = useState('');

  const openEngagements = useMemo(() => {
    const engagements = allEngagements?.length ? allEngagements : mockEngagements;
    return engagements
      .filter((b) => b.status === 'open')
      .filter((b) =>
        search
          ? b.title.toLowerCase().includes(search.toLowerCase()) ||
            b.description.toLowerCase().includes(search.toLowerCase())
          : true
      )
      .filter((b) => (categoryFilter ? b.category === categoryFilter : true))
      .filter((b) =>
        minReward ? b.reward_amount >= parseFloat(minReward) : true
      )
      .filter((b) =>
        maxReward ? b.reward_amount <= parseFloat(maxReward) : true
      );
  }, [allEngagements, search, categoryFilter, minReward, maxReward]);

  return (
    <section>
      <h2 className="text-lg font-semibold text-white/80 mb-4">
        Marketplace
      </h2>

      {/* Filters */}
      <GlassCard className="mb-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search engagements..."
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm placeholder-white/30 focus:outline-none focus:border-accent/50 transition-colors"
            />
          </div>
          <div>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-accent/50 transition-colors appearance-none"
            >
              <option value="">All Categories</option>
              <option value="development">Development</option>
              <option value="design">Design</option>
              <option value="data">Data</option>
              <option value="writing">Writing</option>
              <option value="legal">Legal</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <input
              type="number"
              step="0.01"
              min="0"
              value={minReward}
              onChange={(e) => setMinReward(e.target.value)}
              placeholder="Min ETH"
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm placeholder-white/30 focus:outline-none focus:border-accent/50 transition-colors"
            />
          </div>
          <div>
            <input
              type="number"
              step="0.01"
              min="0"
              value={maxReward}
              onChange={(e) => setMaxReward(e.target.value)}
              placeholder="Max ETH"
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm placeholder-white/30 focus:outline-none focus:border-accent/50 transition-colors"
            />
          </div>
        </div>
      </GlassCard>

      {openEngagements.length === 0 ? (
        <GlassCard>
          <p className="text-white/40 text-center py-4">
            No engagements match your filters.
          </p>
        </GlassCard>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {openEngagements.map((engagement) => {
            const requester = mockAgents.find((a) => a.id === engagement.requester_id);
            return (
              <EngagementCard
                key={engagement.id}
                engagement={engagement}
                requesterReputation={requester?.reputation_score}
              />
            );
          })}
        </div>
      )}
    </section>
  );
}

// ── Negotiation Item (provider perspective) ───────────────────────────────

function ProviderNegotiationItem({
  negotiation,
}: {
  negotiation: typeof mockNegotiations[0];
}) {
  const [expanded, setExpanded] = useState(false);
  const engagement = mockEngagements.find((b) => b.id === negotiation.engagement_id);
  const requester = mockAgents.find((a) => a.id === negotiation.requester_id);
  const turns = mockNegotiationTurns.filter(
    (t) => t.negotiation_id === negotiation.id
  );

  return (
    <GlassCard className="cursor-pointer" onClick={() => setExpanded(!expanded)}>
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h4 className="text-white font-medium truncate">
            {engagement?.title ?? negotiation.engagement_id}
          </h4>
          <p className="text-white/40 text-sm mt-0.5">
            with {requester?.name ?? 'Unknown'} &middot; {negotiation.turn_count}{' '}
            turns
          </p>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge status={negotiation.status} />
          {negotiation.current_terms?.price !== undefined && (
            <EthAmount
              amount={negotiation.current_terms.price as number}
              className="text-white"
            />
          )}
        </div>
      </div>
      {expanded && (
        <div className="mt-4 pt-4 border-t border-white/5">
          <NegotiationTimeline turns={turns} />
        </div>
      )}
    </GlassCard>
  );
}

// ── Main Page ───────────────────────────────────────────────────────────────

export default function ProviderDashboard() {
  const { data: contracts } = useContracts({ provider_id: PROVIDER_ID });
  const { data: negotiations } = useNegotiations({ provider_id: PROVIDER_ID });

  const providerContracts = contracts?.length
    ? contracts.filter((c) => c.provider_id === PROVIDER_ID)
    : mockContracts.filter((c) => c.provider_id === PROVIDER_ID);

  const providerNegotiations = negotiations?.length
    ? negotiations.filter((n) => n.provider_id === PROVIDER_ID)
    : mockNegotiations.filter((n) => n.provider_id === PROVIDER_ID);

  const providerProposals = mockProposals.filter(
    (p) => p.provider_id === PROVIDER_ID
  );

  const totalEarned = providerContracts
    .filter((c) => c.status === 'settled')
    .reduce((sum, c) => sum + c.amount, 0);

  const inEscrow = providerContracts
    .filter((c) => c.status !== 'settled' && c.status !== 'cancelled')
    .reduce((sum, c) => sum + c.amount, 0);

  const completedCount = providerContracts.filter(
    (c) => c.status === 'settled'
  ).length;

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-10">
        {/* ── Earnings Overview ──────────────────────────────────── */}
        <section>
          <h2 className="text-lg font-semibold text-white/80 mb-4">
            Earnings Overview
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <GlassCard>
              <p className="text-white/40 text-sm mb-1">Total Earned</p>
              <EthAmount
                amount={totalEarned}
                className="text-2xl text-green-400"
              />
            </GlassCard>
            <GlassCard>
              <p className="text-white/40 text-sm mb-1">In Escrow</p>
              <EthAmount
                amount={inEscrow}
                className="text-2xl text-accent"
              />
            </GlassCard>
            <GlassCard>
              <p className="text-white/40 text-sm mb-1">Completed Engagements</p>
              <p className="text-2xl font-bold text-white">{completedCount}</p>
            </GlassCard>
          </div>
        </section>

        {/* ── Marketplace ──────────────────────────────────────── */}
        <Marketplace />

        {/* ── My Proposals ──────────────────────────────────────── */}
        <section>
          <h2 className="text-lg font-semibold text-white/80 mb-4">
            My Proposals
          </h2>
          {providerProposals.length === 0 ? (
            <GlassCard>
              <p className="text-white/40 text-center py-4">
                No proposals submitted yet.
              </p>
            </GlassCard>
          ) : (
            <div className="space-y-3">
              {providerProposals.map((proposal) => {
                const engagement = mockEngagements.find(
                  (b) => b.id === proposal.engagement_id
                );
                return (
                  <GlassCard key={proposal.id}>
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <h4 className="text-white font-medium truncate">
                          {engagement?.title ?? proposal.engagement_id}
                        </h4>
                        <p className="text-white/40 text-sm mt-0.5">
                          Proposed{' '}
                          <EthAmount amount={proposal.proposed_price} /> &middot;{' '}
                          Deadline{' '}
                          {new Date(
                            proposal.proposed_deadline
                          ).toLocaleDateString()}
                        </p>
                      </div>
                      <StatusBadge status={proposal.status} />
                    </div>
                    <p className="text-white/50 text-sm mt-3 leading-relaxed">
                      {proposal.approach_summary}
                    </p>
                  </GlassCard>
                );
              })}
            </div>
          )}
        </section>

        {/* ── Active Negotiations ───────────────────────────────── */}
        <section>
          <h2 className="text-lg font-semibold text-white/80 mb-4">
            Active Negotiations
          </h2>
          {providerNegotiations.length === 0 ? (
            <GlassCard>
              <p className="text-white/40 text-center py-4">
                No active negotiations.
              </p>
            </GlassCard>
          ) : (
            <div className="space-y-4">
              {providerNegotiations.map((n) => (
                <ProviderNegotiationItem key={n.id} negotiation={n} />
              ))}
            </div>
          )}
        </section>

        {/* ── My Contracts ──────────────────────────────────────── */}
        <section>
          <h2 className="text-lg font-semibold text-white/80 mb-4">
            My Contracts
          </h2>
          {providerContracts.length === 0 ? (
            <GlassCard>
              <p className="text-white/40 text-center py-4">
                No contracts yet.
              </p>
            </GlassCard>
          ) : (
            <div className="space-y-4">
              {providerContracts.map((contract) => {
                const engagement = mockEngagements.find(
                  (b) => b.id === contract.engagement_id
                );
                const requester = mockAgents.find(
                  (a) => a.id === contract.requester_id
                );
                return (
                  <GlassCard key={contract.id}>
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h4 className="text-white font-medium">
                          {engagement?.title ?? contract.engagement_id}
                        </h4>
                        <p className="text-white/40 text-sm mt-0.5">
                          Requester: {requester?.name ?? 'Unknown'} &middot;{' '}
                          <EthAmount amount={contract.amount} />
                        </p>
                      </div>
                      <div className="flex gap-2">
                        {(contract.status === 'in_progress' ||
                          contract.status === 'funded') && (
                          <button className="px-4 py-1.5 rounded-xl bg-accent/20 text-accent text-sm font-medium hover:bg-accent/30 transition-colors">
                            Deliver
                          </button>
                        )}
                      </div>
                    </div>
                    <ContractStatusTracker status={contract.status} />
                  </GlassCard>
                );
              })}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
