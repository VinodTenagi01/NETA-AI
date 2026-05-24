/**
 * GeoJSON Mapping API client.
 * All calls go to /api/v1/geo/ and are served by the FastAPI backend.
 */

import type {
  BoothDetailPopup,
  BoothGeoJSONResponse,
  DataLayerType,
  DemographicOverlayType,
  GeoJSONFeatureCollection,
  ZoneProperties,
} from "../types/geo";

const BASE = "/api/v1/geo";

async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const geoApi = {
  /** Constituency outer boundary GeoJSON */
  getConstituencyBoundary: (acNumber = "52") =>
    apiFetch<GeoJSONFeatureCollection>(`${BASE}/constituency/${acNumber}/boundary`),

  /** Zone overlay with live KPI attributes */
  getZoneOverlay: (constituencyId?: string) => {
    const params = constituencyId ? `?constituency_id=${constituencyId}` : "";
    return apiFetch<{ geojson: GeoJSONFeatureCollection<ZoneProperties>; summary: Record<string, unknown> }>(
      `${BASE}/zones${params}`
    );
  },

  /** Booth points GeoJSON for a given data layer */
  getBoothsGeoJSON: (params: {
    constituencyId?: string;
    zoneCode?: string;
    layer?: DataLayerType;
  }): Promise<BoothGeoJSONResponse> => {
    const qs = new URLSearchParams();
    if (params.constituencyId) qs.set("constituency_id", params.constituencyId);
    if (params.zoneCode) qs.set("zone_code", params.zoneCode);
    if (params.layer) qs.set("layer", params.layer);
    return apiFetch<BoothGeoJSONResponse>(`${BASE}/booths?${qs}`);
  },

  /** Booth popup card data */
  getBoothPopup: (boothId: string) =>
    apiFetch<BoothDetailPopup>(`${BASE}/booths/${boothId}/popup`),

  /** Booth catchment polygon */
  getBoothCatchment: (boothId: string) =>
    apiFetch<GeoJSONFeatureCollection>(`${BASE}/booths/${boothId}/catchment`),

  /** Demographic overlay */
  getDemographicOverlay: (overlayType: DemographicOverlayType, constituencyId: string) =>
    apiFetch<GeoJSONFeatureCollection>(
      `${BASE}/demographics/${overlayType}?constituency_id=${constituencyId}`
    ),

  /** Upload ECI booth CSV */
  importBoothsCsv: async (
    file: File,
    constituencyId: string,
    dryRun = false
  ) => {
    const fd = new FormData();
    fd.append("file", file);
    return apiFetch<Record<string, unknown>>(
      `${BASE}/import/booths?constituency_id=${constituencyId}&dry_run=${dryRun}`,
      { method: "POST", headers: {}, body: fd }
    );
  },

  /** Upload ECI voter roll CSV */
  importVotersCsv: async (
    file: File,
    constituencyId: string,
    dryRun = false
  ) => {
    const fd = new FormData();
    fd.append("file", file);
    return apiFetch<Record<string, unknown>>(
      `${BASE}/import/voters?constituency_id=${constituencyId}&dry_run=${dryRun}`,
      { method: "POST", headers: {}, body: fd }
    );
  },

  /** Upload GeoJSON layer (boundary/catchments) */
  importGeoJSONLayer: async (
    file: File,
    layerType: "constituency_boundary" | "zone_boundaries" | "booth_catchments",
    constituencyId: string
  ) => {
    const fd = new FormData();
    fd.append("file", file);
    return apiFetch<Record<string, unknown>>(
      `${BASE}/import/geojson?layer_type=${layerType}&constituency_id=${constituencyId}`,
      { method: "POST", headers: {}, body: fd }
    );
  },
};
