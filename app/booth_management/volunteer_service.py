"""
Volunteer Service

Handles volunteer lifecycle management and coordination.
"""

import logging
from uuid import UUID
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_design.models import Booth, BoothVolunteer, User
from app.booth_management.models import VolunteerResponse, CoverageResponse
from app.booth_management.exceptions import BoothNotFound, VolunteerNotFound, InvalidVolunteerRole
from app.booth_management.risk_calculator import RiskCalculator

logger = logging.getLogger(__name__)

VALID_VOLUNTEER_ROLES = {"BOOTH_AGENT", "VOTER_CONTACT", "TRANSPORT", "COORDINATOR"}


class VolunteerService:
    """Service for volunteer management operations."""

    def __init__(self):
        self.calculator = RiskCalculator()

    async def list_volunteers(
        self,
        db: AsyncSession,
        booth_id: UUID,
    ) -> list[VolunteerResponse]:
        """
        List volunteers for a booth.

        Args:
            db: Database session
            booth_id: Booth ID

        Returns:
            List of VolunteerResponse objects
        """
        stmt = select(BoothVolunteer).where(BoothVolunteer.booth_id == booth_id)
        result = await db.execute(stmt)
        volunteers = result.scalars().all()

        return [self._volunteer_to_response(v) for v in volunteers]

    async def add_volunteer(
        self,
        db: AsyncSession,
        booth_id: UUID,
        volunteer_name: str,
        phone: Optional[str],
        role: str,
        user_id: Optional[UUID] = None,
    ) -> VolunteerResponse:
        """
        Add volunteer to booth.

        Args:
            db: Database session
            booth_id: Booth ID
            volunteer_name: Name of volunteer
            phone: Phone number (optional)
            role: Volunteer role (BOOTH_AGENT, VOTER_CONTACT, TRANSPORT, COORDINATOR)
            user_id: Link to User (optional)

        Returns:
            VolunteerResponse

        Raises:
            BoothNotFound: If booth doesn't exist
            InvalidVolunteerRole: If role is invalid
        """
        # Verify booth exists
        booth_stmt = select(Booth).where(Booth.id == booth_id)
        booth_result = await db.execute(booth_stmt)
        booth = booth_result.scalar()

        if not booth:
            raise BoothNotFound(str(booth_id))

        # Validate role
        if role not in VALID_VOLUNTEER_ROLES:
            raise InvalidVolunteerRole(role)

        # Create volunteer
        volunteer = BoothVolunteer(
            booth_id=booth_id,
            volunteer_name=volunteer_name,
            phone=phone,
            role=role,
            user_id=user_id,
        )

        db.add(volunteer)
        await db.commit()
        await db.refresh(volunteer)

        logger.info(
            f"Added {role} volunteer '{volunteer_name}' to booth {booth_id}"
        )

        return self._volunteer_to_response(volunteer)

    async def update_volunteer(
        self,
        db: AsyncSession,
        volunteer_id: UUID,
        role: Optional[str] = None,
        is_confirmed: Optional[bool] = None,
    ) -> VolunteerResponse:
        """
        Update volunteer assignment.

        Args:
            db: Database session
            volunteer_id: Volunteer ID
            role: New role (optional)
            is_confirmed: Confirmation status (optional)

        Returns:
            Updated VolunteerResponse

        Raises:
            VolunteerNotFound: If volunteer doesn't exist
            InvalidVolunteerRole: If role is invalid
        """
        stmt = select(BoothVolunteer).where(BoothVolunteer.id == volunteer_id)
        result = await db.execute(stmt)
        volunteer = result.scalar()

        if not volunteer:
            raise VolunteerNotFound(str(volunteer_id))

        # Update fields
        if role is not None:
            if role not in VALID_VOLUNTEER_ROLES:
                raise InvalidVolunteerRole(role)
            volunteer.role = role

        if is_confirmed is not None:
            volunteer.is_confirmed = is_confirmed

        await db.commit()
        await db.refresh(volunteer)

        logger.info(f"Updated volunteer {volunteer_id}")

        return self._volunteer_to_response(volunteer)

    async def remove_volunteer(
        self,
        db: AsyncSession,
        volunteer_id: UUID,
    ) -> None:
        """
        Remove volunteer from booth.

        Args:
            db: Database session
            volunteer_id: Volunteer ID

        Raises:
            VolunteerNotFound: If volunteer doesn't exist
        """
        stmt = select(BoothVolunteer).where(BoothVolunteer.id == volunteer_id)
        result = await db.execute(stmt)
        volunteer = result.scalar()

        if not volunteer:
            raise VolunteerNotFound(str(volunteer_id))

        booth_id = volunteer.booth_id
        await db.delete(volunteer)
        await db.commit()

        logger.info(f"Removed volunteer {volunteer_id} from booth {booth_id}")

    async def get_booth_coverage(
        self,
        db: AsyncSession,
        booth_id: UUID,
    ) -> CoverageResponse:
        """
        Get volunteer coverage analysis for booth.

        Args:
            db: Database session
            booth_id: Booth ID

        Returns:
            CoverageResponse with coverage metrics

        Raises:
            BoothNotFound: If booth doesn't exist
        """
        # Get booth with volunteers
        from sqlalchemy.orm import joinedload
        stmt = select(Booth).where(Booth.id == booth_id).options(joinedload(Booth.volunteers))
        result = await db.execute(stmt)
        booth = result.scalar()

        if not booth:
            raise BoothNotFound(str(booth_id))

        # Count volunteers by role
        by_role = {}
        for volunteer in booth.volunteers:
            by_role[volunteer.role] = by_role.get(volunteer.role, 0) + 1

        # Calculate coverage percentage
        coverage_pct = self.calculator.estimate_volunteer_coverage(
            len(booth.volunteers),
            booth.total_voters,
        )

        # Determine status
        if coverage_pct >= 100:
            status = "FULL"
        elif coverage_pct >= 50:
            status = "PARTIAL"
        else:
            status = "MINIMAL"

        return CoverageResponse(
            booth_id=booth_id,
            booth_number=booth.booth_number,
            total_volunteers=len(booth.volunteers),
            by_role=by_role,
            coverage_percentage=coverage_pct,
            coverage_status=status,
        )

    async def get_coverage_by_role(
        self,
        db: AsyncSession,
        booth_id: UUID,
    ) -> dict:
        """
        Get detailed coverage breakdown by role.

        Args:
            db: Database session
            booth_id: Booth ID

        Returns:
            Dict with coverage info per role
        """
        stmt = select(BoothVolunteer).where(BoothVolunteer.booth_id == booth_id)
        result = await db.execute(stmt)
        volunteers = result.scalars().all()

        # Count by role and confirmation status
        role_stats = {}
        for role in VALID_VOLUNTEER_ROLES:
            role_volunteers = [v for v in volunteers if v.role == role]
            role_stats[role] = {
                "total": len(role_volunteers),
                "confirmed": sum(1 for v in role_volunteers if v.is_confirmed),
                "unconfirmed": sum(1 for v in role_volunteers if not v.is_confirmed),
            }

        return role_stats

    async def confirm_multiple_volunteers(
        self,
        db: AsyncSession,
        volunteer_ids: list[UUID],
    ) -> int:
        """
        Bulk confirm volunteers.

        Args:
            db: Database session
            volunteer_ids: List of volunteer IDs to confirm

        Returns:
            Count of confirmed volunteers
        """
        confirmed = 0
        for volunteer_id in volunteer_ids:
            stmt = select(BoothVolunteer).where(BoothVolunteer.id == volunteer_id)
            result = await db.execute(stmt)
            volunteer = result.scalar()

            if volunteer and not volunteer.is_confirmed:
                volunteer.is_confirmed = True
                confirmed += 1

        if confirmed > 0:
            await db.commit()
            logger.info(f"Confirmed {confirmed} volunteers")

        return confirmed

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _volunteer_to_response(self, volunteer: BoothVolunteer) -> VolunteerResponse:
        """Convert ORM volunteer to Pydantic response model."""
        return VolunteerResponse(
            id=volunteer.id,
            booth_id=volunteer.booth_id,
            volunteer_name=volunteer.volunteer_name,
            phone=volunteer.phone,
            role=volunteer.role,
            is_confirmed=volunteer.is_confirmed,
            created_at=volunteer.created_at,
        )
