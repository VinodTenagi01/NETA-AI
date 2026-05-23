"""Test models for ground operations testing - SQLite compatible."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Float, Date, Numeric
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    """Test User model."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(15))
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    zone_id = Column(String(36), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    mfa_secret = Column(String(255))
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime(timezone=True))
    last_checkin_at = Column(DateTime(timezone=True), nullable=True)
    login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class Constituency(Base):
    """Test Constituency model."""
    __tablename__ = "constituencies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    ac_number = Column(String(10), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    state = Column(String(100), nullable=False)
    total_booths = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class CampaignZone(Base):
    """Test CampaignZone model."""
    __tablename__ = "campaign_zones"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    constituency_id = Column(String(36), ForeignKey("constituencies.id"), nullable=False)
    zone_code = Column(String(50), nullable=False)
    zone_name = Column(String(255), nullable=False)
    assigned_commander_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    total_booths = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class Booth(Base):
    """Test Booth model."""
    __tablename__ = "booths"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    constituency_id = Column(String(36), ForeignKey("constituencies.id"), nullable=False)
    zone_id = Column(String(36), ForeignKey("campaign_zones.id"), nullable=False)
    booth_number = Column(String(10), nullable=False)
    booth_name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    address = Column(String(500), nullable=True)
    total_voters = Column(Integer, default=0)
    female_voters = Column(Integer, default=0)
    male_voters = Column(Integer, default=0)
    third_gender = Column(Integer, default=0)
    assigned_commander = Column(String(36), ForeignKey("users.id"), nullable=True)
    risk_score = Column(Float, default=50.0)
    contact_rate = Column(Float, default=0.0)
    health_score = Column(Float, default=50.0)
    swing_booth = Column(Boolean, default=False)
    historical_margin = Column(Float, nullable=True)
    last_report_at = Column(DateTime(timezone=True), nullable=True)
    last_contact_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class FieldReport(Base):
    """Test FieldReport model."""
    __tablename__ = "field_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    booth_id = Column(String(36), ForeignKey("booths.id"), nullable=False)
    reported_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(String(500), nullable=False)
    severity = Column(Integer, nullable=False)
    voter_sentiment = Column(String(20), nullable=True)
    photo_url = Column(String(500), nullable=True)
    audio_url = Column(String(500), nullable=True)
    gps_lat = Column(Float, nullable=True)
    gps_lng = Column(Float, nullable=True)
    reported_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class Escalation(Base):
    """Test Escalation model."""
    __tablename__ = "escalations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    field_report_id = Column(String(36), ForeignKey("field_reports.id"), nullable=False)
    assigned_to = Column(String(36), ForeignKey("users.id"), nullable=False)
    status = Column(String(20), nullable=False, default="NEW")
    sla_minutes = Column(Integer, nullable=False)
    sla_deadline = Column(DateTime(timezone=True), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(String(2000), nullable=True)
    escalated_to = Column(String(36), ForeignKey("users.id"), nullable=True)
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class WorkerAttendance(Base):
    """Test WorkerAttendance model."""
    __tablename__ = "worker_attendance"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    booth_id = Column(String(36), ForeignKey("booths.id"), nullable=False)
    zone_id = Column(String(36), ForeignKey("campaign_zones.id"), nullable=False)
    checked_in_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    checked_out_at = Column(DateTime(timezone=True), nullable=True)
    gps_lat = Column(Float, nullable=True)
    gps_lng = Column(Float, nullable=True)
    is_present = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class MoodSnapshot(Base):
    """Test MoodSnapshot model."""
    __tablename__ = "mood_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    zone_id = Column(String(36), ForeignKey("campaign_zones.id"), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    avg_sentiment_score = Column(Numeric(3, 3), nullable=False)
    positive_pct = Column(Numeric(5, 2), nullable=False, default=0)
    neutral_pct = Column(Numeric(5, 2), nullable=False, default=0)
    negative_pct = Column(Numeric(5, 2), nullable=False, default=0)
    mixed_pct = Column(Numeric(5, 2), nullable=False, default=0)
    report_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
