-- ============================================================
-- NETA AI — Initial Schema Migration
-- Constituency: Serilingampally AC-52, Telangana
-- Version: 001
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================
-- 1. CONSTITUENCIES
-- ============================================================
CREATE TABLE IF NOT EXISTS constituencies (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    state           VARCHAR(100) NOT NULL,
    ac_number       VARCHAR(10) NOT NULL UNIQUE,
    total_booths    INTEGER,
    total_voters    INTEGER,
    geojson_url     TEXT,
    boundary_geojson JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 2. CAMPAIGN ZONES
-- ============================================================
CREATE TABLE IF NOT EXISTS campaign_zones (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    constituency_id     UUID NOT NULL REFERENCES constituencies(id) ON DELETE CASCADE,
    zone_name           VARCHAR(100) NOT NULL,
    zone_code           VARCHAR(10) NOT NULL,
    description         TEXT,
    boundary_geojson    JSONB,
    key_areas           TEXT,
    approx_booth_count  INTEGER,
    approx_voter_count  INTEGER,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (constituency_id, zone_code)
);

-- ============================================================
-- 3. USERS (depends on campaign_zones for zone_id FK)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name       VARCHAR(255) NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    phone           VARCHAR(15),
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(50) NOT NULL CHECK (role IN (
                        'super_admin','campaign_manager','ground_commander',
                        'data_analyst','field_worker','candidate')),
    zone_id         UUID REFERENCES campaign_zones(id),
    is_active       BOOLEAN DEFAULT TRUE NOT NULL,
    mfa_secret      VARCHAR(255),
    mfa_enabled     BOOLEAN DEFAULT FALSE NOT NULL,
    last_login      TIMESTAMPTZ,
    login_attempts  INTEGER DEFAULT 0 NOT NULL,
    locked_until    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ============================================================
-- 4. BOOTHS
-- ============================================================
CREATE TABLE IF NOT EXISTS booths (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    constituency_id     UUID NOT NULL REFERENCES constituencies(id),
    zone_id             UUID REFERENCES campaign_zones(id),
    booth_number        VARCHAR(10) NOT NULL,
    booth_name          VARCHAR(255),
    location            GEOGRAPHY(POINT, 4326),
    address             TEXT,
    total_voters        INTEGER DEFAULT 0,
    female_voters       INTEGER DEFAULT 0,
    male_voters         INTEGER DEFAULT 0,
    third_gender        INTEGER DEFAULT 0,
    assigned_commander  UUID REFERENCES users(id),
    risk_score          DECIMAL(5,2) DEFAULT 50.0,
    contact_rate        DECIMAL(5,2) DEFAULT 0.0,
    health_score        DECIMAL(5,2) DEFAULT 50.0,
    swing_booth         BOOLEAN DEFAULT FALSE NOT NULL,
    historical_margin   DECIMAL(5,2),
    last_report_at      TIMESTAMPTZ,
    last_contact_at     TIMESTAMPTZ,
    catchment_geojson   JSONB,
    created_at          TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at          TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE (constituency_id, booth_number)
);

CREATE INDEX IF NOT EXISTS idx_booths_zone ON booths(zone_id);
CREATE INDEX IF NOT EXISTS idx_booths_constituency ON booths(constituency_id);
CREATE INDEX IF NOT EXISTS idx_booths_risk_score ON booths(risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_booths_location ON booths USING GIST (location);

-- ============================================================
-- 5. BOOTH VOLUNTEERS
-- ============================================================
CREATE TABLE IF NOT EXISTS booth_volunteers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booth_id        UUID NOT NULL REFERENCES booths(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES users(id),
    volunteer_name  VARCHAR(255) NOT NULL,
    phone           VARCHAR(15),
    role            VARCHAR(30) CHECK (role IN ('BOOTH_AGENT','VOTER_CONTACT','TRANSPORT','COORDINATOR')),
    shift_start     TIME,
    shift_end       TIME,
    notes           TEXT,
    is_confirmed    BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 6. FIELD REPORTS
-- ============================================================
CREATE TABLE IF NOT EXISTS field_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booth_id        UUID NOT NULL REFERENCES booths(id),
    reported_by     UUID NOT NULL REFERENCES users(id),
    category        VARCHAR(50) NOT NULL CHECK (category IN (
                        'VOTER_MOOD','INFRASTRUCTURE','OPPOSITION_ACTIVITY',
                        'SECURITY','LOGISTICS','OTHER')),
    description     TEXT NOT NULL CHECK (length(description) <= 500),
    severity        SMALLINT NOT NULL CHECK (severity BETWEEN 1 AND 5),
    voter_sentiment VARCHAR(20) CHECK (voter_sentiment IN (
                        'POSITIVE','NEUTRAL','NEGATIVE','MIXED')),
    sentiment_score DECIMAL(4,3),
    photo_url       TEXT,
    gps_lat         DECIMAL(9,6),
    gps_lng         DECIMAL(9,6),
    processed       BOOLEAN DEFAULT FALSE NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_field_reports_booth_created ON field_reports(booth_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_field_reports_severity ON field_reports(severity) WHERE severity >= 4;

-- ============================================================
-- 7. NEWS ARTICLES
-- ============================================================
CREATE TABLE IF NOT EXISTS news_articles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feed_source         VARCHAR(100) NOT NULL,
    feed_tier           SMALLINT NOT NULL CHECK (feed_tier IN (1, 2, 3)),
    title               TEXT NOT NULL,
    url                 TEXT NOT NULL UNIQUE,
    body_excerpt        TEXT,
    language            VARCHAR(10) DEFAULT 'en',
    published_at        TIMESTAMPTZ,
    ingested_at         TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    sentiment_polarity  DECIMAL(4,3),
    political_tone      VARCHAR(30) CHECK (political_tone IN (
                            'PRO_INCUMBENT','NEUTRAL','ANTI_INCUMBENT')),
    impact_score        DECIMAL(4,2),
    entity_tags         JSONB DEFAULT '[]',
    narrative_cluster   VARCHAR(100),
    processed           BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_news_published_sentiment ON news_articles(published_at DESC, sentiment_polarity);
CREATE INDEX IF NOT EXISTS idx_news_impact ON news_articles(impact_score DESC) WHERE impact_score >= 5.0;

-- ============================================================
-- 8. ALERTS
-- ============================================================
CREATE TABLE IF NOT EXISTS alerts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_type      VARCHAR(100) NOT NULL,
    severity        VARCHAR(20) NOT NULL CHECK (severity IN ('CRITICAL','WARNING','INFO')),
    source_module   VARCHAR(50) NOT NULL,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    affected_booths UUID[],
    meta            JSONB DEFAULT '{}',
    acknowledged    BOOLEAN DEFAULT FALSE NOT NULL,
    acknowledged_by UUID REFERENCES users(id),
    acknowledged_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_severity_created ON alerts(severity, created_at DESC) WHERE NOT acknowledged;

-- ============================================================
-- 9. ESCALATIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS escalations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id            UUID REFERENCES alerts(id),
    field_report_id     UUID REFERENCES field_reports(id),
    assigned_to         UUID NOT NULL REFERENCES users(id),
    assigned_by         UUID REFERENCES users(id),
    status              VARCHAR(20) NOT NULL DEFAULT 'NEW'
                            CHECK (status IN ('NEW','ASSIGNED','IN_PROGRESS','RESOLVED','CLOSED')),
    sla_minutes         INTEGER NOT NULL,
    sla_deadline        TIMESTAMPTZ NOT NULL,
    whatsapp_sent       BOOLEAN DEFAULT FALSE NOT NULL,
    reminder_sent       BOOLEAN DEFAULT FALSE NOT NULL,
    resolved_at         TIMESTAMPTZ,
    resolution_notes    TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at          TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- ============================================================
-- 10. INTELLIGENCE BRIEFS
-- ============================================================
CREATE TABLE IF NOT EXISTS intelligence_briefs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brief_date          DATE NOT NULL UNIQUE,
    executive_summary   TEXT NOT NULL,
    top_risks           JSONB NOT NULL DEFAULT '[]',
    opportunity_zones   JSONB NOT NULL DEFAULT '[]',
    recommended_actions JSONB NOT NULL DEFAULT '[]',
    narrative_digest    TEXT,
    win_probability     DECIMAL(5,2),
    generated_at        TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    delivered_at        TIMESTAMPTZ,
    delivery_status     VARCHAR(20) DEFAULT 'PENDING'
);

-- ============================================================
-- 11. INTELLIGENCE SCORES (time-series)
-- ============================================================
CREATE TABLE IF NOT EXISTS intelligence_scores (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type     VARCHAR(20) NOT NULL CHECK (entity_type IN ('constituency','zone','booth')),
    entity_id       UUID NOT NULL,
    score_type      VARCHAR(50) NOT NULL,
    score_value     DECIMAL(7,4) NOT NULL,
    computed_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_intelligence_scores_entity ON intelligence_scores(entity_id, score_type, computed_at DESC);

-- ============================================================
-- 12. VOTERS
-- ============================================================
CREATE TABLE IF NOT EXISTS voters (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booth_id        UUID NOT NULL REFERENCES booths(id),
    voter_id        VARCHAR(50) UNIQUE,
    full_name       VARCHAR(255) NOT NULL,
    gender          CHAR(1) CHECK (gender IN ('M','F','O')),
    age             SMALLINT,
    phone_encrypted BYTEA,
    address_encrypted BYTEA,
    is_contacted    BOOLEAN DEFAULT FALSE NOT NULL,
    last_contacted  TIMESTAMPTZ,
    upload_batch_id UUID,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_voters_booth ON voters(booth_id);
CREATE INDEX IF NOT EXISTS idx_voters_voter_id ON voters(voter_id) WHERE voter_id IS NOT NULL;

-- ============================================================
-- 13. CONSTITUENCY DEMOGRAPHICS
-- ============================================================
CREATE TABLE IF NOT EXISTS constituency_demographics (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    constituency_id     UUID NOT NULL REFERENCES constituencies(id),
    ward_id             VARCHAR(20),
    ward_name           VARCHAR(255),
    total_population    INTEGER,
    voter_population    INTEGER,
    male_voters         INTEGER,
    female_voters       INTEGER,
    sc_population_pct   DECIMAL(5,2),
    st_population_pct   DECIMAL(5,2),
    obc_population_pct  DECIMAL(5,2),
    literacy_rate_pct   DECIMAL(5,2),
    youth_voter_pct     DECIMAL(5,2),
    data_source         VARCHAR(100),
    data_year           SMALLINT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_demographics_ward ON constituency_demographics(constituency_id, ward_id);

-- ============================================================
-- 14. BOOTH WARD MAPPING
-- ============================================================
CREATE TABLE IF NOT EXISTS booth_ward_mapping (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booth_id    UUID NOT NULL REFERENCES booths(id) UNIQUE,
    ward_id     VARCHAR(20) NOT NULL,
    ward_name   VARCHAR(255),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 15. AUDIT LOGS (immutable)
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id),
    action      VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id   UUID,
    old_value   JSONB,
    new_value   JSONB,
    ip_address  INET,
    user_agent  TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Revoke destructive operations from app user
REVOKE UPDATE, DELETE ON audit_logs FROM netaai_app;

-- ============================================================
-- UPDATE TRIGGERS (updated_at automation)
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY['users','booths','escalations'] LOOP
        EXECUTE format(
            'CREATE TRIGGER trg_%s_updated_at
             BEFORE UPDATE ON %I
             FOR EACH ROW EXECUTE FUNCTION update_updated_at()',
            t, t
        );
    END LOOP;
END;
$$;
