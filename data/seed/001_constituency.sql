-- ============================================================
-- Seed: Constituency — Serilingampally AC-52
-- ============================================================
INSERT INTO constituencies (id, name, state, ac_number, total_booths, total_voters, geojson_url)
VALUES (
    '11111111-0052-4000-8000-000000000001',
    'Serilingampally',
    'Telangana',
    '52',
    315,
    296000,
    '/api/v1/geo/constituency/52/boundary'
)
ON CONFLICT (ac_number) DO UPDATE SET
    total_booths = EXCLUDED.total_booths,
    total_voters = EXCLUDED.total_voters,
    geojson_url  = EXCLUDED.geojson_url;
