# Data Flow Analysis: Search vs Scrape Response Structures

## Executive Summary

The system uses a **3-phase pipeline** for article processing:
1. **SEARCH** - Find candidates (metadata only, no full content)
2. **AI SELECTION** - Choose best 5 articles using GPT-4o-mini
3. **SCRAPE** - Fetch full content for selected articles

**Critical Issue**: The scrape response structure differs significantly from search, and metadata from Phase 1 is **LOST** during Phase 3, requiring reconstruction or fallback values.

---

## Phase-by-Phase Data Structures

### Phase 1: SEARCH - Candidate Discovery
**Function**: `FirecrawlNewsService.search_news_candidates()`
**API Call**: `client.search(query, limit=10, sources=["news", "web"])`
**Cost**: 1 search request (~$0.01)

#### Search Response Structure
```python
# Raw response from Firecrawl
response.web = [SearchResultWeb, ...]
response.news = [SearchResultNews, ...]

# SearchResultWeb structure
SearchResultWeb:
  url: 'https://topstartups.io/'
  title: 'Top Startups 2026'
  description: 'AI startups · Biotech startups...'
  category: None

# SearchResultNews structure
SearchResultNews:
  title: 'Data centers at sea...'
  url: 'https://www.geekwire.com/...'
  snippet: 'Oregon-based Panthalassa raised $140M...'
  date: '21 hours ago'
  image_url: 'https://...'
  position: 1
  category: None
```

#### Extracted Candidate Dict (for AI selection)
**File**: `news_service.py:226-232`
```python
candidate = {
    'title': data.get('title') or data.get('headline') or 'Untitled',
    'description': data.get('description') or data.get('summary') or '',
    'url': data.get('url') or data.get('link') or '',
    'source': data.get('source') or data.get('domain') or 'Unknown',
    'date': pub_date.isoformat(),  # datetime -> ISO string
}
```

**Available Fields**: title, description, url, source, date
**Content**: Summary/snippet only (100-200 chars)
**Purpose**: Lightweight metadata for AI ranking

---

### Phase 2: AI SELECTION - GPT-4o-mini Ranking
**Function**: `ArticleSelectorService.select_articles()`
**Input**: List of candidate dicts from Phase 1
**Output**: List of 5 selected URLs

#### Prompt Structure
**File**: `article_selector_service.py:109-116`
```python
articles_text = "\n\n".join([
    f"URL: {article['url']}\n"
    f"Title: {article['title']}\n"
    f"Source: {article['source']}\n"
    f"Date: {article['date']}\n"
    f"Description: {article['description']}"
    for article in candidates
])
```

**Available to AI**: All 5 fields from candidate dict
**Decision Criteria**: Relevance, credibility, diversity, tone match, recency
**Output**: `["url1", "url2", "url3", "url4", "url5"]`

---

### Phase 3: SCRAPE - Full Content Retrieval
**Function**: `FirecrawlNewsService.scrape_selected_articles()`
**API Call**: `client.scrape_url(url, params={'formats': ['markdown']})`
**Cost**: 5 scrape requests (~$0.025 total)

#### Scrape Response Structure
```python
# Raw response from Firecrawl (from docs)
{
  markdown: "Launch Week I is here! Full article content...",
  metadata: {
    title: "Home - Firecrawl",
    description: "Page description from meta tags",
    sourceURL: "https://firecrawl.dev",
    statusCode: 200
  }
}

# After model_dump() conversion
{
  'markdown': 'Full article markdown content...',
  'title': 'Article Title',  # May differ from search title
  'url': 'https://...',
  'source': None,           # NOT in scrape response
  'domain': None,            # NOT in scrape response
  'published_date': None,    # NOT in scrape response
  'author': None,            # NOT in scrape response
}
```

#### Parse to FetchedNewsArticle
**File**: `news_service.py:826-878`
```python
def _parse_article(self, data: Dict[str, Any]) -> Optional[FetchedNewsArticle]:
    # Extract fields with fallbacks
    title = data.get('title') or data.get('headline') or 'Untitled'

    # Content - prioritize markdown from scrape
    content = (
        data.get('markdown') or      # From scrape: full content
        data.get('content') or
        data.get('text') or
        data.get('description') or
        ''
    )

    # Build FetchedNewsArticle
    article = FetchedNewsArticle(
        title=title,                   # From scrape
        content=content,               # FROM SCRAPE (markdown)
        summary=data.get('summary') or data.get('excerpt'),  # Usually None
        source=data.get('source') or data.get('domain') or 'Unknown',  # LOST
        author=data.get('author'),     # Usually None
        published_date=data.get('published_date') or datetime.utcnow(),  # LOST
        url=data.get('url') or 'https://example.com',
        topics=data.get('topics') or data.get('categories') or [],  # LOST
    )
```

#### FetchedNewsArticle Model
**File**: `news_service.py:29-96`
```python
class FetchedNewsArticle(BaseModel):
    title: str                    # FROM: scrape.title
    content: str                  # FROM: scrape.markdown (FULL CONTENT)
    summary: Optional[str]        # MISSING: fallback to content[:200]
    source: str                   # MISSING: fallback to 'Unknown'
    author: Optional[str]         # MISSING: None
    published_date: datetime      # MISSING: fallback to utcnow()
    url: HttpUrl                  # FROM: scrape.url
    relevance_score: float        # NOT USED in 3-phase flow
    topics: List[str]             # MISSING: []
    word_count: int               # CALCULATED: from content
```

---

### Phase 4: TRANSFORMATION - Script Service Conversion
**Function**: `PodcastOrchestrator._generate_script()`
**Input**: List[FetchedNewsArticle] from scrape
**Output**: List[NewsArticle] for script generation

#### Conversion Logic
**File**: `orchestrator.py:454-465`
```python
news_articles = [
    NewsArticle(
        title=article.title,              # Preserved
        summary=article.summary or article.content[:200],  # Fallback
        content=article.content,          # Preserved (full markdown)
        source=article.source,            # May be 'Unknown'
        url=str(article.url),             # Preserved
        published_at=article.published_date,  # May be utcnow()
        category=article.topics[0] if article.topics else None,  # May be None
    )
    for article in articles
]
```

#### NewsArticle Model (Script Service)
**File**: `script_service.py:65-89`
```python
class NewsArticle(BaseModel):
    title: str                    # Required
    summary: str                  # Required (fallback to content[:200])
    content: str                  # Required (full markdown from scrape)
    source: Optional[str]         # Optional (may be 'Unknown')
    url: Optional[str]            # Optional
    published_at: Optional[datetime]  # Optional (may be utcnow())
    category: Optional[str]       # Optional (may be None)
```

---

## Comparison Table: Search vs Scrape

| Field | Search (Phase 1) | Scrape (Phase 3) | Status | Impact |
|-------|------------------|------------------|--------|--------|
| **title** | ✅ Original headline | ✅ Page title | PRESERVED | May differ (SEO vs article title) |
| **description/snippet** | ✅ 100-200 char summary | ❌ Not in response | LOST | Used for AI selection only |
| **content** | ❌ Not available | ✅ Full markdown | GAINED | Main value from scrape |
| **url** | ✅ Article URL | ✅ Same URL | PRESERVED | Identical |
| **source** | ✅ Publication name | ❌ Not in response | **LOST** | Falls back to 'Unknown' |
| **date** | ✅ Published date | ❌ Not in response | **LOST** | Falls back to utcnow() |
| **author** | ❌ Not in search | ❌ Not in scrape | NOT AVAILABLE | Always None |
| **topics/category** | ❌ Not in search | ❌ Not in scrape | NOT AVAILABLE | Always [] or None |
| **image_url** | ✅ (news only) | ❌ Not used | IGNORED | Not captured |
| **position** | ✅ Search rank | ❌ N/A | LOST | Not preserved |

---

## Critical Data Loss Issues

### 1. Source Attribution Lost
**Problem**: `source` field from search is not preserved in scrape response
**Current Behavior**: Falls back to `'Unknown'`
**Impact**:
- Podcast script says "According to Unknown..."
- Loss of credibility signals
- Cannot filter by trusted sources

**Example**:
```python
# Phase 1: Search result
candidate = {
    'source': 'TechCrunch',
    'url': 'https://techcrunch.com/article'
}

# Phase 3: Scrape result
{
    'markdown': '...',
    'url': 'https://techcrunch.com/article',
    'source': None  # NOT IN RESPONSE
}

# Parsed article
FetchedNewsArticle(
    source='Unknown',  # FALLBACK
    ...
)
```

### 2. Publication Date Lost
**Problem**: `published_date` from search is not in scrape response
**Current Behavior**: Falls back to `datetime.utcnow()`
**Impact**:
- All articles appear to be published "now"
- Cannot sort by recency in script
- "Breaking news" vs "analysis piece" distinction lost

**Example**:
```python
# Phase 1: Search result
candidate = {
    'date': '2026-05-03T14:30:00Z',  # 2 days ago
}

# Phase 3: Parsed article
FetchedNewsArticle(
    published_date=datetime.utcnow(),  # NOW (incorrect)
)
```

### 3. Description/Snippet Lost
**Problem**: Search snippet is perfect for summaries but not available in scrape
**Current Behavior**: Falls back to `content[:200]` (raw markdown)
**Impact**:
- Summary may include markdown syntax
- First 200 chars might be ads/navigation
- Lost curated excerpt from search

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: SEARCH (search_news_candidates)                       │
├─────────────────────────────────────────────────────────────────┤
│ INPUT: interests, limit=10                                      │
│ API: client.search(query, sources=["news", "web"])            │
│ COST: 1 request (~$0.01)                                       │
│                                                                 │
│ OUTPUT: List[Dict] candidates                                  │
│   {                                                             │
│     'title': 'Article Headline',                               │
│     'description': '100-200 char snippet',  ← ONLY HERE        │
│     'url': 'https://...',                                      │
│     'source': 'TechCrunch',                ← ONLY HERE         │
│     'date': '2026-05-03T14:30:00Z'         ← ONLY HERE         │
│   }                                                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: AI SELECTION (select_articles)                        │
├─────────────────────────────────────────────────────────────────┤
│ INPUT: candidates (all 5 fields available)                     │
│ MODEL: GPT-4o-mini                                             │
│ LOGIC: Rank by relevance, credibility, diversity              │
│                                                                 │
│ OUTPUT: List[str] selected_urls                                │
│   ['url1', 'url2', 'url3', 'url4', 'url5']                    │
│                                                                 │
│ ⚠️  METADATA DISCARDED - only URLs passed to Phase 3           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: SCRAPE (scrape_selected_articles)                     │
├─────────────────────────────────────────────────────────────────┤
│ INPUT: 5 URLs (NO metadata from Phase 1)                       │
│ API: client.scrape_url(url, formats=['markdown'])             │
│ COST: 5 requests (~$0.025)                                     │
│                                                                 │
│ OUTPUT: List[FetchedNewsArticle]                               │
│   FetchedNewsArticle(                                          │
│     title='...',              ← From scrape.title             │
│     content='...',            ← From scrape.markdown (NEW)    │
│     url='...',                ← From scrape.url               │
│     source='Unknown',         ← LOST (fallback)               │
│     published_date=utcnow(),  ← LOST (fallback)               │
│     summary=None,             ← LOST (no snippet in scrape)   │
│     topics=[],                ← LOST (not in scrape)          │
│   )                                                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: CONVERSION (NewsArticle for script)                   │
├─────────────────────────────────────────────────────────────────┤
│ INPUT: List[FetchedNewsArticle] with missing fields            │
│                                                                 │
│ OUTPUT: List[NewsArticle]                                      │
│   NewsArticle(                                                 │
│     title=article.title,                                       │
│     content=article.content,         # Full markdown           │
│     summary=content[:200],           # Fallback (may be ugly) │
│     source='Unknown',                # From fallback          │
│     published_at=utcnow(),          # From fallback          │
│     category=None                    # From fallback          │
│   )                                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Transformation Requirements

### 1. Search Result → Candidate Dict (Phase 1 → 2)
**Location**: `news_service.py:226-232`
**Mapping**:
```python
SearchResult → candidate dict
├─ title/headline → 'title'
├─ description/snippet → 'description'
├─ url/link → 'url'
├─ source/domain → 'source'
└─ date → 'date' (ISO string)
```
**Status**: ✅ Working correctly

### 2. Candidate Dict → AI Prompt (Phase 2)
**Location**: `article_selector_service.py:109-116`
**Mapping**: All 5 fields formatted into text prompt
**Status**: ✅ Working correctly

### 3. Scrape Response → FetchedNewsArticle (Phase 3)
**Location**: `news_service.py:826-878`
**Mapping**:
```python
Scrape Response → FetchedNewsArticle
├─ markdown → content ✅ (MAIN VALUE)
├─ title → title ✅
├─ url → url ✅
├─ ??? → source ❌ (fallback: 'Unknown')
├─ ??? → published_date ❌ (fallback: utcnow())
├─ ??? → summary ❌ (fallback: None)
└─ ??? → topics ❌ (fallback: [])
```
**Status**: ⚠️ Working but loses metadata

### 4. FetchedNewsArticle → NewsArticle (Phase 3 → 4)
**Location**: `orchestrator.py:454-465`
**Mapping**:
```python
FetchedNewsArticle → NewsArticle
├─ title → title ✅
├─ content → content ✅
├─ url → url ✅
├─ summary or content[:200] → summary ⚠️
├─ source → source ⚠️ ('Unknown' if lost)
├─ published_date → published_at ⚠️ (utcnow if lost)
└─ topics[0] → category ⚠️ (None if lost)
```
**Status**: ⚠️ Working but propagates missing data

---

## Information Preserved/Lost Summary

### ✅ Preserved Through All Phases
1. **URL** - Identical throughout (used as join key)
2. **Title** - May differ slightly (search headline vs page title)
3. **Content** - GAINED in Phase 3 (full markdown, main value)

### ⚠️ Used Then Discarded
4. **Description/Snippet** - Available in Phase 1-2 only, used for AI selection
5. **Image URL** - Available in Phase 1 only (news results), never captured
6. **Position/Rank** - Available in Phase 1 only, not preserved

### ❌ Lost in Phase 3
7. **Source** - Known in Phase 1, lost in Phase 3, becomes 'Unknown'
8. **Published Date** - Known in Phase 1, lost in Phase 3, becomes utcnow()
9. **Topics/Category** - Never available (not in search or scrape)
10. **Author** - Never available (not in search or scrape)

---

## Recommendations

### Option 1: Pass Original Metadata Alongside Scrape (RECOMMENDED)
**Approach**: Create a lookup dict from Phase 1 candidates, use in Phase 3 parsing

**Implementation**:
```python
# In orchestrator._fetch_news()
candidates_lookup = {c['url']: c for c in candidates}

# Pass to scrape function
articles = await self.news_service.scrape_selected_articles(
    selected_urls,
    original_metadata=candidates_lookup  # NEW PARAMETER
)

# In _parse_article()
def _parse_article(self, data, original_metadata=None):
    url = data.get('url')
    original = original_metadata.get(url) if original_metadata else {}

    article = FetchedNewsArticle(
        title=data.get('title') or original.get('title') or 'Untitled',
        content=data.get('markdown') or '',
        source=original.get('source') or 'Unknown',  # FROM PHASE 1
        published_date=original.get('date') or datetime.utcnow(),  # FROM PHASE 1
        summary=original.get('description'),  # FROM PHASE 1
        url=url,
        ...
    )
```

**Pros**:
- Preserves all Phase 1 metadata
- No additional API costs
- Source attribution accurate
- Publication dates correct
- Better summaries (curated snippets)

**Cons**:
- Requires signature changes
- URLs must match exactly (edge case: redirects)

### Option 2: Extract Metadata from Scraped Content
**Approach**: Parse date/source from scraped markdown using regex/LLM

**Pros**:
- Works even if search didn't find metadata
- May find more accurate dates

**Cons**:
- Unreliable (site-specific formats)
- Adds latency
- May require LLM calls (cost)

### Option 3: Accept the Loss, Use Fallbacks (CURRENT)
**Approach**: Continue using 'Unknown' and utcnow()

**Pros**:
- Simple, no changes needed

**Cons**:
- Poor UX ("According to Unknown...")
- Incorrect dates in script
- Loss of credibility signals

---

## Key Insights for Implementation

1. **URL is the Join Key**: Use URL to match Phase 1 metadata to Phase 3 articles
2. **AI Selection Only Needs Metadata**: Full content scraping can wait until after selection
3. **Scrape Response is Minimal**: Firecrawl only returns markdown + basic page info
4. **Two Distinct Article Types**:
   - `candidate dict`: Lightweight metadata for ranking (Phase 1-2)
   - `FetchedNewsArticle`: Full content for script generation (Phase 3-4)
5. **The Gap**: No bridge between Phase 1 metadata and Phase 3 parsing

---

## Cost Analysis

| Phase | API Calls | Estimated Cost | Data Volume |
|-------|-----------|----------------|-------------|
| Phase 1: Search | 1 search | ~$0.01 | 10 candidates × 500 bytes = 5 KB |
| Phase 2: AI Select | 1 GPT-4o-mini | ~$0.001 | ~2 KB prompt |
| Phase 3: Scrape | 5 scrapes | ~$0.025 | 5 articles × 50 KB = 250 KB |
| **Total** | **7 API calls** | **~$0.036** | **~257 KB** |

**Current Waste**: Losing 5 metadata fields from Phase 1 that cost money to obtain

---

## Conclusion

The 3-phase pipeline is well-architected for cost efficiency (search → rank → scrape), but suffers from **metadata loss** between phases. The selected URLs are passed to Phase 3 in isolation, without the rich metadata available from Phase 1.

**Impact**: Articles are correctly scraped with full content, but lose source attribution and publication dates, forcing fallbacks to 'Unknown' and utcnow().

**Solution**: Implement Option 1 (pass original metadata lookup) to preserve Phase 1 data through Phase 3 parsing.
