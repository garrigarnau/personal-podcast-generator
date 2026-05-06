"""
Admin dashboard endpoints for monitoring and analytics.

This module provides endpoints for:
- Aggregate KPIs (total podcasts, avg latency, costs)
- Recent podcast activity
- Daily metrics and volume data
- System health monitoring
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, cast, Date, Integer

from app.core.database import get_session
from app.models.podcast import Podcast, PodcastStatus
from app.models.metrics import Metrics
from app.schemas.admin import (
    AdminStatsResponse,
    KPISummary,
    DailyVolumeData,
    RecentPodcastItem,
    RecentPodcastResponse,
    DailyMetricsResponse,
)

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    summary="Get aggregate statistics",
    description=(
        "Retrieve comprehensive system statistics including KPIs, daily volume "
        "data, and recent podcast activity. This endpoint powers the admin dashboard."
    ),
    responses={
        200: {
            "description": "Statistics retrieved successfully",
        }
    }
)
async def get_admin_stats(
    days: int = 30,
    session: AsyncSession = Depends(get_session),
) -> AdminStatsResponse:
    """
    Get comprehensive admin statistics.

    This endpoint aggregates data from podcasts and metrics tables to provide
    a complete overview of system performance, including KPIs, volume trends,
    and recent activity.

    Args:
        days: Number of days to include in volume data (default: 30)
        session: Database session

    Returns:
        AdminStatsResponse with KPIs, volume data, and recent podcasts
    """
    logger.info(f"Fetching admin stats for last {days} days")

    # Get KPIs
    # Total podcasts
    total_podcasts_result = await session.execute(
        select(func.count()).select_from(Podcast)
    )
    total_podcasts = total_podcasts_result.scalar() or 0

    # Success rate
    completed_podcasts_result = await session.execute(
        select(func.count()).select_from(Podcast).where(
            Podcast.status == PodcastStatus.COMPLETED
        )
    )
    completed_podcasts = completed_podcasts_result.scalar() or 0

    success_rate = (
        (completed_podcasts / total_podcasts * 100)
        if total_podcasts > 0
        else 0.0
    )

    # Average latency, total cost, tokens, and characters
    metrics_aggregate = await session.execute(
        select(
            func.avg(Metrics.latency_ms).label("avg_latency"),
            func.avg(Metrics.news_fetch_ms).label("avg_news_fetch"),
            func.avg(Metrics.script_generation_ms).label("avg_script_generation"),
            func.avg(Metrics.audio_generation_ms).label("avg_audio_generation"),
            func.sum(Metrics.cost_estimate).label("total_cost"),
            func.sum(Metrics.tokens_used).label("total_tokens"),
            func.sum(Metrics.elevenlabs_characters).label("total_characters"),
            func.sum(func.coalesce(Metrics.firecrawl_scrapes, 0)).label("total_firecrawl_scrapes"),
            func.sum(func.coalesce(Metrics.firecrawl_cost, 0.0)).label("total_firecrawl_cost"),
            func.sum(func.coalesce(Metrics.openai_cost, 0.0)).label("total_openai_cost"),
            func.sum(func.coalesce(Metrics.elevenlabs_cost, 0.0)).label("total_elevenlabs_cost"),
        )
    )
    metrics_data = metrics_aggregate.one_or_none()

    avg_latency_ms = float(metrics_data.avg_latency or 0)
    avg_news_fetch_ms = float(metrics_data.avg_news_fetch or 0)
    avg_script_generation_ms = float(metrics_data.avg_script_generation or 0)
    avg_audio_generation_ms = float(metrics_data.avg_audio_generation or 0)
    total_cost_usd = float(metrics_data.total_cost or 0)
    total_tokens = int(metrics_data.total_tokens or 0)
    total_characters = int(metrics_data.total_characters or 0)
    total_firecrawl_scrapes = int(metrics_data.total_firecrawl_scrapes or 0)
    total_firecrawl_cost = float(metrics_data.total_firecrawl_cost or 0)
    total_openai_cost = float(metrics_data.total_openai_cost or 0)
    total_elevenlabs_cost = float(metrics_data.total_elevenlabs_cost or 0)

    # Use actual tracked costs from database
    # Fall back to calculation only if no actual costs are tracked (backward compatibility)
    openai_cost = total_openai_cost if total_openai_cost > 0 else (total_tokens / 1000) * 0.03 if total_tokens > 0 else 0.0
    elevenlabs_cost = total_elevenlabs_cost if total_elevenlabs_cost > 0 else (total_characters / 1000) * 0.30 if total_characters > 0 else 0.0
    firecrawl_cost = total_firecrawl_cost

    cost_breakdown = {
        "openai": round(openai_cost, 4),
        "elevenlabs": round(elevenlabs_cost, 4),
        "firecrawl": round(firecrawl_cost, 4),
    }

    # Ensure total_cost_usd matches the breakdown sum
    # This prevents mismatches from rounding or old records
    breakdown_total = openai_cost + elevenlabs_cost + firecrawl_cost
    total_cost_usd = round(breakdown_total, 4)

    # Latency breakdown by service
    latency_breakdown = {
        "news_fetch": round(avg_news_fetch_ms, 2),
        "script_generation": round(avg_script_generation_ms, 2),
        "audio_generation": round(avg_audio_generation_ms, 2),
    }

    kpis = KPISummary(
        total_podcasts=total_podcasts,
        avg_latency_ms=avg_latency_ms,
        total_cost_usd=total_cost_usd,
        success_rate=round(success_rate, 2),
        total_tokens=total_tokens,
        total_characters=total_characters,
        total_firecrawl_scrapes=total_firecrawl_scrapes,
        total_firecrawl_cost=total_firecrawl_cost,
        total_openai_cost=openai_cost,
        total_elevenlabs_cost=elevenlabs_cost,
        cost_breakdown=cost_breakdown,
        latency_breakdown=latency_breakdown,
    )

    logger.info(
        f"KPIs calculated: total={total_podcasts}, success_rate={success_rate:.2f}%, "
        f"avg_latency={avg_latency_ms:.2f}ms, total_cost=${total_cost_usd:.2f}"
    )

    # Get daily volume data
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Query daily aggregates
    daily_query = await session.execute(
        select(
            cast(Podcast.created_at, Date).label("date"),
            func.count().label("total"),
            func.sum(
                cast((Podcast.status == PodcastStatus.COMPLETED), Integer)
            ).label("completed"),
            func.sum(
                cast((Podcast.status == PodcastStatus.FAILED), Integer)
            ).label("failed"),
            func.sum(
                cast(
                    (Podcast.status.in_([PodcastStatus.PENDING, PodcastStatus.PROCESSING])),
                    Integer
                )
            ).label("pending"),
        )
        .where(Podcast.created_at >= cutoff_date)
        .group_by(cast(Podcast.created_at, Date))
        .order_by(cast(Podcast.created_at, Date).desc())
    )

    daily_podcast_data = daily_query.all()

    # Get daily metrics (latency and cost)
    daily_metrics_query = await session.execute(
        select(
            cast(Metrics.created_at, Date).label("date"),
            func.avg(Metrics.latency_ms).label("avg_latency"),
            func.sum(Metrics.cost_estimate).label("total_cost"),
        )
        .where(Metrics.created_at >= cutoff_date)
        .group_by(cast(Metrics.created_at, Date))
    )

    daily_metrics_map = {
        row.date: (float(row.avg_latency or 0), float(row.total_cost or 0))
        for row in daily_metrics_query.all()
    }

    # Combine podcast counts with metrics
    volume_data: List[DailyVolumeData] = []
    for row in daily_podcast_data:
        avg_latency, total_cost = daily_metrics_map.get(row.date, (0.0, 0.0))

        volume_data.append(
            DailyVolumeData(
                day=row.date,
                total=row.total or 0,
                completed=row.completed or 0,
                failed=row.failed or 0,
                pending=row.pending or 0,
                avg_latency_ms=avg_latency,
                total_cost_usd=total_cost,
            )
        )

    logger.info(f"Retrieved daily volume data for {len(volume_data)} days")

    # Get recent podcasts
    recent_podcasts_query = await session.execute(
        select(Podcast)
        .order_by(Podcast.created_at.desc())
        .limit(20)
    )
    recent_podcasts_list = recent_podcasts_query.scalars().all()

    # Get metrics for recent podcasts
    recent_podcast_ids = [p.id for p in recent_podcasts_list]
    metrics_query = await session.execute(
        select(Metrics).where(Metrics.podcast_id.in_(recent_podcast_ids))
    )
    metrics_map = {m.podcast_id: m for m in metrics_query.scalars().all()}

    recent_podcasts = [
        RecentPodcastItem(
            id=p.id,
            user_id=p.user_id,
            status=p.status.value,
            created_at=p.created_at,
            latency_ms=metrics_map[p.id].latency_ms if p.id in metrics_map else None,
            cost_usd=metrics_map[p.id].cost_estimate if p.id in metrics_map else None,
            error_message=p.error_message,
            firecrawl_searches=metrics_map[p.id].firecrawl_searches if p.id in metrics_map else None,
            firecrawl_scrapes=metrics_map[p.id].firecrawl_scrapes if p.id in metrics_map else None,
            firecrawl_cost=metrics_map[p.id].firecrawl_cost if p.id in metrics_map else None,
            tokens_used=metrics_map[p.id].tokens_used if p.id in metrics_map else None,
            elevenlabs_characters=metrics_map[p.id].elevenlabs_characters if p.id in metrics_map else None,
            openai_cost=metrics_map[p.id].openai_cost if p.id in metrics_map else None,
            elevenlabs_cost=metrics_map[p.id].elevenlabs_cost if p.id in metrics_map else None,
        )
        for p in recent_podcasts_list
    ]

    logger.info(f"Retrieved {len(recent_podcasts)} recent podcasts")

    return AdminStatsResponse(
        kpis=kpis,
        volume_data=volume_data,
        recent_podcasts=recent_podcasts,
        generated_at=datetime.utcnow(),
    )


@router.get(
    "/podcasts/recent",
    response_model=RecentPodcastResponse,
    summary="Get recent podcasts",
    description=(
        "Retrieve a paginated list of recent podcasts across all users. "
        "Useful for monitoring recent activity and identifying issues."
    ),
    responses={
        200: {
            "description": "Recent podcasts retrieved successfully",
        }
    }
)
async def get_recent_podcasts(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
) -> RecentPodcastResponse:
    """
    Get recent podcasts with pagination and optional status filtering.

    This endpoint returns recently created podcasts across all users,
    ordered by creation date (newest first). Useful for admin monitoring.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (1-100)
        status_filter: Optional status filter
        session: Database session

    Returns:
        RecentPodcastResponse with paginated recent podcasts
    """
    logger.info(
        f"Fetching recent podcasts: page={page}, page_size={page_size}, "
        f"status_filter={status_filter}"
    )

    # Validate pagination
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Page must be >= 1"
        )

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Page size must be between 1 and 100"
        )

    # Build query with optional status filter
    query = select(Podcast)

    if status_filter:
        try:
            status_enum = PodcastStatus(status_filter)
            query = query.where(Podcast.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status: {status_filter}"
            )

    # Get total count
    count_query = select(func.count()).select_from(Podcast)
    if status_filter:
        count_query = count_query.where(Podcast.status == status_enum)

    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.order_by(Podcast.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    podcasts_list = result.scalars().all()

    # Get metrics for podcasts
    podcast_ids = [p.id for p in podcasts_list]
    if podcast_ids:
        metrics_query = await session.execute(
            select(Metrics).where(Metrics.podcast_id.in_(podcast_ids))
        )
        metrics_map = {m.podcast_id: m for m in metrics_query.scalars().all()}
    else:
        metrics_map = {}

    podcasts = [
        RecentPodcastItem(
            id=p.id,
            user_id=p.user_id,
            status=p.status.value,
            created_at=p.created_at,
            latency_ms=metrics_map[p.id].latency_ms if p.id in metrics_map else None,
            cost_usd=metrics_map[p.id].cost_estimate if p.id in metrics_map else None,
            error_message=p.error_message,
            firecrawl_searches=metrics_map[p.id].firecrawl_searches if p.id in metrics_map else None,
            firecrawl_scrapes=metrics_map[p.id].firecrawl_scrapes if p.id in metrics_map else None,
            firecrawl_cost=metrics_map[p.id].firecrawl_cost if p.id in metrics_map else None,
            tokens_used=metrics_map[p.id].tokens_used if p.id in metrics_map else None,
            elevenlabs_characters=metrics_map[p.id].elevenlabs_characters if p.id in metrics_map else None,
            openai_cost=metrics_map[p.id].openai_cost if p.id in metrics_map else None,
            elevenlabs_cost=metrics_map[p.id].elevenlabs_cost if p.id in metrics_map else None,
        )
        for p in podcasts_list
    ]

    logger.info(
        f"Retrieved {len(podcasts)} recent podcasts, total={total}, page={page}"
    )

    return RecentPodcastResponse(
        podcasts=podcasts,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/metrics/daily",
    response_model=DailyMetricsResponse,
    summary="Get daily metrics",
    description=(
        "Retrieve daily volume and performance metrics for charting and analysis. "
        "Includes podcast counts, completion rates, latency, and costs."
    ),
    responses={
        200: {
            "description": "Daily metrics retrieved successfully",
        }
    }
)
async def get_daily_metrics(
    days: int = 30,
    session: AsyncSession = Depends(get_session),
) -> DailyMetricsResponse:
    """
    Get daily aggregated metrics for charts and analysis.

    This endpoint provides daily breakdowns of podcast generation volume,
    success rates, latency, and costs. Designed for time-series visualization
    in the admin dashboard.

    Args:
        days: Number of days to include (1-365, default: 30)
        session: Database session

    Returns:
        DailyMetricsResponse with daily metrics data
    """
    logger.info(f"Fetching daily metrics for last {days} days")

    # Validate days parameter
    if days < 1 or days > 365:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Days must be between 1 and 365"
        )

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Get daily podcast counts by status
    daily_query = await session.execute(
        select(
            cast(Podcast.created_at, Date).label("date"),
            func.count().label("total"),
            func.sum(
                cast((Podcast.status == PodcastStatus.COMPLETED), Integer)
            ).label("completed"),
            func.sum(
                cast((Podcast.status == PodcastStatus.FAILED), Integer)
            ).label("failed"),
            func.sum(
                cast(
                    (Podcast.status.in_([PodcastStatus.PENDING, PodcastStatus.PROCESSING])),
                    Integer
                )
            ).label("pending"),
        )
        .where(Podcast.created_at >= cutoff_date)
        .group_by(cast(Podcast.created_at, Date))
        .order_by(cast(Podcast.created_at, Date).asc())
    )

    daily_podcast_data = daily_query.all()

    # Get daily metrics (latency and cost)
    daily_metrics_query = await session.execute(
        select(
            cast(Metrics.created_at, Date).label("date"),
            func.avg(Metrics.latency_ms).label("avg_latency"),
            func.sum(Metrics.cost_estimate).label("total_cost"),
        )
        .where(Metrics.created_at >= cutoff_date)
        .group_by(cast(Metrics.created_at, Date))
    )

    daily_metrics_map = {
        row.date: (float(row.avg_latency or 0), float(row.total_cost or 0))
        for row in daily_metrics_query.all()
    }

    # Combine data
    metrics: List[DailyVolumeData] = []
    total_podcasts = 0
    total_cost = 0.0

    for row in daily_podcast_data:
        avg_latency, day_cost = daily_metrics_map.get(row.date, (0.0, 0.0))

        metrics.append(
            DailyVolumeData(
                day=row.date,
                total=row.total or 0,
                completed=row.completed or 0,
                failed=row.failed or 0,
                pending=row.pending or 0,
                avg_latency_ms=avg_latency,
                total_cost_usd=day_cost,
            )
        )

        total_podcasts += row.total or 0
        total_cost += day_cost

    logger.info(
        f"Retrieved daily metrics for {len(metrics)} days, "
        f"total_podcasts={total_podcasts}, total_cost=${total_cost:.2f}"
    )

    return DailyMetricsResponse(
        metrics=metrics,
        days=days,
        total_podcasts=total_podcasts,
        total_cost_usd=round(total_cost, 2),
    )
