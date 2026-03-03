'use client';

import Header from '@/components/Header';
import GlassCard from '@/components/GlassCard';
import StatusBadge from '@/components/StatusBadge';
import EthAmount from '@/components/EthAmount';
import ReputationBadge from '@/components/ReputationBadge';
import { useAgents, useBounties, useContracts, useNegotiations } from '@/lib/hooks';
import {
  mockBounties,
  mockContracts,
  mockNegotiations,
  mockAgents,
  mockActivityFeed,
  type ActivityEvent,
} from '@/lib/mock-data';

// ── Activity event icon/color ───────────────────────────────────────────────

const eventTypeConfig: Record<
  string,
  { color: string; label: string }
> = {
  bounty_posted: { color: 'bg-blue-500', label: 'Bounty Posted' },
  proposal_submitted: { color: 'bg-purple-500', label: 'Proposal' },
  negotiation_started: { color: 'bg-amber-500', label: 'Negotiation' },
  contract_funded: { color: 'bg-cyan-500', label: 'Funded' },
  contract_settled: { color: 'bg-green-500', label: 'Settled' },
  dispute_opened: { color: 'bg-red-500', label: 'Dispute' },
};

function ActivityItem({ event }: { event: ActivityEvent }) {
  const config = eventTypeConfig[event.event_type] ?? {
    color: 'bg-gray-500',
    label: 'Event',
  };

  return (
    <div className="flex items-start gap-3 py-3">
      <div
        className={`w-2.5 h-2.5 rounded-full mt-1.5 shrink-0 ${config.color}`}
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-white/80 text-sm font-medium">
            {event.agent_name}
          </span>
          <span className="text-white/30 text-xs">&middot;</span>
          <span className="text-white/50 text-xs">{config.label}</span>
        </div>
        <p className="text-white/40 text-sm mt-0.5 truncate">
          {event.bounty_title}
          {event.amount !== undefined && (
            <span className="ml-2">
              <EthAmount amount={event.amount} className="text-xs" />
            </span>
          )}
        </p>
      </div>
      <span className="text-white/20 text-xs shrink-0">
        {new Date(event.created_at).toLocaleDateString(undefined, {
          month: 'short',
          day: 'numeric',
        })}
      </span>
    </div>
  );
}

// ── Main Page ───────────────────────────────────────────────────────────────

export default function AdminDashboard() {
  const { data: bounties } = useBounties();
  const { data: contracts } = useContracts();
  const { data: negotiations } = useNegotiations();
  const { data: agents } = useAgents();

  const allBounties = bounties?.length ? bounties : mockBounties;
  const allContracts = contracts?.length ? contracts : mockContracts;
  const allNegotiations = negotiations?.length ? negotiations : mockNegotiations;
  const allAgents = agents?.length ? agents : mockAgents;

  const totalBounties = allBounties.length;
  const activeNegotiations = allNegotiations.filter(
    (n) => n.status !== 'agreed' && n.status !== 'rejected'
  ).length;
  const totalVolume = allContracts.reduce((sum, c) => sum + c.amount, 0);
  const activeDisputes = allContracts.filter(
    (c) => c.status === 'disputed'
  ).length;

  const disputedContracts = allContracts.filter(
    (c) => c.status === 'disputed'
  );

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-10">
        {/* ── Platform Overview ──────────────────────────────────── */}
        <section>
          <h2 className="text-lg font-semibold text-white/80 mb-4">
            Platform Overview
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <GlassCard>
              <p className="text-white/40 text-sm mb-1">Total Bounties</p>
              <p className="text-2xl font-bold text-white">{totalBounties}</p>
            </GlassCard>
            <GlassCard>
              <p className="text-white/40 text-sm mb-1">Active Negotiations</p>
              <p className="text-2xl font-bold text-amber-400">
                {activeNegotiations}
              </p>
            </GlassCard>
            <GlassCard>
              <p className="text-white/40 text-sm mb-1">Total Volume</p>
              <EthAmount
                amount={totalVolume}
                className="text-2xl text-accent"
              />
            </GlassCard>
            <GlassCard>
              <p className="text-white/40 text-sm mb-1">Active Disputes</p>
              <p className="text-2xl font-bold text-red-400">
                {activeDisputes}
              </p>
            </GlassCard>
          </div>
        </section>

        {/* ── Disputes Queue ────────────────────────────────────── */}
        <section>
          <h2 className="text-lg font-semibold text-white/80 mb-4">
            Disputes Queue
          </h2>
          {disputedContracts.length === 0 ? (
            <GlassCard>
              <p className="text-white/40 text-center py-4">
                No active disputes. All clear.
              </p>
            </GlassCard>
          ) : (
            <div className="space-y-4">
              {disputedContracts.map((contract) => {
                const bounty = allBounties.find(
                  (b) => b.id === contract.bounty_id
                );
                const poster = allAgents.find(
                  (a) => a.id === contract.poster_id
                );
                const solver = allAgents.find(
                  (a) => a.id === contract.solver_id
                );

                return (
                  <GlassCard key={contract.id}>
                    <div className="flex items-start justify-between gap-4 mb-4">
                      <div>
                        <h4 className="text-white font-medium">
                          {bounty?.title ?? contract.bounty_id}
                        </h4>
                        <div className="flex items-center gap-4 mt-2 text-sm text-white/40">
                          <span>
                            Poster:{' '}
                            <span className="text-white/60">
                              {poster?.name ?? 'Unknown'}
                            </span>
                          </span>
                          <span>
                            Solver:{' '}
                            <span className="text-white/60">
                              {solver?.name ?? 'Unknown'}
                            </span>
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <EthAmount amount={contract.amount} className="text-white" />
                        <StatusBadge status="disputed" />
                      </div>
                    </div>

                    {bounty?.deliverable_url && (
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-white/40">Deliverable:</span>
                        <a
                          href={bounty.deliverable_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-accent hover:text-accent/80 transition-colors underline underline-offset-2"
                        >
                          {bounty.deliverable_url}
                        </a>
                      </div>
                    )}

                    <div className="flex gap-2 mt-4">
                      <button className="px-4 py-1.5 rounded-xl bg-green-500/20 text-green-400 text-sm font-medium hover:bg-green-500/30 transition-colors">
                        Resolve (Pay Solver)
                      </button>
                      <button className="px-4 py-1.5 rounded-xl bg-red-500/20 text-red-400 text-sm font-medium hover:bg-red-500/30 transition-colors">
                        Resolve (Refund Poster)
                      </button>
                    </div>
                  </GlassCard>
                );
              })}
            </div>
          )}
        </section>

        {/* ── Agent Registry ────────────────────────────────────── */}
        <section>
          <h2 className="text-lg font-semibold text-white/80 mb-4">
            Agent Registry
          </h2>
          <GlassCard className="overflow-hidden p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="text-left text-xs text-white/40 font-medium px-6 py-3 uppercase tracking-wider">
                      Agent
                    </th>
                    <th className="text-left text-xs text-white/40 font-medium px-6 py-3 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="text-center text-xs text-white/40 font-medium px-6 py-3 uppercase tracking-wider">
                      Reputation
                    </th>
                    <th className="text-center text-xs text-white/40 font-medium px-6 py-3 uppercase tracking-wider">
                      Posted
                    </th>
                    <th className="text-center text-xs text-white/40 font-medium px-6 py-3 uppercase tracking-wider">
                      Completed
                    </th>
                    <th className="text-left text-xs text-white/40 font-medium px-6 py-3 uppercase tracking-wider">
                      Capabilities
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {allAgents.map((agent) => (
                    <tr
                      key={agent.id}
                      className="hover:bg-white/5 transition-colors"
                    >
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-white font-medium text-sm">
                            {agent.name}
                          </p>
                          <p className="text-white/30 text-xs font-mono mt-0.5">
                            {agent.wallet_address.slice(0, 6)}...
                            {agent.wallet_address.slice(-4)}
                          </p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <StatusBadge status={agent.agent_type} />
                      </td>
                      <td className="px-6 py-4 text-center">
                        <div className="flex justify-center">
                          <ReputationBadge
                            score={agent.reputation_score}
                            size="sm"
                          />
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center text-white/60 text-sm">
                        {agent.bounties_posted}
                      </td>
                      <td className="px-6 py-4 text-center text-white/60 text-sm">
                        {agent.bounties_completed}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-1">
                          {agent.capabilities.slice(0, 3).map((cap) => (
                            <span
                              key={cap}
                              className="px-2 py-0.5 rounded bg-white/5 text-white/40 text-xs"
                            >
                              {cap}
                            </span>
                          ))}
                          {agent.capabilities.length > 3 && (
                            <span className="text-white/30 text-xs">
                              +{agent.capabilities.length - 3}
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>
        </section>

        {/* ── Recent Activity ───────────────────────────────────── */}
        <section>
          <h2 className="text-lg font-semibold text-white/80 mb-4">
            Recent Activity
          </h2>
          <GlassCard>
            <div className="divide-y divide-white/5">
              {mockActivityFeed.map((event) => (
                <ActivityItem key={event.id} event={event} />
              ))}
            </div>
          </GlassCard>
        </section>
      </main>
    </div>
  );
}
