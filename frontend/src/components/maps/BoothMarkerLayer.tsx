/**
 * BoothMarkerLayer — renders 315 booth points on the map.
 * Each marker is color-coded by the active data layer.
 * Click → booth detail popup.
 */

import L from "leaflet";
import React, { useEffect, useRef } from "react";
import { useMap } from "react-leaflet";
import type { BoothGeoJSONResponse, BoothProperties } from "../../types/geo";

interface Props {
  geojson: BoothGeoJSONResponse["geojson"];
  onBoothClick: (boothId: string) => void;
  selectedBoothId: string | null;
}

function makeCircleIcon(color: string, size: number, isSelected: boolean): L.DivIcon {
  const borderColor = isSelected ? "#1e40af" : "#fff";
  const borderWidth = isSelected ? 3 : 1.5;
  const s = isSelected ? size + 4 : size;
  return L.divIcon({
    className: "",
    iconSize: [s, s],
    iconAnchor: [s / 2, s / 2],
    html: `<div style="
      width:${s}px;height:${s}px;
      border-radius:50%;
      background:${color};
      border:${borderWidth}px solid ${borderColor};
      box-shadow:0 1px 3px rgba(0,0,0,0.4);
      transition:transform 0.15s;
    "></div>`,
  });
}

export const BoothMarkerLayer: React.FC<Props> = ({
  geojson,
  onBoothClick,
  selectedBoothId,
}) => {
  const map = useMap();
  const layerGroupRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!map) return;

    // Clear previous markers
    if (layerGroupRef.current) {
      layerGroupRef.current.clearLayers();
    } else {
      layerGroupRef.current = L.layerGroup().addTo(map);
    }

    const lg = layerGroupRef.current;

    geojson.features.forEach((feature) => {
      const props = feature.properties as BoothProperties;
      if (!feature.geometry || feature.geometry.type !== "Point") return;

      const [lng, lat] = feature.geometry.coordinates;
      const isSelected = props.id === selectedBoothId;
      const icon = makeCircleIcon(props.color, props.marker_size, isSelected);

      const marker = L.marker([lat, lng], { icon });

      // Tooltip (hover)
      marker.bindTooltip(
        `<div class="text-xs font-semibold">
          <div>Booth ${props.booth_number}</div>
          <div class="text-gray-500">${props.booth_name}</div>
          <div>Risk: ${props.risk_score} | Health: ${props.health_score}</div>
          ${props.swing_booth ? '<div class="text-yellow-600">⚡ SWING BOOTH</div>' : ""}
        </div>`,
        { direction: "top", className: "neta-tooltip" }
      );

      marker.on("click", () => onBoothClick(props.id));
      lg.addLayer(marker);
    });

    return () => {
      if (layerGroupRef.current) {
        layerGroupRef.current.clearLayers();
      }
    };
  }, [map, geojson, selectedBoothId, onBoothClick]);

  return null;
};
