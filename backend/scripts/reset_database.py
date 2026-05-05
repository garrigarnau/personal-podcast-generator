#!/usr/bin/env python3
"""
Complete database reset script.

This script:
1. Drops the entire database
2. Recreates it
3. Runs migrations

Usage:
    python scripts/reset_database.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, create_engine
from app.core.config import settings


def get_postgres_url():
    """Get PostgreSQL URL for postgres database (not podcast_db)."""
    # Replace the database name with 'postgres'
    db_url = str(settings.DATABASE_URL)
    # Convert asyncpg to psycopg2 for synchronous connection
    db_url = db_url.replace('postgresql+asyncpg', 'postgresql')
    db_url = db_url.rsplit('/', 1)[0] + '/postgres'
    return db_url


def reset_database():
    """Drop and recreate the database."""
    print("🔥 Resetting database...")
    print()

    # Get database name from settings
    db_name = 'podcast_db'

    # Connect to postgres database (not podcast_db)
    postgres_url = get_postgres_url()
    engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")

    try:
        with engine.connect() as conn:
            # Terminate all connections to the database
            print(f"Terminating connections to {db_name}...")
            conn.execute(text(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{db_name}'
                AND pid <> pg_backend_pid();
            """))

            # Drop database
            print(f"Dropping database {db_name}...")
            conn.execute(text(f"DROP DATABASE IF EXISTS {db_name};"))
            print(f"✅ Database {db_name} dropped")

            # Create database
            print(f"Creating database {db_name}...")
            conn.execute(text(f"CREATE DATABASE {db_name} OWNER podcast_user;"))
            print(f"✅ Database {db_name} created")

        print()
        print("✨ Database reset complete!")
        print()
        print("Now run migrations:")
        print("  cd backend")
        print("  alembic upgrade head")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    print("\n" + "="*50)
    print("   DATABASE RESET UTILITY")
    print("="*50 + "\n")

    confirm = input("⚠️  This will DELETE the entire database. Are you sure? (yes/no): ")
    if confirm.lower() == "yes":
        reset_database()
    else:
        print("❌ Cancelled")
