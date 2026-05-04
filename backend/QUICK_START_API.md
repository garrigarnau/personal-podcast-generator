# Quick Start Guide - FastAPI Endpoints

**Personal Podcast Generator API**

## Start the Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Test the API

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected: `{"status": "healthy", "service": "personal-podcast-generator", "version": "1.0.0"}`

---

### 2. Create a User

```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "interests": ["artificial intelligence", "technology"],
    "topics": ["machine learning", "startups"],
    "language": "en",
    "duration_minutes": 10
  }'
```

**Save the returned `id` for next steps!**

---

### 3. Generate a Podcast

Replace `<USER_ID>` with the ID from step 2:

```bash
curl -X POST "http://localhost:8000/api/v1/podcasts/generate?user_id=<USER_ID>" \
  -H "Content-Type: application/json" \
  -d '{
    "interests": ["AI", "technology"],
    "tone": "professional",
    "length": 10
  }'
```

**Save the returned `id` for polling!**

---

### 4. Poll Podcast Status

Replace `<PODCAST_ID>` with the ID from step 3:

```bash
curl http://localhost:8000/api/v1/podcasts/<PODCAST_ID>/status
```

Poll every 2-5 seconds until status is `completed`.

---

### 5. Get Completed Podcast

```bash
curl http://localhost:8000/api/v1/podcasts/<PODCAST_ID>
```

Returns full details including `audio_url` and `script`.

---

### 6. List User's Podcasts

```bash
curl "http://localhost:8000/api/v1/podcasts/?user_id=<USER_ID>&page=1&page_size=10"
```

---

### 7. Admin Dashboard Stats

```bash
curl http://localhost:8000/api/v1/admin/stats?days=30
```

Returns KPIs, volume data, and recent podcasts.

---

## Interactive Documentation

Open in browser:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Try all endpoints directly from the browser!

---

## Common Status Codes

- **200** - Success (GET, PUT)
- **201** - Created (POST user)
- **202** - Accepted (POST podcast - async processing)
- **204** - No Content (DELETE)
- **404** - Not Found
- **422** - Validation Error

---

## Environment Variables

Required in `.env`:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/podcast_generator
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
FIRECRAWL_API_KEY=...
```

---

## Complete Example Workflow

```bash
# 1. Create user
USER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{"interests": ["AI"], "language": "en"}')

USER_ID=$(echo $USER_RESPONSE | jq -r '.id')
echo "Created user: $USER_ID"

# 2. Generate podcast
PODCAST_RESPONSE=$(curl -s -X POST \
  "http://localhost:8000/api/v1/podcasts/generate?user_id=$USER_ID" \
  -H "Content-Type: application/json" \
  -d '{"interests": ["AI"], "tone": "professional", "length": 10}')

PODCAST_ID=$(echo $PODCAST_RESPONSE | jq -r '.id')
echo "Started podcast generation: $PODCAST_ID"

# 3. Poll until complete
while true; do
  STATUS=$(curl -s "http://localhost:8000/api/v1/podcasts/$PODCAST_ID/status" | jq -r '.status')
  echo "Status: $STATUS"

  if [ "$STATUS" = "completed" ]; then
    echo "Podcast ready!"
    curl -s "http://localhost:8000/api/v1/podcasts/$PODCAST_ID" | jq '.audio_url'
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "Generation failed"
    break
  fi

  sleep 3
done
```

---

## File Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── podcasts.py       # 4 endpoints
│   │   ├── users.py          # 4 endpoints
│   │   └── admin.py          # 3 endpoints
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── podcast.py        # Request/response schemas
│   │   ├── user.py
│   │   └── admin.py
│   ├── models/               # SQLAlchemy models
│   ├── core/                 # Database, config
│   ├── services/             # Business logic
│   └── main.py               # FastAPI app
├── requirements.txt
└── API_DOCUMENTATION.md      # Full documentation
```

---

## Troubleshooting

### Import Errors

Make sure you have all dependencies:

```bash
pip install -r requirements.txt
```

### Database Connection Errors

Check your `.env` file and ensure PostgreSQL is running:

```bash
# Test database connection
psql $DATABASE_URL
```

### Port Already in Use

Change the port:

```bash
uvicorn app.main:app --reload --port 8001
```

---

## Next Steps

1. **Integrate Services:**
   - Implement `generate_podcast_background` in `podcasts.py`
   - Connect Firecrawl, GPT-4o, and ElevenLabs services

2. **Add Tests:**
   ```bash
   pytest tests/
   ```

3. **Deploy:**
   - Use Docker: `docker-compose up`
   - Or deploy to cloud (AWS, GCP, Azure)

---

**Ready to build amazing podcasts! 🎙️**
