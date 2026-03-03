'use client';

import { clsx } from 'clsx';

interface TimelineTurn {
  id: string;
  agent_name?: string;
  turn_type: string;
  proposed_terms?: Record<string, unknown> | null;
  message?: string | null;
  created_at: string;
}

interface NegotiationTimelineProps {
  turns: TimelineTurn[];
  className?: string;
}

const turnTypeColors: Record<string, { bg: string; text: string; dot: string }> = {
  propose: {
    bg: 'bg-blue-500/20',
    text: 'text-blue-400',
    dot: 'bg-blue-500',
  },
  counter: {
    bg: 'bg-amber-500/20',
    text: 'text-amber-400',
    dot: 'bg-amber-500',
  },
  accept: {
    bg: 'bg-green-500/20',
    text: 'text-green-400',
    dot: 'bg-green-500',
  },
  reject: {
    bg: 'bg-red-500/20',
    text: 'text-red-400',
    dot: 'bg-red-500',
  },
};

const defaultTurnColor = {
  bg: 'bg-gray-500/20',
  text: 'text-gray-400',
  dot: 'bg-gray-500',
};

function formatTerms(terms: Record<string, unknown>): React.ReactNode {
  const entries: { label: string; value: string }[] = [];

  if (terms.price !== undefined) {
    entries.push({ label: 'Price', value: `${terms.price} ETH` });
  }
  if (terms.deadline) {
    entries.push({
      label: 'Deadline',
      value: new Date(terms.deadline as string).toLocaleDateString(),
    });
  }
  if (Array.isArray(terms.deliverables)) {
    entries.push({
      label: 'Deliverables',
      value: (terms.deliverables as string[]).join(', '),
    });
  }

  if (entries.length === 0) return null;

  return (
    <div className="mt-2 space-y-1">
      {entries.map((entry) => (
        <div key={entry.label} className="flex gap-2 text-xs">
          <span className="text-white/40 min-w-[80px]">{entry.label}:</span>
          <span className="text-white/70">{entry.value}</span>
        </div>
      ))}
    </div>
  );
}

function formatTime(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function NegotiationTimeline({
  turns,
  className,
}: NegotiationTimelineProps) {
  if (!turns || turns.length === 0) {
    return (
      <div
        className={clsx('text-white/40 text-sm py-4 text-center', className)}
        data-testid="negotiation-timeline-empty"
      >
        No negotiation turns yet.
      </div>
    );
  }

  return (
    <div className={clsx('relative', className)} data-testid="negotiation-timeline">
      {/* Vertical line */}
      <div className="absolute left-4 top-3 bottom-3 w-px bg-white/10" />

      <div className="space-y-4">
        {turns.map((turn) => {
          const color = turnTypeColors[turn.turn_type] ?? defaultTurnColor;

          return (
            <div key={turn.id} className="relative pl-10">
              {/* Dot */}
              <div
                className={clsx(
                  'absolute left-[11px] top-3 w-[10px] h-[10px] rounded-full ring-2 ring-background',
                  color.dot
                )}
              />

              {/* Bubble */}
              <div className="glass p-4">
                <div className="flex items-center gap-3 mb-1">
                  <span
                    className={clsx(
                      'px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider',
                      color.bg,
                      color.text
                    )}
                  >
                    {turn.turn_type}
                  </span>
                  <span className="text-white/80 text-sm font-medium">
                    {turn.agent_name ?? 'Unknown'}
                  </span>
                  <span className="text-white/30 text-xs ml-auto">
                    {formatTime(turn.created_at)}
                  </span>
                </div>

                {turn.message && (
                  <p className="text-white/60 text-sm leading-relaxed">
                    {turn.message}
                  </p>
                )}

                {turn.proposed_terms && formatTerms(turn.proposed_terms)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
