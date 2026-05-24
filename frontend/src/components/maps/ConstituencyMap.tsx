/**
 * ConstituencyMap — Leaflet.js map container for Serilingampally AC-52.
 *
 * Layer hierarchy (PRD Section 22.2):
 *   Base: OpenStreetMap
 *   Group 1 (Constituency Layers): boundary, wards, zones
 *   Group 2 (Data Layers): choropleth — health/risk/contact/density/sentiment
 *   Marker Layer: booth points
 *   Optional: field workers, opposition activity
 */

import React, { useCallback, useState } from "react";
import {
  MapContainer,
  TileLayer,
  ZoomControl,
  useMap,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";

import type { DataLayerType, DemographicOverlayType } from "../../types/geo";
import {
  useBoothPopup,
  useBoothsGeoJSON,
  useConstituencyBoundary,
  useDemographicOverlay,
  useZoneOverlay,
} from "../../hooks/useConstituencyData";
import { BoothMarkerLayer } from "./BoothMarkerLayer";
import { BoothPopupCard } from "./BoothPopupCard";
import { ConstituencyBoundaryLayer } from "./ConstituencyBoundaryLayer";
import { ZoneOverlayLayer } from "./ZoneOverlayLayer";
import { MapLayerControls } from "./MapLayerControls";

// Serilingampally AC-52 center and default zoom
const AC52_CENTER: [number, number] = [17.470, 78.362];
const AC52_ZOOM = 13;

export interface MapLayerState {
  showConstituencyBoundary: boolean;
  showZones: boolean;
  showBoothMarkers: boolean;
  showWorkerPositions: boolean;
  showOppositionActivity: boolean;
  dataLayer: DataLayerType;
  demographicOverlay: DemographicOverlayType | null;
}

const DEFAULT_LAYERS: MapLayerState = {
  showConstituencyBoundary: true,
  showZones: false,
  showBoothMarkers: true,
  showWorkerPositions: false,
  showOppositionActivity: false,
  dataLayer: "risk",
  demographicOverlay: null,
};

export const ConstituencyMap: React.FC = () => {
  const [layers, setLayers] = useState<MapLayerState>(DEFAULT_LAYERS);
  const [selectedBoothId, setSelectedBoothId] = useState<string | null>(null);
  const [selectedZone, setSelectedZone] = useState<string | undefined>(undefined);

  const { data: boundaryData } = useConstituencyBoundary();
  const { data: zoneData } = useZoneOverlay();
  const { data: boothData, isLoading: boothsLoading } = useBoothsGeoJSON(
    layers.dataLayer,
    selectedZone
  );
  const { data: popupData } = useBoothPopup(selectedBoothId);

  const updateLayer = useCallback(
    <K extends keyof MapLayerState>(key: K, value: MapLayerState[K]) => {
      setLayers((prev) => ({ ...prev, [key]: value }));
    },
    []
  );

  return (
    <div className="relative w-full h-full">
      <MapContainer
        center={AC52_CENTER}
        zoom={AC52_ZOOM}
        zoomControl={false}
        className="w-full h-full z-0"
        preferCanvas
      >
        <ZoomControl position="bottomright" />

        {/* Base tile layer */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={19}
        />

        {/* Constituency boundary */}
        {layers.showConstituencyBoundary && boundaryData && (
          <ConstituencyBoundaryLayer geojson={boundaryData} />
        )}

        {/* Zone overlays */}
        {layers.showZones && zoneData && (
          <ZoneOverlayLayer
            geojson={zoneData.geojson}
            onZoneClick={(code) =>
              setSelectedZone((prev) => (prev === code ? undefined : code))
            }
            selectedZone={selectedZone}
          />
        )}

        {/* Booth markers */}
        {layers.showBoothMarkers && boothData && (
          <BoothMarkerLayer
            geojson={boothData.geojson}
            onBoothClick={setSelectedBoothId}
            selectedBoothId={selectedBoothId}
          />
        )}
      </MapContainer>

      {/* Layer control panel */}
      <MapLayerControls
        layers={layers}
        onChange={updateLayer}
        boothCount={boothData?.total ?? 0}
        loading={boothsLoading}
        selectedZone={selectedZone}
        onClearZone={() => setSelectedZone(undefined)}
      />

      {/* Booth detail popup */}
      {selectedBoothId && popupData && (
        <BoothPopupCard
          data={popupData}
          onClose={() => setSelectedBoothId(null)}
        />
      )}
    </div>
  );
};

export default ConstituencyMap;
