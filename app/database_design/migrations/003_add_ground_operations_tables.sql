-- Migration 003: Add Ground Operations Tables & Fields
-- Date: 2026-05-23
-- Purpose: Add FieldReport extensions, WorkerAttendance, MoodSnapshot for Session 04
-- Status: Extends existing tables + creates new tables

BEGIN;

-- ============================================================================
-- PART 1: Extend existing field_reports table
-- ============================================================================

-- Add missing columns to field_reports (if not already present)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'field_reports' AND column_name = 'audio_url'
    ) THEN
        ALTER TABLE field_reports ADD COLUMN audio_url TEXT;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'field_reports' AND column_name = 'reported_at'
    ) THEN
        ALTER TABLE field_reports ADD COLUMN reported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'field_reports' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE field_reports ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() ON UPDATE CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Add missing indexes for field_reports
CREATE INDEX IF NOT EXISTS idx_field_reports_reported_by
    ON field_reports(reported_by, created_at DESC);

-- ============================================================================
-- PART 2: Extend existing escalations table
-- ============================================================================

-- Add missing columns to escalations
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'escalations' AND column_name = 'acknowledged_at'
    ) THEN
        ALTER TABLE escalations ADD COLUMN acknowledged_at TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'escalations' AND column_name = 'escalated_to'
    ) THEN
        ALTER TABLE escalations ADD COLUMN escalated_to UUID REFERENCES users(id);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'escalations' AND column_name = 'escalated_at'
    ) THEN
        ALTER TABLE escalations ADD COLUMN escalated_at TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;

-- Update escalations to have unique constraint on field_report_id
DO $$
BEGIN
    -- Remove old constraint if exists (with different name)
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'escalations' AND constraint_name = 'uq_field_report_id'
    ) THEN
        ALTER TABLE escalations DROP CONSTRAINT uq_field_report_id;
    END IF;
END $$;

-- Add unique constraint
ALTER TABLE escalations ADD CONSTRAINT uq_escalation_field_report
    UNIQUE(field_report_id) WHERE field_report_id IS NOT NULL;

-- Add indexes for escalations
CREATE INDEX IF NOT EXISTS idx_escalations_status_deadline
    ON escalations(status, sla_deadline);

CREATE INDEX IF NOT EXISTS idx_escalations_assigned_to
    ON escalations(assigned_to, status);

-- ============================================================================
-- PART 3: Create new WorkerAttendance table
-- ============================================================================

CREATE TABLE IF NOT EXISTS worker_attendance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    booth_id UUID NOT NULL REFERENCES booths(id),
    zone_id UUID NOT NULL REFERENCES campaign_zones(id),
    checked_in_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    checked_out_at TIMESTAMP WITH TIME ZONE,
    gps_lat NUMERIC(9, 6),
    gps_lng NUMERIC(9, 6),
    is_present BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_worker_coords CHECK (
        (gps_lat IS NULL AND gps_lng IS NULL) OR
        (gps_lat IS NOT NULL AND gps_lng IS NOT NULL AND gps_lat >= -90 AND gps_lat <= 90 AND gps_lng >= -180 AND gps_lng <= 180)
    )
);

-- Indexes for worker_attendance
CREATE INDEX IF NOT EXISTS idx_worker_attendance_user_checkin
    ON worker_attendance(user_id, checked_in_at DESC);

CREATE INDEX IF NOT EXISTS idx_worker_attendance_zone_checkin
    ON worker_attendance(zone_id, checked_in_at DESC);

CREATE INDEX IF NOT EXISTS idx_worker_attendance_checkout
    ON worker_attendance(checked_out_at) WHERE checked_out_at IS NOT NULL;

-- ============================================================================
-- PART 4: Create new MoodSnapshot table
-- ============================================================================

CREATE TABLE IF NOT EXISTS mood_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone_id UUID NOT NULL REFERENCES campaign_zones(id),
    snapshot_date DATE NOT NULL,
    avg_sentiment_score NUMERIC(4, 3) NOT NULL,
    positive_pct NUMERIC(5, 2) DEFAULT 0.0,
    neutral_pct NUMERIC(5, 2) DEFAULT 0.0,
    negative_pct NUMERIC(5, 2) DEFAULT 0.0,
    mixed_pct NUMERIC(5, 2) DEFAULT 0.0,
    report_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_mood_score CHECK (avg_sentiment_score >= 0 AND avg_sentiment_score <= 1),
    CONSTRAINT ck_mood_percentages CHECK (positive_pct + neutral_pct + negative_pct + mixed_pct >= 0 AND positive_pct + neutral_pct + negative_pct + mixed_pct <= 100),
    CONSTRAINT uq_mood_zone_date UNIQUE(zone_id, snapshot_date)
);

-- Indexes for mood_snapshots
CREATE INDEX IF NOT EXISTS idx_mood_snapshots_zone_date
    ON mood_snapshots(zone_id, snapshot_date DESC);

CREATE INDEX IF NOT EXISTS idx_mood_snapshots_score
    ON mood_snapshots(avg_sentiment_score);

-- ============================================================================
-- PART 5: Verification
-- ============================================================================

-- Verify tables exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'worker_attendance') THEN
        RAISE EXCEPTION 'Migration failed: worker_attendance table not found';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'mood_snapshots') THEN
        RAISE EXCEPTION 'Migration failed: mood_snapshots table not found';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'field_reports' AND column_name = 'reported_at'
    ) THEN
        RAISE EXCEPTION 'Migration failed: field_reports.reported_at column not found';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'escalations' AND column_name = 'acknowledged_at'
    ) THEN
        RAISE EXCEPTION 'Migration failed: escalations.acknowledged_at column not found';
    END IF;
END $$;

COMMIT;
