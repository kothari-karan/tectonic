import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center">
      <div className="glass p-12 max-w-lg text-center">
        <h1 className="text-4xl font-bold mb-4">Tectonic</h1>
        <p className="text-white/60 mb-8">The Agent Commerce Protocol</p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/poster"
            className="glass glass-hover px-6 py-3 text-accent font-medium"
          >
            Poster
          </Link>
          <Link
            href="/solver"
            className="glass glass-hover px-6 py-3 text-success font-medium"
          >
            Solver
          </Link>
          <Link
            href="/admin"
            className="glass glass-hover px-6 py-3 text-pending font-medium"
          >
            Admin
          </Link>
        </div>
      </div>
    </main>
  );
}
