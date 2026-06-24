import { CountyPrediction } from "@/lib/predictions";
import {
  formatMargin,
  getPartyLabel,
  getCountyFillColor,
} from "@/lib/map-utils";

interface MapTooltipProps {
  prediction: CountyPrediction;
  x: number;
  y: number;
}

export default function MapTooltip({ prediction, x, y }: MapTooltipProps) {
  const p = prediction;
  const margin = p.predicted_margin_r;
  const dotColor = getCountyFillColor(margin);

  const tooltipW = 264;
  const tooltipH = 200;
  const windowW = typeof window !== "undefined" ? window.innerWidth : 1200;
  const windowH = typeof window !== "undefined" ? window.innerHeight : 800;

  const left = x + tooltipW + 24 > windowW ? x - tooltipW - 8 : x + 16;
  const top = y + tooltipH + 16 > windowH ? y - tooltipH + 16 : y - 8;

  return (
    <div
      className="pointer-events-none fixed z-[100] w-64 rounded-xl border border-gray-200 bg-white/95 p-4 shadow-xl backdrop-blur-sm transition-opacity duration-150"
      style={{ left, top }}
    >
      {/* Header */}
      <div className="mb-2.5 flex items-center gap-2">
        <span
          className="inline-block h-3 w-3 rounded-full"
          style={{ backgroundColor: dotColor }}
        />
        <h4 className="text-sm font-bold text-gray-900">
          {p.county_name} County
        </h4>
      </div>

      {/* Party + Margin */}
      <div className="mb-3 flex items-baseline justify-between">
        <span className="text-xs font-medium text-gray-500">
          {getPartyLabel(margin)}
        </span>
        <span
          className="text-lg font-extrabold tabular-nums"
          style={{ color: dotColor }}
        >
          {formatMargin(margin)}
        </span>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 border-t border-gray-100 pt-2.5 text-xs">
        <Stat label="Std Dev" value={`${(p.margin_std * 100).toFixed(1)}%`} />
        <Stat
          label="Turnout"
          value={`${(p.avg_turnout_rate * 100).toFixed(1)}%`}
        />
        <Stat label="95% CI Low" value={`${(p.ci_low * 100).toFixed(1)}%`} />
        <Stat label="95% CI High" value={`${(p.ci_high * 100).toFixed(1)}%`} />
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-gray-400">{label}</span>
      <span className="ml-1 font-mono font-semibold text-gray-700">
        {value}
      </span>
    </div>
  );
}
