-- Migration 004: News Intelligence Schema Extensions
-- Date: 2026-05-26
-- Purpose: Extend news_articles table with Session 05 columns and indexes
-- Note: news_articles base table created in 001_initial_schema.sql

BEGIN;

-- Add narrative_cluster column if not present (may already exist from 001)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'news_articles' AND column_name = 'narrative_cluster'
    ) THEN
        ALTER TABLE news_articles ADD COLUMN narrative_cluster VARCHAR(100);
    END IF;
END $$;

-- Add processed column if not present
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'news_articles' AND column_name = 'processed'
    ) THEN
        ALTER TABLE news_articles ADD COLUMN processed BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
END $$;

-- Add indexes for clustering and processing
CREATE INDEX IF NOT EXISTS idx_news_narrative_cluster
    ON news_articles(narrative_cluster) WHERE narrative_cluster IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_news_processed
    ON news_articles(processed, ingested_at DESC) WHERE processed = TRUE;

CREATE INDEX IF NOT EXISTS idx_news_feed_source_ingested
    ON news_articles(feed_source, ingested_at DESC);

CREATE INDEX IF NOT EXISTS idx_news_ingested_at
    ON news_articles(ingested_at DESC);

-- Verification
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'news_articles') THEN
        RAISE EXCEPTION 'Migration failed: news_articles table not found';
    END IF;
END $$;

COMMIT;
