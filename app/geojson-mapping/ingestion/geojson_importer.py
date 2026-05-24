"""
GeoJSON Layer Importer.
Handles importing ECI/GHMC GeoJSON files for:
  - constituency_boundary → constituencies.boundary_geojson
  - zone_boundaries       → campaign_zones.boundary_geojson
  - booth_catchments      → booths.catchment_geojson (matched by booth_number)
"""
import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_design.models import Booth, CampaignZone, Constituency
from app.geojson_mapping.schemas import GeoJSONImportResult


class GeoJSONImporter:
    def __init__(self, db: AsyncSession, constituency_id: UUID):
        self.db = db
        self.constituency_id = constituency_id

    async def import_layer(
        self,
        layer_type: str,
        geojson: dict,
    ) -> GeoJSONImportResult:
        features = geojson.get("features", [])

        if layer_type == "constituency_boundary":
            return await self._import_constituency_boundary(features)
        if layer_type == "zone_boundaries":
            return await self._import_zone_boundaries(features)
        if layer_type == "booth_catchments":
            return await self._import_booth_catchments(features)

        return GeoJSONImportResult(
            status="failed",
            layer_type=layer_type,
            features_imported=0,
            features_skipped=0,
            errors=[f"Unknown layer_type: {layer_type}"],
        )

    async def _import_constituency_boundary(self, features: list) -> GeoJSONImportResult:
        result = await self.db.execute(
            select(Constituency).where(Constituency.id == self.constituency_id)
        )
        constituency = result.scalar_one_or_none()
        if not constituency:
            return GeoJSONImportResult(
                status="failed",
                layer_type="constituency_boundary",
                features_imported=0,
                features_skipped=0,
                errors=[f"Constituency {self.constituency_id} not found"],
            )

        if not features:
            return GeoJSONImportResult(
                status="failed",
                layer_type="constituency_boundary",
                features_imported=0,
                features_skipped=0,
                errors=["No features in GeoJSON"],
            )

        # Store the full FeatureCollection in boundary_geojson
        constituency.boundary_geojson = {"type": "FeatureCollection", "features": features}
        await self.db.flush()

        return GeoJSONImportResult(
            status="success",
            layer_type="constituency_boundary",
            features_imported=1,
            features_skipped=len(features) - 1 if len(features) > 1 else 0,
        )

    async def _import_zone_boundaries(self, features: list) -> GeoJSONImportResult:
        result = await self.db.execute(
            select(CampaignZone).where(CampaignZone.constituency_id == self.constituency_id)
        )
        zones = {z.zone_code: z for z in result.scalars().all()}

        imported, skipped, errors = 0, 0, []

        for feat in features:
            props = feat.get("properties", {})
            zone_code = props.get("zone_code") or props.get("ZONE_CODE") or props.get("Zone_Code")

            if not zone_code or zone_code not in zones:
                skipped += 1
                errors.append(f"Zone code '{zone_code}' not found in DB — skipped")
                continue

            zones[zone_code].boundary_geojson = feat["geometry"]
            imported += 1

        await self.db.flush()

        return GeoJSONImportResult(
            status="success" if not errors else "partial",
            layer_type="zone_boundaries",
            features_imported=imported,
            features_skipped=skipped,
            errors=errors,
        )

    async def _import_booth_catchments(self, features: list) -> GeoJSONImportResult:
        result = await self.db.execute(
            select(Booth.booth_number, Booth.id).where(Booth.constituency_id == self.constituency_id)
        )
        booth_map = {row.booth_number: row.id for row in result.all()}

        imported, skipped, errors = 0, 0, []

        for feat in features:
            props = feat.get("properties", {})
            booth_num = str(
                props.get("booth_number")
                or props.get("BOOTH_NUMBER")
                or props.get("Booth_Number")
                or ""
            ).strip().zfill(3)

            if not booth_num or booth_num not in booth_map:
                skipped += 1
                errors.append(f"Booth '{booth_num}' not found — skipped")
                continue

            booth_result = await self.db.execute(
                select(Booth).where(Booth.id == booth_map[booth_num])
            )
            booth = booth_result.scalar_one_or_none()
            if booth:
                booth.catchment_geojson = feat["geometry"]
                imported += 1

        await self.db.flush()

        return GeoJSONImportResult(
            status="success" if not errors else "partial",
            layer_type="booth_catchments",
            features_imported=imported,
            features_skipped=skipped,
            errors=errors,
        )
