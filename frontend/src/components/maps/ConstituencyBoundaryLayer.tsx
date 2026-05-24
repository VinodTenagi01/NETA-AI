/**
 * ConstituencyBoundaryLayer — renders AC-52 outer boundary polygon.
 * Always visible; serves as the map frame of reference.
 */

import L from "leaflet";
import React, { useEffect, useRef } from "react";
import { useMap } from "react-leaflet";
import type { GeoJSONFeatureCollection } from "../../types/geo";

interface Props {
  geojson: GeoJSONFeatureCollection;
}

const BOUNDARY_STYLE: L.PathOptions = {
  color: "#1e40af",
  weight: 2.5,
  opacity: 0.9,
  fill: false,
  dashArray: "6,4",
};

export const ConstituencyBoundaryLayer: React.FC<Props> = ({ geojson }) => {
  const map = useMap();
  const layerRef = useRef<L.GeoJSON | null>(null);

  useEffect(() => {
    if (!map) return;
    if (layerRef.current) {
      map.removeLayer(layerRef.current);
    }

    layerRef.current = L.geoJSON(geojson as L.GeoJsonObject, {
      style: BOUNDARY_STYLE,
    }).addTo(map);

    return () => {
      if (layerRef.current) {
        map.removeLayer(layerRef.current);
      }
    };
  }, [map, geojson]);

  return null;
};
