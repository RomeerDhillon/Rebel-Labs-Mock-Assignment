"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import mapData from "@/lib/nc-counties-svg.json";
import {
  getCountyPrediction,
  getCountyFillColor,
  getCountyHoverColor,
} from "@/lib/map-utils";
import MapTooltip from "./MapTooltip";

interface InteractiveNCMapProps {
  selectedFips: string | null;
  onSelect: (fips: string | null) => void;
  className?: string;
}

export default function InteractiveNCMap({
  selectedFips,
  onSelect,
  className = "",
}: InteractiveNCMapProps) {
  const [hoveredFips, setHoveredFips] = useState<string | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);

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
      onSelect(selectedFips === fips ? null : fips);
    },
    [selectedFips, onSelect],
  );

  const handleBackgroundClick = useCallback(
    (e: React.MouseEvent) => {
      const tag = (e.target as Element).tagName;
      if (tag === "svg" || tag === "rect") {
        onSelect(null);
      }
    },
    [onSelect],
  );

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        onSelect(null);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onSelect]);

  const hoveredPrediction = hoveredFips
    ? getCountyPrediction(hoveredFips)
    : null;

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <svg
        viewBox={mapData.viewBox}
        className="h-full w-full"
        onMouseMove={handleMouseMove}
        onClick={handleBackgroundClick}
        role="img"
        aria-label="Interactive map of North Carolina counties showing projected election results"
      >
        <rect x="0" y="0" width="900" height="400" fill="transparent" />

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
                isSelected
                  ? "#fbbf24"
                  : isHovered
                    ? "#ffffff"
                    : "rgba(255,255,255,0.35)"
              }
              strokeWidth={isSelected ? 2.5 : isHovered ? 1.8 : 0.5}
              className="cursor-pointer outline-none"
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
              tabIndex={0}
              role="button"
              aria-label={`${county.name} County`}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  handleCountyClick(county.fips);
                }
              }}
              onFocus={() => handleCountyEnter(county.fips)}
              onBlur={handleCountyLeave}
            />
          );
        })}
      </svg>

      {hoveredPrediction && (
        <MapTooltip
          prediction={hoveredPrediction}
          x={tooltipPos.x}
          y={tooltipPos.y}
        />
      )}
    </div>
  );
}
