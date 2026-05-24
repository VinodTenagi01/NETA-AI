"""
Integration Tests for Booth Management

End-to-end tests of booth management workflows.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.database_design.database import Base
from app.database_design.models import Booth, BoothVolunteer, Constituency, CampaignZone, User
from app.booth_management.service import BoothService
from app.booth_management.volunteer_service import VolunteerService
from app.booth_management.risk_calculator import RiskCalculator
from app.booth_management.exceptions import BoothNotFound, VolunteerNotFound


# ============================================================================
# Test Database Setup
# ============================================================================

@pytest.fixture
async def test_db():
    """Create in-memory SQLite test database."""
    # Use SQLite for testing (simpler than PostgreSQL)
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create test data
    async with async_session() as session:
        # Create constituency
        constituency = Constituency(
            id=uuid4(),
            name="Serilingampally",
            state="Telangana",
            ac_number="AC-52",
            total_booths=100,
            total_voters=450000,
        )
        session.add(constituency)

        # Create zone
        zone = CampaignZone(
            id=uuid4(),
            constituency_id=constituency.id,
            zone_name="West Zone",
            zone_code="WZ-01",
        )
        session.add(zone)

        # Create test user
        user = User(
            id=uuid4(),
            full_name="Test Commander",
            email="commander@test.com",
            password_hash="hash",
            role="ground_commander",
        )
        session.add(user)

        # Create test booth
        booth = Booth(
            id=uuid4(),
            constituency_id=constituency.id,
            zone_id=zone.id,
            booth_number="001",
            booth_name="Test Booth",
            address="123 Test Street",
            total_voters=1000,
            female_voters=500,
            male_voters=500,
            swing_booth=False,
            historical_margin=8.5,
        )
        session.add(booth)

        await session.commit()

        # Store IDs for tests
        session.constituency_id = constituency.id
        session.zone_id = zone.id
        session.user_id = user.id
        session.booth_id = booth.id

    yield async_session
    await engine.dispose()


# ============================================================================
# Booth Service Integration Tests
# ============================================================================

class TestBoothServiceIntegration:
    """Integration tests for BoothService."""

    @pytest.mark.asyncio
    async def test_list_booths_empty(self, test_db):
        """Test listing booths when database is empty."""
        async with test_db() as db:
            service = BoothService()
            response = await service.list_booths(db)

            assert response.total == 1  # Test booth created in fixture
            assert len(response.booths) == 1

    @pytest.mark.asyncio
    async def test_get_booth_by_id(self, test_db):
        """Test retrieving a specific booth."""
        async with test_db() as db:
            service = BoothService()

            # Get test booth ID from fixture
            async with test_db() as setup_db:
                stmt = "SELECT id FROM booths LIMIT 1"
                # Can't execute raw SQL easily in async, so use alternate approach

            # Create and retrieve booth
            response = await service.list_booths(db, limit=1)
            booth_id = response.booths[0].id

            booth = await service.get_booth(db, booth_id)
            assert booth.id == booth_id
            assert booth.booth_number == "001"

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

            # Get booth ID
            response = await service.list_booths(db, limit=1)
            booth_id = response.booths[0].id

            # Update contact rate
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

            # Get booth
            response = await service.list_booths(db, limit=1)
            booth_id = response.booths[0].id

            # Recompute scores
            updated = await service.recompute_booth_scores(db, booth_id)

            # Booth with 0 contact rate should have moderate-high risk
            assert 20.0 <= updated.risk_score <= 40.0
            assert 0.0 <= updated.health_score <= 30.0

    @pytest.mark.asyncio
    async def test_get_risk_report_for_constituency(self, test_db):
        """Test generating risk report for constituency."""
        async with test_db() as db:
            service = BoothService()

            # Get constituency ID from setup
            all_booths = await service.list_booths(db, limit=1)
            constituency_id = all_booths.booths[0].constituency_id

            # Get risk report
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

            # Get constituency ID
            all_booths = await service.list_booths(db, limit=1)
            constituency_id = all_booths.booths[0].constituency_id

            # Get dashboard
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

            # Get booth ID
            booth_service = BoothService()
            booths = await booth_service.list_booths(db, limit=1)
            booth_id = booths.booths[0].id

            # Add volunteer
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

            # Get booth ID
            booth_service = BoothService()
            booths = await booth_service.list_booths(db, limit=1)
            booth_id = booths.booths[0].id

            # Try to add volunteer with invalid role
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

            # Get booth
            booths = await booth_service.list_booths(db, limit=1)
            booth_id = booths.booths[0].id

            # Add multiple volunteers
            for i in range(3):
                await volunteer_service.add_volunteer(
                    db,
                    booth_id,
                    volunteer_name=f"Volunteer {i+1}",
                    phone=f"987654321{i}",
                    role=["BOOTH_AGENT", "VOTER_CONTACT", "TRANSPORT"][i],
                )

            # List volunteers
            volunteers = await volunteer_service.list_volunteers(db, booth_id)
            assert len(volunteers) == 3

    @pytest.mark.asyncio
    async def test_update_volunteer_confirmation(self, test_db):
        """Test confirming a volunteer."""
        async with test_db() as db:
            volunteer_service = VolunteerService()
            booth_service = BoothService()

            # Add volunteer
            booths = await booth_service.list_booths(db, limit=1)
            booth_id = booths.booths[0].id

            volunteer = await volunteer_service.add_volunteer(
                db,
                booth_id,
                volunteer_name="Test Volunteer",
                phone="9876543210",
                role="BOOTH_AGENT",
            )

            # Confirm volunteer
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

            # Add volunteer
            booths = await booth_service.list_booths(db, limit=1)
            booth_id = booths.booths[0].id

            volunteer = await volunteer_service.add_volunteer(
                db,
                booth_id,
                volunteer_name="Test Volunteer",
                phone="9876543210",
                role="BOOTH_AGENT",
            )

            # Remove volunteer
            await volunteer_service.remove_volunteer(db, volunteer.id)

            # Verify removed
            with pytest.raises(VolunteerNotFound):
                await volunteer_service.remove_volunteer(db, volunteer.id)

    @pytest.mark.asyncio
    async def test_get_booth_coverage(self, test_db):
        """Test getting booth volunteer coverage."""
        async with test_db() as db:
            volunteer_service = VolunteerService()
            booth_service = BoothService()

            # Get booth
            booths = await booth_service.list_booths(db, limit=1)
            booth_id = booths.booths[0].id

            # Add volunteers
            for i in range(5):
                await volunteer_service.add_volunteer(
                    db,
                    booth_id,
                    volunteer_name=f"Volunteer {i+1}",
                    phone=f"987654321{i}",
                    role="BOOTH_AGENT",
                )

            # Get coverage
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

            # Get booth
            booths = await booth_service.list_booths(db, limit=1)
            booth_id = booths.booths[0].id

            # Step 1: Update contact rate
            updated = await booth_service.update_booth(db, booth_id, contact_rate=60.0)
            assert updated.contact_rate == 60.0

            # Step 2: Add volunteers
            for i in range(4):
                await volunteer_service.add_volunteer(
                    db,
                    booth_id,
                    volunteer_name=f"Volunteer {i+1}",
                    phone=f"987654321{i}",
                    role=["BOOTH_AGENT", "VOTER_CONTACT", "TRANSPORT", "COORDINATOR"][i],
                )

            # Step 3: Recompute scores
            updated = await booth_service.recompute_booth_scores(db, booth_id)
            # With 60% contact rate and 4 volunteers, should have decent health/risk
            assert 20.0 <= updated.risk_score <= 50.0
            assert 30.0 <= updated.health_score <= 70.0

            # Step 4: Check coverage
            coverage = await volunteer_service.get_booth_coverage(db, booth_id)
            assert coverage.total_volunteers == 4
            assert coverage.coverage_percentage > 0

    @pytest.mark.asyncio
    async def test_risk_assessment_workflow(self, test_db):
        """Test risk assessment workflow."""
        async with test_db() as db:
            booth_service = BoothService()

            # Get booth
            booths = await booth_service.list_booths(db, limit=1)
            booth_id = booths.booths[0].id
            constituency_id = booths.booths[0].constituency_id

            # Mark as low contact, high risk
            await booth_service.update_booth(db, booth_id, contact_rate=10.0)
            await booth_service.recompute_booth_scores(db, booth_id)

            # Get risk report
            report = await booth_service.get_risk_report(db, constituency_id)

            # Should be identified as high risk
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
