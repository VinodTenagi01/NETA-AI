/**
 * MapLayerControls — sidebar panel for toggling map layers
 * and switching choropleth data layers.
 */

import React from "react";
import type { DataLayerType, MapLayerState } from "./ConstituencyMap";

interface Props {
  layers: MapLayerState;
  onChange: <K extends keyof MapLayerState>(key: K, value: MapLayerState[K]) => void;
  boothCount: number;
  loading: boolean;
  selectedZone?: string;
  onClearZone: () => void;
}

const DATA_LAYERS: { value: DataLayerType; label: string }[] = [
  { value: "risk", label: "Risk Score" },
  { value: "health", label: "Health Score" },
  { value: "contact_rate", label: "Contact Rate" },
  { value: "voter_density", label: "Voter Density" },
  { value: "sentiment", label: "Sentiment" },
];

export const MapLayerControls: React.FC<Props> = ({
  layers,
  onChange,
  boothCount,
  loading,
  selectedZone,
  onClearZone,
}) => {
  return (
    <div className="absolute top-4 right-4 z-[1000] w-56 bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-3 py-2 bg-blue-700 text-white">
        <p className="text-xs font-bold">MAP LAYERS</p>
        <p className="text-[10px] text-blue-200">Serilingampally AC-52</p>
      </div>

      <div className="px-3 py-2 space-y-3">
        {/* Booth count */}
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Booths visible</span>
          <span className="font-semibold text-gray-800">
            {loading ? "…" : boothCount}
          </span>
        </div>

        {/* Zone filter */}
        {selectedZone && (
          <div className="flex items-center justify-between bg-blue-50 text-blue-800 text-xs px-2 py-1 rounded-lg">
            <span>Zone: <b>{selectedZone}</b></span>
            <button onClick={onClearZone} className="ml-2 text-blue-500 hover:text-blue-700">
              ✕ Clear
            </button>
          </div>
        )}

        {/* Boundary toggles */}
        <div className="space-y-1.5">
          <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">
            Layers
          </p>
          {[
            { key: "showConstituencyBoundary" as const, label: "Constituency Boundary" },
            { key: "showZones" as const, label: "Zone Boundaries" },
            { key: "showBoothMarkers" as const, label: "Booth Markers" },
            { key: "showWorkerPositions" as const, label: "Worker Positions" },
          ].map(({ key, label }) => (
            <label key={key} className="flex items-center gap-2 text-xs cursor-pointer">
              <input
                type="checkbox"
                checked={layers[key] as boolean}
                onChange={(e) => onChange(key, e.target.checked as MapLayerState[typeof key])}
                className="rounded text-blue-600"
              />
              <span className="text-gray-700">{label}</span>
            </label>
          ))}
        </div>

        {/* Data layer selector */}
        <div className="space-y-1.5">
          <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">
            Color Layer
          </p>
          {DATA_LAYERS.map(({ value, label }) => (
            <label key={value} className="flex items-center gap-2 text-xs cursor-pointer">
              <input
                type="radio"
                name="dataLayer"
                value={value}
                checked={layers.dataLayer === value}
                onChange={() => onChange("dataLayer", value)}
                className="text-blue-600"
              />
              <span className="text-gray-700">{label}</span>
            </label>
          ))}
        </div>

        {/* Legend */}
        <div className="space-y-1">
          <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">
            Risk Legend
          </p>
          {[
            { color: "#22c55e", label: "0–35 HEALTHY" },
            { color: "#eab308", label: "36–60 WATCH" },
            { color: "#f97316", label: "61–80 AT-RISK" },
            { color: "#ef4444", label: "81–100 CRITICAL" },
          ].map(({ color, label }) => (
            <div key={label} className="flex items-center gap-2 text-xs">
              <div
                className="w-3 h-3 rounded-full border border-white shadow-sm"
                style={{ backgroundColor: color }}
              />
              <span className="text-gray-600">{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
