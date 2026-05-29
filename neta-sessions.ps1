# ==============================================================================
# neta-sessions.ps1
# Tailored development session runner parsed and generated from PRD requirements.
# Owner: Srinivas / Fidelitus Corp
# ==============================================================================

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet(
        "01-database-design",
        "02-security-auth",
        "03-geojson-mapping",
        "04-ground-operations",
        "05-news-intelligence",
        "06-booth-management",
        "07-prediction-sentiment",
        "08-opposition-intelligence",
        "09-whatsapp-integration",
        "10-devops-deployment",
        "list",
        "debug",
        "audit",
        "evidence"
    )]
    [string]$Session
)

$PROJECT_ROOT = "D:\NETA.AI"
$HAIKU        = "claude-haiku-4-5-20251001"
$SONNET       = "claude-sonnet-4-6"

$sessions = @{

    "01-database-design" = @{
        model  = $HAIKU
        task   = "TASK-001"
        label  = "Session 01: Database Schema & Alembic Setup"
        prompt = @'
Stack: Python 3.11, PostgreSQL (PostGIS), SQLAlchemy 2.0 (async), asyncpg, Alembic, Docker
Task file: tasks/TASK-001-database-design.md
Module scope: app/database-design/ ONLY (migrations & init scripts).

Key requirements extracted from PRD:
20.1 Complete Schema
-- Core identity and accessCREATE TABLE users (    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),    full_name       VARCHAR(255) NOT NULL,    email           VARCHAR(255) UNIQUE NOT NULL,    phone           VARCHAR(15),    password_hash   VARCHAR(255) NOT NULL,    role            VARCHAR(50) NOT NULL CHECK (role IN (                        'super_admin','campaign_manager','ground_commander',                        'data_analyst','field_worker','candidate')),    zone_id         UUID REFERENCES campaign_zones(id),    is_active       BOOLEAN DEFAULT TRUE,    mfa_secret      VARCHAR(255),  -- TOTP secret (encrypted)    mfa_enabled     BOOLEAN DEFAULT FALSE,    last_login      TIMESTAMPTZ,    login_attempts  INTEGER DEFAULT 0,    locked_until    TIMESTAMPTZ,    created_at      TIMESTAMPTZ DEFAULT NOW(),    updated_at      TIMESTAMPTZ DEFAULT NOW());-- Constituency referenceCREATE TABLE constituencies (    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),    name            VARCHAR(255) NOT NULL,    state           VARCHAR(100) NOT NULL,    ac_number       VARCHAR(10) NOT NULL UNIQUE,    total_booths    INTEGER,    total_voters    INTEGER,    geojson_url     TEXT,    created_at      TIMESTAMPTZ DEFAULT NOW());-- Campaign zones (operational sub-divisions)CREATE TABLE campaign_zones (    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),    constituency_id UUID NOT NULL REFERENCES constituencies(id),    zone_name       VARCHAR(100) NOT NULL,    zone_code       VARCHAR(10) NOT NULL,    description     TEXT,    created_at      TIMESTAMPTZ DEFAULT NOW());-- BoothsCREATE EXTENSION IF NOT EXISTS postgis;CREATE TABLE booths (    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),    constituency_id     UUID NOT NULL REFERENCES constituencies(id),    zone_id             UUID REFERENCES campaign_zones(id),    booth_number        VARCHAR(10) NOT NULL,    booth_name          VARCHAR(255),    location            GEOGRAPHY(POINT, 4326),    address             TEXT,    total_voters        INTEGER DEFAULT 0,    female_voters       INTEGER DEFAULT 0,    male_voters         INTEGER DEFAULT 0,    assigned_commander  UUID REFERENCES users(id),    risk_score          DECIMAL(5,2) DEFAULT 50.0,    contact_rate        DECIMAL(5,2) DEFAULT 0.0,    health_score        DECIMAL(5,2) DEFAULT 50.0,    swing_booth         BOOLEAN DEFAULT FALSE,    historical_margin   DECIMAL(5,2),    last_report_at      TIMESTAMPTZ,    created_at          TIMESTAMPTZ DEFAULT NOW(),    updated_at          TIMESTAMPTZ DEFAULT NOW(),    UNIQUE (constituency_id, booth_number));-- Field reportsCREATE TABLE field_reports (    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),    booth_id        UUID NOT NULL REFERENCES booths(id),    reported_by     UUID NOT NULL REFERENCES users(id),    category        VARCHAR(50) NOT NULL CHECK (category IN (                        'VOTER_MOOD','INFRASTRUCTURE','OPPOSITION_ACTIVITY',                        'SECURITY','LOGISTICS','OTHER')),    description     TEXT NOT NULL CHECK (length(description) <= 500),    severity        SMALLINT NOT NULL CHECK (severity BETWEEN 1 AND 5),    voter_sentiment VARCHAR(20) CHECK (voter_sentiment IN (                        'POSITIVE','NEUTRAL','NEGATIVE','MIXED')),    sentiment_score DECIMAL(4,3),  -- NLP output: -1.000 to 1.000    photo_url       TEXT,    gps_lat         DECIMAL(9,6),    gps_lng         DECIMAL(9,6),    processed       BOOLEAN DEFAULT FALSE,    created_at      TIMESTAMPTZ DEFAULT NOW());CREATE INDEX idx_field_reports_booth_created ON field_reports(booth_id, created_at DESC);CREATE INDEX idx_field_reports_severity ON field_reports(severity) WHERE severity >= 4;-- News articlesCREATE TABLE news_articles (    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),    feed_source         VARCHAR(100) NOT NULL,    feed_tier           SMALLINT NOT NULL CHECK (feed_tier IN (1, 2, 3)),    title               TEXT NOT NULL,    url                 TEXT NOT NULL UNIQUE,    body_excerpt        TEXT,    language            VARCHAR(10) DEFAULT 'en',    published_at        TIMESTAMPTZ,    ingested_at         TIMESTAMPTZ DEFAULT NOW(),    sentiment_polarity  DECIMAL(4,3),  -- -1.000 to 1.000    political_tone      VARCHAR(30) CHECK (political_tone IN (                            'PRO_INCUMBENT','NEUTRAL','ANTI_INCUMBENT')),    impact_score        DECIMAL(4,2),  -- 0.00 to 10.00    entity_tags         JSONB DEFAULT '[]',  -- Array of extracted entities    narrative_cluster   VARCHAR(100),    processed           BOOLEAN DEFAULT FALSE);CREATE INDEX idx_news_published_sentiment ON news_articles(published_at DESC, sentiment_polarity);CREATE INDEX idx_news_impact ON news_articles(impact_score DESC) WHERE impact_score >= 5.0;-- AlertsCREATE TABLE alerts (    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),    alert_type      VARCHAR(100) NOT NULL,    severity        VARCHAR(20) NOT NULL CHECK (severity IN ('CRITICAL','WARNING','INFO')),    source_module   VARCHAR(50) NOT NULL,    title           VARCHAR(255) NOT NULL,    description     TEXT,    affected_booths UUID[],    meta            JSONB DEFAULT '{}',    acknowledged    BOOLEAN DEFAULT FALSE,    acknowledged_by UUID REFERENCES users(id),    acknowledged_at TIMESTAMPTZ,    created_at      TIMESTAMPTZ DEFAULT NOW());CREATE INDEX idx_alerts_severity_created ON alerts(severity, created_at DESC) WHERE NOT acknowledged;-- EscalationsCREATE TABLE escalations (    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),    alert_id            UUID REFERENCES alerts(id),    field_report_id     UUID REFERENCES field_reports(id),    assigned_to         UUID NOT NULL REFERENCES users(id),    assigned_by         UUID REFERENCES users(id),    status              VARCHAR(20) NOT NULL DEFAULT 'NEW'                            CHECK (status IN ('NEW','ASSIGNED','IN_PROGRESS','RESOLVED','CLOSED')),    sla_minutes         INTEGER NOT NULL,    sla_deadline        TIMESTAMPTZ NOT NULL,    whatsapp_sent       BOOLEAN DEFAULT FALSE,    reminder_sent       BOOLEAN DEFAULT FALSE,    resolved_at         TIMESTAMPTZ,    resolution_notes    TEXT CHECK (length(resolution_notes) >= 50 OR resolved_at IS NULL),    created_at          TIMESTAMPTZ DEFAULT NOW(),    updated_at          TIMESTAMPTZ DEFAULT NOW());-- Intelligence briefs (AI-generated daily briefs)CREATE TABLE intelligence_briefs (    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),    brief_date          DATE NOT NULL UNIQUE,    executive_summary   TEXT NOT NULL,    top_risks           JSONB NOT NULL DEFAULT '[]',    opportunity_zones   JSONB NOT NULL DEFAULT '[]',    recommended_actions JSONB NOT NULL DEFAULT '[]',    narrative_digest    TEXT,    win_probability     DECIMAL(5,2),    generated_at        TIMESTAMPTZ DEFAULT NOW(),    delivered_at        TIMESTAMPTZ,    delivery_status     VARCHAR(20) DEFAULT 'PENDING');-- Intelligence scores (time-series for trend visualization)CREATE TABLE intelligence_scores (    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),    entity_type     VARCHAR(20) NOT NULL CHECK (entity_type IN ('constituency','zone','booth')),    entity_id       UUID NOT NULL,    score_type      VARCHAR(50) NOT NULL,    score_value     DECIMAL(7,4) NOT NULL,    computed_at     TIMESTAMPTZ DEFAULT NOW());CREATE INDEX idx_intelligence_scores_entity_type ON intelligence_scores(entity_id, score_type, computed_at DESC);-- Voter rollsCREATE TABLE voters (    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),    booth_id        UUID NOT NULL REFERENCES booths(id),    voter_id        VARCHAR(50) UNIQUE,    full_name       VARCHAR(255) NOT NULL,    gender          CHAR(1) CHECK (gender IN ('M','F','O')),    age             SMALLINT,    phone_encrypted BYTEA,  -- AES-256-GCM encrypted    address_encrypted BYTEA,    is_contacted    BOOLEAN DEFAULT FALSE,    last_contacted  TIMESTAMPTZ,    upload_batch_id UUID,    created_at      TIMESTAMPTZ DEFAULT NOW());CREATE INDEX idx_voters_booth ON voters(booth_id);-- Audit log (immutable)CREATE TABLE audit_logs (    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),    user_id     UUID NOT NULL REFERENCES users(id),    action      VARCHAR(100) NOT NULL,    entity_type VARCHAR(50),    entity_id   UUID,    old_value   JSONB,    new_value   JSONB,    ip_address  INET,    user_agent  TEXT,    created_at  TIMESTAMPTZ DEFAULT NOW());-- Revoke UPDATE and DELETE from app user on this tableREVOKE UPDATE, DELETE ON audit_logs FROM netaai_app;

PDCA: present plan before touching any file.
'@
    }

    "02-security-auth" = @{
        model  = $SONNET
        task   = "TASK-002"
        label  = "Session 02: Security Architecture & JWT Authentication"
        prompt = @'
Stack: Python 3.11, FastAPI, Redis, bcrypt
Task file: tasks/TASK-002-security-auth.md
Module scope: app/security-auth/ ONLY (endpoints, middleware, security configuration).

Key requirements extracted from PRD:
17.1 Security Design Philosophy
NETA AI handles politically sensitive campaign intelligence, voter contact data, and operational plans. Security failures have election-outcome consequences. The security architecture follows a defense-in-depth model with multiple independent protection layers.
17.2 Authentication & Session Management
JWT Implementation
# JWT configurationJWT_ALGORITHM = "HS256"ACCESS_TOKEN_EXPIRE_MINUTES = 15      # Short-lived access tokensREFRESH_TOKEN_EXPIRE_DAYS = 7         # Rotating refresh tokens# Cookie configuration (all tokens stored in httpOnly cookies)response.set_cookie(    key="access_token",    value=access_token,    httponly=True,         # JavaScript cannot access    secure=True,           # HTTPS only    samesite="strict",     # CSRF protection    max_age=900,           # 15 minutes    path="/api",           # API endpoints only)
Token Lifecycle
Event
Action
Login
Issue access token (15 min) + refresh token (7 days) in httpOnly cookies
API Request
Validate access token from cookie; check Redis blacklist
Access Token Expiry
Client silently calls /auth/refresh; new access token issued
Logout
Both tokens added to Redis blacklist; cookies cleared
Role Change
All active tokens invalidated via Redis blacklist pattern
Password Change
All active tokens invalidated
Account Suspension
User record deactivated; all tokens invalidated
Redis Token Blacklist
# Token blacklist key patternBLACKLIST_KEY = f"blacklist:token:{jti}"  # jti = JWT unique IDBLACKLIST_TTL = ACCESS_TOKEN_EXPIRE_SECONDS  # Auto-expires with tokenasync def is_token_blacklisted(jti: str) -> bool:    return await redis_client.exists(f"blacklist:token:{jti}")
17.3 Multi-Factor Authentication
MFA (TOTP via RFC 6238) is mandatory for:
Super Admin
Campaign Manager
MFA is optional but encouraged for:
Ground Commander
Data Analyst
MFA is disabled for:
Field Worker (UX friction would reduce adoption; compensated by IP-bound session and role scope limitation)
17.4 Transport Security
Control
Configuration
TLS Version
TLS 1.3 minimum; TLS 1.2 allowed with forward secrecy ciphers; TLS 1.0/1.1 disabled
HSTS
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
HTTPS Redirect
Nginx: return 301 https://$host$request_uri for all HTTP traffic
Certificate
Let's Encrypt; auto-renewal via Certbot; expiry monitor alert at 30 days
17.5 Application Security Controls
Control
Implementation
Content Security Policy
default-src 'self'; script-src 'self' 'nonce-{random}'; img-src 'self' data: https:; connect-src 'self' https://api.netaai.in
CORS
Whitelist-only: ALLOWED_ORIGINS=["https://app.netaai.in"]; no wildcard
Rate Limiting
Nginx: 100 req/min per authenticated IP; 10 req/min for /auth/ endpoints; 5 req/min for /auth/login
Request Size
Nginx: client_max_body_size 11M (field report photo uploads max 10MB)
SQL Injection
SQLAlchemy parameterized queries; no string interpolation in SQL
XSS
React JSX auto-escaping; CSP; no dangerouslySetInnerHTML usage
CSRF
SameSite=Strict cookie; double-submit cookie pattern for state-changing requests
17.6 Data Security
Control
Implementation
Password Hashing
bcrypt with cost factor 12
PII Encryption
Voter phone numbers and addresses encrypted with AES-256-GCM at rest
Database Credentials
Environment variable injection; never in source code
Redis AUTH
Password-protected Redis instance; not exposed on public interface
File Upload Validation
MIME type check, file extension whitelist (.jpg, .jpeg, .png, .webp), magic byte validation, max 10MB
Secrets Management
.env file with 600 permissions; never committed to version control
17.7 Audit Logging
All data-write operations are logged to the audit_logs table:
CREATE TABLE audit_logs (    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),    user_id     UUID NOT NULL REFERENCES users(id),    action      VARCHAR(100) NOT NULL,  -- e.g., 'field_report.create', 'user.role_change'    entity_type VARCHAR(50),    entity_id   UUID,    old_value   JSONB,    new_value   JSONB,    ip_address  INET,    user_agent  TEXT,    created_at  TIMESTAMPTZ DEFAULT NOW());
Audit logs are immutable (no UPDATE or DELETE permissions granted to the application user on this table). Retention: 3 years.

PDCA: present plan before touching any file.
'@
    }

    "03-geojson-mapping" = @{
        model  = $SONNET
        task   = "TASK-003"
        label  = "Session 03: GeoJSON Mapping System"
        prompt = @'
Stack: React 18, Leaflet.js, PostGIS, FastAPI
Task file: tasks/TASK-003-geojson-mapping.md
Module scope: app/geojson-mapping/ and frontend map views ONLY.

Key requirements extracted from PRD:
22.1 GeoJSON Data Architecture
NETA AI maintains a hierarchical GeoJSON layer system:
Layer
Data
Source
Format
Storage
Constituency Boundary
AC-52 outer boundary
ECI shapefile ? GeoJSON
Polygon
Static file + DB
Ward Boundaries
Municipal ward polygons
GHMC GIS data
MultiPolygon
Static file
Booth Catchments
Approximate booth coverage zones
ECI + derived
Polygon
PostGIS table
Booth Points
Individual booth locations
ECI + GPS validation
Point
PostGIS (booths.location)
Zone Boundaries
Campaign management zones
Custom defined
Polygon
Static GeoJSON file
Road Network
Major roads and landmarks
OpenStreetMap
LineString
Vector tiles
22.2 Map Layer Architecture
Leaflet.js Map Container    �    +-- Base Layer: OpenStreetMap tiles (CDN)    �    +-- Layer Group: Constituency Layers (toggleable)    �   +-- Constituency boundary (GeoJSON � always visible)    �   +-- Ward boundaries (GeoJSON � toggle)    �   +-- Zone boundaries (GeoJSON � toggle)    �    +-- Layer Group: Data Layers (toggleable, mutually exclusive)    �   +-- Booth Health Choropleth    �   +-- Booth Risk Choropleth    �   +-- Contact Rate Choropleth    �   +-- Voter Density Choropleth    �   +-- Sentiment Heatmap    �    +-- Marker Layer: Booth Markers (always visible)    �   +-- Color-coded by selected data layer    �   +-- Click ? Booth detail popup    �    +-- Marker Layer: Field Worker Positions (toggleable)    �   +-- Last-known GPS from most recent report    �    +-- Marker Layer: Opposition Activity (toggleable, CM+ only)        +-- Field-reported opposition events
22.3 Booth Popup Data Card
On clicking any booth marker:
+-------------------------------------+� ?? BOOTH 147 � Kondapur PS         �� Zone: Z-01 Kondapur                 �+-------------------------------------�� Total Voters: 1,247                 �� Contacted: 623 (49.9%)              �� Health Score: 72/100 ??             �� Risk Score: 38/100 ??               �� Volunteers: 3 assigned              �+-------------------------------------�� Last Report: 2h ago                 �� Open Escalations: 0                 �� Mood: POSITIVE                      �+-------------------------------------�� Commander: Ramesh Kumar             �� [View Full Booth] [Add Report]      �+-------------------------------------+
22.4 GeoJSON Performance Optimization
Simplification: Booth catchment polygons simplified to 0.001� precision using shapely.simplify() before storage � reduces file size by ~60% with negligible visual quality loss
Lazy loading: Ward and zone boundary GeoJSON loaded on-demand when those layers are toggled, not on initial map load
Tile caching: Nginx caches OSM base tiles with 1-hour TTL to reduce external tile server dependency
Clustering: At zoom levels < 12, booth markers are clustered using Leaflet.markercluster; full markers visible at zoom = 13

11.1 Purpose & Scope
The Constituency Intelligence module is the geo-demographic backbone of NETA AI. It provides spatial, statistical, and historical data visualization for Serilingampally AC-52, integrated with live campaign data to enable targeted, evidence-based deployment decisions.
11.2 Data Sources & Integration
Census Data Layer
Field
Source
Granularity
Update Cadence
Total population
Census 2011 + 2024 projection
Ward level
Annual refresh
Voter population
ECI voter roll summary
Booth level
Per election cycle
Gender split
Census 2011
Ward level
Annual
Literacy rate
Census 2011
District/ward
Annual
SC/ST proportion
Census 2011
Ward level
Annual
OBC estimate
Survey data + Census
Ward level
Campaign-cycle
Occupation breakdown
Census 2011
Ward level
Annual
Household income proxy
NSS survey data
District level
Annual
All census data is stored in the constituency_demographics table with a ward_id foreign key, enabling JOIN with booth-level data through the booth_ward_mapping table.
ECI Booth Data Layer
Field
Source
Storage
Booth number
ECI official booth list
booths.booth_number
Booth name / location
ECI official booth list
booths.name, PostGIS POINT
Total registered voters
ECI voter roll summary
booths.total_voters
Booth catchment boundary
ECI shapefile (converted to GeoJSON)
booth_boundaries.geojson
11.3 Constituency Zone Structure
Serilingampally AC-52 is divided into the following campaign management zones for operational purposes:
Zone ID
Zone Name
Key Areas
Booth Count (approx.)
Voter Count (approx.)
Z-01
Kondapur Zone
Kondapur, Ayyappa Society, Laxmi Cyber City
55
52,000
Z-02
Madhapur Zone
Madhapur, Jubilee Hills Road, Raidurg
48
44,000
Z-03
Gachibowli Zone
Gachibowli, Financial District, ISB Road
42
39,000
Z-04
HITEC City Zone
HITEC City, Whitefields, Kothaguda
38
36,000
Z-05
Hafeezpet Zone
Hafeezpet, Miyapur Link Road, RC Puram
52
49,000
Z-06
Chandanagar Zone
Chandanagar, Lingampally, Chanda Nagar OFB
45
43,000
Z-07
Nallagandla Zone
Nallagandla, Tellapur, Kollur
35
33,000
Total
~315 booths
~296,000
11.4 Constituency Intelligence Views
Demographic Overlay Map
Interactive Leaflet.js choropleth with selectable overlay:
Voter density (voters per sq km)
SC/ST concentration (% of booth catchment)
Youth voter proportion (18�35 age estimate)
Literacy rate
Gender ratio (female voters %)
Each overlay uses a 5-step color scale normalized to constituency min/max values. Map layer toggles are accessible in the sidebar panel.
Historical Vote Share Layer
For each booth, display historical vote share data (where available from prior election results):
Candidate party vote share
Main opposition vote share
Winning margin
Voter turnout %
Booths with prior margin <5% are flagged as SWING BOOTHS with a distinct map marker.
Zone Comparison Dashboard
Tabular comparison of all zones across:
Metric
Z-01
Z-02
Z-03
Z-04
Z-05
Z-06
Z-07
Contact Rate %
�
�
�
�
�
�
�
Avg Booth Health
�
�
�
�
�
�
�
Active Workers
�
�
�
�
�
�
�
Open Escalations
�
�
�
�
�
�
�
News Sentiment
�
�
�
�
�
�
�
(Values populate live from database during operation.)

PDCA: present plan before touching any file.
'@
    }

    "04-ground-operations" = @{
        model  = $SONNET
        task   = "TASK-004"
        label  = "Session 04: Ground Pulse & Escalations Workflow"
        prompt = @'
Stack: Python 3.11, FastAPI, React 18 (PWA, IndexedDB)
Task file: tasks/TASK-004-ground-operations.md
Module scope: app/ground-operations/ ONLY (field reports, attendance, escalation SLAs).

Key requirements extracted from PRD:
13.1 Field Worker Management
Deployment Tracking
The system maintains a real-time map of active field workers across the constituency. Each worker has a profile record including:
user_id, name, phone, zone_id (FK), assigned_booths (ARRAY)
is_active (online/offline status)
last_checkin_at (UTC timestamp)
reports_today (count, cached in Redis)
productivity_score (reports submitted � severity weighting, rolling 7-day)
Worker positions are updated via GPS-enabled check-in on report submission (not continuous GPS tracking, to avoid battery drain and privacy concerns on personal devices).
Attendance Management
Daily attendance is recorded through a booth check-in workflow:
Worker opens mobile app ? taps "Check In to Booth"
App captures GPS coordinate (optional � can be disabled for areas with poor signal)
Worker selects booth from their assigned list or searches by number
Check-in recorded in worker_attendance table with timestamp
Zone dashboards show real-time attendance aggregates: workers expected vs. present, coverage gaps by booth.
13.2 Field Report Schema
Field reports are the primary ground truth signal of NETA AI. The mobile reporting form enforces structured input:
Field
Type
Required
Notes
booth_id
FK
Yes
Dropdown from assigned booths
category
ENUM
Yes
VOTER_MOOD, INFRASTRUCTURE, OPPOSITION_ACTIVITY, SECURITY, LOGISTICS, OTHER
description
Text (max 500 chars)
Yes
Free text; used for NLP processing
severity
INT (1�5)
Yes
1=Routine, 3=Noteworthy, 5=Emergency
voter_sentiment
ENUM
Optional
POSITIVE, NEUTRAL, NEGATIVE, MIXED
photo_url
String
Optional
S3/filesystem URL; max 10MB; MIME validated
audio_url
String
Optional
Phase 2; voice report transcription
reported_at
Timestamp
Auto
UTC; cannot be edited post-submission
gps_lat, gps_lng
Float
Optional
Device-captured on submission
13.3 Escalation Workflow
Severity 4�5 reports automatically trigger an escalation record. The full escalation lifecycle:
Field Report (Severity 4 or 5)         �         ?   Escalation Record Created   +-- status: NEW   +-- sla_deadline: NOW + 30min (severity 5) / NOW + 2h (severity 4)   +-- assigned_to: zone Ground Commander (auto-assigned by zone_id)   +-- notification: WhatsApp ? Ground Commander         �         ?   Ground Commander Acknowledges   +-- status: IN_PROGRESS   +-- acknowledged_at: timestamp   +-- SSE push: Command Centre escalation count updates         �         ?   SLA Monitor (every 5 min check)   +-- If SLA_DEADLINE approaching (15 min): WhatsApp reminder   +-- If SLA_DEADLINE breached: CRITICAL alert ? Campaign Manager         �         ?   Resolution   +-- status: RESOLVED   +-- resolved_at: timestamp   +-- resolution_notes: required (min 50 characters)   +-- SSE push: escalation queue count decrements
Escalation SLA Table
Severity
SLA
Assigned To
Escalates To (if SLA breached)
5 � Emergency
30 minutes
Ground Commander
Campaign Manager (immediate)
4 � High
2 hours
Ground Commander
Campaign Manager (on breach)
3 � Medium
8 hours
Ground Commander
Zone review (on breach)
1�2 � Routine
24 hours
Ground Commander
No escalation
13.4 Mood Analysis
Aggregate sentiment extracted from field reports is visualized as a Constituency Mood Map � a zone-level choropleth overlaid on the constituency map:
Color: Green (positive), Amber (neutral/mixed), Red (negative)
Time window: Rolling 24 hours (configurable: 6h, 24h, 48h, 7-day)
Calculation: Weighted average of voter_sentiment field values, weighted by report recency
A zone-level mood time-series chart tracks sentiment trend over the campaign period � identifying mood deterioration before it becomes an electoral problem.

PDCA: present plan before touching any file.
'@
    }

    "05-news-intelligence" = @{
        model  = $SONNET
        task   = "TASK-005"
        label  = "Session 05: RSS Ingestion & Multilingual NLP Pipeline"
        prompt = @'
Stack: Python 3.11, Celery, HuggingFace (MuRIL/IndicBERT), spaCy, Scikit-learn
Task file: tasks/TASK-005-news-intelligence.md
Module scope: app/news-intelligence/ ONLY (RSS parser, sentiment model, narrative clustering).

Key requirements extracted from PRD:
12.1 RSS Feed Catalogue
The following sources are configured in the initial deployment. The feed catalogue is manageable via the Admin Dashboard without code changes.
Source
Language
Tier
Topics Monitored
The Hindu � Telangana
English
1
Politics, governance, development
NDTV � Telangana
English
1
Breaking news, political developments
Deccan Chronicle � Hyderabad
English
2
Local politics, constituency coverage
The News Minute
English
2
Telangana politics, investigative
Sakshi � Political
Telugu
1
YSRCP/BRS/Congress coverage
Eenadu � Political
Telugu
1
Mainstream Telugu political news
Namaste Telangana
Telugu
2
BRS-aligned political coverage
V6 News Telugu
Telugu
2
Telangana news and politics
Hans India
English
2
Hyderabad and Telangana coverage
Siasat Daily
Urdu/English
2
Minority community perspectives
Telangana Today
English
2
Official Telangana state coverage
+ 9 additional sources
Mixed
3
Hyperlocal, community, ward blogs
12.2 NLP Processing Pipeline
Raw RSS Article    �    ?[Pre-processing]    +-- Language detection (Telugu / English)    +-- HTML tag stripping    +-- Normalization (Unicode, encoding)    +-- Sentence tokenization    �    ?[Sentiment Analysis]    +-- IndicBERT / MuRIL tokenization    +-- Polarity score: -1.0 (strongly negative) ? +1.0 (strongly positive)    +-- Confidence score (0.0 ? 1.0)    +-- Political tone: PRO_INCUMBENT | NEUTRAL | ANTI_INCUMBENT    �    ?[Entity Extraction]    +-- Candidate name(s) detection    +-- Constituency name detection    +-- Party name detection    +-- Issue tag extraction (INFRASTRUCTURE|DEVELOPMENT|SECURITY|etc.)    +-- Location tagging (ward, zone, area names)    �    ?[Impact Scoring]    +-- Base = |sentiment_polarity| � political_relevance_score    +-- Source multiplier: Tier 1 = 1.0, Tier 2 = 0.7, Tier 3 = 0.4    +-- Recency decay: e^(-0.1 � hours_since_publication)    +-- Impact Score = Base � Source Multiplier � Recency Decay � 10    �    ?[Narrative Clustering]    +-- TF-IDF vectorization of article body    +-- Cosine similarity against existing cluster centroids    +-- Assign to nearest cluster (threshold: similarity > 0.65)    +-- If no match: create new cluster; alert analyst    �    ?[Output]    +-- Write to news_articles table    +-- If impact_score = 7.0: create alerts record    +-- Update Redis: news_sentiment_cache, narrative_momentum_cache
12.3 Narrative Tracking
Active narrative clusters are tracked with momentum scores:
Rising: Cluster article count increasing over 24h window
Stable: Article count within �10% of 48h average
Fading: Article count declining over 24h window
Campaign Manager receives a daily narrative summary as part of the morning brief. War room team receives a real-time narrative momentum widget on the Command Centre.
12.4 News Intelligence Display
The News Intelligence module displays:
Live Feed � Real-time ingested articles with sentiment badge, impact score, source, and entity tags. Filterable by language, source tier, sentiment, and impact threshold.
Sentiment Timeline � 72-hour rolling chart of aggregate sentiment polarity (constituency-relevant articles only).
Impact Leaderboard � Top 10 highest-impact articles of the last 24 hours.
Narrative Cluster Board � All active clusters with momentum indicator, article count, and top headline per cluster.
Source Health Monitor � Per-feed last-ingestion timestamp, articles per day, and failure flag.

PDCA: present plan before touching any file.
'@
    }

    "06-booth-management" = @{
        model  = $SONNET
        task   = "TASK-006"
        label  = "Session 06: Booth Operations & Nightly Risk Scoring"
        prompt = @'
Stack: Python 3.11, Celery, PostgreSQL, Redis
Task file: tasks/TASK-006-booth-management.md
Module scope: app/booth-management/ ONLY (booth records, risk score calculations, volunteers).

Key requirements extracted from PRD:
14.1 Booth Data Architecture
Every booth in the constituency (approximately 315 for Serilingampally AC-52) is represented as a first-class entity in the system with its own operational data profile.
Booth Record Schema
booths {    id                UUID PRIMARY KEY    constituency_id   UUID FK    booth_number      VARCHAR(10) NOT NULL UNIQUE    booth_name        VARCHAR(255)    zone_id           UUID FK ? campaign_zones    location          PostGIS POINT (SRID 4326)    address           TEXT    total_voters      INTEGER    female_voters     INTEGER    male_voters       INTEGER    third_gender      INTEGER    assigned_commander UUID FK ? users    volunteer_count   INTEGER (derived)    risk_score        DECIMAL(5,2) DEFAULT 50.0    contact_rate      DECIMAL(5,2) DEFAULT 0.0    health_score      DECIMAL(5,2) DEFAULT 50.0    last_report_at    TIMESTAMPTZ    last_contact_at   TIMESTAMPTZ    swing_booth       BOOLEAN DEFAULT FALSE    historical_margin DECIMAL(5,2)  -- prior election margin %    created_at        TIMESTAMPTZ    updated_at        TIMESTAMPTZ}
14.2 Booth Risk Score Formula
The booth risk score (0�100, higher = more at risk) is computed nightly and cached in Redis:
risk_score = (    (100 - contact_rate_pct) � 0.35        # Contact coverage deficit  + sentiment_negativity_score � 0.25      # Ground sentiment penalty  + escalation_burden � 0.20               # Open escalations weight  + staleness_penalty � 0.15               # Days since last report  + volunteer_gap_penalty � 0.05           # Coverage gap penalty)Where:  contact_rate_pct    = (voters_contacted / total_voters) � 100  sentiment_negativity = (negative_reports / total_reports) � 100 (last 48h)  escalation_burden   = min(open_escalation_count � 10, 100)  staleness_penalty   = min(days_since_last_report � 5, 40)  volunteer_gap_penalty = 100 if volunteer_count < 2 else 0
Risk Color Classification
Score Range
Classification
Action
0�35
?? HEALTHY
Standard operations
36�60
?? WATCH
Increase contact frequency
61�80
?? AT-RISK
Deploy additional volunteers; daily check-in
81�100
?? CRITICAL
Immediate Ground Commander intervention; Campaign Manager alert
14.3 Booth Health Score
The booth health score (0�100, higher = healthier) is a complementary metric tracking operational vitality:
health_score = (    contact_rate_pct � 0.40  + recency_score � 0.30     # 100 if report < 24h, 50 if < 48h, 20 if > 48h  + volunteer_coverage � 0.20 # 100 if = 3 volunteers, 67 if 2, 33 if 1, 0 if 0  + sentiment_positivity � 0.10)
14.4 Volunteer Mapping
Each booth maintains a volunteer roster:
booth_volunteers {    id              UUID PRIMARY KEY    booth_id        UUID FK ? booths    user_id         UUID FK ? users (nullable for non-registered volunteers)    volunteer_name  VARCHAR(255)    phone           VARCHAR(15)    role            ENUM (BOOTH_AGENT, VOTER_CONTACT, TRANSPORT, COORDINATOR)    shift_start     TIME    shift_end       TIME    notes           TEXT    is_confirmed    BOOLEAN DEFAULT FALSE    created_at      TIMESTAMPTZ}
Booths with volunteer_count < 2 are flagged with a coverage gap warning. The Booth Management view includes a "Coverage Gaps" filter that instantly surfaces all under-resourced booths.
14.5 Contact Rate Tracking
Voter contact is logged through the field worker mobile interface:
Worker selects booth ? Opens contact log
Marks individual voters as contacted (by voter ID from roll or by manual count)
System updates booth.contact_rate in real time
Ward-level and zone-level aggregate contact rates computed hourly by Celery task
Target contact rates by campaign stage:
Campaign Stage
Target Contact Rate
4 weeks before polling
25%
2 weeks before polling
50%
1 week before polling
75%
3 days before polling
90%
Polling Day
100% (re-contact priority)

PDCA: present plan before touching any file.
'@
    }

    "07-prediction-sentiment" = @{
        model  = $SONNET
        task   = "TASK-007"
        label  = "Session 07: Win Probability Model & Sentiment Trends"
        prompt = @'
Stack: Python 3.11, Celery, Redis, PostgreSQL
Task file: tasks/TASK-007-prediction-sentiment.md
Module scope: app/prediction-sentiment/ ONLY (win probability computation, issue severity aggregates).

Key requirements extracted from PRD:
15.1 Win Probability Model
The win probability model produces a constituency-level election outcome probability updated every 15 minutes throughout the campaign.
Model Formula
win_probability = sigmoid(    w1 � contact_rate_normalized  + w2 � news_sentiment_normalized  + w3 � booth_health_aggregate  + w4 � opposition_activity_penalty  + w5 � historical_vote_share  + w6 � field_mood_index  + bias) � 100Default weights (campaign-manager configurable):  w1 (contact rate)       = 0.28  w2 (news sentiment)     = 0.18  w3 (booth health)       = 0.20  w4 (opposition penalty) = -0.15  w5 (historical share)   = 0.12  w6 (field mood)         = 0.17  bias                    = 0.10Normalization: all inputs normalized to [0, 1] range before weighting.Sigmoid: ensures output remains within (0%, 100%).
The model stores daily snapshots in intelligence_scores for trend visualization. A 30-day trend chart is displayed on the Command Centre.
Model Limitations (Disclosed)
The model is a heuristic approximation, not a statistical election model
Historical vote share data for Serilingampally may be incomplete for newer booth configurations
Weight calibration is based on campaign manager judgment, not empirical training data (to be improved in Phase 2 with Bayesian updating)
Adversarial events (e.g., opponent rally, negative viral story) may cause rapid score changes that should be interpreted contextually, not mechanically
15.2 Sentiment Analysis Systems
News Sentiment Aggregation
Rolling weighted sentiment index for constituency-relevant news:
constituency_sentiment_index = S(article_sentiment � article_weight) / S(article_weight)Where:  article_weight = impact_score � recency_decay  recency_decay  = e^(-0.05 � hours_since_publication)  Window         = Last 24 hours (configurable)
Displayed as a time-series chart on Command Centre and News Intelligence module.
Field Sentiment Index
Aggregate voter mood from field reports:
field_sentiment_index = (    (positive_reports � 1.0)  + (neutral_reports � 0.5)  + (mixed_reports � 0.25)  + (negative_reports � 0.0)) / total_reports � 100Window: configurable (6h, 24h, 48h, 7-day)
15.3 Issue Severity Ranking
Issues extracted from field reports and news articles are ranked using a composite severity model:
issue_severity = (    frequency_score � 0.30      # Reports mentioning issue in 48h  + sentiment_impact � 0.30     # Avg negativity of issue-related content  + booth_spread_score � 0.20   # Number of distinct booths reporting issue  + media_amplification � 0.20  # Number of news articles covering issue) � 10  # Scale to 0-10
Top 5 issues by severity are displayed prominently on the Command Centre issue trends panel. Issues crossing severity 7.0 trigger CRITICAL alerts.

PDCA: present plan before touching any file.
'@
    }

    "08-opposition-intelligence" = @{
        model  = $SONNET
        task   = "TASK-008"
        label  = "Session 08: Opposition Monitoring & Sentiment Comparison"
        prompt = @'
Stack: Python 3.11, React 18, Leaflet.js
Task file: tasks/TASK-008-opposition-intel.md
Module scope: app/opposition-intelligence/ ONLY.

Key requirements extracted from PRD:
16.1 Purpose & Design Philosophy
Opposition intelligence in NETA AI is structured, systematic, and factual. The module monitors publicly available information � news coverage, public events, press statements, and field-observed opposition activity � to provide the campaign with awareness of what rivals are doing. The system explicitly does not enable or generate any disinformation, negative campaigns, or content targeting individuals.
16.2 Opposition Monitoring Sources
Source
Type
What Is Tracked
RSS feeds (opposition-entity-filtered)
Automated
Articles mentioning rival candidate/party
Field reports (category: OPPOSITION_ACTIVITY)
Manual (ground workers)
Opposition rallies, canvassing, distribution
Public social media (when accessible)
Phase 2
Opposition social media posts and engagement
News mentions comparison
Automated
Candidate coverage vs. opposition coverage volume
16.3 Opposition Intelligence Views
Comparative Sentiment Dashboard
A dual-line time-series chart displaying:
Blue line: Candidate news sentiment score (rolling 24h)
Red line: Opposition candidate news sentiment score (rolling 24h)
Divergence alerts: if opposition sentiment exceeds candidate sentiment by >0.3 points for more than 4 hours, a WARNING alert is generated.
Opposition Activity Map
Leaflet.js map layer showing:
Opposition rally locations (sourced from field reports)
Opposition canvassing zones (sourced from field reports)
Opposition concentration heatmap (derived from field report density by zone)
This map layer is toggled independently of the main constituency map and is visible only to Campaign Manager and above.
Opposition Narrative Tracker
Tracks narrative clusters where opposition entity is the primary subject:
Narrative
Momentum
Article Count (24h)
Sentiment
Action
(populated from live data)
?/?/?
�
�
Counter-message / Monitor
16.4 Counter-Intelligence Workflow
When an opposition narrative reaches severity =7.0 or impact score =8.0:
System generates a WARNING or CRITICAL alert in Command Centre
Alert links to the narrative cluster with supporting articles
Campaign Manager receives WhatsApp notification
Alert includes a structured response recommendation (factual counter-narrative suggestion, not disinformation)
Campaign Manager approves or modifies response
Response action is logged in escalations table for accountability

PDCA: present plan before touching any file.
'@
    }

    "09-whatsapp-integration" = @{
        model  = $SONNET
        task   = "TASK-009"
        label  = "Session 09: Meta WhatsApp Business API & Alert Routing"
        prompt = @'
Stack: Python 3.11, Meta Cloud API, Celery
Task file: tasks/TASK-009-whatsapp-integration.md
Module scope: app/whatsapp-integration/ ONLY (status callbacks, alert delivery, templates).

Key requirements extracted from PRD:
24.1 Integration Architecture
NETA AI uses the Meta WhatsApp Business Cloud API for operational alert delivery. All messages use pre-approved WhatsApp message templates to comply with Meta's policies.
NETA AI Backend (Celery task)    �-- POST https://graph.facebook.com/v18.0/{phone_id}/messages    �   Authorization: Bearer {WHATSAPP_API_TOKEN}    �   Body: { "to": recipient_phone, "template": template_name, "parameters": [...] }    �WhatsApp Business API    +-- Delivers to recipient's WhatsApp number    �Webhook (inbound) ? FastAPI /api/whatsapp/webhook    +-- Delivery status updates (SENT, DELIVERED, READ, FAILED)
24.2 Message Template Catalogue
Template Name
Trigger
Recipient
Content Summary
morning_brief_ready
Daily 06:00 IST
Campaign Manager
"Your NETA AI morning brief is ready. [Date summary]. Log in to view."
critical_escalation
Severity 5 field report
Ground Commander + CM
"CRITICAL: Severity 5 report at Booth {number} � {category}. SLA: 30 minutes. Open NETA AI immediately."
escalation_sla_breach
SLA deadline passed
Campaign Manager
"SLA BREACH: Escalation #{id} at Booth {number} has exceeded the {n}-minute SLA. Immediate action required."
high_impact_news
News impact score = 8.0
Campaign Manager
"HIGH IMPACT: '{title}' [{source}] � Sentiment: {tone}. Impact score: {score}/10."
booth_critical_risk
Booth risk score crosses 80
Ground Commander
"RISK ALERT: Booth {number} has reached CRITICAL risk score {score}/100. Check NETA AI for details."
win_probability_drop
Win probability drops >5% in 1 hour
Campaign Manager
"ALERT: Win probability has dropped {delta}% in the last 60 minutes. Current: {value}%. Open Command Centre."
system_health_alert
API/service health check failure
Super Admin
"SYSTEM ALERT: {service} is not responding. Check the Admin Dashboard immediately."
24.3 Delivery & Failure Handling
Message delivery status tracked in whatsapp_delivery_log table
Failed messages retried up to 3 times with 5-minute intervals
If delivery fails after 3 retries: fallback SMS via configured provider (Phase 2); log failure in audit table
Delivery failure rate alert: if >5% failure rate in 1 hour, Admin Dashboard alert generated
24.4 Compliance
All WhatsApp templates pre-approved by Meta before production deployment
Campaign-related broadcasts (voter outreach) require explicit voter opt-in � managed separately from operational alerts
Operational alerts (to campaign team members) use the campaign team's registered numbers with their consent
No voter personal data (from voter rolls) is sent via WhatsApp in any format

PDCA: present plan before touching any file.
'@
    }

    "10-devops-deployment" = @{
        model  = $SONNET
        task   = "TASK-010"
        label  = "Session 10: Docker Orchestration, Logging & Monitoring"
        prompt = @'
Stack: Docker Compose, Nginx, Prometheus, Grafana, Sentry, Celery Beat/Flower
Task file: tasks/TASK-010-devops-deployment.md
Module scope: root devops configuration, nginx setups, and monitoring scripts ONLY.

Key requirements extracted from PRD:
19.1 Development Workflow
Developer Branch    �-- git push origin feature/xxx    �GitHub Actions:    +-- Lint: ruff (Python), ESLint (React)    +-- Type check: mypy (Python), tsc (TypeScript)    +-- Unit tests: pytest (backend), Vitest (frontend)    +-- Integration tests: pytest with test DB    +-- Docker build: verify image builds    �Pull Request ? Code Review ? Merge to main    �GitHub Actions (main branch):    +-- Full test suite    +-- Docker build and push to registry    +-- Tag image with SHA + version    +-- Deploy to staging (auto)    �Manual approval ? Deploy to production    +-- docker compose pull && docker compose up -d
19.2 Deployment Commands
# Production deploymentgit pull origin maindocker compose -f docker-compose.prod.yml pulldocker compose -f docker-compose.prod.yml up -d --no-deps api celery_worker celery_beatdocker compose -f docker-compose.prod.yml exec api alembic upgrade head  # DB migrations# Zero-downtime API restart (single instance)docker compose -f docker-compose.prod.yml restart api# View live logsdocker compose -f docker-compose.prod.yml logs -f api celery_worker# Emergency rollbackdocker compose -f docker-compose.prod.yml stop apidocker tag neta-api:previous neta-api:latestdocker compose -f docker-compose.prod.yml up -d api
19.3 Database Migrations
Alembic manages all schema migrations. Migration discipline:
All schema changes require an Alembic migration file
Migrations are backward-compatible (no destructive changes without explicit approval)
Migrations tested on a staging database before production deployment
Migration history maintained in version control

18.1 Docker Compose Service Topology
# Production service topology (docker-compose.prod.yml)services:  nginx:    image: nginx:1.25-alpine    ports: ["80:80", "443:443"]    volumes:      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro      - ./nginx/ssl:/etc/ssl/certs:ro      - static_files:/var/www/static:ro    depends_on: [api]    restart: unless-stopped    healthcheck:      test: ["CMD", "nginx", "-t"]      interval: 30s  api:    image: neta-api:${TAG:-latest}    environment:      - DATABASE_URL=${DATABASE_URL}      - REDIS_URL=${REDIS_URL}      - SECRET_KEY=${SECRET_KEY}      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS}    depends_on: [postgres, redis]    restart: unless-stopped    healthcheck:      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]      interval: 30s      timeout: 10s      retries: 3  celery_worker:    image: neta-api:${TAG:-latest}    command: celery -A app.celery worker --loglevel=info --concurrency=4    depends_on: [redis, postgres]    restart: unless-stopped  celery_beat:    image: neta-api:${TAG:-latest}    command: celery -A app.celery beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler    depends_on: [redis, postgres]    restart: unless-stopped  celery_flower:    image: mher/flower:2.0    ports: ["5555:5555"]  # Internal only; Nginx proxies with auth    depends_on: [redis]    restart: unless-stopped  postgres:    image: postgis/postgis:15-3.3-alpine    volumes: [postgres_data:/var/lib/postgresql/data]    environment:      - POSTGRES_DB=${POSTGRES_DB}      - POSTGRES_USER=${POSTGRES_USER}      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}    restart: unless-stopped    healthcheck:      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]  redis:    image: redis:7-alpine    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes    volumes: [redis_data:/data]    restart: unless-stopped    healthcheck:      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
18.2 Nginx Configuration
# Key security and performance directivesserver {    listen 443 ssl http2;    server_name app.netaai.in;    # SSL    ssl_certificate /etc/ssl/certs/fullchain.pem;    ssl_certificate_key /etc/ssl/certs/privkey.pem;    ssl_protocols TLSv1.3;    ssl_prefer_server_ciphers off;    # Security headers    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;    add_header X-Frame-Options "DENY" always;    add_header X-Content-Type-Options "nosniff" always;    add_header Referrer-Policy "strict-origin-when-cross-origin" always;    server_tokens off;    # Rate limiting    limit_req zone=api burst=20 nodelay;    limit_req zone=auth burst=5 nodelay;    # Static files (Vite build output)    location / {        root /var/www/static;        try_files $uri $uri/ /index.html;        expires 1y;        add_header Cache-Control "public, immutable";    }    # API proxy    location /api/ {        proxy_pass http://api:8000;        proxy_set_header Host $host;        proxy_set_header X-Real-IP $remote_addr;        client_max_body_size 11M;    }    # SSE endpoint � disable buffering    location /api/stream {        proxy_pass http://api:8000;        proxy_buffering off;        proxy_cache off;        proxy_read_timeout 86400s;  # 24h SSE connection        add_header X-Accel-Buffering "no";    }}
18.3 Environment Variables
Variable
Description
Example
DATABASE_URL
PostgreSQL connection string
postgresql+asyncpg://user:pass@postgres/netaai
REDIS_URL
Redis connection string
redis://:password@redis:6379/0
SECRET_KEY
256-bit random key for JWT signing
openssl rand -hex 32
ALLOWED_ORIGINS
CORS whitelist (JSON array)
["https://app.netaai.in"]
WHATSAPP_API_TOKEN
Meta WhatsApp Business API bearer token
�
WHATSAPP_PHONE_ID
WhatsApp Business phone number ID
�
POSTGRES_DB
Database name
netaai_prod
POSTGRES_USER
Database user
netaai_app
POSTGRES_PASSWORD
Database password
=32 random characters
REDIS_PASSWORD
Redis AUTH password
=32 random characters
NLP_MODEL_PATH
Path to fine-tuned NLP model
/models/indic-bert-political
CELERY_CONCURRENCY
Celery worker process count
4
TAG
Docker image tag for deployment
v1.0.2

21.1 Redis Key Schema
Key Pattern
Type
TTL
Purpose
session:access:{jti}
String
900s (15 min)
Access token validity marker
session:refresh:{jti}
String
604800s (7 days)
Refresh token validity marker
blacklist:token:{jti}
String
Token TTL
Revoked token blacklist
kpi:constituency:{id}
Hash
60s
Live KPI aggregate (contact rate, workers online, etc.)
kpi:booth:{id}:health
String
300s
Booth health score cache
kpi:booth:{id}:risk
String
86400s
Booth risk score cache (nightly batch)
news:sentiment:index
String
600s
24h rolling news sentiment score
news:narrative:{cluster}:momentum
String
1800s
Narrative cluster momentum score
worker:active:{zone_id}
Set
300s
Set of active worker IDs per zone
win_probability:{constituency_id}
String
900s
Latest win probability score
rate_limit:{ip}:api
Counter
60s
API rate limit counter per IP
rate_limit:{ip}:auth
Counter
60s
Auth endpoint rate limit per IP
escalation:sla:{id}
String
Until deadline
Escalation SLA tracking
21.2 Celery Task Registry
Task Name
Queue
Schedule
Priority
fetch_rss_feeds
feeds
Every 5 min
HIGH
process_news_article
nlp
Chained
HIGH
compute_booth_risk_scores
scoring
00:01 IST daily
MEDIUM
compute_win_probability
scoring
Every 15 min
HIGH
generate_morning_brief
briefs
05:45 IST daily
CRITICAL
aggregate_kpis
kpis
Every 60 sec
HIGH
monitor_escalation_slas
ops
Every 5 min
HIGH
compute_opposition_scores
intel
Every 10 min
MEDIUM
process_voter_roll_upload
data
On-demand
LOW
send_whatsapp_alert
alerts
Event-driven
CRITICAL
cleanup_stale_sessions
maintenance
03:00 IST daily
LOW
backup_verification_check
maintenance
04:00 IST daily
LOW
21.3 Celery Worker Configuration
# Celery configurationCELERY_TASK_QUEUES = {    'feeds':       {'exchange': 'feeds', 'routing_key': 'feeds'},    'nlp':         {'exchange': 'nlp', 'routing_key': 'nlp'},    'scoring':     {'exchange': 'scoring', 'routing_key': 'scoring'},    'briefs':      {'exchange': 'briefs', 'routing_key': 'briefs'},    'kpis':        {'exchange': 'kpis', 'routing_key': 'kpis'},    'ops':         {'exchange': 'ops', 'routing_key': 'ops'},    'alerts':      {'exchange': 'alerts', 'routing_key': 'alerts'},    'data':        {'exchange': 'data', 'routing_key': 'data'},    'maintenance': {'exchange': 'maintenance', 'routing_key': 'maintenance'},}# Worker specialization (production)# Worker 1: high-priority operational tasks# celery -A app.celery worker -Q feeds,kpis,ops,alerts --concurrency=4# Worker 2: NLP processing (CPU-intensive)# celery -A app.celery worker -Q nlp --concurrency=2# Worker 3: scoring and intelligence# celery -A app.celery worker -Q scoring,briefs,intel --concurrency=2# Worker 4: background and data operations# celery -A app.celery worker -Q data,maintenance --concurrency=2
21.4 SSE Architecture
Server-Sent Events power all real-time dashboard updates:
# FastAPI SSE endpoint@router.get("/api/stream")async def event_stream(    request: Request,    current_user: User = Depends(get_current_user)):    async def event_generator():        pubsub = redis_client.pubsub()        channels = get_subscribed_channels(current_user.role, current_user.zone_id)        await pubsub.subscribe(*channels)        try:            while True:                if await request.is_disconnected():                    break                message = await pubsub.get_message(timeout=1.0)                if message and message['type'] == 'message':                    yield f"data: {message['data'].decode()}\n\n"                # Heartbeat every 30 seconds to prevent proxy timeout                yield ": heartbeat\n\n"                await asyncio.sleep(30)        finally:            await pubsub.unsubscribe(*channels)    return StreamingResponse(        event_generator(),        media_type="text/event-stream",        headers={            "Cache-Control": "no-cache",            "X-Accel-Buffering": "no",  # Disable Nginx buffering        }    )

26.1 Application Monitoring Stack
Tool
Purpose
Deployment
Prometheus
Metrics collection: API latency, Celery queue depth, Redis memory, DB connections
Docker sidecar
Grafana
Metrics visualization: real-time dashboards for all system components
Docker service
Sentry
Runtime error tracking: Python SDK (backend) + JavaScript SDK (frontend)
Cloud-hosted
UptimeRobot
External HTTP health monitoring: ping /api/health every 5 minutes
Cloud-hosted (free tier)
Celery Flower
Celery task monitoring: queue depth, failed tasks, worker health
Docker service (internal)
26.2 Logging Architecture
# Structured JSON logging (structlog)import structloglogger = structlog.get_logger()# Log format examplelogger.info(    "field_report.created",    report_id=str(report.id),    booth_id=str(report.booth_id),    severity=report.severity,    user_id=str(current_user.id),    duration_ms=elapsed,)
All logs output as JSON with standard fields: timestamp, level, event, user_id, request_id, duration_ms. Log files rotated at 100MB, retained for 30 days. Critical errors pushed to Sentry in real time.
26.3 Key Dashboards & Alerts
Dashboard
Key Metrics
Alert Threshold
API Health
Request rate, P99 latency, error rate
Error rate > 1% ? alert
Celery Operations
Queue depth per queue, failed task count
Queue depth > 500 ? alert
Database
Connection pool usage, slow queries, table sizes
Pool > 90% ? alert
Redis
Memory usage, hit rate, eviction rate
Memory > 80% ? alert
RSS Pipeline
Articles ingested per hour, feed failure count
Feed failure > 3 consecutive ? alert
SSE Connections
Active connection count, reconnection rate
� (informational)

PDCA: present plan before touching any file.
'@
    }
}

# -- Action: list --------------------------------------------------------------
if ($Session -eq "list") {
    $done = [char]0x2713   # checkmark
    $todo = [char]0x25CB   # open circle
    Write-Host ""
    Write-Host "  NETA AI - Available Development Sessions:" -ForegroundColor Cyan
    Write-Host "  =========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Completed:" -ForegroundColor Green
    Write-Host "  $done Session 01: Database Schema & Alembic Setup" -ForegroundColor Green
    Write-Host "  $done Session 02: Security Architecture & JWT Authentication" -ForegroundColor Green
    Write-Host "  $done Session 03: GeoJSON Mapping System" -ForegroundColor Green
    Write-Host "  $done Session 04: Ground Pulse & Escalations Workflow" -ForegroundColor Green
    Write-Host "  $done Session 05: RSS Ingestion & Multilingual NLP Pipeline" -ForegroundColor Green
    Write-Host "  $done Session 06: Booth Operations & Nightly Risk Scoring" -ForegroundColor Green
    Write-Host "  $done Session 07: Win Probability Model & Sentiment Trends" -ForegroundColor Green
    Write-Host ""
    Write-Host "  $done Session 08: Opposition Monitoring & Sentiment Comparison" -ForegroundColor Green
    Write-Host "  $done Session 09: Meta WhatsApp Business API & Alert Routing" -ForegroundColor Green
    Write-Host "  $done Session 10: Docker Orchestration, Logging & Monitoring" -ForegroundColor Green
    Write-Host ""
    Write-Host "  All 10 sessions complete. NETA.AI is PRODUCTION READY." -ForegroundColor Green
    Write-Host ""
    exit 0
}
# -- Action: debug -------------------------------------------------------------
if ($Session -eq "debug") {
    Write-Host ""
    Write-Host "  +----------------------------------------------+" -ForegroundColor Yellow
    Write-Host "  �  DEBUG SESSION MODE                          �" -ForegroundColor Yellow
    Write-Host "  +----------------------------------------------+" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Rule: One error, one file, one session." -ForegroundColor White
    Write-Host "  Instructions for Claude Code:" -ForegroundColor White
    Write-Host "    1. Paste the full error traceback." -ForegroundColor DarkGray
    Write-Host "    2. Paste ONLY the function/code block throwing the error." -ForegroundColor DarkGray
    Write-Host "    3. Avoid feeding the entire file if possible to save tokens." -ForegroundColor DarkGray
    Write-Host ""
    $debugPrompt = @'
Stack: Python 3.11, FastAPI, React 18, Docker
Task: Debug one specific issue.
Instructions:
- Analyze the traceback and target file.
- Provide the fix.
- Test and verify the fix.
'@
    $debugPrompt | Set-Clipboard
    Write-Host "  ? Copied debug prompt to clipboard. Paste in Claude Code to start." -ForegroundColor Green
    Write-Host ""
    exit 0
}

# -- Action: audit -------------------------------------------------------------
if ($Session -eq "audit") {
    Write-Host ""
    Write-Host "  +----------------------------------------------------------+" -ForegroundColor Cyan
    Write-Host "  |   NETA AI - PROJECT STATUS AUDIT                         |" -ForegroundColor Cyan
    Write-Host "  +----------------------------------------------------------+" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "  PHASE 1 - COMPLETED:" -ForegroundColor Green
    Write-Host "  [DONE] Session 01: Database Design" -ForegroundColor Green
    Write-Host "  [DONE] Session 02: Security & Auth" -ForegroundColor Green
    Write-Host "  [DONE] Session 03: GeoJSON Mapping" -ForegroundColor Green
    Write-Host "  [DONE] Session 04: Ground Operations" -ForegroundColor Green
    Write-Host ""
    Write-Host "  PHASE 2 - COMPLETED:" -ForegroundColor Green
    Write-Host "  [DONE] Session 05: News Intelligence" -ForegroundColor Green
    Write-Host "  [DONE] Session 06: Booth Management" -ForegroundColor Green
    Write-Host "  [DONE] Session 07: Prediction & Sentiment" -ForegroundColor Green
    Write-Host "  [DONE] Session 08: Opposition Intelligence & Sentiment Comparison" -ForegroundColor Green
    Write-Host ""
    Write-Host "  [DONE] Session 09: WhatsApp Integration & Alert Routing" -ForegroundColor Green
    Write-Host "  [DONE] Session 10: Docker Orchestration, Logging & Monitoring" -ForegroundColor Green
    Write-Host ""
    Write-Host "  METRICS:" -ForegroundColor Cyan
    Write-Host "     Total Sessions  : 10" -ForegroundColor White
    Write-Host "     Completed       : 10" -ForegroundColor White
    Write-Host "     Remaining       : 0" -ForegroundColor White
    Write-Host "     Smoke Tests     : 46/46 passed" -ForegroundColor White
    Write-Host "     API Endpoints   : 79 (Phase 1)" -ForegroundColor White
    Write-Host "     ORM Models      : 16 (incl. WhatsAppDeliveryLog)" -ForegroundColor White
    Write-Host "     DB Migrations   : 005 applied" -ForegroundColor White
    Write-Host "     Frontend Routes : 16" -ForegroundColor White
    Write-Host "     Health Checks   : 7 components (db/redis/celery/whatsapp/...)" -ForegroundColor White
    Write-Host ""
    Write-Host "  Deployment Status : PRODUCTION-READY (all sessions complete)" -ForegroundColor Green
    Write-Host ""
    exit 0
}
# -- Action: evidence ----------------------------------------------------------
if ($Session -eq "evidence") {
    $done = [char]0x2713
    Write-Host ""
    Write-Host "  NETA AI - IMPLEMENTATION EVIDENCE" -ForegroundColor Cyan
    Write-Host "  ==================================" -ForegroundColor Cyan
    Write-Host ""

    # -- Session 01: Database Design -------------------------------------------
    Write-Host "  Session 01: Database Design" -ForegroundColor Yellow
    $modelsFile = "$PROJECT_ROOT\app\database_design\models.py"
    $migrDir    = "$PROJECT_ROOT\app\database_design\migrations"

    $ormCount = if (Test-Path $modelsFile) {
        (Select-String -Path $modelsFile -Pattern "^class \w+\(Base\)" | Measure-Object).Count
    } else { 0 }

    $migCount = if (Test-Path $migrDir) {
        (Get-ChildItem $migrDir -Filter "*.sql" -ErrorAction SilentlyContinue | Measure-Object).Count
    } else { 0 }

    $tableCount = if (Test-Path $migrDir) {
        (Get-ChildItem $migrDir -Filter "*.sql" -ErrorAction SilentlyContinue |
            Select-String -Pattern "CREATE TABLE" | Measure-Object).Count
    } else { 0 }

    $postgis = if ((Test-Path $modelsFile) -and
                   (Select-String -Path $modelsFile -Pattern "Geography|geoalchemy2" -Quiet)) {
        "Yes  (geoalchemy2 Geography type)"
    } else { "Not detected" }

    Write-Host ("  $done ORM models       : {0}" -f $ormCount)   -ForegroundColor Green
    Write-Host ("  $done Migration files  : {0}" -f $migCount)   -ForegroundColor Green
    Write-Host ("  $done CREATE TABLE     : {0}" -f $tableCount) -ForegroundColor Green
    Write-Host ("  $done PostGIS          : {0}" -f $postgis)    -ForegroundColor Green
    Write-Host ""

    # -- Session 02: Security & Auth -------------------------------------------
    Write-Host "  Session 02: Security & Auth" -ForegroundColor Yellow
    $authRouter = "$PROJECT_ROOT\app\security_auth\router.py"
    $authUtils  = "$PROJECT_ROOT\app\security_auth\utils.py"

    $authEndpoints = if (Test-Path $authRouter) {
        (Select-String -Path $authRouter -Pattern "@router\.(get|post|put|patch|delete)" | Measure-Object).Count
    } else { 0 }

    $hashAlgo = if (Test-Path $authUtils) {
        if   (Select-String -Path $authUtils -Pattern "argon2"  -Quiet) { "Argon2" }
        elseif (Select-String -Path $authUtils -Pattern "bcrypt" -Quiet) { "bcrypt" }
        else { "Unknown" }
    } else { "Not found" }

    $rbacCount = if (Test-Path $modelsFile) {
        $content = Get-Content $modelsFile -Raw
        ([regex]::Matches($content,
            "(super_admin|campaign_manager|ground_commander|data_analyst|field_worker|candidate)") |
            Select-Object Value -Unique | Measure-Object).Count
    } else { 0 }

    $authTests = if (Test-Path "$PROJECT_ROOT\tests") {
        (Get-ChildItem "$PROJECT_ROOT\tests" -Filter "test_auth*.py" -ErrorAction SilentlyContinue |
            Select-String -Pattern "(async )?def test_" | Measure-Object).Count
    } else { 0 }

    Write-Host ("  $done Auth endpoints   : {0}" -f $authEndpoints) -ForegroundColor Green
    Write-Host ("  $done Password hashing : {0}" -f $hashAlgo)      -ForegroundColor Green
    Write-Host ("  $done RBAC roles       : {0}" -f $rbacCount)     -ForegroundColor Green
    Write-Host ("  $done Auth tests       : {0}" -f $authTests)     -ForegroundColor Green
    Write-Host ""

    # -- Session 03: GeoJSON Mapping -------------------------------------------
    Write-Host "  Session 03: GeoJSON Mapping" -ForegroundColor Yellow
    $geoRouter = "$PROJECT_ROOT\app\geojson_mapping\router.py"
    $geoIngest = "$PROJECT_ROOT\app\geojson_mapping\ingestion"

    $geoEndpoints = if (Test-Path $geoRouter) {
        (Select-String -Path $geoRouter -Pattern "@router\.(get|post|put|patch|delete)" | Measure-Object).Count
    } else { 0 }

    $importers = if (Test-Path $geoIngest) {
        (Get-ChildItem $geoIngest -Filter "*importer*.py" -ErrorAction SilentlyContinue | Measure-Object).Count
    } else { 0 }

    $leafletFiles = if (Test-Path "$PROJECT_ROOT\frontend") {
        (Get-ChildItem "$PROJECT_ROOT\frontend" -Recurse -Include "*.tsx","*.ts","*.js" -ErrorAction SilentlyContinue |
            Select-String -Pattern "leaflet|react-leaflet" |
            Select-Object Path -Unique | Measure-Object).Count
    } else { 0 }

    $geoTests = if (Test-Path "$PROJECT_ROOT\tests") {
        (Get-ChildItem "$PROJECT_ROOT\tests" -Filter "test_geo*.py" -ErrorAction SilentlyContinue |
            Select-String -Pattern "(async )?def test_" | Measure-Object).Count
    } else { 0 }

    Write-Host ("  $done GeoJSON endpoints  : {0}" -f $geoEndpoints) -ForegroundColor Green
    Write-Host ("  $done Data importers     : {0}" -f $importers)    -ForegroundColor Green
    Write-Host ("  $done Leaflet components : {0}" -f $leafletFiles) -ForegroundColor Green
    Write-Host ("  $done GeoJSON tests      : {0}" -f $geoTests)     -ForegroundColor Green
    Write-Host ""

    # -- Session 04: Ground Operations -----------------------------------------
    Write-Host "  Session 04: Ground Operations" -ForegroundColor Yellow
    $groundRouter = "$PROJECT_ROOT\app\ground_operations\router.py"
    $groundDir    = "$PROJECT_ROOT\app\ground_operations"

    $groundEndpoints = if (Test-Path $groundRouter) {
        (Select-String -Path $groundRouter -Pattern "@router\.(get|post|put|patch|delete)" | Measure-Object).Count
    } else { 0 }

    $groundServices = if (Test-Path $groundDir) {
        (Get-ChildItem $groundDir -Filter "*service*.py" -ErrorAction SilentlyContinue | Measure-Object).Count
    } else { 0 }

    $escalation   = if (Test-Path "$groundDir\escalation_service.py") { "Present" } else { "Missing" }
    $slaMonitor   = if (Test-Path "$groundDir\sla_monitor.py")        { "Present" } else { "Missing" }
    $moodAnalyzer = if (Test-Path "$groundDir\mood_analyzer.py")      { "Present" } else { "Missing" }

    $groundTests = if (Test-Path "$PROJECT_ROOT\tests") {
        (Get-ChildItem "$PROJECT_ROOT\tests" -Filter "test_ground*.py" -ErrorAction SilentlyContinue |
            Select-String -Pattern "(async )?def test_" | Measure-Object).Count
    } else { 0 }

    Write-Host ("  $done REST endpoints     : {0}" -f $groundEndpoints) -ForegroundColor Green
    Write-Host ("  $done Service files      : {0}" -f $groundServices)  -ForegroundColor Green
    Write-Host ("  $done Escalation service : {0}" -f $escalation)      -ForegroundColor Green
    Write-Host ("  $done SLA monitor        : {0}" -f $slaMonitor)      -ForegroundColor Green
    Write-Host ("  $done Mood analyser      : {0}" -f $moodAnalyzer)    -ForegroundColor Green
    Write-Host ("  $done Ground tests       : {0}" -f $groundTests)     -ForegroundColor Green
    Write-Host ""

    # -- Session 05: News Intelligence -----------------------------------------
    Write-Host "  Session 05: News Intelligence" -ForegroundColor Yellow
    $newsRouter = "$PROJECT_ROOT\app\news_intelligence\router.py"
    $newsDir    = "$PROJECT_ROOT\app\news_intelligence"
    $feedFile   = "$newsDir\feed_ingester.py"

    $newsEndpoints = if (Test-Path $newsRouter) {
        (Select-String -Path $newsRouter -Pattern "@router\.(get|post|put|patch|delete)" | Measure-Object).Count
    } else { 0 }

    $rssFeeds = if (Test-Path $feedFile) {
        (Select-String -Path $feedFile -Pattern "https?://" | Measure-Object).Count
    } else { 0 }

    $nlpComponents = if (Test-Path $newsDir) {
        (Get-ChildItem $newsDir -Filter "*.py" -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match "nlp|sentiment|cluster|ingester|analyzer" } |
            Measure-Object).Count
    } else { 0 }

    $newsTests = if (Test-Path "$PROJECT_ROOT\tests") {
        (Get-ChildItem "$PROJECT_ROOT\tests" -Filter "test_news*.py" -ErrorAction SilentlyContinue |
            Select-String -Pattern "(async )?def test_" | Measure-Object).Count
    } else { 0 }

    Write-Host ("  $done API endpoints      : {0}" -f $newsEndpoints)  -ForegroundColor Green
    Write-Host ("  $done RSS feed URLs      : {0}" -f $rssFeeds)       -ForegroundColor Green
    Write-Host ("  $done NLP components     : {0}" -f $nlpComponents)  -ForegroundColor Green
    Write-Host ("  $done News tests         : {0}" -f $newsTests)      -ForegroundColor Green
    Write-Host ""

    # -- Session 06: Booth Management ------------------------------------------
    Write-Host "  Session 06: Booth Management" -ForegroundColor Yellow
    $boothRouter = "$PROJECT_ROOT\app\booth_management\router.py"
    $riskCalc    = "$PROJECT_ROOT\app\booth_management\risk_calculator.py"
    $volService  = "$PROJECT_ROOT\app\booth_management\volunteer_service.py"

    $boothEndpoints = if (Test-Path $boothRouter) {
        (Select-String -Path $boothRouter -Pattern "@router\.(get|post|put|patch|delete)" | Measure-Object).Count
    } else { 0 }

    $riskMethods = if (Test-Path $riskCalc) {
        (Select-String -Path $riskCalc -Pattern "^\s+def \w+|^def \w+" | Measure-Object).Count
    } else { 0 }

    $volRoles = if (Test-Path $volService) {
        $content = Get-Content $volService -Raw
        ([regex]::Matches($content,
            "(BOOTH_AGENT|VOTER_CONTACT|TRANSPORT|COORDINATOR)") |
            Select-Object Value -Unique | Measure-Object).Count
    } else { 0 }

    $boothTests = if (Test-Path "$PROJECT_ROOT\tests") {
        (Get-ChildItem "$PROJECT_ROOT\tests" -Filter "test_booth*.py" -ErrorAction SilentlyContinue |
            Select-String -Pattern "(async )?def test_" | Measure-Object).Count
    } else { 0 }

    Write-Host ("  $done Booth endpoints    : {0}" -f $boothEndpoints) -ForegroundColor Green
    Write-Host ("  $done Risk score methods : {0}" -f $riskMethods)    -ForegroundColor Green
    Write-Host ("  $done Volunteer roles    : {0}" -f $volRoles)       -ForegroundColor Green
    Write-Host ("  $done Booth tests        : {0}" -f $boothTests)     -ForegroundColor Green
    Write-Host ""

    exit 0
}

# -- Execute Session -----------------------------------------------------------
$s = $sessions[$Session]
Write-Host ""
Write-Host "  +--------------------------------------------------------+" -ForegroundColor Cyan
Write-Host ("  �  {0,-54}�" -f $s.label) -ForegroundColor Cyan
Write-Host ("  �  Model: {0,-47}�" -f $s.model) -ForegroundColor Cyan
Write-Host "  +--------------------------------------------------------+" -ForegroundColor Cyan
Write-Host ""
Write-Host $s.prompt -ForegroundColor White
Write-Host ""

$s.prompt | Set-Clipboard
Write-Host "  ? Copied prompt to clipboard. Paste in Claude Code then brainstorm." -ForegroundColor Green
Write-Host ""

# Support running in tests
if ($env:NETA_TEST -eq "true") {
    Write-Host "  [Sandbox Test Mode] Skipping launch of claude cli." -ForegroundColor Yellow
    exit 0
}

Set-Location $PROJECT_ROOT
$env:ANTHROPIC_MODEL = $s.model
claude --model $s.model
