/**
 * ZoneOverlayLayer — renders Z-01 through Z-07 zone polygons.
 * Click to filter booth markers by zone.
 */

import L from "leaflet";
import React, { useEffect, useRef } from "react";
import { useMap } from "react-leaflet";
import type { GeoJSONFeatureCollection, ZoneProperties } from "../../types/geo";

interface Props {
  geojson: GeoJSONFeatureCollection<ZoneProperties>;
  onZoneClick: (zoneCode: string) => void;
  selectedZone?: string;
}

export const ZoneOverlayLayer: React.FC<Props> = ({
  geojson,
  onZoneClick,
  selectedZone,
}) => {
  const map = useMap();
  const layerRef = useRef<L.GeoJSON | null>(null);

  useEffect(() => {
    if (!map) return;
    if (layerRef.current) {
      map.removeLayer(layerRef.current);
    }

    layerRef.current = L.geoJSON(geojson as L.GeoJsonObject, {
      style: (feature) => {
        const code = feature?.properties?.zone_code;
        const color = feature?.properties?.color ?? "#6b7280";
        const isSelected = code === selectedZone;
        return {
          color,
          weight: isSelected ? 2.5 : 1.5,
          opacity: 0.8,
          fillColor: color,
          fillOpacity: isSelected ? 0.25 : 0.10,
        };
      },
      onEachFeature: (feature, layer) => {
        const props = feature.properties as ZoneProperties;

        layer.bindTooltip(
          `<div class="text-xs font-semibold">
            <div>${props.zone_code} — ${props.zone_name}</div>
            <div class="text-gray-500">${props.key_areas}</div>
            <div class="mt-1 grid grid-cols-2 gap-x-3">
              <span>Booths: <b>${props.booth_count || props.approx_booth_count}</b></span>
              <span>Health: <b>${props.avg_health_score?.toFixed(0) ?? "—"}</b></span>
              <span>Contact: <b>${props.contact_rate_pct?.toFixed(1) ?? 0}%</b></span>
              <span>Escalations: <b>${props.open_escalations ?? 0}</b></span>
            </div>
          </div>`,
          { sticky: true, className: "neta-tooltip" }
        );

        layer.on("click", () => onZoneClick(props.zone_code));
      },
    }).addTo(map);

    return () => {
      if (layerRef.current) {
        map.removeLayer(layerRef.current);
      }
    };
  }, [map, geojson, selectedZone, onZoneClick]);

  return null;
};
