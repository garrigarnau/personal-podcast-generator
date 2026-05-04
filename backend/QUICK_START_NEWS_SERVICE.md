# Quick Start: FirecrawlNewsService

## 5-Minute Setup Guide

### 1. Prerequisites

Ensure you have:
- Python 3.11+
- Firecrawl API key (get from https://firecrawl.dev)
- Environment variables configured

```bash
# In your .env file
FIRECRAWL_API_KEY=your_api_key_here
```

### 2. Basic Usage

```python
import asyncio
from app.services import get_news_service

async def main():
    # Get service instance
    service = get_news_service()

    # Fetch news
    articles = await service.fetch_news(
        interests=["artificial intelligence", "startups"],
        max_articles=5
    )

    # Use the articles
    for article in articles:
        print(f"{article.title} - Score: {article.relevance_score:.2f}")

asyncio.run(main())
```

### 3. Common Parameters

```python
articles = await service.fetch_news(
    interests=["tech", "AI"],        # Required: list of topics
    max_articles=5,                  # Optional: default 5
    days_back=7,                     # Optional: default 7 days
    min_relevance_score=0.3          # Optional: default 0.3 (0.0-1.0)
)
```

### 4. Full Pipeline Example

```python
from app.services import (
    get_news_service,
    NewsArticle,
    generate_podcast_script
)

async def generate_podcast():
    # Step 1: Fetch news
    fetched = await get_news_service().fetch_news(
        interests=["technology"],
        max_articles=3
    )

    # Step 2: Convert format
    articles = [
        NewsArticle(
            title=a.title,
            summary=a.summary or a.content[:500],
            content=a.content,
            source=a.source,
            url=str(a.url),
            published_at=a.published_date,
            category=a.topics[0] if a.topics else None
        )
        for a in fetched
    ]

    # Step 3: Generate script
    script, metrics = await generate_podcast_script(
        articles=articles,
        tone="casual",
        length="medium"
    )

    print(f"Generated {script.total_word_count} word script")
    return script

asyncio.run(generate_podcast())
```

### 5. Error Handling

```python
from app.services.news_service import (
    FirecrawlNewsServiceError,
    RateLimitError,
    APIError
)

try:
    articles = await service.fetch_news(interests=["tech"])
except RateLimitError:
    print("Hit rate limit, waiting...")
    await asyncio.sleep(60)
except APIError as e:
    print(f"API error: {e}")
except FirecrawlNewsServiceError as e:
    print(f"Service error: {e}")
```

### 6. Monitoring Usage

```python
# Check API usage
stats = service.get_usage_stats()
print(f"Requests: {stats['total_requests']}")
print(f"Cost: ${stats['total_cost_usd']:.4f}")

# Reset counters
service.reset_usage_stats()
```

### 7. Testing

```bash
# Run test script
cd backend
python -m test_news_service
```

### 8. Common Issues

**No articles found?**
- Check interests are not too specific
- Lower `min_relevance_score` to 0.2
- Increase `days_back` to 14
- Verify API key is valid

**Rate limit errors?**
- Add delays between requests
- Reduce request frequency
- Check `get_usage_stats()`

**Low relevance scores?**
- Use more specific interests
- Try different keyword combinations
- Check article topics match interests

### 9. Production Best Practices

```python
# Use singleton pattern
service = get_news_service()  # ✓ Good

# Don't create multiple instances
service = FirecrawlNewsService()  # ✗ Avoid

# Cache results
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_fetch(interests_tuple):
    return asyncio.run(
        get_news_service().fetch_news(
            interests=list(interests_tuple)
        )
    )

# Monitor costs
if service.get_usage_stats()['total_cost_usd'] > 10:
    logger.warning("High API usage!")
```

### 10. Next Steps

- Read full documentation: `NEWS_SERVICE_README.md`
- Check integration example: `example_integration.py`
- Review source code: `app/services/news_service.py`

## Quick Reference

### Import Statements
```python
from app.services import (
    get_news_service,           # Get singleton instance
    FetchedNewsArticle,         # Article model
    FirecrawlNewsServiceError,  # Base exception
    RateLimitError,             # Rate limit error
    APIError,                   # API error
)
```

### Article Properties
```python
article.title              # str
article.content            # str
article.summary            # Optional[str]
article.source             # str
article.author             # Optional[str]
article.published_date     # datetime
article.url                # HttpUrl
article.relevance_score    # float (0.0-1.0)
article.topics             # List[str]
article.word_count         # int
```

### Service Methods
```python
await service.fetch_news(...)           # Main fetch method
service.get_usage_stats()               # Get usage metrics
service.reset_usage_stats()             # Reset counters
```

---

**Need Help?**
- Check logs for detailed error messages
- Review `NEWS_SERVICE_README.md` for comprehensive docs
- Run `test_news_service.py` to verify setup
