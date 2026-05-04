"""
News Service for fetching and ranking relevant news articles using Firecrawl API.

This module provides production-grade news fetching capabilities with:
- Async/await for all network operations
- Comprehensive error handling and retries
- Rate limiting and cost tracking
- Relevance scoring based on user interests
- Date filtering for recent news
- Structured logging for observability
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import Counter
import re

from pydantic import BaseModel, Field, HttpUrl, validator
from firecrawl import FirecrawlApp
from app.core.config import settings


# Configure logging
logger = logging.getLogger(__name__)


class FetchedNewsArticle(BaseModel):
    """
    Structured model for news articles with validation.

    Note: This is the enriched version from Firecrawl with relevance scoring.
    Use this for the news fetching pipeline, then convert to FetchedNewsArticle for script generation.

    Attributes:
        title: Article headline
        content: Full article text content
        summary: Brief summary or excerpt
        source: Publication/website name
        author: Article author (optional)
        published_date: ISO format publication date
        url: Source URL of the article
        relevance_score: Calculated relevance score (0.0 - 1.0)
        topics: Extracted topics/categories
        word_count: Approximate word count of content
    """

    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=50)
    summary: Optional[str] = Field(None, max_length=1000)
    source: str = Field(..., min_length=1, max_length=200)
    author: Optional[str] = Field(None, max_length=200)
    published_date: datetime
    url: HttpUrl
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    topics: List[str] = Field(default_factory=list)
    word_count: int = Field(default=0, ge=0)

    @validator('content')
    def calculate_word_count(cls, v, values):
        """Calculate word count from content."""
        values['word_count'] = len(v.split())
        return v

    @validator('published_date', pre=True)
    def parse_date(cls, v):
        """Parse various date formats to datetime."""
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # Try multiple date formats
            formats = [
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%dT%H:%M:%S.%f%z',
                '%Y-%m-%d',
                '%Y-%m-%dT%H:%M:%SZ',
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(v, fmt)
                except ValueError:
                    continue
            # If no format matches, try ISO format
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"Could not parse date: {v}, using current time")
                return datetime.utcnow()
        return datetime.utcnow()

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            HttpUrl: lambda v: str(v)
        }


class FirecrawlNewsServiceError(Exception):
    """Base exception for Firecrawl News Service errors."""
    pass


class RateLimitError(FirecrawlNewsServiceError):
    """Raised when API rate limit is exceeded."""
    pass


class APIError(FirecrawlNewsServiceError):
    """Raised when API returns an error response."""
    pass


class FirecrawlNewsService:
    """
    Production-grade news fetching service using Firecrawl API.

    Features:
    - Async operations for high performance
    - Intelligent relevance ranking
    - Date filtering for recent news
    - Rate limiting and retry logic
    - Cost tracking and observability
    - Comprehensive error handling
    """

    # Rate limiting configuration
    MAX_REQUESTS_PER_MINUTE = 60
    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 2  # seconds

    # API cost tracking (approximate, adjust based on actual pricing)
    SEARCH_COST_PER_REQUEST = 0.01  # USD
    SCRAPE_COST_PER_PAGE = 0.005    # USD

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_retries: int = RETRY_ATTEMPTS,
        timeout: int = 30
    ):
        """
        Initialize the Firecrawl News Service.

        Args:
            api_key: Firecrawl API key (defaults to settings)
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or settings.FIRECRAWL_API_KEY
        self.max_retries = max_retries
        self.timeout = timeout

        # Initialize Firecrawl client
        try:
            self.client = FirecrawlApp(api_key=self.api_key)
            logger.info("Firecrawl News Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firecrawl client: {e}")
            raise FirecrawlNewsServiceError(f"Initialization failed: {e}")

        # Cost tracking
        self._total_requests = 0
        self._total_cost = 0.0
        self._request_timestamps: List[datetime] = []

    async def fetch_news(
        self,
        interests: List[str],
        max_articles: int = 5,
        days_back: int = 7,
        min_relevance_score: float = 0.3
    ) -> List[FetchedNewsArticle]:
        """
        Fetch and rank news articles based on user interests.

        Args:
            interests: List of user interest keywords/topics
            max_articles: Maximum number of articles to return
            days_back: Only include articles from last N days
            min_relevance_score: Minimum relevance score threshold (0.0 - 1.0)

        Returns:
            List of FetchedNewsArticle objects sorted by relevance

        Raises:
            FirecrawlNewsServiceError: On service errors
            RateLimitError: When rate limit is exceeded
            APIError: On API errors
        """
        if not interests:
            logger.warning("No interests provided, returning empty results")
            return []

        logger.info(
            f"Fetching news for interests: {interests}, "
            f"max_articles: {max_articles}, days_back: {days_back}"
        )

        try:
            # Check rate limits
            await self._check_rate_limit()

            # Search for news articles
            raw_articles = await self._search_news(interests, max_articles * 3)

            if not raw_articles:
                logger.warning("No articles found from search")
                return []

            # Filter by date
            recent_articles = self._filter_by_date(raw_articles, days_back)
            logger.info(f"Filtered to {len(recent_articles)} recent articles")

            if not recent_articles:
                logger.warning(f"No articles found within last {days_back} days")
                return []

            # Parse and validate articles
            parsed_articles = []
            for article_data in recent_articles:
                try:
                    article = self._parse_article(article_data)
                    if article:
                        parsed_articles.append(article)
                except Exception as e:
                    logger.warning(f"Failed to parse article: {e}")
                    continue

            # Rank by relevance
            for article in parsed_articles:
                article.relevance_score = self._rank_relevance(article, interests)

            # Filter by minimum relevance score
            relevant_articles = [
                article for article in parsed_articles
                if article.relevance_score >= min_relevance_score
            ]

            # Sort by relevance and limit
            relevant_articles.sort(key=lambda x: x.relevance_score, reverse=True)
            final_articles = relevant_articles[:max_articles]

            logger.info(
                f"Returning {len(final_articles)} articles with "
                f"avg relevance: {sum(a.relevance_score for a in final_articles) / len(final_articles):.2f}"
            )

            return final_articles

        except RateLimitError:
            logger.error("Rate limit exceeded")
            raise
        except Exception as e:
            logger.error(f"Error fetching news: {e}", exc_info=True)
            raise FirecrawlNewsServiceError(f"Failed to fetch news: {e}")

    async def _search_news(
        self,
        interests: List[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Search for news articles using Firecrawl API.

        Args:
            interests: Search keywords/topics
            limit: Maximum number of results

        Returns:
            List of raw article data dictionaries
        """
        # Build search query
        query = self._build_search_query(interests)
        logger.debug(f"Search query: {query}")

        # Execute search with retry logic
        for attempt in range(self.max_retries):
            try:
                # Note: Firecrawl's Python SDK may need to be used in sync mode
                # and wrapped with asyncio.to_thread for true async behavior
                result = await asyncio.to_thread(
                    self._execute_search,
                    query,
                    limit
                )

                self._track_request(cost=self.SEARCH_COST_PER_REQUEST)
                return result

            except Exception as e:
                logger.warning(
                    f"Search attempt {attempt + 1}/{self.max_retries} failed: {e}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    raise APIError(f"Search failed after {self.max_retries} attempts: {e}")

        return []

    def _execute_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Execute synchronous search call to Firecrawl API.

        Args:
            query: Search query string
            limit: Maximum results

        Returns:
            List of search results
        """
        try:
            # Use Firecrawl's search functionality
            # Note: Adjust based on actual Firecrawl API methods
            response = self.client.search(query, params={
                'limit': limit,
                'formats': ['markdown', 'html'],
            })

            if isinstance(response, dict) and 'data' in response:
                return response['data']
            elif isinstance(response, list):
                return response
            else:
                logger.warning(f"Unexpected response format: {type(response)}")
                return []

        except AttributeError:
            # Fallback: If search is not available, use scraping with URLs
            logger.warning("Search method not available, using alternative approach")
            return self._fallback_news_fetch(query, limit)
        except Exception as e:
            logger.error(f"Search execution failed: {e}")
            raise

    def _fallback_news_fetch(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Fallback method using direct URL scraping for known news sources.

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of scraped articles
        """
        # Example news sources to scrape
        news_sources = [
            f"https://news.google.com/search?q={query.replace(' ', '+')}",
            f"https://www.bbc.com/search?q={query.replace(' ', '+')}",
        ]

        articles = []
        for url in news_sources[:limit]:
            try:
                result = self.client.scrape_url(url)
                if result:
                    articles.append(result)
                    self._track_request(cost=self.SCRAPE_COST_PER_PAGE)
            except Exception as e:
                logger.warning(f"Failed to scrape {url}: {e}")
                continue

        return articles

    def _build_search_query(self, interests: List[str]) -> str:
        """
        Build optimized search query from interests.

        Args:
            interests: List of interest keywords

        Returns:
            Formatted search query string
        """
        # Combine interests with OR logic for broad coverage
        # Add "news" keyword to focus on news content
        query_parts = [f'"{interest}" news' for interest in interests[:5]]
        return ' OR '.join(query_parts)

    def _filter_by_date(
        self,
        articles: List[Dict[str, Any]],
        days_back: int
    ) -> List[Dict[str, Any]]:
        """
        Filter articles to only include recent publications.

        Args:
            articles: List of article dictionaries
            days_back: Include articles from last N days

        Returns:
            Filtered list of recent articles
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        filtered = []

        for article in articles:
            # Try to extract publication date
            pub_date = self._extract_date(article)

            if pub_date and pub_date >= cutoff_date:
                filtered.append(article)
            elif not pub_date:
                # If no date found, include it (will be handled in parsing)
                logger.debug(f"No date found for article, including: {article.get('url', 'unknown')}")
                filtered.append(article)

        return filtered

    def _extract_date(self, article: Dict[str, Any]) -> Optional[datetime]:
        """
        Extract publication date from article data.

        Args:
            article: Article data dictionary

        Returns:
            Parsed datetime or None
        """
        # Try common date field names
        date_fields = ['published_date', 'publishedAt', 'date', 'pubDate', 'published']

        for field in date_fields:
            if field in article and article[field]:
                try:
                    if isinstance(article[field], str):
                        return datetime.fromisoformat(article[field].replace('Z', '+00:00'))
                    elif isinstance(article[field], datetime):
                        return article[field]
                except (ValueError, AttributeError):
                    continue

        return None

    def _parse_article(self, data: Dict[str, Any]) -> Optional[FetchedNewsArticle]:
        """
        Parse raw article data into FetchedNewsArticle model.

        Args:
            data: Raw article data from API

        Returns:
            FetchedNewsArticle instance or None if parsing fails
        """
        try:
            # Extract fields with fallbacks
            title = data.get('title') or data.get('headline') or 'Untitled'

            # Content can be in various fields
            content = (
                data.get('content') or
                data.get('markdown') or
                data.get('text') or
                data.get('description') or
                ''
            )

            if len(content) < 50:
                logger.debug(f"Article content too short, skipping: {title}")
                return None

            # Build FetchedNewsArticle
            article = FetchedNewsArticle(
                title=title,
                content=content,
                summary=data.get('summary') or data.get('excerpt'),
                source=data.get('source') or data.get('domain') or 'Unknown',
                author=data.get('author'),
                published_date=data.get('published_date') or data.get('publishedAt') or datetime.utcnow(),
                url=data.get('url') or data.get('link') or 'https://example.com',
                topics=data.get('topics') or data.get('categories') or [],
            )

            return article

        except Exception as e:
            logger.warning(f"Failed to parse article: {e}")
            return None

    def _rank_relevance(
        self,
        article: FetchedNewsArticle,
        interests: List[str]
    ) -> float:
        """
        Calculate relevance score for article based on user interests.

        Uses TF-IDF-like scoring with multiple factors:
        - Keyword frequency in title (higher weight)
        - Keyword frequency in content
        - Topic matching
        - Recency bonus

        Args:
            article: FetchedNewsArticle to score
            interests: User interest keywords

        Returns:
            Relevance score between 0.0 and 1.0
        """
        if not interests:
            return 0.5  # Neutral score if no interests

        # Normalize interests to lowercase
        interests_lower = [i.lower() for i in interests]

        # Score components
        title_score = 0.0
        content_score = 0.0
        topic_score = 0.0
        recency_score = 0.0

        # 1. Title matching (40% weight)
        title_text = article.title.lower()
        title_matches = sum(1 for interest in interests_lower if interest in title_text)
        title_score = min(title_matches / len(interests), 1.0) * 0.4

        # 2. Content matching (30% weight)
        content_text = article.content.lower()
        content_words = re.findall(r'\w+', content_text)
        content_counter = Counter(content_words)

        interest_frequency = sum(
            content_counter.get(interest.replace(' ', ''), 0)
            for interest in interests_lower
        )
        # Normalize by content length
        if article.word_count > 0:
            content_score = min(interest_frequency / article.word_count * 100, 1.0) * 0.3

        # 3. Topic matching (20% weight)
        if article.topics:
            article_topics_lower = [t.lower() for t in article.topics]
            topic_matches = sum(
                1 for interest in interests_lower
                if any(interest in topic for topic in article_topics_lower)
            )
            topic_score = min(topic_matches / len(interests), 1.0) * 0.2

        # 4. Recency bonus (10% weight)
        age_hours = (datetime.utcnow() - article.published_date).total_seconds() / 3600
        # Exponential decay: newer = higher score
        recency_score = max(0, 1 - (age_hours / (24 * 7))) * 0.1  # 7-day decay

        # Total score
        total_score = title_score + content_score + topic_score + recency_score

        logger.debug(
            f"Relevance for '{article.title[:50]}...': "
            f"title={title_score:.2f}, content={content_score:.2f}, "
            f"topics={topic_score:.2f}, recency={recency_score:.2f}, "
            f"total={total_score:.2f}"
        )

        return min(total_score, 1.0)

    async def _check_rate_limit(self) -> None:
        """
        Check and enforce API rate limits.

        Raises:
            RateLimitError: If rate limit would be exceeded
        """
        now = datetime.utcnow()

        # Clean old timestamps (older than 1 minute)
        self._request_timestamps = [
            ts for ts in self._request_timestamps
            if (now - ts).total_seconds() < 60
        ]

        # Check if we're at the limit
        if len(self._request_timestamps) >= self.MAX_REQUESTS_PER_MINUTE:
            wait_time = 60 - (now - self._request_timestamps[0]).total_seconds()
            logger.warning(f"Rate limit reached, need to wait {wait_time:.1f}s")
            raise RateLimitError(
                f"Rate limit exceeded. Please wait {wait_time:.1f} seconds."
            )

        # Add current request timestamp
        self._request_timestamps.append(now)

    def _track_request(self, cost: float) -> None:
        """
        Track API usage and costs.

        Args:
            cost: Estimated cost in USD for this request
        """
        self._total_requests += 1
        self._total_cost += cost

        logger.info(
            f"API Usage - Total requests: {self._total_requests}, "
            f"Total cost: ${self._total_cost:.4f}"
        )

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get current usage statistics.

        Returns:
            Dictionary with usage metrics
        """
        return {
            'total_requests': self._total_requests,
            'total_cost_usd': round(self._total_cost, 4),
            'requests_last_minute': len(self._request_timestamps),
            'rate_limit': self.MAX_REQUESTS_PER_MINUTE,
        }

    def reset_usage_stats(self) -> None:
        """Reset usage tracking counters."""
        self._total_requests = 0
        self._total_cost = 0.0
        self._request_timestamps = []
        logger.info("Usage statistics reset")


# Singleton instance for convenience
_service_instance: Optional[FirecrawlNewsService] = None


def get_news_service() -> FirecrawlNewsService:
    """
    Get or create singleton news service instance.

    Returns:
        FirecrawlNewsService instance
    """
    global _service_instance

    if _service_instance is None:
        _service_instance = FirecrawlNewsService()
        logger.info("Created new FirecrawlNewsService singleton instance")

    return _service_instance
