"""
Script Generation Service for Personal Podcast Generator.

This module handles the generation of conversational podcast scripts using OpenAI's GPT-4o.
It creates engaging dialogues between two hosts (Alex and Sonia) with natural conversation flow,
emotional cues, and speaker transitions.

Features:
- Async OpenAI integration with GPT-4o
- Configurable tone (Serious/Casual) and length (Short/Long)
- Token usage tracking for cost monitoring
- Comprehensive error handling and retries
- Structured output with speaker tags and break markers
- Version-controlled prompt templates
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

from openai import AsyncOpenAI, OpenAIError, RateLimitError, APITimeoutError
from pydantic import BaseModel, Field, validator

from app.core.config import settings


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# ============================================================================
# Enums
# ============================================================================

class ToneType(str, Enum):
    """Podcast tone types."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    EDUCATIONAL = "educational"
    CONVERSATIONAL = "conversational"


class LengthType(str, Enum):
    """Podcast length types."""
    SHORT = "short"      # ~5 minutes, ~1000 words
    MEDIUM = "medium"    # ~10 minutes, ~2000 words
    LONG = "long"        # ~15 minutes, ~3000 words


class SpeakerType(str, Enum):
    """Podcast speaker types."""
    ALEX = "ALEX"
    SONIA = "SONIA"


# ============================================================================
# Pydantic Models
# ============================================================================

class NewsArticle(BaseModel):
    """
    News article data structure for script generation.

    Attributes:
        title: Article headline
        summary: Brief article summary
        content: Full article text
        source: Article source/publication name
        url: Article URL
        published_at: Publication timestamp
        category: Article category/topic
    """
    title: str = Field(..., description="Article headline")
    summary: str = Field(..., description="Brief article summary")
    content: str = Field(..., description="Full article text")
    source: Optional[str] = Field(None, description="Article source")
    url: Optional[str] = Field(None, description="Article URL")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    category: Optional[str] = Field(None, description="Article category")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ScriptSegment(BaseModel):
    """
    Individual script segment representing a single speaker turn.

    Attributes:
        speaker: Who is speaking (ALEX or SONIA)
        text: What they are saying
        order: Segment order in the script
        emotion: Optional emotional cue (excited, thoughtful, concerned, etc.)
        pause_after: Whether to add a pause after this segment
    """
    speaker: SpeakerType = Field(..., description="Speaker identifier")
    text: str = Field(..., min_length=1, description="Dialogue text")
    order: int = Field(..., ge=0, description="Segment order")
    emotion: Optional[str] = Field(None, description="Emotional cue")
    pause_after: bool = Field(False, description="Add pause after segment")

    @validator('text')
    def clean_text(cls, v):
        """Remove speaker tags and clean whitespace."""
        # Remove common speaker tag patterns
        for pattern in ['[ALEX]:', '[SONIA]:', 'ALEX:', 'SONIA:', '[BREAK]']:
            v = v.replace(pattern, '')
        return v.strip()


class PodcastScript(BaseModel):
    """
    Complete podcast script with metadata.

    Attributes:
        title: News-style headline summarizing the episode
        segments: List of script segments in order
        total_word_count: Total words in script
        estimated_duration_seconds: Estimated audio duration
        tone: Tone used for generation
        length: Target length category
        topics_covered: List of topics discussed
        sources_cited: List of source articles used
        generation_metadata: Additional metadata about generation
        created_at: Script creation timestamp
    """
    title: str = Field(..., max_length=100, description="News-style headline for the episode")
    segments: List[ScriptSegment] = Field(..., min_items=1, description="Script segments")
    total_word_count: int = Field(..., ge=0, description="Total word count")
    estimated_duration_seconds: int = Field(..., ge=0, description="Estimated duration in seconds")
    tone: ToneType = Field(..., description="Script tone")
    length: LengthType = Field(..., description="Target length")
    topics_covered: List[str] = Field(default_factory=list, description="Topics covered")
    sources_cited: List[str] = Field(default_factory=list, description="Sources cited")
    generation_metadata: Dict[str, Any] = Field(default_factory=dict, description="Generation metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")

    def get_full_text(self) -> str:
        """Get complete script as formatted text."""
        lines = []
        for segment in self.segments:
            emotion = f" ({segment.emotion})" if segment.emotion else ""
            lines.append(f"[{segment.speaker.value}]{emotion}: {segment.text}")
            if segment.pause_after:
                lines.append("[BREAK]")
        return "\n\n".join(lines)

    def get_speaker_balance(self) -> Dict[str, float]:
        """Calculate speaking balance between hosts."""
        alex_words = sum(len(s.text.split()) for s in self.segments if s.speaker == SpeakerType.ALEX)
        sonia_words = sum(len(s.text.split()) for s in self.segments if s.speaker == SpeakerType.SONIA)
        total = alex_words + sonia_words
        return {
            "alex_percentage": round((alex_words / total * 100) if total > 0 else 0, 2),
            "sonia_percentage": round((sonia_words / total * 100) if total > 0 else 0, 2)
        }


class GenerationMetrics(BaseModel):
    """
    Metrics for script generation performance.

    Attributes:
        tokens_used: Total tokens consumed
        prompt_tokens: Tokens in prompt
        completion_tokens: Tokens in completion
        model_used: OpenAI model identifier
        latency_ms: Generation latency in milliseconds
        retry_count: Number of retries needed
        cost_estimate: Estimated cost in USD
    """
    tokens_used: int = Field(..., ge=0, description="Total tokens used")
    prompt_tokens: int = Field(..., ge=0, description="Prompt tokens")
    completion_tokens: int = Field(..., ge=0, description="Completion tokens")
    model_used: str = Field(..., description="Model identifier")
    latency_ms: int = Field(..., ge=0, description="Latency in milliseconds")
    retry_count: int = Field(0, ge=0, description="Number of retries")
    cost_estimate: float = Field(..., ge=0, description="Estimated cost USD")


# ============================================================================
# Script Generator Service
# ============================================================================

class ScriptGeneratorService:
    """
    Service for generating podcast scripts using OpenAI GPT-4o.

    This service transforms news articles into engaging conversational podcasts
    with two hosts: Alex (enthusiastic) and Sonia (analytical).

    Features:
    - Async OpenAI integration
    - Configurable tone and length
    - Token usage tracking
    - Automatic retries with exponential backoff
    - Comprehensive error handling
    - Structured output parsing

    Example:
        service = ScriptGeneratorService()
        script = await service.generate_script(
            news_articles=articles,
            preferences={"tone": "casual", "length": "medium"}
        )
    """

    # Prompt version for tracking improvements
    PROMPT_VERSION = "1.0.0"

    # Model configuration
    MODEL = "gpt-4o"
    DEFAULT_TEMPERATURE = 0.8
    DEFAULT_MAX_TOKENS = 4000

    # Cost constants (per 1K tokens) - GPT-4o pricing
    COST_PER_1K_INPUT_TOKENS = 0.0025   # $2.50 per 1M input tokens
    COST_PER_1K_OUTPUT_TOKENS = 0.01    # $10.00 per 1M output tokens

    # Retry configuration
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1.0  # seconds
    MAX_RETRY_DELAY = 10.0     # seconds

    # Length configurations (word counts)
    LENGTH_CONFIG = {
        LengthType.SHORT: {"target_words": 750, "max_tokens": 1500},
        LengthType.MEDIUM: {"target_words": 1500, "max_tokens": 3000},
        LengthType.LONG: {"target_words": 2250, "max_tokens": 4500}
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Script Generator Service.

        Args:
            api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = AsyncOpenAI(api_key=self.api_key)
        logger.info(f"ScriptGeneratorService initialized with prompt version {self.PROMPT_VERSION}")

    async def generate_script(
        self,
        news_articles: List[NewsArticle],
        preferences: Dict[str, Any]
    ) -> tuple[PodcastScript, GenerationMetrics]:
        """
        Generate a podcast script from news articles.

        Args:
            news_articles: List of news articles to transform
            preferences: User preferences (tone, length, topics, etc.)

        Returns:
            Tuple of (PodcastScript, GenerationMetrics)

        Raises:
            ValueError: If no articles provided or invalid preferences
            OpenAIError: If API call fails after retries
        """
        if not news_articles:
            raise ValueError("At least one news article is required")

        # Extract preferences
        tone = ToneType(preferences.get("tone", "professional").lower())

        # Handle length - can be either int (minutes) or string ("short"/"medium"/"long")
        length_value = preferences.get("length", "medium")
        if isinstance(length_value, int):
            # Convert minutes to length category
            if length_value <= 7:
                length_str = "short"
            elif length_value <= 12:
                length_str = "medium"
            else:
                length_str = "long"
        else:
            length_str = str(length_value).lower()

        length = LengthType(length_str)

        logger.info(
            f"Generating script: tone={tone.value}, length={length.value}, "
            f"articles={len(news_articles)}"
        )

        start_time = datetime.utcnow()
        retry_count = 0

        # Build prompt
        system_prompt = self._build_system_prompt(tone)
        user_prompt = self._build_user_prompt(news_articles, tone, length)

        # Generate with retries
        raw_output = None
        usage_data = None

        for attempt in range(self.MAX_RETRIES):
            try:
                raw_output, usage_data = await self._call_openai(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    length=length
                )
                break  # Success

            except RateLimitError as e:
                retry_count += 1
                if attempt < self.MAX_RETRIES - 1:
                    delay = min(
                        self.INITIAL_RETRY_DELAY * (2 ** attempt),
                        self.MAX_RETRY_DELAY
                    )
                    logger.warning(
                        f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error("Max retries exceeded due to rate limiting")
                    raise

            except APITimeoutError as e:
                retry_count += 1
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.INITIAL_RETRY_DELAY * (2 ** attempt)
                    logger.warning(
                        f"API timeout, retrying in {delay}s (attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error("Max retries exceeded due to timeout")
                    raise

            except OpenAIError as e:
                logger.error(f"OpenAI API error: {str(e)}")
                raise

        # Calculate metrics
        end_time = datetime.utcnow()
        latency_ms = int((end_time - start_time).total_seconds() * 1000)

        metrics = GenerationMetrics(
            tokens_used=usage_data["total_tokens"],
            prompt_tokens=usage_data["prompt_tokens"],
            completion_tokens=usage_data["completion_tokens"],
            model_used=self.MODEL,
            latency_ms=latency_ms,
            retry_count=retry_count,
            cost_estimate=self._calculate_cost(
                usage_data["prompt_tokens"],
                usage_data["completion_tokens"]
            )
        )

        logger.info(
            f"Script generated: {metrics.tokens_used} tokens, "
            f"{latency_ms}ms, ${metrics.cost_estimate:.4f}"
        )

        # Parse output into structured script
        script = self._parse_script(
            raw_output=raw_output,
            tone=tone,
            length=length,
            articles=news_articles,
            metrics=metrics
        )

        return script, metrics

    def _build_system_prompt(self, tone: ToneType) -> str:
        """
        Build system prompt based on tone preference.

        Args:
            tone: Desired tone for the podcast

        Returns:
            System prompt string
        """
        base_prompt = """You are a professional radio producer creating an engaging podcast dialogue between two hosts:

**ALEX**: Enthusiastic, energetic, asks probing questions. Brings excitement and curiosity to the conversation. Often introduces new topics and reacts with genuine interest.

**SONIA**: Analytical, thoughtful, provides depth and context. Brings expertise and nuanced perspectives. Often explains complex topics clearly and adds insightful commentary.

Your task is to create a natural, flowing conversation that feels authentic and engaging."""

        tone_instructions = {
            ToneType.PROFESSIONAL: """
TONE: Professional and authoritative
- Focus on facts, data, and expert analysis
- Maintain formal, polished delivery
- Use precise, industry-standard terminology
- Present information with credibility and depth
- Appeal to informed audiences seeking expertise""",

            ToneType.CASUAL: """
TONE: Casual and relaxed
- Use everyday language and relatable examples
- Include light humor and personal reactions
- Show genuine curiosity and surprise
- Make complex topics accessible and fun
- Feel like a conversation between friends""",

            ToneType.EDUCATIONAL: """
TONE: Educational and informative
- Explain concepts clearly with teaching intent
- Break down complex ideas into understandable parts
- Provide context, background, and examples
- Guide listeners through learning journey
- Focus on understanding and knowledge building""",

            ToneType.CONVERSATIONAL: """
TONE: Conversational and engaging
- Natural, flowing dialogue style
- Balance information with entertainment
- Use storytelling and narrative techniques
- Encourage curiosity and exploration
- Keep listeners engaged through dynamic exchanges"""
        }

        format_instructions = """

FORMAT REQUIREMENTS:
- Start each line with speaker tag: [ALEX]: or [SONIA]:
- Add emotional cues in parentheses when relevant: [ALEX] (excited): or [SONIA] (thoughtful):
- Insert [BREAK] on its own line for natural pauses between topics
- Alternate speakers naturally - avoid long monologues
- Include transitions between topics
- End with a strong conclusion

STRUCTURE:
1. Opening: Hook the listener immediately with the most interesting angle
2. Body: Explore 2-4 key topics with depth and different perspectives
3. Discussion: Natural back-and-forth, questions, reactions
4. Closing: Summarize key takeaways and leave listeners thinking

CONVERSATION TIPS:
- Let speakers interrupt or build on each other's points
- Include "hmm", "wow", "interesting" - natural reactions
- Ask clarifying questions
- Reference earlier points in the conversation
- Show genuine engagement between hosts"""

        return base_prompt + tone_instructions[tone] + format_instructions

    def _build_user_prompt(
        self,
        articles: List[NewsArticle],
        tone: ToneType,
        length: LengthType
    ) -> str:
        """
        Build user prompt with article content and specifications.

        Args:
            articles: News articles to include
            tone: Desired tone
            length: Target length

        Returns:
            User prompt string
        """
        target_words = self.LENGTH_CONFIG[length]["target_words"]

        # Prepare article summaries
        articles_text = "\n\n".join([
            f"Article {i+1}: {article.title}\n"
            f"Source: {article.source or 'Unknown'}\n"
            f"Summary: {article.summary}\n"
            f"Content: {article.content[:1000]}..."  # Limit content length
            for i, article in enumerate(articles[:5])  # Limit to 5 articles
        ])

        prompt = f"""Create a podcast script based on these news articles:

{articles_text}

SPECIFICATIONS:
- Target length: ~{target_words} words ({length.value})
- Tone: {tone.value}
- Format: Dialogue between ALEX and SONIA
- Include speaker tags, emotional cues, and [BREAK] markers
- Make it engaging, informative, and natural

Focus on the most interesting angles, surprising facts, and different perspectives. Make listeners want to keep listening!"""

        return prompt

    async def _call_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        length: LengthType
    ) -> tuple[str, Dict[str, int]]:
        """
        Call OpenAI API to generate script.

        Args:
            system_prompt: System instructions
            user_prompt: User request with articles
            length: Target length for token limit

        Returns:
            Tuple of (generated_text, usage_dict)

        Raises:
            OpenAIError: If API call fails
        """
        max_tokens = self.LENGTH_CONFIG[length]["max_tokens"]

        try:
            response = await self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.DEFAULT_TEMPERATURE,
                max_tokens=max_tokens,
                top_p=1.0,
                frequency_penalty=0.3,  # Reduce repetition
                presence_penalty=0.2,   # Encourage topic diversity
            )

            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }

            return content, usage

        except OpenAIError as e:
            logger.error(f"OpenAI API error in _call_openai: {str(e)}")
            raise

    def _parse_script(
        self,
        raw_output: str,
        tone: ToneType,
        length: LengthType,
        articles: List[NewsArticle],
        metrics: GenerationMetrics
    ) -> PodcastScript:
        """
        Parse raw GPT output into structured PodcastScript.

        Args:
            raw_output: Raw text from GPT
            tone: Script tone
            length: Script length category
            articles: Source articles
            metrics: Generation metrics

        Returns:
            Structured PodcastScript object
        """
        segments = []
        lines = raw_output.strip().split('\n')
        order = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for break marker
            if '[BREAK]' in line.upper():
                if segments:  # Add pause to previous segment
                    segments[-1].pause_after = True
                continue

            # Parse speaker tag
            speaker = None
            emotion = None
            text = line

            # Try to extract speaker and emotion
            if line.startswith('[ALEX]'):
                speaker = SpeakerType.ALEX
                text = line[6:].strip()
            elif line.startswith('[SONIA]'):
                speaker = SpeakerType.SONIA
                text = line[7:].strip()
            else:
                # Try without brackets
                if line.upper().startswith('ALEX:'):
                    speaker = SpeakerType.ALEX
                    text = line[5:].strip()
                elif line.upper().startswith('SONIA:'):
                    speaker = SpeakerType.SONIA
                    text = line[6:].strip()

            if not speaker:
                # If no speaker tag, append to previous segment or skip
                if segments:
                    segments[-1].text += " " + text
                continue

            # Extract emotion if present
            if text.startswith('(') and ')' in text:
                emotion_end = text.index(')')
                emotion = text[1:emotion_end]
                text = text[emotion_end+1:].strip()
                if text.startswith(':'):
                    text = text[1:].strip()
            elif ':' in text[:50]:  # Colon near start might be separator
                text = text.split(':', 1)[1].strip()

            if text:  # Only add if there's actual content
                segments.append(ScriptSegment(
                    speaker=speaker,
                    text=text,
                    order=order,
                    emotion=emotion,
                    pause_after=False
                ))
                order += 1

        # Calculate word count and duration
        total_text = " ".join(s.text for s in segments)
        word_count = len(total_text.split())

        # Estimate duration: average speaking rate is ~200 words per minute
        # Add time for pauses
        words_per_minute = 200
        pause_time = sum(2 for s in segments if s.pause_after)  # 2 seconds per pause
        duration_seconds = int((word_count / words_per_minute * 60) + pause_time)

        # Extract topics and sources
        topics = list(set(article.category for article in articles if article.category))
        sources = list(set(article.source for article in articles if article.source))

        # Build metadata
        generation_metadata = {
            "prompt_version": self.PROMPT_VERSION,
            "model": metrics.model_used,
            "tokens_used": metrics.tokens_used,
            "cost_estimate": metrics.cost_estimate,
            "retry_count": metrics.retry_count,
            "generation_timestamp": datetime.utcnow().isoformat(),
            "articles_count": len(articles)
        }

        script = PodcastScript(
            segments=segments,
            total_word_count=word_count,
            estimated_duration_seconds=duration_seconds,
            tone=tone,
            length=length,
            topics_covered=topics,
            sources_cited=sources,
            generation_metadata=generation_metadata,
            created_at=datetime.utcnow()
        )

        # Log speaker balance
        balance = script.get_speaker_balance()
        logger.info(
            f"Script parsed: {len(segments)} segments, {word_count} words, "
            f"{duration_seconds}s, balance={balance}"
        )

        return script

    def _calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        Calculate estimated cost for API call.

        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        input_cost = (prompt_tokens / 1000) * self.COST_PER_1K_INPUT_TOKENS
        output_cost = (completion_tokens / 1000) * self.COST_PER_1K_OUTPUT_TOKENS
        return round(input_cost + output_cost, 4)


# ============================================================================
# Helper Functions
# ============================================================================

async def generate_podcast_script(
    articles: List[NewsArticle],
    tone: str = "professional",
    length: str = "medium"
) -> tuple[PodcastScript, GenerationMetrics]:
    """
    Convenience function to generate a podcast script.

    Args:
        articles: List of news articles
        tone: Tone preference (professional/casual/educational/conversational)
        length: Length preference (short/medium/long)

    Returns:
        Tuple of (PodcastScript, GenerationMetrics)

    Example:
        articles = [NewsArticle(...), ...]
        script, metrics = await generate_podcast_script(
            articles=articles,
            tone="casual",
            length="medium"
        )
    """
    service = ScriptGeneratorService()
    return await service.generate_script(
        news_articles=articles,
        preferences={"tone": tone, "length": length}
    )


def parse_script_text(
    script_text: str,
    tone: str = "professional",
    length: str = "medium"
) -> PodcastScript:
    """
    Parse a manually written script text into a PodcastScript object.

    This function allows you to bypass news fetching and AI script generation
    by directly providing a pre-written script in the standard format.

    Expected format:
        [ALEX] (emotion): dialogue text
        [SONIA] (emotion): dialogue text
        [BREAK]
        [CLOSING]
        [END]

    Args:
        script_text: Raw script text with speaker tags and markers
        tone: Tone type for metadata (professional/casual/educational/conversational)
        length: Length type for metadata (short/medium/long)

    Returns:
        PodcastScript object ready for audio generation

    Example:
        script_text = '''
        [ALEX] (enthusiastic): Welcome to our podcast!
        [SONIA] (thoughtful): Thanks for having me.
        [BREAK]
        [ALEX]: Let's dive into today's topics.
        '''
        script = parse_script_text(script_text, tone="casual", length="short")
    """
    import re

    segments: List[ScriptSegment] = []
    order = 0

    # Split by lines and process
    lines = script_text.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for [BREAK] marker
        if '[BREAK]' in line.upper():
            # Mark the previous segment to pause after
            if segments:
                segments[-1].pause_after = True
            continue

        # Check for special markers to skip
        if any(marker in line.upper() for marker in ['[CLOSING]', '[END]', '```']):
            continue

        # Match speaker pattern: [SPEAKER] (emotion): text or [SPEAKER]: text
        speaker_pattern = r'\[(' + '|'.join([s.value for s in SpeakerType]) + r')\]\s*(?:\(([^)]+)\))?\s*:\s*(.+)'
        match = re.match(speaker_pattern, line, re.IGNORECASE)

        if match:
            speaker_name = match.group(1).upper()
            emotion = match.group(2)
            text = match.group(3).strip()

            # Map to SpeakerType
            try:
                speaker = SpeakerType(speaker_name)
            except ValueError:
                logger.warning(f"Unknown speaker: {speaker_name}, skipping line")
                continue

            # Create segment
            segment = ScriptSegment(
                speaker=speaker,
                text=text,
                order=order,
                emotion=emotion,
                pause_after=False
            )
            segments.append(segment)
            order += 1

    if not segments:
        raise ValueError("No valid segments found in script text")

    # Calculate metadata
    total_words = sum(len(segment.text.split()) for segment in segments)
    estimated_duration = int(total_words / 200 * 60)  # Assume 200 WPM

    # Map tone and length to enums
    try:
        tone_enum = ToneType(tone)
    except ValueError:
        tone_enum = ToneType.PROFESSIONAL

    try:
        length_enum = LengthType(length)
    except ValueError:
        length_enum = LengthType.MEDIUM

    # Create PodcastScript
    script = PodcastScript(
        segments=segments,
        total_word_count=total_words,
        estimated_duration_seconds=estimated_duration,
        tone=tone_enum,
        length=length_enum,
        topics_covered=["Manual Script"],
        sources_cited=["User Provided"],
        generation_metadata={
            "source": "manual_input",
            "parsed_segments": len(segments),
        }
    )

    logger.info(
        f"Parsed script: {len(segments)} segments, {total_words} words, "
        f"~{estimated_duration}s duration"
    )

    return script
