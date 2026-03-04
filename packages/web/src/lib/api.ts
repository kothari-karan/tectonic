const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ── Types matching API schemas ──────────────────────────────────────────────

export interface Agent {
  id: string;
  name: string;
  agent_type: string;
  wallet_address: string;
  capabilities: string[];
  reputation_score: number;
  engagements_posted: number;
  engagements_completed: number;
}

export interface Engagement {
  id: string;
  title: string;
  description: string;
  acceptance_criteria: string[];
  category: string;
  reward_amount: number;
  reward_token: string;
  requester_id: string;
  provider_id: string | null;
  status: string;
  deadline: string;
  escrow_address: string | null;
  deliverable_url: string | null;
  created_at: string;
}

export interface Proposal {
  id: string;
  engagement_id: string;
  provider_id: string;
  status: string;
  proposed_price: number;
  proposed_deadline: string;
  approach_summary: string;
  created_at: string;
}

export interface Negotiation {
  id: string;
  engagement_id: string;
  requester_id: string;
  provider_id: string;
  status: string;
  current_terms: Record<string, unknown>;
  turn_count: number;
  created_at: string;
}

export interface NegotiationTurn {
  id: string;
  negotiation_id: string;
  agent_id: string;
  agent_name?: string;
  sequence: number;
  turn_type: string;
  proposed_terms: Record<string, unknown> | null;
  message: string | null;
  created_at: string;
}

export interface Contract {
  id: string;
  engagement_id: string;
  requester_id: string;
  provider_id: string;
  status: string;
  agreed_terms: Record<string, unknown>;
  amount: number;
  escrow_contract_address: string | null;
  funding_tx_hash: string | null;
  release_tx_hash: string | null;
  created_at: string;
}

export interface ReputationEvent {
  id: string;
  agent_id: string;
  event_type: string;
  score_change: number;
  description: string;
  created_at: string;
}

export interface AgentReputation {
  agent_id: string;
  score: number;
  events: ReputationEvent[];
}

// ── Fetch helpers ───────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  });

  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }

  return res.json() as Promise<T>;
}

// ── API functions ───────────────────────────────────────────────────────────

export interface EngagementFilters {
  status?: string;
  category?: string;
  requester_id?: string;
  provider_id?: string;
  min_reward?: number;
  max_reward?: number;
}

export async function fetchEngagements(params?: EngagementFilters): Promise<Engagement[]> {
  const searchParams = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.set(key, String(value));
      }
    });
  }
  const query = searchParams.toString();
  return apiFetch<Engagement[]>(`/engagements${query ? `?${query}` : ''}`);
}

export async function fetchEngagement(id: string): Promise<Engagement> {
  return apiFetch<Engagement>(`/engagements/${id}`);
}

export async function createEngagement(engagement: {
  title: string;
  description: string;
  acceptance_criteria: string[];
  category: string;
  reward_amount: number;
  reward_token?: string;
  requester_id: string;
  deadline: string;
}): Promise<Engagement> {
  return apiFetch<Engagement>('/engagements', {
    method: 'POST',
    body: JSON.stringify(engagement),
  });
}

export async function fetchProposals(engagementId: string): Promise<Proposal[]> {
  return apiFetch<Proposal[]>(`/engagements/${engagementId}/proposals`);
}

export async function createProposal(proposal: {
  engagement_id: string;
  provider_id: string;
  proposed_price: number;
  proposed_deadline: string;
  approach_summary: string;
}): Promise<Proposal> {
  return apiFetch<Proposal>(`/engagements/${proposal.engagement_id}/proposals`, {
    method: 'POST',
    body: JSON.stringify(proposal),
  });
}

export async function fetchNegotiation(id: string): Promise<Negotiation> {
  return apiFetch<Negotiation>(`/negotiations/${id}`);
}

export async function fetchNegotiations(params?: {
  requester_id?: string;
  provider_id?: string;
  status?: string;
}): Promise<Negotiation[]> {
  const searchParams = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.set(key, String(value));
      }
    });
  }
  const query = searchParams.toString();
  return apiFetch<Negotiation[]>(`/negotiations${query ? `?${query}` : ''}`);
}

export async function fetchNegotiationTurns(
  negotiationId: string
): Promise<NegotiationTurn[]> {
  return apiFetch<NegotiationTurn[]>(`/negotiations/${negotiationId}/turns`);
}

export async function fetchContract(id: string): Promise<Contract> {
  return apiFetch<Contract>(`/contracts/${id}`);
}

export async function fetchContracts(params?: {
  requester_id?: string;
  provider_id?: string;
  status?: string;
}): Promise<Contract[]> {
  const searchParams = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.set(key, String(value));
      }
    });
  }
  const query = searchParams.toString();
  return apiFetch<Contract[]>(`/contracts${query ? `?${query}` : ''}`);
}

export async function fetchAgent(id: string): Promise<Agent> {
  return apiFetch<Agent>(`/agents/${id}`);
}

export async function fetchAgents(): Promise<Agent[]> {
  return apiFetch<Agent[]>('/agents');
}

export async function fetchAgentReputation(
  agentId: string
): Promise<AgentReputation> {
  return apiFetch<AgentReputation>(`/agents/${agentId}/reputation`);
}
