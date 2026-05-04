# Personal Podcast Generator API Documentation

**Version:** 1.0.0
**Base URL:** `http://localhost:8000/api/v1`

## Overview

Production-grade FastAPI backend for generating personalized podcasts from web content. Features async processing, comprehensive error handling, and observability.

## Table of Contents

- [Getting Started](#getting-started)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Podcast Endpoints](#podcast-endpoints)
  - [User Endpoints](#user-endpoints)
  - [Admin Endpoints](#admin-endpoints)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

---

## Getting Started

### Running the API

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Interactive Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Schema:** http://localhost:8000/openapi.json

---

## Authentication

**Current Status:** No authentication required (MVP)
**Future:** JWT-based authentication with user roles

---

## Endpoints

### Podcast Endpoints

#### 1. Generate Podcast (Async)

**POST** `/api/v1/podcasts/generate`

Triggers asynchronous podcast generation. Returns immediately with `202 Accepted` and a task ID for polling.

**Query Parameters:**
- `user_id` (UUID, required): User identifier

**Request Body:**
```json
{
  "interests": ["artificial intelligence", "machine learning"],
  "tone": "professional",
  "length": 10,
  "sources": ["https://techcrunch.com"]
}
```

**Response (202 Accepted):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "audio_url": null,
  "error_message": null,
  "progress": 0
}
```

**Field Validation:**
- `interests`: 1-10 items, non-empty strings
- `tone`: Must be one of: `professional`, `casual`, `educational`, `conversational`
- `length`: 5-30 minutes
- `sources`: Optional, max 20 URLs

---

#### 2. Get Podcast Details

**GET** `/api/v1/podcasts/{podcast_id}`

Retrieve complete podcast details including status, audio URL, and script.

**Path Parameters:**
- `podcast_id` (UUID, required): Podcast identifier

**Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "123e4567-e89b-12d3-a456-426614174001",
  "status": "completed",
  "audio_url": "https://storage.example.com/podcasts/123.mp3",
  "script": "Welcome to your personalized podcast...",
  "error_message": null,
  "metadata": "{\"topics\": [\"AI\", \"tech\"], \"sources\": 5}",
  "created_at": "2026-05-04T10:00:00Z",
  "updated_at": "2026-05-04T10:05:00Z"
}
```

**Status Values:**
- `pending`: Generation queued
- `processing`: Currently generating
- `completed`: Ready with audio URL
- `failed`: Generation failed (see `error_message`)

---

#### 3. Poll Podcast Status (Lightweight)

**GET** `/api/v1/podcasts/{podcast_id}/status`

Lightweight endpoint optimized for polling. Returns only essential status information.

**Path Parameters:**
- `podcast_id` (UUID, required): Podcast identifier

**Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "audio_url": null,
  "error_message": null,
  "progress": 50
}
```

**Polling Best Practices:**
- Start with 2-second intervals
- Exponential backoff to 10 seconds max
- Stop polling after 5 minutes (timeout)

---

#### 4. List User's Podcasts

**GET** `/api/v1/podcasts/`

Retrieve paginated list of podcasts for a user with optional status filtering.

**Query Parameters:**
- `user_id` (UUID, required): User identifier
- `page` (int, default: 1): Page number (1-indexed)
- `page_size` (int, default: 10): Items per page (1-100)
- `status_filter` (string, optional): Filter by status

**Response (200 OK):**
```json
{
  "podcasts": [...],
  "total": 42,
  "page": 1,
  "page_size": 10,
  "total_pages": 5
}
```

---

### User Endpoints

#### 1. Create User

**POST** `/api/v1/users/`

Create a new user with preferences and settings.

**Request Body:**
```json
{
  "interests": ["technology", "science"],
  "topics": ["AI", "machine learning"],
  "sources": ["TechCrunch", "MIT Technology Review"],
  "language": "en",
  "duration_minutes": 10,
  "voice_settings": {
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "stability": 0.5,
    "similarity_boost": 0.75
  }
}
```

**Response (201 Created):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "preferences": {...},
  "schedule_settings": {...},
  "created_at": "2026-05-04T10:00:00Z",
  "updated_at": "2026-05-04T10:00:00Z"
}
```

---

#### 2. Get User Profile

**GET** `/api/v1/users/{user_id}`

Retrieve complete user profile including preferences and schedule settings.

**Path Parameters:**
- `user_id` (UUID, required): User identifier

**Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "preferences": {
    "interests": ["technology", "science"],
    "topics": ["AI", "climate change"],
    "sources": ["TechCrunch"],
    "language": "en",
    "duration_minutes": 10,
    "voice_settings": {
      "voice_id": "21m00Tcm4TlvDq8ikWAM",
      "stability": 0.5,
      "similarity_boost": 0.75
    }
  },
  "schedule_settings": {
    "enabled": false,
    "frequency": "daily",
    "time": "08:00",
    "timezone": "UTC",
    "days_of_week": [1, 2, 3, 4, 5]
  },
  "created_at": "2026-05-04T10:00:00Z",
  "updated_at": "2026-05-04T10:00:00Z"
}
```

---

#### 3. Update User Preferences

**PUT** `/api/v1/users/{user_id}/preferences`

Update user preferences. Only provided fields are updated (partial update).

**Path Parameters:**
- `user_id` (UUID, required): User identifier

**Request Body (all fields optional):**
```json
{
  "interests": ["AI", "quantum computing"],
  "duration_minutes": 15,
  "voice_settings": {
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "stability": 0.6,
    "similarity_boost": 0.8
  }
}
```

**Response (200 OK):**
Returns updated user profile (same format as GET user).

---

#### 4. Delete User

**DELETE** `/api/v1/users/{user_id}`

Delete user and all associated data (podcasts, metrics). **Irreversible operation.**

**Path Parameters:**
- `user_id` (UUID, required): User identifier

**Response (204 No Content):**
Empty response body.

---

### Admin Endpoints

#### 1. Get Aggregate Statistics

**GET** `/api/v1/admin/stats`

Comprehensive system statistics including KPIs, daily volume data, and recent activity.

**Query Parameters:**
- `days` (int, default: 30): Number of days for volume data

**Response (200 OK):**
```json
{
  "kpis": {
    "total_podcasts": 1234,
    "avg_latency_ms": 45000.5,
    "total_cost_usd": 123.45,
    "success_rate": 98.5,
    "total_tokens": 500000,
    "total_characters": 250000
  },
  "volume_data": [
    {
      "date": "2026-05-04",
      "total": 42,
      "completed": 40,
      "failed": 1,
      "pending": 1,
      "avg_latency_ms": 43500.0,
      "total_cost_usd": 4.25
    }
  ],
  "recent_podcasts": [...],
  "generated_at": "2026-05-04T12:00:00Z"
}
```

**KPI Definitions:**
- `total_podcasts`: All-time podcast count
- `avg_latency_ms`: Average end-to-end generation time
- `total_cost_usd`: Cumulative cost (GPT-4 + ElevenLabs)
- `success_rate`: Percentage of completed podcasts
- `total_tokens`: GPT-4 tokens consumed
- `total_characters`: ElevenLabs characters processed

---

#### 2. Get Recent Podcasts

**GET** `/api/v1/admin/podcasts/recent`

Paginated list of recent podcasts across all users.

**Query Parameters:**
- `page` (int, default: 1): Page number
- `page_size` (int, default: 20): Items per page (1-100)
- `status_filter` (string, optional): Filter by status

**Response (200 OK):**
```json
{
  "podcasts": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "user_id": "123e4567-e89b-12d3-a456-426614174001",
      "status": "completed",
      "created_at": "2026-05-04T10:00:00Z",
      "latency_ms": 45000,
      "cost_usd": 0.12,
      "error_message": null
    }
  ],
  "total": 500,
  "page": 1,
  "page_size": 20
}
```

---

#### 3. Get Daily Metrics

**GET** `/api/v1/admin/metrics/daily`

Daily aggregated metrics for time-series charts and analysis.

**Query Parameters:**
- `days` (int, default: 30): Number of days (1-365)

**Response (200 OK):**
```json
{
  "metrics": [
    {
      "date": "2026-05-04",
      "total": 42,
      "completed": 40,
      "failed": 1,
      "pending": 1,
      "avg_latency_ms": 43500.0,
      "total_cost_usd": 4.25
    }
  ],
  "days": 30,
  "total_podcasts": 1234,
  "total_cost_usd": 123.45
}
```

---

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET/PUT/DELETE |
| 201 | Created | Successful POST (resource created) |
| 202 | Accepted | Async operation started |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid request format |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation failed |
| 500 | Internal Server Error | Server-side error |

### Validation Errors (422)

```json
{
  "detail": "Request validation failed",
  "errors": [
    {
      "loc": ["body", "interests"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limiting

**Current Status:** Not implemented (MVP)
**Future:**
- Anonymous: 10 requests/minute
- Authenticated: 100 requests/minute
- Admin: 1000 requests/minute

---

## Observability

### Logging

All endpoints log:
- Request details (method, path, parameters)
- Operation results (success/failure)
- Performance metrics (latency)
- Error traces (stack traces for failures)

**Log Format:**
```
2026-05-04 10:00:00 - app.api.podcasts - INFO - Creating podcast for user_id=123...
```

### Monitoring Endpoints

- **Health Check:** `GET /health`
- **Metrics:** Use `/admin/stats` for operational metrics

---

## Development

### Running Tests

```bash
# Unit tests
pytest tests/unit

# Integration tests
pytest tests/integration

# All tests with coverage
pytest --cov=app tests/
```

### Code Quality

```bash
# Format code
black app/

# Lint code
ruff check app/

# Type checking
mypy app/
```

---

## Support

For issues or questions:
- **GitHub Issues:** [project-repo]/issues
- **Documentation:** http://localhost:8000/docs
- **Contact:** Prosper AI Team
