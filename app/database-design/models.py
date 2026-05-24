"""
SQLAlchemy ORM models — exact match to PRD Section 20.1 schema.
All models use UUID PKs and TIMESTAMPTZ columns.
PostGIS Geography type used for booth locations.
"""
import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import BYTEA, INET, JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database_design.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(15))
    password_hash = Column(String(255), nullable=False)
    role = Column(
        String(50),
        nullable=False,
        comment="super_admin|campaign_manager|ground_commander|data_analyst|field_worker|candidate",
    )
    zone_id = Column(UUID(as_uuid=True), ForeignKey("campaign_zones.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    mfa_secret = Column(String(255))
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime(timezone=True))
    login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    zone = relationship("CampaignZone", back_populates="users", foreign_keys=[zone_id])
    field_reports = relationship("FieldReport", back_populates="reporter", foreign_keys="FieldReport.reported_by")

    __table_args__ = (
        CheckConstraint(
            "role IN ('super_admin','campaign_manager','ground_commander','data_analyst','field_worker','candidate')",
            name="ck_users_role",
        ),
    )


class Constituency(Base):
    __tablename__ = "constituencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    state = Column(String(100), nullable=False)
    ac_number = Column(String(10), unique=True, nullable=False)
    total_booths = Column(Integer)
    total_voters = Column(Integer)
    geojson_url = Column(Text)
    boundary_geojson = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    zones = relationship("CampaignZone", back_populates="constituency")
    booths = relationship("Booth", back_populates="constituency")
    demographics = relationship("ConstituencyDemographics", back_populates="constituency")


class CampaignZone(Base):
    __tablename__ = "campaign_zones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    constituency_id = Column(UUID(as_uuid=True), ForeignKey("constituencies.id"), nullable=False)
    zone_name = Column(String(100), nullable=False)
    zone_code = Column(String(10), nullable=False)
    description = Column(Text)
    boundary_geojson = Column(JSONB)
    key_areas = Column(Text)
    approx_booth_count = Column(Integer)
    approx_voter_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    constituency = relationship("Constituency", back_populates="zones")
    booths = relationship("Booth", back_populates="zone")
    users = relationship("User", back_populates="zone", foreign_keys="User.zone_id")

    __table_args__ = (UniqueConstraint("constituency_id", "zone_code", name="uq_zone_code"),)


class Booth(Base):
    __tablename__ = "booths"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    constituency_id = Column(UUID(as_uuid=True), ForeignKey("constituencies.id"), nullable=False)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("campaign_zones.id"), nullable=True)
    booth_number = Column(String(10), nullable=False)
    booth_name = Column(String(255))
    location = Column(Geography(geometry_type="POINT", srid=4326))
    address = Column(Text)
    total_voters = Column(Integer, default=0)
    female_voters = Column(Integer, default=0)
    male_voters = Column(Integer, default=0)
    third_gender = Column(Integer, default=0)
    assigned_commander = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    risk_score = Column(Numeric(5, 2), default=50.0)
    contact_rate = Column(Numeric(5, 2), default=0.0)
    health_score = Column(Numeric(5, 2), default=50.0)
    swing_booth = Column(Boolean, default=False, nullable=False)
    historical_margin = Column(Numeric(5, 2))
    last_report_at = Column(DateTime(timezone=True))
    last_contact_at = Column(DateTime(timezone=True))
    catchment_geojson = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    constituency = relationship("Constituency", back_populates="booths")
    zone = relationship("CampaignZone", back_populates="booths")
    field_reports = relationship("FieldReport", back_populates="booth")
    volunteers = relationship("BoothVolunteer", back_populates="booth")
    voters = relationship("Voter", back_populates="booth")

    __table_args__ = (
        UniqueConstraint("constituency_id", "booth_number", name="uq_booth_number"),
        Index("idx_booth_zone", "zone_id"),
        Index("idx_booth_risk", "risk_score"),
    )


class BoothVolunteer(Base):
    __tablename__ = "booth_volunteers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booth_id = Column(UUID(as_uuid=True), ForeignKey("booths.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    volunteer_name = Column(String(255), nullable=False)
    phone = Column(String(15))
    role = Column(String(30))
    is_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    booth = relationship("Booth", back_populates="volunteers")

    __table_args__ = (
        CheckConstraint(
            "role IN ('BOOTH_AGENT','VOTER_CONTACT','TRANSPORT','COORDINATOR')",
            name="ck_volunteer_role",
        ),
    )


class FieldReport(Base):
    __tablename__ = "field_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booth_id = Column(UUID(as_uuid=True), ForeignKey("booths.id"), nullable=False)
    reported_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(SmallInteger, nullable=False)
    voter_sentiment = Column(String(20))
    sentiment_score = Column(Numeric(4, 3))
    photo_url = Column(Text)
    gps_lat = Column(Numeric(9, 6))
    gps_lng = Column(Numeric(9, 6))
    processed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    booth = relationship("Booth", back_populates="field_reports")
    reporter = relationship("User", back_populates="field_reports", foreign_keys=[reported_by])

    __table_args__ = (
        CheckConstraint(
            "category IN ('VOTER_MOOD','INFRASTRUCTURE','OPPOSITION_ACTIVITY','SECURITY','LOGISTICS','OTHER')",
            name="ck_report_category",
        ),
        CheckConstraint("severity BETWEEN 1 AND 5", name="ck_report_severity"),
        CheckConstraint(
            "voter_sentiment IN ('POSITIVE','NEUTRAL','NEGATIVE','MIXED') OR voter_sentiment IS NULL",
            name="ck_report_sentiment",
        ),
        Index("idx_field_reports_booth_created", "booth_id", "created_at"),
        Index("idx_field_reports_severity_high", "severity"),
    )


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feed_source = Column(String(100), nullable=False)
    feed_tier = Column(SmallInteger, nullable=False)
    title = Column(Text, nullable=False)
    url = Column(Text, unique=True, nullable=False)
    body_excerpt = Column(Text)
    language = Column(String(10), default="en")
    published_at = Column(DateTime(timezone=True))
    ingested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sentiment_polarity = Column(Numeric(4, 3))
    political_tone = Column(String(30))
    impact_score = Column(Numeric(4, 2))
    entity_tags = Column(JSONB, default=list)
    narrative_cluster = Column(String(100))
    processed = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        CheckConstraint("feed_tier IN (1, 2, 3)", name="ck_news_tier"),
        CheckConstraint(
            "political_tone IN ('PRO_INCUMBENT','NEUTRAL','ANTI_INCUMBENT') OR political_tone IS NULL",
            name="ck_news_tone",
        ),
        Index("idx_news_published_sentiment", "published_at", "sentiment_polarity"),
        Index("idx_news_impact", "impact_score"),
    )


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    source_module = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    affected_booths = Column(ARRAY(UUID(as_uuid=True)))
    meta = Column(JSONB, default=dict)
    acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    escalations = relationship("Escalation", back_populates="alert")

    __table_args__ = (
        CheckConstraint("severity IN ('CRITICAL','WARNING','INFO')", name="ck_alert_severity"),
        Index("idx_alerts_severity_created", "severity", "created_at"),
    )


class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id"), nullable=True)
    field_report_id = Column(UUID(as_uuid=True), ForeignKey("field_reports.id"), nullable=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(String(20), default="NEW", nullable=False)
    sla_minutes = Column(Integer, nullable=False)
    sla_deadline = Column(DateTime(timezone=True), nullable=False)
    whatsapp_sent = Column(Boolean, default=False, nullable=False)
    reminder_sent = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    alert = relationship("Alert", back_populates="escalations")

    __table_args__ = (
        CheckConstraint(
            "status IN ('NEW','ASSIGNED','IN_PROGRESS','RESOLVED','CLOSED')",
            name="ck_escalation_status",
        ),
    )


class IntelligenceBrief(Base):
    __tablename__ = "intelligence_briefs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brief_date = Column(Date, unique=True, nullable=False)
    executive_summary = Column(Text, nullable=False)
    top_risks = Column(JSONB, default=list, nullable=False)
    opportunity_zones = Column(JSONB, default=list, nullable=False)
    recommended_actions = Column(JSONB, default=list, nullable=False)
    narrative_digest = Column(Text)
    win_probability = Column(Numeric(5, 2))
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    delivered_at = Column(DateTime(timezone=True))
    delivery_status = Column(String(20), default="PENDING")


class IntelligenceScore(Base):
    __tablename__ = "intelligence_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(20), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    score_type = Column(String(50), nullable=False)
    score_value = Column(Numeric(7, 4), nullable=False)
    computed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('constituency','zone','booth')",
            name="ck_score_entity_type",
        ),
        Index("idx_intelligence_scores_entity", "entity_id", "score_type", "computed_at"),
    )


class Voter(Base):
    __tablename__ = "voters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booth_id = Column(UUID(as_uuid=True), ForeignKey("booths.id"), nullable=False)
    voter_id = Column(String(50), unique=True)
    full_name = Column(String(255), nullable=False)
    gender = Column(String(1))
    age = Column(SmallInteger)
    phone_encrypted = Column(BYTEA)
    address_encrypted = Column(BYTEA)
    is_contacted = Column(Boolean, default=False, nullable=False)
    last_contacted = Column(DateTime(timezone=True))
    upload_batch_id = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    booth = relationship("Booth", back_populates="voters")

    __table_args__ = (
        CheckConstraint("gender IN ('M','F','O') OR gender IS NULL", name="ck_voter_gender"),
        Index("idx_voters_booth", "booth_id"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(UUID(as_uuid=True))
    old_value = Column(JSONB)
    new_value = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ConstituencyDemographics(Base):
    __tablename__ = "constituency_demographics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    constituency_id = Column(UUID(as_uuid=True), ForeignKey("constituencies.id"), nullable=False)
    ward_id = Column(String(20))
    ward_name = Column(String(255))
    total_population = Column(Integer)
    voter_population = Column(Integer)
    male_voters = Column(Integer)
    female_voters = Column(Integer)
    sc_population_pct = Column(Numeric(5, 2))
    st_population_pct = Column(Numeric(5, 2))
    obc_population_pct = Column(Numeric(5, 2))
    literacy_rate_pct = Column(Numeric(5, 2))
    youth_voter_pct = Column(Numeric(5, 2))
    data_source = Column(String(100))
    data_year = Column(SmallInteger)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    constituency = relationship("Constituency", back_populates="demographics")

    __table_args__ = (Index("idx_demographics_ward", "constituency_id", "ward_id"),)


class BoothWardMapping(Base):
    __tablename__ = "booth_ward_mapping"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booth_id = Column(UUID(as_uuid=True), ForeignKey("booths.id"), nullable=False, unique=True)
    ward_id = Column(String(20), nullable=False)
    ward_name = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
