'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { clsx } from 'clsx';

const personas = [
  { name: 'Poster', href: '/poster' },
  { name: 'Solver', href: '/solver' },
  { name: 'Admin', href: '/admin' },
] as const;

export default function Header() {
  const pathname = usePathname();

  const activePersona = personas.find((p) => pathname.startsWith(p.href));

  return (
    <header className="glass border-t-0 rounded-t-none border-x-0 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded-lg bg-accent/20 flex items-center justify-center border border-accent/30">
            <span className="text-accent font-bold text-sm">T</span>
          </div>
          <span className="text-xl font-bold text-white tracking-tight group-hover:text-accent transition-colors">
            Tectonic
          </span>
        </Link>

        <nav className="flex items-center gap-1" data-testid="persona-nav">
          {personas.map((persona) => {
            const isActive = activePersona?.href === persona.href;
            return (
              <Link
                key={persona.href}
                href={persona.href}
                data-testid={`persona-${persona.name.toLowerCase()}`}
                className={clsx(
                  'px-5 py-2 rounded-xl text-sm font-medium transition-all duration-300',
                  isActive
                    ? 'bg-accent/20 text-accent border border-accent/30 shadow-[0_0_12px_rgba(59,130,246,0.2)]'
                    : 'text-white/60 hover:text-white hover:bg-white/5 border border-transparent'
                )}
              >
                {persona.name}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
