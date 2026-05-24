"""
NLP Processing Service

Provides sentiment analysis, entity extraction, and political tone classification
using IndicBERT or MuRIL models.

Handles Telugu and English text with confidence scoring.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


# Keywords for political tone classification
INCUMBENT_KEYWORDS = {
    "development", "progress", "achievement", "success", "growth", "improvement",
    "investment", "infrastructure", "healthcare", "education", "jobs", "employment",
    "responsible", "competent", "experienced", "track record"
}

OPPOSITION_KEYWORDS = {
    "failure", "mismanagement", "corruption", "inefficient", "incompetent",
    "scandal", "controversy", "broke promise", "unfulfilled", "delay",
    "neglect", "problem", "crisis", "challenge", "opposition"
}

# Entity recognition patterns (simplistic regex for MVP)
CANDIDATE_PATTERNS = [
    r"(?:Mr\.|Ms\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
]

PARTY_PATTERNS = [
    r"(BJP|Congress|YSRCP|BRS|AAP|DMK|AIADMK|TDP|BJD|SP|BSP|CPI|DMK|NCP|Shiv\s+Sena|JDU|RJD)",
]

ISSUE_PATTERNS = [
    r"(?:on\s+|regarding\s+|about\s+|concerning\s+)(development|healthcare|education|agriculture|employment|infrastructure|security|law\s+and\s+order)",
]


class NLPService:
    """
    NLP processing service for sentiment analysis, entity extraction, and tone classification.

    Phase 1: Rule-based heuristics and keyword matching
    Phase 2: Integrate IndicBERT/MuRIL models from HuggingFace
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize NLP service.

        Args:
            model_path: Path to pre-trained NLP model (IndicBERT/MuRIL)
                       If None, use rule-based heuristics
        """
        self.model_path = model_path
        self.model = None
        self.tokenizer = None

        # Phase 2: Load model if provided
        if model_path:
            try:
                from transformers import AutoTokenizer, AutoModelForSequenceClassification

                logger.info(f"Loading NLP model from {model_path}")
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
                logger.info("NLP model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load NLP model: {e}. Falling back to heuristics.")

    def analyze_sentiment(self, text: str) -> dict:
        """
        Analyze sentiment of text.

        Args:
            text: Article text or excerpt

        Returns:
            dict: {"polarity": float (-1.0 to 1.0), "confidence": float (0.0 to 1.0)}
        """
        if not text or len(text.strip()) < 10:
            return {"polarity": 0.0, "confidence": 0.5}

        # Phase 2: Use model if available
        if self.model and self.tokenizer:
            try:
                import torch

                # Tokenize and truncate
                inputs = self.tokenizer(
                    text[:512],
                    return_tensors="pt",
                    truncation=True,
                    max_length=512,
                )

                # Inference
                with torch.no_grad():
                    outputs = self.model(**inputs)

                # Extract polarity (assuming labels 0=negative, 1=neutral, 2=positive)
                logits = outputs.logits[0]
                probabilities = torch.softmax(logits, dim=0)
                predicted_class = torch.argmax(logits).item()

                confidence = probabilities[predicted_class].item()
                polarity = (predicted_class - 1.0) * 0.5  # Map 0,1,2 to -0.5, 0.0, 0.5

                return {"polarity": float(polarity), "confidence": float(confidence)}

            except Exception as e:
                logger.error(f"Model inference failed: {e}. Using heuristics.")

        # Phase 1: Rule-based heuristics
        text_lower = text.lower()
        positive_score = sum(1 for word in ["positive", "good", "excellent", "great", "success"]
                            if word in text_lower)
        negative_score = sum(1 for word in ["negative", "bad", "poor", "failure", "scandal"]
                            if word in text_lower)

        total_score = positive_score + negative_score
        if total_score == 0:
            return {"polarity": 0.0, "confidence": 0.3}

        polarity = (positive_score - negative_score) / max(total_score, 1)
        confidence = min(total_score * 0.1, 1.0)  # Rough confidence estimate

        return {"polarity": float(polarity), "confidence": float(confidence)}

    def classify_political_tone(self, text: str) -> str:
        """
        Classify political tone: PRO_INCUMBENT | NEUTRAL | ANTI_INCUMBENT

        Args:
            text: Article text or excerpt

        Returns:
            str: Political tone classification
        """
        if not text:
            return "NEUTRAL"

        text_lower = text.lower()

        # Count incumbent/opposition keywords
        incumbent_count = sum(1 for keyword in INCUMBENT_KEYWORDS if keyword in text_lower)
        opposition_count = sum(1 for keyword in OPPOSITION_KEYWORDS if keyword in text_lower)

        # Simple heuristic
        if incumbent_count > opposition_count + 1:
            return "PRO_INCUMBENT"
        elif opposition_count > incumbent_count + 1:
            return "ANTI_INCUMBENT"
        else:
            return "NEUTRAL"

    def extract_entities(self, text: str) -> dict:
        """
        Extract named entities from text: candidates, parties, issues, locations.

        Args:
            text: Article text or excerpt

        Returns:
            dict: {"candidates": [...], "parties": [...], "issues": [...], "locations": [...]}
        """
        entities = {
            "candidates": [],
            "parties": [],
            "issues": [],
            "locations": [],
        }

        if not text:
            return entities

        # Extract candidates using regex
        for pattern in CANDIDATE_PATTERNS:
            matches = re.findall(pattern, text)
            entities["candidates"].extend(matches)

        # Extract parties
        for pattern in PARTY_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities["parties"].extend(matches)

        # Extract issues
        for pattern in ISSUE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities["issues"].extend(matches)

        # Extract locations (basic: common Telangana area names)
        locations = [
            "Serilingampally", "Kondapur", "Madhapur", "Gachibowli", "HITEC City",
            "Hafeezpet", "Chandanagar", "Nallagandla", "Hyderabad", "Telangana"
        ]
        entities["locations"] = [loc for loc in locations if loc.lower() in text.lower()]

        # Remove duplicates and limit size
        for key in entities:
            entities[key] = list(set(entities[key]))[:10]

        return entities

    def compute_impact_score(
        self,
        sentiment_polarity: float,
        feed_tier: int,
        hours_since_publication: float = 0.0,
    ) -> float:
        """
        Compute impact score: |polarity| × source_weight × recency_decay × 10

        Args:
            sentiment_polarity: Sentiment score (-1.0 to 1.0)
            feed_tier: Feed tier (1, 2, or 3)
            hours_since_publication: Hours elapsed since article published

        Returns:
            float: Impact score (0.0–10.0)
        """
        # Polarity weight: |polarity| gives 0.0–1.0
        polarity_weight = abs(sentiment_polarity)

        # Source weight
        source_weights = {1: 1.0, 2: 0.7, 3: 0.4}
        source_weight = source_weights.get(feed_tier, 0.4)

        # Recency decay: e^(-0.1 × hours)
        import math
        recency_decay = math.exp(-0.1 * hours_since_publication)

        # Final score
        impact_score = polarity_weight * source_weight * recency_decay * 10.0

        return float(max(0.0, min(10.0, impact_score)))  # Clamp to 0.0–10.0
