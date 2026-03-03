'use client';

import { useState } from 'react';
import Header from '@/components/Header';
import GlassCard from '@/components/GlassCard';
import BountyCard from '@/components/BountyCard';
import StatusBadge from '@/components/StatusBadge';
import EthAmount from '@/components/EthAmount';
import ContractStatusTracker from '@/components/ContractStatusTracker';
import NegotiationTimeline from '@/components/NegotiationTimeline';
import { useBounties, useContracts, useNegotiations, useNegotiationTurns } from '@/lib/hooks';
import {
  mockBounties,
  mockContracts,
  mockNegotiations,
  mockNegotiationTurns,
  mockAgents,
  mockProposals,
} from '@/lib/mock-data';

const POSTER_ID = 'agent-poster-001';

// ── Post New Bounty Form ────────────────────────────────────────────────────

function PostBountyForm() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [criteria, setCriteria] = useState<string[]>(['']);
  const [category, setCategory] = useState('development');
  const [rewardAmount, setRewardAmount] = useState('');
  const [deadline, setDeadline] = useState('');
  const [submitted, setSubmitted] = useState(false);

  function addCriteria() {
    setCriteria([...criteria, '']);
  }

  function removeCriteria(index: number) {
    setCriteria(criteria.filter((_, i) => i !== index));
  }

  function updateCriteria(index: number, value: string) {
    const updated = [...criteria];
    updated[index] = value;
    setCriteria(updated);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    // In a real app this would call createBounty() from api.ts
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 3000);
  }

  return (
    <GlassCard>
      <h2 className="text-xl font-bold text-white mb-6">Post New Bounty</h2>
      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm text-white/60 mb-1.5">Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-white/30 focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/30 transition-colors"
            placeholder="e.g., ERC-20 Token with Vesting Schedule"
            required
          />
        </div>

        <div>
          <label className="block text-sm text-white/60 mb-1.5">
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={4}
            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-white/30 focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/30 transition-colors resize-none"
            placeholder="Describe the work you need done..."
            required
          />
        </div>

        <div>
          <label className="block text-sm text-white/60 mb-1.5">
            Acceptance Criteria
          </label>
          <div className="space-y-2">
            {criteria.map((item, i) => (
              <div key={i} className="flex gap-2">
                <input
                  type="text"
                  value={item}
                  onChange={(e) => updateCriteria(i, e.target.value)}
                  className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-white text-sm placeholder-white/30 focus:outline-none focus:border-accent/50 transition-colors"
                  placeholder={`Criterion ${i + 1}`}
                />
                {criteria.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeCriteria(i)}
                    className="px-3 py-2 text-red-400/60 hover:text-red-400 hover:bg-red-500/10 rounded-xl transition-colors text-sm"
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              onClick={addCriteria}
              className="text-sm text-accent/70 hover:text-accent transition-colors"
            >
              + Add criterion
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-white/60 mb-1.5">
              Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-accent/50 transition-colors appearance-none"
            >
              <option value="development">Development</option>
              <option value="design">Design</option>
              <option value="data">Data</option>
              <option value="writing">Writing</option>
              <option value="legal">Legal</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-white/60 mb-1.5">
              Reward Amount
            </label>
            <div className="relative">
              <input
                type="number"
                step="0.01"
                min="0"
                value={rewardAmount}
                onChange={(e) => setRewardAmount(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-white/30 focus:outline-none focus:border-accent/50 transition-colors pr-14"
                placeholder="0.00"
                required
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-white/40 text-sm">
                ETH
              </span>
            </div>
          </div>

          <div>
            <label className="block text-sm text-white/60 mb-1.5">
              Deadline
            </label>
            <input
              type="date"
              value={deadline}
              onChange={(e) => setDeadline(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-accent/50 transition-colors"
              required
            />
          </div>
        </div>

        <button
          type="submit"
          className="w-full bg-accent hover:bg-accent/80 text-white font-semibold py-3 rounded-xl transition-all duration-300 shadow-[0_0_20px_rgba(59,130,246,0.3)] hover:shadow-[0_0_30px_rgba(59,130,246,0.5)]"
        >
          {submitted ? 'Bounty Posted!' : 'Post Bounty'}
        </button>
      </form>
    </GlassCard>
  );
}

// ── Negotiation list item ───────────────────────────────────────────────────

function NegotiationItem({ negotiation }: { negotiation: typeof mockNegotiations[0] }) {
  const [expanded, setExpanded] = useState(false);
  const bounty = mockBounties.find((b) => b.id === negotiation.bounty_id);
  const solver = mockAgents.find((a) => a.id === negotiation.solver_id);
  const turns = mockNegotiationTurns.filter(
    (t) => t.negotiation_id === negotiation.id
  );

  return (
    <GlassCard className="cursor-pointer" onClick={() => setExpanded(!expanded)}>
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h4 className="text-white font-medium truncate">
            {bounty?.title ?? negotiation.bounty_id}
          </h4>
          <p className="text-white/40 text-sm mt-0.5">
            with {solver?.name ?? 'Unknown'} &middot; {negotiation.turn_count}{' '}
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

export default function PosterDashboard() {
  const { data: bounties } = useBounties({ poster_id: POSTER_ID });
  const { data: contracts } = useContracts({ poster_id: POSTER_ID });
  const { data: negotiations } = useNegotiations({ poster_id: POSTER_ID });

  const posterBounties = bounties?.length
    ? bounties.filter((b) => b.poster_id === POSTER_ID)
    : mockBounties.filter((b) => b.poster_id === POSTER_ID);

  const posterContracts = contracts?.length
    ? contracts.filter((c) => c.poster_id === POSTER_ID)
    : mockContracts.filter((c) => c.poster_id === POSTER_ID);

  const posterNegotiations = negotiations?.length
    ? negotiations.filter((n) => n.poster_id === POSTER_ID)
    : mockNegotiations.filter((n) => n.poster_id === POSTER_ID);

  const totalEscrowed = posterContracts
    .filter((c) => c.status !== 'settled' && c.status !== 'cancelled')
    .reduce((sum, c) => sum + c.amount, 0);

  const totalPaid = posterContracts
    .filter((c) => c.status === 'settled')
    .reduce((sum, c) => sum + c.amount, 0);

  const activeBountyCount = posterBounties.filter(
    (b) => b.status !== 'settled' && b.status !== 'cancelled'
  ).length;

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-10">
        {/* ── Spending Overview ──────────────────────────────────── */}
        <section>
          <h2 className="text-lg font-semibold text-white/80 mb-4">
            Spending Overview
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <GlassCard>
              <p className="text-white/40 text-sm mb-1">Total Escrowed</p>
              <EthAmount amount={totalEscrowed} className="text-2xl text-accent" />
            </GlassCard>
            <GlassCard>
              <p className="text-white/40 text-sm mb-1">Total Paid</p>
              <EthAmount amount={totalPaid} className="text-2xl text-green-400" />
            </GlassCard>
            <GlassCard>
              <p className="text-white/40 text-sm mb-1">Active Bounties</p>
              <p className="text-2xl font-bold text-white">{activeBountyCount}</p>
            </GlassCard>
          </div>
        </section>

        {/* ── My Bounties ───────────────────────────────────────── */}
        <section>
          <h2 className="text-lg font-semibold text-white/80 mb-4">
            My Bounties
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {posterBounties.map((bounty) => {
              const proposals = mockProposals.filter(
                (p) => p.bounty_id === bounty.id
              );
              return (
                <BountyCard
                  key={bounty.id}
                  bounty={bounty}
                  proposalCount={proposals.length}
                />
              );
            })}
          </div>
        </section>

        {/* ── Post New Bounty ───────────────────────────────────── */}
        <section>
          <PostBountyForm />
        </section>

        {/* ── Active Negotiations ───────────────────────────────── */}
        <section>
          <h2 className="text-lg font-semibold text-white/80 mb-4">
            Active Negotiations
          </h2>
          {posterNegotiations.length === 0 ? (
            <GlassCard>
              <p className="text-white/40 text-center py-4">
                No active negotiations.
              </p>
            </GlassCard>
          ) : (
            <div className="space-y-4">
              {posterNegotiations.map((n) => (
                <NegotiationItem key={n.id} negotiation={n} />
              ))}
            </div>
          )}
        </section>

        {/* ── My Contracts ──────────────────────────────────────── */}
        <section>
          <h2 className="text-lg font-semibold text-white/80 mb-4">
            My Contracts
          </h2>
          {posterContracts.length === 0 ? (
            <GlassCard>
              <p className="text-white/40 text-center py-4">No contracts yet.</p>
            </GlassCard>
          ) : (
            <div className="space-y-4">
              {posterContracts.map((contract) => {
                const bounty = mockBounties.find(
                  (b) => b.id === contract.bounty_id
                );
                const solver = mockAgents.find(
                  (a) => a.id === contract.solver_id
                );
                return (
                  <GlassCard key={contract.id}>
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h4 className="text-white font-medium">
                          {bounty?.title ?? contract.bounty_id}
                        </h4>
                        <p className="text-white/40 text-sm mt-0.5">
                          Solver: {solver?.name ?? 'Unknown'} &middot;{' '}
                          <EthAmount amount={contract.amount} />
                        </p>
                      </div>
                      <div className="flex gap-2">
                        {contract.status === 'pending' && (
                          <button className="px-4 py-1.5 rounded-xl bg-accent/20 text-accent text-sm font-medium hover:bg-accent/30 transition-colors">
                            Fund
                          </button>
                        )}
                        {contract.status === 'delivered' && (
                          <button className="px-4 py-1.5 rounded-xl bg-green-500/20 text-green-400 text-sm font-medium hover:bg-green-500/30 transition-colors">
                            Verify
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
