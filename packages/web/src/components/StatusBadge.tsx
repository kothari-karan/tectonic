'use client';

import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface StatusBadgeProps {
  status: string;
  className?: string;
}

const statusColorMap: Record<string, { bg: string; text: string; glow: string }> = {
  open: {
    bg: 'bg-amber-500/20',
    text: 'text-amber-400',
    glow: 'shadow-[0_0_8px_rgba(245,158,11,0.3)]',
  },
  pending: {
    bg: 'bg-amber-500/20',
    text: 'text-amber-400',
    glow: 'shadow-[0_0_8px_rgba(245,158,11,0.3)]',
  },
  negotiating: {
    bg: 'bg-blue-500/20',
    text: 'text-blue-400',
    glow: 'shadow-[0_0_8px_rgba(59,130,246,0.3)]',
  },
  in_progress: {
    bg: 'bg-blue-500/20',
    text: 'text-blue-400',
    glow: 'shadow-[0_0_8px_rgba(59,130,246,0.3)]',
  },
  funded: {
    bg: 'bg-blue-500/20',
    text: 'text-blue-400',
    glow: 'shadow-[0_0_8px_rgba(59,130,246,0.3)]',
  },
  agreed: {
    bg: 'bg-sky-500/20',
    text: 'text-sky-300',
    glow: 'shadow-[0_0_8px_rgba(56,189,248,0.3)]',
  },
  delivered: {
    bg: 'bg-sky-500/20',
    text: 'text-sky-300',
    glow: 'shadow-[0_0_8px_rgba(56,189,248,0.3)]',
  },
  verified: {
    bg: 'bg-sky-500/20',
    text: 'text-sky-300',
    glow: 'shadow-[0_0_8px_rgba(56,189,248,0.3)]',
  },
  settled: {
    bg: 'bg-green-500/20',
    text: 'text-green-400',
    glow: 'shadow-[0_0_8px_rgba(34,197,94,0.3)]',
  },
  completed: {
    bg: 'bg-green-500/20',
    text: 'text-green-400',
    glow: 'shadow-[0_0_8px_rgba(34,197,94,0.3)]',
  },
  confirmed: {
    bg: 'bg-green-500/20',
    text: 'text-green-400',
    glow: 'shadow-[0_0_8px_rgba(34,197,94,0.3)]',
  },
  disputed: {
    bg: 'bg-red-500/20',
    text: 'text-red-400',
    glow: 'shadow-[0_0_8px_rgba(239,68,68,0.3)]',
  },
  cancelled: {
    bg: 'bg-gray-500/20',
    text: 'text-gray-400',
    glow: 'shadow-[0_0_8px_rgba(107,114,128,0.2)]',
  },
  rejected: {
    bg: 'bg-gray-500/20',
    text: 'text-gray-400',
    glow: 'shadow-[0_0_8px_rgba(107,114,128,0.2)]',
  },
  accepted: {
    bg: 'bg-green-500/20',
    text: 'text-green-400',
    glow: 'shadow-[0_0_8px_rgba(34,197,94,0.3)]',
  },
};

const defaultColor = {
  bg: 'bg-gray-500/20',
  text: 'text-gray-400',
  glow: 'shadow-[0_0_8px_rgba(107,114,128,0.2)]',
};

export default function StatusBadge({ status, className }: StatusBadgeProps) {
  const color = statusColorMap[status] ?? defaultColor;

  return (
    <span
      className={twMerge(
        clsx(
          'inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider',
          color.bg,
          color.text,
          color.glow,
          className
        )
      )}
      data-testid="status-badge"
    >
      {status.replace(/_/g, ' ')}
    </span>
  );
}
