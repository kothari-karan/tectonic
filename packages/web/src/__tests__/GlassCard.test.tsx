import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import GlassCard from '@/components/GlassCard';

describe('GlassCard', () => {
  it('renders children', () => {
    render(<GlassCard>Hello World</GlassCard>);
    expect(screen.getByText('Hello World')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <GlassCard className="custom-class">Content</GlassCard>
    );
    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('applies glass base styles', () => {
    const { container } = render(<GlassCard>Content</GlassCard>);
    expect(container.firstChild).toHaveClass('glass');
  });

  it('handles onClick', () => {
    const handleClick = vi.fn();
    render(<GlassCard onClick={handleClick}>Clickable</GlassCard>);
    fireEvent.click(screen.getByText('Clickable'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('sets role="button" when onClick is provided', () => {
    const handleClick = vi.fn();
    render(<GlassCard onClick={handleClick}>Clickable</GlassCard>);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('does not set role="button" when onClick is not provided', () => {
    render(<GlassCard>Static</GlassCard>);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('adds glass-hover class when onClick is provided', () => {
    const handleClick = vi.fn();
    const { container } = render(
      <GlassCard onClick={handleClick}>Clickable</GlassCard>
    );
    expect(container.firstChild).toHaveClass('glass-hover');
  });

  it('supports keyboard activation with Enter', () => {
    const handleClick = vi.fn();
    render(<GlassCard onClick={handleClick}>Clickable</GlassCard>);
    fireEvent.keyDown(screen.getByRole('button'), { key: 'Enter' });
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('supports keyboard activation with Space', () => {
    const handleClick = vi.fn();
    render(<GlassCard onClick={handleClick}>Clickable</GlassCard>);
    fireEvent.keyDown(screen.getByRole('button'), { key: ' ' });
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
