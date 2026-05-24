#!/usr/bin/env python3
"""
NETA AI — Real Dataset Import CLI.
Run this when campaign team provides actual ECI booth/voter data.

Usage examples:
  # Import booth list CSV
  python scripts/import_real_data.py booths data/imports/serilingampally_booths.csv

  # Import voter rolls
  python scripts/import_real_data.py voters data/imports/part1_voters.csv

  # Import GeoJSON boundary from converted shapefile
  python scripts/import_real_data.py geojson data/imports/ac52_boundary.geojson --layer constituency_boundary

  # Dry run (validates without writing)
  python scripts/import_real_data.py booths data/imports/booths.csv --dry-run

  # Convert ECI shapefile to GeoJSON first (requires gdal/ogr2ogr):
  #   ogr2ogr -f GeoJSON ac52_boundary.geojson AC52_BOUNDARY.shp -t_srs EPSG:4326

Prerequisites:
    pip install httpx
    PostgreSQL must be running with seed data applied:
        psql -U netaai_app -d netaai_prod -f data/seed/001_constituency.sql
        psql -U netaai_app -d netaai_prod -f data/seed/002_zones.sql
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import httpx
except ImportError:
    print("ERROR: Install httpx first: pip install httpx")
    sys.exit(1)

# Default local dev API base
API_BASE = "http://localhost:8000/api/v1/geo"
CONSTITUENCY_ID = "11111111-0052-4000-8000-000000000001"


def import_booths(path: Path, dry_run: bool = False):
    print(f"\nImporting booth data from: {path}")
    if dry_run:
        print("DRY RUN — no data will be written")

    with open(path, "rb") as f:
        url = f"{API_BASE}/import/booths?constituency_id={CONSTITUENCY_ID}&dry_run={str(dry_run).lower()}"
        resp = httpx.post(url, files={"file": (path.name, f, "text/csv")}, timeout=120.0)

    if resp.status_code in (200, 201):
        result = resp.json()
        print(f"\nResult: {result['status'].upper()}")
        print(f"  Total rows: {result['total_rows']}")
        print(f"  Inserted:   {result['inserted']}")
        print(f"  Updated:    {result['updated']}")
        print(f"  Skipped:    {result['skipped']}")
        if result.get("errors"):
            print(f"\nErrors ({len(result['errors'])}):")
            for e in result["errors"][:10]:
                print(f"  {e}")
        if result.get("warnings"):
            print(f"\nWarnings ({len(result['warnings'])}):")
            for w in result["warnings"][:10]:
                print(f"  {w}")
        if result.get("duplicate_booth_numbers"):
            print(f"\nDuplicate booth numbers: {result['duplicate_booth_numbers'][:10]}")
        if result.get("invalid_coordinates"):
            print(f"Invalid coordinates: {result['invalid_coordinates'][:10]}")
    else:
        print(f"ERROR: HTTP {resp.status_code}")
        print(resp.text)
        sys.exit(1)


def import_voters(path: Path, dry_run: bool = False):
    print(f"\nImporting voter roll from: {path}")
    if dry_run:
        print("DRY RUN — no data will be written")

    with open(path, "rb") as f:
        url = f"{API_BASE}/import/voters?constituency_id={CONSTITUENCY_ID}&dry_run={str(dry_run).lower()}"
        resp = httpx.post(url, files={"file": (path.name, f, "text/csv")}, timeout=300.0)

    if resp.status_code in (200, 201):
        result = resp.json()
        print(f"\nResult: {result['status'].upper()}")
        print(f"  Total rows: {result['total_rows']}")
        print(f"  Inserted:   {result['inserted']}")
        print(f"  Updated:    {result['updated']}")
        print(f"  Skipped:    {result['skipped']}")
        if result.get("errors"):
            print(f"\nErrors ({len(result['errors'])}):")
            for e in result["errors"][:10]:
                print(f"  {e}")
    else:
        print(f"ERROR: HTTP {resp.status_code}")
        print(resp.text)
        sys.exit(1)


def import_geojson(path: Path, layer_type: str):
    print(f"\nImporting GeoJSON layer '{layer_type}' from: {path}")

    # Basic validation before upload
    with open(path) as f:
        data = json.load(f)
    if data.get("type") != "FeatureCollection":
        print("ERROR: File must be a GeoJSON FeatureCollection")
        sys.exit(1)
    print(f"  Features found: {len(data.get('features', []))}")

    with open(path, "rb") as f:
        url = f"{API_BASE}/import/geojson?layer_type={layer_type}&constituency_id={CONSTITUENCY_ID}"
        resp = httpx.post(
            url,
            files={"file": (path.name, f, "application/json")},
            timeout=120.0,
        )

    if resp.status_code in (200, 201):
        result = resp.json()
        print(f"\nResult: {result['status'].upper()}")
        print(f"  Imported: {result['features_imported']}")
        print(f"  Skipped:  {result['features_skipped']}")
        if result.get("errors"):
            print(f"\nErrors: {result['errors'][:10]}")
    else:
        print(f"ERROR: HTTP {resp.status_code}")
        print(resp.text)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="NETA AI Real Dataset Importer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "command",
        choices=["booths", "voters", "geojson"],
        help="Type of data to import",
    )
    parser.add_argument("file", type=Path, help="Path to data file")
    parser.add_argument(
        "--layer",
        default="constituency_boundary",
        choices=["constituency_boundary", "zone_boundaries", "booth_catchments"],
        help="GeoJSON layer type (required for geojson command)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate without writing to database",
    )
    parser.add_argument(
        "--api-base",
        default=API_BASE,
        help=f"API base URL (default: {API_BASE})",
    )

    args = parser.parse_args()

    if not args.file.exists():
        print(f"ERROR: File not found: {args.file}")
        sys.exit(1)

    if args.command == "booths":
        import_booths(args.file, dry_run=args.dry_run)
    elif args.command == "voters":
        import_voters(args.file, dry_run=args.dry_run)
    elif args.command == "geojson":
        import_geojson(args.file, layer_type=args.layer)


if __name__ == "__main__":
    main()
