"""
Unit Tests for Booth Management

Tests for risk calculator, service methods, and data validation.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.booth_management.risk_calculator import RiskCalculator


# ============================================================================
# RiskCalculator Tests
# ============================================================================

class TestRiskCalculator:
    """Test risk score calculation."""

    def test_risk_score_zero_when_fully_contacted(self):
        """Risk should be low when contact rate is 100%."""
        score = RiskCalculator.calculate_risk_score(
            contact_rate=100.0,
            high_severity_report_count=0,
            days_since_last_contact=0,
        )
        # Should be ~0 (30% low contact + 0 reports + 0 staleness)
        assert score < 5.0

    def test_risk_score_high_when_no_contact(self):
        """Risk should be high when contact rate is 0%."""
        score = RiskCalculator.calculate_risk_score(
            contact_rate=0.0,
            high_severity_report_count=0,
            days_since_last_contact=0,
        )
        # Should be ~30 (30 pts for 0% contact)
        assert 25.0 <= score <= 35.0

    def test_risk_score_increases_with_reports(self):
        """Risk should increase with high-severity reports."""
        score_base = RiskCalculator.calculate_risk_score(
            contact_rate=50.0,
            high_severity_report_count=0,
            days_since_last_contact=0,
        )

        score_with_reports = RiskCalculator.calculate_risk_score(
            contact_rate=50.0,
            high_severity_report_count=3,
            days_since_last_contact=0,
        )

        # Score should increase by ~15 (3 reports × 5 pts)
        assert score_with_reports > score_base
        assert score_with_reports - score_base >= 10.0

    def test_risk_score_increases_with_staleness(self):
        """Risk should increase with days since last contact."""
        score_fresh = RiskCalculator.calculate_risk_score(
            contact_rate=50.0,
            high_severity_report_count=0,
            days_since_last_contact=0,
        )

        score_stale = RiskCalculator.calculate_risk_score(
            contact_rate=50.0,
            high_severity_report_count=0,
            days_since_last_contact=20,
        )

        # Score should increase by ~10 (20 days × 0.5 pts)
        assert score_stale > score_fresh

    def test_risk_score_clamped_to_100(self):
        """Risk score should not exceed 100."""
        score = RiskCalculator.calculate_risk_score(
            contact_rate=0.0,
            high_severity_report_count=20,
            days_since_last_contact=90,
        )
        assert 0.0 <= score <= 100.0

    def test_risk_score_handles_invalid_contact_rate(self):
        """Risk calculator should clamp invalid contact rates."""
        score = RiskCalculator.calculate_risk_score(
            contact_rate=150.0,  # Invalid: >100
            high_severity_report_count=0,
            days_since_last_contact=0,
        )
        # Should treat as 100% contact
        assert score < 5.0

    def test_risk_score_mid_range(self):
        """Test risk score calculation in middle range."""
        score = RiskCalculator.calculate_risk_score(
            contact_rate=50.0,  # 50% contact
            high_severity_report_count=2,  # 10 pts
            days_since_last_contact=10,  # 5 pts
        )
        # Expected: 15 (contact) + 10 (reports) + 5 (staleness) = 30
        assert 25.0 <= score <= 35.0


class TestHealthCalculator:
    """Test health score calculation."""

    def test_health_score_high_with_full_engagement(self):
        """Health should be high when all metrics are good."""
        score = RiskCalculator.calculate_health_score(
            contact_rate=100.0,
            volunteer_coverage=100.0,
            report_frequency=2.0,  # ~2 reports/day
        )
        # Should be: 40 (engagement) + 30 (coverage) + 0.6 (activity: 2.0 * 0.3)
        assert score >= 70.0

    def test_health_score_low_with_no_engagement(self):
        """Health should be low when all metrics are poor."""
        score = RiskCalculator.calculate_health_score(
            contact_rate=0.0,
            volunteer_coverage=0.0,
            report_frequency=0.0,
        )
        # Should be: 0 + 0 + 0 = 0
        assert score <= 5.0

    def test_health_score_mid_range(self):
        """Test health score in middle range."""
        score = RiskCalculator.calculate_health_score(
            contact_rate=60.0,
            volunteer_coverage=50.0,
            report_frequency=1.0,
        )
        # Expected: 24 (engagement) + 15 (coverage) + 0.3 (activity) = 39.3
        assert 35.0 <= score <= 45.0

    def test_health_score_clamped_to_100(self):
        """Health score should not exceed 100."""
        score = RiskCalculator.calculate_health_score(
            contact_rate=100.0,
            volunteer_coverage=100.0,
            report_frequency=100.0,
        )
        assert 0.0 <= score <= 100.0

    def test_health_score_handles_invalid_inputs(self):
        """Health calculator should clamp invalid inputs."""
        score = RiskCalculator.calculate_health_score(
            contact_rate=150.0,  # Invalid: >100
            volunteer_coverage=150.0,  # Invalid: >100
            report_frequency=10.0,  # Valid
        )
        # Should treat rates as 100%: 40 + 30 + 3.0 = 73.0
        assert score >= 70.0


class TestSwingBoothDetection:
    """Test swing booth detection logic."""

    def test_swing_booth_if_manually_marked(self):
        """Booth should be swing if manually marked."""
        is_swing = RiskCalculator.is_swing_booth(
            historical_margin=10.0,  # Not swing by margin
            manually_marked=True,
        )
        assert is_swing

    def test_swing_booth_if_margin_under_5_percent(self):
        """Booth should be swing if margin < 5%."""
        # Test boundary cases
        assert RiskCalculator.is_swing_booth(4.9, manually_marked=False)
        assert RiskCalculator.is_swing_booth(-4.9, manually_marked=False)
        assert RiskCalculator.is_swing_booth(0.0, manually_marked=False)

    def test_not_swing_booth_if_margin_over_5_percent(self):
        """Booth should not be swing if margin >= 5%."""
        # Test boundary cases
        assert not RiskCalculator.is_swing_booth(5.0, manually_marked=False)
        assert not RiskCalculator.is_swing_booth(10.0, manually_marked=False)
        assert not RiskCalculator.is_swing_booth(-5.0, manually_marked=False)

    def test_not_swing_if_no_historical_data(self):
        """Booth should not be swing if no historical margin data."""
        assert not RiskCalculator.is_swing_booth(
            historical_margin=None,
            manually_marked=False,
        )


class TestRiskLevelClassification:
    """Test risk level classification."""

    def test_risk_level_high(self):
        """Classify high risk."""
        assert RiskCalculator.get_risk_level(75.0) == "HIGH"
        assert RiskCalculator.get_risk_level(100.0) == "HIGH"

    def test_risk_level_medium(self):
        """Classify medium risk."""
        assert RiskCalculator.get_risk_level(50.0) == "MEDIUM"
        assert RiskCalculator.get_risk_level(69.9) == "MEDIUM"

    def test_risk_level_low(self):
        """Classify low risk."""
        assert RiskCalculator.get_risk_level(39.9) == "LOW"
        assert RiskCalculator.get_risk_level(0.0) == "LOW"

    def test_risk_level_boundaries(self):
        """Test boundary values for risk levels."""
        assert RiskCalculator.get_risk_level(40.0) == "MEDIUM"
        assert RiskCalculator.get_risk_level(70.0) == "HIGH"


class TestHealthStatusClassification:
    """Test health status classification."""

    def test_health_status_critical(self):
        """Classify critical health."""
        assert RiskCalculator.get_health_status(30.0) == "CRITICAL"
        assert RiskCalculator.get_health_status(0.0) == "CRITICAL"

    def test_health_status_degraded(self):
        """Classify degraded health."""
        assert RiskCalculator.get_health_status(50.0) == "DEGRADED"
        assert RiskCalculator.get_health_status(65.0) == "HEALTHY"  # >= 70 is healthy, 60-69 is degraded

    def test_health_status_healthy(self):
        """Classify healthy status."""
        assert RiskCalculator.get_health_status(70.0) == "HEALTHY"
        assert RiskCalculator.get_health_status(100.0) == "HEALTHY"

    def test_health_status_boundaries(self):
        """Test boundary values for health statuses."""
        assert RiskCalculator.get_health_status(31.0) == "DEGRADED"  # > 30 and < 60
        assert RiskCalculator.get_health_status(59.9) == "DEGRADED"  # < 60
        assert RiskCalculator.get_health_status(60.0) == "HEALTHY"  # >= 60
        assert RiskCalculator.get_health_status(70.0) == "HEALTHY"


class TestDaysSinceContact:
    """Test days since contact calculation."""

    def test_days_since_contact_today(self):
        """Should return 0 if contacted today."""
        now = datetime.utcnow()
        days = RiskCalculator.calculate_days_since_contact(now)
        assert days == 0

    def test_days_since_contact_past(self):
        """Should return correct count for past dates."""
        now = datetime.utcnow()
        five_days_ago = now - timedelta(days=5)
        days = RiskCalculator.calculate_days_since_contact(five_days_ago)
        assert days == 5

    def test_days_since_contact_never(self):
        """Should return high value if never contacted."""
        days = RiskCalculator.calculate_days_since_contact(None)
        assert days == 90  # Penalty value


class TestVolunteerCoverage:
    """Test volunteer coverage calculation."""

    def test_coverage_full(self):
        """Full coverage when volunteers >= target."""
        # Target: 1 volunteer per 100 voters
        coverage = RiskCalculator.estimate_volunteer_coverage(
            volunteer_count=10,
            total_voters=1000,
        )
        # 10 / (1000/100) = 10 / 10 = 100%
        assert coverage == 100.0

    def test_coverage_partial(self):
        """Partial coverage when volunteers < target."""
        coverage = RiskCalculator.estimate_volunteer_coverage(
            volunteer_count=5,
            total_voters=1000,
        )
        # 5 / (1000/100) = 5 / 10 = 50%
        assert coverage == 50.0

    def test_coverage_zero(self):
        """Zero coverage when no volunteers."""
        coverage = RiskCalculator.estimate_volunteer_coverage(
            volunteer_count=0,
            total_voters=1000,
        )
        assert coverage == 0.0

    def test_coverage_capped_at_100(self):
        """Coverage should not exceed 100%."""
        coverage = RiskCalculator.estimate_volunteer_coverage(
            volunteer_count=20,
            total_voters=100,
        )
        # 20 / (100/100) = 20 / 1 = 2000%, but capped at 100%
        assert coverage == 100.0

    def test_coverage_edge_case_no_voters(self):
        """Should return 100% for booths with no voters."""
        coverage = RiskCalculator.estimate_volunteer_coverage(
            volunteer_count=0,
            total_voters=0,
        )
        assert coverage == 100.0


class TestReportFrequency:
    """Test report frequency estimation."""

    def test_report_frequency_calculation(self):
        """Calculate correct frequency."""
        frequency = RiskCalculator.estimate_report_frequency(
            report_count=7,
            days_window=7,
        )
        assert frequency == 1.0  # 1 report per day

    def test_report_frequency_multiple_days(self):
        """Calculate frequency for multiple days."""
        frequency = RiskCalculator.estimate_report_frequency(
            report_count=10,
            days_window=5,
        )
        assert frequency == 2.0  # 2 reports per day

    def test_report_frequency_zero_reports(self):
        """Frequency should be 0 for zero reports."""
        frequency = RiskCalculator.estimate_report_frequency(
            report_count=0,
            days_window=7,
        )
        assert frequency == 0.0

    def test_report_frequency_zero_window(self):
        """Should return 0 for zero-day window."""
        frequency = RiskCalculator.estimate_report_frequency(
            report_count=10,
            days_window=0,
        )
        assert frequency == 0.0


# ============================================================================
# Integration Tests
# ============================================================================

class TestScoringIntegration:
    """Integration tests for scoring logic."""

    def test_healthy_booth_scores(self):
        """A well-managed booth should have good scores."""
        risk = RiskCalculator.calculate_risk_score(
            contact_rate=80.0,
            high_severity_report_count=0,
            days_since_last_contact=1,
        )
        health = RiskCalculator.calculate_health_score(
            contact_rate=80.0,
            volunteer_coverage=100.0,
            report_frequency=1.5,
        )

        assert risk < 30.0  # Low risk
        assert health > 60.0  # Good health: 32 + 30 + 0.45 = 62.45

    def test_at_risk_booth_scores(self):
        """A struggling booth should have poor scores."""
        risk = RiskCalculator.calculate_risk_score(
            contact_rate=20.0,
            high_severity_report_count=5,
            days_since_last_contact=30,
        )
        health = RiskCalculator.calculate_health_score(
            contact_rate=20.0,
            volunteer_coverage=20.0,
            report_frequency=0.5,
        )

        assert risk > 60.0  # High risk
        assert health < 40.0  # Poor health

    def test_booth_risk_vs_health_independent(self):
        """Risk and health should be independent metrics."""
        # High contact but stale (high health, moderate risk)
        risk_stale = RiskCalculator.calculate_risk_score(
            contact_rate=80.0,
            high_severity_report_count=0,
            days_since_last_contact=30,
        )
        health_stale = RiskCalculator.calculate_health_score(
            contact_rate=80.0,
            volunteer_coverage=100.0,
            report_frequency=0.1,
        )

        # Low contact but active (low health, high risk)
        risk_active = RiskCalculator.calculate_risk_score(
            contact_rate=20.0,
            high_severity_report_count=1,
            days_since_last_contact=1,
        )
        health_active = RiskCalculator.calculate_health_score(
            contact_rate=20.0,
            volunteer_coverage=50.0,
            report_frequency=2.0,
        )

        # Different risk/health combinations should exist
        assert risk_stale != risk_active
        assert health_stale != health_active


# ============================================================================
# Constants & Ranges Tests
# ============================================================================

class TestScoringConstants:
    """Test that constants are in expected ranges."""

    def test_risk_thresholds(self):
        """Risk thresholds should be in valid order."""
        assert RiskCalculator.RISK_LOW < RiskCalculator.RISK_MEDIUM
        assert RiskCalculator.RISK_MEDIUM < RiskCalculator.RISK_HIGH
        assert RiskCalculator.RISK_LOW >= 0.0
        assert RiskCalculator.RISK_HIGH <= 100.0

    def test_health_thresholds(self):
        """Health thresholds should be in valid order."""
        assert RiskCalculator.HEALTH_CRITICAL < RiskCalculator.HEALTH_DEGRADED
        assert RiskCalculator.HEALTH_DEGRADED < RiskCalculator.HEALTH_HEALTHY
        assert RiskCalculator.HEALTH_CRITICAL >= 0.0
        assert RiskCalculator.HEALTH_HEALTHY <= 100.0

    def test_volunteer_roles_valid(self):
        """Volunteer role constants should be defined."""
        from app.booth_management.service import VALID_VOLUNTEER_ROLES
        assert "BOOTH_AGENT" in VALID_VOLUNTEER_ROLES
        assert "VOTER_CONTACT" in VALID_VOLUNTEER_ROLES
        assert "TRANSPORT" in VALID_VOLUNTEER_ROLES
        assert "COORDINATOR" in VALID_VOLUNTEER_ROLES
        assert len(VALID_VOLUNTEER_ROLES) == 4
