/**
 * React Query hooks for GeoJSON map data.
 * Uses stale-while-revalidate for KPI freshness.
 */

import { useQuery } from "@tanstack/react-query";
import type { DataLayerType, DemographicOverlayType } from "../types/geo";
import { geoApi } from "../services/geoApi";

const CONSTITUENCY_ID = "11111111-0052-4000-8000-000000000001";

export function useConstituencyBoundary(acNumber = "52") {
  return useQuery({
    queryKey: ["geo", "boundary", acNumber],
    queryFn: () => geoApi.getConstituencyBoundary(acNumber),
    staleTime: 24 * 60 * 60 * 1000, // boundary rarely changes
  });
}

export function useZoneOverlay() {
  return useQuery({
    queryKey: ["geo", "zones", CONSTITUENCY_ID],
    queryFn: () => geoApi.getZoneOverlay(CONSTITUENCY_ID),
    staleTime: 60 * 1000,         // refresh every 60s
    refetchInterval: 60 * 1000,
  });
}

export function useBoothsGeoJSON(
  layer: DataLayerType = "risk",
  zoneCode?: string
) {
  return useQuery({
    queryKey: ["geo", "booths", CONSTITUENCY_ID, layer, zoneCode],
    queryFn: () => geoApi.getBoothsGeoJSON({ constituencyId: CONSTITUENCY_ID, layer, zoneCode }),
    staleTime: 30 * 1000,
    refetchInterval: 30 * 1000,
  });
}

export function useBoothPopup(boothId: string | null) {
  return useQuery({
    queryKey: ["geo", "booth-popup", boothId],
    queryFn: () => geoApi.getBoothPopup(boothId!),
    enabled: !!boothId,
    staleTime: 30 * 1000,
  });
}

export function useDemographicOverlay(
  overlayType: DemographicOverlayType,
  enabled = false
) {
  return useQuery({
    queryKey: ["geo", "demographics", overlayType, CONSTITUENCY_ID],
    queryFn: () => geoApi.getDemographicOverlay(overlayType, CONSTITUENCY_ID),
    enabled,
    staleTime: 60 * 60 * 1000, // demographics rarely change
  });
}
