import {
  rCounties,
  dCounties,
  statewideWinner,
  statewideRPct,
  statewideDPct,
  closestCounty,
  largestMarginCounty,
} from "@/lib/statewide-stats";
import { formatMargin } from "@/lib/map-utils";

export default function StatewideSummary() {
  const winnerColor =
    statewideWinner === "Republican" ? "text-red-600" : "text-blue-600";
  const winnerBorder =
    statewideWinner === "Republican" ? "border-red-200" : "border-blue-200";
  const winnerBg =
    statewideWinner === "Republican" ? "bg-red-50/50" : "bg-blue-50/50";

  return (
    <section className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
      {/* Projected Winner */}
      <div
        className={`col-span-2 sm:col-span-1 rounded-xl border ${winnerBorder} ${winnerBg} p-4 shadow-sm`}
      >
        <p className="text-[11px] font-medium uppercase tracking-wider text-gray-400">
          Projected Winner
        </p>
        <p className={`mt-1 text-xl font-extrabold ${winnerColor}`}>
          {statewideWinner}
        </p>
        <p className="mt-0.5 text-[11px] text-gray-400">Pop-weighted avg</p>
      </div>

      {/* R Vote % */}
      <SummaryCard
        label="Republican %"
        value={`${statewideRPct}%`}
        accent="text-red-600"
        border="border-gray-200"
      />

      {/* D Vote % */}
      <SummaryCard
        label="Democratic %"
        value={`${statewideDPct}%`}
        accent="text-blue-600"
        border="border-gray-200"
      />

      {/* R Counties */}
      <SummaryCard
        label="R Counties"
        value={String(rCounties)}
        accent="text-red-600"
        border="border-gray-200"
      />

      {/* D Counties */}
      <SummaryCard
        label="D Counties"
        value={String(dCounties)}
        accent="text-blue-600"
        border="border-gray-200"
      />

      {/* Closest Race */}
      <SummaryCard
        label="Closest Race"
        value={closestCounty.county_name}
        sub={formatMargin(closestCounty.predicted_margin_r)}
        accent="text-purple-600"
        border="border-gray-200"
      />

      {/* Largest Margin */}
      <SummaryCard
        label="Largest Margin"
        value={largestMarginCounty.county_name}
        sub={formatMargin(largestMarginCounty.predicted_margin_r)}
        accent={
          largestMarginCounty.predicted_margin_r > 0
            ? "text-red-600"
            : "text-blue-600"
        }
        border="border-gray-200"
      />
    </section>
  );
}

function SummaryCard({
  label,
  value,
  sub,
  accent,
  border,
}: {
  label: string;
  value: string;
  sub?: string;
  accent: string;
  border: string;
}) {
  return (
    <div className={`rounded-xl border ${border} bg-white p-4 shadow-sm`}>
      <p className="text-[11px] font-medium uppercase tracking-wider text-gray-400">
        {label}
      </p>
      <p className={`mt-1 text-xl font-extrabold tabular-nums ${accent}`}>
        {value}
      </p>
      {sub && (
        <p className="mt-0.5 text-[11px] font-medium text-gray-400">{sub}</p>
      )}
    </div>
  );
}
