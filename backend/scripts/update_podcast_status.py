#!/usr/bin/env python3
"""
Script to update podcast status in the database.

Usage:
    python scripts/update_podcast_status.py [OPTIONS]

Examples:
    # List all podcasts with status summary
    python scripts/update_podcast_status.py --list

    # Mark all non-failed podcasts as COMPLETED (default action)
    python scripts/update_podcast_status.py

    # Mark all non-failed podcasts as COMPLETED with audio URL template
    python scripts/update_podcast_status.py --audio-url "https://storage.example.com/{id}.mp3"

    # Mark all PENDING podcasts as FAILED
    python scripts/update_podcast_status.py --fail-pending

    # Mark all PENDING podcasts as FAILED with custom error message
    python scripts/update_podcast_status.py --fail-pending --error-message "Generation timeout"
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_factory
from app.models.podcast import Podcast, PodcastStatus
from uuid import UUID


async def update_all_to_completed(audio_url: str = None) -> None:
    """
    Update all non-failed podcasts to COMPLETED status.

    PENDING, PROCESSING, and already COMPLETED podcasts will be set to COMPLETED.
    FAILED podcasts are left unchanged.

    Args:
        audio_url: Audio URL template (can include {id} placeholder)
    """
    async with async_session_factory() as session:
        try:
            # Fetch all podcasts that are NOT failed
            result = await session.execute(
                select(Podcast).where(Podcast.status != PodcastStatus.FAILED)
            )
            podcasts = result.scalars().all()

            if not podcasts:
                print("ℹ️  No non-failed podcasts found")
                return

            print(f"📻 Found {len(podcasts)} non-failed podcast(s) to update")
            print(f"   Updating all to COMPLETED status\n")

            updated_count = 0
            for podcast in podcasts:
                old_status = podcast.status.value
                print(f"   [{old_status.upper()}] {podcast.title or 'Untitled'} ({podcast.id})")

                # Generate audio URL if template provided
                url = None
                if audio_url:
                    url = audio_url.replace("{id}", str(podcast.id))
                    podcast.mark_completed(url)
                else:
                    podcast.status = PodcastStatus.COMPLETED
                    podcast.updated_at = datetime.utcnow()

                updated_count += 1

            await session.commit()
            print(f"\n✅ Successfully updated {updated_count} podcast(s) to COMPLETED")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error: {e}")
            raise




async def mark_pending_as_failed(error_message: str = None) -> None:
    """
    Mark all PENDING podcasts as FAILED.

    Args:
        error_message: Error message to set for failed podcasts
    """
    async with async_session_factory() as session:
        try:
            # Fetch all pending podcasts
            result = await session.execute(
                select(Podcast).where(Podcast.status == PodcastStatus.PENDING)
            )
            podcasts = result.scalars().all()

            if not podcasts:
                print("ℹ️  No pending podcasts found")
                return

            print(f"📻 Found {len(podcasts)} pending podcast(s) to mark as FAILED\n")

            error = error_message or "Manually marked as failed"
            updated_count = 0

            for podcast in podcasts:
                print(f"   ❌ {podcast.title or 'Untitled'} ({podcast.id})")
                podcast.mark_failed(error)
                updated_count += 1

            await session.commit()
            print(f"\n✅ Successfully marked {updated_count} podcast(s) as FAILED")
            print(f"   Error message: {error}")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error: {e}")
            raise


async def list_podcasts() -> None:
    """
    List all podcasts with status summary.
    """
    async with async_session_factory() as session:
        try:
            result = await session.execute(select(Podcast).order_by(Podcast.created_at.desc()))
            podcasts = result.scalars().all()

            if not podcasts:
                print("ℹ️  No podcasts found")
                return

            # Count by status
            status_counts = {}
            for podcast in podcasts:
                status = podcast.status.value
                status_counts[status] = status_counts.get(status, 0) + 1

            print(f"\n📊 Status Summary:")
            print(f"   Total: {len(podcasts)}")
            for status, count in sorted(status_counts.items()):
                print(f"   {status.upper()}: {count}")

            print(f"\n📻 All Podcasts:\n")

            for podcast in podcasts:
                status_emoji = {
                    'pending': '⏳',
                    'processing': '🔄',
                    'completed': '✅',
                    'failed': '❌'
                }.get(podcast.status.value, '❓')

                print(f"{status_emoji} [{podcast.status.value.upper()}] {podcast.title or 'Untitled'}")
                print(f"   ID: {podcast.id}")
                print(f"   Created: {podcast.created_at}")
                if podcast.audio_url:
                    print(f"   Audio: {podcast.audio_url}")
                if podcast.error_message:
                    print(f"   Error: {podcast.error_message}")
                print()

        except Exception as e:
            print(f"❌ Error: {e}")
            raise


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Update podcast statuses in the database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--audio-url",
        help="Audio URL template (use {id} as placeholder for podcast ID) - used with default action"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all podcasts with status summary (doesn't update anything)"
    )

    parser.add_argument(
        "--fail-pending",
        action="store_true",
        help="Mark all PENDING podcasts as FAILED"
    )

    parser.add_argument(
        "--error-message",
        help="Error message to set when marking podcasts as FAILED (used with --fail-pending)"
    )

    args = parser.parse_args()

    # Handle list command
    if args.list:
        asyncio.run(list_podcasts())
        return

    # Handle fail-pending command
    if args.fail_pending:
        print("🔄 Marking all PENDING podcasts as FAILED...")
        asyncio.run(mark_pending_as_failed(error_message=args.error_message))
        return

    # Default: Update all non-failed podcasts to COMPLETED
    print("🔄 Updating all non-failed podcasts to COMPLETED...")
    if args.audio_url:
        print(f"   Using audio URL template: {args.audio_url}")
    else:
        print("   No audio URL provided")

    asyncio.run(update_all_to_completed(audio_url=args.audio_url))


if __name__ == "__main__":
    main()
