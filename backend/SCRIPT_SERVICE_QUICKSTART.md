# Script Service Quick Start Guide

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
# Already included in requirements.txt
pip install openai==1.54.3
```

### 2. Configure API Key
```bash
# Add to .env file
OPENAI_API_KEY=sk-your-openai-api-key
```

### 3. Import and Use
```python
from app.services.script_service import generate_podcast_script, NewsArticle

# Create article
article = NewsArticle(
    title="Your Article Title",
    summary="Brief summary",
    content="Full article content...",
    source="Source Name",
    category="Technology"
)

# Generate script
script, metrics = await generate_podcast_script(
    articles=[article],
    tone="casual",      # or "serious", "balanced"
    length="medium"     # or "short", "long"
)

# Use the script
print(f"Generated {script.total_word_count} words")
print(script.get_full_text())
```

## 📚 Common Use Cases

### Use Case 1: Basic Generation
```python
from app.services import ScriptGeneratorService, NewsArticle

service = ScriptGeneratorService()
articles = [NewsArticle(...)]

script, metrics = await service.generate_script(
    news_articles=articles,
    preferences={"tone": "balanced", "length": "medium"}
)
```

### Use Case 2: With User Preferences
```python
# From user model
user_prefs = user.preferences

script, metrics = await generate_podcast_script(
    articles=articles,
    tone=user_prefs.get("tone", "balanced"),
    length=user_prefs.get("podcast_length", "medium")
)
```

### Use Case 3: Save to Database
```python
from app.models import Podcast, Metrics as MetricsModel

# Generate script
script, metrics = await generate_podcast_script(articles, "casual", "short")

# Create podcast record
podcast = Podcast(
    user_id=user.id,
    script=script.get_full_text(),
    status=PodcastStatus.PROCESSING,
    metadata={"word_count": script.total_word_count}
)
db.add(podcast)

# Create metrics record
metrics_record = MetricsModel(
    podcast_id=podcast.id,
    tokens_used=metrics.tokens_used,
    script_generation_ms=metrics.latency_ms,
    cost_estimate=metrics.cost_estimate
)
db.add(metrics_record)
await db.commit()
```

### Use Case 4: Error Handling
```python
from openai import OpenAIError

try:
    script, metrics = await generate_podcast_script(
        articles=articles,
        tone="casual",
        length="medium"
    )
except ValueError as e:
    print(f"Invalid input: {e}")
except OpenAIError as e:
    print(f"API error: {e}")
    # Log error, retry later, or notify user
```

## 🎛️ Configuration Options

### Tone Types
- **`serious`**: Professional, data-driven, factual
- **`casual`**: Conversational, friendly, accessible
- **`balanced`**: Mix of both (recommended)

### Length Types
- **`short`**: ~5 minutes (~750 words)
- **`medium`**: ~10 minutes (~1500 words)
- **`long`**: ~15 minutes (~2250 words)

## 📊 Monitoring

### Access Metrics
```python
script, metrics = await generate_podcast_script(...)

print(f"Tokens: {metrics.tokens_used}")
print(f"Cost: ${metrics.cost_estimate}")
print(f"Latency: {metrics.latency_ms}ms")
print(f"Retries: {metrics.retry_count}")
```

### Speaker Balance
```python
balance = script.get_speaker_balance()
print(f"Alex: {balance['alex_percentage']}%")
print(f"Sonia: {balance['sonia_percentage']}%")
```

### Script Details
```python
print(f"Word count: {script.total_word_count}")
print(f"Duration: {script.estimated_duration_seconds}s")
print(f"Segments: {len(script.segments)}")
print(f"Topics: {script.topics_covered}")
print(f"Sources: {script.sources_cited}")
```

## 🧪 Testing

### Run Tests
```bash
cd backend
python test_script_service.py
```

### Example Integration
```bash
python example_integration.py
```

## 💡 Best Practices

### ✅ Do
- Validate articles before passing to service
- Handle errors gracefully with try/except
- Log metrics for monitoring
- Use async/await properly
- Monitor costs in production
- Test with various article types

### ❌ Don't
- Don't pass empty article lists
- Don't block async operations
- Don't ignore error handling
- Don't process too many articles at once (limit: 5)
- Don't expose API keys in logs

## 🔧 Troubleshooting

### Issue: Rate Limit Errors
```python
# Service automatically retries with backoff
# If persistent, implement request queuing:
from asyncio import Semaphore

semaphore = Semaphore(5)  # Max 5 concurrent requests

async def generate_with_limit(articles, tone, length):
    async with semaphore:
        return await generate_podcast_script(articles, tone, length)
```

### Issue: High Costs
```python
# Use shorter lengths
script, metrics = await generate_podcast_script(
    articles=articles[:3],  # Limit articles
    tone="casual",
    length="short"  # Shorter = cheaper
)
```

### Issue: Poor Quality Scripts
```python
# Adjust preferences
preferences = {
    "tone": "balanced",  # Try different tones
    "length": "medium"   # Medium often best quality
}

# Filter articles by relevance
high_quality_articles = [
    a for a in articles
    if a.relevance_score > 0.7
][:5]
```

## 📖 API Reference

### NewsArticle
```python
NewsArticle(
    title: str,              # Required
    summary: str,            # Required
    content: str,            # Required
    source: str = None,      # Optional
    url: str = None,         # Optional
    published_at: datetime = None,  # Optional
    category: str = None     # Optional
)
```

### generate_podcast_script()
```python
await generate_podcast_script(
    articles: List[NewsArticle],  # Required
    tone: str = "balanced",       # Optional
    length: str = "medium"        # Optional
) -> Tuple[PodcastScript, GenerationMetrics]
```

### PodcastScript Properties
```python
script.segments              # List[ScriptSegment]
script.total_word_count      # int
script.estimated_duration_seconds  # int
script.tone                  # ToneType
script.length               # LengthType
script.topics_covered       # List[str]
script.sources_cited        # List[str]
script.get_full_text()      # str
script.get_speaker_balance() # Dict[str, float]
```

### GenerationMetrics Properties
```python
metrics.tokens_used         # int
metrics.prompt_tokens       # int
metrics.completion_tokens   # int
metrics.model_used          # str
metrics.latency_ms          # int
metrics.retry_count         # int
metrics.cost_estimate       # float
```

## 🎯 Production Checklist

- [ ] Set OPENAI_API_KEY in environment
- [ ] Configure logging level (INFO in production)
- [ ] Set up error monitoring (Sentry, etc.)
- [ ] Implement cost tracking and alerts
- [ ] Add rate limiting if needed
- [ ] Test with production data
- [ ] Monitor metrics dashboard
- [ ] Set up API key rotation
- [ ] Configure backup API keys
- [ ] Test error recovery scenarios

## 📞 Support

See full documentation: `SCRIPT_SERVICE_DOCS.md`

For issues:
1. Check logs for detailed error messages
2. Verify API key configuration
3. Review test suite examples
4. Check OpenAI API status page
