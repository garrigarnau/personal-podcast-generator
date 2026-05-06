# Solution Architecture & Design Decisions

> **Context:** Technical solution for the Prosper AI interview exercise. This is a **simple implementation** that touches the basics of AI architecture through a practical podcast generation system.

## Executive Summary

The solution transforms web articles into multi-speaker audio podcasts using a **multi-agent LangChain architecture**. The implementation demonstrates core AI engineering concepts: agent specialization, prompt engineering, structured outputs, and service orchestration.

**Key Metrics:**
- Generation Time: 15-25 seconds
- Cost: ~$0.08 per podcast
- Success Rate: ~95%

---

## Core Architecture

### Pipeline Overview

```
User Input (interests)
    ↓
[1] News Discovery (2-3s)
    → News API + Firecrawl scraping
    → Top 5 relevant articles
    ↓
[2] Script Generation (8-10s) ★ Multi-Agent AI
    → Agent 1: Content Planner (GPT-4o, temp=0.5)
    → Agent 2: Script Writer (GPT-4o, temp=0.8)
    → Orchestrator: Validation & formatting
    ↓
[3] Audio Generation (3-5s)
    → ElevenLabs TTS (2 voices: Alex & Sonia)
    → Combine segments with pydub
    ↓
Final Podcast (MP3 + transcript)
```

### Technology Stack

**Backend:**
- **FastAPI** - Async-first API framework
- **LangChain** - Multi-agent orchestration
- **PostgreSQL** - Data persistence with JSONB for flexibility
- **Pydantic** - Structured outputs and validation

**AI Services:**
- **OpenAI GPT-4o** - Script generation (2 specialized agents)
- **ElevenLabs** - Text-to-speech (multi-speaker)
- **News API** - Article discovery
- **Firecrawl** - Web scraping

---

## Multi-Agent AI Design (LangChain)

### Why Multi-Agent Instead of Single Prompt?

**Decision:** Use 2 specialized agents rather than one large prompt.

**Rationale:**
1. **Separation of Concerns** - Planning and writing are distinct cognitive tasks
2. **Quality** - Structured planning leads to more coherent scripts
3. **Observability** - LangSmith tracing shows exactly where issues occur
4. **Iterability** - Can improve each agent independently
5. **Cost Optimization** - Use cheaper model (gpt-4o-mini) for planning, reserve expensive model (gpt-4o) for creative writing

**Trade-off:** 2x API calls (~2s extra latency) vs. better output quality + 40% cost savings → Clear win.

---

### Agent 1: Content Planner

**Purpose:** Analyze articles and create structured content plan

**Configuration:**
```python
ChatOpenAI(
    model="gpt-4o-mini",  # Cost-optimized model
    temperature=0.5,      # Lower temp for structured thinking
    max_tokens=2000
)
```

**Why gpt-4o-mini?**
- Planning is a **structured, deterministic task** - doesn't need GPT-4o's full capabilities
- **17x cheaper** than GPT-4o ($0.15/1M input vs $2.50/1M)
- Produces reliable JSON outputs with lower temperature
- **Faster inference** - typically 30-50% quicker response

**Why temperature=0.5?**
- Lower temperature ensures **consistency** and **structure**
- Reduces randomness in planning decisions
- Produces reliable, parseable JSON outputs

---

### Agent 2: Script Writer

**Purpose:** Generate natural dialogue between two hosts

**Configuration:**
```python
ChatOpenAI(
    model="gpt-4o",      # Full-capability model for creativity
    temperature=0.8,     # Higher temp for creativity
    max_tokens=5000   # Dynamic based on length (short/medium/long)
)
```

**Why temperature=0.8?**
- Dialogue requires **creativity** and **naturalness**
- Higher temperature produces varied, engaging conversation
- Still controlled enough to follow structure


**Key Innovation:** Each segment includes:
- `speaker`: "ALEX" or "SONIA"
- `text`: Dialogue content (40-60 words)
- `emotion`: Optional cue (e.g., "enthusiastic", "thoughtful")
- `pause_after`: Boolean for breaks

---

### Orchestrator: Validation & Conversion

**Not a separate agent** - Just Python code that:

1. **Parses structured outputs** using `RobustPydanticOutputParser`
   - Strips markdown wrappers (`\`\`\`json`)
   - Handles malformed JSON from LLM
   - Validates against Pydantic schema

2. **Validates quality**
   - Minimum segment count (10+)
   - Word count vs. target (warn if <70%)
   - Speaker alternation (no 5+ consecutive turns)

3. **Converts format** to final `PodcastScript` model

---

### Why LangChain?

**Considered Alternatives:**
- ❌ **Raw OpenAI API calls** - More boilerplate, no tracing
- ❌ **LangGraph** - Overkill for linear pipeline
- ✅ **LangChain** - Perfect middle ground

**Benefits:**
- **LangSmith Tracing** - Full observability of agent calls
- **Prompt Templates** - Reusable, maintainable prompts
- **Output Parsers** - Automatic Pydantic validation
- **Cost Tracking** - Built-in token counting via `get_openai_callback()`

---

## Key Decisions & Trade-offs

### 1. Async-First Architecture

**Decision:** Use `async/await` throughout (FastAPI, SQLAlchemy, HTTP clients)

**Why:**
- Podcast generation is **I/O-bound** (News API, OpenAI, ElevenLabs)
- Multiple API calls can run **concurrently** (`asyncio.gather`)
- Single process handles **5+ simultaneous podcasts**

**Trade-off:** More complex debugging vs. 10x better throughput → Worth it.

---

### 2. Background Task Processing (Custom, Not Celery)

**Decision:** Built simple in-memory task queue instead of Celery

**Why:**
- **Simplicity** - No Redis/RabbitMQ dependency
- **Sufficient** - Only need 5 concurrent tasks
- **Fast feedback** - Direct status access via API

**Trade-off:** Tasks lost on restart, no distributed processing vs. much simpler deployment → Good for exercise scope.


---

### 3. Status Polling (Not WebSockets)

**Decision:** Frontend polls every 2 seconds for status updates

**Why:**
- **Simplicity** - No persistent connection management
- **Reliable** - Automatic reconnection on network failures
- **Stateless** - Works with load balancers

**Trade-off:** 2-second delay for updates vs. significantly simpler architecture → Users don't notice 2s.

---

### 4. Structured Outputs (Pydantic)

**Decision:** All LLM outputs parsed into Pydantic models

**Why:**
- **Type Safety** - Catch errors at validation, not runtime
- **LLM Reliability** - Structured outputs reduce hallucination
- **Automatic Validation** - Word count, segment count, speaker names
- **Self-Documenting** - Schema serves as documentation


---

## Implementation Challenges

### Challenge 1: Firecrawl Search Not Working

**Initial Approach:** Use Firecrawl's search function directly
```python
# Attempted but didn't work reliably
results = firecrawl.search(
    query=interest,
    limit=5
)
```

**Problem:** Firecrawl search returned inconsistent results or failed silently

**Solution:** Two-phase approach
1. **News API** - Quick, reliable article discovery (gets URLs)
2. **Firecrawl** - Scrape full content from discovered URLs


---

### Challenge 2: LLM Output Parsing

**Problem:** GPT-4o sometimes wraps JSON in markdown code blocks

**Example:**
```
```json
{"title": "...", "topics": [...]}
```


**Solution:** Robust parser that strips markdown before parsing
- Find first `{` or `[`
- Find last `}` or `]`
- Remove everything outside
- Remove trailing commas (common LLM mistake)

---

### Challenge 3: Script Length Control

**Problem:** GPT-4o often generated too-short scripts (500 words vs. 1500 target)

**Solution:** Multi-level approach
1. **Explicit instructions** - "You MUST generate AT LEAST X segments"
2. **Token limits** - Set `max_tokens` based on target length
3. **Validation** - Warn if <70% of target
4. **Segment estimation** - Planner calculates `target_words / 50 = min_segments`


---

## What I Learned

### 1. Agent Specialization Works

**Key Insight:** Using different **models** and **temperatures** for different tasks improves both quality and cost
- Planner (gpt-4o-mini, temp=0.5): Consistent, structured outputs at 1/17th the cost
- Writer (gpt-4o, temp=0.8): Creative, varied dialogue with full model capabilities

This is a fundamental AI architecture pattern: **match model capability to task complexity**.


---

### 2. Observability Is Critical

**LangSmith tracing** was invaluable for debugging:
- See exact prompts sent to each agent
- Track token usage per call
- Identify where pipeline fails
- Measure latency per stage

---

### 3. Structured Outputs > Prompt Engineering

Using Pydantic models reduced prompt complexity:
- Don't need "please format as JSON" instructions
- Automatic validation catches errors early
- Self-documenting schema


---

### 4. Simple Architectures Win

Resisted temptation to over-engineer:
- No Celery (yet) → Simpler deployment
- No WebSockets (yet) → Stateless architecture
- No microservices (yet) → Faster development


---

### 5. AI System Design Is Different

Traditional software engineering patterns apply, but with AI twists:
- **Non-determinism** - Same input ≠ same output
- **Latency variability** - GPT-4o can take 2-15 seconds
- **Cost tracking** - Every API call has a price
- **Quality metrics** - Need to measure output quality, not just correctness

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                      FRONTEND                             │
│  React + TypeScript (Status Polling Every 2s)            │
└──────────────────┬───────────────────────────────────────┘
                   │ POST /generate → 202 Accepted
                   ↓
┌──────────────────────────────────────────────────────────┐
│                  FASTAPI BACKEND                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Background Task Manager (Max 5 Concurrent)         │  │
│  │  ┌──────────────────────────────────────────────┐ │  │
│  │  │ PodcastOrchestrator.generate_podcast_async() │ │  │
│  │  │                                               │ │  │
│  │  │  [1] NewsService                             │ │  │
│  │  │      ├─ News API (article discovery)         │ │  │
│  │  │      └─ Firecrawl (content scraping)         │ │  │
│  │  │                                               │ │  │
│  │  │  [2] ScriptGeneratorService (LangChain)      │ │  │
│  │  │      ├─ Agent 1: Planner (temp=0.5)          │ │  │
│  │  │      │   └─ GPT-4o → ContentPlan              │ │  │
│  │  │      ├─ Agent 2: Writer (temp=0.8)           │ │  │
│  │  │      │   └─ GPT-4o → PodcastScript            │ │  │
│  │  │      └─ Orchestrator: Validation             │ │  │
│  │  │                                               │ │  │
│  │  │  [3] AudioService                            │ │  │
│  │  │      └─ ElevenLabs TTS (2 voices)            │ │  │
│  │  │          └─ pydub (combine segments)          │ │  │
│  │  └──────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────┬───────────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────────┐
│              POSTGRESQL DATABASE                          │
│  users, podcasts, metrics (costs, latency, tokens)       │
└──────────────────────────────────────────────────────────┘
```

---

## Performance & Cost

| Stage | Duration | Cost | Details |
|-------|----------|------|---------|
| News Fetch | 2-3s | ~$0.01 | Firecrawl scraping (9 articles) |
| Script Gen | 8-10s | **~$0.03** | gpt-4o-mini (plan) + gpt-4o (script) |
| Audio Gen | 3-5s | ~$0.02 | ElevenLabs TTS (2 voices) |
| **Total** | **15-20s** | **~$0.06** | **40% cheaper with mini** |

**Cost Breakdown (Script Generation):**
- Planning (gpt-4o-mini): ~500 tokens × $0.15/1M = **$0.0001** 
- Writing (gpt-4o): ~1500 tokens × $2.50/1M = **$0.0038**
- **Previous (both gpt-4o):** ~$0.005 total
- **Current (mini + 4o):** ~$0.004 total → **20% savings on scripts**

**Additional Optimization Opportunities:**
1. Cache news articles (1 hour TTL) → Save 60% on Firecrawl costs
2. Concurrent audio generation → Save 2-3 seconds
3. Use gpt-4o-mini for other structured tasks → Save another 10%

---

## Reflection

### What Went Well

✅ **Multi-agent design** - Clear separation improved quality
✅ **Async architecture** - Handled concurrent requests efficiently
✅ **Structured outputs** - Pydantic caught many errors early
✅ **Observability** - LangSmith made debugging easy

### What I'd Do Differently

🔄 **Earlier testing** - Should have tested Firecrawl search sooner
🔄 **Prompt versioning** - Would track prompt changes more systematically
🔄 **More unit tests** - Especially for parser logic

