"""SLA monitoring and breach detection."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_design.models import Escalation
from app.ground_operations.escalation_service import EscalationService
from app.ground_operations.models import EscalationResponse, SLAMonitorStatus


logger = logging.getLogger(__name__)


class SLAMonitorService:
    """Service for SLA breach detection and monitoring."""

    async def check_sla_breaches(
        self, db: AsyncSession
    ) -> list[EscalationResponse]:
        """Check for SLA breaches and escalate to campaign manager."""
        escalation_service = EscalationService()
        breached = await escalation_service.check_sla_breaches(db)

        # Log mock notifications (Phase 1)
        for escalation in breached:
            logger.warning(
                f"[MOCK WHATSAPP] SLA Breached - Escalation {escalation.id} "
                f"assigned to {escalation.escalated_to_name}"
            )

        return breached

    async def check_sla_warnings(
        self, db: AsyncSession
    ) -> list[EscalationResponse]:
        """Check for escalations approaching SLA deadline (15 min before)."""
        now = datetime.now(timezone.utc)
        warning_time = now + timedelta(minutes=15)

        stmt = select(Escalation).where(
            and_(
                Escalation.status.in_(["NEW", "IN_PROGRESS"]),
                Escalation.sla_deadline < warning_time,
                Escalation.sla_deadline > now,
            )
        )
        result = await db.execute(stmt)
        at_risk = result.scalars().all()

        escalation_service = EscalationService()
        responses = []

        for escalation in at_risk:
            response = await escalation_service._escalation_to_response(
                db, escalation
            )
            responses.append(response)

            # Log mock notification (Phase 1)
            logger.warning(
                f"[MOCK WHATSAPP] SLA Warning - Escalation {escalation.id} "
                f"deadline in 15 minutes. Assigned to {response.assigned_to_name}"
            )

        return responses

    async def get_sla_status(self, db: AsyncSession) -> SLAMonitorStatus:
        """Get current SLA status summary."""
        now = datetime.now(timezone.utc)

        # Get all open escalations
        stmt = select(Escalation).where(
            Escalation.status.in_(["NEW", "IN_PROGRESS"])
        )
        result = await db.execute(stmt)
        open_escalations = result.scalars().all()

        escalation_service = EscalationService()

        breached = []
        at_risk = []
        on_track_count = 0

        for escalation in open_escalations:
            response = await escalation_service._escalation_to_response(
                db, escalation
            )

            if escalation.sla_deadline < now:
                breached.append(response)
            elif escalation.sla_deadline - now < timedelta(minutes=15):
                at_risk.append(response)
            else:
                on_track_count += 1

        return SLAMonitorStatus(
            total_escalations=len(open_escalations),
            breached=breached,
            at_risk=at_risk,
            on_track_count=on_track_count,
        )
