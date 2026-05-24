"""
Pydantic schemas for the GeoJSON Mapping module.
Covers constituency boundaries, zone overlays, booth data,
demographic layers, and data ingestion responses.
"""
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ---------- GeoJSON primitives ----------

class GeoJSONPoint(BaseModel):
    type: str = "Point"
    coordinates: list[float]  # [lng, lat]


class GeoJSONPolygon(BaseModel):
    type: str = "Polygon"
    coordinates: list[list[list[float]]]


class GeoJSONFeatureProperties(BaseModel):
    model_config = {"extra": "allow"}


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    properties: dict[str, Any]
    geometry: dict[str, Any] | None


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[GeoJSONFeature]
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------- Constituency ----------

class ConstituencyBoundaryResponse(BaseModel):
    ac_number: str
    ac_name: str
    state: str
    total_booths: int
    total_voters: int
    geojson: GeoJSONFeatureCollection


# ---------- Zone ----------

class ZoneProperties(BaseModel):
    id: str
    zone_code: str
    zone_name: str
    key_areas: str
    approx_booth_count: int
    approx_voter_count: int
    contact_rate_pct: float = 0.0
    avg_health_score: float = 50.0
    open_escalations: int = 0
    active_workers: int = 0


class ZoneOverlayResponse(BaseModel):
    geojson: GeoJSONFeatureCollection
    summary: dict[str, Any]


# ---------- Booth ----------

class BoothMapPoint(BaseModel):
    id: UUID
    booth_number: str
    booth_name: str
    zone_code: str
    zone_name: str
    lat: float
    lng: float
    total_voters: int
    female_voters: int
    male_voters: int
    contact_rate: float
    health_score: float
    risk_score: float
    swing_booth: bool
    last_report_at: Optional[str]
    open_escalations: int = 0
    volunteer_count: int = 0
    mood: Optional[str] = None


class BoothGeoJSONResponse(BaseModel):
    geojson: GeoJSONFeatureCollection
    total: int
    bounds: dict[str, float]  # {min_lat, max_lat, min_lng, max_lng}


class BoothDetailPopup(BaseModel):
    """Data for booth popup card on map click (PRD Section 22.3)."""
    id: UUID
    booth_number: str
    booth_name: str
    zone_code: str
    zone_name: str
    total_voters: int
    contacted: int
    contact_pct: float
    health_score: float
    risk_score: float
    volunteer_count: int
    last_report_hours: Optional[float]
    open_escalations: int
    mood: Optional[str]
    assigned_commander_name: Optional[str]


# ---------- Data Layer ----------

class DataLayerType(str):
    HEALTH = "health"
    RISK = "risk"
    CONTACT_RATE = "contact_rate"
    VOTER_DENSITY = "voter_density"
    SENTIMENT = "sentiment"


class ChoroplethLayer(BaseModel):
    layer_type: str
    features: list[dict[str, Any]]
    scale_min: float
    scale_max: float
    color_steps: list[str] = [
        "#fee2e2", "#fca5a5", "#f87171", "#ef4444", "#b91c1c"
    ]


# ---------- Ingestion ----------

class BoothCSVRow(BaseModel):
    """Expected columns in ECI booth CSV upload."""
    booth_number: str
    booth_name: str
    address: Optional[str] = None
    total_voters: int
    female_voters: int
    male_voters: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ward_id: Optional[str] = None
    ward_name: Optional[str] = None


class VoterCSVRow(BaseModel):
    """Expected columns in ECI voter roll CSV upload."""
    booth_number: str
    voter_id: str
    full_name: str
    gender: str
    age: int
    address: Optional[str] = None
    phone: Optional[str] = None

    @field_validator("gender")
    @classmethod
    def normalize_gender(cls, v: str) -> str:
        v = v.strip().upper()
        mapping = {"MALE": "M", "FEMALE": "F", "OTHER": "O", "M": "M", "F": "F", "O": "O"}
        if v not in mapping:
            raise ValueError(f"Invalid gender: {v}")
        return mapping[v]


class IngestionReport(BaseModel):
    status: str  # "success" | "partial" | "failed"
    total_rows: int
    inserted: int
    updated: int
    skipped: int
    errors: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    duplicate_booth_numbers: list[str] = Field(default_factory=list)
    invalid_coordinates: list[str] = Field(default_factory=list)


class GeoJSONImportResult(BaseModel):
    status: str
    layer_type: str
    features_imported: int
    features_skipped: int
    errors: list[str] = Field(default_factory=list)
