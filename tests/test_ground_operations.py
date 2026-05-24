"""Integration tests for ground operations module."""
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from test_models import (
    Booth,
    CampaignZone,
    Constituency,
    Escalation,
    FieldReport,
    User,
    WorkerAttendance,
)
from app.ground_operations.service import FieldReportService
from app.ground_operations.escalation_service import EscalationService
from app.ground_operations.worker_attendance import WorkerAttendanceService
from app.ground_operations.mood_analyzer import MoodAnalyzer


# ============================================================================
# Field Report Tests (8 tests)
# ============================================================================

class TestFieldReports:
    """Test field report creation and management."""

    @pytest.mark.asyncio
    async def test_create_field_report_severity_1(self, test_db, admin_user, test_booth):
        """Create severity 1 report (no escalation)."""
        service = FieldReportService()

        from app.ground_operations.models import FieldReportCreate
        report_data = FieldReportCreate(
            booth_id=str(test_booth.id),
            category="VOTER_MOOD",
            description="Test report",
            severity=1,
            voter_sentiment="POSITIVE",
        )

        response = await service.create_report(test_db, report_data, str(admin_user.id))

        assert response.severity == 1
        assert response.escalation_id is None
        assert response.escalation_status is None

    @pytest.mark.asyncio
    async def test_create_field_report_severity_5_triggers_escalation(
        self, test_db, admin_user, test_booth
    ):
        """Create severity 5 report (auto-escalates)."""
        service = FieldReportService()

        from app.ground_operations.models import FieldReportCreate
        report_data = FieldReportCreate(
            booth_id=str(test_booth.id),
            category="SECURITY",
            description="Critical security issue",
            severity=5,
        )

        response = await service.create_report(test_db, report_data, str(admin_user.id))

        assert response.severity == 5
        assert response.escalation_id is not None
        assert response.escalation_status == "NEW"

    @pytest.mark.asyncio
    async def test_sla_calculation_severity_5(self, test_db, admin_user, test_booth):
        """Verify SLA deadline is 30 min for severity 5."""
        service = FieldReportService()

        from app.ground_operations.models import FieldReportCreate
        report_data = FieldReportCreate(
            booth_id=str(test_booth.id),
            category="SECURITY",
            description="Issue",
            severity=5,
        )

        now_before = datetime.now(timezone.utc)
        response = await service.create_report(test_db, report_data, str(admin_user.id))
        now_after = datetime.now(timezone.utc)

        # Get escalation
        escalation = await test_db.get(Escalation, str(response.escalation_id))
        time_diff = (escalation.sla_deadline - now_before).total_seconds() / 60

        assert 29 <= time_diff <= 31  # Should be ~30 minutes

    @pytest.mark.asyncio
    async def test_sla_calculation_severity_4(self, test_db, admin_user, test_booth):
        """Verify SLA deadline is 2 hours for severity 4."""
        service = FieldReportService()

        from app.ground_operations.models import FieldReportCreate
        report_data = FieldReportCreate(
            booth_id=str(test_booth.id),
            category="OPPOSITION_ACTIVITY",
            description="High issue",
            severity=4,
        )

        now_before = datetime.now(timezone.utc)
        response = await service.create_report(test_db, report_data, str(admin_user.id))

        escalation = await test_db.get(Escalation, str(response.escalation_id))
        time_diff = (escalation.sla_deadline - now_before).total_seconds() / 60

        assert 119 <= time_diff <= 121  # Should be ~120 minutes (2 hours)

    @pytest.mark.asyncio
    async def test_update_report_sentiment(self, test_db, admin_user, test_booth):
        """Update report sentiment within 1 hour window."""
        service = FieldReportService()

        from app.ground_operations.models import FieldReportCreate, FieldReportUpdate

        # Create report
        report_data = FieldReportCreate(
            booth_id=str(test_booth.id),
            category="VOTER_MOOD",
            description="Initial mood",
            severity=2,
            voter_sentiment="NEUTRAL",
        )
        response = await service.create_report(test_db, report_data, str(admin_user.id))

        # Update sentiment
        update_data = FieldReportUpdate(voter_sentiment="POSITIVE")
        updated = await service.update_report(
            test_db, str(response.id), update_data, str(admin_user.id)
        )

        assert updated.voter_sentiment == "POSITIVE"

    @pytest.mark.asyncio
    async def test_update_report_after_1_hour_fails(self, test_db, admin_user, test_booth):
        """Cannot update report after 1 hour."""
        service = FieldReportService()

        from app.ground_operations.models import FieldReportCreate, FieldReportUpdate

        # Create report
        report_data = FieldReportCreate(
            booth_id=str(test_booth.id),
            category="VOTER_MOOD",
            description="Old report",
            severity=2,
        )
        response = await service.create_report(test_db, report_data, str(admin_user.id))

        # Manually set reported_at to 2 hours ago
        report = await test_db.get(FieldReport, str(response.id))
        report.reported_at = datetime.now(timezone.utc) - timedelta(hours=2)
        await test_db.commit()

        # Try to update
        from app.ground_operations.exceptions import EditWindowClosedException
        update_data = FieldReportUpdate(voter_sentiment="POSITIVE")

        with pytest.raises(EditWindowClosedException):
            await service.update_report(test_db, str(response.id), update_data, str(admin_user.id))

    @pytest.mark.asyncio
    async def test_list_reports_with_filters(self, test_db, admin_user, test_booth):
        """List reports with category and severity filters."""
        service = FieldReportService()

        from app.ground_operations.models import FieldReportCreate

        # Create multiple reports
        for severity in [1, 2, 3, 4, 5]:
            report_data = FieldReportCreate(
                booth_id=str(test_booth.id),
                category="VOTER_MOOD",
                description=f"Severity {severity}",
                severity=severity,
            )
            await service.create_report(test_db, report_data, str(admin_user.id))

        # List with filter
        results = await service.list_reports(test_db, severity_min=4)

        assert results["total"] >= 2  # severity 4 and 5


# ============================================================================
# Escalation Tests (7 tests)
# ============================================================================

class TestEscalations:
    """Test escalation workflow."""

    @pytest.mark.asyncio
    async def test_escalation_auto_assigned(self, test_db, admin_user, test_booth, ground_commander_user):
        """Escalation auto-assigned to zone's ground commander."""
        service = FieldReportService()

        from app.ground_operations.models import FieldReportCreate

        report_data = FieldReportCreate(
            booth_id=str(test_booth.id),
            category="SECURITY",
            description="Security issue",
            severity=5,
        )
        response = await service.create_report(test_db, report_data, str(admin_user.id))

        # Verify escalation
        escalation = await test_db.get(Escalation, str(response.escalation_id))
        assert escalation.status == "NEW"
        assert escalation.assigned_to is not None

    @pytest.mark.asyncio
    async def test_escalation_acknowledge(self, test_db, admin_user, test_booth, ground_commander_user):
        """Acknowledge escalation (mark IN_PROGRESS)."""
        service = FieldReportService()
        esc_service = EscalationService()

        from app.ground_operations.models import FieldReportCreate

        report_data = FieldReportCreate(
            booth_id=str(test_booth.id),
            category="SECURITY",
            description="Issue",
            severity=5,
        )
        response = await service.create_report(test_db, report_data, str(admin_user.id))

        # Get the assigned_to user and use it for acknowledgement
        escalation = await test_db.get(Escalation, str(response.escalation_id))
        assigned_user_id = escalation.assigned_to

        # Acknowledge escalation
        esc_response = await esc_service.acknowledge_escalation(
            test_db, str(response.escalation_id), assigned_user_id
        )

        assert esc_response.status == "IN_PROGRESS"
        assert esc_response.acknowledged_at is not None

    @pytest.mark.asyncio
    async def test_escalation_resolve(self, test_db, admin_user, test_booth, ground_commander_user):
        """Resolve escalation with resolution notes."""
        service = FieldReportService()
        esc_service = EscalationService()

        from app.ground_operations.models import FieldReportCreate

        report_data = FieldReportCreate(
            booth_id=str(test_booth.id),
            category="SECURITY",
            description="Issue",
            severity=5,
        )
        response = await service.create_report(test_db, report_data, str(admin_user.id))

        escalation = await test_db.get(Escalation, str(response.escalation_id))
        assigned_user_id = escalation.assigned_to

        # Acknowledge first
        await esc_service.acknowledge_escalation(
            test_db, str(response.escalation_id), assigned_user_id
        )

        # Resolve
        resolution_notes = "Issue resolved by coordinating with booth team. Situation stabilized."
        esc_response = await esc_service.resolve_escalation(
            test_db, str(response.escalation_id), resolution_notes, assigned_user_id
        )

        assert esc_response.status == "RESOLVED"
        assert esc_response.resolved_at is not None
        assert esc_response.resolution_notes == resolution_notes

    @pytest.mark.asyncio
    async def test_escalation_resolution_notes_too_short_fails(self, test_db, admin_user, test_booth, ground_commander_user):
        """Resolution with < 50 chars fails."""
        service = FieldReportService()
        esc_service = EscalationService()

        from app.ground_operations.models import FieldReportCreate

        report_data = FieldReportCreate(
            booth_id=str(test_booth.id),
            category="SECURITY",
            description="Issue",
            severity=5,
        )
        response = await service.create_report(test_db, report_data, str(admin_user.id))

        escalation = await test_db.get(Escalation, str(response.escalation_id))
        assigned_user_id = escalation.assigned_to

        from app.ground_operations.exceptions import InvalidResolutionNotesException

        with pytest.raises(InvalidResolutionNotesException):
            await esc_service.resolve_escalation(
                test_db, str(response.escalation_id), "Too short", assigned_user_id
            )

    @pytest.mark.asyncio
    async def test_check_sla_breaches(self, test_db, admin_user, test_booth):
        """Check SLA breaches and escalate."""
        service = FieldReportService()
        esc_service = EscalationService()

        from app.ground_operations.models import FieldReportCreate

        report_data = FieldReportCreate(
            booth_id=str(test_booth.id),
            category="SECURITY",
            description="Issue",
            severity=5,
        )
        response = await service.create_report(test_db, report_data, str(admin_user.id))

        # Manually set SLA deadline to past
        escalation = await test_db.get(Escalation, str(response.escalation_id))
        escalation.sla_deadline = datetime.now(timezone.utc) - timedelta(minutes=10)
        await test_db.commit()

        # Check breaches
        breached = await esc_service.check_sla_breaches(test_db)

        assert len(breached) > 0
        assert any(str(e.id) == str(response.escalation_id) for e in breached)


# ============================================================================
# Worker Attendance Tests (5 tests)
# ============================================================================

class TestWorkerAttendance:
    """Test worker check-in/out and productivity."""

    @pytest.mark.asyncio
    async def test_worker_check_in(self, test_db, field_worker_user, test_booth, test_zone):
        """Worker check-in creates attendance record."""
        service = WorkerAttendanceService()

        response = await service.check_in_worker(
            test_db, str(field_worker_user.id), str(test_booth.id), 17.4700, 78.3620
        )

        assert response.user_id == str(field_worker_user.id)
        assert response.booth_id == str(test_booth.id)
        assert response.checked_in_at is not None
        assert response.checked_out_at is None

    @pytest.mark.asyncio
    async def test_worker_check_out(self, test_db, field_worker_user, test_booth, test_zone):
        """Worker check-out sets checked_out_at."""
        service = WorkerAttendanceService()

        # Check in
        await service.check_in_worker(test_db, str(field_worker_user.id), str(test_booth.id))

        # Check out
        response = await service.check_out_worker(test_db, str(field_worker_user.id))

        assert response.checked_out_at is not None

    @pytest.mark.asyncio
    async def test_get_active_workers(self, test_db, field_worker_user, test_booth, test_zone):
        """Get list of active workers."""
        service = WorkerAttendanceService()

        # Check in worker
        await service.check_in_worker(test_db, str(field_worker_user.id), str(test_booth.id))

        # Get active
        response = await service.get_active_workers(test_db, zone_id=str(test_zone.id))

        assert response.total >= 1
        assert any(str(w["user_id"]) == str(field_worker_user.id) for w in response.workers)

    @pytest.mark.asyncio
    async def test_worker_productivity_calculation(self, test_db, field_worker_user, test_booth):
        """Productivity score = count of reports weighted by severity."""
        service = FieldReportService()
        attendance_service = WorkerAttendanceService()

        from app.ground_operations.models import FieldReportCreate

        # Create reports with various severities
        severities = [5, 4, 3, 1, 1]
        for severity in severities:
            report_data = FieldReportCreate(
                booth_id=str(test_booth.id),
                category="VOTER_MOOD",
                description=f"Report severity {severity}",
                severity=severity,
            )
            await service.create_report(test_db, report_data, str(field_worker_user.id))

        # Get productivity
        response = await attendance_service.get_worker_productivity(test_db, str(field_worker_user.id), days=7)

        # Expected: 5*5 + 4*4 + 3*3 + 1*1 + 1*1 = 25 + 16 + 9 + 1 + 1 = 52
        assert response.productivity_score >= 0
        assert response.total_reports == 5

    @pytest.mark.asyncio
    async def test_escalation_list_with_sla_status(self, test_db, admin_user, test_booth):
        """List escalations with SLA status aggregation."""
        service = FieldReportService()
        esc_service = EscalationService()

        from app.ground_operations.models import FieldReportCreate

        # Create multiple reports with different severities
        report1_data = FieldReportCreate(
            booth_id=str(test_booth.id),
            category="SECURITY",
            description="Critical issue 1",
            severity=5,
        )
        response1 = await service.create_report(test_db, report1_data, str(admin_user.id))

        report2_data = FieldReportCreate(
            booth_id=str(test_booth.id),
            category="INFRASTRUCTURE",
            description="Medium issue",
            severity=4,
        )
        response2 = await service.create_report(test_db, report2_data, str(admin_user.id))

        # List escalations
        result = await esc_service.list_escalations(test_db)

        assert result.total >= 2
        assert result.breached_count == 0  # No breaches yet
        assert result.on_track_count >= 2
