import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ContractStatusTracker from '@/components/ContractStatusTracker';

describe('ContractStatusTracker', () => {
  it('renders the tracker', () => {
    render(<ContractStatusTracker status="pending" />);
    expect(screen.getByTestId('contract-status-tracker')).toBeInTheDocument();
  });

  it('displays all stage labels', () => {
    render(<ContractStatusTracker status="pending" />);
    expect(screen.getByText('Pending Funding')).toBeInTheDocument();
    expect(screen.getByText('Funded')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
    expect(screen.getByText('Delivered')).toBeInTheDocument();
    expect(screen.getByText('Verified')).toBeInTheDocument();
    expect(screen.getByText('Settled')).toBeInTheDocument();
  });

  it('highlights current stage with accent color for pending', () => {
    render(<ContractStatusTracker status="pending" />);
    const label = screen.getByText('Pending Funding');
    expect(label.className).toContain('text-accent');
  });

  it('highlights current stage for funded', () => {
    render(<ContractStatusTracker status="funded" />);
    const label = screen.getByText('Funded');
    expect(label.className).toContain('text-accent');
  });

  it('highlights current stage for in_progress', () => {
    render(<ContractStatusTracker status="in_progress" />);
    const label = screen.getByText('In Progress');
    expect(label.className).toContain('text-accent');
  });

  it('highlights current stage for delivered', () => {
    render(<ContractStatusTracker status="delivered" />);
    const label = screen.getByText('Delivered');
    expect(label.className).toContain('text-accent');
  });

  it('highlights current stage for verified', () => {
    render(<ContractStatusTracker status="verified" />);
    const label = screen.getByText('Verified');
    expect(label.className).toContain('text-accent');
  });

  it('highlights current stage for settled', () => {
    render(<ContractStatusTracker status="settled" />);
    const label = screen.getByText('Settled');
    expect(label.className).toContain('text-accent');
  });

  it('marks previous stages as completed (green) for in_progress', () => {
    render(<ContractStatusTracker status="in_progress" />);
    const pendingLabel = screen.getByText('Pending Funding');
    const fundedLabel = screen.getByText('Funded');
    expect(pendingLabel.className).toContain('text-green-400');
    expect(fundedLabel.className).toContain('text-green-400');
  });

  it('marks future stages as inactive for funded', () => {
    render(<ContractStatusTracker status="funded" />);
    const inProgressLabel = screen.getByText('In Progress');
    expect(inProgressLabel.className).toContain('text-white/30');
  });

  it('shows disputed status with special badge', () => {
    render(<ContractStatusTracker status="disputed" />);
    expect(screen.getByText('disputed')).toBeInTheDocument();
  });

  it('shows cancelled status with special badge', () => {
    render(<ContractStatusTracker status="cancelled" />);
    expect(screen.getByText('cancelled')).toBeInTheDocument();
  });
});
