-- Migration 002: Add father_name and serial_number to voters table
-- These fields are required by the voter roll OCR ingestion pipeline.

BEGIN;

ALTER TABLE voters
    ADD COLUMN IF NOT EXISTS father_name    VARCHAR(255),
    ADD COLUMN IF NOT EXISTS serial_number  INTEGER;

-- Index for fast lookup within a booth by serial number
CREATE INDEX IF NOT EXISTS idx_voters_serial
    ON voters (booth_id, serial_number);

-- Verify
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'voters' AND column_name = 'father_name'
    ) THEN
        RAISE EXCEPTION 'Migration 002 failed: father_name column not found';
    END IF;
    RAISE NOTICE 'Migration 002 applied: voters.father_name + serial_number added';
END;
$$;

COMMIT;
