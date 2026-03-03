'use client';

import { clsx } from 'clsx';

interface ContractStatusTrackerProps {
  status: string;
  className?: string;
}

const stages = [
  { key: 'pending', label: 'Pending Funding' },
  { key: 'funded', label: 'Funded' },
  { key: 'in_progress', label: 'In Progress' },
  { key: 'delivered', label: 'Delivered' },
  { key: 'verified', label: 'Verified' },
  { key: 'settled', label: 'Settled' },
] as const;

const stageIndex: Record<string, number> = {
  pending: 0,
  funded: 1,
  in_progress: 2,
  delivered: 3,
  verified: 4,
  settled: 5,
  completed: 5,
  disputed: -1,
  cancelled: -1,
};

export default function ContractStatusTracker({
  status,
  className,
}: ContractStatusTrackerProps) {
  const currentIdx = stageIndex[status] ?? -1;

  // Special display for disputed/cancelled
  if (status === 'disputed' || status === 'cancelled') {
    return (
      <div className={clsx('', className)} data-testid="contract-status-tracker">
        <div className="flex items-center gap-2">
          {stages.map((stage, i) => (
            <div key={stage.key} className="flex items-center flex-1 last:flex-initial">
              <div className="flex flex-col items-center gap-1.5 flex-1">
                <div
                  className={clsx(
                    'w-3 h-3 rounded-full',
                    'bg-gray-600'
                  )}
                />
                <span className="text-[10px] text-white/30 text-center leading-tight">
                  {stage.label}
                </span>
              </div>
              {i < stages.length - 1 && (
                <div className="h-0.5 flex-1 mx-1 bg-white/5 rounded-full min-w-[20px]" />
              )}
            </div>
          ))}
        </div>
        <div className="mt-3 text-center">
          <span
            className={clsx(
              'px-3 py-1 rounded-full text-xs font-semibold uppercase',
              status === 'disputed'
                ? 'bg-red-500/20 text-red-400'
                : 'bg-gray-500/20 text-gray-400'
            )}
          >
            {status}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className={clsx('', className)} data-testid="contract-status-tracker">
      <div className="flex items-center gap-2">
        {stages.map((stage, i) => {
          const isCompleted = i < currentIdx;
          const isCurrent = i === currentIdx;

          return (
            <div key={stage.key} className="flex items-center flex-1 last:flex-initial">
              <div className="flex flex-col items-center gap-1.5 flex-1">
                <div
                  className={clsx(
                    'w-3 h-3 rounded-full transition-all duration-500',
                    isCompleted && 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]',
                    isCurrent &&
                      'bg-accent shadow-[0_0_12px_rgba(59,130,246,0.5)] ring-2 ring-accent/30',
                    !isCompleted && !isCurrent && 'bg-white/10'
                  )}
                />
                <span
                  className={clsx(
                    'text-[10px] text-center leading-tight transition-colors',
                    isCompleted && 'text-green-400/80',
                    isCurrent && 'text-accent font-semibold',
                    !isCompleted && !isCurrent && 'text-white/30'
                  )}
                >
                  {stage.label}
                </span>
              </div>
              {i < stages.length - 1 && (
                <div
                  className={clsx(
                    'h-0.5 flex-1 mx-1 rounded-full min-w-[20px] transition-all duration-500',
                    i < currentIdx ? 'bg-green-500/60' : 'bg-white/5'
                  )}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
