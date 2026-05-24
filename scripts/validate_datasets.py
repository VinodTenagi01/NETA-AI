#!/usr/bin/env python3
"""
NETA AI Dataset Validation Script
Validates booth CSV, voter roll CSV, and GeoJSON files before DB import.

Usage:
    python scripts/validate_datasets.py --booths data/imports/booths.csv
    python scripts/validate_datasets.py --voters data/imports/voters.csv
    python scripts/validate_datasets.py --geojson data/imports/boundary.geojson
    python scripts/validate_datasets.py --all data/imports/

Output: validation_report_YYYYMMDD_HHMMSS.json
"""

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

# Serilingampally AC-52 constraints
CONSTITUENCY_BOUNDS = {"lat_min": 17.40, "lat_max": 17.55, "lng_min": 78.26, "lng_max": 78.42}
EXPECTED_BOOTH_RANGE = (280, 350)
EXPECTED_VOTER_RANGE = (250_000, 350_000)

BOOTH_REQUIRED_COLS = {"booth_number", "booth_name", "total_voters", "female_voters", "male_voters"}
VOTER_REQUIRED_COLS = {"booth_number", "voter_id", "full_name", "gender", "age"}


def validate_booths_csv(path: Path) -> dict:
    report = {
        "file": str(path),
        "type": "booths_csv",
        "status": "ok",
        "total_rows": 0,
        "errors": [],
        "warnings": [],
        "stats": {},
    }

    if not path.exists():
        report["status"] = "failed"
        report["errors"].append(f"File not found: {path}")
        return report

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = set(h.strip().lower() for h in (reader.fieldnames or []))

        missing = BOOTH_REQUIRED_COLS - headers
        if missing:
            report["status"] = "failed"
            report["errors"].append(f"Missing required columns: {missing}")
            return report

        rows = list(reader)

    report["total_rows"] = len(rows)

    if not EXPECTED_BOOTH_RANGE[0] <= len(rows) <= EXPECTED_BOOTH_RANGE[1]:
        report["warnings"].append(
            f"Expected {EXPECTED_BOOTH_RANGE[0]}–{EXPECTED_BOOTH_RANGE[1]} booths, got {len(rows)}"
        )

    booth_numbers: dict[str, int] = {}
    total_voters_sum = 0
    invalid_coords = []
    zero_voter_booths = []

    for idx, row in enumerate(rows, 2):
        r = {k.strip().lower(): v.strip() for k, v in row.items()}
        bn = r.get("booth_number", "").strip()

        # Duplicate check
        if bn in booth_numbers:
            report["errors"].append(f"Row {idx}: duplicate booth_number '{bn}' (first seen at row {booth_numbers[bn]})")
        else:
            booth_numbers[bn] = idx

        # Voter count validation
        try:
            tv = int(r.get("total_voters", 0))
            fv = int(r.get("female_voters", 0))
            mv = int(r.get("male_voters", 0))
            total_voters_sum += tv

            if tv <= 0:
                zero_voter_booths.append(bn)
            if fv + mv > tv:
                report["errors"].append(f"Row {idx}: booth {bn}: female+male ({fv+mv}) > total_voters ({tv})")
        except ValueError:
            report["errors"].append(f"Row {idx}: booth {bn}: non-integer voter counts")

        # Coordinate validation (optional fields)
        lat_str = r.get("latitude")
        lng_str = r.get("longitude")
        if lat_str and lng_str:
            try:
                lat, lng = float(lat_str), float(lng_str)
                b = CONSTITUENCY_BOUNDS
                if not (b["lat_min"] <= lat <= b["lat_max"] and b["lng_min"] <= lng <= b["lng_max"]):
                    invalid_coords.append(bn)
            except ValueError:
                report["errors"].append(f"Row {idx}: booth {bn}: non-numeric coordinates")

    if not EXPECTED_VOTER_RANGE[0] <= total_voters_sum <= EXPECTED_VOTER_RANGE[1]:
        report["warnings"].append(
            f"Total voters sum ({total_voters_sum:,}) outside expected range "
            f"{EXPECTED_VOTER_RANGE[0]:,}–{EXPECTED_VOTER_RANGE[1]:,}"
        )

    if zero_voter_booths:
        report["warnings"].append(f"{len(zero_voter_booths)} booths with total_voters=0: {zero_voter_booths[:5]}...")

    if invalid_coords:
        report["warnings"].append(f"{len(invalid_coords)} booths have coordinates outside AC-52 bounds")

    report["stats"] = {
        "unique_booth_numbers": len(booth_numbers),
        "total_voters_sum": total_voters_sum,
        "booths_with_coordinates": sum(
            1 for r in rows
            if r.get("latitude") and r.get("longitude")
        ),
        "invalid_coordinate_count": len(invalid_coords),
    }

    if report["errors"]:
        report["status"] = "failed"
    elif report["warnings"]:
        report["status"] = "warnings"

    return report


def validate_voters_csv(path: Path) -> dict:
    report = {
        "file": str(path),
        "type": "voters_csv",
        "status": "ok",
        "total_rows": 0,
        "errors": [],
        "warnings": [],
        "stats": {},
    }

    if not path.exists():
        report["status"] = "failed"
        report["errors"].append(f"File not found: {path}")
        return report

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = set(h.strip().lower() for h in (reader.fieldnames or []))

        missing = VOTER_REQUIRED_COLS - headers
        if missing:
            report["status"] = "failed"
            report["errors"].append(f"Missing required columns: {missing}")
            return report

        rows = list(reader)

    report["total_rows"] = len(rows)

    voter_ids: dict[str, int] = {}
    gender_counts: dict[str, int] = {"M": 0, "F": 0, "O": 0, "invalid": 0}
    booths_in_file: set[str] = set()
    age_errors = []
    GENDER_MAP = {"M", "F", "O", "MALE", "FEMALE", "OTHER"}

    for idx, row in enumerate(rows, 2):
        r = {k.strip().lower(): v.strip() for k, v in row.items()}
        vid = r.get("voter_id", "").strip().upper()
        booth = r.get("booth_number", "").strip()
        gender = r.get("gender", "").strip().upper()

        if not vid:
            report["errors"].append(f"Row {idx}: empty voter_id")
            continue

        if vid in voter_ids:
            report["errors"].append(f"Row {idx}: duplicate voter_id '{vid}' (first at row {voter_ids[vid]})")
        else:
            voter_ids[vid] = idx

        booths_in_file.add(booth)

        if gender not in GENDER_MAP:
            gender_counts["invalid"] += 1
        elif gender in {"M", "MALE"}:
            gender_counts["M"] += 1
        elif gender in {"F", "FEMALE"}:
            gender_counts["F"] += 1
        else:
            gender_counts["O"] += 1

        age_str = r.get("age", "")
        try:
            age = int(age_str)
            if not 18 <= age <= 120:
                age_errors.append(f"Row {idx}: age {age} out of range for voter {vid}")
        except ValueError:
            report["errors"].append(f"Row {idx}: non-integer age '{age_str}' for voter {vid}")

    if age_errors:
        report["warnings"].extend(age_errors[:20])
        if len(age_errors) > 20:
            report["warnings"].append(f"... and {len(age_errors) - 20} more age warnings")

    if gender_counts["invalid"] > 0:
        report["warnings"].append(
            f"{gender_counts['invalid']} voters have unrecognized gender codes"
        )

    report["stats"] = {
        "unique_voter_ids": len(voter_ids),
        "unique_booth_numbers": len(booths_in_file),
        "gender_distribution": gender_counts,
    }

    if report["errors"]:
        report["status"] = "failed"
    elif report["warnings"]:
        report["status"] = "warnings"

    return report


def validate_geojson(path: Path) -> dict:
    report = {
        "file": str(path),
        "type": "geojson",
        "status": "ok",
        "total_features": 0,
        "errors": [],
        "warnings": [],
        "stats": {},
    }

    if not path.exists():
        report["status"] = "failed"
        report["errors"].append(f"File not found: {path}")
        return report

    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        report["status"] = "failed"
        report["errors"].append(f"Invalid JSON: {e}")
        return report

    if data.get("type") != "FeatureCollection":
        report["errors"].append("Root object must be a GeoJSON FeatureCollection")
        report["status"] = "failed"
        return report

    features = data.get("features", [])
    report["total_features"] = len(features)

    geom_types: dict[str, int] = {}
    missing_geometry = 0

    for i, feat in enumerate(features):
        if feat.get("type") != "Feature":
            report["errors"].append(f"Feature {i}: type is not 'Feature'")
        geom = feat.get("geometry")
        if not geom:
            missing_geometry += 1
            continue
        gt = geom.get("type")
        geom_types[gt] = geom_types.get(gt, 0) + 1

    if missing_geometry:
        report["warnings"].append(f"{missing_geometry} features have null geometry")

    report["stats"]["geometry_types"] = geom_types

    if report["errors"]:
        report["status"] = "failed"
    elif report["warnings"]:
        report["status"] = "warnings"

    return report


def main():
    parser = argparse.ArgumentParser(description="NETA AI Dataset Validator")
    parser.add_argument("--booths", type=Path, help="Path to booths CSV")
    parser.add_argument("--voters", type=Path, help="Path to voter roll CSV")
    parser.add_argument("--geojson", type=Path, help="Path to GeoJSON file")
    parser.add_argument("--all", type=Path, dest="data_dir", help="Scan a directory for all importable files")
    parser.add_argument("--output", type=Path, default=None, help="Save JSON report to file")
    args = parser.parse_args()

    reports = []

    if args.booths:
        reports.append(validate_booths_csv(args.booths))
    if args.voters:
        reports.append(validate_voters_csv(args.voters))
    if args.geojson:
        reports.append(validate_geojson(args.geojson))
    if args.data_dir:
        d = args.data_dir
        for p in d.glob("*.csv"):
            # Heuristic: detect file type by headers
            with open(p, newline="", encoding="utf-8-sig") as f:
                headers = set(h.strip().lower() for h in (csv.DictReader(f).fieldnames or []))
            if "voter_id" in headers:
                reports.append(validate_voters_csv(p))
            elif "booth_number" in headers:
                reports.append(validate_booths_csv(p))
        for p in d.glob("*.geojson"):
            reports.append(validate_geojson(p))

    if not reports:
        print("No input files specified. Use --booths, --voters, --geojson, or --all.")
        sys.exit(1)

    # Print summary
    overall_ok = all(r["status"] in {"ok", "warnings"} for r in reports)
    print(f"\n{'='*60}")
    print("NETA AI Dataset Validation Report")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    for r in reports:
        status_icon = {"ok": "[OK]", "warnings": "[WARN]", "failed": "[FAIL]"}.get(r["status"], "[?]")
        print(f"\n{status_icon} {r['file']}")
        print(f"   Type: {r['type']} | Rows/Features: {r.get('total_rows', r.get('total_features', '?'))}")
        if r.get("errors"):
            for e in r["errors"][:5]:
                print(f"   ERROR: {e}")
        if r.get("warnings"):
            for w in r["warnings"][:5]:
                print(f"   WARN:  {w}")
        if r.get("stats"):
            for k, v in r["stats"].items():
                print(f"   STAT:  {k}: {v}")

    print(f"\n{'='*60}")
    print(f"OVERALL: {'PASS' if overall_ok else 'FAIL'}")
    print(f"{'='*60}\n")

    if args.output:
        result = {"generated_at": datetime.now().isoformat(), "overall": "pass" if overall_ok else "fail", "reports": reports}
        args.output.write_text(json.dumps(result, indent=2))
        print(f"Report saved to {args.output}")

    sys.exit(0 if overall_ok else 1)


if __name__ == "__main__":
    main()
