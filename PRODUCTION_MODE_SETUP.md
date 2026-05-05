# Production Mode Setup - Ready to Test

## ✅ Configuration Status

All systems are configured for **FULL PRODUCTION MODE** with real API calls:

### Backend Configuration
- ✅ **ElevenLabs API Key**: Configured in `.env`
- ✅ **OpenAI API Key**: Configured in `.env`
- ✅ **Firecrawl API Key**: Configured in `.env`
- ✅ **Streaming TTS**: Enabled (using `eleven_flash_v2_5`)
- ✅ **Mock Mode**: Disabled (will make real API calls)

### Frontend Configuration
- ✅ **Mock Audio**: Set to `false` in `Home.tsx:188`
- ✅ **Real Audio Generation**: Enabled

## 🚀 How to Start Testing

### 1. Start the Backend

```bash
cd backend

# Make sure dependencies are installed
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

### 2. Start the Frontend

```bash
cd frontend

# Make sure dependencies are installed
npm install

# Start the development server
npm run dev
```

Frontend will be available at: `http://localhost:5173` (or similar)

### 3. Test the Full Pipeline

#### Option A: Full Pipeline (News → Script → Audio)
1. Open the frontend in your browser
2. Login with your credentials
3. Add interests (e.g., "AI", "technology", "startups")
4. Set tone (professional/casual/educational)
5. Set length (short/medium/long)
6. Click "Generate Podcast"
7. Wait for completion (polling will show progress)
8. Listen to the generated audio!

**Expected Timeline:**
- News fetching: ~10-20 seconds
- Script generation: ~30-60 seconds
- Audio generation: ~60-120 seconds (depends on length)
- **Total: ~2-4 minutes**

#### Option B: Script-to-Audio (Skip News + GPT)
Use the test script or API directly:

```bash
cd backend
python test_script_to_audio.py
```

(Update the auth token in the script first)

**Expected Timeline:**
- Script parsing: <1 second
- Audio generation: ~60-120 seconds
- **Total: ~1-2 minutes**

## 💰 API Costs Per Podcast

### Full Pipeline:
```
Firecrawl (news):     ~$0.05
OpenAI (script):      ~$0.30
ElevenLabs (audio):   ~$0.96
------------------------
Total:                ~$1.31
```

### Script-to-Audio:
```
ElevenLabs (audio):   ~$0.96
------------------------
Total:                ~$0.96
```

## 📊 What to Monitor

### 1. Backend Logs
Watch for:
- ✅ "Starting audio generation for podcast: {id}"
- ✅ "Audio segment generated successfully"
- ✅ "Audio generation completed"
- ❌ Any "ElevenLabs API error" messages

### 2. Frontend UI
- Progress updates should show: 0% → 50% → 100%
- Status changes: pending → processing → completed
- Audio URL should appear when completed

### 3. Generated Files
Audio files are saved to: `/tmp/podcasts/{podcast_id}.mp3`

Check:
```bash
ls -lh /tmp/podcasts/
```

## 🔧 Troubleshooting

### "ElevenLabs API error: 401"
- Check your API key in `.env`
- Verify key is active at https://elevenlabs.io/app/settings/api-keys

### "ElevenLabs API error: 402"
- You've run out of credits
- Check your quota at https://elevenlabs.io/app/usage
- Upgrade plan or wait for monthly reset

### "Audio generation takes too long"
- This is normal for streaming TTS
- ~60-120 seconds for a 10-minute podcast
- Check backend logs for progress

### "No audio file generated"
- Check `/tmp/podcasts/` directory exists
- Verify write permissions
- Look for errors in backend logs

### Frontend shows "pending" forever
- Check backend is running (`http://localhost:8000/health`)
- Check backend logs for errors
- Verify polling is working (Network tab in DevTools)

## 🧪 Quick Validation Tests

### Test 1: Health Check
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy"}
```

### Test 2: Authentication
```bash
# Login first to get token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"demopassword"}'
```

### Test 3: Generate Test Podcast (Mock Mode)
```bash
curl -X POST http://localhost:8000/api/v1/podcasts/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "interests": ["AI"],
    "tone": "professional",
    "length": 5,
    "mock_audio": true
  }'
```

### Test 4: Generate Real Podcast (Production Mode)
Change `"mock_audio": true` to `"mock_audio": false` in Test 3.

## 📝 Current Configuration Summary

```yaml
Environment: development (with production API calls)
Debug: true
SQL Echo: false

API Keys:
  - ElevenLabs: ✅ Configured
  - OpenAI: ✅ Configured
  - Firecrawl: ✅ Configured

Services:
  - News Service: ✅ Ready (Firecrawl)
  - Script Service: ✅ Ready (GPT-4)
  - Audio Service: ✅ Ready (ElevenLabs Streaming TTS)
  - Article Selector: ✅ Ready

Models:
  - Script: gpt-4o
  - Audio: eleven_flash_v2_5 (streaming)

Audio Format:
  - Format: MP3
  - Sample Rate: 44100 Hz
  - Bitrate: 128 kbps
  - Channels: Mono
```

## 🎯 Ready to Test!

Everything is configured correctly. Simply:

1. Start backend: `cd backend && uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Open browser to frontend URL
4. Generate your first podcast!

The system will now make **real API calls** to:
- Firecrawl (for news)
- OpenAI (for script)
- ElevenLabs (for audio with streaming)

Good luck! 🎙️🚀
