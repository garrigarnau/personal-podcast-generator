# Podcast Generation Workflow

Complete end-to-end workflow documentation for the Personal Podcast Generator, from user input to finished audio podcast.

## Table of Contents

- [Overview](#overview)
- [Architecture Diagram](#architecture-diagram)
- [Detailed Workflow](#detailed-workflow)
- [Stage 1: News Discovery](#stage-1-news-discovery)
- [Stage 2: Script Generation](#stage-2-script-generation)
- [Stage 3: Audio Generation](#stage-3-audio-generation)
- [Data Flow](#data-flow)
- [Error Handling](#error-handling)
- [Performance Metrics](#performance-metrics)

---

## Overview

The podcast generation system orchestrates multiple AI services to transform web articles into engaging multi-speaker audio content. The entire process takes **15-25 seconds** and costs approximately **$0.06-0.12 per podcast**.

### Services Involved

| Service | Purpose | Model/API | Approx. Cost |
|---------|---------|-----------|--------------|
| News API | Article discovery | REST API | Free tier |
| Firecrawl | Web scraping | REST API | ~$0.01 |
| OpenAI GPT-4o | Script generation | LangChain + gpt-4o | ~$0.05 |
| ElevenLabs | Text-to-speech | eleven_flash_v2_5 | ~$0.02 |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│                      (React Frontend)                                │
│                                                                       │
│  [Set Interests] → [Choose Tone/Length] → [Generate Button]         │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ POST /api/v1/podcasts/generate
                                │ { interests, tone, length }
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         FASTAPI BACKEND                              │
│                                                                       │
│  1. Validate Request                                                 │
│  2. Create Podcast Record (status: PENDING)                         │
│  3. Add Background Task                                              │
│  4. Return 202 Accepted with podcast_id                             │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ Background Task Queue
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    PODCAST ORCHESTRATOR                              │
│                  (Background Worker Process)                         │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ STAGE 1: NEWS DISCOVERY (2-3 seconds)                       │   │
│  │                                                               │   │
│  │  ┌────────────┐      ┌─────────────┐                       │   │
│  │  │ News API   │ ───→ │ Firecrawl   │                       │   │
│  │  │ Search     │      │ Web Scrape  │                       │   │
│  │  └────────────┘      └─────────────┘                       │   │
│  │        ↓                     ↓                               │   │
│  │   [Keywords]          [Full Content]                        │   │
│  │        ↓                     ↓                               │   │
│  │  ┌──────────────────────────────┐                          │   │
│  │  │  Relevance Scoring           │                          │   │
│  │  │  Filter by Date/Topics       │                          │   │
│  │  └──────────────────────────────┘                          │   │
│  │                ↓                                             │   │
│  │    [Top 5-9 Relevant Articles]                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                ↓                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ STAGE 2: SCRIPT GENERATION (8-10 seconds)                  │   │
│  │                                                               │   │
│  │  ┌──────────────────────────────────────────────┐          │   │
│  │  │  LangChain Multi-Agent System (GPT-4o)       │          │   │
│  │  │                                               │          │   │
│  │  │  Agent 1: Content Planner                   │          │   │
│  │  │  ├─ Analyze articles                         │          │   │
│  │  │  ├─ Extract key points                       │          │   │
│  │  │  ├─ Create outline & story arc               │          │   │
│  │  │  ├─ Generate episode title                   │          │   │
│  │  │  └─ Estimate segment count                   │          │   │
│  │  │           ↓                                   │          │   │
│  │  │  Agent 2: Script Writer                      │          │   │
│  │  │  ├─ Generate dialogue (ALEX & SONIA)        │          │   │
│  │  │  ├─ Add emotional cues                       │          │   │
│  │  │  ├─ Insert breaks/transitions                │          │   │
│  │  │  ├─ Match tone (professional/casual/etc)     │          │   │
│  │  │  ├─ Validate structure internally            │          │   │
│  │  │  └─ Ensure target word count                 │          │   │
│  │  │           ↓                                   │          │   │
│  │  │  Orchestrator: Format & Validate             │          │   │
│  │  │  ├─ Parse structured JSON output             │          │   │
│  │  │  ├─ Validate segment count                   │          │   │
│  │  │  ├─ Check speaker alternation                │          │   │
│  │  │  ├─ Convert to PodcastScript format          │          │   │
│  │  │  └─ Track token usage & costs                │          │   │
│  │  └──────────────────────────────────────────────┘          │   │
│  │                ↓                                             │   │
│  │    [Complete Script with Speaker Tags]                     │   │
│  │    Format: [ALEX](emotion): text...                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                ↓                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ STAGE 3: AUDIO GENERATION (3-5 seconds)                    │   │
│  │                                                               │   │
│  │  ┌──────────────────────────────────────────────┐          │   │
│  │  │  Parse Script into Segments                  │          │   │
│  │  │  ├─ Extract speaker tags                     │          │   │
│  │  │  ├─ Split by speaker turns                   │          │   │
│  │  │  └─ Identify break markers                   │          │   │
│  │  └──────────────────────────────────────────────┘          │   │
│  │                ↓                                             │   │
│  │  ┌──────────────────────────────────────────────┐          │   │
│  │  │  For Each Segment:                           │          │   │
│  │  │                                               │          │   │
│  │  │  IF [ALEX] → ElevenLabs Voice:               │          │   │
│  │  │     pNInz6obpgDQGcFmaJgB (Adam - deep male)  │          │   │
│  │  │                                               │          │   │
│  │  │  IF [SONIA] → ElevenLabs Voice:              │          │   │
│  │  │     EXAVITQu4vr4xnSDxMaL (Bella - pro female)│          │   │
│  │  │                                               │          │   │
│  │  │  IF [BREAK] → Insert silence (1 second)      │          │   │
│  │  │                                               │          │   │
│  │  │  API Call → ElevenLabs TTS                   │          │   │
│  │  │  ├─ Model: eleven_flash_v2_5                 │          │   │
│  │  │  ├─ Format: MP3, 44.1kHz, 128kbps           │          │   │
│  │  │  ├─ Retry: 3 attempts with backoff           │          │   │
│  │  │  └─ Return: Audio segment bytes              │          │   │
│  │  └──────────────────────────────────────────────┘          │   │
│  │                ↓                                             │   │
│  │  ┌──────────────────────────────────────────────┐          │   │
│  │  │  Combine Audio Segments (pydub)              │          │   │
│  │  │  ├─ Join segments in order                   │          │   │
│  │  │  ├─ Add silence for breaks                   │          │   │
│  │  │  ├─ Normalize audio levels                   │          │   │
│  │  │  └─ Export final MP3                         │          │   │
│  │  └──────────────────────────────────────────────┘          │   │
│  │                ↓                                             │   │
│  │    [Final Podcast MP3 File]                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                ↓                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ STAGE 4: SAVE RESULTS                                       │   │
│  │                                                               │   │
│  │  Save to Database:                                           │   │
│  │  ├─ podcast.audio_url = "/tmp/podcasts/{id}.mp3"           │   │
│  │  ├─ podcast.script = full_script_text                       │   │
│  │  ├─ podcast.title = generated_title                         │   │
│  │  ├─ podcast.status = COMPLETED                              │   │
│  │  └─ podcast.metadata = {topics, sources, articles}          │   │
│  │                                                               │   │
│  │  Create Metrics Record:                                      │   │
│  │  ├─ tokens_used (OpenAI)                                    │   │
│  │  ├─ elevenlabs_characters                                   │   │
│  │  ├─ firecrawl_searches, firecrawl_scrapes                   │   │
│  │  ├─ costs (openai, elevenlabs, firecrawl)                   │   │
│  │  ├─ latency_ms (news, script, audio)                        │   │
│  │  └─ total_cost_estimate                                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ Status Updates Every 2s
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│                      (React Frontend)                                │
│                                                                       │
│  [Status Polling] → Show Progress → [Play Audio]                   │
│  - "Fetching news..."                                                │
│  - "Generating script..."                                            │
│  - "Creating audio..."                                               │
│  - "Complete! ✓"                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Workflow

### Request Initiation

**Frontend Action:**
```typescript
POST /api/v1/podcasts/generate
{
  "interests": ["AI", "Technology", "Startups"],
  "tone": "casual",
  "length": "medium",
  "sources": ["techcrunch", "theverge"],
  "mock_audio": false
}
```

**Backend Response (Immediate):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "audio_url": null,
  "error_message": null,
  "progress": 0
}
```

**Timeline:** T+0ms to T+100ms

---

## Stage 1: News Discovery

### Phase 1: Article Search

**Service:** News API
**Duration:** ~1-2 seconds
**Cost:** Free (rate-limited)

```python
# For each interest keyword
for interest in ["AI", "Technology", "Startups"]:
    results = news_api.search(
        query=interest,
        language="en",
        sort_by="publishedAt",
        from_date=datetime.now() - timedelta(days=7),
        page_size=3
    )
    candidates.extend(results.articles)

# Total: 3 interests × 3 articles = 9 candidates
```

**Output:**
```python
[
  {
    "title": "OpenAI Announces GPT-5 Release",
    "url": "https://techcrunch.com/...",
    "source": "TechCrunch",
    "publishedAt": "2025-05-01T10:30:00Z"
  },
  # ... 8 more articles
]
```

### Phase 2: Full Article Scraping

**Service:** Firecrawl API
**Duration:** ~1 second
**Cost:** ~$0.01 (varies by article count)

```python
# Scrape full content from each candidate URL
for article in candidates:
    scraped = firecrawl.scrape(
        url=article.url,
        formats=["markdown", "html"],
        only_main_content=True,
        wait_for="networkidle"
    )

    article.content = scraped.markdown
    article.summary = scraped.description
    article.topics = scraped.topics
```

**Metrics Tracked:**
- `firecrawl_searches`: Number of search queries
- `firecrawl_scrapes`: Number of articles scraped
- `firecrawl_cost`: USD cost

### Phase 3: Relevance Scoring

**Algorithm:**
```python
def calculate_relevance_score(article, interests):
    score = 0.0

    # Keyword matching (0.0 - 0.5)
    for interest in interests:
        if interest.lower() in article.content.lower():
            score += 0.1

    # Recency bonus (0.0 - 0.3)
    days_old = (now - article.publishedAt).days
    if days_old <= 1:
        score += 0.3
    elif days_old <= 3:
        score += 0.2
    elif days_old <= 7:
        score += 0.1

    # Topic matching (0.0 - 0.2)
    matching_topics = set(article.topics) & set(interests)
    score += len(matching_topics) * 0.1

    return min(score, 1.0)

# Sort by relevance and take top N
articles = sorted(articles, key=lambda a: a.relevance_score, reverse=True)[:5]
```

**Output:**
```python
[
  FetchedNewsArticle(
    title="OpenAI Announces GPT-5 Release",
    url="https://...",
    content="Full article content...",
    source="TechCrunch",
    publishedAt="2025-05-01",
    topics=["AI", "OpenAI", "LLM"],
    relevance_score=0.85
  ),
  # ... 4 more top articles
]
```

**Timeline:** T+100ms to T+3500ms

---

## Stage 2: Script Generation

### Multi-Agent Architecture

The script generation uses **LangChain** with two specialized agents coordinated by an orchestrator.

### Agent 1: Content Planner

**Responsibility:** Analyze articles and create structured outline
**Input:** List of 5-9 articles with full content
**Model:** GPT-4o (via LangChain)
**Duration:** ~2-3 seconds

```python
system_prompt = """
You are a podcast content planner. Analyze news articles and create
a compelling outline for a conversational podcast between two hosts.

Output format (JSON):
{
  "topics": ["topic1", "topic2", ...],
  "key_points": ["point1", "point2", ...],
  "narrative_arc": {
    "intro": "...",
    "body": ["segment1", "segment2", ...],
    "conclusion": "..."
  },
  "estimated_duration": 600
}
"""

content_plan = openai.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Articles: {articles}"}
    ],
    response_format={"type": "json_object"}
)
```

**Output:**
```json
{
  "topics": ["GPT-5 announcement", "AI regulation", "startup funding"],
  "key_points": [
    "OpenAI releasing GPT-5 in Q3 2025",
    "EU finalizing AI Act regulations",
    "AI startups raised $12B this quarter"
  ],
  "narrative_arc": {
    "intro": "Welcome back! Big week in AI...",
    "body": [
      "Let's start with OpenAI's GPT-5 announcement",
      "Now, shifting to regulatory news",
      "Finally, the funding landscape"
    ],
    "conclusion": "That's all for this week's tech roundup"
  },
  "estimated_duration": 600
}
```

### Agent 2: Script Writer

**Responsibility:** Generate conversational dialogue
**Input:** Content plan + tone preferences
**Model:** GPT-4o (via LangChain)
**Duration:** ~4-5 seconds

```python
system_prompt = """
You are a professional podcast script writer. Create engaging dialogue
between two hosts (ALEX and SONIA) based on the content plan.

ALEX: Deep male voice, enthusiastic, asks questions
SONIA: Professional female voice, insightful, provides context

Format:
[ALEX](enthusiastic): Welcome back everyone!
[SONIA](thoughtful): Thanks for having me, Alex.
[BREAK]

Rules:
- Natural conversation flow
- {tone} tone (professional/casual/educational/conversational)
- Target length: {word_count} words (~{duration} minutes)
- Include [BREAK] for scene transitions
- Add emotional cues in parentheses
"""

script = openai.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Plan: {content_plan}"}
    ]
)
```

**Output Example:**
```
[ALEX](enthusiastic): Hey everyone, welcome back to Tech This Week!
I'm Alex, and I'm here with Sonia.

[SONIA](warm): Thanks Alex! Great to be here. And wow, what a week
it's been in AI.

[ALEX](excited): Right?! I mean, OpenAI just dropped the news
about GPT-5. Sonia, what's your take on this?

[SONIA](thoughtful): Well, this is significant because...

[BREAK]

[ALEX](curious): Now, let's shift gears to regulations...
```

### Orchestrator: Validation & Format Conversion

**Responsibility:** Validate outputs and format for audio generation

```python
# Parse agent outputs (using RobustPydanticOutputParser)
content_plan = parse_json(agent1_output)  # ContentPlan model
script_output = parse_json(agent2_output)  # PodcastScriptOutput model

# Validate word count meets target
word_count_ratio = script_output.total_word_count / target_words
if word_count_ratio < 0.7:  # Less than 70% of target
    logger.warning(f"Script is too short: {word_count_ratio:.1%} of target")

# Validate segment count and speaker alternation
# (Built into Pydantic validation - see lines 185-206)
if len(script_output.segments) < 10:
    raise ValueError("Must have at least 10 segments")

# Warn if same speaker talks 5+ times consecutively
# (Automatic validation in PodcastScriptOutput model)

# Convert to PodcastScript format
podcast_script = PodcastScript(
    title=content_plan.title,  # Title from Content Planner
    segments=[
        ScriptSegment(
            speaker=seg.speaker,
            text=seg.text,
            emotion=seg.emotion,
            pause_after=seg.pause_after,
            order=i
        )
        for i, seg in enumerate(script_output.segments)
    ],
    word_count=script_output.total_word_count,
    estimated_duration=word_count / 150 * 60,  # 150 WPM
    tone=tone,
    length=length,
    topics_covered=script_output.topics_covered,
    sources_cited=script_output.sources_cited,
    generation_metadata={
        "langchain_version": "1.0.0",
        "model": "gpt-4o",
        "multi_agent": True,
        "articles_count": len(articles)
    }
)

# Track metrics
metrics.tokens_used = total_tokens_from_both_agents
metrics.openai_cost = calculate_cost(tokens_used, model="gpt-4o")
```

**Metrics Tracked:**
- `tokens_used`: Total OpenAI tokens consumed
- `openai_cost`: USD cost (~$0.05 for ~1500 tokens)
- `script_generation_ms`: Time taken

**Quality Validation:**
The Script Writer agent (Agent 2) includes built-in quality checks:
- Pydantic validation ensures proper JSON structure
- Minimum segment count enforced (10+)
- Speaker alternation validated (no 5+ consecutive turns)
- Word count tracked and validated against target
- Tone consistency maintained through prompt instructions

**Timeline:** T+3500ms to T+13500ms

---

## Stage 3: Audio Generation

### Process Flow

```python
# 1. Parse script into segments
segments = []
for line in script.split('\n'):
    if match := re.match(r'\[(\w+)\]\((\w+)\):\s*(.+)', line):
        speaker, emotion, text = match.groups()
        segments.append({
            'speaker': speaker,
            'emotion': emotion,
            'text': text
        })
    elif '[BREAK]' in line:
        segments.append({'type': 'break', 'duration': 1.0})

# 2. Map speakers to voices
VOICE_MAPPING = {
    'ALEX': 'pNInz6obpgDQGcFmaJgB',   # Adam (deep male)
    'SONIA': 'EXAVITQu4vr4xnSDxMaL'   # Bella (professional female)
}

# 3. Generate audio for each segment
audio_segments = []
for segment in segments:
    if segment.get('type') == 'break':
        # Insert silence
        silence = AudioSegment.silent(duration=1000)  # 1 second
        audio_segments.append(silence)
    else:
        # Generate speech with ElevenLabs
        audio_bytes = await elevenlabs.text_to_speech(
            text=segment['text'],
            voice_id=VOICE_MAPPING[segment['speaker']],
            model_id="eleven_flash_v2_5",
            output_format="mp3_44100_128",
            voice_settings={
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        )

        audio = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
        audio_segments.append(audio)

# 4. Combine all segments
final_audio = audio_segments[0]
for segment in audio_segments[1:]:
    final_audio += segment

# 5. Export to file
output_path = f"/tmp/podcasts/{podcast_id}.mp3"
final_audio.export(
    output_path,
    format="mp3",
    bitrate="128k",
    parameters=["-ar", "44100", "-ac", "1"]
)
```

### ElevenLabs Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| Model | eleven_flash_v2_5 | Fast, low-latency TTS |
| Format | mp3_44100_128 | 44.1kHz, 128kbps MP3 |
| Stability | 0.5 | Voice consistency |
| Similarity Boost | 0.75 | Voice cloning accuracy |
| Speaker Boost | True | Enhanced clarity |

### Voice Characteristics

**ALEX (Voice ID: pNInz6obpgDQGcFmaJgB)**
- Name: Adam
- Type: Deep male voice
- Tone: Enthusiastic, engaging
- Use case: Primary host, asks questions

**SONIA (Voice ID: EXAVITQu4vr4xnSDxMaL)**
- Name: Bella
- Type: Professional female voice
- Tone: Thoughtful, insightful
- Use case: Expert co-host, provides context

### Retry Logic

```python
max_retries = 3
for attempt in range(max_retries):
    try:
        audio = await elevenlabs.text_to_speech(...)
        break
    except Exception as e:
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
            continue
        else:
            raise AudioGenerationError(f"Failed after {max_retries} attempts")
```

### Metrics Tracked

```python
metrics.elevenlabs_characters = sum(len(seg['text']) for seg in segments)
metrics.elevenlabs_cost = metrics.elevenlabs_characters / 1000 * 0.30  # $0.30/1k chars
metrics.audio_generation_ms = time_end - time_start
```

**Timeline:** T+13500ms to T+18500ms

---

## Data Flow

### Database Updates Throughout Workflow

**Initial Creation (T+100ms):**
```sql
INSERT INTO podcasts (id, user_id, status, created_at)
VALUES ('550e8400...', 'user-123', 'pending', NOW());
```

**Status Update - Processing (T+200ms):**
```sql
UPDATE podcasts SET status = 'processing' WHERE id = '550e8400...';
```

**After News Fetch (T+3500ms):**
```sql
UPDATE podcasts
SET podcast_metadata = jsonb_set(podcast_metadata, '{articles}', '...')
WHERE id = '550e8400...';
```

**After Script Generation (T+13500ms):**
```sql
UPDATE podcasts
SET
  title = 'OpenAI Announces GPT-5, EU Finalizes AI Regulations',
  script = '[ALEX](enthusiastic): Welcome back everyone!...',
  podcast_metadata = jsonb_set(
    podcast_metadata,
    '{topics}',
    '["GPT-5", "AI regulation", "startup funding"]'
  )
WHERE id = '550e8400...';
```

**After Audio Generation (T+18500ms):**
```sql
UPDATE podcasts
SET
  audio_url = '/tmp/podcasts/550e8400.mp3',
  status = 'completed',
  updated_at = NOW()
WHERE id = '550e8400...';

INSERT INTO metrics (
  id, podcast_id,
  tokens_used, elevenlabs_characters,
  firecrawl_searches, firecrawl_scrapes,
  openai_cost, elevenlabs_cost, firecrawl_cost,
  latency_ms, news_fetch_ms, script_generation_ms, audio_generation_ms,
  created_at
)
VALUES (
  'metric-123', '550e8400...',
  1547, 4023,
  3, 9,
  0.0463, 0.0241, 0.0089,
  18234, 3187, 10012, 5035,
  NOW()
);
```

### Frontend Polling

**Every 2 seconds:**
```typescript
const pollStatus = async () => {
  const response = await fetch(`/api/v1/podcasts/${podcastId}/status`);
  const data = await response.json();

  if (data.status === 'completed') {
    // Load audio player
    loadAudioPlayer(data.audio_url);
    stopPolling();
  } else if (data.status === 'failed') {
    showError(data.error_message);
    stopPolling();
  }

  // Update progress indicator
  updateProgress(data.status);
};
```

---

## Error Handling

### Error Types and Recovery

| Error Type | Stage | Recovery Strategy |
|------------|-------|-------------------|
| News API rate limit | Stage 1 | Exponential backoff, retry |
| Firecrawl timeout | Stage 1 | Skip article, continue with others |
| OpenAI rate limit | Stage 2 | Retry with backoff (3 attempts) |
| Invalid JSON from LLM | Stage 2 | Parse markdown-wrapped JSON |
| ElevenLabs API error | Stage 3 | Retry segment (max 3 attempts) |
| Database connection | Any | Rollback transaction, retry |

### Error Propagation

```python
try:
    # Execute pipeline
    articles = await fetch_news()
    script = await generate_script(articles)
    audio = await generate_audio(script)
    await save_results(audio)

except NewsServiceError as e:
    await update_podcast(
        status='failed',
        error_message=f"Failed to fetch news: {str(e)}"
    )

except ScriptGenerationError as e:
    # Save articles even if script fails
    await save_partial_results(articles=articles)
    await update_podcast(
        status='failed',
        error_message=f"Failed to generate script: {str(e)}"
    )

except AudioGenerationError as e:
    # Save script even if audio fails
    await save_partial_results(articles=articles, script=script)
    await update_podcast(
        status='failed',
        error_message=f"Failed to generate audio: {str(e)}"
    )

except Exception as e:
    logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    await update_podcast(
        status='failed',
        error_message="Internal server error"
    )
```

---

## Performance Metrics

### Typical Generation Times

| Stage | Duration | Percentage |
|-------|----------|------------|
| News Discovery | 2-3s | 15% |
| Script Generation | 8-10s | 50% |
| Audio Generation | 3-5s | 25% |
| Database Saves | 1-2s | 10% |
| **Total** | **15-20s** | **100%** |

### Cost Breakdown

| Service | Unit | Rate | Typical Usage | Cost |
|---------|------|------|---------------|------|
| News API | Calls | Free | 3 searches | $0.00 |
| Firecrawl | Scrapes | Variable | 9 articles | $0.01 |
| OpenAI GPT-4o | 1M tokens | $5.00 | 1500 tokens | $0.05 |
| ElevenLabs | 1k chars | $0.30 | 4000 chars | $0.02 |
| **Total** | - | - | - | **$0.08** |

### Optimization Opportunities

1. **Caching:** Cache scraped articles for 1 hour (reduces Firecrawl costs)
2. **Batch Processing:** Generate multiple podcasts simultaneously
3. **Model Selection:** Use gpt-4o-mini for simpler tasks (50% cost reduction)
4. **Voice Reuse:** Cache common phrases/intros (reduces ElevenLabs calls)

---

## API Endpoints for Workflow Monitoring

### Check Status
```bash
GET /api/v1/podcasts/{podcast_id}/status

Response:
{
  "id": "550e8400...",
  "status": "processing",  # pending|processing|completed|failed
  "audio_url": null,
  "progress": {
    "stage": "script_generation",
    "percentage": 65
  }
}
```

### Get Full Details
```bash
GET /api/v1/podcasts/{podcast_id}

Response:
{
  "id": "550e8400...",
  "title": "OpenAI Announces GPT-5...",
  "script": "[ALEX]: Welcome...",
  "audio_url": "/tmp/podcasts/550e8400.mp3",
  "status": "completed",
  "podcast_metadata": {
    "topics": ["GPT-5", "AI regulation"],
    "sources": ["TechCrunch", "The Verge"],
    "articles": [...]
  },
  "created_at": "2025-05-06T10:00:00Z",
  "updated_at": "2025-05-06T10:00:20Z"
}
```

### Get Metrics
```bash
GET /api/v1/admin/stats

Response:
{
  "kpis": {
    "total_podcasts": 156,
    "avg_latency_ms": 18234,
    "total_api_cost": 12.45,
    "success_rate": 0.95
  },
  "cost_breakdown": {
    "openai": 7.23,
    "elevenlabs": 3.74,
    "firecrawl": 1.48
  }
}
```

---

## Next Steps

- **Monitor production:** Use admin dashboard at `/admin`
- **Optimize costs:** Review metrics and identify expensive operations
- **Improve quality:** Analyze failed generations and adjust prompts
- **Scale up:** Add more concurrent workers for high demand

**See Also:**
- [README.md](README.md) - Project overview
- [SETUP.md](SETUP.md) - Installation guide
- [DOCKER_SETUP.md](DOCKER_SETUP.md) - Docker deployment
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
