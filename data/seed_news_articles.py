"""
Seed script: inserts sample news articles into news_articles table.
Run inside the container: python data/seed_news_articles.py
"""
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database_design.models import NewsArticle

SAMPLE_ARTICLES = [
    {
        "title": "Infrastructure development in Serilingampally sees major boost",
        "url": "https://thehindu.com/news/cities/hyderabad/serilingampally-infra-boost/article1",
        "feed_source": "The Hindu",
        "feed_tier": 1,
        "sentiment_polarity": 0.65,
        "political_tone": "PRO_INCUMBENT",
        "impact_score": 8.2,
        "entity_tags": {
            "candidates": [],
            "parties": ["TRS", "Congress"],
            "issues": ["infrastructure", "development"],
            "locations": ["Serilingampally", "Hyderabad"],
        },
        "language": "en",
        "narrative_cluster": "infrastructure-development",
        "body_excerpt": (
            "The Serilingampally constituency has witnessed a significant boost in "
            "infrastructure development with new roads and flyovers being inaugurated. "
            "The incumbent MLA lauded the progress as a sign of the government's commitment."
        ),
        "days_ago": 1,
    },
    {
        "title": "Opposition party holds rally in Chandanagar, alleges corruption",
        "url": "https://thehindu.com/news/cities/hyderabad/chandanagar-rally-corruption/article2",
        "feed_source": "The Hindu",
        "feed_tier": 1,
        "sentiment_polarity": -0.55,
        "political_tone": "ANTI_INCUMBENT",
        "impact_score": 7.1,
        "entity_tags": {
            "candidates": [],
            "parties": ["BJP", "TRS"],
            "issues": ["corruption", "accountability"],
            "locations": ["Chandanagar", "Serilingampally"],
        },
        "language": "en",
        "narrative_cluster": "opposition-allegations",
        "body_excerpt": (
            "The opposition party held a large rally in Chandanagar today, with party leaders "
            "alleging widespread corruption in the constituency. They demanded a CBI inquiry "
            "into infrastructure contracts awarded over the past two years."
        ),
        "days_ago": 2,
    },
    {
        "title": "Voter turnout expected to be high in upcoming by-elections",
        "url": "https://ndtv.com/india-news/serilingampally-voter-turnout-high/article3",
        "feed_source": "NDTV",
        "feed_tier": 1,
        "sentiment_polarity": 0.12,
        "political_tone": "NEUTRAL",
        "impact_score": 5.8,
        "entity_tags": {
            "candidates": [],
            "parties": [],
            "issues": ["elections", "voter-turnout"],
            "locations": ["Serilingampally"],
        },
        "language": "en",
        "narrative_cluster": "election-activity",
        "body_excerpt": (
            "Political analysts predict high voter turnout in the upcoming Serilingampally "
            "by-elections. Booth-level surveys indicate increased voter enthusiasm compared "
            "to the previous election cycle."
        ),
        "days_ago": 3,
    },
    {
        "title": "నేర్చుకోవడానికి సెరిలింగంపల్లిలో కొత్త పాఠశాల నిర్మించబడింది",
        "url": "https://sakshi.com/news/ap/serilingampally-new-school/article4",
        "feed_source": "Sakshi",
        "feed_tier": 1,
        "sentiment_polarity": 0.72,
        "political_tone": "PRO_INCUMBENT",
        "impact_score": 6.3,
        "entity_tags": {
            "candidates": [],
            "parties": ["TRS"],
            "issues": ["education", "development"],
            "locations": ["Serilingampally"],
        },
        "language": "te",
        "narrative_cluster": "infrastructure-development",
        "body_excerpt": (
            "సెరిలింగంపల్లి నియోజకవర్గంలో కొత్త ప్రభుత్వ పాఠశాల నిర్మాణం పూర్తైంది. "
            "ఇందులో 500 మంది విద్యార్థులకు చదువుకునే అవకాశం ఉంటుంది."
        ),
        "days_ago": 4,
    },
    {
        "title": "Youth wing protest over unemployment in constituency",
        "url": "https://deccanchronicle.com/news/hyderabad/youth-protest-unemployment/article5",
        "feed_source": "Deccan Chronicle",
        "feed_tier": 2,
        "sentiment_polarity": -0.42,
        "political_tone": "ANTI_INCUMBENT",
        "impact_score": 4.9,
        "entity_tags": {
            "candidates": [],
            "parties": ["Congress"],
            "issues": ["unemployment", "youth"],
            "locations": ["Serilingampally", "Hyderabad"],
        },
        "language": "en",
        "narrative_cluster": "opposition-allegations",
        "body_excerpt": (
            "Youth wing members of the opposition held a protest march demanding "
            "employment opportunities in Serilingampally. They presented a memorandum "
            "to the constituency office highlighting rising unemployment figures."
        ),
        "days_ago": 5,
    },
    {
        "title": "New water supply project benefits 50,000 residents in zone 3",
        "url": "https://namaste-telangana.com/news/serilingampally-water-project/article6",
        "feed_source": "Namaste Telangana",
        "feed_tier": 3,
        "sentiment_polarity": 0.81,
        "political_tone": "PRO_INCUMBENT",
        "impact_score": 5.5,
        "entity_tags": {
            "candidates": [],
            "parties": ["TRS"],
            "issues": ["water-supply", "infrastructure"],
            "locations": ["Serilingampally", "Zone-3"],
        },
        "language": "en",
        "narrative_cluster": "infrastructure-development",
        "body_excerpt": (
            "A new water supply pipeline project has been inaugurated in Zone 3 of "
            "Serilingampally, benefiting over 50,000 residents. The project was funded "
            "by the state government under the Nal Se Jal scheme."
        ),
        "days_ago": 6,
    },
    {
        "title": "Campaign finance irregularities alleged by opposition leaders",
        "url": "https://hansindia.com/news/politics/serilingampally-campaign-finance/article7",
        "feed_source": "Hans India",
        "feed_tier": 3,
        "sentiment_polarity": -0.68,
        "political_tone": "ANTI_INCUMBENT",
        "impact_score": 6.8,
        "entity_tags": {
            "candidates": [],
            "parties": ["BJP", "Congress"],
            "issues": ["corruption", "campaign-finance"],
            "locations": ["Serilingampally"],
        },
        "language": "en",
        "narrative_cluster": "opposition-allegations",
        "body_excerpt": (
            "Opposition party leaders have filed a complaint with the Election Commission "
            "alleging campaign finance irregularities in Serilingampally constituency. "
            "They claim undisclosed funds were used in booth-level voter outreach programs."
        ),
        "days_ago": 0,
    },
    {
        "title": "Serilingampally sees surge in voter registration drives",
        "url": "https://siasat.com/news/serilingampally-voter-registration/article8",
        "feed_source": "Siasat Daily",
        "feed_tier": 3,
        "sentiment_polarity": 0.28,
        "political_tone": "NEUTRAL",
        "impact_score": 4.1,
        "entity_tags": {
            "candidates": [],
            "parties": [],
            "issues": ["elections", "voter-registration"],
            "locations": ["Serilingampally"],
        },
        "language": "en",
        "narrative_cluster": "election-activity",
        "body_excerpt": (
            "Voter registration drives in Serilingampally have seen a significant surge, "
            "with over 12,000 new voters added to electoral rolls in the past month. "
            "Civil society organizations and all major political parties participated."
        ),
        "days_ago": 2,
    },
]


async def seed():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        now = datetime.now(timezone.utc)
        added = 0

        for data in SAMPLE_ARTICLES:
            days_ago = data.pop("days_ago")
            pub_at = now - timedelta(days=days_ago, hours=3)

            from sqlalchemy import select
            existing = await session.execute(
                select(NewsArticle).where(NewsArticle.url == data["url"])
            )
            if existing.scalar():
                print(f"  skip (exists): {data['title'][:60]}")
                continue

            article = NewsArticle(
                published_at=pub_at,
                ingested_at=now - timedelta(days=days_ago),
                processed=True,
                **data,
            )
            session.add(article)
            added += 1
            print(f"  added: {data['title'][:60]}")

        await session.commit()
        print(f"\nDone. {added} articles seeded.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
