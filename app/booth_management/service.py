"""
Booth Management Service

Business logic for booth CRUD, risk scoring, and reporting.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_, or_, desc, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database_design.models import Booth, BoothVolunteer, FieldReport, User
from app.booth_management.models import (
    BoothResponse, BoothListResponse, VolunteerResponse,
    RiskReportResponse, HealthDashboardResponse, CoverageResponse,
)
from app.booth_management.exceptions import (
    BoothNotFound, VolunteerNotFound, InvalidBoothRequest,
    InvalidVolunteerRole, RiskCalculationError,
)
from app.booth_management.risk_calculator import RiskCalculator

logger = logging.getLogger(__name__)

# Valid volunteer roles
VALID_VOLUNTEER_ROLES = {"BOOTH_AGENT", "VOTER_CONTACT", "TRANSPORT", "COORDINATOR"}


class BoothService:
    """Service for booth management operations."""

    def __init__(self):
        self.calculator = RiskCalculator()

    async def list_booths(
        self,
        db: AsyncSession,
        zone_id: Optional[UUID] = None,
        constituency_id: Optional[UUID] = None,
        risk_min: Optional[float] = None,
        risk_max: Optional[float] = None,
        health_min: Optional[float] = None,
        health_max: Optional[float] = None,
        contact_rate_min: Optional[float] = None,
        swing_only: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> BoothListResponse:
        """
        List booths with filtering and aggregation.

        Args:
            db: Database session
            zone_id: Filter by zone
            constituency_id: Filter by constituency
            risk_min/risk_max: Filter by risk score range
            health_min/health_max: Filter by health score range
            contact_rate_min: Minimum contact rate
            swing_only: Filter to swing booths only
            limit: Result limit
            offset: Pagination offset

        Returns:
            BoothListResponse with booths and aggregations
        """
        # Build base query
        stmt = select(Booth)

        # Apply filters
        if constituency_id:
            stmt = stmt.where(Booth.constituency_id == constituency_id)

        if zone_id:
            stmt = stmt.where(Booth.zone_id == zone_id)

        if risk_min is not None:
            stmt = stmt.where(Booth.risk_score >= risk_min)

        if risk_max is not None:
            stmt = stmt.where(Booth.risk_score <= risk_max)

        if health_min is not None:
            stmt = stmt.where(Booth.health_score >= health_min)

        if health_max is not None:
            stmt = stmt.where(Booth.health_score <= health_max)

        if contact_rate_min is not None:
            stmt = stmt.where(Booth.contact_rate >= contact_rate_min)

        if swing_only:
            stmt = stmt.where(Booth.swing_booth == True)

        # Get total count before pagination
        count_stmt = select(func.count(Booth.id)).select_from(Booth)
        for clause in stmt.whereclause.__iter__() if stmt.whereclause is not None else []:
            count_stmt = count_stmt.where(clause)

        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        # Load volunteers for each booth
        stmt = stmt.options(joinedload(Booth.volunteers))

        # Order and paginate
        stmt = stmt.order_by(desc(Booth.updated_at)).limit(limit).offset(offset)

        result = await db.execute(stmt)
        booths = result.unique().scalars().all()

        # Convert to response models
        booth_responses = [self._booth_to_response(b) for b in booths]

        # Compute aggregations
        by_risk = await self._count_by_risk_level(db)
        by_health = await self._count_by_health_status(db)

        return BoothListResponse(
            booths=booth_responses,
            total=total,
            by_risk_level=by_risk,
            by_health_status=by_health,
        )

    async def get_booth(self, db: AsyncSession, booth_id: UUID) -> BoothResponse:
        """Get a single booth by ID."""
        stmt = select(Booth).where(Booth.id == booth_id).options(joinedload(Booth.volunteers))
        result = await db.execute(stmt)
        booth = result.scalar()

        if not booth:
            raise BoothNotFound(str(booth_id))

        return self._booth_to_response(booth)

    async def update_booth(
        self,
        db: AsyncSession,
        booth_id: UUID,
        contact_rate: Optional[float] = None,
        notes: Optional[str] = None,
        last_contact_at: Optional[datetime] = None,
    ) -> BoothResponse:
        """
        Update booth fields.

        Args:
            db: Database session
            booth_id: Booth ID
            contact_rate: Update contact rate (0-100)
            notes: Additional notes
            last_contact_at: Update last contact timestamp

        Returns:
            Updated BoothResponse
        """
        # Fetch booth
        stmt = select(Booth).where(Booth.id == booth_id).options(joinedload(Booth.volunteers))
        result = await db.execute(stmt)
        booth = result.scalar()

        if not booth:
            raise BoothNotFound(str(booth_id))

        # Validate and update fields
        if contact_rate is not None:
            if not (0 <= contact_rate <= 100):
                raise InvalidBoothRequest("contact_rate must be between 0 and 100")
            booth.contact_rate = contact_rate

        if last_contact_at is not None:
            booth.last_contact_at = last_contact_at

        booth.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(booth, ["volunteers"])

        return self._booth_to_response(booth)

    async def assign_commander(
        self,
        db: AsyncSession,
        booth_id: UUID,
        user_id: UUID,
    ) -> BoothResponse:
        """
        Assign a ground commander to booth.

        Args:
            db: Database session
            booth_id: Booth ID
            user_id: User ID to assign as commander

        Returns:
            Updated BoothResponse
        """
        stmt = select(Booth).where(Booth.id == booth_id).options(joinedload(Booth.volunteers))
        result = await db.execute(stmt)
        booth = result.scalar()

        if not booth:
            raise BoothNotFound(str(booth_id))

        # Verify user exists
        user_stmt = select(User).where(User.id == user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar()

        if not user:
            raise InvalidBoothRequest(f"User {user_id} not found")

        # Update commander
        booth.assigned_commander = user
        booth.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(booth, ["volunteers"])

        return self._booth_to_response(booth)

    async def recompute_booth_scores(
        self,
        db: AsyncSession,
        booth_id: UUID,
    ) -> BoothResponse:
        """
        Recompute risk and health scores for a booth.

        Fetches latest metrics and recalculates scores.

        Args:
            db: Database session
            booth_id: Booth ID

        Returns:
            Updated BoothResponse with new scores
        """
        stmt = select(Booth).where(Booth.id == booth_id).options(joinedload(Booth.volunteers))
        result = await db.execute(stmt)
        booth = result.scalar()

        if not booth:
            raise BoothNotFound(str(booth_id))

        try:
            # Count high-severity field reports from last 7 days
            cutoff = datetime.utcnow() - timedelta(days=7)
            report_stmt = select(func.count(FieldReport.id)).where(
                and_(
                    FieldReport.booth_id == booth_id,
                    FieldReport.severity >= 4,
                    FieldReport.reported_at >= cutoff,
                )
            )
            report_result = await db.execute(report_stmt)
            high_severity_count = report_result.scalar() or 0

            # Calculate days since last contact
            days_since_contact = self.calculator.calculate_days_since_contact(
                booth.last_contact_at
            )

            # Calculate volunteer coverage
            volunteer_coverage = self.calculator.estimate_volunteer_coverage(
                len(booth.volunteers),
                booth.total_voters,
            )

            # Count recent reports
            count_stmt = select(func.count(FieldReport.id)).where(
                and_(
                    FieldReport.booth_id == booth_id,
                    FieldReport.reported_at >= cutoff,
                )
            )
            count_result = await db.execute(count_stmt)
            recent_report_count = count_result.scalar() or 0

            report_frequency = self.calculator.estimate_report_frequency(
                recent_report_count,
                days_window=7,
            )

            # Calculate new scores
            new_risk_score = self.calculator.calculate_risk_score(
                booth.contact_rate,
                high_severity_count,
                days_since_contact,
            )

            new_health_score = self.calculator.calculate_health_score(
                booth.contact_rate,
                volunteer_coverage,
                report_frequency,
            )

            # Update booth
            booth.risk_score = new_risk_score
            booth.health_score = new_health_score
            booth.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(booth, ["volunteers"])

            logger.info(
                f"Recomputed scores for booth {booth_id}: risk={new_risk_score}, health={new_health_score}"
            )

            return self._booth_to_response(booth)

        except Exception as e:
            logger.error(f"Error recomputing scores for booth {booth_id}: {e}")
            raise RiskCalculationError(f"Failed to recompute scores: {str(e)}")

    async def get_risk_report(
        self,
        db: AsyncSession,
        constituency_id: UUID,
    ) -> RiskReportResponse:
        """
        Get risk report for a constituency.

        Identifies high-risk, swing, and under-resourced booths.

        Args:
            db: Database session
            constituency_id: Constituency ID

        Returns:
            RiskReportResponse with risk analysis
        """
        # Get all booths in constituency
        stmt = select(Booth).where(
            Booth.constituency_id == constituency_id
        ).options(joinedload(Booth.volunteers))

        result = await db.execute(stmt)
        booths = result.unique().scalars().all()

        # Categorize booths
        high_risk_booths = [
            b for b in booths
            if b.risk_score >= self.calculator.RISK_HIGH
        ]

        swing_booths = [b for b in booths if b.swing_booth]

        under_resourced = [
            b for b in booths
            if self.calculator.estimate_volunteer_coverage(
                len(b.volunteers), b.total_voters
            ) < 50.0
        ]

        # Generate interventions
        interventions = []
        if high_risk_booths:
            interventions.append(
                f"Allocate additional resources to {len(high_risk_booths)} high-risk booths"
            )
        if under_resourced:
            interventions.append(
                f"Recruit volunteers for {len(under_resourced)} under-resourced booths"
            )
        if swing_booths:
            interventions.append(
                f"Focus campaign efforts on {len(swing_booths)} swing booths"
            )

        return RiskReportResponse(
            constituency_id=constituency_id,
            high_risk_booths=[self._booth_to_response(b) for b in high_risk_booths],
            swing_booths=[self._booth_to_response(b) for b in swing_booths],
            under_resourced=[self._booth_to_response(b) for b in under_resourced],
            recommended_interventions=interventions,
        )

    async def get_health_dashboard(
        self,
        db: AsyncSession,
        constituency_id: UUID,
    ) -> HealthDashboardResponse:
        """
        Get booth health dashboard for a constituency.

        Args:
            db: Database session
            constituency_id: Constituency ID

        Returns:
            HealthDashboardResponse
        """
        # Get all booths
        stmt = select(Booth).where(
            Booth.constituency_id == constituency_id
        ).options(joinedload(Booth.volunteers))

        result = await db.execute(stmt)
        booths = result.unique().scalars().all()

        # Count by health status
        healthy = sum(1 for b in booths if b.health_score >= self.calculator.HEALTH_HEALTHY)
        degraded = sum(
            1 for b in booths
            if self.calculator.HEALTH_DEGRADED <= b.health_score < self.calculator.HEALTH_HEALTHY
        )
        critical = sum(1 for b in booths if b.health_score <= self.calculator.HEALTH_CRITICAL)

        # Calculate averages
        avg_risk = sum(b.risk_score for b in booths) / len(booths) if booths else 0
        avg_health = sum(b.health_score for b in booths) / len(booths) if booths else 0

        # Identify booths needing attention
        attention_needed = [
            b for b in booths
            if b.health_score < self.calculator.HEALTH_DEGRADED
            or b.risk_score >= self.calculator.RISK_HIGH
        ]

        return HealthDashboardResponse(
            constituency_id=constituency_id,
            total_booths=len(booths),
            healthy=healthy,
            degraded=degraded,
            critical=critical,
            average_risk_score=avg_risk,
            average_health_score=avg_health,
            booths_needing_attention=[self._booth_to_response(b) for b in attention_needed],
        )

    # ========================================================================
    # Volunteer Operations
    # ========================================================================

    async def list_volunteers(
        self,
        db: AsyncSession,
        booth_id: UUID,
    ) -> list[VolunteerResponse]:
        """List volunteers for a booth."""
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
        """Add volunteer to booth."""
        # Validate booth exists
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

        logger.info(f"Added volunteer {volunteer.id} to booth {booth_id}")

        return self._volunteer_to_response(volunteer)

    async def update_volunteer(
        self,
        db: AsyncSession,
        volunteer_id: UUID,
        role: Optional[str] = None,
        is_confirmed: Optional[bool] = None,
    ) -> VolunteerResponse:
        """Update volunteer assignment."""
        stmt = select(BoothVolunteer).where(BoothVolunteer.id == volunteer_id)
        result = await db.execute(stmt)
        volunteer = result.scalar()

        if not volunteer:
            raise VolunteerNotFound(str(volunteer_id))

        if role is not None:
            if role not in VALID_VOLUNTEER_ROLES:
                raise InvalidVolunteerRole(role)
            volunteer.role = role

        if is_confirmed is not None:
            volunteer.is_confirmed = is_confirmed

        await db.commit()
        await db.refresh(volunteer)

        return self._volunteer_to_response(volunteer)

    async def remove_volunteer(
        self,
        db: AsyncSession,
        volunteer_id: UUID,
    ) -> None:
        """Remove volunteer from booth."""
        stmt = select(BoothVolunteer).where(BoothVolunteer.id == volunteer_id)
        result = await db.execute(stmt)
        volunteer = result.scalar()

        if not volunteer:
            raise VolunteerNotFound(str(volunteer_id))

        await db.delete(volunteer)
        await db.commit()

        logger.info(f"Removed volunteer {volunteer_id}")

    async def get_booth_coverage(
        self,
        db: AsyncSession,
        booth_id: UUID,
    ) -> CoverageResponse:
        """Get volunteer coverage for a booth."""
        # Get booth
        booth_stmt = select(Booth).where(Booth.id == booth_id).options(joinedload(Booth.volunteers))
        booth_result = await db.execute(booth_stmt)
        booth = booth_result.scalar()

        if not booth:
            raise BoothNotFound(str(booth_id))

        # Count volunteers by role
        by_role = {}
        for volunteer in booth.volunteers:
            by_role[volunteer.role] = by_role.get(volunteer.role, 0) + 1

        # Calculate coverage
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

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _booth_to_response(self, booth: Booth) -> BoothResponse:
        """Convert ORM booth to Pydantic response model."""
        return BoothResponse(
            id=booth.id,
            constituency_id=booth.constituency_id,
            zone_id=booth.zone_id,
            booth_number=booth.booth_number,
            booth_name=booth.booth_name,
            address=booth.address,
            total_voters=booth.total_voters,
            female_voters=booth.female_voters,
            male_voters=booth.male_voters,
            third_gender=booth.third_gender,
            risk_score=float(booth.risk_score) if booth.risk_score else 50.0,
            health_score=float(booth.health_score) if booth.health_score else 50.0,
            contact_rate=float(booth.contact_rate) if booth.contact_rate else 0.0,
            swing_booth=booth.swing_booth,
            historical_margin=float(booth.historical_margin) if booth.historical_margin else None,
            last_report_at=booth.last_report_at,
            last_contact_at=booth.last_contact_at,
            assigned_commander_id=booth.assigned_commander,
            volunteers=[self._volunteer_to_response(v) for v in booth.volunteers],
            created_at=booth.created_at,
            updated_at=booth.updated_at,
        )

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

    async def _count_by_risk_level(self, db: AsyncSession) -> dict:
        """Count booths by risk level."""
        stmt = select(
            func.sum(
                case(
                    [
                        (Booth.risk_score >= self.calculator.RISK_HIGH, 1),
                    ],
                    else_=0,
                )
            ).label("high"),
            func.sum(
                case(
                    [
                        (
                            and_(
                                Booth.risk_score >= self.calculator.RISK_MEDIUM,
                                Booth.risk_score < self.calculator.RISK_HIGH,
                            ),
                            1,
                        ),
                    ],
                    else_=0,
                )
            ).label("medium"),
            func.sum(
                case(
                    [
                        (Booth.risk_score < self.calculator.RISK_MEDIUM, 1),
                    ],
                    else_=0,
                )
            ).label("low"),
        )

        result = await db.execute(stmt)
        row = result.first()

        return {
            "high": row[0] or 0,
            "medium": row[1] or 0,
            "low": row[2] or 0,
        }

    async def _count_by_health_status(self, db: AsyncSession) -> dict:
        """Count booths by health status."""
        stmt = select(
            func.sum(
                case(
                    [
                        (Booth.health_score >= self.calculator.HEALTH_HEALTHY, 1),
                    ],
                    else_=0,
                )
            ).label("healthy"),
            func.sum(
                case(
                    [
                        (
                            and_(
                                Booth.health_score >= self.calculator.HEALTH_DEGRADED,
                                Booth.health_score < self.calculator.HEALTH_HEALTHY,
                            ),
                            1,
                        ),
                    ],
                    else_=0,
                )
            ).label("degraded"),
            func.sum(
                case(
                    [
                        (Booth.health_score <= self.calculator.HEALTH_CRITICAL, 1),
                    ],
                    else_=0,
                )
            ).label("critical"),
        )

        result = await db.execute(stmt)
        row = result.first()

        return {
            "healthy": row[0] or 0,
            "degraded": row[1] or 0,
            "critical": row[2] or 0,
        }
