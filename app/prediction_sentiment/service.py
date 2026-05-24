"""
Prediction Service

Orchestrates win probability predictions, sentiment forecasting,
and demographic analysis across the election campaign.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_design.models import Booth, FieldReport, User
from app.booth_management.risk_calculator import RiskCalculator
from app.ground_operations.mood_analyzer import MoodAnalyzer
from app.prediction_sentiment.win_probability import WinProbabilityCalculator
from app.prediction_sentiment.sentiment_forecaster import SentimentForecaster
from app.prediction_sentiment.demographic_analyzer import DemographicAnalyzer
from app.prediction_sentiment.models import (
    WinProbabilityResponse,
    SentimentBreakdownResponse,
    SentimentForecastResponse,
    DemographicSentimentResponse,
)
from app.prediction_sentiment.exceptions import (
    PredictionNotAvailable,
    ForecastingError,
    DemographicAnalysisError,
)

logger = logging.getLogger(__name__)


class PredictionService:
    """Service for election predictions and sentiment analysis."""

    def __init__(self):
        self.win_prob_calc = WinProbabilityCalculator()
        self.sentiment_forecaster = SentimentForecaster()
        self.demographic_analyzer = DemographicAnalyzer()
        self.mood_analyzer = MoodAnalyzer()
        self.risk_calculator = RiskCalculator()

    async def get_win_probability(
        self,
        db: AsyncSession,
        constituency_id: UUID,
        include_booth_breakdown: bool = False,
    ) -> WinProbabilityResponse:
        """
        Calculate overall election win probability.

        Args:
            db: Database session
            constituency_id: Constituency ID
            include_booth_breakdown: Whether to include booth-level predictions

        Returns:
            WinProbabilityResponse with overall and component probabilities

        Raises:
            PredictionNotAvailable: If insufficient data
        """
        try:
            # Get constituency booths
            stmt = select(Booth).where(Booth.constituency_id == constituency_id)
            result = await db.execute(stmt)
            booths = result.scalars().all()

            if not booths:
                raise PredictionNotAvailable("No booths found for constituency")

            # Calculate average metrics across booths
            booth_health_scores = [b.health_score for b in booths if b.health_score is not None]
            contact_rates = [b.contact_rate for b in booths if b.contact_rate is not None]
            volunteer_coverage_list = []
            risk_scores = [b.risk_score for b in booths if b.risk_score is not None]

            if not booth_health_scores or not contact_rates:
                raise PredictionNotAvailable("Insufficient booth data for prediction")

            booth_health_avg = sum(booth_health_scores) / len(booth_health_scores)
            contact_rate_avg = sum(contact_rates) / len(contact_rates)
            risk_avg = sum(risk_scores) / len(risk_scores) if risk_scores else 50.0

            # Get voter sentiment from mood analyzer
            voter_sentiment_score = await self._get_constituency_sentiment(db, constituency_id)

            # Get news sentiment trend
            news_sentiment_trend = await self._get_news_sentiment_trend(db, constituency_id)

            # Estimate volunteer coverage
            volunteer_coverage = await self._estimate_volunteer_coverage(db, constituency_id)

            # Calculate win probability
            win_prob = self.win_prob_calc.calculate_win_probability(
                booth_health_avg=booth_health_avg,
                voter_sentiment_score=voter_sentiment_score,
                contact_rate_avg=contact_rate_avg,
                volunteer_coverage=volunteer_coverage,
                news_sentiment_trend=news_sentiment_trend,
            )

            # Calculate confidence interval
            data_quality_score = min(len(booths) / 100.0, 1.0)
            lower, upper = self.win_prob_calc.calculate_confidence_interval(
                base_probability=win_prob,
                sample_size=len(booths),
                data_quality_score=data_quality_score,
            )

            # Determine trend
            prev_win_prob = None  # Could load from history
            trend = self.win_prob_calc.calculate_probability_trend(win_prob, prev_win_prob)

            # Identify key factors
            key_factors = self.win_prob_calc.identify_key_factors(
                booth_health_avg,
                voter_sentiment_score,
                contact_rate_avg,
                volunteer_coverage,
                news_sentiment_trend,
            )

            components = {
                "booth_health": booth_health_avg,
                "voter_sentiment": voter_sentiment_score,
                "contact_rate": contact_rate_avg,
                "volunteer_coverage": volunteer_coverage,
                "news_sentiment": news_sentiment_trend,
            }

            # Optional: booth breakdown
            by_booth = None
            if include_booth_breakdown:
                by_booth = await self._predict_booth_probabilities(db, booths)

            return WinProbabilityResponse(
                overall_probability=win_prob,
                confidence_interval=(lower, upper),
                trend=trend,
                components=components,
                by_booth=by_booth,
                last_updated=datetime.now(),
            )

        except PredictionNotAvailable:
            raise
        except Exception as e:
            logger.error(f"Error calculating win probability: {e}")
            raise PredictionNotAvailable(f"Prediction failed: {str(e)}")

    async def get_sentiment_breakdown(
        self,
        db: AsyncSession,
        constituency_id: UUID,
    ) -> SentimentBreakdownResponse:
        """
        Get voter sentiment breakdown by zone and demographic.

        Args:
            db: Database session
            constituency_id: Constituency ID

        Returns:
            SentimentBreakdownResponse with zonal and demographic breakdowns
        """
        try:
            # Get zone sentiments
            zone_sentiments = await self._get_zone_sentiments(db, constituency_id)

            # Get demographic sentiments
            demo_sentiments = await self._get_demographic_sentiments(db, constituency_id)

            # Calculate overall sentiment
            all_sentiments = list(zone_sentiments.values()) + [
                v.get("sentiment", 0) for v in demo_sentiments.values()
            ]
            overall_sentiment = sum(all_sentiments) / len(all_sentiments) if all_sentiments else 0.0

            # Calculate distribution
            positive = sum(1 for s in all_sentiments if s > 0.3)
            negative = sum(1 for s in all_sentiments if s < -0.3)
            neutral = len(all_sentiments) - positive - negative

            distribution = {
                "POSITIVE": (positive / len(all_sentiments) * 100) if all_sentiments else 0,
                "NEUTRAL": (neutral / len(all_sentiments) * 100) if all_sentiments else 0,
                "NEGATIVE": (negative / len(all_sentiments) * 100) if all_sentiments else 0,
            }

            return SentimentBreakdownResponse(
                overall_sentiment=overall_sentiment,
                by_zone=zone_sentiments,
                by_demographic=demo_sentiments,
                distribution=distribution,
                last_updated=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Error in sentiment breakdown: {e}")
            raise ForecastingError(f"Sentiment analysis failed: {str(e)}")

    async def get_sentiment_forecast(
        self,
        db: AsyncSession,
        constituency_id: UUID,
        forecast_days: int = 7,
    ) -> SentimentForecastResponse:
        """
        Forecast voter sentiment for next N days.

        Args:
            db: Database session
            constituency_id: Constituency ID
            forecast_days: Number of days to forecast

        Returns:
            SentimentForecastResponse with forecasted values
        """
        try:
            # Get historical sentiment data
            historical = await self._get_historical_sentiment(db, constituency_id)

            if not historical or len(historical) < 3:
                raise PredictionNotAvailable("Insufficient historical sentiment data")

            # Current sentiment
            current_sentiment = historical[-1][1]

            # Forecast using linear regression
            forecasts = self.sentiment_forecaster.forecast_sentiment_linear(
                historical,
                forecast_days=forecast_days,
            )

            # Calculate metrics
            momentum = self.sentiment_forecaster.calculate_momentum(historical)
            volatility = self.sentiment_forecaster.calculate_volatility(historical)
            trend = self.sentiment_forecaster.classify_trend(
                current_sentiment,
                momentum=momentum,
            )

            # Calculate confidence
            forecast_confidence = self.sentiment_forecaster.calculate_forecast_confidence(
                historical_count=len(historical),
                data_recency_days=0,  # Assuming latest data
                volatility=volatility,
            )

            # Convert forecasts to response format
            from app.prediction_sentiment.models import ForecastDataPoint

            forecast_data = [
                ForecastDataPoint(
                    timestamp=ts,
                    value=sentiment,
                    confidence_lower=sentiment - (1.0 - forecast_confidence),
                    confidence_upper=sentiment + (1.0 - forecast_confidence),
                )
                for ts, sentiment in forecasts
            ]

            return SentimentForecastResponse(
                current_sentiment=current_sentiment,
                forecast=forecast_data,
                trend=trend,
                forecast_confidence=forecast_confidence,
                aggregation_level="constituency",
                last_updated=datetime.now(),
            )

        except PredictionNotAvailable:
            raise
        except Exception as e:
            logger.error(f"Error in sentiment forecast: {e}")
            raise ForecastingError(f"Forecasting failed: {str(e)}")

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _get_constituency_sentiment(
        self,
        db: AsyncSession,
        constituency_id: UUID,
    ) -> float:
        """Get average voter sentiment for constituency from field reports."""
        stmt = (
            select(func.avg(FieldReport.mood))
            .select_from(FieldReport)
            .join(Booth)
            .where(Booth.constituency_id == constituency_id)
            .where(FieldReport.created_at >= datetime.now() - timedelta(days=30))
        )
        result = await db.execute(stmt)
        avg_mood = result.scalar()

        # Map mood (POSITIVE/NEGATIVE/NEUTRAL) to -1..1 scale
        if avg_mood is None:
            return 0.0

        mood_map = {"POSITIVE": 0.7, "NEUTRAL": 0.0, "NEGATIVE": -0.7, "MIXED": 0.0}
        return mood_map.get(str(avg_mood), 0.0)

    async def _get_news_sentiment_trend(
        self,
        db: AsyncSession,
        constituency_id: UUID,
    ) -> float:
        """Get news sentiment trend from articles."""
        stmt = (
            select(func.avg(Article.sentiment_score))
            .where(Article.created_at >= datetime.now() - timedelta(days=7))
        )
        result = await db.execute(stmt)
        avg_sentiment = result.scalar()

        return avg_sentiment if avg_sentiment else 0.0

    async def _estimate_volunteer_coverage(
        self,
        db: AsyncSession,
        constituency_id: UUID,
    ) -> float:
        """Estimate volunteer coverage for constituency."""
        stmt = (
            select(func.count(FieldReport.id))
            .select_from(FieldReport)
            .join(Booth)
            .where(Booth.constituency_id == constituency_id)
        )
        result = await db.execute(stmt)
        volunteer_count = result.scalar() or 0

        stmt = select(func.count(Booth.id)).where(Booth.constituency_id == constituency_id)
        result = await db.execute(stmt)
        booth_count = result.scalar() or 1

        # Simple: volunteer_count / booth_count ratio
        coverage = min(volunteer_count / (booth_count * 5), 1.0)
        return coverage

    async def _predict_booth_probabilities(
        self,
        db: AsyncSession,
        booths: list,
    ) -> list:
        """Predict win probability for each booth."""
        from app.prediction_sentiment.models import BoothPredictionResponse

        predictions = []
        for booth in booths[:10]:  # Limit to first 10 for performance
            prob = self.win_prob_calc.calculate_booth_win_probability(
                booth_health=booth.health_score,
                booth_contact_rate=booth.contact_rate,
                booth_volunteer_coverage=0.5,  # Placeholder
                booth_sentiment=0.0,  # Placeholder
                booth_risk_score=booth.risk_score,
            )

            trend = "stable"  # Placeholder
            factors = ["Booth Health", "Contact Rate", "Volunteer Coverage"]

            predictions.append(
                BoothPredictionResponse(
                    booth_id=booth.id,
                    booth_number=booth.booth_number,
                    win_probability=prob,
                    confidence=0.75,
                    trend=trend,
                    primary_factors=factors,
                )
            )

        return predictions

    async def _get_zone_sentiments(self, db: AsyncSession, constituency_id: UUID) -> dict:
        """Get sentiment by zone."""
        # Placeholder: could integrate with Session 04 MoodAnalyzer
        return {}

    async def _get_demographic_sentiments(self, db: AsyncSession, constituency_id: UUID) -> dict:
        """Get sentiment by demographic."""
        # Placeholder: would analyze field reports by demographic
        return {}

    async def _get_historical_sentiment(
        self,
        db: AsyncSession,
        constituency_id: UUID,
    ) -> list[tuple[datetime, float]]:
        """Get historical sentiment data as time series."""
        # Placeholder: would query aggregated sentiment history
        now = datetime.now()
        return [
            (now - timedelta(days=7), 0.2),
            (now - timedelta(days=6), 0.25),
            (now - timedelta(days=5), 0.3),
            (now - timedelta(days=4), 0.35),
            (now - timedelta(days=3), 0.4),
            (now - timedelta(days=2), 0.45),
            (now - timedelta(days=1), 0.5),
        ]
