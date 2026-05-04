"""
Schema verification script.

This script verifies that all database models are properly configured
and can generate SQL schema without errors.

Usage:
    python verify_schema.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy.schema import CreateTable
from app.core.database import Base
from app.models import User, Podcast, Metrics


def verify_schema():
    """Verify database schema and print table creation SQL."""
    print("=" * 80)
    print("DATABASE SCHEMA VERIFICATION")
    print("=" * 80)

    # Check that all models are imported
    models = [User, Podcast, Metrics]
    print(f"\n✓ Found {len(models)} models: {[m.__name__ for m in models]}")

    # Print metadata info
    tables = Base.metadata.sorted_tables
    print(f"\n✓ Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table.name}")
        print(f"    Columns: {len(table.columns)}")
        print(f"    Indexes: {len(table.indexes)}")
        print(f"    Foreign Keys: {len(list(table.foreign_keys))}")

    # Generate and print CREATE TABLE statements
    print("\n" + "=" * 80)
    print("GENERATED SQL SCHEMA")
    print("=" * 80)

    from sqlalchemy.dialects import postgresql

    for table in tables:
        print(f"\n-- Table: {table.name}")
        print(CreateTable(table).compile(dialect=postgresql.dialect()))

    # Verify relationships
    print("\n" + "=" * 80)
    print("RELATIONSHIPS")
    print("=" * 80)

    print("\nUser relationships:")
    for rel in User.__mapper__.relationships:
        print(f"  - {rel.key}: {rel.direction.name} to {rel.entity.class_.__name__}")

    print("\nPodcast relationships:")
    for rel in Podcast.__mapper__.relationships:
        print(f"  - {rel.key}: {rel.direction.name} to {rel.entity.class_.__name__}")

    print("\nMetrics relationships:")
    for rel in Metrics.__mapper__.relationships:
        print(f"  - {rel.key}: {rel.direction.name} to {rel.entity.class_.__name__}")

    # Verify model methods
    print("\n" + "=" * 80)
    print("MODEL METHODS")
    print("=" * 80)

    print("\nUser methods:")
    user_methods = [m for m in dir(User) if not m.startswith('_') and callable(getattr(User, m))]
    print(f"  {', '.join(user_methods)}")

    print("\nPodcast methods:")
    podcast_methods = [m for m in dir(Podcast) if not m.startswith('_') and callable(getattr(Podcast, m))]
    print(f"  {', '.join(podcast_methods)}")

    print("\nMetrics methods:")
    metrics_methods = [m for m in dir(Metrics) if not m.startswith('_') and callable(getattr(Metrics, m))]
    print(f"  {', '.join(metrics_methods)}")

    print("\n" + "=" * 80)
    print("✓ Schema verification completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        verify_schema()
    except Exception as e:
        print(f"\n✗ Schema verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
