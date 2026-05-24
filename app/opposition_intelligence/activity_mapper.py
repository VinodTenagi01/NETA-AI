"""
Activity Mapper

Maps opposition ground activities (rallies, canvassing) to GeoJSON layers.
"""

from typing import Optional


class ActivityMapper:
    """Map opposition activities to geospatial representations."""

    @staticmethod
    def generate_opposition_geojson(
        locations: list[dict],
    ) -> dict:
        """
        Generate GeoJSON FeatureCollection for opposition activities.

        Args:
            locations: List of opposition activity locations with lat/lon

        Returns:
            GeoJSON FeatureCollection
        """
        features = []

        for location in locations:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [location.get("longitude"), location.get("latitude")],
                },
                "properties": {
                    "name": location.get("location_name", "Opposition Activity"),
                    "activity_type": location.get("activity_type", "unknown"),
                    "intensity": location.get("intensity", 0.5),
                    "timestamp": str(location.get("timestamp", "")),
                    "description": location.get("description", ""),
                },
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "features": features,
        }

    @staticmethod
    def cluster_opposition_locations(
        locations: list[dict],
        grid_size: int = 500,
    ) -> list[dict]:
        """
        Cluster opposition locations by geographic proximity.

        Args:
            locations: List of opposition activity locations
            grid_size: Grid cell size in meters

        Returns:
            List of location clusters
        """
        if not locations:
            return []

        # Simple grid-based clustering
        clusters = {}

        for location in locations:
            lat = location.get("latitude", 0)
            lon = location.get("longitude", 0)

            # Convert to grid coordinates (simplified)
            grid_lat = int(lat * 1000 / grid_size)
            grid_lon = int(lon * 1000 / grid_size)
            grid_key = f"{grid_lat}_{grid_lon}"

            if grid_key not in clusters:
                clusters[grid_key] = {
                    "center_lat": lat,
                    "center_lon": lon,
                    "locations": [],
                    "total_intensity": 0,
                }

            clusters[grid_key]["locations"].append(location)
            clusters[grid_key]["total_intensity"] += location.get("intensity", 0.5)

        # Convert to list and calculate cluster properties
        result = []
        for grid_key, cluster in clusters.items():
            avg_intensity = (
                cluster["total_intensity"] / len(cluster["locations"])
                if cluster["locations"]
                else 0
            )

            result.append(
                {
                    "grid_key": grid_key,
                    "center_lat": cluster["center_lat"],
                    "center_lon": cluster["center_lon"],
                    "location_count": len(cluster["locations"]),
                    "average_intensity": avg_intensity,
                    "locations": cluster["locations"],
                }
            )

        return result

    @staticmethod
    def generate_heatmap_grid(
        locations: list[dict],
        grid_size: int = 500,
        constituency_bounds: Optional[dict] = None,
    ) -> dict:
        """
        Generate heatmap grid from opposition locations.

        Args:
            locations: Opposition activity locations
            grid_size: Grid cell size
            constituency_bounds: Optional boundary box

        Returns:
            Heatmap grid data
        """
        if not locations:
            return {
                "grid": {},
                "intensity_scale": (0.0, 0.0),
                "max_intensity": 0.0,
            }

        # Calculate grid
        clusters = ActivityMapper.cluster_opposition_locations(locations, grid_size)

        grid = {}
        intensities = []

        for cluster in clusters:
            grid_key = cluster["grid_key"]
            intensity = cluster["average_intensity"]

            grid[grid_key] = {
                "center_lat": cluster["center_lat"],
                "center_lon": cluster["center_lon"],
                "intensity": intensity,
                "location_count": cluster["location_count"],
            }

            intensities.append(intensity)

        min_intensity = min(intensities) if intensities else 0.0
        max_intensity = max(intensities) if intensities else 0.0

        return {
            "grid": grid,
            "intensity_scale": (min_intensity, max_intensity),
            "max_intensity": max_intensity,
            "total_locations": len(locations),
            "cluster_count": len(clusters),
        }

    @staticmethod
    def identify_concentration_zones(
        heatmap: dict,
        threshold: float = 0.7,
    ) -> list[dict]:
        """
        Identify high-concentration opposition zones.

        Args:
            heatmap: Generated heatmap data
            threshold: Intensity threshold for concentration

        Returns:
            List of concentration zones
        """
        if not heatmap or "grid" not in heatmap:
            return []

        max_intensity = heatmap.get("max_intensity", 1.0)
        if max_intensity == 0:
            return []

        zones = []

        for grid_key, cell in heatmap["grid"].items():
            intensity = cell.get("intensity", 0)

            if intensity >= (max_intensity * threshold):
                zones.append(
                    {
                        "grid_key": grid_key,
                        "center_lat": cell.get("center_lat"),
                        "center_lon": cell.get("center_lon"),
                        "intensity": intensity,
                        "location_count": cell.get("location_count"),
                        "concentration_level": "HIGH"
                        if intensity >= (max_intensity * 0.9)
                        else "MODERATE",
                    }
                )

        return sorted(zones, key=lambda z: z["intensity"], reverse=True)
