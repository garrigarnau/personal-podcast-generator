"""
Database initialization script.

This script initializes the database and creates all tables.
Use this for development/testing only. In production, use Alembic migrations.

Usage:
    python -m app.db_init
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import init_db, engine
from app.models import User, Podcast, Metrics


async def main() -> None:
    """Initialize database tables."""
    print("Initializing database...")
    print(f"Database URL: {engine.url}")

    try:
        await init_db()
        print("✓ Database tables created successfully!")

        # Print created tables
        from app.core.database import Base
        print("\nCreated tables:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")

    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        sys.exit(1)
    finally:
        from app.core.database import close_db
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
