import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import EngagementCard from '@/components/EngagementCard';

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

const mockEngagement = {
  id: 'engagement-test',
  title: 'Test Engagement Title',
  category: 'development',
  reward_amount: 2.5,
  status: 'open',
  deadline: '2030-12-31T00:00:00Z',
};

describe('EngagementCard', () => {
  it('displays engagement title', () => {
    render(<EngagementCard engagement={mockEngagement} />);
    expect(screen.getByText('Test Engagement Title')).toBeInTheDocument();
  });

  it('displays engagement category', () => {
    render(<EngagementCard engagement={mockEngagement} />);
    expect(screen.getByText('development')).toBeInTheDocument();
  });

  it('displays reward amount in ETH', () => {
    render(<EngagementCard engagement={mockEngagement} />);
    expect(screen.getByText('2.5')).toBeInTheDocument();
    expect(screen.getByTestId('eth-amount')).toHaveTextContent('ETH');
  });

  it('displays status badge', () => {
    render(<EngagementCard engagement={mockEngagement} />);
    expect(screen.getByTestId('status-badge')).toHaveTextContent('open');
  });

  it('displays proposal count when provided', () => {
    render(<EngagementCard engagement={mockEngagement} proposalCount={3} />);
    expect(screen.getByText('3 proposals')).toBeInTheDocument();
  });

  it('displays singular proposal text for count of 1', () => {
    render(<EngagementCard engagement={mockEngagement} proposalCount={1} />);
    expect(screen.getByText('1 proposal')).toBeInTheDocument();
  });

  it('displays requester reputation when provided', () => {
    render(<EngagementCard engagement={mockEngagement} requesterReputation={85} />);
    expect(screen.getByText('Rep 85')).toBeInTheDocument();
  });

  it('links to the engagement detail page', () => {
    render(<EngagementCard engagement={mockEngagement} />);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/engagement/engagement-test');
  });

  it('has the engagement-card test id', () => {
    render(<EngagementCard engagement={mockEngagement} />);
    expect(screen.getByTestId('engagement-card')).toBeInTheDocument();
  });
});
