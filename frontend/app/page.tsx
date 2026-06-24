import Link from "next/link";
import predictions from "@/lib/predictions";

export default function Home() {
  const rCount = predictions.filter((p) => p.predicted_margin_r > 0).length;
  const dCount = predictions.length - rCount;
  const avgMargin =
    predictions.reduce((s, p) => s + p.predicted_margin_r, 0) /
    predictions.length;

  const top5R = [...predictions]
    .sort((a, b) => b.predicted_margin_r - a.predicted_margin_r)
    .slice(0, 5);
  const top5D = [...predictions]
    .sort((a, b) => a.predicted_margin_r - b.predicted_margin_r)
    .slice(0, 5);
  const closest = [...predictions]
    .sort(
      (a, b) => Math.abs(a.predicted_margin_r) - Math.abs(b.predicted_margin_r),
    )
    .slice(0, 5);

  return (
    <div className="space-y-10">
      {/* Hero */}
      <section className="rounded-2xl bg-gradient-to-br from-blue-600 to-red-600 p-10 text-white">
        <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
          NC 2024 Voter Simulation
        </h1>
        <p className="mt-3 max-w-2xl text-lg text-white/90">
          An agent-based behavioral simulation that generates synthetic voters,
          models turnout and vote choice probabilistically, and predicts
          county-level presidential margins for all 100 North Carolina counties.
        </p>
        <div className="mt-6 flex gap-4">
          <Link
            href="/counties"
            className="rounded-lg bg-white px-5 py-2.5 text-sm font-semibold text-gray-900 shadow hover:bg-gray-100 transition"
          >
            Explore Counties
          </Link>
          <Link
            href="/methodology"
            className="rounded-lg border border-white/40 px-5 py-2.5 text-sm font-semibold text-white hover:bg-white/10 transition"
          >
            Methodology
          </Link>
        </div>
      </section>

      {/* Summary Cards */}
      <section className="grid gap-4 sm:grid-cols-3">
        <Card label="R-Leaning Counties" value={String(rCount)} color="red" />
        <Card label="D-Leaning Counties" value={String(dCount)} color="blue" />
        <Card
          label="Avg County Margin"
          value={`${avgMargin > 0 ? "R" : "D"}+${Math.abs(avgMargin * 100).toFixed(1)}%`}
          color="gray"
        />
      </section>

      {/* Lists */}
      <section className="grid gap-6 md:grid-cols-3">
        <RankList
          title="Most Republican"
          items={top5R}
          color="red"
          format={(p) => `R+${(p.predicted_margin_r * 100).toFixed(1)}%`}
        />
        <RankList
          title="Most Democratic"
          items={top5D}
          color="blue"
          format={(p) =>
            `D+${(Math.abs(p.predicted_margin_r) * 100).toFixed(1)}%`
          }
        />
        <RankList
          title="Closest Races"
          items={closest}
          color="purple"
          format={(p) => {
            const party = p.predicted_margin_r > 0 ? "R" : "D";
            return `${party}+${(Math.abs(p.predicted_margin_r) * 100).toFixed(1)}%`;
          }}
        />
      </section>
    </div>
  );
}

function Card({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) {
  const border =
    color === "red"
      ? "border-red-200"
      : color === "blue"
        ? "border-blue-200"
        : "border-gray-200";
  return (
    <div className={`rounded-xl border ${border} bg-white p-6 shadow-sm`}>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="mt-1 text-3xl font-bold">{value}</p>
    </div>
  );
}

interface RankItem {
  county_name: string;
  predicted_margin_r: number;
}

function RankList({
  title,
  items,
  color,
  format,
}: {
  title: string;
  items: RankItem[];
  color: string;
  format: (p: RankItem) => string;
}) {
  const heading =
    color === "red"
      ? "text-red-700"
      : color === "blue"
        ? "text-blue-700"
        : "text-purple-700";
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <h3
        className={`mb-3 text-sm font-semibold uppercase tracking-wide ${heading}`}
      >
        {title}
      </h3>
      <ol className="space-y-2 text-sm">
        {items.map((p, i) => (
          <li key={p.county_name} className="flex justify-between">
            <span>
              {i + 1}. {p.county_name}
            </span>
            <span className="font-mono font-medium">{format(p)}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
