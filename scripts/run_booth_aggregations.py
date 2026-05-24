"""
Booth-wise aggregation runner.

Populates:
  • booth_daily_pulse  — today's voter contact snapshot for AC52-001
  • intelligence_scores — constituency-level data quality score
  • booths.total_voters — syncs from actual voter_records count

Usage:
    python scripts/run_booth_aggregations.py
"""
from __future__ import annotations

import io
import sys
from datetime import date

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import psycopg2
import uuid

DB_DSN = "host=host.docker.internal port=5432 dbname=neta_db user=neta_user password=neta_pass_local"
BOOTH_ID = "b0010001-0001-0001-0001-000000000001"
CONSTITUENCY_ID = "11111111-0052-4000-8000-000000000001"
TODAY = date.today()


def run() -> None:
    conn = psycopg2.connect(DB_DSN)
    conn.autocommit = False
    cur = conn.cursor()

    # ── 1. Read current voter stats ───────────────────────────
    cur.execute("""
        SELECT
            count(*)                                               AS total_imported,
            sum(CASE WHEN is_contacted THEN 1 ELSE 0 END)         AS contacted,
            sum(CASE WHEN gender = 'M' THEN 1 ELSE 0 END)         AS male,
            sum(CASE WHEN gender = 'F' THEN 1 ELSE 0 END)         AS female,
            sum(CASE WHEN gender IS NULL THEN 1 ELSE 0 END)       AS gender_missing,
            sum(CASE WHEN age IS NOT NULL THEN 1 ELSE 0 END)      AS age_known,
            sum(CASE WHEN name = 'UNKNOWN' THEN 1 ELSE 0 END)     AS unnamed,
            sum(CASE WHEN father_or_husband_name IS NOT NULL
                      THEN 1 ELSE 0 END)                          AS father_known
        FROM voter_records
        WHERE booth_id = %s
    """, (BOOTH_ID,))
    stats = cur.fetchone()
    (total_imp, contacted, male, female, gender_miss,
     age_known, unnamed, father_known) = stats

    eci_total = 1157
    coverage_pct = round(total_imp / eci_total * 100, 2)
    name_quality_pct = round((total_imp - unnamed) / total_imp * 100, 2) if total_imp else 0
    gender_quality_pct = round((male + female) / total_imp * 100, 2) if total_imp else 0

    print(f"Voter Stats for Booth AC52-001:")
    print(f"  imported={total_imp}, eci_total={eci_total}, coverage={coverage_pct}%")
    print(f"  named={total_imp - unnamed}/{total_imp} ({name_quality_pct}%)")
    print(f"  gender_known={male + female}/{total_imp} ({gender_quality_pct}%)")
    print(f"  male={male}, female={female}, gender_missing={gender_miss}")
    print(f"  age_known={age_known}, father_known={father_known}")

    # ── 2. Upsert booth_daily_pulse ───────────────────────────
    cur.execute("""
        INSERT INTO booth_daily_pulse
            (id, booth_id, pulse_date, avg_mood_score, report_count,
             voter_contact_count, opposition_activity_level, notes, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (booth_id, pulse_date) DO UPDATE
            SET voter_contact_count      = EXCLUDED.voter_contact_count,
                notes                    = EXCLUDED.notes
    """, (
        str(uuid.uuid4()),
        BOOTH_ID,
        TODAY,
        None,           # avg_mood_score: no field reports yet
        0,              # report_count: no worker reports yet
        contacted,      # voter_contact_count from is_contacted flag
        "none",
        f"Auto-aggregated. Imported {total_imp}/{eci_total} voters ({coverage_pct}% coverage). "
        f"Name quality: {name_quality_pct}%, Gender known: {gender_quality_pct}%",
    ))
    print(f"\n[booth_daily_pulse] upserted for {TODAY}")

    # ── 3. Update booth.total_voters to reflect ECI confirmed count ──
    cur.execute("""
        UPDATE booths SET total_voters = 1157 WHERE id = %s
    """, (BOOTH_ID,))
    print(f"[booths] total_voters confirmed = 1157")

    # ── 4. Intelligence score: data_quality for the constituency ──
    data_quality_score = round(
        (coverage_pct / 100 * 0.4) +           # 40% weight: coverage
        (name_quality_pct / 100 * 0.35) +       # 35% weight: name quality
        (gender_quality_pct / 100 * 0.25),      # 25% weight: gender completeness
        4
    )
    components = {
        "coverage_pct": coverage_pct,
        "name_quality_pct": name_quality_pct,
        "gender_quality_pct": gender_quality_pct,
        "total_imported": total_imp,
        "eci_total": eci_total,
        "male": male,
        "female": female,
        "age_known": age_known,
    }
    import json
    cur.execute("""
        INSERT INTO intelligence_scores
            (id, constituency_id, booth_id, score_date, score_type, score, components, computed_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (constituency_id, booth_id, score_date, score_type) DO UPDATE
            SET score      = EXCLUDED.score,
                components = EXCLUDED.components,
                computed_at = NOW()
    """, (
        str(uuid.uuid4()),
        CONSTITUENCY_ID,
        BOOTH_ID,
        TODAY,
        "data_quality",
        data_quality_score,
        json.dumps(components),
    ))
    print(f"[intelligence_scores] data_quality={data_quality_score:.4f} for {TODAY}")

    # ── 5. Update constituency total_voters ───────────────────
    cur.execute("""
        UPDATE constituencies
        SET total_voters = (
            SELECT sum(b.total_voters) FROM booths b WHERE b.constituency_id = %s
        ),
        updated_at = NOW()
        WHERE id = %s
    """, (CONSTITUENCY_ID, CONSTITUENCY_ID))
    print(f"[constituencies] total_voters aggregated from booth data")

    conn.commit()
    cur.close()
    conn.close()
    print("\nAll aggregations committed.")


if __name__ == "__main__":
    run()
