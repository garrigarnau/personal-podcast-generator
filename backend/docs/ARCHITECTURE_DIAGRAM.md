# Orchestration Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Frontend (React + TypeScript)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │   Generate   │  │    Status    │  │     Task     │  │    Admin     ││
│  │   Podcast    │  │    Polling   │  │  Monitoring  │  │  Dashboard   ││
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘│
└─────────┼──────────────────┼──────────────────┼──────────────────┼───────┘
          │                  │                  │                  │
          │ POST /generate   │ GET /status      │ GET /tasks       │ GET /admin
          │                  │                  │                  │
┌─────────▼──────────────────▼──────────────────▼──────────────────▼───────┐
│                         FastAPI Backend (Python)                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                      API Layer (app/api/)                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │  │
│  │  │  podcasts.py │  │   tasks.py   │  │   admin.py   │            │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────────┘            │  │
│  └─────────┼──────────────────┼───────────────────────────────────────┘  │
│            │                  │                                           │
│            │ Background Task  │ Query Status                              │
│            │                  │                                           │
│  ┌─────────▼──────────────────▼───────────────────────────────────────┐  │
│  │              Task Management Layer (app/services/)                 │  │
│  │                                                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │                     TaskManager                              │  │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │  │  │
│  │  │  │  Task Queue  │→ │   Semaphore  │→ │ Queue Worker │     │  │  │
│  │  │  │  (Priority)  │  │ (Concurrent) │  │  (Async)     │     │  │  │
│  │  │  └──────────────┘  └──────────────┘  └──────┬───────┘     │  │  │
│  │  └───────────────────────────────────────────────┼─────────────┘  │  │
│  └────────────────────────────────────────────────────┼───────────────┘  │
│                                                        │                  │
│                                          Execute Task  │                  │
│                                                        │                  │
│  ┌────────────────────────────────────────────────────▼───────────────┐  │
│  │                   PodcastOrchestrator                               │  │
│  │                                                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │  Stage 1: Update Status → PROCESSING                        │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  │                           ↓                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │  Stage 2: Fetch News Articles                               │  │  │
│  │  │  ┌──────────────────────────────────────────────────────┐  │  │  │
│  │  │  │         NewsService (Firecrawl API)                  │  │  │  │
│  │  │  │  • Search by interests                               │  │  │  │
│  │  │  │  • Filter by date                                    │  │  │  │
│  │  │  │  • Rank by relevance                                 │  │  │  │
│  │  │  │  • Return top N articles                             │  │  │  │
│  │  │  └──────────────────────────────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  │                           ↓                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │  Stage 3: Generate Script                                   │  │  │
│  │  │  ┌──────────────────────────────────────────────────────┐  │  │  │
│  │  │  │      ScriptService (OpenAI GPT-4o)                   │  │  │  │
│  │  │  │  • Convert articles to dialogue                      │  │  │  │
│  │  │  │  • Apply tone preferences                            │  │  │  │
│  │  │  │  • Format with speaker tags                          │  │  │  │
│  │  │  │  • Save script to DB                                 │  │  │  │
│  │  │  └──────────────────────────────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  │                           ↓                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │  Stage 4: Generate Audio                                    │  │  │
│  │  │  ┌──────────────────────────────────────────────────────┐  │  │  │
│  │  │  │       AudioService (ElevenLabs TTS)                  │  │  │  │
│  │  │  │  • Process segments by speaker                       │  │  │  │
│  │  │  │  • Generate audio for each segment                   │  │  │  │
│  │  │  │  • Combine segments                                  │  │  │  │
│  │  │  │  • Save to local storage                             │  │  │  │
│  │  │  └──────────────────────────────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  │                           ↓                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │  Stage 5: Save Results & Metrics                            │  │  │
│  │  │  • Update podcast with audio URL                            │  │  │
│  │  │  • Save comprehensive metrics                               │  │  │
│  │  │  • Update status → COMPLETED                                │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  │                                                                     │  │
│  │  Error Handling (Any Stage):                                       │  │
│  │  • Catch exceptions                                                │  │
│  │  • Save partial results                                            │  │
│  │  • Mark status → FAILED                                            │  │
│  │  • Log error with context                                          │  │
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                           │
│            ┌───────────────────────────────────────────────┐             │
│            │       Database (PostgreSQL + AsyncPG)         │             │
│            │  ┌─────────────┐  ┌─────────────┐            │             │
│            │  │   Podcasts  │  │   Metrics   │            │             │
│            │  │   (Status)  │  │   (Costs)   │            │             │
│            │  └─────────────┘  └─────────────┘            │             │
│            └───────────────────────────────────────────────┘             │
└───────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. API Layer
- **podcasts.py**: Handles podcast generation requests, creates DB records
- **tasks.py**: Provides task monitoring and management endpoints
- **admin.py**: Analytics and system statistics

### 2. Task Management Layer
- **TaskManager**: Manages background task execution
  - Priority queue for task scheduling
  - Semaphore for concurrency control (default: 5)
  - Queue worker for async execution
  - Status tracking per task

### 3. Orchestration Layer
- **PodcastOrchestrator**: Coordinates the complete pipeline
  - Manages database transactions
  - Tracks stage-by-stage progress
  - Collects metrics from all services
  - Handles errors gracefully

### 4. Service Layer
- **NewsService**: Fetches and ranks news articles
- **ScriptService**: Generates conversational scripts
- **AudioService**: Converts scripts to speech

### 5. Database Layer
- **Podcasts**: Stores podcast records and status
- **Metrics**: Tracks performance and costs
- **Users**: Stores user preferences

## Data Flow

### Request Flow
```
1. User submits generation request
   ↓
2. API creates podcast record (status: PENDING)
   ↓
3. Background task added to TaskManager queue
   ↓
4. Queue worker picks up task (status: QUEUED → RUNNING)
   ↓
5. Orchestrator executes pipeline stages
   ↓
6. Database updated at each stage
   ↓
7. Final status: COMPLETED or FAILED
```

### Status Updates
```
PENDING → PROCESSING → COMPLETED
                    ↘ FAILED (on error)
```

### Metrics Collection
```
Each Stage:
  ├─ Start time
  ├─ Execute operation
  ├─ End time
  ├─ Calculate latency
  ├─ Track resource usage
  └─ Estimate cost

Final:
  ├─ Aggregate all metrics
  ├─ Calculate total latency
  ├─ Sum costs
  └─ Save to database
```

## Error Handling Flow

```
Service Call
    ↓
Try:
  ├─ Execute operation
  ├─ Retry on transient errors
  └─ Return result
    ↓
Catch Exception:
  ├─ Log error with context
  ├─ Save partial results
  ├─ Update status to FAILED
  ├─ Save error message
  └─ Continue to cleanup
    ↓
Finally:
  ├─ Close connections
  ├─ Release resources
  └─ Update task status
```

## Concurrency Model

```
┌─────────────────────────────────────────┐
│         Incoming Requests               │
│  (Unlimited - non-blocking)             │
└────────────┬────────────────────────────┘
             │
             ↓ Add to Queue
┌─────────────────────────────────────────┐
│      Task Queue (Priority-based)        │
│  ┌───────┐ ┌───────┐ ┌───────┐         │
│  │ High  │ │Normal │ │  Low  │         │
│  │Priority│ │Priority│ │Priority│       │
│  └───────┘ └───────┘ └───────┘         │
└────────────┬────────────────────────────┘
             │
             ↓ Queue Worker
┌─────────────────────────────────────────┐
│        Semaphore (Max: 5)               │
│  ┌──────┐ ┌──────┐ ┌──────┐            │
│  │ Task │ │ Task │ │ Task │ ... (max 5)│
│  │  1   │ │  2   │ │  3   │            │
│  └──────┘ └──────┘ └──────┘            │
└─────────────────────────────────────────┘
             │
             ↓ Execute
    Orchestrator Pipeline
```

## Monitoring Points

```
Application Level:
├─ Total tasks processed
├─ Success/failure rate
├─ Average latency per stage
└─ Total costs

Task Level:
├─ Current status
├─ Duration
├─ Stage progress
└─ Error messages

System Level:
├─ Active tasks
├─ Queue depth
├─ Database connections
└─ API rate limits
```
