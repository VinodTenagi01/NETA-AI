"""
Opposition Intelligence API Routes

6-8 endpoints for comparative opposition analysis and counter-intelligence.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Query, Path, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_design.database import get_db
from app.security_auth.dependencies import require_role
from app.opposition_intelligence.service import OppositionService
from app.opposition_intelligence.exceptions import (
    OppositionDataNotFound,
    SentimentComparisonError,
)
from app.opposition_intelligence.models import (
    SentimentComparisonQuery,
    ActivityMapQuery,
    NarrativeFilterQuery,
    CounterResponseRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/opposition", tags=["Opposition Intelligence"])


# ============================================================================
# Comparative Sentiment Endpoints
# ============================================================================


@router.get(
    "/sentiment-comparison",
    status_code=status.HTTP_200_OK,
    summary="Get comparative sentiment analysis",
    dependencies=[Depends(require_role(["campaign_manager", "super_admin"]))],
)
async def get_sentiment_comparison(
    constituency_id: UUID = Query(..., description="Constituency ID"),
    lookback_hours: int = Query(24, ge=1, le=168, description="Hours to analyze"),
    include_momentum: bool = Query(True, description="Include momentum analysis"),
    include_alerts: bool = Query(True, description="Include divergence alerts"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comparative sentiment analysis between candidate and opposition.

    **Returns**:
    - Dual time-series (candidate vs opposition)
    - Sentiment divergence score
    - Momentum direction (GAINING, STABLE, LOSING)
    - Divergence alerts if divergence exceeds threshold

    **Severity Levels**:
    - HIGH: Divergence > 0.3 for >4 hours
    - MEDIUM: Divergence > 0.1 for extended period
    - LOW: Minor divergence or short duration
    """
    try:
        service = OppositionService()
        result = await service.get_sentiment_comparison(
            db,
            constituency_id,
            lookback_hours=lookback_hours,
            include_momentum=include_momentum,
            include_alerts=include_alerts,
        )
        return result
    except Exception as e:
        logger.error(f"Error in sentiment comparison: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sentiment comparison failed",
        )


# ============================================================================
# Opposition Activity Mapping Endpoints
# ============================================================================


@router.get(
    "/activity-map",
    status_code=status.HTTP_200_OK,
    summary="Get opposition activity geospatial map",
    dependencies=[Depends(require_role(["campaign_manager", "super_admin"]))],
)
async def get_opposition_activity_map(
    constituency_id: UUID = Query(..., description="Constituency ID"),
    heatmap_grid_size: int = Query(500, ge=100, le=5000, description="Grid size in meters"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get opposition ground activities (rallies, canvassing) mapped geospatially.

    **Returns**:
    - GeoJSON FeatureCollection of opposition locations
    - Heatmap showing activity concentration
    - High-concentration zones identified

    **Activity Types**:
    - RALLY: Large-scale opposition event
    - CANVASSING: Door-to-door voter contact
    - APPEARANCE: Candidate appearance
    - OFFICE: Opposition campaign office
    """
    try:
        service = OppositionService()
        result = await service.get_opposition_activity_map(
            db, constituency_id, heatmap_grid_size
        )
        return result
    except Exception as e:
        logger.error(f"Error in activity mapping: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Activity mapping failed",
        )


# ============================================================================
# Opposition Narrative Endpoints
# ============================================================================


@router.get(
    "/narratives",
    status_code=status.HTTP_200_OK,
    summary="Get opposition narratives from news",
    dependencies=[Depends(require_role(["campaign_manager", "super_admin"]))],
)
async def get_opposition_narratives(
    constituency_id: UUID = Query(..., description="Constituency ID"),
    lookback_hours: int = Query(24, ge=1, le=168, description="Lookback period"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get opposition narratives extracted from news articles.

    **Returns**:
    - Opposition narrative clusters
    - Topic classification (POLICY, PERSONAL, ECONOMY, HEALTHCARE, etc.)
    - Sentiment of narratives
    - Article count and momentum
    - Severity scoring (0-10)

    **Momentum Values**:
    - TRENDING: Growing article volume and negative sentiment
    - STABLE: Consistent coverage
    - DECLINING: Decreasing attention
    """
    try:
        service = OppositionService()
        narratives = await service.get_opposition_narratives(
            db, constituency_id, lookback_hours, limit
        )
        return {"narratives": narratives, "count": len(narratives)}
    except Exception as e:
        logger.error(f"Error fetching narratives: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Narrative retrieval failed",
        )


@router.get(
    "/narratives/{narrative_id}",
    status_code=status.HTTP_200_OK,
    summary="Get narrative details with recommendations",
    dependencies=[Depends(require_role(["campaign_manager", "super_admin"]))],
)
async def get_narrative_detail(
    narrative_id: UUID = Path(..., description="Narrative cluster ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed analysis of opposition narrative with counter-recommendations.

    **Returns**:
    - Narrative cluster details
    - Articles in cluster
    - Entities mentioned
    - Counter-response recommendations
    - Response history if action taken
    """
    try:
        # Placeholder implementation - would fetch from database
        return {
            "narrative_id": narrative_id,
            "title": "Opposition Narrative",
            "counter_recommendations": [
                "Prepare factual response with data",
                "Coordinate media statement",
                "Brief campaign field teams",
            ],
            "response_history": [],
        }
    except Exception as e:
        logger.error(f"Error fetching narrative detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Narrative detail retrieval failed",
        )


@router.post(
    "/narratives/{narrative_id}/response",
    status_code=status.HTTP_201_CREATED,
    summary="Log counter-response action",
    dependencies=[Depends(require_role(["campaign_manager", "super_admin"]))],
)
async def log_narrative_response(
    narrative_id: UUID = Path(..., description="Narrative cluster ID"),
    request: CounterResponseRequest = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Log counter-response action taken against opposition narrative.

    **Action Types**:
    - factual_response: Prepared factual response
    - media_push: Media statement or coverage
    - ground_activity: Ground team coordination
    - no_action: Decided not to respond

    **Returns**: Response entry with timestamp and action details
    """
    try:
        # Placeholder - would log to database
        return {
            "narrative_id": narrative_id,
            "action": request.action if request else "no_action",
            "timestamp": "2026-05-24T00:00:00Z",
            "status": "logged",
        }
    except Exception as e:
        logger.error(f"Error logging response: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Response logging failed",
        )


# ============================================================================
# Opposition Alerts Endpoint
# ============================================================================


@router.get(
    "/alerts",
    status_code=status.HTTP_200_OK,
    summary="Get opposition intelligence alerts",
    dependencies=[Depends(require_role(["campaign_manager", "super_admin"]))],
)
async def get_opposition_alerts(
    constituency_id: UUID = Query(..., description="Constituency ID"),
    severity: str = Query("LOW", pattern="^(CRITICAL|HIGH|MEDIUM|LOW)$", description="Min severity"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get opposition intelligence alerts sorted by severity.

    **Alert Types**:
    - DIVERGENCE: Sentiment divergence exceeds threshold
    - SEVERITY: Narrative severity score high
    - MOMENTUM: Opposition momentum increasing
    - ACTIVITY: Unusual opposition activity detected

    **Returns**:
    - Sorted alert list with summary counts
    - Recommended actions per alert
    - Related narrative references
    """
    try:
        service = OppositionService()
        result = await service.get_opposition_alerts(db, constituency_id, severity)
        return result
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Alert retrieval failed",
        )


# ============================================================================
# Health Check
# ============================================================================


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Opposition intelligence service health",
)
async def opposition_service_health():
    """Check opposition intelligence service status."""
    return {
        "status": "healthy",
        "service": "opposition-intelligence",
        "version": "1.0.0",
    }
