-- ================================================================
-- Migration 005: Serilingampally AC-52 Real Constituency & Booth
-- Applies to:  live schema (alembic version 004 → 005)
-- Targets:     constituencies, booths, voter_records
-- Source:      ECI Electoral Roll 2025, S29 Telangana, AC-52 Part 1
-- ================================================================

BEGIN;

-- ── 1. Serilingampally AC-52 constituency ───────────────────────
INSERT INTO constituencies (
    id,
    name,
    full_name,
    state,
    assembly_number,
    constituency_type,
    total_voters,
    total_booths,
    is_active,
    created_at,
    updated_at
) VALUES (
    '11111111-0052-4000-8000-000000000001',
    'Serilingampally',
    'Serilingampally (GENERAL) AC-52',
    'Telangana',
    52,
    'assembly',
    NULL,   -- will be updated after full roll import
    315,    -- confirmed from ECI Part list
    true,
    NOW(),
    NOW()
)
ON CONFLICT (id) DO UPDATE
    SET full_name     = EXCLUDED.full_name,
        assembly_number = EXCLUDED.assembly_number,
        total_booths  = EXCLUDED.total_booths,
        updated_at    = NOW();

-- ── 2. Booth 001: GHMC Ward Office, Rai Darga ─────────────────
-- Real ECI data: Part 1, Serial 1-1187, Male 603, Female 554, Total 1157
INSERT INTO booths (
    id,
    constituency_id,
    code,
    name,
    address,
    zone,
    latitude,
    longitude,
    total_voters,
    status,
    is_covered,
    created_at,
    updated_at
) VALUES (
    'b0010001-0001-0001-0001-000000000001',
    '11111111-0052-4000-8000-000000000001',
    'AC52-001',
    'GHMC Ward Office Room No 1 Rai Darga',
    'GHMC Ward Office, Darga Hussain Shawali, Rai Durga, Serilingampally, Rangareddy, 500104',
    'Serilingampally',
    17.4920,
    78.3140,
    1157,
    'swing',
    false,
    NOW(),
    NOW()
)
ON CONFLICT (constituency_id, code) DO UPDATE
    SET name         = EXCLUDED.name,
        address      = EXCLUDED.address,
        latitude     = EXCLUDED.latitude,
        longitude    = EXCLUDED.longitude,
        total_voters = EXCLUDED.total_voters,
        updated_at   = NOW();

-- ── 3. Demographic profile for Booth 001 ──────────────────────
-- Source: ECI Electoral Roll 2025 header page
-- Male: 603 (52.1%), Female: 554 (47.9%), Total: 1157
INSERT INTO demographic_profiles (
    id,
    booth_id,
    male_pct,
    female_pct,
    data_source,
    survey_year,
    confidence_score,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'b0010001-0001-0001-0001-000000000001',
    52.12,   -- 603/1157 * 100
    47.88,   -- 554/1157 * 100
    'eci_electoral_roll_2025',
    2025,
    0.99,
    NOW(),
    NOW()
)
ON CONFLICT (booth_id, data_source, survey_year) DO UPDATE
    SET male_pct         = EXCLUDED.male_pct,
        female_pct       = EXCLUDED.female_pct,
        confidence_score = EXCLUDED.confidence_score,
        updated_at       = NOW();

-- ── 4. Fix existing SWD voter records ─────────────────────────
-- 489 records imported in a prior session have:
--   • ec_voter_id prefix 'SWD' (OCR error for 'SWO')
--   • name = 'UNKNOWN'
--   • booth_id pointing to Chandanagar B-001 (wrong constituency)
-- Correct them to use the real Serilingampally booth.
UPDATE voter_records
SET booth_id    = 'b0010001-0001-0001-0001-000000000001',
    ec_voter_id = 'SWO' || SUBSTRING(ec_voter_id FROM 4)  -- SWD→SWO
WHERE booth_id  = 'f95107fe-627d-40ed-9289-db04a1d61b2b'  -- Chandanagar B-001
  AND ec_voter_id LIKE 'SWD%';

-- Fix the handful of 'WD' prefix records (S dropped in OCR)
-- e.g. WD3915230 (9 chars) cannot be safely fixed without knowing the S prefix
-- Mark them for review by setting a note in name field
UPDATE voter_records
SET name = 'UNKNOWN-BAD-EPIC'
WHERE booth_id = 'f95107fe-627d-40ed-9289-db04a1d61b2b'
  AND ec_voter_id NOT LIKE 'SWO%'
  AND ec_voter_id NOT LIKE 'SWD%';

-- ── 5. Alembic version bump ─────────────────────────────────────
UPDATE alembic_version SET version_num = '005';

COMMIT;
