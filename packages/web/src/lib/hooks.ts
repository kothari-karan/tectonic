'use client';

import { useQuery } from '@tanstack/react-query';
import {
  fetchBounties,
  fetchBounty,
  fetchProposals,
  fetchNegotiation,
  fetchNegotiations,
  fetchNegotiationTurns,
  fetchContract,
  fetchContracts,
  fetchAgent,
  fetchAgents,
  fetchAgentReputation,
  type BountyFilters,
  type Bounty,
  type Proposal,
  type Negotiation,
  type NegotiationTurn,
  type Contract,
  type Agent,
  type AgentReputation,
} from './api';
import {
  mockBounties,
  mockProposals,
  mockNegotiations,
  mockNegotiationTurns,
  mockContracts,
  mockAgents,
  mockReputationEvents,
} from './mock-data';

// ── Helper: gracefully fall back to mock data when the API is unavailable ──

function withFallback<T>(fetcher: () => Promise<T>, fallback: T) {
  return async (): Promise<T> => {
    try {
      return await fetcher();
    } catch {
      return fallback;
    }
  };
}

// ── Bounties ────────────────────────────────────────────────────────────────

export function useBounties(filters?: BountyFilters) {
  return useQuery<Bounty[]>({
    queryKey: ['bounties', filters],
    queryFn: withFallback(() => fetchBounties(filters), mockBounties),
  });
}

export function useBounty(id: string) {
  return useQuery<Bounty | undefined>({
    queryKey: ['bounty', id],
    queryFn: withFallback(
      () => fetchBounty(id),
      mockBounties.find((b) => b.id === id)
    ),
    enabled: !!id,
  });
}

// ── Proposals ───────────────────────────────────────────────────────────────

export function useProposals(bountyId: string) {
  return useQuery<Proposal[]>({
    queryKey: ['proposals', bountyId],
    queryFn: withFallback(
      () => fetchProposals(bountyId),
      mockProposals.filter((p) => p.bounty_id === bountyId)
    ),
    enabled: !!bountyId,
  });
}

// ── Negotiations ────────────────────────────────────────────────────────────

export function useNegotiation(id: string) {
  return useQuery<Negotiation | undefined>({
    queryKey: ['negotiation', id],
    queryFn: withFallback(
      () => fetchNegotiation(id),
      mockNegotiations.find((n) => n.id === id)
    ),
    enabled: !!id,
  });
}

export function useNegotiations(params?: {
  poster_id?: string;
  solver_id?: string;
  status?: string;
}) {
  return useQuery<Negotiation[]>({
    queryKey: ['negotiations', params],
    queryFn: withFallback(() => fetchNegotiations(params), mockNegotiations),
  });
}

export function useNegotiationTurns(negotiationId: string) {
  return useQuery<NegotiationTurn[]>({
    queryKey: ['negotiation-turns', negotiationId],
    queryFn: withFallback(
      () => fetchNegotiationTurns(negotiationId),
      mockNegotiationTurns.filter((t) => t.negotiation_id === negotiationId)
    ),
    enabled: !!negotiationId,
  });
}

// ── Contracts ───────────────────────────────────────────────────────────────

export function useContract(id: string) {
  return useQuery<Contract | undefined>({
    queryKey: ['contract', id],
    queryFn: withFallback(
      () => fetchContract(id),
      mockContracts.find((c) => c.id === id)
    ),
    enabled: !!id,
  });
}

export function useContracts(params?: {
  poster_id?: string;
  solver_id?: string;
  status?: string;
}) {
  return useQuery<Contract[]>({
    queryKey: ['contracts', params],
    queryFn: withFallback(() => fetchContracts(params), mockContracts),
  });
}

// ── Agents ──────────────────────────────────────────────────────────────────

export function useAgent(id: string) {
  return useQuery<Agent | undefined>({
    queryKey: ['agent', id],
    queryFn: withFallback(
      () => fetchAgent(id),
      mockAgents.find((a) => a.id === id)
    ),
    enabled: !!id,
  });
}

export function useAgents() {
  return useQuery<Agent[]>({
    queryKey: ['agents'],
    queryFn: withFallback(() => fetchAgents(), mockAgents),
  });
}

export function useAgentReputation(agentId: string) {
  return useQuery<AgentReputation | undefined>({
    queryKey: ['agent-reputation', agentId],
    queryFn: withFallback(() => fetchAgentReputation(agentId), {
      agent_id: agentId,
      score: mockAgents.find((a) => a.id === agentId)?.reputation_score ?? 0,
      events: mockReputationEvents.filter((e) => e.agent_id === agentId),
    }),
    enabled: !!agentId,
  });
}
