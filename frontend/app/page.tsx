import Link from "next/link";
import StatewideSummary from "@/components/StatewideSummary";
import DashboardPage from "@/components/DashboardPage";

export default function Home() {
  return (
    <div className="space-y-6">
      {/* Compact Hero */}
      <section className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-gray-900 sm:text-3xl">
            North Carolina Election Projection Dashboard
          </h1>
          <p className="mt-1 max-w-2xl text-sm text-gray-500">
            Interactive county-level projections and statewide election analysis
            powered by agent-based voter simulation.
          </p>
        </div>
        <div className="flex shrink-0 gap-2">
          <Link
            href="/results"
            className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-xs font-semibold text-gray-600 shadow-sm hover:bg-gray-50 transition-colors"
          >
            Data View
          </Link>
          <Link
            href="/about"
            className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-xs font-semibold text-gray-600 shadow-sm hover:bg-gray-50 transition-colors"
          >
            Methodology
          </Link>
        </div>
      </section>

      {/* Statewide Summary Cards */}
      <StatewideSummary />

      {/* Interactive Map + Details Panel */}
      <DashboardPage />
    </div>
  );
}
