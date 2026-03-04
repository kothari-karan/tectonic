'use client';

import Link from 'next/link';
import { clsx } from 'clsx';
import StatusBadge from './StatusBadge';
import EthAmount from './EthAmount';

interface EngagementCardEngagement {
  id: string;
  title: string;
  category: string;
  reward_amount: number;
  status: string;
  deadline: string;
  requester_id?: string;
  provider_id?: string | null;
}

interface EngagementCardProps {
  engagement: EngagementCardEngagement;
  proposalCount?: number;
  requesterReputation?: number;
  className?: string;
}

const categoryColors: Record<string, string> = {
  development: 'bg-purple-500/20 text-purple-300',
  design: 'bg-pink-500/20 text-pink-300',
  data: 'bg-cyan-500/20 text-cyan-300',
  writing: 'bg-emerald-500/20 text-emerald-300',
  legal: 'bg-orange-500/20 text-orange-300',
  other: 'bg-gray-500/20 text-gray-300',
};

function relativeTime(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = date.getTime() - now.getTime();
  const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays < 0) {
    const absDays = Math.abs(diffDays);
    if (absDays === 1) return '1 day ago';
    if (absDays < 30) return `${absDays} days ago`;
    return 'expired';
  }
  if (diffDays === 0) return 'today';
  if (diffDays === 1) return 'tomorrow';
  if (diffDays < 7) return `in ${diffDays} days`;
  if (diffDays < 30) return `in ${Math.ceil(diffDays / 7)} weeks`;
  return `in ${Math.ceil(diffDays / 30)} months`;
}

export default function EngagementCard({
  engagement,
  proposalCount,
  requesterReputation,
  className,
}: EngagementCardProps) {
  const catColor = categoryColors[engagement.category] ?? categoryColors.other;

  return (
    <Link href={`/engagement/${engagement.id}`} className="block">
      <div
        className={clsx(
          'glass glass-hover p-6 flex flex-col gap-4',
          className
        )}
        data-testid="engagement-card"
      >
        {/* Header row */}
        <div className="flex items-start justify-between gap-3">
          <h3 className="text-white font-semibold text-base leading-snug line-clamp-2 flex-1">
            {engagement.title}
          </h3>
          <StatusBadge status={engagement.status} />
        </div>

        {/* Category tag */}
        <div className="flex items-center gap-3">
          <span
            className={clsx(
              'px-2.5 py-0.5 rounded-md text-xs font-medium',
              catColor
            )}
          >
            {engagement.category}
          </span>
        </div>

        {/* Bottom row */}
        <div className="flex items-center justify-between mt-auto pt-2 border-t border-white/5">
          <EthAmount
            amount={engagement.reward_amount}
            className="text-white text-lg"
          />

          <div className="flex items-center gap-4 text-xs text-white/40">
            <span title="Deadline">{relativeTime(engagement.deadline)}</span>
            {proposalCount !== undefined && (
              <span title="Proposals">
                {proposalCount} proposal{proposalCount !== 1 ? 's' : ''}
              </span>
            )}
            {requesterReputation !== undefined && (
              <span
                title="Requester reputation"
                className="text-white/50 font-medium"
              >
                Rep {requesterReputation}
              </span>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}
