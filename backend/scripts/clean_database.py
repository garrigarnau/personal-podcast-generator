#!/usr/bin/env python3
"""
Clean database script - Removes all data from the database.

Usage:
    python scripts/clean_database.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import engine, Base
from app.models.user import User
from app.models.podcast import Podcast
from app.models.metrics import Metrics


async def clean_database():
    """Drop all tables and recreate them."""
    print("🗑️  Cleaning database...")

    async with engine.begin() as conn:
        # Drop all tables
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("✅ All tables dropped")

        # Recreate all tables
        print("Recreating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("✅ All tables recreated")

    print("\n✨ Database cleaned successfully!")
    print("All data has been removed and tables recreated.")


async def truncate_data():
    """Delete all data but keep table structure."""
    print("🧹 Truncating all data...")

    async with engine.begin() as conn:
        # Disable foreign key checks temporarily
        await conn.execute(text("SET session_replication_role = 'replica';"))

        # Truncate tables
        print("Truncating metrics...")
        await conn.execute(text("TRUNCATE TABLE metrics CASCADE;"))

        print("Truncating podcasts...")
        await conn.execute(text("TRUNCATE TABLE podcasts CASCADE;"))

        print("Truncating users...")
        await conn.execute(text("TRUNCATE TABLE users CASCADE;"))

        # Re-enable foreign key checks
        await conn.execute(text("SET session_replication_role = 'origin';"))

    print("\n✨ All data truncated successfully!")
    print("Table structure remains intact.")


async def main():
    """Main function."""
    print("\n" + "="*50)
    print("   DATABASE CLEANUP UTILITY")
    print("="*50 + "\n")

    print("Choose an option:")
    print("1. Drop and recreate all tables (complete reset)")
    print("2. Truncate all data (keep table structure)")
    print("3. Cancel")

    choice = input("\nEnter your choice (1-3): ").strip()

    if choice == "1":
        confirm = input("\n⚠️  This will DELETE ALL TABLES and DATA. Are you sure? (yes/no): ")
        if confirm.lower() == "yes":
            await clean_database()
        else:
            print("❌ Cancelled")
    elif choice == "2":
        confirm = input("\n⚠️  This will DELETE ALL DATA. Are you sure? (yes/no): ")
        if confirm.lower() == "yes":
            await truncate_data()
        else:
            print("❌ Cancelled")
    else:
        print("❌ Cancelled")


if __name__ == "__main__":
    asyncio.run(main())
