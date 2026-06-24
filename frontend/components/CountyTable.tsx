"use client";

import { useState, useMemo } from "react";
import predictions, { CountyPrediction } from "@/lib/predictions";

type SortKey =
  | "county_name"
  | "predicted_margin_r"
  | "margin_std"
  | "avg_turnout_rate";

export default function CountyTable() {
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("county_name");
  const [sortAsc, setSortAsc] = useState(true);

  const filtered = useMemo(() => {
    const data = predictions.filter((p) =>
      p.county_name.toLowerCase().includes(search.toLowerCase()),
    );
    data.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === "string" && typeof bv === "string")
        return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
      return sortAsc
        ? (av as number) - (bv as number)
        : (bv as number) - (av as number);
    });
    return data;
  }, [search, sortKey, sortAsc]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortAsc(!sortAsc);
    else {
      setSortKey(key);
      setSortAsc(key === "county_name");
    }
  }

  function arrow(key: SortKey) {
    if (sortKey !== key) return "";
    return sortAsc ? " \u25B2" : " \u25BC";
  }

  return (
    <div className="space-y-4">
      <input
        type="text"
        placeholder="Search counties..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full max-w-sm rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
      />

      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-500">
            <tr>
              <Th onClick={() => toggleSort("county_name")}>
                County{arrow("county_name")}
              </Th>
              <Th onClick={() => toggleSort("predicted_margin_r")} right>
                Margin{arrow("predicted_margin_r")}
              </Th>
              <Th onClick={() => toggleSort("margin_std")} right>
                Std Dev{arrow("margin_std")}
              </Th>
              <Th right>95% CI</Th>
              <Th onClick={() => toggleSort("avg_turnout_rate")} right>
                Turnout{arrow("avg_turnout_rate")}
              </Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.map((p) => (
              <Row key={p.county_fips} p={p} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Th({
  children,
  onClick,
  right,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  right?: boolean;
}) {
  return (
    <th
      className={`px-4 py-3 font-semibold ${right ? "text-right" : ""} ${onClick ? "cursor-pointer select-none hover:text-gray-800" : ""}`}
      onClick={onClick}
    >
      {children}
    </th>
  );
}

function Row({ p }: { p: CountyPrediction }) {
  const margin = p.predicted_margin_r;
  const party = margin > 0 ? "R" : "D";
  const color = margin > 0 ? "text-red-600" : "text-blue-600";
  const bg =
    margin > 0
      ? "bg-red-50 hover:bg-red-100/60"
      : "bg-blue-50 hover:bg-blue-100/60";

  const barWidth = Math.min(Math.abs(margin) * 100, 50);

  return (
    <tr className={`${bg} transition-colors`}>
      <td className="px-4 py-2.5 font-medium">{p.county_name}</td>
      <td
        className={`px-4 py-2.5 text-right font-mono font-semibold ${color}`}
      >
        <div className="relative inline-flex items-center gap-2">
          <span>
            {party}+{(Math.abs(margin) * 100).toFixed(1)}%
          </span>
          <span
            className={`inline-block h-3 rounded ${margin > 0 ? "bg-red-400" : "bg-blue-400"}`}
            style={{ width: `${barWidth}px` }}
          />
        </div>
      </td>
      <td className="px-4 py-2.5 text-right font-mono text-gray-500">
        {(p.margin_std * 100).toFixed(1)}%
      </td>
      <td className="px-4 py-2.5 text-right font-mono text-gray-500">
        [{(p.ci_low * 100).toFixed(1)}, {(p.ci_high * 100).toFixed(1)}]
      </td>
      <td className="px-4 py-2.5 text-right font-mono text-gray-500">
        {(p.avg_turnout_rate * 100).toFixed(1)}%
      </td>
    </tr>
  );
}
