"""
Sentiment Forecaster

Time-series sentiment analysis and forecasting.
Predicts voter sentiment trends over future periods.
"""

from datetime import datetime, timedelta
from typing import Optional


class SentimentForecaster:
    """Forecast sentiment trends using simple time-series methods."""

    # Recency weights for smoothing
    RECENT_WEIGHT = 0.5
    HISTORICAL_WEIGHT = 0.5

    @staticmethod
    def calculate_moving_average(
        historical_sentiments: list[tuple[datetime, float]],
        window_days: int = 7,
    ) -> float:
        """
        Calculate moving average sentiment.

        Args:
            historical_sentiments: List of (timestamp, sentiment) tuples
            window_days: Window size in days

        Returns:
            Moving average sentiment (-1 to 1)
        """
        if not historical_sentiments:
            return 0.0

        cutoff_date = datetime.now() - timedelta(days=window_days)
        recent = [s for ts, s in historical_sentiments if ts >= cutoff_date]

        if not recent:
            return 0.0

        return sum(recent) / len(recent)

    @staticmethod
    def calculate_momentum(
        historical_sentiments: list[tuple[datetime, float]],
        recent_days: int = 7,
        historical_days: int = 30,
    ) -> float:
        """
        Calculate sentiment momentum (trend direction and speed).

        Args:
            historical_sentiments: List of (timestamp, sentiment) tuples
            recent_days: Days for recent period
            historical_days: Days for historical period

        Returns:
            Momentum score (-1 to 1, negative = declining)
        """
        if len(historical_sentiments) < 2:
            return 0.0

        now = datetime.now()
        recent_cutoff = now - timedelta(days=recent_days)
        historical_cutoff = now - timedelta(days=historical_days)

        recent = [s for ts, s in historical_sentiments if ts >= recent_cutoff]
        historical = [s for ts, s in historical_sentiments if historical_cutoff <= ts < recent_cutoff]

        if not recent or not historical:
            return 0.0

        recent_avg = sum(recent) / len(recent)
        historical_avg = sum(historical) / len(historical)

        momentum = recent_avg - historical_avg
        return max(-1.0, min(1.0, momentum))

    @staticmethod
    def calculate_volatility(
        historical_sentiments: list[tuple[datetime, float]],
        window_days: int = 30,
    ) -> float:
        """
        Calculate sentiment volatility (standard deviation).

        Args:
            historical_sentiments: List of (timestamp, sentiment) tuples
            window_days: Window size in days

        Returns:
            Volatility (0 to 1, higher = more volatile)
        """
        if len(historical_sentiments) < 2:
            return 0.0

        cutoff_date = datetime.now() - timedelta(days=window_days)
        recent = [s for ts, s in historical_sentiments if ts >= cutoff_date]

        if len(recent) < 2:
            return 0.0

        mean = sum(recent) / len(recent)
        variance = sum((x - mean) ** 2 for x in recent) / len(recent)
        std_dev = variance ** 0.5

        return min(1.0, std_dev)

    @staticmethod
    def forecast_sentiment_linear(
        historical_sentiments: list[tuple[datetime, float]],
        forecast_days: int = 7,
    ) -> list[tuple[datetime, float]]:
        """
        Forecast sentiment using simple linear regression.

        Args:
            historical_sentiments: List of (timestamp, sentiment) tuples
            forecast_days: Number of days to forecast

        Returns:
            List of (future_date, predicted_sentiment) tuples
        """
        if len(historical_sentiments) < 2:
            current = datetime.now()
            return [(current + timedelta(days=i), 0.0) for i in range(1, forecast_days + 1)]

        # Convert timestamps to numeric (days since start)
        start_date = historical_sentiments[0][0]
        x_values = [(ts - start_date).days for ts, _ in historical_sentiments]
        y_values = [s for _, s in historical_sentiments]

        # Simple linear regression
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x ** 2 for x in x_values)

        if sum_x2 - (sum_x ** 2) / n == 0:
            # Flat trend
            slope = 0.0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)

        intercept = (sum_y - slope * sum_x) / n

        # Generate forecasts
        last_date = historical_sentiments[-1][0]
        last_x = x_values[-1]
        forecasts = []

        for i in range(1, forecast_days + 1):
            future_date = last_date + timedelta(days=i)
            future_x = last_x + i
            predicted_sentiment = intercept + slope * future_x
            predicted_sentiment = max(-1.0, min(1.0, predicted_sentiment))
            forecasts.append((future_date, predicted_sentiment))

        return forecasts

    @staticmethod
    def forecast_sentiment_exponential_smoothing(
        historical_sentiments: list[tuple[datetime, float]],
        forecast_days: int = 7,
        alpha: float = 0.3,
    ) -> list[tuple[datetime, float]]:
        """
        Forecast sentiment using exponential smoothing.

        Args:
            historical_sentiments: List of (timestamp, sentiment) tuples
            forecast_days: Number of days to forecast
            alpha: Smoothing factor (0-1, higher = more weight on recent)

        Returns:
            List of (future_date, predicted_sentiment) tuples
        """
        if not historical_sentiments:
            current = datetime.now()
            return [(current + timedelta(days=i), 0.0) for i in range(1, forecast_days + 1)]

        sentiments = [s for _, s in historical_sentiments]

        # Initialize smoothed value
        smoothed = sentiments[0]
        smoothed_values = [smoothed]

        # Apply exponential smoothing
        for i in range(1, len(sentiments)):
            smoothed = alpha * sentiments[i] + (1 - alpha) * smoothed
            smoothed_values.append(smoothed)

        # Forecast using last smoothed value
        last_date = historical_sentiments[-1][0]
        last_smoothed = smoothed_values[-1]
        forecasts = []

        for i in range(1, forecast_days + 1):
            future_date = last_date + timedelta(days=i)
            # Simple: assume trend continues with decay
            predicted = last_smoothed
            forecasts.append((future_date, predicted))

        return forecasts

    @staticmethod
    def calculate_forecast_confidence(
        historical_count: int,
        data_recency_days: int,
        volatility: float,
    ) -> float:
        """
        Calculate confidence in sentiment forecast.

        Args:
            historical_count: Number of historical data points
            data_recency_days: Days since last data point
            volatility: Sentiment volatility (0-1)

        Returns:
            Confidence score (0-1)
        """
        # Base confidence from data volume
        if historical_count >= 100:
            base_confidence = 0.85
        elif historical_count >= 30:
            base_confidence = 0.70
        elif historical_count >= 10:
            base_confidence = 0.55
        else:
            base_confidence = 0.40

        # Reduce confidence if data is stale
        if data_recency_days > 14:
            base_confidence *= 0.8
        elif data_recency_days > 7:
            base_confidence *= 0.9

        # Reduce confidence if volatile
        base_confidence *= (1.0 - volatility * 0.3)

        return max(0.0, min(1.0, base_confidence))

    @staticmethod
    def classify_trend(
        current_sentiment: float,
        previous_sentiment: Optional[float] = None,
        momentum: Optional[float] = None,
    ) -> str:
        """
        Classify sentiment trend.

        Args:
            current_sentiment: Current sentiment (-1 to 1)
            previous_sentiment: Previous sentiment (-1 to 1)
            momentum: Momentum score (-1 to 1)

        Returns:
            Trend: 'improving', 'stable', or 'declining'
        """
        if previous_sentiment is not None:
            delta = current_sentiment - previous_sentiment
            if delta > 0.1:
                return "improving"
            elif delta < -0.1:
                return "declining"
            else:
                return "stable"
        elif momentum is not None:
            if momentum > 0.1:
                return "improving"
            elif momentum < -0.1:
                return "declining"
            else:
                return "stable"
        else:
            return "stable"
