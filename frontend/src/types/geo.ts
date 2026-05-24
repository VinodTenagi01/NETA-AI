// GeoJSON + domain types for the mapping module

export interface GeoJSONPoint {
  type: "Point";
  coordinates: [number, number]; // [lng, lat]
}

export interface GeoJSONPolygon {
  type: "Polygon";
  coordinates: number[][][];
}

export interface GeoJSONFeature<P = Record<string, unknown>> {
  type: "Feature";
  properties: P;
  geometry: GeoJSONPoint | GeoJSONPolygon | null;
}

export interface GeoJSONFeatureCollection<P = Record<string, unknown>> {
  type: "FeatureCollection";
  features: GeoJSONFeature<P>[];
  metadata?: Record<string, unknown>;
}

// ---------- Booth ----------

export interface BoothProperties {
  id: string;
  booth_number: string;
  booth_name: string;
  zone_code: string;
  zone_name: string;
  total_voters: number;
  female_voters: number;
  male_voters: number;
  contact_rate: number;
  health_score: number;
  risk_score: number;
  swing_booth: boolean;
  last_report_hours: number | null;
  color: string;
  layer: DataLayerType;
  marker_size: number;
}

export interface BoothDetailPopup {
  id: string;
  booth_number: string;
  booth_name: string;
  zone_code: string;
  zone_name: string;
  total_voters: number;
  contacted: number;
  contact_pct: number;
  health_score: number;
  risk_score: number;
  volunteer_count: number;
  last_report_hours: number | null;
  open_escalations: number;
  mood: string | null;
  assigned_commander_name: string | null;
}

export interface BoothGeoJSONResponse {
  geojson: GeoJSONFeatureCollection<BoothProperties>;
  total: number;
  bounds: {
    min_lat: number;
    max_lat: number;
    min_lng: number;
    max_lng: number;
  };
}

// ---------- Zone ----------

export interface ZoneProperties {
  zone_code: string;
  zone_name: string;
  key_areas: string;
  approx_booth_count: number;
  approx_voter_count: number;
  contact_rate_pct: number;
  avg_health_score: number;
  open_escalations: number;
  active_workers: number;
  booth_count: number;
  color: string;
}

export type DataLayerType = "risk" | "health" | "contact_rate" | "voter_density" | "sentiment";

// ---------- Demographics ----------

export type DemographicOverlayType =
  | "voter_density"
  | "sc_st"
  | "youth"
  | "literacy"
  | "gender_ratio";
