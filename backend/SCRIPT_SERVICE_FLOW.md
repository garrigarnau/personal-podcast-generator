# Script Generation Service - Flow Diagram

## 🔄 Complete Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SCRIPT GENERATION FLOW                            │
└─────────────────────────────────────────────────────────────────────────┘

1. INPUT STAGE
   ┌──────────────────────────────────────────────────────────────┐
   │  Client Request                                               │
   │  ┌─────────────────────────────────────────────────────────┐ │
   │  │ news_articles: List[NewsArticle]                        │ │
   │  │ preferences: {                                          │ │
   │  │   "tone": "casual" | "serious" | "balanced"            │ │
   │  │   "length": "short" | "medium" | "long"                │ │
   │  │ }                                                       │ │
   │  └─────────────────────────────────────────────────────────┘ │
   └──────────────────────────────────────────────────────────────┘
                              ↓
   ┌──────────────────────────────────────────────────────────────┐
   │  Input Validation                                             │
   │  • Validate articles list (not empty)                         │
   │  • Parse tone enum                                            │
   │  • Parse length enum                                          │
   │  • Extract preferences                                        │
   └──────────────────────────────────────────────────────────────┘
                              ↓

2. PROMPT BUILDING STAGE
   ┌──────────────────────────────────────────────────────────────┐
   │  Build System Prompt                                          │
   │  ┌────────────────────────────────────────────────────────┐  │
   │  │ • Character definitions (Alex & Sonia)                 │  │
   │  │ • Tone-specific instructions                           │  │
   │  │ • Format requirements                                  │  │
   │  │ • Structure guidelines                                 │  │
   │  │ • Conversation tips                                    │  │
   │  └────────────────────────────────────────────────────────┘  │
   └──────────────────────────────────────────────────────────────┘
                              ↓
   ┌──────────────────────────────────────────────────────────────┐
   │  Build User Prompt                                            │
   │  ┌────────────────────────────────────────────────────────┐  │
   │  │ Articles (max 5):                                      │  │
   │  │ ┌────────────────────────────────────────────────────┐ │  │
   │  │ │ Article 1: Title, Source, Summary                  │ │  │
   │  │ │ Content: [truncated to 1000 chars]...              │ │  │
   │  │ └────────────────────────────────────────────────────┘ │  │
   │  │ ┌────────────────────────────────────────────────────┐ │  │
   │  │ │ Article 2: ...                                     │ │  │
   │  │ └────────────────────────────────────────────────────┘ │  │
   │  │                                                        │  │
   │  │ Specifications:                                        │  │
   │  │ • Target: ~{target_words} words                       │  │
   │  │ • Tone: {tone}                                        │  │
   │  │ • Format: Dialogue with speaker tags                  │  │
   │  └────────────────────────────────────────────────────────┘  │
   └──────────────────────────────────────────────────────────────┘
                              ↓

3. API CALL STAGE (with Retry Logic)
   ┌──────────────────────────────────────────────────────────────┐
   │  Attempt 1                                                    │
   │  ┌────────────────────────────────────────────────────────┐  │
   │  │ AsyncOpenAI.chat.completions.create()                  │  │
   │  │ • model: "gpt-4o"                                      │  │
   │  │ • temperature: 0.8                                     │  │
   │  │ • max_tokens: {based on length}                       │  │
   │  │ • frequency_penalty: 0.3                              │  │
   │  │ • presence_penalty: 0.2                               │  │
   │  └────────────────────────────────────────────────────────┘  │
   └──────────────────────────────────────────────────────────────┘
                              ↓
                       ┌──────┴──────┐
                       │   Success?  │
                       └──────┬──────┘
                     No ←────┴────→ Yes
                      ↓              ↓
   ┌──────────────────────────────────────┐    ┌─────────────────┐
   │  Error Handling                      │    │  Continue to    │
   │  ┌────────────────────────────────┐  │    │  Parsing Stage  │
   │  │ RateLimitError?                │  │    └─────────────────┘
   │  │ • Wait: 1s → 2s → 4s (exp)    │  │
   │  │ • Max retries: 3              │  │
   │  │ • Max delay: 10s              │  │
   │  ├────────────────────────────────┤  │
   │  │ APITimeoutError?              │  │
   │  │ • Retry with delay            │  │
   │  ├────────────────────────────────┤  │
   │  │ Other OpenAIError?            │  │
   │  │ • Log and raise               │  │
   │  └────────────────────────────────┘  │
   └──────────────────────────────────────┘
                      ↓
              [Retry or Fail]

4. PARSING STAGE
   ┌──────────────────────────────────────────────────────────────┐
   │  Raw GPT Output                                               │
   │  ┌────────────────────────────────────────────────────────┐  │
   │  │ [ALEX]: Welcome to today's episode!                    │  │
   │  │                                                        │  │
   │  │ [SONIA] (thoughtful): Indeed, let's dive into...      │  │
   │  │                                                        │  │
   │  │ [ALEX] (excited): Wow, that's incredible!             │  │
   │  │                                                        │  │
   │  │ [BREAK]                                               │  │
   │  │                                                        │  │
   │  │ [SONIA]: Let me explain...                            │  │
   │  └────────────────────────────────────────────────────────┘  │
   └──────────────────────────────────────────────────────────────┘
                              ↓
   ┌──────────────────────────────────────────────────────────────┐
   │  Parse into Segments                                          │
   │  For each line:                                               │
   │  ┌────────────────────────────────────────────────────────┐  │
   │  │ 1. Identify speaker ([ALEX] or [SONIA])               │  │
   │  │ 2. Extract emotion if present (excited, thoughtful)   │  │
   │  │ 3. Extract dialogue text                              │  │
   │  │ 4. Check for [BREAK] marker                           │  │
   │  │ 5. Create ScriptSegment object                        │  │
   │  └────────────────────────────────────────────────────────┘  │
   └──────────────────────────────────────────────────────────────┘
                              ↓
   ┌──────────────────────────────────────────────────────────────┐
   │  Calculate Metrics                                            │
   │  • Word count: len(text.split())                              │
   │  • Duration: (words / 150 * 60) + pause_time                  │
   │  • Extract topics from articles                               │
   │  • Extract sources from articles                              │
   │  • Speaker balance: alex_words / total_words                  │
   └──────────────────────────────────────────────────────────────┘
                              ↓

5. OUTPUT STAGE
   ┌──────────────────────────────────────────────────────────────┐
   │  PodcastScript Object                                         │
   │  ┌────────────────────────────────────────────────────────┐  │
   │  │ segments: [                                            │  │
   │  │   ScriptSegment(speaker=ALEX, text="...", order=0),   │  │
   │  │   ScriptSegment(speaker=SONIA, text="...", order=1),  │  │
   │  │   ...                                                  │  │
   │  │ ]                                                      │  │
   │  │ total_word_count: 1487                                │  │
   │  │ estimated_duration_seconds: 595                       │  │
   │  │ tone: ToneType.CASUAL                                 │  │
   │  │ length: LengthType.MEDIUM                             │  │
   │  │ topics_covered: ["Technology", "AI"]                  │  │
   │  │ sources_cited: ["TechNews", "Wired"]                  │  │
   │  │ generation_metadata: {...}                            │  │
   │  └────────────────────────────────────────────────────────┘  │
   └──────────────────────────────────────────────────────────────┘
                              ↓
   ┌──────────────────────────────────────────────────────────────┐
   │  GenerationMetrics Object                                     │
   │  ┌────────────────────────────────────────────────────────┐  │
   │  │ tokens_used: 1523                                      │  │
   │  │ prompt_tokens: 845                                     │  │
   │  │ completion_tokens: 678                                 │  │
   │  │ model_used: "gpt-4o"                                   │  │
   │  │ latency_ms: 2150                                       │  │
   │  │ retry_count: 0                                         │  │
   │  │ cost_estimate: 0.0428                                  │  │
   │  └────────────────────────────────────────────────────────┘  │
   └──────────────────────────────────────────────────────────────┘
                              ↓
   ┌──────────────────────────────────────────────────────────────┐
   │  Return: Tuple[PodcastScript, GenerationMetrics]              │
   └──────────────────────────────────────────────────────────────┘
```

## 📊 Data Flow Diagram

```
┌─────────────┐
│   Client    │
│   Request   │
└──────┬──────┘
       │
       │ List[NewsArticle] + preferences
       ↓
┌─────────────────────────────────────────┐
│    ScriptGeneratorService               │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  1. Validate Input               │  │
│  └──────────────────────────────────┘  │
│             ↓                           │
│  ┌──────────────────────────────────┐  │
│  │  2. Build Prompts                │  │
│  │     • System (tone-based)        │  │
│  │     • User (articles + specs)    │  │
│  └──────────────────────────────────┘  │
│             ↓                           │
│  ┌──────────────────────────────────┐  │
│  │  3. Call OpenAI API              │  │
│  │     (with retry logic)           │  │
│  └──────────────────────────────────┘  │
│             ↓                           │
│  ┌──────────────────────────────────┐  │
│  │  4. Parse Response               │  │
│  │     • Extract segments           │  │
│  │     • Calculate metrics          │  │
│  └──────────────────────────────────┘  │
│             ↓                           │
│  ┌──────────────────────────────────┐  │
│  │  5. Return Results               │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
       │
       │ PodcastScript + GenerationMetrics
       ↓
┌──────────────┐
│   Database   │
│   Storage    │
└──────────────┘
```

## 🔄 Retry Logic Flow

```
┌───────────────────────────────────────────────────────┐
│              OpenAI API Call with Retries             │
└───────────────────────────────────────────────────────┘

for attempt in range(MAX_RETRIES):
    │
    ├── Try API Call
    │   └── await client.chat.completions.create(...)
    │
    ├── Success? ──→ Break loop, continue
    │
    ├── RateLimitError?
    │   ├── attempt < MAX_RETRIES - 1?
    │   │   ├── Yes: Calculate delay
    │   │   │   └── delay = min(1.0 * (2^attempt), 10.0)
    │   │   │       ├── attempt 0: 1.0s
    │   │   │       ├── attempt 1: 2.0s
    │   │   │       └── attempt 2: 4.0s
    │   │   └── await asyncio.sleep(delay)
    │   │       └── Continue to next attempt
    │   │
    │   └── No: Log error, raise exception
    │
    ├── APITimeoutError?
    │   └── Similar retry logic
    │
    └── Other Error?
        └── Log and raise immediately

After loop:
├── Success: Return (raw_output, usage_data)
└── Failure: Exception raised to caller
```

## 📈 Token Flow & Cost Calculation

```
┌────────────────────────────────────────────────────────┐
│              Token Usage & Cost Tracking               │
└────────────────────────────────────────────────────────┘

Input (Prompt):
┌─────────────────────────────────────┐
│ System Prompt (~500 tokens)         │
│ • Character definitions             │
│ • Tone instructions                 │
│ • Format requirements               │
└─────────────────────────────────────┘
            +
┌─────────────────────────────────────┐
│ User Prompt (~300-800 tokens)       │
│ • Article content (truncated)       │
│ • Specifications                    │
└─────────────────────────────────────┘
            ↓
    [Total Input Tokens]
            ↓
┌─────────────────────────────────────┐
│ GPT-4o Processing                   │
└─────────────────────────────────────┘
            ↓
    [Output Tokens]
┌─────────────────────────────────────┐
│ Short:   ~400-600 tokens            │
│ Medium:  ~800-1200 tokens           │
│ Long:    ~1200-1800 tokens          │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│ Cost Calculation:                   │
│                                     │
│ input_cost = (prompt_tokens / 1000) │
│              × $0.0025              │
│                                     │
│ output_cost = (completion_tokens /  │
│                1000) × $0.01        │
│                                     │
│ total_cost = input_cost +           │
│              output_cost            │
└─────────────────────────────────────┘
            ↓
    Example (Medium):
    ├── Prompt: 850 tokens × $0.0025 = $0.0021
    ├── Output: 1000 tokens × $0.01 = $0.0100
    └── Total: $0.0121
```

## 🎯 Decision Flow: Tone Selection

```
                ┌─────────────┐
                │ User Tone   │
                │ Preference  │
                └──────┬──────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ↓              ↓              ↓
   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │ Serious │   │ Casual  │   │Balanced │
   └────┬────┘   └────┬────┘   └────┬────┘
        │             │              │
        ↓             ↓              ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│Professional  │ │Conversational│ │Mix of Both   │
│Informative   │ │Approachable  │ │Professional  │
│Data-focused  │ │Light humor   │ │yet Accessible│
│Precise       │ │Relatable     │ │Balanced      │
│              │ │              │ │              │
│• Facts       │ │• Everyday    │ │• Clear       │
│• Statistics  │ │  language    │ │  language    │
│• Expert      │ │• Personal    │ │• Data +      │
│  analysis    │ │  reactions   │ │  human angle │
│• Respectful  │ │• Curiosity   │ │• Credible +  │
│  discourse   │ │• Accessible  │ │  engaging    │
└──────────────┘ └──────────────┘ └──────────────┘
        │             │              │
        └──────────────┼──────────────┘
                       ↓
            ┌──────────────────┐
            │ System Prompt    │
            │ with Tone Style  │
            └──────────────────┘
```

## ⏱️ Performance Timeline

```
T=0ms    Client Request
         └─→ validate_input()
              │
T=5ms    Input validated
         └─→ build_system_prompt()
              │
T=10ms   System prompt ready
         └─→ build_user_prompt()
              │
T=20ms   User prompt ready
         └─→ call_openai()
              │
              ├─→ Network latency (50-100ms)
              │
T=70ms       ├─→ OpenAI processing (1500-2500ms)
              │
T=2170ms     └─→ Response received
              │
T=2180ms Parse response
         └─→ parse_script()
              │
              ├─→ Extract segments
              ├─→ Calculate metrics
              └─→ Build objects
              │
T=2200ms Return results

Total: ~2200ms (2.2 seconds)
```

## 🔍 Error Handling Flow

```
                  ┌──────────────┐
                  │  API Call    │
                  └──────┬───────┘
                         │
                    ┌────┴────┐
                    │Success? │
                    └────┬────┘
                      No │ Yes
        ┌────────────────┼────────────────┐
        │                                 │
        ↓                                 ↓
┌────────────────┐              ┌─────────────┐
│  Error Type?   │              │  Continue   │
└────────┬───────┘              │  to Parse   │
         │                      └─────────────┘
    ┌────┼────┬────┬────┐
    │    │    │    │    │
    ↓    ↓    ↓    ↓    ↓
┌────────────────────────────┐
│ RateLimitError             │
│ • Log warning              │
│ • Calculate backoff delay  │
│ • Sleep(delay)             │
│ • Retry (up to 3 times)    │
└────────────────────────────┘
         │
┌────────────────────────────┐
│ APITimeoutError            │
│ • Log warning              │
│ • Sleep with backoff       │
│ • Retry (up to 3 times)    │
└────────────────────────────┘
         │
┌────────────────────────────┐
│ OpenAIError                │
│ • Log error with details   │
│ • Raise to caller          │
│ • No retry                 │
└────────────────────────────┘
         │
┌────────────────────────────┐
│ ValueError                 │
│ • Invalid input            │
│ • Raise immediately        │
└────────────────────────────┘
         │
         ↓
┌────────────────────────────┐
│ Max retries exceeded?      │
│ • Yes: Raise final error   │
│ • No: Continue retrying    │
└────────────────────────────┘
```

## 🎨 Output Structure

```
PodcastScript
├── segments: List[ScriptSegment]
│   ├── [0] ScriptSegment
│   │   ├── speaker: ALEX
│   │   ├── text: "Welcome to today's episode!"
│   │   ├── order: 0
│   │   ├── emotion: None
│   │   └── pause_after: False
│   │
│   ├── [1] ScriptSegment
│   │   ├── speaker: SONIA
│   │   ├── text: "Indeed, let's dive into..."
│   │   ├── order: 1
│   │   ├── emotion: "thoughtful"
│   │   └── pause_after: False
│   │
│   ├── [2] ScriptSegment
│   │   ├── speaker: ALEX
│   │   ├── text: "Wow, that's incredible!"
│   │   ├── order: 2
│   │   ├── emotion: "excited"
│   │   └── pause_after: True  ← [BREAK] marker
│   │
│   └── ...
│
├── total_word_count: 1487
├── estimated_duration_seconds: 595
├── tone: ToneType.CASUAL
├── length: LengthType.MEDIUM
├── topics_covered: ["Technology", "AI"]
├── sources_cited: ["TechNews", "Wired"]
├── generation_metadata:
│   ├── prompt_version: "1.0.0"
│   ├── model: "gpt-4o"
│   ├── tokens_used: 1523
│   ├── cost_estimate: 0.0428
│   └── ...
└── created_at: 2026-05-04T...
```

This comprehensive flow documentation helps visualize the entire script generation process from input to output!
