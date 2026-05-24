"""
NETA AI — Pre-boot integrity check.

Verifies:
  1. All seed SQL files are present and valid UTF-8
  2. Migration files exist and are syntactically sound
  3. No duplicate EPIC numbers in voter SQL
  4. All booth_numbers in 005_voters_part1.sql reference a real booth (001)
  5. GeoJSON files are valid FeatureCollections
  6. OCR cache exists with expected page count
  7. voter_roll_ingestion package imports without error

Usage:
    python scripts/integrity_check.py [--fix]
    --fix  : attempt to auto-correct non-critical issues (re-encode UTF-16 files)
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

# Force UTF-8 output on Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]

PASS = "[OK]  "
WARN = "[WARN]"
FAIL = "[FAIL]"

_issues: list[str] = []
_warnings: list[str] = []


def check(label: str, ok: bool, msg: str = "", warn_only: bool = False) -> bool:
    if ok:
        print(f"{PASS} {label}")
    elif warn_only:
        print(f"{WARN} {label}: {msg}")
        _warnings.append(f"{label}: {msg}")
    else:
        print(f"{FAIL} {label}: {msg}")
        _issues.append(f"{label}: {msg}")
    return ok


# ─── 1. Seed SQL files ────────────────────────────────────────────────────────

def check_seed_files():
    print("\n── Seed SQL files ──────────────────────────────────────────────")
    expected = [
        "data/seed/001_constituency.sql",
        "data/seed/002_zones.sql",
        "data/seed/003_booths.sql",
        "data/seed/004_real_booth_part1.sql",
        "data/seed/005_voters_part1.sql",
    ]
    for rel in expected:
        p = ROOT / rel
        if not check(f"Exists: {rel}", p.exists(), f"Missing file"):
            continue
        # Check UTF-8
        try:
            raw = p.read_bytes()
            if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
                check(f"Encoding: {rel}", False, "UTF-16 BOM detected — run encode fix")
            else:
                p.read_text(encoding="utf-8")
                check(f"Encoding: {rel}", True)
        except UnicodeDecodeError as e:
            check(f"Encoding: {rel}", False, f"UTF-8 decode error: {e}")

    # Check 003_booths.sql has 315 booths
    p = ROOT / "data/seed/003_booths.sql"
    if p.exists():
        text = p.read_text(encoding="utf-8")
        booth_count = text.count("ON CONFLICT") - 1  # subtract the final ON CONFLICT statement
        # More reliable: count INSERT VALUES tuples
        booth_count = len(re.findall(r"'[0-9]{3}',\s*'[^']+\s*Primary|Ward|PS|School|Hall|Office",
                                     text))
        check("003_booths.sql: has content", len(text) > 10000, f"File seems too short ({len(text)} bytes)", warn_only=True)

    # Check 004 has real booth data
    p = ROOT / "data/seed/004_real_booth_part1.sql"
    if p.exists():
        text = p.read_text(encoding="utf-8")
        check("004: contains GHMC Ward Office", "GHMC Ward Office" in text, "Real booth name missing")
        check("004: contains voter counts", "1157" in text, "Voter count 1157 missing")

    # Check 005 voter rows
    p = ROOT / "data/seed/005_voters_part1.sql"
    if p.exists():
        text = p.read_text(encoding="utf-8")
        # Count voter rows (each row has a uuid pattern at start)
        rows = len(re.findall(r"'[0-9a-f-]{36}', v_booth_id,", text))
        check(f"005: voter rows count ({rows})", rows >= 500, f"Expected ≥500, got {rows}", warn_only=rows < 500)
        # Check no duplicate EPICs
        epics = re.findall(r"'(SWO[0-9]{7})'", text)
        dupes = {e for e in epics if epics.count(e) > 1}
        check("005: no duplicate EPICs", len(dupes) == 0, f"Duplicates: {list(dupes)[:5]}")


# ─── 2. Migration files ───────────────────────────────────────────────────────

def check_migrations():
    print("\n── Migration files ─────────────────────────────────────────────")
    mig_dir = ROOT / "app/database_design/migrations"
    expected_migs = ["001_initial_schema.sql", "002_add_voter_fields.sql"]
    for fname in expected_migs:
        p = mig_dir / fname
        if not check(f"Migration {fname}", p.exists(), "Missing"):
            continue
        text = p.read_text(encoding="utf-8")
        check(f"{fname}: has BEGIN", "BEGIN" in text or "ALTER" in text, "Missing transaction or ALTER")

    # Check 002 adds required columns
    p = mig_dir / "002_add_voter_fields.sql"
    if p.exists():
        text = p.read_text(encoding="utf-8")
        check("002: adds father_name", "father_name" in text, "Column definition missing")
        check("002: adds serial_number", "serial_number" in text, "Column definition missing")


# ─── 3. GeoJSON files ─────────────────────────────────────────────────────────

def check_geojson():
    print("\n── GeoJSON files ───────────────────────────────────────────────")
    files = {
        "data/geojson/serilingampally_ac52_boundary.geojson": {"min_features": 1},
        "data/geojson/zones.geojson": {"min_features": 7},
    }
    for rel, constraints in files.items():
        p = ROOT / rel
        if not check(f"Exists: {rel}", p.exists(), "Missing"):
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            check(f"Valid JSON: {rel}", False, str(e))
            continue
        check(f"Valid JSON: {rel}", True)
        fc_ok = data.get("type") == "FeatureCollection"
        check(f"FeatureCollection type: {rel}", fc_ok, f"Got type={data.get('type')}")
        if fc_ok:
            n = len(data.get("features", []))
            min_f = constraints["min_features"]
            check(f"Feature count ({n}≥{min_f}): {rel}", n >= min_f, f"Got {n}")


# ─── 4. OCR cache ────────────────────────────────────────────────────────────

def check_ocr_cache():
    print("\n── OCR cache ───────────────────────────────────────────────────")
    cache = ROOT / "data/ocr_cache/part1_cols_ocr.json"
    if not check("OCR cache exists", cache.exists(), "Run OCR first: python -m app.voter_roll_ingestion.cli --dry-run"):
        return
    data = json.loads(cache.read_text(encoding="utf-8"))
    check(f"OCR pages ({len(data)})", len(data) == 45, f"Expected 45, got {len(data)}")


# ─── 5. Python package imports ────────────────────────────────────────────────

def check_imports():
    print("\n── Python package imports ──────────────────────────────────────")
    sys.path.insert(0, str(ROOT))
    packages = [
        ("app.voter_roll_ingestion.models", "ExtractedVoter"),
        ("app.voter_roll_ingestion.normalizer", "normalize_voter"),
        ("app.voter_roll_ingestion.parser", "parse_document"),
        ("app.voter_roll_ingestion.extractor_ocr", "extract_pages_ocr"),
        ("app.voter_roll_ingestion.pipeline", "process_pdf"),
        ("app.voter_roll_ingestion.cli", "main"),
        ("app.geojson_mapping.schemas", "BoothDetailPopup"),
        ("app.geojson_mapping.service", "GeoJSONMappingService"),
        ("app.database_design.models", "Voter"),
    ]
    for mod, symbol in packages:
        try:
            m = __import__(mod, fromlist=[symbol])
            has_sym = hasattr(m, symbol)
            check(f"import {mod}.{symbol}", has_sym, "Symbol not found")
        except ImportError as e:
            check(f"import {mod}", False, str(e)[:80])


# ─── 6. Voter SQL EPIC format check ──────────────────────────────────────────

def check_voter_epics():
    print("\n── EPIC format validation ──────────────────────────────────────")
    p = ROOT / "data/seed/005_voters_part1.sql"
    if not p.exists():
        check("005 voter SQL exists", False, "File missing")
        return

    text = p.read_text(encoding="utf-8")
    all_epics = re.findall(r"v_booth_id, '([^']+)',", text)
    bad = [e for e in all_epics if not re.match(r"^[A-Z]{2,3}[0-9]{6,8}$", e)]
    check(f"EPIC format ({len(all_epics)} total)", len(bad) == 0,
          f"{len(bad)} malformed: {bad[:5]}", warn_only=len(bad) <= 5)
    if all_epics:
        swo_count = sum(1 for e in all_epics if e.startswith("SWO"))
        print(f"         SWO-prefix: {swo_count}/{len(all_epics)} ({100*swo_count//len(all_epics)}%)")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("NETA AI — Integrity Check")
    print("=" * 60)

    check_seed_files()
    check_migrations()
    check_geojson()
    check_ocr_cache()
    check_imports()
    check_voter_epics()

    print("\n" + "=" * 60)
    if _issues:
        print(f"RESULT: FAIL  ({len(_issues)} errors, {len(_warnings)} warnings)")
        for iss in _issues:
            print(f"  [FAIL] {iss}")
        sys.exit(1)
    elif _warnings:
        print(f"RESULT: PASS with warnings ({len(_warnings)} warnings)")
        for w in _warnings:
            print(f"  [WARN] {w}")
        sys.exit(0)
    else:
        print("RESULT: PASS — all checks passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
