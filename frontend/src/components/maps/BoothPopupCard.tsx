/**
 * BoothPopupCard — fixed-position popup card matching PRD Section 22.3 layout.
 * Displayed when a booth marker is clicked.
 */

import React from "react";
import type { BoothDetailPopup } from "../../types/geo";

interface Props {
  data: BoothDetailPopup;
  onClose: () => void;
}

const RISK_BADGE = (score: number) => {
  if (score <= 35) return "bg-green-100 text-green-800";
  if (score <= 60) return "bg-yellow-100 text-yellow-800";
  if (score <= 80) return "bg-orange-100 text-orange-800";
  return "bg-red-100 text-red-800";
};

const RISK_LABEL = (score: number) => {
  if (score <= 35) return "HEALTHY";
  if (score <= 60) return "WATCH";
  if (score <= 80) return "AT-RISK";
  return "CRITICAL";
};

const MOOD_COLOR: Record<string, string> = {
  POSITIVE: "text-green-600",
  NEUTRAL: "text-gray-500",
  NEGATIVE: "text-red-600",
  MIXED: "text-yellow-600",
};

export const BoothPopupCard: React.FC<Props> = ({ data, onClose }) => {
  const contactPct = data.contact_pct.toFixed(1);
  const lastReportText =
    data.last_report_hours == null
      ? "No reports yet"
      : data.last_report_hours < 1
      ? "< 1h ago"
      : `${Math.floor(data.last_report_hours)}h ago`;

  return (
    <div className="absolute bottom-6 left-4 z-[1000] w-72 bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="flex items-start justify-between px-4 py-3 bg-gray-50 border-b border-gray-200">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-gray-900">
              Booth {data.booth_number}
            </span>
            {data.open_escalations > 0 && (
              <span className="text-xs bg-red-500 text-white px-1.5 py-0.5 rounded-full">
                {data.open_escalations} ESC
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500 mt-0.5">{data.booth_name}</p>
          <p className="text-xs text-gray-400">
            {data.zone_code} · {data.zone_name}
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 text-lg leading-none mt-0.5"
          aria-label="Close"
        >
          ×
        </button>
      </div>

      {/* Body */}
      <div className="px-4 py-3 space-y-2">
        {/* Voter stats */}
        <div className="grid grid-cols-2 gap-x-4 text-xs">
          <div>
            <span className="text-gray-500">Total Voters</span>
            <p className="font-semibold text-gray-900">
              {data.total_voters.toLocaleString()}
            </p>
          </div>
          <div>
            <span className="text-gray-500">Contacted</span>
            <p className="font-semibold text-gray-900">
              {data.contacted.toLocaleString()}{" "}
              <span className="text-gray-400">({contactPct}%)</span>
            </p>
          </div>
        </div>

        {/* Scores */}
        <div className="grid grid-cols-2 gap-x-4 text-xs">
          <div>
            <span className="text-gray-500">Health Score</span>
            <p className="font-semibold text-gray-900">
              {data.health_score.toFixed(0)}/100
            </p>
          </div>
          <div>
            <span className="text-gray-500">Risk Score</span>
            <p>
              <span
                className={`text-xs font-semibold px-1.5 py-0.5 rounded ${RISK_BADGE(data.risk_score)}`}
              >
                {data.risk_score.toFixed(0)} · {RISK_LABEL(data.risk_score)}
              </span>
            </p>
          </div>
        </div>

        {/* Volunteers */}
        <div className="text-xs">
          <span className="text-gray-500">Volunteers</span>
          <span className="ml-2 font-semibold text-gray-900">
            {data.volunteer_count}
            {data.volunteer_count < 2 && (
              <span className="ml-1 text-orange-500">⚠ Coverage gap</span>
            )}
          </span>
        </div>
      </div>

      {/* Divider */}
      <div className="border-t border-gray-100 mx-4" />

      {/* Meta */}
      <div className="px-4 py-3 grid grid-cols-3 gap-x-2 text-xs">
        <div>
          <span className="text-gray-400">Last Report</span>
          <p className="text-gray-700 font-medium mt-0.5">{lastReportText}</p>
        </div>
        <div>
          <span className="text-gray-400">Escalations</span>
          <p
            className={`font-medium mt-0.5 ${
              data.open_escalations > 0 ? "text-red-600" : "text-gray-700"
            }`}
          >
            {data.open_escalations}
          </p>
        </div>
        <div>
          <span className="text-gray-400">Mood</span>
          <p
            className={`font-medium mt-0.5 ${
              data.mood ? MOOD_COLOR[data.mood] ?? "text-gray-700" : "text-gray-400"
            }`}
          >
            {data.mood ?? "—"}
          </p>
        </div>
      </div>

      {/* Commander */}
      {data.assigned_commander_name && (
        <>
          <div className="border-t border-gray-100 mx-4" />
          <div className="px-4 py-2 text-xs text-gray-500">
            Commander:{" "}
            <span className="text-gray-800 font-medium">
              {data.assigned_commander_name}
            </span>
          </div>
        </>
      )}

      {/* Actions */}
      <div className="px-4 pb-3 flex gap-2">
        <a
          href={`/booths/${data.id}`}
          className="flex-1 text-center text-xs py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          View Full Booth
        </a>
        <a
          href={`/reports/new?booth=${data.id}`}
          className="flex-1 text-center text-xs py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
        >
          Add Report
        </a>
      </div>
    </div>
  );
};
