"""
GeoJSON Mapping Service — PostGIS queries and GeoJSON construction.
Responsible for:
  - Constituency boundary layer
  - Zone boundary overlays
  - Booth point GeoJSON with live KPI overlay
  - Choropleth data layers (health/risk/contact/density/sentiment)
  - Booth detail popup data
"""
import json
import math
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_design.models import (
    Booth,
    BoothVolunteer,
    CampaignZone,
    Constituency,
    Escalation,
    FieldReport,
    User,
)
from app.geojson_mapping.schemas import (
    BoothDetailPopup,
    BoothGeoJSONResponse,
    BoothMapPoint,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    ZoneOverlayResponse,
)

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "geojson"

RISK_COLOR_SCALE = {
    (0, 35):   "#22c55e",   # green — healthy
    (36, 60):  "#eab308",   # yellow — watch
    (61, 80):  "#f97316",   # orange — at-risk
    (81, 100): "#ef4444",   # red — critical
}

HEALTH_COLOR_SCALE = [
    "#fee2e2", "#fca5a5", "#f87171", "#ef4444", "#b91c1c"
]


def _risk_color(score: float) -> str:
    for (lo, hi), color in RISK_COLOR_SCALE.items():
        if lo <= score <= hi:
            return color
    return "#6b7280"


def _health_color(score: float) -> str:
    idx = min(int(score / 20), 4)
    colors = ["#b91c1c", "#ef4444", "#f97316", "#eab308", "#22c55e"]
    return colors[idx]


class GeoJSONMappingService:

    async def get_constituency_boundary(
        self,
        db: AsyncSession,
        ac_number: str = "52",
    ) -> dict[str, Any]:
        """
        Return constituency boundary GeoJSON.
        Tries DB-stored boundary first, falls back to static file.
        """
        result = await db.execute(
            select(Constituency).where(Constituency.ac_number == ac_number)
        )
        constituency = result.scalar_one_or_none()

        if constituency and constituency.boundary_geojson:
            boundary = constituency.boundary_geojson
        else:
            static_path = DATA_DIR / "serilingampally_ac52_boundary.geojson"
            with open(static_path) as f:
                fc = json.load(f)
            boundary = fc

            # Enrich with live voter/booth counts from DB
            if constituency:
                for feat in boundary.get("features", []):
                    feat["properties"]["total_booths"] = constituency.total_booths or 0
                    feat["properties"]["total_voters"] = constituency.total_voters or 0

        return boundary

    async def get_zone_overlay(
        self,
        db: AsyncSession,
        constituency_id: Optional[UUID] = None,
    ) -> ZoneOverlayResponse:
        """
        Return zone boundaries as GeoJSON with live KPI attributes.
        """
        # Load static zone boundaries
        static_path = DATA_DIR / "zones.geojson"
        with open(static_path) as f:
            base_fc = json.load(f)

        # Fetch live KPI aggregates per zone from DB
        zone_kpis = await self._get_zone_kpis(db, constituency_id)

        enriched_features = []
        for feat in base_fc.get("features", []):
            code = feat["properties"]["zone_code"]
            kpi = zone_kpis.get(code, {})
            feat["properties"].update({
                "contact_rate_pct": kpi.get("avg_contact_rate", 0.0),
                "avg_health_score": kpi.get("avg_health_score", 50.0),
                "active_workers": kpi.get("active_workers", 0),
                "open_escalations": kpi.get("open_escalations", 0),
                "booth_count": kpi.get("booth_count", 0),
            })
            enriched_features.append(GeoJSONFeature(
                type="Feature",
                properties=feat["properties"],
                geometry=feat["geometry"],
            ))

        fc = GeoJSONFeatureCollection(
            type="FeatureCollection",
            features=enriched_features,
            metadata={"layer": "zone_boundaries", "zones": len(enriched_features)},
        )

        summary = {
            "total_zones": len(enriched_features),
            "zone_kpis": zone_kpis,
        }

        return ZoneOverlayResponse(geojson=fc, summary=summary)

    async def get_booths_geojson(
        self,
        db: AsyncSession,
        constituency_id: Optional[UUID] = None,
        zone_code: Optional[str] = None,
        layer: str = "risk",
    ) -> BoothGeoJSONResponse:
        """
        Return all booths as GeoJSON points with KPI overlay data.
        layer: 'risk' | 'health' | 'contact_rate' | 'voter_density' | 'sentiment'
        """
        query = (
            select(
                Booth.id,
                Booth.booth_number,
                Booth.booth_name,
                Booth.zone_id,
                Booth.total_voters,
                Booth.female_voters,
                Booth.male_voters,
                Booth.contact_rate,
                Booth.health_score,
                Booth.risk_score,
                Booth.swing_booth,
                Booth.last_report_at,
                func.ST_Y(func.ST_AsText(Booth.location)).label("lat"),
                func.ST_X(func.ST_AsText(Booth.location)).label("lng"),
                CampaignZone.zone_code,
                CampaignZone.zone_name,
            )
            .outerjoin(CampaignZone, Booth.zone_id == CampaignZone.id)
        )

        if constituency_id:
            query = query.where(Booth.constituency_id == constituency_id)
        if zone_code:
            query = query.where(CampaignZone.zone_code == zone_code)

        result = await db.execute(query)
        booths = result.all()

        features = []
        lats, lngs = [], []

        for row in booths:
            lat = float(row.lat) if row.lat else 17.470
            lng = float(row.lng) if row.lng else 78.362
            lats.append(lat)
            lngs.append(lng)

            color = self._layer_color(row, layer)
            last_report_hours = None
            if row.last_report_at:
                from datetime import datetime, timezone
                delta = datetime.now(timezone.utc) - row.last_report_at.replace(tzinfo=timezone.utc)
                last_report_hours = round(delta.total_seconds() / 3600, 1)

            features.append(GeoJSONFeature(
                type="Feature",
                properties={
                    "id": str(row.id),
                    "booth_number": row.booth_number,
                    "booth_name": row.booth_name or f"Booth {row.booth_number}",
                    "zone_code": row.zone_code or "",
                    "zone_name": row.zone_name or "",
                    "total_voters": row.total_voters or 0,
                    "female_voters": row.female_voters or 0,
                    "male_voters": row.male_voters or 0,
                    "contact_rate": float(row.contact_rate or 0),
                    "health_score": float(row.health_score or 50),
                    "risk_score": float(row.risk_score or 50),
                    "swing_booth": row.swing_booth,
                    "last_report_hours": last_report_hours,
                    "color": color,
                    "layer": layer,
                    "marker_size": self._marker_size(row.total_voters or 0),
                },
                geometry={
                    "type": "Point",
                    "coordinates": [lng, lat],
                },
            ))

        bounds = {
            "min_lat": min(lats) if lats else 17.420,
            "max_lat": max(lats) if lats else 17.520,
            "min_lng": min(lngs) if lngs else 78.280,
            "max_lng": max(lngs) if lngs else 78.410,
        }

        fc = GeoJSONFeatureCollection(
            type="FeatureCollection",
            features=features,
            metadata={"layer": layer, "total": len(features)},
        )

        return BoothGeoJSONResponse(geojson=fc, total=len(features), bounds=bounds)

    async def get_booth_popup(
        self,
        db: AsyncSession,
        booth_id: UUID,
    ) -> BoothDetailPopup:
        """Booth detail popup card data (PRD Section 22.3)."""
        result = await db.execute(
            select(
                Booth,
                CampaignZone.zone_code,
                CampaignZone.zone_name,
                User.full_name.label("commander_name"),
            )
            .outerjoin(CampaignZone, Booth.zone_id == CampaignZone.id)
            .outerjoin(User, Booth.assigned_commander == User.id)
            .where(Booth.id == booth_id)
        )
        row = result.first()
        if not row:
            raise ValueError(f"Booth {booth_id} not found")

        booth, zone_code, zone_name, commander_name = row

        # Volunteer count
        vol_result = await db.execute(
            select(func.count()).select_from(BoothVolunteer).where(BoothVolunteer.booth_id == booth_id)
        )
        volunteer_count = vol_result.scalar() or 0

        # Open escalations
        esc_result = await db.execute(
            select(func.count()).select_from(Escalation).where(
                Escalation.field_report_id.in_(
                    select(FieldReport.id).where(FieldReport.booth_id == booth_id)
                ),
                Escalation.status.in_(["NEW", "ASSIGNED", "IN_PROGRESS"]),
            )
        )
        open_escalations = esc_result.scalar() or 0

        # Recent mood from field reports (last 24h)
        mood_result = await db.execute(
            select(FieldReport.voter_sentiment)
            .where(
                FieldReport.booth_id == booth_id,
                FieldReport.voter_sentiment.isnot(None),
            )
            .order_by(FieldReport.created_at.desc())
            .limit(5)
        )
        sentiments = [r[0] for r in mood_result.all()]
        mood = self._aggregate_mood(sentiments)

        total_v = booth.total_voters or 0
        contact_count = int(total_v * float(booth.contact_rate or 0) / 100)

        last_report_hours = None
        if booth.last_report_at:
            from datetime import datetime, timezone
            delta = datetime.now(timezone.utc) - booth.last_report_at.replace(tzinfo=timezone.utc)
            last_report_hours = round(delta.total_seconds() / 3600, 1)

        return BoothDetailPopup(
            id=booth.id,
            booth_number=booth.booth_number,
            booth_name=booth.booth_name or f"Booth {booth.booth_number}",
            zone_code=zone_code or "",
            zone_name=zone_name or "",
            total_voters=total_v,
            contacted=contact_count,
            contact_pct=float(booth.contact_rate or 0),
            health_score=float(booth.health_score or 50),
            risk_score=float(booth.risk_score or 50),
            volunteer_count=volunteer_count,
            last_report_hours=last_report_hours,
            open_escalations=open_escalations,
            mood=mood,
            assigned_commander_name=commander_name,
        )

    async def get_demographic_overlay(
        self,
        db: AsyncSession,
        constituency_id: UUID,
        overlay_type: str = "voter_density",
    ) -> GeoJSONFeatureCollection:
        """
        Return demographic choropleth data joined to zone boundaries.
        overlay_type: voter_density | sc_st | youth | literacy | gender_ratio
        """
        from app.database_design.models import ConstituencyDemographics

        result = await db.execute(
            select(ConstituencyDemographics).where(
                ConstituencyDemographics.constituency_id == constituency_id
            )
        )
        demo_rows = result.scalars().all()

        # Map ward → demographic values
        ward_map = {row.ward_id: row for row in demo_rows}

        static_path = DATA_DIR / "zones.geojson"
        with open(static_path) as f:
            base_fc = json.load(f)

        features = []
        for feat in base_fc.get("features", []):
            zone_code = feat["properties"]["zone_code"]
            demo = ward_map.get(zone_code)
            value = self._extract_demo_value(demo, overlay_type) if demo else 0

            props = {**feat["properties"], "overlay_value": value, "overlay_type": overlay_type}
            features.append(GeoJSONFeature(
                type="Feature",
                properties=props,
                geometry=feat["geometry"],
            ))

        return GeoJSONFeatureCollection(
            type="FeatureCollection",
            features=features,
            metadata={"overlay_type": overlay_type},
        )

    # ------ Private helpers ------

    async def _get_zone_kpis(
        self,
        db: AsyncSession,
        constituency_id: Optional[UUID],
    ) -> dict[str, dict]:
        query = (
            select(
                CampaignZone.zone_code,
                func.count(Booth.id).label("booth_count"),
                func.avg(Booth.contact_rate).label("avg_contact_rate"),
                func.avg(Booth.health_score).label("avg_health_score"),
            )
            .outerjoin(Booth, Booth.zone_id == CampaignZone.id)
            .group_by(CampaignZone.zone_code)
        )
        if constituency_id:
            query = query.where(CampaignZone.constituency_id == constituency_id)

        result = await db.execute(query)
        return {
            row.zone_code: {
                "booth_count": row.booth_count or 0,
                "avg_contact_rate": round(float(row.avg_contact_rate or 0), 2),
                "avg_health_score": round(float(row.avg_health_score or 50), 2),
                "active_workers": 0,    # populated from Redis cache in production
                "open_escalations": 0,  # populated from Redis cache in production
            }
            for row in result.all()
        }

    def _layer_color(self, row: Any, layer: str) -> str:
        if layer == "risk":
            return _risk_color(float(row.risk_score or 50))
        if layer == "health":
            return _health_color(float(row.health_score or 50))
        if layer == "contact_rate":
            rate = float(row.contact_rate or 0)
            if rate >= 75:
                return "#22c55e"
            if rate >= 50:
                return "#eab308"
            if rate >= 25:
                return "#f97316"
            return "#ef4444"
        return "#6b7280"

    @staticmethod
    def _marker_size(total_voters: int) -> int:
        if total_voters >= 1200:
            return 12
        if total_voters >= 900:
            return 10
        return 8

    @staticmethod
    def _aggregate_mood(sentiments: list[str]) -> Optional[str]:
        if not sentiments:
            return None
        counts = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0, "MIXED": 0}
        for s in sentiments:
            if s in counts:
                counts[s] += 1
        return max(counts, key=counts.get)

    @staticmethod
    def _extract_demo_value(demo: Any, overlay_type: str) -> float:
        mapping = {
            "voter_density": demo.voter_population or 0,
            "sc_st": float(demo.sc_population_pct or 0) + float(demo.st_population_pct or 0),
            "youth": float(demo.youth_voter_pct or 0),
            "literacy": float(demo.literacy_rate_pct or 0),
            "gender_ratio": (
                (demo.female_voters / demo.voter_population * 100)
                if demo.voter_population
                else 50.0
            ),
        }
        return mapping.get(overlay_type, 0)
