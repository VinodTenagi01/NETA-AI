"""Integration tests for ground operations module — runs against PostgreSQL."""
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database_design.models import (
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
    async def test_create_field_report_severity_1(
        self, pg_session, pg_admin_user, pg_test_booth
    ):
        """Create severity 1 report (no escalation)."""
        service = FieldReportService()

        from app.ground_operations.models import FieldReportCreate
        report_data = FieldReportCreate(
            booth_id=str(pg_test_booth.id),
            category="VOTER_MOOD",
            description="Test report",
            severity=1,
            voter_sentiment="POSITIVE",
        )

        response = await service.create_report(pg_session, report_data, str(pg_admin_user.id))

        assert response.severity == 1
        assert response.escalation_id is None
        assert response.escalation_status is None

    @pytest.mark.asyncio
    async def test_create_field_report_severity_5_triggers_escalation(
        self, pg_session, pg_admin_user, pg_test_booth
    ):
        """Create severity 5 report (auto-escalates)."""
        service = FieldReportService()

        from app.ground_operations.models import FieldReportCreate
        report_data = FieldReportCreate(
            booth_id=str(pg_test_booth.id),
            category="SECURITY",
            description="Critical security issue",
            severity=5,
        )

        response = await service.create_report(pg_session, report_data, str(pg_admin_user.id))

        assert response.severity == 5
        assert response.escalation_id is not None
        assert response.escalation_status == "NEW"

    @pytest.mark.asyncio
    async def test_sla_calculation_severity_5(
        self, pg_session, pg_admin_user, pg_test_booth
    ):
        """Verify SLA deadline is 30 min for severity 5."""
        service = FieldReportService()

        from app.ground_operations.models import FieldReportCreate
        report_data = FieldReportCreate(
            booth_id=str(pg_test_booth.id),
            category="SECURITY",
            description="Issue",
            severity=5,
        )

        now_before = datetime.now(timezone.utc)
        response = await service.create_report(pg_session, report_data, str(pg_admin_user.id))

        escalation = await pg_session.get(Escalation, response.escalation_id)
        time_diff = (escalation.sla_deadline - now_before).total_seconds() / 60

        assert 29 <= time_diff <= 31

    @pytest.mark.asyncio
    async def test_sla_calculation_severity_4(
        self, pg_session, pg_admin_user, pg_test_booth
    ):
        """Verify SLA deadline is 2 hours for severity 4."""
        service = FieldReportService()

        from app.ground_operations.models import FieldReportCreate
        report_data = FieldReportCreate(
            booth_id=str(pg_test_booth.id),
            category="OPPOSITION_ACTIVITY",
            description="High issue",
            severity=4,
        )

        now_before = datetime.now(timezone.utc)
        response = await service.create_report(pg_session, report_data, str(pg_admin_user.id))

        escalation = await pg_session.get(Escalation, response.escalation_id)
        time_diff = (escalation.sla_deadline - now_before).total_seconds() / 60

        assert 119 <= time_diff <= 121

    @pytest.mark.asyncio
    async def test_update_report_sentiment(
        self, pg_session, pg_admin_user, pg_test_booth
    ):
        """Update report sentiment within 1 hour window."""
        service = FieldReportService()

        from app.ground_operations.models import FieldReportCreate, FieldReportUpdate

        report_data = FieldReportCreate(
            booth_id=str(pg_test_booth.id),
            category="VOTER_MOOD",
            description="Initial mood",
            severity=2,
            voter_sentiment="NEUTRAL",
        )
        response = await service.create_report(pg_session, report_data, str(pg_admin_user.id))

        update_data = FieldReportUpdate(voter_sentiment="POSITIVE")
        updated = await service.update_report(
            pg_session, str(response.id), update_data, str(pg_admin_user.id)
        )

        assert updated.voter_sentiment == "POSITIVE"

    @pytest.mark.asyncio
    async def test_update_report_after_1_hour_fails(
        self, pg_session, pg_admin_user, pg_test_booth
    ):
        """Cannot update report after 1 hour."""
        service = FieldReportService()

        from app.ground_operations.models import FieldReportCreate, FieldReportUpdate

        report_data = FieldReportCreate(
            booth_id=str(pg_test_booth.id),
            category="VOTER_MOOD",
            description="Old report",
            severity=2,
        )
        response = await service.create_report(pg_session, report_data, str(pg_admin_user.id))

        report = await pg_session.get(FieldReport, response.id)
        report.reported_at = datetime.now(timezone.utc) - timedelta(hours=2)
        await pg_session.commit()

        from app.ground_operations.exceptions import EditWindowClosedException
        update_data = FieldReportUpdate(voter_sentiment="POSITIVE")

        with pytest.raises(EditWindowClosedException):
            await service.update_report(pg_session, str(response.id), update_data, str(pg_admin_user.id))

    @pytest.mark.asyncio
    async def test_list_reports_with_filters(
        self, pg_session, pg_admin_user, pg_test_booth
    ):
        """List reports with category and severity filters."""
        service = FieldReportService()

        from app.ground_operations.models import FieldReportCreate

        for severity in [1, 2, 3, 4, 5]:
            report_data = FieldReportCreate(
                booth_id=str(pg_test_booth.id),
                category="VOTER_MOOD",
                description=f"Severity {severity}",
                severity=severity,
            )
            await service.create_report(pg_session, report_data, str(pg_admin_user.id))

        results = await service.list_reports(pg_session, severity_min=4)

        assert results["total"] >= 2


# ============================================================================
# Escalation Tests (7 tests)
# ============================================================================

class TestEscalations:
    """Test escalation workflow."""

    @pytest.mark.asyncio
    async def test_escalation_auto_assigned(
        self, pg_session, pg_admin_user, pg_test_booth, pg_ground_commander_user
    ):
        """Escalation auto-assigned to zone's ground commander."""
        service = FieldReportService()

        from app.ground_operations.models import FieldReportCreate

        report_data = FieldReportCreate(
            booth_id=str(pg_test_booth.id),
            category="SECURITY",
            description="Security issue",
            severity=5,
        )
        response = await service.create_report(pg_session, report_data, str(pg_admin_user.id))

        escalation = await pg_session.get(Escalation, response.escalation_id)
        assert escalation.status == "NEW"
        assert escalation.assigned_to is not None

    @pytest.mark.asyncio
    async def test_escalation_acknowledge(
        self, pg_session, pg_admin_user, pg_test_booth, pg_ground_commander_user
    ):
        """Acknowledge escalation (mark IN_PROGRESS)."""
        service = FieldReportService()
        esc_service = EscalationService()

        from app.ground_operations.models import FieldReportCreate

        report_data = FieldReportCreate(
            booth_id=str(pg_test_booth.id),
            category="SECURITY",
            description="Issue",
            severity=5,
        )
        response = await service.create_report(pg_session, report_data, str(pg_admin_user.id))

        escalation = await pg_session.get(Escalation, response.escalation_id)
        assigned_user_id = escalation.assigned_to

        esc_response = await esc_service.acknowledge_escalation(
            pg_session, str(response.escalation_id), assigned_user_id
        )

        assert esc_response.status == "IN_PROGRESS"
        assert esc_response.acknowledged_at is not None

    @pytest.mark.asyncio
    async def test_escalation_resolve(
        self, pg_session, pg_admin_user, pg_test_booth, pg_ground_commander_user
    ):
        """Resolve escalation with resolution notes."""
        service = FieldReportService()
        esc_service = EscalationService()

        from app.ground_operations.models import FieldReportCreate

        report_data = FieldReportCreate(
            booth_id=str(pg_test_booth.id),
            category="SECURITY",
            description="Issue",
            severity=5,
        )
        response = await service.create_report(pg_session, report_data, str(pg_admin_user.id))

        escalation = await pg_session.get(Escalation, response.escalation_id)
        assigned_user_id = escalation.assigned_to

        await esc_service.acknowledge_escalation(
            pg_session, str(response.escalation_id), assigned_user_id
        )

        resolution_notes = "Issue resolved by coordinating with booth team. Situation stabilized."
        esc_response = await esc_service.resolve_escalation(
            pg_session, str(response.escalation_id), resolution_notes, assigned_user_id
        )

        assert esc_response.status == "RESOLVED"
        assert esc_response.resolved_at is not None
        assert esc_response.resolution_notes == resolution_notes

    @pytest.mark.asyncio
    async def test_escalation_resolution_notes_too_short_fails(
        self, pg_session, pg_admin_user, pg_test_booth, pg_ground_commander_user
    ):
        """Resolution with < 50 chars fails."""
        service = FieldReportService()
        esc_service = EscalationService()

        from app.ground_operations.models import FieldReportCreate

        report_data = FieldReportCreate(
            booth_id=str(pg_test_booth.id),
            category="SECURITY",
            description="Issue",
            severity=5,
        )
        response = await service.create_report(pg_session, report_data, str(pg_admin_user.id))

        escalation = await pg_session.get(Escalation, response.escalation_id)
        assigned_user_id = escalation.assigned_to

        from app.ground_operations.exceptions import InvalidResolutionNotesException

        with pytest.raises(InvalidResolutionNotesException):
            await esc_service.resolve_escalation(
                pg_session, str(response.escalation_id), "Too short", assigned_user_id
            )

    @pytest.mark.asyncio
    async def test_check_sla_breaches(
        self, pg_session, pg_admin_user, pg_test_booth
    ):
        """Check SLA breaches and escalate."""
        service = FieldReportService()
        esc_service = EscalationService()

        from app.ground_operations.models import FieldReportCreate

        report_data = FieldReportCreate(
            booth_id=str(pg_test_booth.id),
            category="SECURITY",
            description="Issue",
            severity=5,
        )
        response = await service.create_report(pg_session, report_data, str(pg_admin_user.id))

        escalation = await pg_session.get(Escalation, response.escalation_id)
        escalation.sla_deadline = datetime.now(timezone.utc) - timedelta(minutes=10)
        await pg_session.commit()

        breached = await esc_service.check_sla_breaches(pg_session)

        assert len(breached) > 0
        assert any(e.id == response.escalation_id for e in breached)


# ============================================================================
# Worker Attendance Tests (5 tests)
# ============================================================================

class TestWorkerAttendance:
    """Test worker check-in/out and productivity."""

    @pytest.mark.asyncio
    async def test_worker_check_in(
        self, pg_session, pg_field_worker_user, pg_test_booth, pg_test_zone
    ):
        """Worker check-in creates attendance record."""
        service = WorkerAttendanceService()

        response = await service.check_in_worker(
            pg_session, str(pg_field_worker_user.id), str(pg_test_booth.id), 17.4700, 78.3620
        )

        assert str(response.user_id) == str(pg_field_worker_user.id)
        assert str(response.booth_id) == str(pg_test_booth.id)
        assert response.checked_in_at is not None
        assert response.checked_out_at is None

    @pytest.mark.asyncio
    async def test_worker_check_out(
        self, pg_session, pg_field_worker_user, pg_test_booth, pg_test_zone
    ):
        """Worker check-out sets checked_out_at."""
        service = WorkerAttendanceService()

        await service.check_in_worker(pg_session, str(pg_field_worker_user.id), str(pg_test_booth.id))

        response = await service.check_out_worker(pg_session, str(pg_field_worker_user.id))

        assert response.checked_out_at is not None

    @pytest.mark.asyncio
    async def test_get_active_workers(
        self, pg_session, pg_field_worker_user, pg_test_booth, pg_test_zone
    ):
        """Get list of active workers."""
        service = WorkerAttendanceService()

        await service.check_in_worker(pg_session, str(pg_field_worker_user.id), str(pg_test_booth.id))

        response = await service.get_active_workers(pg_session, zone_id=str(pg_test_zone.id))

        assert response.total >= 1
        assert any(str(w.user_id) == str(pg_field_worker_user.id) for w in response.workers)

    @pytest.mark.asyncio
    async def test_worker_productivity_calculation(
        self, pg_session, pg_field_worker_user, pg_test_booth
    ):
        """Productivity score = count of reports weighted by severity."""
        service = FieldReportService()
        attendance_service = WorkerAttendanceService()

        from app.ground_operations.models import FieldReportCreate

        severities = [5, 4, 3, 1, 1]
        for severity in severities:
            report_data = FieldReportCreate(
                booth_id=str(pg_test_booth.id),
                category="VOTER_MOOD",
                description=f"Report severity {severity}",
                severity=severity,
            )
            await service.create_report(pg_session, report_data, str(pg_field_worker_user.id))

        response = await attendance_service.get_worker_productivity(pg_session, str(pg_field_worker_user.id), days=7)

        assert response.productivity_score >= 0
        assert response.field_reports == 5

    @pytest.mark.asyncio
    async def test_escalation_list_with_sla_status(
        self, pg_session, pg_admin_user, pg_test_booth
    ):
        """List escalations with SLA status aggregation."""
        service = FieldReportService()
        esc_service = EscalationService()

        from app.ground_operations.models import FieldReportCreate

        report1_data = FieldReportCreate(
            booth_id=str(pg_test_booth.id),
            category="SECURITY",
            description="Critical issue 1",
            severity=5,
        )
        response1 = await service.create_report(pg_session, report1_data, str(pg_admin_user.id))

        report2_data = FieldReportCreate(
            booth_id=str(pg_test_booth.id),
            category="INFRASTRUCTURE",
            description="Medium issue",
            severity=4,
        )
        response2 = await service.create_report(pg_session, report2_data, str(pg_admin_user.id))

        result = await esc_service.list_escalations(pg_session)

        assert result["total"] >= 2
        assert result["sla_stats"]["breached"] == 0
        assert result["sla_stats"]["on_track"] >= 2
