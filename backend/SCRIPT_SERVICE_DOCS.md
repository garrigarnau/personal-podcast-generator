# Script Generation Service Documentation

## Overview

The Script Generation Service is a production-quality service that transforms news articles into engaging conversational podcast scripts using OpenAI's GPT-4o. It creates natural dialogues between two hosts (Alex and Sonia) with configurable tone, length, and comprehensive error handling.

## Features

### Core Capabilities
- **Async OpenAI Integration**: Uses async OpenAI client for non-blocking operations
- **Dual Host System**: Creates dialogue between Alex (enthusiastic) and Sonia (analytical)
- **Configurable Parameters**: Adjustable tone (Serious/Casual/Balanced) and length (Short/Medium/Long)
- **Structured Output**: Produces well-formatted scripts with speaker tags, emotional cues, and break markers
- **Token Tracking**: Monitors token usage for cost estimation and optimization
- **Error Handling**: Comprehensive error handling with automatic retries and exponential backoff
- **Production Logging**: Detailed logging for monitoring and debugging

### Advanced Features
- **Prompt Versioning**: Version-controlled prompts for iterative improvement
- **Cost Monitoring**: Real-time cost estimation based on token usage
- **Performance Metrics**: Tracks latency, retry count, and resource usage
- **Speaker Balance Analysis**: Monitors speaking time distribution between hosts
- **Duration Estimation**: Calculates estimated audio duration based on word count

## Architecture

### Class Structure

```
ScriptGeneratorService
├── generate_script()          # Main entry point
├── _build_system_prompt()     # Creates tone-specific system instructions
├── _build_user_prompt()       # Formats articles into user prompt
├── _call_openai()             # Handles API communication
├── _parse_script()            # Parses raw output into structured format
└── _calculate_cost()          # Estimates API costs
```

### Data Models

#### NewsArticle
Input data structure for news content:
```python
{
    "title": str,
    "summary": str,
    "content": str,
    "source": Optional[str],
    "url": Optional[str],
    "published_at": Optional[datetime],
    "category": Optional[str]
}
```

#### PodcastScript
Output data structure for generated scripts:
```python
{
    "segments": List[ScriptSegment],
    "total_word_count": int,
    "estimated_duration_seconds": int,
    "tone": ToneType,
    "length": LengthType,
    "topics_covered": List[str],
    "sources_cited": List[str],
    "generation_metadata": Dict[str, Any],
    "created_at": datetime
}
```

#### ScriptSegment
Individual speaker turn:
```python
{
    "speaker": SpeakerType,  # ALEX or SONIA
    "text": str,
    "order": int,
    "emotion": Optional[str],
    "pause_after": bool
}
```

#### GenerationMetrics
Performance and cost metrics:
```python
{
    "tokens_used": int,
    "prompt_tokens": int,
    "completion_tokens": int,
    "model_used": str,
    "latency_ms": int,
    "retry_count": int,
    "cost_estimate": float
}
```

## Configuration

### Tone Types
- **Serious**: Professional, fact-focused, data-driven discourse
- **Casual**: Conversational, relatable, approachable language
- **Balanced**: Mix of professionalism and accessibility (default)

### Length Types
| Length | Target Words | Estimated Duration | Max Tokens |
|--------|-------------|-------------------|------------|
| Short  | ~750 words  | ~5 minutes        | 1,500      |
| Medium | ~1,500 words| ~10 minutes       | 3,000      |
| Long   | ~2,250 words| ~15 minutes       | 4,500      |

### Model Settings
- **Model**: GPT-4o (gpt-4o)
- **Temperature**: 0.8 (for creative, natural conversation)
- **Frequency Penalty**: 0.3 (reduce repetition)
- **Presence Penalty**: 0.2 (encourage topic diversity)

### Cost Structure (GPT-4o Pricing)
- **Input Tokens**: $0.0025 per 1K tokens ($2.50 per 1M)
- **Output Tokens**: $0.01 per 1K tokens ($10.00 per 1M)

### Retry Configuration
- **Max Retries**: 3
- **Initial Delay**: 1 second
- **Backoff Strategy**: Exponential (2^attempt)
- **Max Delay**: 10 seconds

## Usage

### Basic Usage

```python
from app.services.script_service import ScriptGeneratorService, NewsArticle

# Initialize service
service = ScriptGeneratorService()

# Prepare articles
articles = [
    NewsArticle(
        title="Breaking News...",
        summary="Summary...",
        content="Full content...",
        source="News Source",
        category="Technology"
    )
]

# Generate script
script, metrics = await service.generate_script(
    news_articles=articles,
    preferences={"tone": "casual", "length": "medium"}
)

# Access results
print(f"Generated {script.total_word_count} words")
print(f"Cost: ${metrics.cost_estimate}")
print(script.get_full_text())
```

### Convenience Function

```python
from app.services.script_service import generate_podcast_script

# Quick generation
script, metrics = await generate_podcast_script(
    articles=articles,
    tone="balanced",
    length="short"
)
```

### Advanced Usage

```python
# Custom API key
service = ScriptGeneratorService(api_key="sk-...")

# Generate with preferences
script, metrics = await service.generate_script(
    news_articles=articles,
    preferences={
        "tone": "serious",
        "length": "long",
        "topics": ["AI", "Technology"],
        "sources": ["TechNews"]
    }
)

# Analyze speaker balance
balance = script.get_speaker_balance()
print(f"Alex: {balance['alex_percentage']}%")
print(f"Sonia: {balance['sonia_percentage']}%")

# Access individual segments
for segment in script.segments:
    print(f"[{segment.speaker.value}]: {segment.text}")
    if segment.emotion:
        print(f"  Emotion: {segment.emotion}")
    if segment.pause_after:
        print("  [BREAK]")
```

## Prompt Engineering

### System Prompt Structure

1. **Character Definitions**: Establishes Alex (enthusiastic) and Sonia (analytical) personas
2. **Tone Instructions**: Specific guidance based on selected tone
3. **Format Requirements**: Speaker tags, emotional cues, break markers
4. **Structure Guidelines**: Opening hook, body exploration, discussion, conclusion
5. **Conversation Tips**: Natural dialogue patterns, reactions, engagement

### User Prompt Components

1. **Article Content**: Title, source, summary, content (truncated to 1000 chars)
2. **Specifications**: Target word count, tone, format requirements
3. **Instructions**: Focus areas, engagement goals

### Output Format

```
[ALEX]: Welcome to today's episode! We've got some fascinating stories to dive into.

[SONIA] (thoughtful): Indeed, Alex. Let's start with this quantum computing breakthrough...

[ALEX] (excited): Wait, 100x speed improvement? That's incredible!

[BREAK]

[SONIA]: Let me explain what makes this so significant...
```

## Error Handling

### Handled Errors

1. **RateLimitError**: Automatic retry with exponential backoff
2. **APITimeoutError**: Retry with increased delay
3. **OpenAIError**: Logged and re-raised with context
4. **ValueError**: Input validation errors (empty articles, invalid preferences)
5. **Parsing Errors**: Graceful handling of malformed GPT output

### Retry Strategy

```python
for attempt in range(MAX_RETRIES):
    try:
        # API call
        break
    except RateLimitError:
        delay = min(INITIAL_DELAY * (2 ** attempt), MAX_DELAY)
        await asyncio.sleep(delay)
```

### Logging Levels

- **INFO**: Successful operations, script generation metrics
- **WARNING**: Retries, rate limits
- **ERROR**: API failures, parsing errors

## Performance Optimization

### Token Efficiency
- Truncates article content to 1000 characters
- Limits to 5 articles per script
- Optimized prompt structure

### Response Time
- Async operations for non-blocking execution
- Configurable timeouts
- Parallel article processing (future enhancement)

### Cost Optimization
- Token usage tracking
- Length-appropriate max_tokens
- Efficient prompt engineering

## Monitoring and Metrics

### Key Metrics to Track

1. **Token Usage**
   - Prompt tokens
   - Completion tokens
   - Total tokens per request

2. **Performance**
   - Latency (ms)
   - Retry count
   - Success rate

3. **Cost**
   - Per-request cost
   - Daily/monthly totals
   - Cost per podcast

4. **Quality**
   - Word count accuracy
   - Speaker balance
   - Duration estimates

### Logging Examples

```
INFO - ScriptGeneratorService initialized with prompt version 1.0.0
INFO - Generating script: tone=casual, length=medium, articles=3
INFO - Script generated: 1523 tokens, 2150ms, $0.0428
INFO - Script parsed: 47 segments, 1487 words, 595s, balance={'alex_percentage': 52.3, 'sonia_percentage': 47.7}
WARNING - Rate limit hit, retrying in 2.0s (attempt 2/3)
ERROR - OpenAI API error: Invalid API key
```

## Testing

### Unit Tests
```bash
# Run test suite
python backend/test_script_service.py
```

### Test Coverage
- Basic script generation
- All tone/length combinations
- Single vs. multiple articles
- Error handling
- Edge cases

### Example Test Output
```
TEST 1: Basic Script Generation (Balanced tone, Medium length)
✓ Script generated successfully!
  - Segments: 45
  - Word count: 1502
  - Duration: 601s (10m 1s)
  - Tokens used: 1523 (prompt: 845, completion: 678)
  - Cost estimate: $0.0428
```

## Integration

### With Podcast Model
```python
from app.models import Podcast
from app.services.script_service import generate_podcast_script

# Generate script
script, metrics = await generate_podcast_script(
    articles=articles,
    tone=user.preferences.get("tone", "balanced"),
    length=user.preferences.get("length", "medium")
)

# Save to database
podcast = Podcast(
    user_id=user.id,
    script=script.get_full_text(),
    status=PodcastStatus.PROCESSING,
    metadata={
        "word_count": script.total_word_count,
        "duration": script.estimated_duration_seconds,
        "topics": script.topics_covered
    }
)
```

### With Metrics Tracking
```python
from app.models import Metrics

# Create metrics record
metrics_record = Metrics(
    podcast_id=podcast.id,
    tokens_used=metrics.tokens_used,
    script_generation_ms=metrics.latency_ms,
    cost_estimate=metrics.cost_estimate
)
```

## Best Practices

### Do's
✅ Use async/await for all operations
✅ Handle rate limits gracefully with retries
✅ Log important events and errors
✅ Validate input data before processing
✅ Monitor token usage and costs
✅ Test with various article types and lengths
✅ Version control prompt templates

### Don'ts
❌ Don't block with synchronous calls
❌ Don't ignore error handling
❌ Don't expose API keys in logs
❌ Don't process too many articles at once (limit: 5)
❌ Don't skip input validation
❌ Don't set temperature too high (>0.9) or too low (<0.5)

## Troubleshooting

### Common Issues

**Issue**: Scripts too short/long
- **Solution**: Adjust LENGTH_CONFIG target_words and max_tokens

**Issue**: Rate limit errors
- **Solution**: Increase INITIAL_RETRY_DELAY or implement request queue

**Issue**: Poor speaker balance
- **Solution**: Update system prompt to emphasize alternating speakers

**Issue**: Unnatural dialogue
- **Solution**: Adjust temperature, update conversation tips in prompt

**Issue**: High costs
- **Solution**: Reduce max_tokens, optimize prompt length, use caching

## Future Enhancements

### Planned Features
- [ ] Prompt template management system
- [ ] A/B testing framework for prompts
- [ ] Multi-language support
- [ ] Custom host persona configuration
- [ ] Style transfer (match specific podcast styles)
- [ ] Fact-checking integration
- [ ] Citation management
- [ ] Audio timing markers
- [ ] Script editing interface

### Performance Improvements
- [ ] Parallel article processing
- [ ] Response streaming for faster UX
- [ ] Prompt caching
- [ ] Fine-tuned model for podcast scripts
- [ ] Batch processing for multiple scripts

## Version History

### v1.0.0 (Current)
- Initial production release
- GPT-4o integration
- Configurable tone and length
- Comprehensive error handling
- Token tracking and cost estimation
- Structured output parsing
- Production logging

## Support

For issues or questions:
1. Check logs for error details
2. Review test suite for usage examples
3. Verify API key configuration
4. Check OpenAI API status
5. Contact development team

## License

Proprietary - Prosper AI Assessment Project
