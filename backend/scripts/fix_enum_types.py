#!/usr/bin/env python3
"""
Fix enum type conflicts in PostgreSQL.

This script drops existing enum types that might cause conflicts during migrations.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import engine


async def fix_enum_types():
    """Drop existing enum types."""
    print("🔧 Fixing enum type conflicts...")

    async with engine.begin() as conn:
        try:
            # Drop existing enum types
            print("Dropping podcaststatus enum type...")
            await conn.execute(text("DROP TYPE IF EXISTS podcaststatus CASCADE;"))
            print("✅ podcaststatus type dropped")

            print("\n✨ Enum types fixed!")
            print("Now run: alembic upgrade head")

        except Exception as e:
            print(f"❌ Error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(fix_enum_types())
