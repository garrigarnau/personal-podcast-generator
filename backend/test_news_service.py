"""
Test script for FirecrawlNewsService.

Run with: python -m backend.test_news_service
"""

import asyncio
import logging
from app.services.news_service import get_news_service, FetchedNewsArticle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_news_service():
    """Test the news service with sample interests."""

    logger.info("=" * 80)
    logger.info("Testing FirecrawlNewsService")
    logger.info("=" * 80)

    # Initialize service
    service = get_news_service()
    logger.info(f"Service initialized: {service.__class__.__name__}")

    # Test interests
    interests = [
        "artificial intelligence",
        "machine learning",
        "technology startups"
    ]

    logger.info(f"\nFetching news for interests: {interests}")

    try:
        # Fetch news articles
        articles = await service.fetch_news(
            interests=interests,
            max_articles=5,
            days_back=7,
            min_relevance_score=0.3
        )

        logger.info(f"\n{'=' * 80}")
        logger.info(f"Successfully fetched {len(articles)} articles")
        logger.info(f"{'=' * 80}\n")

        # Display results
        for i, article in enumerate(articles, 1):
            logger.info(f"\nArticle {i}:")
            logger.info(f"  Title: {article.title}")
            logger.info(f"  Source: {article.source}")
            logger.info(f"  Published: {article.published_date}")
            logger.info(f"  Relevance Score: {article.relevance_score:.3f}")
            logger.info(f"  Word Count: {article.word_count}")
            logger.info(f"  Topics: {', '.join(article.topics) if article.topics else 'None'}")
            logger.info(f"  URL: {article.url}")
            logger.info(f"  Summary: {article.summary[:200] if article.summary else 'No summary'}...")

        # Display usage stats
        stats = service.get_usage_stats()
        logger.info(f"\n{'=' * 80}")
        logger.info("Usage Statistics:")
        logger.info(f"  Total Requests: {stats['total_requests']}")
        logger.info(f"  Total Cost: ${stats['total_cost_usd']:.4f}")
        logger.info(f"  Requests (last minute): {stats['requests_last_minute']}")
        logger.info(f"  Rate Limit: {stats['rate_limit']}/min")
        logger.info(f"{'=' * 80}\n")

        # Test conversion to script service format
        if articles:
            logger.info("Example conversion to NewsArticle format for script generation:")
            from app.services.script_service import NewsArticle

            script_article = NewsArticle(
                title=articles[0].title,
                summary=articles[0].summary or articles[0].content[:500],
                content=articles[0].content,
                source=articles[0].source,
                url=str(articles[0].url),
                published_at=articles[0].published_date,
                category=articles[0].topics[0] if articles[0].topics else None
            )
            logger.info(f"  Converted article: {script_article.title}")
            logger.info(f"  Ready for script generation: ✓")

        return True

    except Exception as e:
        logger.error(f"Error testing news service: {e}", exc_info=True)
        return False


async def test_error_handling():
    """Test error handling capabilities."""

    logger.info(f"\n{'=' * 80}")
    logger.info("Testing Error Handling")
    logger.info(f"{'=' * 80}\n")

    service = get_news_service()

    # Test with empty interests
    logger.info("Test 1: Empty interests list")
    try:
        articles = await service.fetch_news(interests=[], max_articles=5)
        logger.info(f"  Result: {len(articles)} articles (expected: 0)")
    except Exception as e:
        logger.error(f"  Error: {e}")

    # Test with very restrictive parameters
    logger.info("\nTest 2: Very high relevance threshold")
    try:
        articles = await service.fetch_news(
            interests=["quantum computing"],
            max_articles=10,
            min_relevance_score=0.95  # Very high threshold
        )
        logger.info(f"  Result: {len(articles)} articles (high threshold)")
    except Exception as e:
        logger.error(f"  Error: {e}")

    logger.info(f"\n{'=' * 80}")


async def main():
    """Main test runner."""
    logger.info("Starting News Service Tests\n")

    # Run tests
    success = await test_news_service()

    if success:
        await test_error_handling()
        logger.info("\n✓ All tests completed successfully!")
    else:
        logger.error("\n✗ Tests failed!")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
