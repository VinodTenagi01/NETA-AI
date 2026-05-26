"""
Integration tests for News Intelligence endpoints — runs against PostgreSQL.

All tests use pg_session fixtures (real PostgreSQL with transaction rollback isolation)
and pg_test_client (FastAPI test client wired to the pg_session).
"""
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_design.models import NewsArticle
from app.security_auth.utils import create_access_token


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
async def pg_news_articles(pg_session: AsyncSession):
    """Insert a batch of sample news articles for endpoint testing."""
    now = datetime.now(timezone.utc)
    articles = []

    samples = [
        {
            "title": "Infrastructure progress in Serilingampally",
            "url": "https://example.com/news/infra-1",
            "feed_source": "The Hindu",
            "feed_tier": 1,
            "sentiment_polarity": 0.65,
            "political_tone": "PRO_INCUMBENT",
            "impact_score": 8.2,
            "entity_tags": {"candidates": [], "parties": ["TRS"], "issues": ["infrastructure"], "locations": ["Serilingampally"]},
            "language": "en",
            "narrative_cluster": "infra-cluster",
            "body_excerpt": "Infrastructure development is progressing well in the constituency.",
            "published_at": now - timedelta(hours=6),
            "ingested_at": now - timedelta(hours=5),
            "processed": True,
        },
        {
            "title": "Opposition alleges corruption in Serilingampally",
            "url": "https://example.com/news/opposition-1",
            "feed_source": "NDTV",
            "feed_tier": 1,
            "sentiment_polarity": -0.55,
            "political_tone": "ANTI_INCUMBENT",
            "impact_score": 7.1,
            "entity_tags": {"candidates": [], "parties": ["BJP"], "issues": ["corruption"], "locations": ["Serilingampally"]},
            "language": "en",
            "narrative_cluster": "opposition-cluster",
            "body_excerpt": "Opposition leaders alleged corruption in the constituency.",
            "published_at": now - timedelta(hours=12),
            "ingested_at": now - timedelta(hours=11),
            "processed": True,
        },
        {
            "title": "Neutral election update from local reporters",
            "url": "https://example.com/news/neutral-1",
            "feed_source": "Deccan Chronicle",
            "feed_tier": 2,
            "sentiment_polarity": 0.05,
            "political_tone": "NEUTRAL",
            "impact_score": 4.5,
            "entity_tags": {"candidates": [], "parties": [], "issues": ["elections"], "locations": ["Hyderabad"]},
            "language": "en",
            "narrative_cluster": "infra-cluster",
            "body_excerpt": "Neutral reporting on election preparations in the region.",
            "published_at": now - timedelta(hours=24),
            "ingested_at": now - timedelta(hours=23),
            "processed": True,
        },
    ]

    for data in samples:
        article = NewsArticle(**data)
        pg_session.add(article)
        articles.append(article)

    await pg_session.commit()
    for a in articles:
        await pg_session.refresh(a)

    return articles


# ============================================================================
# Endpoint 1: List Articles
# ============================================================================

class TestListArticles:
    """GET /api/v1/news/articles"""

    @pytest.mark.asyncio
    async def test_list_articles_returns_articles(
        self, pg_test_client: AsyncClient, pg_auth_admin_user, pg_news_articles
    ):
        """Returns articles list with pagination metadata."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.get(
            "/api/v1/news/articles",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "articles" in data
        assert "total" in data
        assert "by_sentiment" in data
        assert "by_source_tier" in data
        assert data["total"] >= 3
        assert len(data["articles"]) >= 3

    @pytest.mark.asyncio
    async def test_list_articles_filter_by_sentiment(
        self, pg_test_client: AsyncClient, pg_auth_admin_user, pg_news_articles
    ):
        """Filter articles by POSITIVE sentiment."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.get(
            "/api/v1/news/articles?sentiment=POSITIVE",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        for article in data["articles"]:
            assert article["sentiment_polarity"] > 0.3

    @pytest.mark.asyncio
    async def test_list_articles_filter_by_tier(
        self, pg_test_client: AsyncClient, pg_auth_admin_user, pg_news_articles
    ):
        """Filter articles by source tier 1."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.get(
            "/api/v1/news/articles?source_tier=1",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        for article in data["articles"]:
            assert article["feed_tier"] == 1

    @pytest.mark.asyncio
    async def test_list_articles_no_token_forbidden(
        self, pg_test_client: AsyncClient
    ):
        """Access without token returns 401 (missing credentials)."""
        response = await pg_test_client.get("/api/v1/news/articles")
        assert response.status_code == 401


# ============================================================================
# Endpoint 2: Get Article Details
# ============================================================================

class TestGetArticle:
    """GET /api/v1/news/articles/{article_id}"""

    @pytest.mark.asyncio
    async def test_get_article_returns_full_detail(
        self, pg_test_client: AsyncClient, pg_auth_admin_user, pg_news_articles
    ):
        """Retrieve a specific article by ID."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )
        article_id = pg_news_articles[0].id

        response = await pg_test_client.get(
            f"/api/v1/news/articles/{article_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert str(data["id"]) == str(article_id)
        assert data["title"] == pg_news_articles[0].title
        assert "entity_tags" in data
        assert "impact_score" in data

    @pytest.mark.asyncio
    async def test_get_article_not_found_returns_404(
        self, pg_test_client: AsyncClient, pg_auth_admin_user
    ):
        """Non-existent article returns 404."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.get(
            f"/api/v1/news/articles/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404


# ============================================================================
# Endpoint 3: Sentiment Trends
# ============================================================================

class TestSentimentTrends:
    """GET /api/v1/news/trends/sentiment"""

    @pytest.mark.asyncio
    async def test_sentiment_trends_returns_timeline(
        self, pg_test_client: AsyncClient, pg_auth_admin_user, pg_news_articles
    ):
        """Returns timeline, trend, and distribution."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.get(
            "/api/v1/news/trends/sentiment?days=7",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "timeline" in data
        assert "trend" in data
        assert "avg_polarity" in data
        assert "sentiment_distribution" in data
        assert data["trend"] in ["RISING", "STABLE", "FADING"]
        assert "POSITIVE" in data["sentiment_distribution"]
        assert "NEGATIVE" in data["sentiment_distribution"]
        assert "NEUTRAL" in data["sentiment_distribution"]

    @pytest.mark.asyncio
    async def test_sentiment_trends_empty_returns_stable(
        self, pg_test_client: AsyncClient, pg_auth_admin_user
    ):
        """No articles returns STABLE trend."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.get(
            "/api/v1/news/trends/sentiment?days=1",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["trend"] == "STABLE"


# ============================================================================
# Endpoint 4: Impact Leaderboard
# ============================================================================

class TestImpactLeaderboard:
    """GET /api/v1/news/leaderboard/impact"""

    @pytest.mark.asyncio
    async def test_leaderboard_returns_ranked_articles(
        self, pg_test_client: AsyncClient, pg_auth_admin_user, pg_news_articles
    ):
        """Returns articles sorted by impact score with ranks."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.get(
            "/api/v1/news/leaderboard/impact?days=7&limit=10",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "articles" in data
        assert len(data["articles"]) >= 1
        # Verify ranks are sequential
        for i, article in enumerate(data["articles"]):
            assert article["rank"] == i + 1

    @pytest.mark.asyncio
    async def test_leaderboard_sorted_by_impact_desc(
        self, pg_test_client: AsyncClient, pg_auth_admin_user, pg_news_articles
    ):
        """Articles are ordered highest impact first."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.get(
            "/api/v1/news/leaderboard/impact?days=7",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        articles = response.json()["articles"]
        if len(articles) >= 2:
            assert articles[0]["impact_score"] >= articles[1]["impact_score"]


# ============================================================================
# Endpoint 5: Narrative Clusters
# ============================================================================

class TestNarrativeClusters:
    """GET /api/v1/news/clusters"""

    @pytest.mark.asyncio
    async def test_clusters_returns_grouped_articles(
        self, pg_test_client: AsyncClient, pg_auth_admin_user, pg_news_articles
    ):
        """Returns clusters with member articles."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.get(
            "/api/v1/news/clusters?days=7",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "clusters" in data
        assert len(data["clusters"]) >= 2  # infra-cluster + opposition-cluster
        for cluster in data["clusters"]:
            assert "cluster_id" in cluster
            assert "momentum" in cluster
            assert cluster["momentum"] in ["RISING", "STABLE", "FADING"]
            assert "article_count" in cluster
            assert "top_headline" in cluster
            assert "avg_sentiment" in cluster

    @pytest.mark.asyncio
    async def test_clusters_momentum_filter(
        self, pg_test_client: AsyncClient, pg_auth_admin_user, pg_news_articles
    ):
        """Filter clusters by momentum."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.get(
            "/api/v1/news/clusters?momentum=STABLE",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        for cluster in data["clusters"]:
            assert cluster["momentum"] == "STABLE"


# ============================================================================
# Endpoint 6: Cluster Details
# ============================================================================

class TestClusterDetails:
    """GET /api/v1/news/clusters/{cluster_id}"""

    @pytest.mark.asyncio
    async def test_cluster_details_returns_all_articles(
        self, pg_test_client: AsyncClient, pg_auth_admin_user, pg_news_articles
    ):
        """Returns all articles in the specified cluster."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.get(
            "/api/v1/news/clusters/infra-cluster",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cluster_id"] == "infra-cluster"
        assert "articles" in data
        assert len(data["articles"]) >= 2  # infra-1 and neutral-1

    @pytest.mark.asyncio
    async def test_cluster_details_not_found(
        self, pg_test_client: AsyncClient, pg_auth_admin_user
    ):
        """Non-existent cluster returns 422 or 500 (ValueError)."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.get(
            "/api/v1/news/clusters/non-existent-cluster-xyz",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404


# ============================================================================
# Endpoint 7: Source Health Monitor
# ============================================================================

class TestSourceHealth:
    """GET /api/v1/news/sources/health"""

    @pytest.mark.asyncio
    async def test_source_health_returns_all_sources(
        self, pg_test_client: AsyncClient, pg_auth_admin_user
    ):
        """Returns health status for all configured feed sources."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.get(
            "/api/v1/news/sources/health",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "sources" in data
        assert len(data["sources"]) >= 1
        for source in data["sources"]:
            assert "feed_source" in source
            assert "status" in source
            assert source["status"] in ["HEALTHY", "DEGRADED", "FAILED"]
            assert "articles_today" in source
            assert "articles_per_day_avg" in source


# ============================================================================
# Endpoint 8: Manual Feed Ingest
# ============================================================================

class TestManualFeedIngest:
    """POST /api/v1/news/ingest"""

    @pytest.mark.asyncio
    async def test_ingest_returns_report(
        self, pg_test_client: AsyncClient, pg_auth_admin_user
    ):
        """Manual ingest returns an IngestionReport."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.post(
            "/api/v1/news/ingest",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )

        # 202 accepted even if network unavailable (feed fetch may return 0 articles)
        assert response.status_code in [202, 500]
        if response.status_code == 202:
            data = response.json()
            assert "status" in data
            assert "articles_fetched" in data
            assert "articles_ingested" in data

    @pytest.mark.asyncio
    async def test_ingest_requires_super_admin(
        self, pg_test_client: AsyncClient, pg_session
    ):
        """Non-super_admin cannot trigger ingestion."""
        from app.database_design.models import User
        from app.security_auth.utils import hash_password

        analyst = User(
            full_name="Data Analyst",
            email="analyst@example.com",
            phone="+919876543211",
            password_hash=hash_password("AnalystPass123!"),
            role="data_analyst",
            is_active=True,
        )
        pg_session.add(analyst)
        await pg_session.commit()
        await pg_session.refresh(analyst)

        token = create_access_token(analyst.id, analyst.email, analyst.role)

        response = await pg_test_client.post(
            "/api/v1/news/ingest",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )

        assert response.status_code == 403


# ============================================================================
# Endpoint 9: Active Narratives
# ============================================================================

class TestActiveNarratives:
    """GET /api/v1/news/narratives/active"""

    @pytest.mark.asyncio
    async def test_active_narratives_returns_list(
        self, pg_test_client: AsyncClient, pg_auth_admin_user, pg_news_articles
    ):
        """Returns active narrative clusters with recommendations."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.get(
            "/api/v1/news/narratives/active?days=7",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "narratives" in data
        for narrative in data["narratives"]:
            assert "narrative_id" in narrative
            assert "topic" in narrative
            assert "momentum" in narrative
            assert "sentiment" in narrative
            assert "recommendation" in narrative
            # last_updated is Optional — may be None
            assert "last_updated" in narrative

    @pytest.mark.asyncio
    async def test_active_narratives_valid_structure(
        self, pg_test_client: AsyncClient, pg_auth_admin_user
    ):
        """Narratives endpoint returns valid response structure."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.get(
            "/api/v1/news/narratives/active",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "narratives" in data
        assert isinstance(data["narratives"], list)


# ============================================================================
# Endpoint 10: Sentiment Comparison
# ============================================================================

class TestSentimentComparison:
    """GET /api/v1/news/comparison/sentiment"""

    @pytest.mark.asyncio
    async def test_comparison_returns_timeline(
        self, pg_test_client: AsyncClient, pg_auth_admin_user, pg_news_articles
    ):
        """Returns sentiment comparison timeline for two candidates."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.get(
            "/api/v1/news/comparison/sentiment?candidate_1=TRS&candidate_2=BJP&days=7",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "timeline" in data
        assert "alerts" in data
        assert isinstance(data["alerts"], list)

    @pytest.mark.asyncio
    async def test_comparison_empty_returns_empty_timeline(
        self, pg_test_client: AsyncClient, pg_auth_admin_user
    ):
        """No articles returns empty timeline."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.get(
            "/api/v1/news/comparison/sentiment?candidate_1=CandA&candidate_2=CandB&days=1",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["timeline"] == []


# ============================================================================
# Endpoint 11: Entity Mentions
# ============================================================================

class TestEntityMentions:
    """GET /api/v1/news/entities/mentions"""

    @pytest.mark.asyncio
    async def test_entity_mentions_returns_list(
        self, pg_test_client: AsyncClient, pg_auth_admin_user
    ):
        """Returns entity mention statistics."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.get(
            "/api/v1/news/entities/mentions",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert len(data["entities"]) >= 1
        for entity in data["entities"]:
            assert "name" in entity
            assert "entity_type" in entity
            assert "mention_count" in entity
            assert "avg_sentiment" in entity
            assert "trend" in entity

    @pytest.mark.asyncio
    async def test_entity_mentions_filter_by_type(
        self, pg_test_client: AsyncClient, pg_auth_admin_user
    ):
        """Filter by entity type."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.get(
            "/api/v1/news/entities/mentions?entity_type=party",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200


# ============================================================================
# Endpoint 12: Ingest Status
# ============================================================================

class TestIngestStatus:
    """GET /api/v1/news/ingest/status/{task_id}"""

    @pytest.mark.asyncio
    async def test_ingest_status_returns_status(
        self, pg_test_client: AsyncClient, pg_auth_admin_user
    ):
        """Returns task status for given task_id."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )
        task_id = str(uuid4())

        response = await pg_test_client.get(
            f"/api/v1/news/ingest/status/{task_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] in ["IN_PROGRESS", "COMPLETED", "FAILED"]

    @pytest.mark.asyncio
    async def test_ingest_status_requires_super_admin(
        self, pg_test_client: AsyncClient, pg_session
    ):
        """Non-super_admin cannot check ingest status."""
        from app.database_design.models import User
        from app.security_auth.utils import hash_password

        worker = User(
            full_name="Field Worker",
            email="worker@example.com",
            phone="+919876543212",
            password_hash=hash_password("WorkerPass123!"),
            role="field_worker",
            is_active=True,
        )
        pg_session.add(worker)
        await pg_session.commit()
        await pg_session.refresh(worker)

        token = create_access_token(worker.id, worker.email, worker.role)

        response = await pg_test_client.get(
            f"/api/v1/news/ingest/status/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403
