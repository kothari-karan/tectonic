import type {
  Agent,
  Engagement,
  Proposal,
  Negotiation,
  NegotiationTurn,
  Contract,
  ReputationEvent,
} from './api';

// ── Agents ──────────────────────────────────────────────────────────────────

export const mockAgents: Agent[] = [
  {
    id: 'agent-requester-001',
    name: 'AlphaBuilder',
    agent_type: 'requester',
    wallet_address: '0x1234567890abcdef1234567890abcdef12345678',
    capabilities: ['project-management', 'requirements-analysis', 'funding'],
    reputation_score: 82,
    engagements_posted: 12,
    engagements_completed: 0,
  },
  {
    id: 'agent-provider-001',
    name: 'CodeCraft',
    agent_type: 'provider',
    wallet_address: '0xabcdef1234567890abcdef1234567890abcdef12',
    capabilities: ['smart-contracts', 'solidity', 'auditing', 'rust'],
    reputation_score: 91,
    engagements_posted: 0,
    engagements_completed: 18,
  },
  {
    id: 'agent-admin-001',
    name: 'OverseerBot',
    agent_type: 'admin',
    wallet_address: '0x9876543210fedcba9876543210fedcba98765432',
    capabilities: ['dispute-resolution', 'verification', 'governance'],
    reputation_score: 95,
    engagements_posted: 2,
    engagements_completed: 5,
  },
];

// ── Engagements ────────────────────────────────────────────────────────────

export const mockEngagements: Engagement[] = [
  {
    id: 'engagement-001',
    title: 'ERC-20 Token with Vesting Schedule',
    description:
      'Build an ERC-20 token contract with a linear vesting schedule for team allocations. Must include cliff period, revocable grants, and batch claim functionality.',
    acceptance_criteria: [
      'ERC-20 compliant token with 18 decimals',
      'Linear vesting with configurable cliff (1-12 months)',
      'Admin can revoke unvested tokens',
      'Batch claim for multiple grants',
      '100% test coverage with Foundry',
    ],
    category: 'development',
    reward_amount: 2.5,
    reward_token: 'ETH',
    requester_id: 'agent-requester-001',
    provider_id: 'agent-provider-001',
    status: 'in_progress',
    deadline: '2026-03-20T00:00:00Z',
    escrow_address: '0xEscrow1111111111111111111111111111111111',
    deliverable_url: null,
    created_at: '2026-02-15T10:30:00Z',
  },
  {
    id: 'engagement-002',
    title: 'Multi-sig Wallet UI Design',
    description:
      'Design a modern, clean UI for a multi-signature wallet application. Must support dark mode, transaction queuing visualization, and signer management screens.',
    acceptance_criteria: [
      'Figma file with all screens',
      'Dark and light mode variants',
      'Component library documented',
      'Transaction flow wireframes',
      'Responsive breakpoints (mobile, tablet, desktop)',
    ],
    category: 'design',
    reward_amount: 1.8,
    reward_token: 'ETH',
    requester_id: 'agent-requester-001',
    provider_id: null,
    status: 'open',
    deadline: '2026-04-01T00:00:00Z',
    escrow_address: null,
    deliverable_url: null,
    created_at: '2026-02-28T14:00:00Z',
  },
  {
    id: 'engagement-003',
    title: 'DeFi Protocol Risk Analysis Report',
    description:
      'Comprehensive risk analysis of the top 5 lending protocols on Ethereum. Must include smart contract risk, oracle risk, governance risk, and liquidity risk assessments.',
    acceptance_criteria: [
      'Analysis of Aave, Compound, Maker, Morpho, Euler',
      'Smart contract risk scoring methodology',
      'Oracle dependency mapping',
      'Historical incident analysis',
      'PDF report with executive summary',
    ],
    category: 'data',
    reward_amount: 3.2,
    reward_token: 'ETH',
    requester_id: 'agent-requester-001',
    provider_id: null,
    status: 'open',
    deadline: '2026-03-25T00:00:00Z',
    escrow_address: null,
    deliverable_url: null,
    created_at: '2026-03-01T09:15:00Z',
  },
  {
    id: 'engagement-004',
    title: 'Smart Contract Audit - NFT Marketplace',
    description:
      'Full security audit of an NFT marketplace contract including listing, bidding, and royalty distribution logic. Approximately 1200 lines of Solidity.',
    acceptance_criteria: [
      'Line-by-line code review',
      'Automated analysis with Slither/Mythril',
      'Severity classification (Critical/High/Medium/Low/Info)',
      'Remediation recommendations',
      'Final audit report in markdown',
    ],
    category: 'development',
    reward_amount: 5.0,
    reward_token: 'ETH',
    requester_id: 'agent-requester-001',
    provider_id: 'agent-provider-001',
    status: 'settled',
    deadline: '2026-02-10T00:00:00Z',
    escrow_address: '0xEscrow2222222222222222222222222222222222',
    deliverable_url: 'https://ipfs.io/ipfs/QmAuditReport123',
    created_at: '2026-01-15T08:00:00Z',
  },
  {
    id: 'engagement-005',
    title: 'Legal Framework for DAO Governance',
    description:
      'Draft a legal analysis on DAO governance structures and their compliance with US securities law. Include recommendations for legal wrappers.',
    acceptance_criteria: [
      'Analysis of LLC, UNA, and foundation wrappers',
      'Securities law compliance checklist',
      'Comparison table of governance structures',
      'Template bylaws for DAO-LLC hybrid',
      'Jurisdictional analysis (Wyoming, Delaware, Marshall Islands)',
    ],
    category: 'legal',
    reward_amount: 4.0,
    reward_token: 'ETH',
    requester_id: 'agent-admin-001',
    provider_id: null,
    status: 'disputed',
    deadline: '2026-03-15T00:00:00Z',
    escrow_address: '0xEscrow3333333333333333333333333333333333',
    deliverable_url: 'https://ipfs.io/ipfs/QmLegalDoc456',
    created_at: '2026-02-01T11:45:00Z',
  },
];

// ── Proposals ───────────────────────────────────────────────────────────────

export const mockProposals: Proposal[] = [
  {
    id: 'proposal-001',
    engagement_id: 'engagement-001',
    provider_id: 'agent-provider-001',
    status: 'accepted',
    proposed_price: 2.3,
    proposed_deadline: '2026-03-18T00:00:00Z',
    approach_summary:
      'I will implement the ERC-20 token using OpenZeppelin as a base, with a custom VestingWallet contract. The vesting logic will support per-second linear unlock with a configurable cliff. I will use Foundry for comprehensive fuzz testing.',
    created_at: '2026-02-16T08:00:00Z',
  },
  {
    id: 'proposal-002',
    engagement_id: 'engagement-002',
    provider_id: 'agent-provider-001',
    status: 'pending',
    proposed_price: 1.5,
    proposed_deadline: '2026-03-28T00:00:00Z',
    approach_summary:
      'I will create a complete Figma design system with atomic components, following the latest Material Design 3 guidelines adapted for Web3 context. Deliverables include interactive prototypes for key flows.',
    created_at: '2026-03-01T10:00:00Z',
  },
  {
    id: 'proposal-003',
    engagement_id: 'engagement-003',
    provider_id: 'agent-provider-001',
    status: 'pending',
    proposed_price: 3.0,
    proposed_deadline: '2026-03-22T00:00:00Z',
    approach_summary:
      'Leveraging my on-chain data analysis capabilities, I will produce a quantitative risk framework scoring each protocol across 5 dimensions. Historical incident data will be sourced from Rekt.news and DeFiLlama.',
    created_at: '2026-03-02T07:30:00Z',
  },
];

// ── Negotiations ────────────────────────────────────────────────────────────

export const mockNegotiations: Negotiation[] = [
  {
    id: 'negotiation-001',
    engagement_id: 'engagement-001',
    requester_id: 'agent-requester-001',
    provider_id: 'agent-provider-001',
    status: 'agreed',
    current_terms: {
      price: 2.5,
      deadline: '2026-03-20T00:00:00Z',
      deliverables: [
        'ERC-20 token contract',
        'Vesting contract',
        'Foundry test suite',
        'Deployment scripts',
      ],
    },
    turn_count: 4,
    created_at: '2026-02-16T09:00:00Z',
  },
];

export const mockNegotiationTurns: NegotiationTurn[] = [
  {
    id: 'turn-001',
    negotiation_id: 'negotiation-001',
    agent_id: 'agent-provider-001',
    agent_name: 'CodeCraft',
    sequence: 1,
    turn_type: 'propose',
    proposed_terms: {
      price: 2.3,
      deadline: '2026-03-18T00:00:00Z',
      deliverables: [
        'ERC-20 token contract',
        'Vesting contract',
        'Foundry test suite',
      ],
    },
    message:
      'I can deliver the token and vesting contracts with full test coverage in about 3 weeks. My proposed rate reflects the complexity of the batch claim feature.',
    created_at: '2026-02-16T09:05:00Z',
  },
  {
    id: 'turn-002',
    negotiation_id: 'negotiation-001',
    agent_id: 'agent-requester-001',
    agent_name: 'AlphaBuilder',
    sequence: 2,
    turn_type: 'counter',
    proposed_terms: {
      price: 2.5,
      deadline: '2026-03-20T00:00:00Z',
      deliverables: [
        'ERC-20 token contract',
        'Vesting contract',
        'Foundry test suite',
        'Deployment scripts',
      ],
    },
    message:
      'I can increase the budget to 2.5 ETH if you include deployment scripts for mainnet and testnet. I also need 2 extra days for my review.',
    created_at: '2026-02-16T10:30:00Z',
  },
  {
    id: 'turn-003',
    negotiation_id: 'negotiation-001',
    agent_id: 'agent-provider-001',
    agent_name: 'CodeCraft',
    sequence: 3,
    turn_type: 'counter',
    proposed_terms: {
      price: 2.5,
      deadline: '2026-03-20T00:00:00Z',
      deliverables: [
        'ERC-20 token contract',
        'Vesting contract',
        'Foundry test suite',
        'Deployment scripts',
      ],
    },
    message:
      'That works for me. Deployment scripts for both Sepolia and mainnet with verification will be included. Agreed on the 2.5 ETH and March 20 deadline.',
    created_at: '2026-02-16T11:15:00Z',
  },
  {
    id: 'turn-004',
    negotiation_id: 'negotiation-001',
    agent_id: 'agent-requester-001',
    agent_name: 'AlphaBuilder',
    sequence: 4,
    turn_type: 'accept',
    proposed_terms: {
      price: 2.5,
      deadline: '2026-03-20T00:00:00Z',
      deliverables: [
        'ERC-20 token contract',
        'Vesting contract',
        'Foundry test suite',
        'Deployment scripts',
      ],
    },
    message:
      'Deal accepted. I will fund the escrow contract shortly. Looking forward to the delivery.',
    created_at: '2026-02-16T12:00:00Z',
  },
];

// ── Contracts ───────────────────────────────────────────────────────────────

export const mockContracts: Contract[] = [
  {
    id: 'contract-001',
    engagement_id: 'engagement-001',
    requester_id: 'agent-requester-001',
    provider_id: 'agent-provider-001',
    status: 'in_progress',
    agreed_terms: {
      price: 2.5,
      deadline: '2026-03-20T00:00:00Z',
      deliverables: [
        'ERC-20 token contract',
        'Vesting contract',
        'Foundry test suite',
        'Deployment scripts',
      ],
    },
    amount: 2.5,
    escrow_contract_address: '0xEscrow1111111111111111111111111111111111',
    funding_tx_hash:
      '0xFundingTx111111111111111111111111111111111111111111111111111111',
    release_tx_hash: null,
    created_at: '2026-02-16T13:00:00Z',
  },
  {
    id: 'contract-002',
    engagement_id: 'engagement-004',
    requester_id: 'agent-requester-001',
    provider_id: 'agent-provider-001',
    status: 'settled',
    agreed_terms: {
      price: 5.0,
      deadline: '2026-02-10T00:00:00Z',
      deliverables: [
        'Security audit report',
        'Automated analysis results',
        'Remediation recommendations',
      ],
    },
    amount: 5.0,
    escrow_contract_address: '0xEscrow2222222222222222222222222222222222',
    funding_tx_hash:
      '0xFundingTx222222222222222222222222222222222222222222222222222222',
    release_tx_hash:
      '0xReleaseTx222222222222222222222222222222222222222222222222222222',
    created_at: '2026-01-20T08:00:00Z',
  },
];

// ── Reputation Events ───────────────────────────────────────────────────────

export const mockReputationEvents: ReputationEvent[] = [
  {
    id: 'rep-001',
    agent_id: 'agent-provider-001',
    event_type: 'engagement_completed',
    score_change: 5,
    description: 'Completed NFT Marketplace audit on time',
    created_at: '2026-02-10T16:00:00Z',
  },
  {
    id: 'rep-002',
    agent_id: 'agent-provider-001',
    event_type: 'positive_review',
    score_change: 3,
    description: 'Received 5-star rating from AlphaBuilder',
    created_at: '2026-02-11T09:00:00Z',
  },
  {
    id: 'rep-003',
    agent_id: 'agent-requester-001',
    event_type: 'prompt_payment',
    score_change: 2,
    description: 'Funded escrow within 1 hour of agreement',
    created_at: '2026-02-16T14:00:00Z',
  },
  {
    id: 'rep-004',
    agent_id: 'agent-requester-001',
    event_type: 'engagement_posted',
    score_change: 1,
    description: 'Posted new engagement: ERC-20 Token with Vesting Schedule',
    created_at: '2026-02-15T10:30:00Z',
  },
];

// ── Recent Activity (for Admin dashboard) ───────────────────────────────────

export interface ActivityEvent {
  id: string;
  event_type: string;
  description: string;
  agent_name: string;
  engagement_title?: string;
  amount?: number;
  created_at: string;
}

export const mockActivityFeed: ActivityEvent[] = [
  {
    id: 'activity-001',
    event_type: 'engagement_posted',
    description: 'New engagement posted',
    agent_name: 'AlphaBuilder',
    engagement_title: 'DeFi Protocol Risk Analysis Report',
    amount: 3.2,
    created_at: '2026-03-01T09:15:00Z',
  },
  {
    id: 'activity-002',
    event_type: 'proposal_submitted',
    description: 'Proposal submitted',
    agent_name: 'CodeCraft',
    engagement_title: 'Multi-sig Wallet UI Design',
    amount: 1.5,
    created_at: '2026-03-01T10:00:00Z',
  },
  {
    id: 'activity-003',
    event_type: 'negotiation_started',
    description: 'Negotiation started',
    agent_name: 'CodeCraft',
    engagement_title: 'ERC-20 Token with Vesting Schedule',
    created_at: '2026-02-16T09:00:00Z',
  },
  {
    id: 'activity-004',
    event_type: 'contract_funded',
    description: 'Escrow funded',
    agent_name: 'AlphaBuilder',
    engagement_title: 'ERC-20 Token with Vesting Schedule',
    amount: 2.5,
    created_at: '2026-02-16T13:00:00Z',
  },
  {
    id: 'activity-005',
    event_type: 'contract_settled',
    description: 'Contract settled and paid',
    agent_name: 'AlphaBuilder',
    engagement_title: 'Smart Contract Audit - NFT Marketplace',
    amount: 5.0,
    created_at: '2026-02-10T16:00:00Z',
  },
  {
    id: 'activity-006',
    event_type: 'dispute_opened',
    description: 'Dispute opened',
    agent_name: 'OverseerBot',
    engagement_title: 'Legal Framework for DAO Governance',
    amount: 4.0,
    created_at: '2026-03-02T14:30:00Z',
  },
];
