"""
Seed script to create a test admin user.

Usage:
    python scripts/seed_admin_user.py
    python scripts/seed_admin_user.py --email admin@example.com --password MySecurePassword123!

Environment:
    DATABASE_URL must be set (async PostgreSQL URL)
"""
import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database_design.models import Base, User
from app.security_auth.utils import hash_password


async def seed_admin_user(email: str = "admin@netaai.in", password: str = "Admin123!Secure"):
    """Create a test admin user."""
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    # Create session factory
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        # Check if user already exists
        query = select(User).where(User.email == email.lower())
        result = await session.execute(query)
        existing = result.scalars().first()

        if existing:
            print(f"[SKIP] User {email} already exists")
            await engine.dispose()
            return False

        # Create admin user
        admin_user = User(
            id=UUID("11111111-1111-1111-1111-111111111111"),  # Fixed UUID for testing
            full_name="System Administrator",
            email=email.lower(),
            phone="+919876543210",
            password_hash=hash_password(password),
            role="super_admin",
            is_active=True,
        )

        session.add(admin_user)
        await session.commit()

        print(f"[OK] Created admin user:")
        print(f"     Email: {email}")
        print(f"     Password: {password}")
        print(f"     Role: super_admin")
        print(f"     UUID: {admin_user.id}")

    await engine.dispose()
    return True


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed admin user")
    parser.add_argument("--email", default="admin@netaai.in", help="Admin email")
    parser.add_argument("--password", default="Admin123!Secure", help="Admin password")
    parser.add_argument("--force", action="store_true", help="Delete and recreate user")

    args = parser.parse_args()

    print("=" * 60)
    print("NETA AI — Seed Admin User")
    print("=" * 60)

    try:
        created = await seed_admin_user(args.email, args.password)
        if not created and not args.force:
            print("\nUser already exists. Use --force to recreate.")
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to create admin user: {e}")
        sys.exit(1)

    print("\n[OK] Database seeding completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
