-- ================================================================
-- Seed: Real ECI Booth 1 — Part 1, AC-52 Serilingampally
-- Source: Electoral Roll 2025 S29 Telangana (verified from PDF)
-- Booth: GHMC Ward Office, ROOM NO 1, Rai Darga
-- Part:  1  |  Voters: 603M + 554F = 1157 (Serial 1–1187)
-- Location: Rai Darga, near Darga Hussain Shawali, Pin 500104
-- Zone: Z-06 Chandanagar (nearest match for Rai Darga area)
-- ================================================================

DO $$
DECLARE
    v_cid UUID := '11111111-0052-4000-8000-000000000001';
    v_zid UUID := '22222222-0006-4000-8000-000000000006';  -- Z-06 Chandanagar
BEGIN

-- Update booth_number 001 with real ECI data (upsert on unique constraint)
INSERT INTO booths (
    id, constituency_id, zone_id,
    booth_number, booth_name, address,
    location,
    total_voters, male_voters, female_voters, third_gender,
    swing_booth, risk_score, health_score, contact_rate,
    created_at, updated_at
)
VALUES (
    gen_random_uuid(), v_cid, v_zid,
    '001',
    'GHMC Ward Office Room No 1 Rai Darga',
    'GHMC Ward Office, Darga Hussain Shawali, Rai Durga, Serilingampally, Rangareddy, 500104',
    ST_GeogFromText('SRID=4326;POINT(78.3140 17.4920)'),
    1157, 603, 554, 0,
    FALSE, 50.0, 50.0, 0.0,
    NOW(), NOW()
)
ON CONFLICT (constituency_id, booth_number)
DO UPDATE SET
    booth_name     = EXCLUDED.booth_name,
    address        = EXCLUDED.address,
    location       = EXCLUDED.location,
    total_voters   = EXCLUDED.total_voters,
    male_voters    = EXCLUDED.male_voters,
    female_voters  = EXCLUDED.female_voters,
    third_gender   = EXCLUDED.third_gender,
    updated_at     = NOW();

RAISE NOTICE 'Booth 001 (Part 1 — GHMC Ward Office Rai Darga) seeded: 603M + 554F = 1157 voters';

END;
$$;
