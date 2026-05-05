# Script-to-Audio Implementation

## Overview

This implementation adds a **direct script-to-audio pipeline** that bypasses news fetching and AI script generation. This saves API credits (Firecrawl + OpenAI) when you already have a pre-written script.

## What Was Implemented

### 1. **Script Parser** (`parse_script_text`)
**Location**: `backend/app/services/script_service.py`

A new function that parses manually written scripts with speaker tags:

```python
def parse_script_text(
    script_text: str,
    tone: str = "professional",
    length: str = "medium"
) -> PodcastScript
```

**Supported Format**:
```
[ALEX] (enthusiastic): Welcome to our podcast!
[SONIA] (thoughtful): Great to be here.
[BREAK]
[ALEX]: Let's dive into today's topics.
[CLOSING]
[END]
```

**Features**:
- Parses speaker tags: `[ALEX]`, `[SONIA]`
- Extracts emotions: `(enthusiastic)`, `(thoughtful)`, etc.
- Handles break markers: `[BREAK]`
- Skips special markers: `[CLOSING]`, `[END]`
- Calculates word count and estimated duration
- Creates proper `PodcastScript` object for audio generation

### 2. **New API Endpoint**
**Location**: `backend/app/api/podcasts.py`

```http
POST /api/v1/podcasts/generate-from-script
```

**Request Body**:
```json
{
  "script_text": "[ALEX]: Welcome...",
  "tone": "professional",
  "length": "medium",
  "mock_audio": false
}
```

**Response**: Same as regular podcast generation (202 Accepted with podcast ID)

### 3. **New Request Schema**
**Location**: `backend/app/schemas/podcast.py`

```python
class ScriptToAudioRequest(BaseModel):
    script_text: str
    tone: str = "professional"
    length: str = "medium"
    mock_audio: bool = False
```

### 4. **Background Task Handler**
**Location**: `backend/app/api/podcasts.py`

```python
async def generate_audio_from_script_background(
    podcast_id: UUID,
    user_id: UUID,
    request_data: ScriptToAudioRequest,
    session: AsyncSession,
) -> None
```

**Flow**:
1. Parse script text → `PodcastScript`
2. Save parsed script to database
3. Generate audio using `ElevenLabsAudioService`
4. Save audio file path
5. Update podcast status to completed
6. Save metrics (no GPT tokens, only ElevenLabs characters)

### 5. **Streaming TTS Improvements**
**Location**: `backend/app/services/audio_service.py`

- ✅ Upgraded to ElevenLabs SDK streaming API
- ✅ Using `eleven_flash_v2_5` model for lower latency
- ✅ Removed manual HTTP requests in favor of SDK
- ✅ Fixed `is_break` attribute check bug

## Usage

### Option 1: Using the Test Script

```bash
cd backend
python test_script_to_audio.py
```

(You'll need to update the auth token in the script)

### Option 2: Using cURL

```bash
curl -X POST http://localhost:8000/api/v1/podcasts/generate-from-script \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "script_text": "[ALEX] (enthusiastic): Welcome to our podcast!\n[SONIA] (thoughtful): Thanks for having me.\n[BREAK]\n[ALEX]: Let'\''s dive in.",
    "tone": "professional",
    "length": "medium",
    "mock_audio": false
  }'
```

### Option 3: Frontend Integration

Add a new "Generate from Script" button that calls:

```typescript
const response = await apiClient.post('/api/v1/podcasts/generate-from-script', {
  script_text: userScript,
  tone: 'professional',
  length: 'medium',
  mock_audio: false
});
```

Then poll for completion using the existing `/status` endpoint.

## Benefits

1. **Save API Credits**:
   - ❌ No Firecrawl news fetching
   - ❌ No OpenAI GPT-4 script generation
   - ✅ Only ElevenLabs TTS (which you need anyway)

2. **Faster Iteration**:
   - Edit scripts manually
   - Regenerate audio quickly
   - No waiting for AI generation

3. **Full Control**:
   - Fine-tune dialogue timing
   - Add specific emotions and pauses
   - Control exact wording

## Cost Comparison

### Normal Flow (Full Pipeline):
```
News Fetching (Firecrawl):  ~$0.05 per request
Script Generation (GPT-4):  ~$0.30 (3000 tokens @ $0.01/1K)
Audio Generation (11Labs):  ~$0.96 (3200 chars @ $0.30/1K)
-----------------------------------------------------------
Total:                      ~$1.31 per podcast
```

### Script-to-Audio Flow:
```
News Fetching (Firecrawl):  $0.00 (skipped)
Script Generation (GPT-4):  $0.00 (skipped)
Audio Generation (11Labs):  ~$0.96 (3200 chars @ $0.30/1K)
-----------------------------------------------------------
Total:                      ~$0.96 per podcast
```

**Savings**: ~27% cost reduction

## Script Format Guide

### Basic Structure
```
[SPEAKER] (emotion): dialogue text
```

### Example
```
[ALEX] (enthusiastic): Welcome back to our tech insights podcast!

[SONIA] (thoughtful): Absolutely, Alex. There's quite a bit to unpack.

[BREAK]

[ALEX]: Speaking of technological advancements...

[SONIA] (analytical): It's a significant development.

[CLOSING]

[ALEX] (optimistic): Thanks for tuning in!

[END]
```

### Rules
1. **Speakers**: Must be `[ALEX]` or `[SONIA]` (case-insensitive)
2. **Emotions**: Optional, in parentheses after speaker tag
3. **Breaks**: Use `[BREAK]` to add 1-second pauses
4. **Markers**: `[CLOSING]`, `[END]` are ignored (for organization only)
5. **Colon**: Required after speaker tag (and emotion if present)

## Testing

1. **Test with Mock Mode** (no API costs):
   ```json
   {
     "script_text": "...",
     "mock_audio": true
   }
   ```

2. **Test with Real Audio**:
   ```json
   {
     "script_text": "...",
     "mock_audio": false
   }
   ```

3. **Poll for Status**:
   ```bash
   curl http://localhost:8000/api/v1/podcasts/{podcast_id}/status \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

## Files Changed

1. ✅ `backend/app/services/script_service.py` - Added `parse_script_text()`
2. ✅ `backend/app/services/audio_service.py` - Streaming TTS + bug fixes
3. ✅ `backend/app/api/podcasts.py` - New endpoint + background task
4. ✅ `backend/app/schemas/podcast.py` - New `ScriptToAudioRequest` schema
5. ✅ `backend/app/schemas/audio.py` - Updated model field names
6. ✅ `backend/app/services/__init__.py` - Exported `parse_script_text`
7. ✅ `frontend/src/pages/Home.tsx` - Enabled real audio (mock_audio=false)
8. ✅ `backend/test_script_to_audio.py` - Test script created

## Next Steps

1. **Add Frontend UI**:
   - Add "Generate from Script" tab/button
   - Text area for script input
   - Same polling mechanism as regular generation

2. **Add Script Editor**:
   - Syntax highlighting for speaker tags
   - Real-time validation
   - Preview word count / duration

3. **Script Library**:
   - Save/load script templates
   - Share scripts between users
   - Version control for scripts

## Troubleshooting

### "No valid segments found in script text"
- Check that speaker tags are `[ALEX]` or `[SONIA]`
- Ensure colons after speaker tags
- Verify script has actual dialogue text

### "Audio generation failed"
- Check `ELEVENLABS_API_KEY` is set in `.env`
- Verify you have ElevenLabs API credits
- Try with `mock_audio: true` first to test parsing

### "Authentication failed"
- Get a valid JWT token first (login endpoint)
- Include token in Authorization header
- Token expires after configured time

## Example Test Script

See the full example script in `/Users/arnau.garriga/Documents/UNI/prosper/personal-podcast-generator/backend/test_script_to_audio.py`

The script includes:
- Complete working example
- Polling logic
- Error handling
- Progress tracking
