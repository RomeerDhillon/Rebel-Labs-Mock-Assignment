"use client";

import { useState, useCallback, useRef } from "react";
import mapData from "@/lib/nc-counties-svg.json";
import {
  getCountyPrediction,
  getCountyFillColor,
  getCountyHoverColor,
  formatMargin,
  getPartyLabel,
} from "@/lib/map-utils";
import { CountyPrediction } from "@/lib/predictions";
import MapTooltip from "./MapTooltip";
import MapLegend from "./MapLegend";

interface CountyMapProps {
  onCountySelect?: (prediction: CountyPrediction | null) => void;
}

export default function CountyMap({ onCountySelect }: CountyMapProps) {
  const [hoveredFips, setHoveredFips] = useState<string | null>(null);
  const [selectedFips, setSelectedFips] = useState<string | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const svgRef = useRef<SVGSVGElement>(null);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    setTooltipPos({ x: e.clientX, y: e.clientY });
  }, []);

  const handleCountyEnter = useCallback((fips: string) => {
    setHoveredFips(fips);
  }, []);

  const handleCountyLeave = useCallback(() => {
    setHoveredFips(null);
  }, []);

  const handleCountyClick = useCallback(
    (fips: string) => {
      const next = selectedFips === fips ? null : fips;
      setSelectedFips(next);
      if (onCountySelect) {
        onCountySelect(next ? (getCountyPrediction(next) ?? null) : null);
      }
    },
    [selectedFips, onCountySelect],
  );

  const handleSvgClick = useCallback(
    (e: React.MouseEvent) => {
      if (
        (e.target as Element).tagName === "svg" ||
        (e.target as Element).tagName === "rect"
      ) {
        setSelectedFips(null);
        if (onCountySelect) onCountySelect(null);
      }
    },
    [onCountySelect],
  );

  const hoveredPrediction = hoveredFips
    ? getCountyPrediction(hoveredFips)
    : null;

  const selectedPrediction = selectedFips
    ? getCountyPrediction(selectedFips)
    : null;

  return (
    <div className="space-y-4">
      {/* Map Container */}
      <div className="relative overflow-hidden rounded-2xl border border-gray-200 bg-gradient-to-b from-gray-50 to-gray-100 shadow-sm">
        <svg
          ref={svgRef}
          viewBox={mapData.viewBox}
          className="w-full h-auto"
          style={{ maxHeight: "65vh" }}
          onMouseMove={handleMouseMove}
          onClick={handleSvgClick}
        >
          {/* Background */}
          <rect x="0" y="0" width="900" height="400" fill="transparent" />

          {/* County Paths */}
          {mapData.counties.map((county) => {
            const prediction = getCountyPrediction(county.fips);
            const margin = prediction?.predicted_margin_r ?? 0;
            const isHovered = hoveredFips === county.fips;
            const isSelected = selectedFips === county.fips;

            const fillColor =
              isHovered || isSelected
                ? getCountyHoverColor(margin)
                : getCountyFillColor(margin);

            return (
              <path
                key={county.fips}
                d={county.d}
                fill={fillColor}
                stroke={
                  isSelected ? "#f59e0b" : isHovered ? "#ffffff" : "#ffffff80"
                }
                strokeWidth={isSelected ? 2.5 : isHovered ? 1.8 : 0.5}
                className="cursor-pointer"
                style={{
                  transition:
                    "fill 200ms ease, stroke 200ms ease, stroke-width 200ms ease",
                }}
                onMouseEnter={() => handleCountyEnter(county.fips)}
                onMouseLeave={handleCountyLeave}
                onClick={(e) => {
                  e.stopPropagation();
                  handleCountyClick(county.fips);
                }}
              />
            );
          })}
        </svg>

        {/* Hover Tooltip */}
        {hoveredPrediction && (
          <MapTooltip
            prediction={hoveredPrediction}
            x={tooltipPos.x}
            y={tooltipPos.y}
          />
        )}
      </div>

      {/* Selected County Info Card */}
      {selectedPrediction && (
        <SelectedCountyCard
          prediction={selectedPrediction}
          onClear={() => {
            setSelectedFips(null);
            if (onCountySelect) onCountySelect(null);
          }}
        />
      )}

      {/* Legend */}
      <MapLegend />
    </div>
  );
}

function SelectedCountyCard({
  prediction,
  onClear,
}: {
  prediction: CountyPrediction;
  onClear: () => void;
}) {
  const p = prediction;
  const margin = p.predicted_margin_r;
  const dotColor = getCountyFillColor(margin);

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-md transition-all duration-300">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <span
            className="inline-block h-4 w-4 rounded-full"
            style={{ backgroundColor: dotColor }}
          />
          <div>
            <h3 className="text-lg font-bold text-gray-900">
              {p.county_name} County
            </h3>
            <p className="text-sm text-gray-500">{getPartyLabel(margin)}</p>
          </div>
        </div>
        <button
          onClick={onClear}
          className="rounded-lg px-3 py-1 text-xs font-medium text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
        >
          Clear
        </button>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard
          label="Predicted Margin"
          value={formatMargin(margin)}
          color={dotColor}
        />
        <StatCard
          label="Std Deviation"
          value={`${(p.margin_std * 100).toFixed(1)}%`}
        />
        <StatCard
          label="95% Confidence"
          value={`[${(p.ci_low * 100).toFixed(1)}, ${(p.ci_high * 100).toFixed(1)}]`}
        />
        <StatCard
          label="Avg Turnout"
          value={`${(p.avg_turnout_rate * 100).toFixed(1)}%`}
        />
      </div>

      {/* Margin Bar */}
      <div className="mt-4">
        <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
          <span>D+100%</span>
          <span>Even</span>
          <span>R+100%</span>
        </div>
        <div className="relative h-3 w-full overflow-hidden rounded-full bg-gray-100">
          {/* Blue half */}
          <div
            className="absolute left-0 top-0 h-full bg-gradient-to-r from-blue-700 to-blue-400"
            style={{ width: "50%" }}
          />
          {/* Red half */}
          <div
            className="absolute right-0 top-0 h-full bg-gradient-to-r from-red-400 to-red-700"
            style={{ width: "50%" }}
          />
          {/* Marker */}
          <div
            className="absolute top-[-2px] h-[calc(100%+4px)] w-1 rounded-full bg-gray-900 shadow"
            style={{ left: `${((margin + 1) / 2) * 100}%` }}
          />
        </div>
      </div>
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
    <div className="rounded-lg bg-gray-50 px-3 py-2">
      <p className="text-xs text-gray-400">{label}</p>
      <p
        className="mt-0.5 text-sm font-bold tabular-nums"
        style={color ? { color } : undefined}
      >
        {value}
      </p>
    </div>
  );
}
