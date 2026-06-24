"use client";

import { useState, useCallback } from "react";
import { getCountyPrediction } from "@/lib/map-utils";
import InteractiveNCMap from "./InteractiveNCMap";
import CountyDetailsPanel from "./CountyDetailsPanel";
import MapLegend from "./MapLegend";

export default function DashboardPage() {
  const [selectedFips, setSelectedFips] = useState<string | null>(null);

  const selectedPrediction = selectedFips
    ? (getCountyPrediction(selectedFips) ?? null)
    : null;

  const handleSelect = useCallback((fips: string | null) => {
    setSelectedFips(fips);
  }, []);

  const handleClose = useCallback(() => {
    setSelectedFips(null);
  }, []);

  return (
    <section>
      {/* Map + Panel Layout */}
      <div className="flex flex-col gap-4 lg:flex-row">
        {/* Map Container */}
        <div className="flex-1 min-w-0">
          <div className="overflow-hidden rounded-2xl border border-gray-200 bg-gradient-to-b from-slate-50 to-slate-100 shadow-sm">
            <InteractiveNCMap
              selectedFips={selectedFips}
              onSelect={handleSelect}
              className="aspect-[9/4]"
            />
          </div>
          <div className="mt-3">
            <MapLegend />
          </div>
        </div>

        {/* Details Panel (desktop) */}
        <div className="hidden lg:block w-80 flex-shrink-0">
          <CountyDetailsPanel
            prediction={selectedPrediction}
            onClose={handleClose}
          />
        </div>
      </div>

      {/* Mobile drawer (rendered by CountyDetailsPanel internally) */}
      {selectedPrediction && (
        <div className="lg:hidden">
          <CountyDetailsPanel
            prediction={selectedPrediction}
            onClose={handleClose}
          />
        </div>
      )}
    </section>
  );
}
