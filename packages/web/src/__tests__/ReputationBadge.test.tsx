import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ReputationBadge from '@/components/ReputationBadge';

describe('ReputationBadge', () => {
  it('displays the score', () => {
    render(<ReputationBadge score={82} />);
    expect(screen.getByTestId('reputation-badge')).toHaveTextContent('82');
  });

  it('applies red ring for scores below 30', () => {
    render(<ReputationBadge score={15} />);
    const badge = screen.getByTestId('reputation-badge');
    expect(badge.className).toContain('border-red-500');
  });

  it('applies amber ring for scores between 30 and 59', () => {
    render(<ReputationBadge score={45} />);
    const badge = screen.getByTestId('reputation-badge');
    expect(badge.className).toContain('border-amber-500');
  });

  it('applies green ring for scores 60 and above', () => {
    render(<ReputationBadge score={75} />);
    const badge = screen.getByTestId('reputation-badge');
    expect(badge.className).toContain('border-green-500');
  });

  it('applies green ring for score exactly 60', () => {
    render(<ReputationBadge score={60} />);
    const badge = screen.getByTestId('reputation-badge');
    expect(badge.className).toContain('border-green-500');
  });

  it('applies amber ring for score exactly 30', () => {
    render(<ReputationBadge score={30} />);
    const badge = screen.getByTestId('reputation-badge');
    expect(badge.className).toContain('border-amber-500');
  });

  it('renders small size', () => {
    render(<ReputationBadge score={50} size="sm" />);
    const badge = screen.getByTestId('reputation-badge');
    expect(badge.className).toContain('w-10');
    expect(badge.className).toContain('h-10');
  });

  it('renders medium size by default', () => {
    render(<ReputationBadge score={50} />);
    const badge = screen.getByTestId('reputation-badge');
    expect(badge.className).toContain('w-14');
    expect(badge.className).toContain('h-14');
  });

  it('renders large size', () => {
    render(<ReputationBadge score={50} size="lg" />);
    const badge = screen.getByTestId('reputation-badge');
    expect(badge.className).toContain('w-20');
    expect(badge.className).toContain('h-20');
  });

  it('has a title attribute with the score', () => {
    render(<ReputationBadge score={82} />);
    const badge = screen.getByTestId('reputation-badge');
    expect(badge).toHaveAttribute('title', 'Reputation: 82');
  });

  it('handles score of 0', () => {
    render(<ReputationBadge score={0} />);
    const badge = screen.getByTestId('reputation-badge');
    expect(badge).toHaveTextContent('0');
    expect(badge.className).toContain('border-red-500');
  });

  it('handles score of 100', () => {
    render(<ReputationBadge score={100} />);
    const badge = screen.getByTestId('reputation-badge');
    expect(badge).toHaveTextContent('100');
    expect(badge.className).toContain('border-green-500');
  });
});
