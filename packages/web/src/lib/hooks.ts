'use client';

import { useQuery } from '@tanstack/react-query';
import {
  fetchEngagements,
  fetchEngagement,
  fetchProposals,
  fetchNegotiation,
  fetchNegotiations,
  fetchNegotiationTurns,
  fetchContract,
  fetchContracts,
  fetchAgent,
  fetchAgents,
  fetchAgentReputation,
  type EngagementFilters,
  type Engagement,
  type Proposal,
  type Negotiation,
  type NegotiationTurn,
  type Contract,
  type Agent,
  type AgentReputation,
} from './api';
import {
  mockEngagements,
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

// ── Engagements ────────────────────────────────────────────────────────────

export function useEngagements(filters?: EngagementFilters) {
  return useQuery<Engagement[]>({
    queryKey: ['engagements', filters],
    queryFn: withFallback(() => fetchEngagements(filters), mockEngagements),
  });
}

export function useEngagement(id: string) {
  return useQuery<Engagement | undefined>({
    queryKey: ['engagement', id],
    queryFn: withFallback(
      () => fetchEngagement(id),
      mockEngagements.find((b) => b.id === id)
    ),
    enabled: !!id,
  });
}

// ── Proposals ───────────────────────────────────────────────────────────

export function useProposals(engagementId: string) {
  return useQuery<Proposal[]>({
    queryKey: ['proposals', engagementId],
    queryFn: withFallback(
      () => fetchProposals(engagementId),
      mockProposals.filter((p) => p.engagement_id === engagementId)
    ),
    enabled: !!engagementId,
  });
}

// ── Negotiations ────────────────────────────────────────────────────────

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
  requester_id?: string;
  provider_id?: string;
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

// ── Contracts ───────────────────────────────────────────────────────────

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
  requester_id?: string;
  provider_id?: string;
  status?: string;
}) {
  return useQuery<Contract[]>({
    queryKey: ['contracts', params],
    queryFn: withFallback(() => fetchContracts(params), mockContracts),
  });
}

// ── Agents ──────────────────────────────────────────────────────────────

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
