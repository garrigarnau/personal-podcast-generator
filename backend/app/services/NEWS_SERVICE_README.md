# FirecrawlNewsService Documentation

## Overview

The `FirecrawlNewsService` is a production-grade news fetching service that uses the Firecrawl API to search, scrape, and rank relevant news articles based on user interests. It's designed for the Personal Podcast Generator application with a focus on reliability, performance, and observability.

## Features

### Core Capabilities
- **Async/Await Support**: All network operations use async/await for high performance
- **Intelligent Relevance Ranking**: Multi-factor scoring algorithm based on user interests
- **Date Filtering**: Only fetches recent news (configurable time window)
- **Rate Limiting**: Automatic rate limit enforcement to prevent API throttling
- **Retry Logic**: Exponential backoff retry mechanism for transient failures
- **Cost Tracking**: Monitors API usage and estimated costs
- **Comprehensive Logging**: Structured logging for observability and debugging
- **Error Handling**: Graceful handling of API errors, timeouts, and edge cases

### Data Model

The service uses the `FetchedNewsArticle` Pydantic model with full validation:

```python
class FetchedNewsArticle(BaseModel):
    title: str                    # Article headline (1-500 chars)
    content: str                  # Full article text (min 50 chars)
    summary: Optional[str]        # Brief summary or excerpt
    source: str                   # Publication/website name
    author: Optional[str]         # Article author
    published_date: datetime      # Publication timestamp
    url: HttpUrl                  # Source URL
    relevance_score: float        # Calculated relevance (0.0-1.0)
    topics: List[str]            # Extracted topics/categories
    word_count: int              # Approximate word count
```

## Usage

### Basic Usage

```python
from app.services import get_news_service, FetchedNewsArticle

# Get singleton instance
service = get_news_service()

# Fetch news articles
articles = await service.fetch_news(
    interests=["artificial intelligence", "startups", "climate tech"],
    max_articles=5,
    days_back=7,
    min_relevance_score=0.3
)

# Process articles
for article in articles:
    print(f"{article.title} (Score: {article.relevance_score:.2f})")
```

### Advanced Usage

```python
# Initialize with custom configuration
from app.services.news_service import FirecrawlNewsService

service = FirecrawlNewsService(
    api_key="your-api-key",
    max_retries=5,
    timeout=60
)

# Fetch with strict filtering
articles = await service.fetch_news(
    interests=["quantum computing", "artificial intelligence"],
    max_articles=10,
    days_back=3,              # Only last 3 days
    min_relevance_score=0.5   # High relevance threshold
)

# Check usage statistics
stats = service.get_usage_stats()
print(f"Total cost: ${stats['total_cost_usd']:.4f}")
print(f"Requests: {stats['total_requests']}")
```

### Integration with Script Service

Convert `FetchedNewsArticle` to `NewsArticle` for script generation:

```python
from app.services import get_news_service, NewsArticle

# Fetch news
fetched_articles = await get_news_service().fetch_news(
    interests=["technology"],
    max_articles=5
)

# Convert for script generation
script_articles = [
    NewsArticle(
        title=article.title,
        summary=article.summary or article.content[:500],
        content=article.content,
        source=article.source,
        url=str(article.url),
        published_at=article.published_date,
        category=article.topics[0] if article.topics else None
    )
    for article in fetched_articles
]

# Generate podcast script
from app.services import generate_podcast_script

script, metrics = await generate_podcast_script(
    articles=script_articles,
    tone="casual",
    length="medium"
)
```

## Architecture

### Class Structure

```
FirecrawlNewsService
├── __init__()              # Initialize Firecrawl client
├── fetch_news()           # Main entry point for fetching news
├── _search_news()         # Search using Firecrawl API
├── _execute_search()      # Synchronous search execution
├── _fallback_news_fetch() # Fallback for direct URL scraping
├── _filter_by_date()      # Filter articles by publication date
├── _parse_article()       # Parse raw API response to model
├── _rank_relevance()      # Calculate relevance scores
├── _check_rate_limit()    # Enforce rate limits
├── _track_request()       # Track API usage and costs
├── get_usage_stats()      # Get current usage metrics
└── reset_usage_stats()    # Reset usage counters
```

### Relevance Scoring Algorithm

The relevance score is calculated using a weighted multi-factor approach:

1. **Title Matching (40% weight)**
   - Direct keyword presence in article title
   - Higher weight because title indicates primary topic

2. **Content Matching (30% weight)**
   - Keyword frequency in article content
   - Normalized by content length to avoid bias

3. **Topic Matching (20% weight)**
   - Matches between interests and article topics/categories
   - Useful when articles have structured metadata

4. **Recency Bonus (10% weight)**
   - Exponential decay over 7 days
   - Newer articles get higher scores

**Formula:**
```
relevance_score = min(1.0,
    title_score * 0.4 +
    content_score * 0.3 +
    topic_score * 0.2 +
    recency_score * 0.1
)
```

### Rate Limiting

- **Default Limit**: 60 requests per minute
- **Tracking**: Rolling window using timestamps
- **Enforcement**: Raises `RateLimitError` when limit exceeded
- **Configurable**: Adjust `MAX_REQUESTS_PER_MINUTE` class variable

### Cost Tracking

Approximate costs are tracked for observability:

- **Search Cost**: $0.01 per request
- **Scrape Cost**: $0.005 per page
- **Total Cost**: Cumulative across all requests
- **Access**: `service.get_usage_stats()['total_cost_usd']`

> **Note**: Adjust cost constants based on actual Firecrawl pricing

## Error Handling

### Exception Hierarchy

```
FirecrawlNewsServiceError          # Base exception
├── RateLimitError                 # Rate limit exceeded
└── APIError                       # API request failed
```

### Error Handling Example

```python
from app.services.news_service import (
    FirecrawlNewsServiceError,
    RateLimitError,
    APIError
)

try:
    articles = await service.fetch_news(interests=["tech"], max_articles=5)
except RateLimitError as e:
    # Handle rate limiting
    print(f"Rate limit hit: {e}")
    await asyncio.sleep(60)  # Wait before retry
except APIError as e:
    # Handle API errors
    logger.error(f"API error: {e}")
    # Fallback to cached data or alternative source
except FirecrawlNewsServiceError as e:
    # Handle other service errors
    logger.error(f"Service error: {e}")
```

## Configuration

### Environment Variables

Required in `.env`:

```bash
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
```

### Service Constants

Configurable class variables:

```python
# Rate limiting
MAX_REQUESTS_PER_MINUTE = 60
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2  # seconds

# Cost tracking (adjust based on actual pricing)
SEARCH_COST_PER_REQUEST = 0.01   # USD
SCRAPE_COST_PER_PAGE = 0.005     # USD
```

## Best Practices

### 1. Use Singleton Pattern

```python
# ✓ Good: Use singleton
service = get_news_service()

# ✗ Avoid: Creating multiple instances
service = FirecrawlNewsService()
```

### 2. Handle Empty Results

```python
articles = await service.fetch_news(interests=["rare topic"])

if not articles:
    logger.warning("No articles found, using fallback content")
    # Implement fallback logic
```

### 3. Monitor Usage

```python
# Check usage periodically
stats = service.get_usage_stats()
if stats['total_cost_usd'] > 10.0:
    logger.warning(f"High API usage: ${stats['total_cost_usd']:.2f}")
    # Alert or throttle requests
```

### 4. Set Appropriate Thresholds

```python
# Adjust based on use case
articles = await service.fetch_news(
    interests=interests,
    max_articles=5,              # Don't over-fetch
    days_back=7,                 # Balance freshness vs availability
    min_relevance_score=0.3      # 0.3-0.5 is a good range
)
```

### 5. Log Context

```python
logger.info(
    f"Fetching news: interests={interests}, "
    f"user_id={user_id}, max={max_articles}"
)
```

## Performance Considerations

### Async Operations

All network calls use `asyncio.to_thread()` to wrap synchronous Firecrawl calls:

```python
result = await asyncio.to_thread(
    self._execute_search,
    query,
    limit
)
```

This allows true async behavior without blocking the event loop.

### Caching Strategy

Consider implementing caching for frequently requested topics:

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache results for 1 hour
@lru_cache(maxsize=100)
def _cached_fetch(interests_tuple, max_articles, timestamp):
    # Implementation
    pass

# Use with timestamp rounding
timestamp = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
articles = _cached_fetch(tuple(interests), max_articles, timestamp)
```

### Batch Processing

For multiple users, use `asyncio.gather()`:

```python
async def fetch_for_users(users):
    tasks = [
        service.fetch_news(
            interests=user.preferences['interests'],
            max_articles=5
        )
        for user in users
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

## Testing

### Unit Tests

Run the test script:

```bash
cd backend
python -m test_news_service
```

### Mock Testing

```python
from unittest.mock import AsyncMock, patch

@patch('app.services.news_service.FirecrawlApp')
async def test_fetch_news(mock_firecrawl):
    # Setup mock
    mock_firecrawl.return_value.search = Mock(return_value={
        'data': [
            {
                'title': 'Test Article',
                'content': 'Test content here...',
                'url': 'https://example.com',
                'published_date': '2026-05-01T00:00:00Z'
            }
        ]
    })

    # Test service
    service = FirecrawlNewsService()
    articles = await service.fetch_news(
        interests=["test"],
        max_articles=1
    )

    assert len(articles) == 1
    assert articles[0].title == "Test Article"
```

## Monitoring & Observability

### Logging

The service uses structured logging:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Service automatically logs:
# - Initialization
# - Fetch requests with parameters
# - API calls and responses
# - Errors and retries
# - Usage statistics
```

### Metrics to Track

1. **Requests per minute**: Monitor rate limit usage
2. **Total cost**: Track API spending
3. **Average relevance score**: Measure result quality
4. **Articles per request**: Monitor fetch efficiency
5. **Error rate**: Track failures and retries
6. **Latency**: Measure response times

### Example Monitoring Integration

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram

news_requests = Counter('news_requests_total', 'Total news requests')
news_articles = Histogram('news_articles_count', 'Articles per request')
news_cost = Counter('news_cost_usd_total', 'Total API cost')

# In service method
news_requests.inc()
articles = await service.fetch_news(...)
news_articles.observe(len(articles))
news_cost.inc(service.get_usage_stats()['total_cost_usd'])
```

## Troubleshooting

### Issue: No articles returned

**Possible causes:**
1. Interests too specific or niche
2. Relevance threshold too high
3. Date range too narrow
4. API rate limit exceeded

**Solutions:**
```python
# Broaden search parameters
articles = await service.fetch_news(
    interests=["tech"],              # More general
    max_articles=10,                 # Request more
    days_back=14,                    # Wider date range
    min_relevance_score=0.2          # Lower threshold
)
```

### Issue: Rate limit errors

**Solution:**
```python
import asyncio
from app.services.news_service import RateLimitError

try:
    articles = await service.fetch_news(...)
except RateLimitError:
    await asyncio.sleep(60)  # Wait 1 minute
    articles = await service.fetch_news(...)  # Retry
```

### Issue: High API costs

**Solutions:**
1. Reduce fetch frequency
2. Lower `max_articles` parameter
3. Implement caching
4. Use higher relevance thresholds
5. Batch process multiple users

### Issue: Poor relevance scores

**Solutions:**
1. Use more specific interests
2. Adjust relevance weights in `_rank_relevance()`
3. Add custom scoring factors
4. Filter by topics/categories

## Future Enhancements

### Potential Improvements

1. **Semantic Search**: Use embeddings for better matching
2. **Source Diversity**: Ensure articles from multiple sources
3. **Duplicate Detection**: Remove similar/duplicate articles
4. **Language Detection**: Filter by language
5. **Quality Scoring**: Score based on source credibility
6. **Trending Topics**: Identify trending topics automatically
7. **Personalization**: Learn from user feedback
8. **Caching Layer**: Redis/Memcached for common queries
9. **A/B Testing**: Test different ranking algorithms
10. **Real-time Updates**: WebSocket support for live news

### Contributing

When extending the service:
- Maintain async/await patterns
- Add comprehensive logging
- Update tests
- Document new features
- Follow existing code style
- Update this README

## License

Part of the Personal Podcast Generator - Prosper AI Hiring Assessment

---

**Questions or Issues?**
Contact the development team or open an issue in the project repository.
