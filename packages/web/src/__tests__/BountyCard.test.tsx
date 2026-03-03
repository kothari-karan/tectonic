import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import BountyCard from '@/components/BountyCard';

// Mock next/link to render a plain anchor
vi.mock('next/link', () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

import { vi } from 'vitest';

const mockBounty = {
  id: 'bounty-test',
  title: 'Test Bounty Title',
  category: 'development',
  reward_amount: 2.5,
  status: 'open',
  deadline: '2030-12-31T00:00:00Z',
};

describe('BountyCard', () => {
  it('displays bounty title', () => {
    render(<BountyCard bounty={mockBounty} />);
    expect(screen.getByText('Test Bounty Title')).toBeInTheDocument();
  });

  it('displays bounty category', () => {
    render(<BountyCard bounty={mockBounty} />);
    expect(screen.getByText('development')).toBeInTheDocument();
  });

  it('displays reward amount in ETH', () => {
    render(<BountyCard bounty={mockBounty} />);
    expect(screen.getByText('2.5')).toBeInTheDocument();
    expect(screen.getByTestId('eth-amount')).toHaveTextContent('ETH');
  });

  it('displays status badge', () => {
    render(<BountyCard bounty={mockBounty} />);
    expect(screen.getByTestId('status-badge')).toHaveTextContent('open');
  });

  it('displays proposal count when provided', () => {
    render(<BountyCard bounty={mockBounty} proposalCount={3} />);
    expect(screen.getByText('3 proposals')).toBeInTheDocument();
  });

  it('displays singular proposal text for count of 1', () => {
    render(<BountyCard bounty={mockBounty} proposalCount={1} />);
    expect(screen.getByText('1 proposal')).toBeInTheDocument();
  });

  it('displays poster reputation when provided', () => {
    render(<BountyCard bounty={mockBounty} posterReputation={85} />);
    expect(screen.getByText('Rep 85')).toBeInTheDocument();
  });

  it('links to the bounty detail page', () => {
    render(<BountyCard bounty={mockBounty} />);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/bounty/bounty-test');
  });

  it('has the bounty-card test id', () => {
    render(<BountyCard bounty={mockBounty} />);
    expect(screen.getByTestId('bounty-card')).toBeInTheDocument();
  });
});
