"""
Risk Calculator Service

Stateless scoring logic for booth risk and health scores.
"""

from datetime import datetime, timedelta
from typing import Optional


class RiskCalculator:
    """
    Calculates booth risk and health scores based on various metrics.
    All methods are static/stateless for testability.
    """

    # Risk score thresholds
    RISK_HIGH = 70.0
    RISK_MEDIUM = 40.0
    RISK_LOW = 0.0

    # Health score thresholds
    HEALTH_CRITICAL = 30.0
    HEALTH_DEGRADED = 60.0
    HEALTH_HEALTHY = 70.0

    @staticmethod
    def calculate_risk_score(
        contact_rate: float,
        high_severity_report_count: int,
        days_since_last_contact: int,
    ) -> float:
        """
        Calculate booth risk score (0-100).

        Risk components:
        - Contact deficit: (1 - contact_rate/100) × 30 (up to 30 pts)
        - Recent field issues: high_severity_reports × 5 (up to 50 pts)
        - Staleness: days_since_last_contact × 0.5 (up to 20 pts)

        Args:
            contact_rate: Voter contact percentage (0-100)
            high_severity_report_count: Count of recent high-severity field reports
            days_since_last_contact: Days since last voter contact

        Returns:
            float: Risk score clamped to [0, 100]
        """
        # Clamp contact_rate to valid range
        contact_rate = max(0.0, min(100.0, contact_rate))

        # Component 1: Contact deficit (30 pts max)
        contact_deficit = (1.0 - contact_rate / 100.0) * 30.0

        # Component 2: Field reports (50 pts max, 5 pts per report)
        report_penalty = min(50.0, high_severity_report_count * 5.0)

        # Component 3: Staleness (20 pts max, 0.5 pts per day)
        staleness_penalty = min(20.0, max(0, days_since_last_contact) * 0.5)

        # Total risk score
        risk_score = contact_deficit + report_penalty + staleness_penalty

        # Clamp to [0, 100]
        return max(0.0, min(100.0, risk_score))

    @staticmethod
    def calculate_health_score(
        contact_rate: float,
        volunteer_coverage: float,
        report_frequency: float,
    ) -> float:
        """
        Calculate booth health score (0-100).

        Health components:
        - Voter engagement: contact_rate × 0.4 (40 pts)
        - Volunteer coverage: (volunteer_coverage/100) × 30 (30 pts)
        - Activity: report_frequency × 0.3 (30 pts)

        Args:
            contact_rate: Voter contact percentage (0-100)
            volunteer_coverage: Volunteer coverage percentage (0-100)
            report_frequency: Reports per week or similar frequency metric

        Returns:
            float: Health score clamped to [0, 100]
        """
        # Clamp inputs to valid ranges
        contact_rate = max(0.0, min(100.0, contact_rate))
        volunteer_coverage = max(0.0, min(100.0, volunteer_coverage))
        report_frequency = max(0.0, report_frequency)

        # Component 1: Voter engagement (40 pts)
        engagement_score = (contact_rate / 100.0) * 40.0

        # Component 2: Volunteer coverage (30 pts)
        coverage_score = (volunteer_coverage / 100.0) * 30.0

        # Component 3: Activity frequency (30 pts, capped at ~3 reports/week)
        activity_score = min(30.0, report_frequency * 0.3)

        # Total health score
        health_score = engagement_score + coverage_score + activity_score

        # Clamp to [0, 100]
        return max(0.0, min(100.0, health_score))

    @staticmethod
    def is_swing_booth(
        historical_margin: Optional[float],
        manually_marked: bool = False,
    ) -> bool:
        """
        Determine if booth is a swing booth.

        Swing booths have:
        - Historical margin < 5%, OR
        - Manually marked as swing booth

        Args:
            historical_margin: Historical election margin (%)
            manually_marked: Manually marked as swing booth

        Returns:
            bool: True if booth is swing, False otherwise
        """
        if manually_marked:
            return True

        if historical_margin is None:
            return False

        # Swing if margin < 5%
        return abs(historical_margin) < 5.0

    @staticmethod
    def get_risk_level(risk_score: float) -> str:
        """
        Classify risk score into level.

        Args:
            risk_score: Risk score (0-100)

        Returns:
            str: Risk level ("HIGH", "MEDIUM", or "LOW")
        """
        if risk_score >= RiskCalculator.RISK_HIGH:
            return "HIGH"
        elif risk_score >= RiskCalculator.RISK_MEDIUM:
            return "MEDIUM"
        else:
            return "LOW"

    @staticmethod
    def get_health_status(health_score: float) -> str:
        """
        Classify health score into status.

        Args:
            health_score: Health score (0-100)

        Returns:
            str: Health status ("CRITICAL", "DEGRADED", or "HEALTHY")
        """
        if health_score <= RiskCalculator.HEALTH_CRITICAL:
            return "CRITICAL"
        elif health_score < RiskCalculator.HEALTH_DEGRADED:
            return "DEGRADED"
        else:
            return "HEALTHY"

    @staticmethod
    def calculate_days_since_contact(last_contact_at: Optional[datetime]) -> int:
        """
        Calculate days since last voter contact.

        Args:
            last_contact_at: Last contact timestamp

        Returns:
            int: Days since contact (0 if contacted today, high number if never contacted)
        """
        if last_contact_at is None:
            # Never contacted - return high penalty value
            return 90  # Assume 90 days ago

        now = datetime.utcnow()
        time_diff = now - last_contact_at
        return max(0, time_diff.days)

    @staticmethod
    def estimate_volunteer_coverage(
        volunteer_count: int,
        total_voters: int,
    ) -> float:
        """
        Estimate volunteer coverage percentage.

        Target: 1 volunteer per 100 voters.

        Args:
            volunteer_count: Number of volunteers assigned
            total_voters: Total voters in booth

        Returns:
            float: Coverage percentage (0-100+), clamped to 100
        """
        if total_voters == 0:
            return 100.0  # Edge case: no voters = 100% coverage

        target_volunteers = total_voters / 100.0
        coverage = (volunteer_count / target_volunteers) * 100.0

        return min(100.0, coverage)  # Cap at 100%

    @staticmethod
    def estimate_report_frequency(
        report_count: int,
        days_window: int = 7,
    ) -> float:
        """
        Estimate report frequency (reports per day in window).

        Args:
            report_count: Number of reports in window
            days_window: Window size in days

        Returns:
            float: Reports per day
        """
        if days_window == 0:
            return 0.0

        return report_count / days_window
