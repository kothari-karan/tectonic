'use client';

import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface ReputationBadgeProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeMap = {
  sm: { container: 'w-10 h-10', text: 'text-xs', ring: 'border-2' },
  md: { container: 'w-14 h-14', text: 'text-sm', ring: 'border-[3px]' },
  lg: { container: 'w-20 h-20', text: 'text-lg', ring: 'border-4' },
};

function getRingColor(score: number): string {
  if (score < 30) return 'border-red-500';
  if (score < 60) return 'border-amber-500';
  return 'border-green-500';
}

function getGlowColor(score: number): string {
  if (score < 30) return 'shadow-[0_0_12px_rgba(239,68,68,0.4)]';
  if (score < 60) return 'shadow-[0_0_12px_rgba(245,158,11,0.4)]';
  return 'shadow-[0_0_12px_rgba(34,197,94,0.4)]';
}

export default function ReputationBadge({
  score,
  size = 'md',
  className,
}: ReputationBadgeProps) {
  const dims = sizeMap[size];

  return (
    <div
      className={twMerge(
        clsx(
          'inline-flex items-center justify-center rounded-full bg-white/5',
          dims.container,
          dims.ring,
          getRingColor(score),
          getGlowColor(score),
          className
        )
      )}
      data-testid="reputation-badge"
      title={`Reputation: ${score}`}
    >
      <span className={clsx('font-bold text-white', dims.text)}>{score}</span>
    </div>
  );
}
