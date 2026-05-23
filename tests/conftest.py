"""
Pytest configuration and shared fixtures for testing.
Uses SQLite in-memory with simplified schema for Phase 1 testing.
"""
import asyncio
from typing import AsyncGenerator
from datetime import datetime
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.security_auth.utils import hash_password

# Import test models - using late import to avoid circular dependencies
def _import_test_models():
    import sys
    from pathlib import Path
    tests_dir = Path(__file__).parent
    sys.path.insert(0, str(tests_dir))
    from test_models import Base, User, Constituency, CampaignZone, Booth, FieldReport, Escalation, WorkerAttendance, MoodSnapshot
    return Base, User, Constituency, CampaignZone, Booth, FieldReport, Escalation, WorkerAttendance, MoodSnapshot

Base, User, Constituency, CampaignZone, Booth, FieldReport, Escalation, WorkerAttendance, MoodSnapshot = _import_test_models()


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine (SQLite in-memory)."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    async def setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(setup())
    yield engine

    async def cleanup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    asyncio.run(cleanup())


@pytest.fixture(scope="function")
async def test_db(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create fresh test database session for each test."""
    AsyncSessionLocal = sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def test_client(test_db):
    """Create test FastAPI client with test database."""
    # Override get_db dependency
    async def override_get_db():
        yield test_db

    from app.database_design.database import get_db
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def admin_user(test_db: AsyncSession) -> User:
    """Create test admin user in test database."""
    user = User(
        full_name="Test Admin",
        email=f"admin+{uuid4()}@test.local",
        phone="+919876543210",
        password_hash=hash_password("TestAdmin123!"),
        role="super_admin",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
async def campaign_manager_user(test_db: AsyncSession) -> User:
    """Create test campaign manager user in test database."""
    user = User(
        full_name="Test Manager",
        email=f"manager+{uuid4()}@test.local",
        phone="+919876543211",
        password_hash=hash_password("TestManager123!"),
        role="campaign_manager",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
async def field_worker_user(test_db: AsyncSession) -> User:
    """Create test field worker user in test database."""
    user = User(
        full_name="Test Worker",
        email=f"worker+{uuid4()}@test.local",
        phone="+919876543212",
        password_hash=hash_password("TestWorker123!"),
        role="field_worker",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
async def ground_commander_user(test_db: AsyncSession) -> User:
    """Create test ground commander user in test database."""
    user = User(
        full_name="Test Commander",
        email=f"commander+{uuid4()}@test.local",
        phone="+919876543213",
        password_hash=hash_password("TestCommander123!"),
        role="ground_commander",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
async def test_constituency(test_db: AsyncSession) -> Constituency:
    """Create test constituency."""
    constituency = Constituency(
        ac_number="52",
        name="Serilingampally",
        state="Telangana",
        total_booths=1,
    )
    test_db.add(constituency)
    await test_db.commit()
    await test_db.refresh(constituency)
    return constituency


@pytest.fixture(scope="function")
async def test_zone(test_db: AsyncSession, test_constituency: Constituency, ground_commander_user: User) -> CampaignZone:
    """Create test campaign zone."""
    zone = CampaignZone(
        constituency_id=test_constituency.id,
        zone_code="Z001",
        zone_name="Test Zone",
        assigned_commander_id=ground_commander_user.id,
        total_booths=1,
    )
    test_db.add(zone)
    await test_db.commit()
    await test_db.refresh(zone)
    return zone


@pytest.fixture(scope="function")
async def test_booth(test_db: AsyncSession, test_constituency: Constituency, test_zone: CampaignZone) -> Booth:
    """Create test booth."""
    booth = Booth(
        constituency_id=test_constituency.id,
        zone_id=test_zone.id,
        booth_number="001",
        booth_name="Test Booth",
        total_voters=1000,
    )
    test_db.add(booth)
    await test_db.commit()
    await test_db.refresh(booth)
    return booth
