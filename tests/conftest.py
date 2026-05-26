"""
Pytest configuration and shared fixtures for testing.
Uses SQLite in-memory (via test_models) for unit/endpoint tests.
Uses PostgreSQL with transaction rollback for integration tests.
"""
import asyncio
import os
from typing import AsyncGenerator
from datetime import datetime
from uuid import uuid4

import pytest
from httpx import AsyncClient, ASGITransport
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
def test_db_engine(event_loop):
    """Create test database engine (SQLite in-memory)."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    async def setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # Use the session event loop instead of asyncio.run() to avoid destroying loop state
    event_loop.run_until_complete(setup())
    yield engine

    async def cleanup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    event_loop.run_until_complete(cleanup())


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
    async def override_get_db():
        yield test_db

    from app.database_design.database import get_db
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# ============================================================================
# SQLite-based fixtures (for unit tests and auth endpoint tests)
# ============================================================================

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


# ============================================================================
# PostgreSQL fixtures (for integration tests using real service code)
# ============================================================================

_PG_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://netaai_app:netaai_password@localhost:5432/netaai_prod",
)


@pytest.fixture
async def pg_session() -> AsyncGenerator[AsyncSession, None]:
    """PostgreSQL session with per-test rollback for full integration tests."""
    engine = create_async_engine(_PG_URL, echo=False)

    async with engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(
            bind=conn,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()

    await engine.dispose()


@pytest.fixture
async def pg_admin_user(pg_session: AsyncSession):
    """Admin user in PostgreSQL test session."""
    from app.database_design.models import User as PgUser
    user = PgUser(
        full_name="Test Admin",
        email=f"admin_{uuid4().hex[:8]}@pg-test.local",
        phone="+919876543210",
        password_hash=hash_password("TestAdmin123!"),
        role="super_admin",
        is_active=True,
    )
    pg_session.add(user)
    await pg_session.commit()
    await pg_session.refresh(user)
    return user


@pytest.fixture
async def pg_field_worker_user(pg_session: AsyncSession, pg_test_zone):
    """Field worker user in PostgreSQL test session."""
    from app.database_design.models import User as PgUser
    user = PgUser(
        full_name="Test Worker",
        email=f"worker_{uuid4().hex[:8]}@pg-test.local",
        phone="+919876543212",
        password_hash=hash_password("TestWorker123!"),
        role="field_worker",
        zone_id=pg_test_zone.id,
        is_active=True,
    )
    pg_session.add(user)
    await pg_session.commit()
    await pg_session.refresh(user)
    return user


@pytest.fixture
async def pg_ground_commander_user(pg_session: AsyncSession, pg_test_zone):
    """Ground commander user in PostgreSQL test session."""
    from app.database_design.models import User as PgUser
    user = PgUser(
        full_name="Test Commander",
        email=f"cmd_{uuid4().hex[:8]}@pg-test.local",
        phone="+919876543213",
        password_hash=hash_password("TestCommander123!"),
        role="ground_commander",
        zone_id=pg_test_zone.id,
        is_active=True,
    )
    pg_session.add(user)
    await pg_session.commit()
    await pg_session.refresh(user)
    return user


@pytest.fixture
async def pg_test_constituency(pg_session: AsyncSession):
    """Test constituency in PostgreSQL test session."""
    from app.database_design.models import Constituency as PgConstituency
    constituency = PgConstituency(
        ac_number=f"T{uuid4().hex[:6]}",
        name="Test Constituency",
        state="Telangana",
        total_booths=1,
    )
    pg_session.add(constituency)
    await pg_session.commit()
    await pg_session.refresh(constituency)
    return constituency


@pytest.fixture
async def pg_test_zone(pg_session: AsyncSession, pg_test_constituency):
    """Test campaign zone in PostgreSQL test session."""
    from app.database_design.models import CampaignZone as PgCampaignZone
    zone = PgCampaignZone(
        constituency_id=pg_test_constituency.id,
        zone_code=f"Z{uuid4().hex[:6]}",
        zone_name="Test Zone",
    )
    pg_session.add(zone)
    await pg_session.commit()
    await pg_session.refresh(zone)
    return zone


@pytest.fixture
async def pg_test_booth(pg_session: AsyncSession, pg_test_constituency, pg_test_zone):
    """Test booth in PostgreSQL test session."""
    from app.database_design.models import Booth as PgBooth
    booth = PgBooth(
        constituency_id=pg_test_constituency.id,
        zone_id=pg_test_zone.id,
        booth_number=f"B{uuid4().hex[:6]}",
        booth_name="Test Booth",
        total_voters=1000,
    )
    pg_session.add(booth)
    await pg_session.commit()
    await pg_session.refresh(booth)
    return booth


@pytest.fixture
async def pg_auth_admin_user(pg_session: AsyncSession):
    """Admin user with fixed email for auth endpoint tests."""
    from app.database_design.models import User as PgUser
    user = PgUser(
        full_name="Test Admin",
        email="admin@example.com",
        phone="+919876543210",
        password_hash=hash_password("TestAdmin123!"),
        role="super_admin",
        is_active=True,
    )
    pg_session.add(user)
    await pg_session.commit()
    await pg_session.refresh(user)
    return user


@pytest.fixture
async def pg_test_client(pg_session: AsyncSession):
    """FastAPI test client backed by PostgreSQL session."""
    async def override_get_db():
        yield pg_session

    from app.database_design.database import get_db
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
