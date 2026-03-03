import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import StatusBadge from '@/components/StatusBadge';

describe('StatusBadge', () => {
  it('renders the status text', () => {
    render(<StatusBadge status="open" />);
    expect(screen.getByTestId('status-badge')).toHaveTextContent('open');
  });

  it('replaces underscores with spaces in display', () => {
    render(<StatusBadge status="in_progress" />);
    expect(screen.getByTestId('status-badge')).toHaveTextContent('in progress');
  });

  it('applies amber color for open status', () => {
    render(<StatusBadge status="open" />);
    const badge = screen.getByTestId('status-badge');
    expect(badge.className).toContain('text-amber-400');
    expect(badge.className).toContain('bg-amber-500/20');
  });

  it('applies amber color for pending status', () => {
    render(<StatusBadge status="pending" />);
    const badge = screen.getByTestId('status-badge');
    expect(badge.className).toContain('text-amber-400');
  });

  it('applies blue color for negotiating status', () => {
    render(<StatusBadge status="negotiating" />);
    const badge = screen.getByTestId('status-badge');
    expect(badge.className).toContain('text-blue-400');
  });

  it('applies blue color for in_progress status', () => {
    render(<StatusBadge status="in_progress" />);
    const badge = screen.getByTestId('status-badge');
    expect(badge.className).toContain('text-blue-400');
  });

  it('applies blue color for funded status', () => {
    render(<StatusBadge status="funded" />);
    const badge = screen.getByTestId('status-badge');
    expect(badge.className).toContain('text-blue-400');
  });

  it('applies sky color for agreed status', () => {
    render(<StatusBadge status="agreed" />);
    const badge = screen.getByTestId('status-badge');
    expect(badge.className).toContain('text-sky-300');
  });

  it('applies sky color for delivered status', () => {
    render(<StatusBadge status="delivered" />);
    const badge = screen.getByTestId('status-badge');
    expect(badge.className).toContain('text-sky-300');
  });

  it('applies sky color for verified status', () => {
    render(<StatusBadge status="verified" />);
    const badge = screen.getByTestId('status-badge');
    expect(badge.className).toContain('text-sky-300');
  });

  it('applies green color for settled status', () => {
    render(<StatusBadge status="settled" />);
    const badge = screen.getByTestId('status-badge');
    expect(badge.className).toContain('text-green-400');
  });

  it('applies green color for completed status', () => {
    render(<StatusBadge status="completed" />);
    const badge = screen.getByTestId('status-badge');
    expect(badge.className).toContain('text-green-400');
  });

  it('applies green color for confirmed status', () => {
    render(<StatusBadge status="confirmed" />);
    const badge = screen.getByTestId('status-badge');
    expect(badge.className).toContain('text-green-400');
  });

  it('applies red color for disputed status', () => {
    render(<StatusBadge status="disputed" />);
    const badge = screen.getByTestId('status-badge');
    expect(badge.className).toContain('text-red-400');
  });

  it('applies gray color for cancelled status', () => {
    render(<StatusBadge status="cancelled" />);
    const badge = screen.getByTestId('status-badge');
    expect(badge.className).toContain('text-gray-400');
  });

  it('applies gray color for rejected status', () => {
    render(<StatusBadge status="rejected" />);
    const badge = screen.getByTestId('status-badge');
    expect(badge.className).toContain('text-gray-400');
  });

  it('applies default gray for unknown status', () => {
    render(<StatusBadge status="unknown_status" />);
    const badge = screen.getByTestId('status-badge');
    expect(badge.className).toContain('text-gray-400');
  });

  it('accepts custom className', () => {
    render(<StatusBadge status="open" className="extra-class" />);
    const badge = screen.getByTestId('status-badge');
    expect(badge.className).toContain('extra-class');
  });
});
