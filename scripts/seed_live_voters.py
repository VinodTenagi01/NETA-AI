"""
Seed voter_records in the live database from OCR parse cache.

Targets:  live schema (voter_records, not voters)
Columns:  id, booth_id, ec_voter_id, serial_number, name,
          father_or_husband_name, age, gender, is_contacted

Strategy:
  1. Parse OCR cache through existing pipeline
  2. For each normalized voter:
       • If ec_voter_id exists  → UPDATE name/father/age/gender/serial
       • If not exists          → INSERT
  3. Report inserted / updated / skipped / invalid

Usage:
    python scripts/seed_live_voters.py [--dry-run]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import uuid
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg2
from psycopg2.extras import execute_values

from app.voter_roll_ingestion.normalizer import normalize_batch
from app.voter_roll_ingestion.parser import parse_document

# ── Config ────────────────────────────────────────────────────────────────────
DB_DSN = "host=host.docker.internal port=5432 dbname=neta_db user=neta_user password=neta_pass_local"
OCR_CACHE = Path("data/ocr_cache/part1_cols_ocr.json")
BOOTH_ID   = "b0010001-0001-0001-0001-000000000001"
CONSTITUENCY_ID = "11111111-0052-4000-8000-000000000001"
BATCH_SIZE = 200


def deterministic_id(epic: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"AC52-PART1-{epic}"))


def load_voters() -> list:
    cache = json.loads(OCR_CACHE.read_text(encoding="utf-8"))
    pages = [(item[0], item[1]) for item in cache]
    doc = parse_document(pages)
    valid, invalid = normalize_batch(doc.voters)
    print(f"[parse]  raw={len(doc.voters)}  valid={len(valid)}  invalid={invalid}")
    return valid


def run(dry_run: bool) -> None:
    voters = load_voters()
    if not voters:
        print("ERROR: no voters parsed from OCR cache", file=sys.stderr)
        sys.exit(1)

    if dry_run:
        print(f"[dry-run] Would process {len(voters)} voter records. Exiting without DB writes.")
        for v in voters[:5]:
            print(f"  {v.ec_voter_id:12s}  {v.name:30s}  {v.gender}  age={v.age}")
        return

    conn = psycopg2.connect(DB_DSN)
    conn.autocommit = False
    cur = conn.cursor()

    # Fetch existing ec_voter_ids for this booth
    cur.execute("SELECT ec_voter_id FROM voter_records WHERE booth_id = %s", (BOOTH_ID,))
    existing: set[str] = {row[0] for row in cur.fetchall()}
    print(f"[db]     existing voter_records for booth: {len(existing)}")

    to_insert: list[tuple] = []
    to_update: list[tuple] = []

    for v in voters:
        row_id = deterministic_id(v.ec_voter_id)
        if v.ec_voter_id in existing:
            # UPDATE: fix name / father_name / age / gender / serial
            to_update.append((
                (v.name or "UNKNOWN").upper(),
                (v.father_or_husband_name or "").upper() or None,
                v.age,
                v.gender,
                v.serial_number,
                v.ec_voter_id,
            ))
        else:
            to_insert.append((
                row_id,
                BOOTH_ID,
                v.ec_voter_id,
                v.serial_number,
                (v.name or "UNKNOWN").upper(),
                (v.father_or_husband_name or "").upper() or None,
                v.age,
                v.gender,
                False,
            ))

    inserted = updated = 0

    # ── Batch INSERT ─────────────────────────────────────────────
    if to_insert:
        for i in range(0, len(to_insert), BATCH_SIZE):
            batch = to_insert[i : i + BATCH_SIZE]
            try:
                execute_values(
                    cur,
                    """INSERT INTO voter_records
                           (id, booth_id, ec_voter_id, serial_number,
                            name, father_or_husband_name, age, gender, is_contacted)
                       VALUES %s
                       ON CONFLICT (ec_voter_id) DO NOTHING""",
                    batch,
                )
                inserted += cur.rowcount if cur.rowcount >= 0 else len(batch)
            except Exception as exc:
                conn.rollback()
                print(f"[error] batch INSERT failed: {exc}", file=sys.stderr)
                # retry one by one
                for row in batch:
                    try:
                        cur.execute(
                            """INSERT INTO voter_records
                                   (id, booth_id, ec_voter_id, serial_number,
                                    name, father_or_husband_name, age, gender, is_contacted)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                               ON CONFLICT (ec_voter_id) DO NOTHING""",
                            row,
                        )
                        inserted += 1
                    except Exception as e2:
                        print(f"  [skip] {row[2]}: {e2}", file=sys.stderr)

    # ── Batch UPDATE ─────────────────────────────────────────────
    if to_update:
        for i in range(0, len(to_update), BATCH_SIZE):
            batch = to_update[i : i + BATCH_SIZE]
            for row in batch:
                cur.execute(
                    """UPDATE voter_records
                       SET name                  = %s,
                           father_or_husband_name = %s,
                           age                   = %s,
                           gender                = %s,
                           serial_number         = %s
                       WHERE ec_voter_id = %s
                         AND (name = 'UNKNOWN'
                              OR gender IS NULL
                              OR father_or_husband_name IS NULL)""",
                    row,
                )
                updated += cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    total = inserted + updated
    print(f"\n[result] inserted={inserted}  updated={updated}  total={total}")
    print(f"         skipped (already had good data)={len(to_update) - updated}")
    print(f"         voters in OCR parse: {len(voters)}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Seed voter_records from OCR cache")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    run(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
