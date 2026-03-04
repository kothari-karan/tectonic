import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import Header from '@/components/Header';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  usePathname: vi.fn(() => '/requester'),
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
    expect(screen.getByTestId('persona-requester')).toBeInTheDocument();
    expect(screen.getByTestId('persona-provider')).toBeInTheDocument();
    expect(screen.getByTestId('persona-admin')).toBeInTheDocument();
  });

  it('renders Requester, Provider, Admin text', () => {
    render(<Header />);
    expect(screen.getByText('Requester')).toBeInTheDocument();
    expect(screen.getByText('Provider')).toBeInTheDocument();
    expect(screen.getByText('Admin')).toBeInTheDocument();
  });

  it('highlights Requester when on /requester path', () => {
    (usePathname as ReturnType<typeof vi.fn>).mockReturnValue('/requester');
    render(<Header />);
    const requesterLink = screen.getByTestId('persona-requester');
    expect(requesterLink.className).toContain('text-accent');
    expect(requesterLink.className).toContain('bg-accent/20');
  });

  it('highlights Provider when on /provider path', () => {
    (usePathname as ReturnType<typeof vi.fn>).mockReturnValue('/provider');
    render(<Header />);
    const providerLink = screen.getByTestId('persona-provider');
    expect(providerLink.className).toContain('text-accent');
  });

  it('highlights Admin when on /admin path', () => {
    (usePathname as ReturnType<typeof vi.fn>).mockReturnValue('/admin');
    render(<Header />);
    const adminLink = screen.getByTestId('persona-admin');
    expect(adminLink.className).toContain('text-accent');
  });

  it('does not highlight non-active personas', () => {
    (usePathname as ReturnType<typeof vi.fn>).mockReturnValue('/requester');
    render(<Header />);
    const providerLink = screen.getByTestId('persona-provider');
    expect(providerLink.className).toContain('text-white/60');
    expect(providerLink.className).not.toContain('bg-accent/20');
  });

  it('links to correct paths', () => {
    render(<Header />);
    expect(screen.getByTestId('persona-requester')).toHaveAttribute(
      'href',
      '/requester'
    );
    expect(screen.getByTestId('persona-provider')).toHaveAttribute(
      'href',
      '/provider'
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
