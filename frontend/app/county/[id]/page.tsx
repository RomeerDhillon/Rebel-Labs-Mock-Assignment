import Link from "next/link";
import { notFound } from "next/navigation";
import predictions from "@/lib/predictions";
import { getCountyByIdOrSlug, getCountySlug } from "@/lib/county-slugs";
import {
  formatMargin,
  getPartyLabel,
  getCountyFillColor,
} from "@/lib/map-utils";

export function generateStaticParams() {
  const params: { id: string }[] = [];
  for (const p of predictions) {
    params.push({ id: p.county_fips });
    params.push({ id: getCountySlug(p.county_name) });
  }
  return params;
}

export default function CountyPage({ params }: { params: { id: string } }) {
  const prediction = getCountyByIdOrSlug(params.id);
  if (!prediction) return notFound();

  const p = prediction;
  const margin = p.predicted_margin_r;
  const dotColor = getCountyFillColor(margin);
  const party = getPartyLabel(margin);

  const sorted = [...predictions].sort(
    (a, b) =>
      Math.abs(a.predicted_margin_r - margin) -
      Math.abs(b.predicted_margin_r - margin),
  );
  const similar = sorted
    .filter((s) => s.county_fips !== p.county_fips)
    .slice(0, 5);

  return (
    <div className="space-y-8">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-gray-400">
        <Link href="/" className="hover:text-gray-600 transition-colors">
          Dashboard
        </Link>
        <span>/</span>
        <Link
          href="/counties"
          className="hover:text-gray-600 transition-colors"
        >
          Counties
        </Link>
        <span>/</span>
        <span className="font-medium text-gray-700">{p.county_name}</span>
      </nav>

      {/* Header */}
      <div className="flex items-center gap-4">
        <span
          className="inline-block h-6 w-6 rounded-full shadow-sm"
          style={{ backgroundColor: dotColor }}
        />
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-gray-900">
            {p.county_name} County
          </h1>
          <p className="text-sm text-gray-500">
            FIPS {p.county_fips} &middot; {party}
          </p>
        </div>
      </div>

      {/* Main Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Predicted Margin"
          value={formatMargin(margin)}
          color={dotColor}
        />
        <StatCard
          label="Std Deviation"
          value={`\u00B1${(p.margin_std * 100).toFixed(1)}%`}
        />
        <StatCard
          label="95% Confidence Interval"
          value={`[${(p.ci_low * 100).toFixed(1)}%, ${(p.ci_high * 100).toFixed(1)}%]`}
        />
        <StatCard
          label="Avg Turnout Rate"
          value={`${(p.avg_turnout_rate * 100).toFixed(1)}%`}
        />
      </div>

      {/* Margin Bar */}
      <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
          Margin Position
        </h2>
        <div className="flex items-center justify-between text-xs text-gray-400 mb-1.5">
          <span>D+100%</span>
          <span>Even</span>
          <span>R+100%</span>
        </div>
        <div className="relative h-4 w-full overflow-hidden rounded-full bg-gray-100">
          <div
            className="absolute left-0 top-0 h-full bg-gradient-to-r from-blue-700 to-blue-400"
            style={{ width: "50%" }}
          />
          <div
            className="absolute right-0 top-0 h-full bg-gradient-to-r from-red-400 to-red-700"
            style={{ width: "50%" }}
          />
          <div
            className="absolute top-[-3px] h-[calc(100%+6px)] w-1.5 rounded-full bg-gray-900 shadow-lg"
            style={{ left: `${((margin + 1) / 2) * 100}%` }}
          />
        </div>
        <div className="mt-2 text-center">
          <span
            className="text-lg font-extrabold tabular-nums"
            style={{ color: dotColor }}
          >
            {formatMargin(margin)}
          </span>
        </div>
      </div>

      {/* Similar Counties */}
      <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-400">
          Counties with Similar Margins
        </h2>
        <div className="space-y-2">
          {similar.map((s) => {
            const sMargin = s.predicted_margin_r;
            const sColor = getCountyFillColor(sMargin);
            return (
              <Link
                key={s.county_fips}
                href={`/county/${getCountySlug(s.county_name)}`}
                className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-2.5 text-sm hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span
                    className="inline-block h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: sColor }}
                  />
                  <span className="font-medium text-gray-700">
                    {s.county_name}
                  </span>
                </div>
                <span
                  className="font-mono font-semibold tabular-nums"
                  style={{ color: sColor }}
                >
                  {formatMargin(sMargin)}
                </span>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Back */}
      <Link
        href="/counties"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-gray-500 hover:text-gray-700 transition-colors"
      >
        &larr; Back to Map
      </Link>
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <p className="text-[11px] font-medium uppercase tracking-wider text-gray-400">
        {label}
      </p>
      <p
        className="mt-1.5 text-2xl font-extrabold tabular-nums"
        style={color ? { color } : undefined}
      >
        {value}
      </p>
    </div>
  );
}
