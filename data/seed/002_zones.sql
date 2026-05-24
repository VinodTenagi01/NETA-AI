-- ============================================================
-- Seed: Campaign Zones — Serilingampally AC-52
-- PRD Section 11.3
-- ============================================================
DO $$
DECLARE
    v_constituency_id UUID := '11111111-0052-4000-8000-000000000001';
BEGIN

INSERT INTO campaign_zones (id, constituency_id, zone_name, zone_code, key_areas, approx_booth_count, approx_voter_count, description)
VALUES
    ('22222222-0001-4000-8000-000000000001', v_constituency_id, 'Kondapur Zone',   'Z-01', 'Kondapur, Ayyappa Society, Laxmi Cyber City', 55, 52000, 'IT corridor zone — high migrant professional voter concentration'),
    ('22222222-0002-4000-8000-000000000002', v_constituency_id, 'Madhapur Zone',   'Z-02', 'Madhapur, Jubilee Hills Road, Raidurg',        48, 44000, 'Tech hub zone — mixed residential and commercial'),
    ('22222222-0003-4000-8000-000000000003', v_constituency_id, 'Gachibowli Zone', 'Z-03', 'Gachibowli, Financial District, ISB Road',    42, 39000, 'Financial district zone — high-income residential'),
    ('22222222-0004-4000-8000-000000000004', v_constituency_id, 'HITEC City Zone', 'Z-04', 'HITEC City, Whitefields, Kothaguda',          38, 36000, 'Technology park zone — corporate and residential mix'),
    ('22222222-0005-4000-8000-000000000005', v_constituency_id, 'Hafeezpet Zone',  'Z-05', 'Hafeezpet, Miyapur Link Road, RC Puram',      52, 49000, 'Semi-urban zone — mixed income, legacy communities'),
    ('22222222-0006-4000-8000-000000000006', v_constituency_id, 'Chandanagar Zone','Z-06', 'Chandanagar, Lingampally, Chanda Nagar OFB',  45, 43000, 'Defence and government residential zone'),
    ('22222222-0007-4000-8000-000000000007', v_constituency_id, 'Nallagandla Zone','Z-07', 'Nallagandla, Tellapur, Kollur',               35, 33000, 'Peri-urban zone — newer residential developments')
ON CONFLICT (constituency_id, zone_code) DO UPDATE SET
    zone_name           = EXCLUDED.zone_name,
    key_areas           = EXCLUDED.key_areas,
    approx_booth_count  = EXCLUDED.approx_booth_count,
    approx_voter_count  = EXCLUDED.approx_voter_count,
    description         = EXCLUDED.description;

END;
$$;
