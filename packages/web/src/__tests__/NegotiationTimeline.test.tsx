import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import NegotiationTimeline from '@/components/NegotiationTimeline';

const mockTurns = [
  {
    id: 'turn-1',
    agent_name: 'CodeCraft',
    turn_type: 'propose',
    proposed_terms: {
      price: 2.3,
      deadline: '2026-03-18T00:00:00Z',
      deliverables: ['Contract A', 'Contract B'],
    },
    message: 'Here is my proposal for the work.',
    created_at: '2026-02-16T09:05:00Z',
  },
  {
    id: 'turn-2',
    agent_name: 'AlphaBuilder',
    turn_type: 'counter',
    proposed_terms: {
      price: 2.5,
      deadline: '2026-03-20T00:00:00Z',
      deliverables: ['Contract A', 'Contract B', 'Scripts'],
    },
    message: 'Counter with higher budget.',
    created_at: '2026-02-16T10:30:00Z',
  },
  {
    id: 'turn-3',
    agent_name: 'AlphaBuilder',
    turn_type: 'accept',
    proposed_terms: null,
    message: 'Deal accepted.',
    created_at: '2026-02-16T12:00:00Z',
  },
];

describe('NegotiationTimeline', () => {
  it('renders empty state when turns is empty', () => {
    render(<NegotiationTimeline turns={[]} />);
    expect(
      screen.getByTestId('negotiation-timeline-empty')
    ).toHaveTextContent('No negotiation turns yet.');
  });

  it('renders the timeline when turns are provided', () => {
    render(<NegotiationTimeline turns={mockTurns} />);
    expect(screen.getByTestId('negotiation-timeline')).toBeInTheDocument();
  });

  it('displays agent names', () => {
    render(<NegotiationTimeline turns={mockTurns} />);
    expect(screen.getByText('CodeCraft')).toBeInTheDocument();
    expect(screen.getAllByText('AlphaBuilder')).toHaveLength(2);
  });

  it('displays turn types', () => {
    render(<NegotiationTimeline turns={mockTurns} />);
    expect(screen.getByText('propose')).toBeInTheDocument();
    expect(screen.getByText('counter')).toBeInTheDocument();
    expect(screen.getByText('accept')).toBeInTheDocument();
  });

  it('displays messages', () => {
    render(<NegotiationTimeline turns={mockTurns} />);
    expect(
      screen.getByText('Here is my proposal for the work.')
    ).toBeInTheDocument();
    expect(
      screen.getByText('Counter with higher budget.')
    ).toBeInTheDocument();
    expect(screen.getByText('Deal accepted.')).toBeInTheDocument();
  });

  it('displays proposed terms (price)', () => {
    render(<NegotiationTimeline turns={mockTurns} />);
    expect(screen.getByText('2.3 ETH')).toBeInTheDocument();
    expect(screen.getByText('2.5 ETH')).toBeInTheDocument();
  });

  it('renders "Unknown" for turns without agent_name', () => {
    const turnsWithoutName = [
      {
        id: 'turn-x',
        turn_type: 'propose',
        message: 'No name turn',
        created_at: '2026-02-16T09:05:00Z',
      },
    ];
    render(<NegotiationTimeline turns={turnsWithoutName} />);
    expect(screen.getByText('Unknown')).toBeInTheDocument();
  });

  it('handles turns without proposed_terms', () => {
    const turnsNoTerms = [
      {
        id: 'turn-y',
        agent_name: 'Agent',
        turn_type: 'accept',
        proposed_terms: null,
        message: 'Accepted.',
        created_at: '2026-02-16T12:00:00Z',
      },
    ];
    render(<NegotiationTimeline turns={turnsNoTerms} />);
    expect(screen.getByText('Accepted.')).toBeInTheDocument();
  });
});
