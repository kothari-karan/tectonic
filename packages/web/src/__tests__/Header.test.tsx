import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import Header from '@/components/Header';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  usePathname: vi.fn(() => '/poster'),
}));

// Mock next/link
vi.mock('next/link', () => ({
  default: ({
    children,
    href,
    className,
    ...props
  }: {
    children: React.ReactNode;
    href: string;
    className?: string;
    [key: string]: unknown;
  }) => (
    <a href={href} className={className} {...props}>
      {children}
    </a>
  ),
}));

import { usePathname } from 'next/navigation';

describe('Header', () => {
  it('renders the Tectonic brand', () => {
    render(<Header />);
    expect(screen.getByText('Tectonic')).toBeInTheDocument();
  });

  it('renders all persona navigation links', () => {
    render(<Header />);
    expect(screen.getByTestId('persona-poster')).toBeInTheDocument();
    expect(screen.getByTestId('persona-solver')).toBeInTheDocument();
    expect(screen.getByTestId('persona-admin')).toBeInTheDocument();
  });

  it('renders Poster, Solver, Admin text', () => {
    render(<Header />);
    expect(screen.getByText('Poster')).toBeInTheDocument();
    expect(screen.getByText('Solver')).toBeInTheDocument();
    expect(screen.getByText('Admin')).toBeInTheDocument();
  });

  it('highlights Poster when on /poster path', () => {
    (usePathname as ReturnType<typeof vi.fn>).mockReturnValue('/poster');
    render(<Header />);
    const posterLink = screen.getByTestId('persona-poster');
    expect(posterLink.className).toContain('text-accent');
    expect(posterLink.className).toContain('bg-accent/20');
  });

  it('highlights Solver when on /solver path', () => {
    (usePathname as ReturnType<typeof vi.fn>).mockReturnValue('/solver');
    render(<Header />);
    const solverLink = screen.getByTestId('persona-solver');
    expect(solverLink.className).toContain('text-accent');
  });

  it('highlights Admin when on /admin path', () => {
    (usePathname as ReturnType<typeof vi.fn>).mockReturnValue('/admin');
    render(<Header />);
    const adminLink = screen.getByTestId('persona-admin');
    expect(adminLink.className).toContain('text-accent');
  });

  it('does not highlight non-active personas', () => {
    (usePathname as ReturnType<typeof vi.fn>).mockReturnValue('/poster');
    render(<Header />);
    const solverLink = screen.getByTestId('persona-solver');
    expect(solverLink.className).toContain('text-white/60');
    expect(solverLink.className).not.toContain('bg-accent/20');
  });

  it('links to correct paths', () => {
    render(<Header />);
    expect(screen.getByTestId('persona-poster')).toHaveAttribute(
      'href',
      '/poster'
    );
    expect(screen.getByTestId('persona-solver')).toHaveAttribute(
      'href',
      '/solver'
    );
    expect(screen.getByTestId('persona-admin')).toHaveAttribute(
      'href',
      '/admin'
    );
  });

  it('has a persona nav container', () => {
    render(<Header />);
    expect(screen.getByTestId('persona-nav')).toBeInTheDocument();
  });
});
