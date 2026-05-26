"""
Integration Tests for Booth Management — runs against PostgreSQL.
"""

import os
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.database_design.models import Booth, BoothVolunteer, Constituency, CampaignZone, User
from app.booth_management.service import BoothService
from app.booth_management.volunteer_service import VolunteerService
from app.booth_management.risk_calculator import RiskCalculator
from app.booth_management.exceptions import BoothNotFound, VolunteerNotFound


_PG_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://netaai_app:netaai_password@postgres:5432/netaai_prod",
)


class _SessionContext:
    def __init__(self, conn):
        self._conn = conn
        self.session = None

    async def __aenter__(self):
        self.session = AsyncSession(
            bind=self._conn,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        return self.session

    async def __aexit__(self, *args):
        await self.session.close()


class _SessionFactory:
    def __init__(self, conn):
        self._conn = conn

    def __call__(self):
        return _SessionContext(self._conn)


@pytest.fixture
async def test_db():
    """PostgreSQL test database with transaction rollback."""
    engine = create_async_engine(_PG_URL, echo=False)

    async with engine.connect() as conn:
        await conn.begin()

        setup = AsyncSession(
            bind=conn,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )

        constituency = Constituency(
            id=uuid4(),
            name="Test Constituency",
            state="Telangana",
            ac_number=f"T{uuid4().hex[:6]}",
            total_booths=100,
            total_voters=450000,
        )
        setup.add(constituency)

        zone = CampaignZone(
            id=uuid4(),
            constituency_id=constituency.id,
            zone_name="West Zone",
            zone_code=f"WZ{uuid4().hex[:4]}",
        )
        setup.add(zone)

        user = User(
            id=uuid4(),
            full_name="Test Commander",
            email=f"cmd_{uuid4().hex[:8]}@bm-test.local",
            phone="+919876543210",
            password_hash="hash",
            role="ground_commander",
            is_active=True,
        )
        setup.add(user)

        booth = Booth(
            id=uuid4(),
            constituency_id=constituency.id,
            zone_id=zone.id,
            booth_number=f"B{uuid4().hex[:4]}",
            booth_name="Test Booth",
            address="123 Test Street",
            total_voters=1000,
            female_voters=500,
            male_voters=500,
            swing_booth=False,
            historical_margin=8.5,
        )
        setup.add(booth)

        await setup.commit()
        await setup.close()

        yield _SessionFactory(conn)

        await conn.rollback()

    await engine.dispose()


# ============================================================================
# Booth Service Integration Tests
# ============================================================================

class TestBoothServiceIntegration:
    """Integration tests for BoothService."""

    @pytest.mark.asyncio
    async def test_list_booths_empty(self, test_db):
        """Test listing booths from database."""
        async with test_db() as db:
            service = BoothService()
            response = await service.list_booths(db)

            assert response.total >= 1
            assert len(response.booths) >= 1

    @pytest.mark.asyncio
    async def test_get_booth_by_id(self, test_db):
        """Test retrieving a specific booth."""
        async with test_db() as db:
            service = BoothService()

            response = await service.list_booths(db, limit=1)
            booth_id = response.booths[0].id

            booth = await service.get_booth(db, booth_id)
            assert booth.id == booth_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_booth_raises_error(self, test_db):
        """Test retrieving non-existent booth raises BoothNotFound."""
        async with test_db() as db:
            service = BoothService()

            with pytest.raises(BoothNotFound):
                await service.get_booth(db, uuid4())

    @pytest.mark.asyncio
    async def test_update_booth_contact_rate(self, test_db):
        """Test updating booth contact rate."""
        async with test_db() as db:
            service = BoothService()

            response = await service.list_booths(db, limit=1)
            booth_id = response.booths[0].id

            updated = await service.update_booth(
                db,
                booth_id,
                contact_rate=75.5,
            )

            assert updated.contact_rate == 75.5

    @pytest.mark.asyncio
    async def test_booth_risk_score_recalculation(self, test_db):
        """Test risk score recomputation."""
        async with test_db() as db:
            service = BoothService()

            response = await service.list_booths(db, limit=1)
            booth_id = response.booths[0].id

            updated = await service.recompute_booth_scores(db, booth_id)

            assert 0.0 <= updated.risk_score <= 100.0
            assert 0.0 <= updated.health_score <= 100.0

    @pytest.mark.asyncio
    async def test_get_risk_report_for_constituency(self, test_db):
        """Test generating risk report for constituency."""
        async with test_db() as db:
            service = BoothService()

            all_booths = await service.list_booths(db, limit=1)
            constituency_id = all_booths.booths[0].constituency_id

            report = await service.get_risk_report(db, constituency_id)

            assert report.constituency_id == constituency_id
            assert isinstance(report.high_risk_booths, list)
            assert isinstance(report.swing_booths, list)
            assert isinstance(report.under_resourced, list)
            assert isinstance(report.recommended_interventions, list)

    @pytest.mark.asyncio
    async def test_get_health_dashboard(self, test_db):
        """Test health dashboard generation."""
        async with test_db() as db:
            service = BoothService()

            all_booths = await service.list_booths(db, limit=1)
            constituency_id = all_booths.booths[0].constituency_id

            dashboard = await service.get_health_dashboard(db, constituency_id)

            assert dashboard.constituency_id == constituency_id
            assert dashboard.total_booths >= 1
            assert dashboard.healthy + dashboard.degraded + dashboard.critical == dashboard.total_booths


# ============================================================================
# Volunteer Service Integration Tests
# ============================================================================

class TestVolunteerServiceIntegration:
    """Integration tests for VolunteerService."""

    @pytest.mark.asyncio
    async def test_add_volunteer_to_booth(self, test_db):
        """Test adding a volunteer to a booth."""
        async with test_db() as db:
            service = VolunteerService()
            booth_service = BoothService()
            booths = await booth_service.list_booths(db, limit=1)
            booth_id = booths.booths[0].id

            volunteer = await service.add_volunteer(
                db,
                booth_id,
                volunteer_name="John Doe",
                phone="9876543210",
                role="BOOTH_AGENT",
            )

            assert volunteer.volunteer_name == "John Doe"
            assert volunteer.role == "BOOTH_AGENT"
            assert volunteer.is_confirmed == False

    @pytest.mark.asyncio
    async def test_add_volunteer_invalid_role_raises_error(self, test_db):
        """Test adding volunteer with invalid role raises error."""
        async with test_db() as db:
            service = VolunteerService()
            booth_service = BoothService()
            booths = await booth_service.list_booths(db, limit=1)
            booth_id = booths.booths[0].id

            from app.booth_management.exceptions import InvalidVolunteerRole
            with pytest.raises(InvalidVolunteerRole):
                await service.add_volunteer(
                    db,
                    booth_id,
                    volunteer_name="Jane Doe",
                    phone="9876543210",
                    role="INVALID_ROLE",
                )

    @pytest.mark.asyncio
    async def test_list_booth_volunteers(self, test_db):
        """Test listing volunteers for a booth."""
        async with test_db() as db:
            volunteer_service = VolunteerService()
            booth_service = BoothService()

            booths = await booth_service.list_booths(db, limit=1)
            booth_id = booths.booths[0].id

            for i in range(3):
                await volunteer_service.add_volunteer(
                    db,
                    booth_id,
                    volunteer_name=f"Volunteer {i+1}",
                    phone=f"987654321{i}",
                    role=["BOOTH_AGENT", "VOTER_CONTACT", "TRANSPORT"][i],
                )

            volunteers = await volunteer_service.list_volunteers(db, booth_id)
            assert len(volunteers) == 3

    @pytest.mark.asyncio
    async def test_update_volunteer_confirmation(self, test_db):
        """Test confirming a volunteer."""
        async with test_db() as db:
            volunteer_service = VolunteerService()
            booth_service = BoothService()

            booths = await booth_service.list_booths(db, limit=1)
            booth_id = booths.booths[0].id

            volunteer = await volunteer_service.add_volunteer(
                db,
                booth_id,
                volunteer_name="Test Volunteer",
                phone="9876543210",
                role="BOOTH_AGENT",
            )

            updated = await volunteer_service.update_volunteer(
                db,
                volunteer.id,
                is_confirmed=True,
            )

            assert updated.is_confirmed == True

    @pytest.mark.asyncio
    async def test_remove_volunteer(self, test_db):
        """Test removing a volunteer."""
        async with test_db() as db:
            volunteer_service = VolunteerService()
            booth_service = BoothService()

            booths = await booth_service.list_booths(db, limit=1)
            booth_id = booths.booths[0].id

            volunteer = await volunteer_service.add_volunteer(
                db,
                booth_id,
                volunteer_name="Test Volunteer",
                phone="9876543210",
                role="BOOTH_AGENT",
            )

            await volunteer_service.remove_volunteer(db, volunteer.id)

            with pytest.raises(VolunteerNotFound):
                await volunteer_service.remove_volunteer(db, volunteer.id)

    @pytest.mark.asyncio
    async def test_get_booth_coverage(self, test_db):
        """Test getting booth volunteer coverage."""
        async with test_db() as db:
            volunteer_service = VolunteerService()
            booth_service = BoothService()

            booths = await booth_service.list_booths(db, limit=1)
            booth_id = booths.booths[0].id

            for i in range(5):
                await volunteer_service.add_volunteer(
                    db,
                    booth_id,
                    volunteer_name=f"Volunteer {i+1}",
                    phone=f"987654321{i}",
                    role="BOOTH_AGENT",
                )

            coverage = await volunteer_service.get_booth_coverage(db, booth_id)

            assert coverage.total_volunteers == 5
            assert "BOOTH_AGENT" in coverage.by_role
            assert coverage.by_role["BOOTH_AGENT"] == 5
            assert coverage.coverage_status in ["FULL", "PARTIAL", "MINIMAL"]


# ============================================================================
# Booth Management Workflow Tests
# ============================================================================

class TestBoothManagementWorkflow:
    """End-to-end workflow tests."""

    @pytest.mark.asyncio
    async def test_complete_booth_setup_workflow(self, test_db):
        """Test complete booth setup workflow."""
        async with test_db() as db:
            booth_service = BoothService()
            volunteer_service = VolunteerService()

            booths = await booth_service.list_booths(db, limit=1)
            booth_id = booths.booths[0].id

            updated = await booth_service.update_booth(db, booth_id, contact_rate=60.0)
            assert updated.contact_rate == 60.0

            for i in range(4):
                await volunteer_service.add_volunteer(
                    db,
                    booth_id,
                    volunteer_name=f"Volunteer {i+1}",
                    phone=f"987654321{i}",
                    role=["BOOTH_AGENT", "VOTER_CONTACT", "TRANSPORT", "COORDINATOR"][i],
                )

            updated = await booth_service.recompute_booth_scores(db, booth_id)
            assert 0.0 <= updated.risk_score <= 100.0
            assert 0.0 <= updated.health_score <= 100.0

            coverage = await volunteer_service.get_booth_coverage(db, booth_id)
            assert coverage.total_volunteers == 4
            assert coverage.coverage_percentage > 0

    @pytest.mark.asyncio
    async def test_risk_assessment_workflow(self, test_db):
        """Test risk assessment workflow."""
        async with test_db() as db:
            booth_service = BoothService()

            booths = await booth_service.list_booths(db, limit=1)
            booth_id = booths.booths[0].id
            constituency_id = booths.booths[0].constituency_id

            await booth_service.update_booth(db, booth_id, contact_rate=10.0)
            await booth_service.recompute_booth_scores(db, booth_id)

            report = await booth_service.get_risk_report(db, constituency_id)

            assert len(report.recommended_interventions) > 0


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling in booth management."""

    @pytest.mark.asyncio
    async def test_update_nonexistent_booth(self, test_db):
        """Test updating non-existent booth raises error."""
        async with test_db() as db:
            service = BoothService()

            with pytest.raises(BoothNotFound):
                await service.update_booth(db, uuid4(), contact_rate=50.0)

    @pytest.mark.asyncio
    async def test_add_volunteer_nonexistent_booth(self, test_db):
        """Test adding volunteer to non-existent booth raises error."""
        async with test_db() as db:
            service = VolunteerService()

            with pytest.raises(BoothNotFound):
                await service.add_volunteer(
                    db,
                    uuid4(),
                    volunteer_name="Test",
                    phone="1234567890",
                    role="BOOTH_AGENT",
                )
