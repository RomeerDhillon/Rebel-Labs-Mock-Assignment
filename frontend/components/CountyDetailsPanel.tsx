"use client";

import Link from "next/link";
import { CountyPrediction } from "@/lib/predictions";
import {
  formatMargin,
  getPartyLabel,
  getCountyFillColor,
} from "@/lib/map-utils";
import { getCountySlug } from "@/lib/county-slugs";

interface CountyDetailsPanelProps {
  prediction: CountyPrediction | null;
  onClose: () => void;
}

export default function CountyDetailsPanel({
  prediction,
  onClose,
}: CountyDetailsPanelProps) {
  if (!prediction) {
    return (
      <div className="flex h-full items-center justify-center rounded-xl border border-dashed border-gray-200 bg-white/50 p-8">
        <div className="text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-gray-100">
            <svg
              className="h-6 w-6 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15.042 21.672 13.684 16.6m0 0-2.51 2.225.569-9.47 5.227 7.917-3.286-.672ZM12 2.25V4.5m5.834.166-1.591 1.591M20.25 10.5H18M7.757 14.743l-1.59 1.59M6 10.5H3.75m4.007-4.243-1.59-1.59"
              />
            </svg>
          </div>
          <p className="text-sm font-medium text-gray-500">
            Click a county on the map
          </p>
          <p className="mt-1 text-xs text-gray-400">
            View detailed projections
          </p>
        </div>
      </div>
    );
  }

  const p = prediction;
  const margin = p.predicted_margin_r;
  const dotColor = getCountyFillColor(margin);
  const party = getPartyLabel(margin);
  const slug = getCountySlug(p.county_name);

  return (
    <>
      {/* Desktop Panel */}
      <div className="hidden lg:block h-full overflow-y-auto rounded-xl border border-gray-200 bg-white shadow-sm">
        <PanelContent
          p={p}
          margin={margin}
          dotColor={dotColor}
          party={party}
          slug={slug}
          onClose={onClose}
        />
      </div>

      {/* Mobile Bottom Drawer */}
      <div className="fixed inset-x-0 bottom-0 z-50 lg:hidden">
        <div className="mx-auto max-w-lg">
          <div className="rounded-t-2xl border border-b-0 border-gray-200 bg-white shadow-2xl">
            {/* Drag Handle */}
            <div className="flex justify-center pt-3 pb-1">
              <div className="h-1 w-10 rounded-full bg-gray-300" />
            </div>
            <div className="max-h-[60vh] overflow-y-auto">
              <PanelContent
                p={p}
                margin={margin}
                dotColor={dotColor}
                party={party}
                slug={slug}
                onClose={onClose}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/20 backdrop-blur-[2px] lg:hidden"
        onClick={onClose}
      />
    </>
  );
}

function PanelContent({
  p,
  margin,
  dotColor,
  party,
  slug,
  onClose,
}: {
  p: CountyPrediction;
  margin: number;
  dotColor: string;
  party: string;
  slug: string;
  onClose: () => void;
}) {
  return (
    <div className="p-5">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <span
            className="inline-block h-4 w-4 rounded-full shadow-sm"
            style={{ backgroundColor: dotColor }}
          />
          <div>
            <h3 className="text-base font-bold text-gray-900">
              {p.county_name}
            </h3>
            <p className="text-xs text-gray-500">{party}</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
          aria-label="Close panel"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M6 18 18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      {/* Margin Headline */}
      <div className="mt-4 rounded-lg bg-gray-50 p-3">
        <p className="text-xs font-medium text-gray-400">Predicted Margin</p>
        <p
          className="mt-0.5 text-2xl font-extrabold tabular-nums"
          style={{ color: dotColor }}
        >
          {formatMargin(margin)}
        </p>
      </div>

      {/* Margin Bar */}
      <div className="mt-4">
        <div className="flex items-center justify-between text-[10px] text-gray-400 mb-1">
          <span>D+100%</span>
          <span>Even</span>
          <span>R+100%</span>
        </div>
        <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-gray-100">
          <div
            className="absolute left-0 top-0 h-full bg-gradient-to-r from-blue-700 to-blue-400"
            style={{ width: "50%" }}
          />
          <div
            className="absolute right-0 top-0 h-full bg-gradient-to-r from-red-400 to-red-700"
            style={{ width: "50%" }}
          />
          <div
            className="absolute top-[-2px] h-[calc(100%+4px)] w-1 rounded-full bg-gray-900 shadow"
            style={{ left: `${((margin + 1) / 2) * 100}%` }}
          />
        </div>
      </div>

      {/* Stats */}
      <div className="mt-4 grid grid-cols-2 gap-3">
        <StatBlock
          label="Std Deviation"
          value={`\u00B1${(p.margin_std * 100).toFixed(1)}%`}
        />
        <StatBlock
          label="Avg Turnout"
          value={`${(p.avg_turnout_rate * 100).toFixed(1)}%`}
        />
        <StatBlock
          label="95% CI Low"
          value={`${(p.ci_low * 100).toFixed(1)}%`}
        />
        <StatBlock
          label="95% CI High"
          value={`${(p.ci_high * 100).toFixed(1)}%`}
        />
      </div>

      {/* Link to full county page */}
      <Link
        href={`/county/${slug}`}
        className="mt-4 block rounded-lg border border-gray-200 bg-gray-50 px-4 py-2.5 text-center text-xs font-semibold text-gray-600 hover:bg-gray-100 transition-colors"
      >
        View Full County Details &rarr;
      </Link>
    </div>
  );
}

function StatBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-gray-50 px-3 py-2">
      <p className="text-[10px] font-medium uppercase tracking-wider text-gray-400">
        {label}
      </p>
      <p className="mt-0.5 text-sm font-bold tabular-nums text-gray-700">
        {value}
      </p>
    </div>
  );
}
