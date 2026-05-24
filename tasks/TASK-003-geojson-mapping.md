# TASK-003 — GeoJSON Mapping & Constituency Views

**Session**: 03
**Status**: IN PROGRESS — Foundation Complete, Real Datasets Pending
**Date**: 2026-05-22
**Model**: claude-sonnet-4-6

---

## Completed

### Phase 1: Dataset Audit
- Scanned `D:\NETA.AI` workspace
- **FINDING**: No real election datasets found in workspace
  - `drive-download-20260522T061335Z-3-001.zip` contains only template/scaffolding files
  - No CSV, GeoJSON, shapefile, or voter roll data present
- Built production infrastructure ready to accept real data when provided

### Phase 2: Database Foundation (Session 01 prerequisite)
- `app/database_design/database.py` — async SQLAlchemy engine
- `app/database_design/models.py` — all PRD tables (users, constituencies, zones, booths, voters, field_reports, news_articles, alerts, escalations, intelligence_briefs, intelligence_scores, audit_logs, constituency_demographics, booth_ward_mapping)
- `app/database_design/migrations/001_initial_schema.sql` — complete PostgreSQL + PostGIS DDL

### Phase 3: Seed Data (PRD-defined)
- `data/seed/001_constituency.sql` — Serilingampally AC-52
- `data/seed/002_zones.sql` — Z-01 through Z-07 (7 zones, all PRD data)
- `data/seed/003_booths.sql` — **315 booths** generated from `scripts/generate_booth_seed.py`
  - Distributed across 7 zones with realistic Hyderabad coordinates
  - Ready to be replaced with real ECI data via ingestion pipeline

### Phase 4: GeoJSON Data Files
- `data/geojson/serilingampally_ac52_boundary.geojson` — constituency boundary polygon [VALIDATED OK]
- `data/geojson/zones.geojson` — Z-01..Z-07 polygons with KPI properties [VALIDATED OK, 7 features]

### Phase 5: GeoJSON Mapping Service (Session 03 core)
- `app/geojson_mapping/schemas.py` — Pydantic schemas for all GeoJSON types
- `app/geojson_mapping/service.py` — PostGIS queries, choropleth data, booth popup
- `app/geojson_mapping/router.py` — 9 FastAPI endpoints (boundary, zones, booths, popup, catchment, demographics, import)

### Phase 6: Data Ingestion Pipeline
- `app/geojson_mapping/ingestion/booth_importer.py` — ECI booth CSV → PostgreSQL
  - Validates: duplicate booth_numbers, coordinate bounds, voter count consistency, missing columns
  - Supports dry_run mode
- `app/geojson_mapping/ingestion/voter_importer.py` — ECI voter roll → PostgreSQL
  - AES-256-GCM encryption for phone + address PII
  - Validates: duplicate voter IDs, booth lookup, gender codes, age range
- `app/geojson_mapping/ingestion/geojson_importer.py` — GeoJSON layer import (boundary/zones/catchments)

### Phase 7: Scripts
- `scripts/validate_datasets.py` — pre-import validation CLI (booths CSV, voters CSV, GeoJSON)
- `scripts/import_real_data.py` — CLI wrapper for API import endpoints
- `scripts/generate_booth_seed.py` — regenerates booth seed from PRD zone specs

### Phase 8: Frontend Components (React/Leaflet.js)
- `frontend/src/types/geo.ts` — TypeScript type definitions
- `frontend/src/services/geoApi.ts` — API client for all geo endpoints
- `frontend/src/hooks/useConstituencyData.ts` — React Query hooks (auto-refresh every 30-60s)
- `frontend/src/components/maps/ConstituencyMap.tsx` — main map container
- `frontend/src/components/maps/BoothMarkerLayer.tsx` — 315 booth markers, color-coded by layer
- `frontend/src/components/maps/BoothPopupCard.tsx` — PRD Section 22.3 popup card
- `frontend/src/components/maps/ConstituencyBoundaryLayer.tsx` — outer boundary
- `frontend/src/components/maps/ZoneOverlayLayer.tsx` — zone polygons with KPI tooltips
- `frontend/src/components/maps/MapLayerControls.tsx` — layer toggle sidebar panel

### Phase 9: Infrastructure
- `requirements.txt` — complete Python dependencies
- `.env.example` — environment variables template
- `docker-compose.yml` — PostgreSQL/PostGIS + Redis + API services
- `app/config.py` — pydantic-settings configuration
- `app/main.py` — FastAPI entry point with router registration

---

## API Endpoints Created

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/geo/constituency/{ac_number}/boundary` | Constituency boundary GeoJSON |
| GET | `/api/v1/geo/zones` | Zone overlay with live KPIs |
| GET | `/api/v1/geo/booths` | All booth points GeoJSON |
| GET | `/api/v1/geo/booths/{id}/popup` | Booth detail popup |
| GET | `/api/v1/geo/booths/{id}/catchment` | Booth catchment polygon |
| GET | `/api/v1/geo/demographics/{type}` | Demographic choropleth |
| POST | `/api/v1/geo/import/booths` | Upload ECI booth CSV |
| POST | `/api/v1/geo/import/voters` | Upload voter roll CSV |
| POST | `/api/v1/geo/import/geojson` | Upload GeoJSON layer |

---

## Blockers

### CRITICAL: No Real Datasets Provided
The task stated "real election datasets have been provided" but none exist in the workspace.

**Required files from campaign team:**
1. `serilingampally_booths.csv` — ECI booth list with coordinates
   - Required columns: `booth_number, booth_name, total_voters, female_voters, male_voters`
   - Optional: `latitude, longitude, address, ward_id, ward_name`
2. `voter_roll_*.csv` — ECI voter roll (one or multiple CSV files)
   - Required columns: `booth_number, voter_id, full_name, gender, age`
3. `AC52_BOUNDARY.shp` or `ac52_boundary.geojson` — official ECI constituency boundary
4. Ward boundary shapefiles from GHMC GIS portal

**How to import when provided:**
```powershell
# Step 1: Validate
python scripts/validate_datasets.py --booths data/imports/booths.csv

# Step 2: Import booths
python scripts/import_real_data.py booths data/imports/booths.csv

# Step 3: Import voters
python scripts/import_real_data.py voters data/imports/voters.csv

# Step 4: Import boundary (after shapefile → GeoJSON conversion)
# ogr2ogr -f GeoJSON ac52.geojson AC52.shp -t_srs EPSG:4326
python scripts/import_real_data.py geojson data/imports/ac52.geojson --layer constituency_boundary
```

---

## Seed Data Loading Instructions

```powershell
# Apply to running PostgreSQL
docker compose up -d postgres redis
docker compose exec postgres psql -U netaai_app -d netaai_prod -f /app/data/seed/001_constituency.sql
docker compose exec postgres psql -U netaai_app -d netaai_prod -f /app/data/seed/002_zones.sql
docker compose exec postgres psql -U netaai_app -d netaai_prod -f /app/data/seed/003_booths.sql
```

---

## Next Steps

- [ ] Campaign team to provide actual ECI booth CSV, voter rolls, and boundary shapefiles
- [ ] Run validation: `python scripts/validate_datasets.py --all data/imports/`
- [ ] Run import: `python scripts/import_real_data.py`
- [ ] Session 02: Complete JWT auth middleware and role enforcement
- [ ] Frontend: Wire `ConstituencyMap` into the Command Centre dashboard page
- [ ] Add ward-level demographic data from GHMC census source
