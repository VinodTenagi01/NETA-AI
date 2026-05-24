"""
GeoJSON Mapping API Router.
Prefix: /api/v1/geo

Endpoints:
  GET  /constituency/{ac_number}/boundary     — constituency boundary GeoJSON
  GET  /zones                                 — zone overlay GeoJSON with live KPIs
  GET  /booths                                — all booth points GeoJSON
  GET  /booths/{booth_id}/popup               — booth detail popup data
  GET  /booths/{booth_id}/catchment           — booth catchment polygon
  GET  /layers/{layer_type}                   — choropleth data layer
  GET  /demographics/{overlay_type}          — demographic overlay
  POST /import/booths                         — import booth CSV
  POST /import/voters                         — import voter roll CSV
  POST /import/geojson                        — import raw GeoJSON layer
"""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_design.database import get_db
from app.geojson_mapping.ingestion.booth_importer import BoothImporter
from app.geojson_mapping.ingestion.voter_importer import VoterImporter
from app.geojson_mapping.schemas import (
    BoothDetailPopup,
    BoothGeoJSONResponse,
    GeoJSONFeatureCollection,
    GeoJSONImportResult,
    IngestionReport,
    ZoneOverlayResponse,
)
from app.geojson_mapping.service import GeoJSONMappingService

router = APIRouter(prefix="/api/v1/geo", tags=["GeoJSON Mapping"])
service = GeoJSONMappingService()


@router.get(
    "/constituency/{ac_number}/boundary",
    summary="Constituency boundary GeoJSON",
    response_model=dict,
)
async def get_constituency_boundary(
    ac_number: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the GeoJSON FeatureCollection for the constituency outer boundary.
    ac_number: "52" for Serilingampally AC-52.
    """
    try:
        return await service.get_constituency_boundary(db, ac_number)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Boundary data not found for AC {ac_number}. Upload via /import/geojson.",
        )


@router.get(
    "/zones",
    summary="Zone overlay GeoJSON with live KPIs",
    response_model=ZoneOverlayResponse,
)
async def get_zone_overlay(
    constituency_id: Optional[UUID] = Query(None, description="Filter to a specific constituency UUID"),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_zone_overlay(db, constituency_id)


@router.get(
    "/booths",
    summary="All booth points GeoJSON",
    response_model=BoothGeoJSONResponse,
)
async def get_booths_geojson(
    constituency_id: Optional[UUID] = Query(None),
    zone_code: Optional[str] = Query(None, description="Filter by zone code, e.g. Z-01"),
    layer: str = Query("risk", description="Color layer: risk|health|contact_rate|voter_density|sentiment"),
    db: AsyncSession = Depends(get_db),
):
    valid_layers = {"risk", "health", "contact_rate", "voter_density", "sentiment"}
    if layer not in valid_layers:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid layer. Choose from: {valid_layers}",
        )
    return await service.get_booths_geojson(db, constituency_id, zone_code, layer)


@router.get(
    "/booths/{booth_id}/popup",
    summary="Booth detail popup card",
    response_model=BoothDetailPopup,
)
async def get_booth_popup(
    booth_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await service.get_booth_popup(db, booth_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/booths/{booth_id}/catchment",
    summary="Booth catchment polygon",
    response_model=dict,
)
async def get_booth_catchment(
    booth_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.database_design.models import Booth

    result = await db.execute(select(Booth.catchment_geojson, Booth.booth_number).where(Booth.id == booth_id))
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Booth not found")

    if row.catchment_geojson:
        return row.catchment_geojson

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No catchment polygon for booth {row.booth_number}. Upload via /import/geojson.",
    )


@router.get(
    "/demographics/{overlay_type}",
    summary="Demographic overlay GeoJSON",
    response_model=GeoJSONFeatureCollection,
)
async def get_demographic_overlay(
    overlay_type: str,
    constituency_id: UUID = Query(..., description="Constituency UUID"),
    db: AsyncSession = Depends(get_db),
):
    valid_overlays = {"voter_density", "sc_st", "youth", "literacy", "gender_ratio"}
    if overlay_type not in valid_overlays:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid overlay type. Choose from: {valid_overlays}",
        )
    return await service.get_demographic_overlay(db, constituency_id, overlay_type)


# ---------- Data Ingestion Endpoints ----------

@router.post(
    "/import/booths",
    summary="Import booth data from ECI CSV",
    response_model=IngestionReport,
    status_code=status.HTTP_201_CREATED,
)
async def import_booths_csv(
    file: UploadFile = File(..., description="ECI booth list CSV"),
    constituency_id: UUID = Query(..., description="Target constituency UUID"),
    dry_run: bool = Query(False, description="Validate without writing to DB"),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload an ECI booth CSV to replace mock booth data.
    Expected columns: booth_number, booth_name, address, total_voters,
    female_voters, male_voters, latitude, longitude, ward_id, ward_name
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only CSV files are accepted",
        )
    content = await file.read()
    importer = BoothImporter(db, constituency_id, dry_run=dry_run)
    return await importer.import_csv(content.decode("utf-8-sig"))


@router.post(
    "/import/voters",
    summary="Import voter roll from ECI CSV",
    response_model=IngestionReport,
    status_code=status.HTTP_201_CREATED,
)
async def import_voters_csv(
    file: UploadFile = File(..., description="ECI voter roll CSV"),
    constituency_id: UUID = Query(..., description="Target constituency UUID"),
    dry_run: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload ECI voter roll CSV.
    Expected columns: booth_number, voter_id, full_name, gender, age, address, phone
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only CSV files are accepted",
        )
    content = await file.read()
    importer = VoterImporter(db, constituency_id, dry_run=dry_run)
    return await importer.import_csv(content.decode("utf-8-sig"))


@router.post(
    "/import/geojson",
    summary="Import raw GeoJSON layer (boundary/catchments)",
    response_model=GeoJSONImportResult,
    status_code=status.HTTP_201_CREATED,
)
async def import_geojson_layer(
    file: UploadFile = File(..., description="GeoJSON FeatureCollection"),
    layer_type: str = Query(..., description="constituency_boundary|zone_boundaries|booth_catchments"),
    constituency_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a GeoJSON file to update boundary or catchment data.
    Use this when ECI shapefiles have been converted via ogr2ogr.
    """
    import json
    valid_layers = {"constituency_boundary", "zone_boundaries", "booth_catchments"}
    if layer_type not in valid_layers:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"layer_type must be one of: {valid_layers}",
        )

    content = await file.read()
    try:
        geojson_data = json.loads(content)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid GeoJSON: {e}",
        )

    if geojson_data.get("type") != "FeatureCollection":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a GeoJSON FeatureCollection",
        )

    from app.geojson_mapping.ingestion.geojson_importer import GeoJSONImporter
    importer = GeoJSONImporter(db, constituency_id)
    return await importer.import_layer(layer_type, geojson_data)
