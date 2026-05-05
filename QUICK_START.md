# 🚀 Quick Start - Production Mode

## Ready to Test!

Everything is configured for **FULL PRODUCTION MODE** with:
- ✅ Real ElevenLabs Streaming TTS
- ✅ Real OpenAI Script Generation
- ✅ Real Firecrawl News Fetching

## Fast Start

```bash
# Option 1: Automated startup
./START_PRODUCTION_TEST.sh

# Option 2: Manual startup
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## Test Full Pipeline

1. Open browser: `http://localhost:5173`
2. Login with credentials
3. Add interests: "AI", "technology"
4. Set preferences (tone, length)
5. Click "Generate Podcast"
6. Wait 2-4 minutes
7. Listen to your podcast!

## Test Script-to-Audio (Skip News + GPT)

```bash
cd backend
python test_script_to_audio.py
```

Or use the new endpoint:
```http
POST /api/v1/podcasts/generate-from-script
```

## Key Changes Made

### 1. Streaming TTS Implemented ✅
- Using ElevenLabs SDK streaming API
- Model: `eleven_flash_v2_5` (low latency)
- No more manual HTTP requests

### 2. Script-to-Audio Mode ✅
- New endpoint: `/generate-from-script`
- Bypasses Firecrawl + OpenAI
- Saves ~$0.35 per podcast

### 3. Production Mode Enabled ✅
- Frontend: `mock_audio: false`
- Backend: Real API calls
- All keys configured

## What to Expect

### Timeline
- News fetching: ~10-20s
- Script generation: ~30-60s
- Audio generation: ~60-120s
- **Total: 2-4 minutes**

### Costs
- Full Pipeline: ~$1.31/podcast
- Script-to-Audio: ~$0.96/podcast

### Output
- Audio files: `/tmp/podcasts/{id}.mp3`
- Format: MP3, 44.1kHz, 128kbps, mono

## Monitoring

Backend logs will show:
```
✅ Starting audio generation for podcast: {id}
✅ Audio segment generated successfully
✅ Audio generation completed
```

Frontend will show:
- Progress: 0% → 50% → 100%
- Status: pending → processing → completed

## Need Help?

See full details:
- `PRODUCTION_MODE_SETUP.md` - Complete setup guide
- `SCRIPT_TO_AUDIO_IMPLEMENTATION.md` - Script-to-audio docs

## Quick Troubleshooting

**"No audio generated"**: Check `/tmp/podcasts/` exists
**"API error 401"**: Check API keys in `.env`
**"API error 402"**: Out of credits, check usage

---

**You're all set! Start the services and test! 🎙️**
