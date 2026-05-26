"""
Integration Tests for Booth Management — runs against PostgreSQL.

Uses pg_session / pg_test_booth fixtures from conftest.py (real PostgreSQL
with savepoint-based transaction rollback so every test leaves no data behind).
"""

import pytest
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.database_design.models import Booth, BoothVolunteer, User
from app.booth_management.service import BoothService
from app.booth_management.volunteer_service import VolunteerService
from app.booth_management.exceptions import BoothNotFound, VolunteerNotFound


# ============================================================================
# Booth Service Integration Tests
# ============================================================================

class TestBoothServiceIntegration:
    """Integration tests for BoothService against PostgreSQL."""

    @pytest.mark.asyncio
    async def test_list_booths_returns_seeded_booth(self, pg_session, pg_test_booth):
        """List booths returns at least the seeded booth."""
        service = BoothService()
        response = await service.list_booths(pg_session)

        assert response.total >= 1
        booth_ids = [b.id for b in response.booths]
        assert pg_test_booth.id in booth_ids

    @pytest.mark.asyncio
    async def test_get_booth_by_id(self, pg_session, pg_test_booth):
        """Retrieve a specific booth by ID."""
        service = BoothService()
        booth = await service.get_booth(pg_session, pg_test_booth.id)

        assert booth.id == pg_test_booth.id
        assert booth.booth_number == pg_test_booth.booth_number

    @pytest.mark.asyncio
    async def test_get_nonexistent_booth_raises_error(self, pg_session):
        """Retrieving a non-existent booth raises BoothNotFound."""
        service = BoothService()

        with pytest.raises(BoothNotFound):
            await service.get_booth(pg_session, uuid4())

    @pytest.mark.asyncio
    async def test_update_booth_contact_rate(self, pg_session, pg_test_booth):
        """Update booth contact rate persists correctly."""
        service = BoothService()

        updated = await service.update_booth(
            pg_session,
            pg_test_booth.id,
            contact_rate=75.5,
        )

        assert updated.contact_rate == 75.5

    @pytest.mark.asyncio
    async def test_update_nonexistent_booth_raises_error(self, pg_session):
        """Updating a non-existent booth raises BoothNotFound."""
        service = BoothService()

        with pytest.raises(BoothNotFound):
            await service.update_booth(pg_session, uuid4(), contact_rate=50.0)

    @pytest.mark.asyncio
    async def test_booth_risk_score_recalculation(self, pg_session, pg_test_booth):
        """Recompute scores returns values in [0, 100]."""
        service = BoothService()

        updated = await service.recompute_booth_scores(pg_session, pg_test_booth.id)

        assert 0.0 <= updated.risk_score <= 100.0
        assert 0.0 <= updated.health_score <= 100.0

    @pytest.mark.asyncio
    async def test_get_risk_report_for_constituency(self, pg_session, pg_test_booth, pg_test_constituency):
        """Risk report contains correct structure for a constituency."""
        service = BoothService()

        report = await service.get_risk_report(pg_session, pg_test_constituency.id)

        assert report.constituency_id == pg_test_constituency.id
        assert isinstance(report.high_risk_booths, list)
        assert isinstance(report.swing_booths, list)
        assert isinstance(report.under_resourced, list)
        assert isinstance(report.recommended_interventions, list)
        assert "total_booths" in report.summary

    @pytest.mark.asyncio
    async def test_get_health_dashboard(self, pg_session, pg_test_booth, pg_test_constituency):
        """Health dashboard counts sum to total_booths."""
        service = BoothService()

        dashboard = await service.get_health_dashboard(pg_session, pg_test_constituency.id)

        assert dashboard.constituency_id == pg_test_constituency.id
        assert dashboard.total_booths >= 1
        assert dashboard.healthy + dashboard.degraded + dashboard.critical == dashboard.total_booths

    @pytest.mark.asyncio
    async def test_list_booths_filter_by_constituency(self, pg_session, pg_test_booth, pg_test_constituency):
        """Filtering by constituency_id returns only that constituency's booths."""
        service = BoothService()

        response = await service.list_booths(pg_session, constituency_id=pg_test_constituency.id)

        assert response.total >= 1
        for booth in response.booths:
            assert booth.constituency_id == pg_test_constituency.id

    @pytest.mark.asyncio
    async def test_list_booths_aggregations_present(self, pg_session, pg_test_booth):
        """List response includes by_risk_level and by_health_status aggregations."""
        service = BoothService()

        response = await service.list_booths(pg_session)

        assert "high" in response.by_risk_level
        assert "medium" in response.by_risk_level
        assert "low" in response.by_risk_level
        assert "healthy" in response.by_health_status
        assert "degraded" in response.by_health_status
        assert "critical" in response.by_health_status


# ============================================================================
# Volunteer Service Integration Tests
# ============================================================================

class TestVolunteerServiceIntegration:
    """Integration tests for VolunteerService against PostgreSQL."""

    @pytest.mark.asyncio
    async def test_add_volunteer_to_booth(self, pg_session, pg_test_booth):
        """Add a volunteer and verify it is returned correctly."""
        service = VolunteerService()

        volunteer = await service.add_volunteer(
            pg_session,
            pg_test_booth.id,
            volunteer_name="John Doe",
            phone="9876543210",
            role="BOOTH_AGENT",
        )

        assert volunteer.volunteer_name == "John Doe"
        assert volunteer.role == "BOOTH_AGENT"
        assert volunteer.is_confirmed is False
        assert volunteer.booth_id == pg_test_booth.id

    @pytest.mark.asyncio
    async def test_add_volunteer_invalid_role_raises_error(self, pg_session, pg_test_booth):
        """Adding a volunteer with an invalid role raises InvalidVolunteerRole."""
        service = VolunteerService()

        from app.booth_management.exceptions import InvalidVolunteerRole
        with pytest.raises(InvalidVolunteerRole):
            await service.add_volunteer(
                pg_session,
                pg_test_booth.id,
                volunteer_name="Jane Doe",
                phone="9876543210",
                role="INVALID_ROLE",
            )

    @pytest.mark.asyncio
    async def test_add_volunteer_nonexistent_booth_raises_error(self, pg_session):
        """Adding a volunteer to a non-existent booth raises BoothNotFound."""
        service = VolunteerService()

        with pytest.raises(BoothNotFound):
            await service.add_volunteer(
                pg_session,
                uuid4(),
                volunteer_name="Test",
                phone="1234567890",
                role="BOOTH_AGENT",
            )

    @pytest.mark.asyncio
    async def test_list_booth_volunteers(self, pg_session, pg_test_booth):
        """List volunteers returns all added volunteers for a booth."""
        service = VolunteerService()

        for i in range(3):
            await service.add_volunteer(
                pg_session,
                pg_test_booth.id,
                volunteer_name=f"Volunteer {i + 1}",
                phone=f"987654321{i}",
                role=["BOOTH_AGENT", "VOTER_CONTACT", "TRANSPORT"][i],
            )

        volunteers = await service.list_volunteers(pg_session, pg_test_booth.id)
        assert len(volunteers) >= 3

    @pytest.mark.asyncio
    async def test_update_volunteer_confirmation(self, pg_session, pg_test_booth):
        """Confirm a volunteer and verify is_confirmed becomes True."""
        service = VolunteerService()

        volunteer = await service.add_volunteer(
            pg_session,
            pg_test_booth.id,
            volunteer_name="Test Volunteer",
            phone="9876543210",
            role="BOOTH_AGENT",
        )

        updated = await service.update_volunteer(
            pg_session,
            volunteer.id,
            is_confirmed=True,
        )

        assert updated.is_confirmed is True

    @pytest.mark.asyncio
    async def test_update_volunteer_role(self, pg_session, pg_test_booth):
        """Update volunteer role persists correctly."""
        service = VolunteerService()

        volunteer = await service.add_volunteer(
            pg_session,
            pg_test_booth.id,
            volunteer_name="Role Test",
            phone="9876543210",
            role="BOOTH_AGENT",
        )

        updated = await service.update_volunteer(
            pg_session,
            volunteer.id,
            role="COORDINATOR",
        )

        assert updated.role == "COORDINATOR"

    @pytest.mark.asyncio
    async def test_remove_volunteer(self, pg_session, pg_test_booth):
        """Remove a volunteer; subsequent removal raises VolunteerNotFound."""
        service = VolunteerService()

        volunteer = await service.add_volunteer(
            pg_session,
            pg_test_booth.id,
            volunteer_name="Removable Volunteer",
            phone="9876543210",
            role="BOOTH_AGENT",
        )

        await service.remove_volunteer(pg_session, volunteer.id)

        with pytest.raises(VolunteerNotFound):
            await service.remove_volunteer(pg_session, volunteer.id)

    @pytest.mark.asyncio
    async def test_get_booth_coverage(self, pg_session, pg_test_booth):
        """Coverage response reflects added volunteers correctly."""
        service = VolunteerService()

        for i in range(5):
            await service.add_volunteer(
                pg_session,
                pg_test_booth.id,
                volunteer_name=f"Coverage Volunteer {i + 1}",
                phone=f"987654321{i}",
                role="BOOTH_AGENT",
            )

        coverage = await service.get_booth_coverage(pg_session, pg_test_booth.id)

        assert coverage.total_volunteers >= 5
        assert "BOOTH_AGENT" in coverage.by_role
        assert coverage.coverage_status in ["FULL", "PARTIAL", "MINIMAL"]


# ============================================================================
# Workflow Integration Tests
# ============================================================================

class TestBoothManagementWorkflow:
    """End-to-end workflow tests for booth management."""

    @pytest.mark.asyncio
    async def test_complete_booth_setup_workflow(self, pg_session, pg_test_booth):
        """Full setup: update contact rate → add volunteers → recompute scores → check coverage."""
        booth_service = BoothService()
        volunteer_service = VolunteerService()

        updated = await booth_service.update_booth(pg_session, pg_test_booth.id, contact_rate=60.0)
        assert updated.contact_rate == 60.0

        for i, role in enumerate(["BOOTH_AGENT", "VOTER_CONTACT", "TRANSPORT", "COORDINATOR"]):
            await volunteer_service.add_volunteer(
                pg_session,
                pg_test_booth.id,
                volunteer_name=f"Setup Volunteer {i + 1}",
                phone=f"987654321{i}",
                role=role,
            )

        scored = await booth_service.recompute_booth_scores(pg_session, pg_test_booth.id)
        assert 0.0 <= scored.risk_score <= 100.0
        assert 0.0 <= scored.health_score <= 100.0

        coverage = await volunteer_service.get_booth_coverage(pg_session, pg_test_booth.id)
        assert coverage.total_volunteers >= 4
        assert coverage.coverage_percentage > 0

    @pytest.mark.asyncio
    async def test_risk_assessment_workflow(self, pg_session, pg_test_booth, pg_test_constituency):
        """Low contact rate booth appears in risk report with recommended interventions."""
        booth_service = BoothService()

        await booth_service.update_booth(pg_session, pg_test_booth.id, contact_rate=10.0)
        await booth_service.recompute_booth_scores(pg_session, pg_test_booth.id)

        report = await booth_service.get_risk_report(pg_session, pg_test_constituency.id)

        assert len(report.recommended_interventions) > 0

    @pytest.mark.asyncio
    async def test_volunteer_coverage_by_role_breakdown(self, pg_session, pg_test_booth):
        """Coverage breakdown tracks each role separately."""
        service = VolunteerService()

        await service.add_volunteer(pg_session, pg_test_booth.id,
                                    volunteer_name="Agent", phone="1111111111", role="BOOTH_AGENT")
        await service.add_volunteer(pg_session, pg_test_booth.id,
                                    volunteer_name="Contact", phone="2222222222", role="VOTER_CONTACT")

        role_stats = await service.get_coverage_by_role(pg_session, pg_test_booth.id)

        assert role_stats["BOOTH_AGENT"]["total"] >= 1
        assert role_stats["VOTER_CONTACT"]["total"] >= 1

    @pytest.mark.asyncio
    async def test_bulk_confirm_volunteers(self, pg_session, pg_test_booth):
        """Bulk confirm a list of volunteers."""
        service = VolunteerService()

        v1 = await service.add_volunteer(pg_session, pg_test_booth.id,
                                         volunteer_name="Bulk V1", phone="3333333331", role="BOOTH_AGENT")
        v2 = await service.add_volunteer(pg_session, pg_test_booth.id,
                                         volunteer_name="Bulk V2", phone="3333333332", role="TRANSPORT")

        confirmed_count = await service.confirm_multiple_volunteers(
            pg_session, [v1.id, v2.id]
        )

        assert confirmed_count == 2
