export default function MapLegend() {
  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-2 rounded-xl border border-gray-200 bg-white px-5 py-3 text-xs shadow-sm">
      <span className="font-semibold text-gray-500 uppercase tracking-wide">
        Legend
      </span>
      <LegendItem color="#1e3a8a" label="Strong D (>40%)" />
      <LegendItem color="#2563eb" label="Lean D (8–40%)" />
      <LegendItem color="#60a5fa" label="Tilt D (<8%)" />
      <LegendItem color="#9ca3af" label="Tie" />
      <LegendItem color="#f87171" label="Tilt R (<8%)" />
      <LegendItem color="#ef4444" label="Lean R (8–40%)" />
      <LegendItem color="#991b1b" label="Strong R (>40%)" />
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span
        className="inline-block h-3 w-3 rounded-sm border border-gray-300"
        style={{ backgroundColor: color }}
      />
      <span className="text-gray-600">{label}</span>
    </div>
  );
}
