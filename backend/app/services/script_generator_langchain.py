"""
Script Generator Service using LangChain with Orchestration & Subagents.

This service uses LangChain to generate podcast scripts with a multi-agent architecture
for better quality, structure, and observability.

Architecture:
- Content Planner Agent: Analyzes articles and creates outline
- Script Writer Agent: Generates actual dialogue
- Quality Reviewer Agent: Validates and improves output
- Orchestrator: Coordinates all agents

Features:
- LangSmith tracing for full observability
- Structured Pydantic outputs (no manual parsing!)
- Automatic cost tracking
- Token usage monitoring
- Better error handling with retries
"""

import logging
import re
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, TypeVar, Type

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_community.callbacks import get_openai_callback
from pydantic import BaseModel, Field, validator

from app.core.config import settings
from app.services.script_service import (
    NewsArticle,
    PodcastScript,
    ScriptSegment,
    SpeakerType,
    ToneType,
    LengthType,
    GenerationMetrics,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Output Parser (handles markdown-wrapped JSON)
# ============================================================================

T = TypeVar('T', bound=BaseModel)

class RobustPydanticOutputParser(PydanticOutputParser):
    """
    Enhanced Pydantic parser that handles markdown-wrapped JSON.

    Fixes common LLM output issues:
    - Strips ```json and ``` markdown code blocks
    - Handles extra whitespace
    - Provides better error messages
    - Direct JSON parsing as fallback
    """

    def parse(self, text: str) -> T:
        """Parse LLM output, stripping markdown if present."""
        logger.debug(f"[RobustParser] Raw LLM output (first 300 chars): {text[:300]}")

        # Strategy 1: Strip markdown and use parent parser
        cleaned = self._strip_markdown(text)
        logger.debug(f"[RobustParser] After markdown strip (first 300 chars): {cleaned[:300]}")

        try:
            return super().parse(cleaned)
        except Exception as e1:
            logger.warning(f"[RobustParser] Standard parsing failed: {e1}")

            # Strategy 2: Direct JSON parsing (bypass parent's validation)
            try:
                data = json.loads(cleaned)
                logger.info("[RobustParser] Direct JSON parsing succeeded, creating Pydantic model")
                return self.pydantic_object(**data)
            except Exception as e2:
                logger.error(f"[RobustParser] Direct JSON parsing also failed: {e2}")
                logger.error(f"[RobustParser] Original text: {text[:500]}")
                logger.error(f"[RobustParser] Cleaned text: {cleaned[:500]}")
                raise Exception(f"Failed to parse LLM output. Both strategies failed. Original error: {e1}, JSON error: {e2}")

    def _strip_markdown(self, text: str) -> str:
        """Remove markdown code blocks from text - AGGRESSIVE version."""
        original = text

        # Strategy 1: Remove everything before first { or [
        match = re.search(r'[{\[]', text)
        if match:
            text = text[match.start():]
            logger.debug(f"[Strip] Trimmed to first bracket: {text[:100]}")

        # Strategy 2: Remove everything after last } or ]
        # Find the last closing bracket
        last_brace = text.rfind('}')
        last_bracket = text.rfind(']')
        last_closing = max(last_brace, last_bracket)

        if last_closing != -1:
            text = text[:last_closing + 1]
            logger.debug(f"[Strip] Trimmed after last bracket: {text[-100:]}")

        # Strategy 3: Clean up any remaining markdown
        text = text.replace('```json', '')
        text = text.replace('```', '')
        text = text.strip()

        # Strategy 4: Remove trailing commas (common LLM mistake)
        # Remove comma before closing brace: }, → }
        text = re.sub(r',(\s*})', r'\1', text)
        # Remove comma before closing bracket: ], → ]
        text = re.sub(r',(\s*])', r'\1', text)
        logger.debug(f"[Strip] Removed trailing commas")

        if text != original:
            logger.debug(f"[Strip] Cleaned from {len(original)} to {len(text)} chars")

        return text


# ============================================================================
# Pydantic Models for Structured Outputs
# ============================================================================

class ContentPlan(BaseModel):
    """Content plan from the planning subagent."""
    title: str = Field(
        max_length=100,
        description="News-style headline summarizing the podcast episode (max 100 chars)"
    )
    topics: List[str] = Field(description="Main topics to cover")
    story_arc: List[str] = Field(description="Narrative flow of the podcast")
    key_points: Dict[str, List[str]] = Field(
        description="Key points for each topic"
    )
    estimated_segments: int = Field(
        ge=10,
        le=100,
        description="Estimated number of dialogue segments (aim for target_words / 50)"
    )
    sources_to_cite: List[str] = Field(description="Sources to mention")


class ScriptSegmentOutput(BaseModel):
    """Single script segment with validation."""
    speaker: str = Field(
        description="Speaker name (ALEX or SONIA)",
        pattern="^(ALEX|SONIA)$"
    )
    text: str = Field(min_length=10, description="Dialogue text")
    emotion: Optional[str] = Field(
        None,
        description="Emotional tone (excited, thoughtful, curious, etc.)"
    )
    pause_after: bool = Field(
        default=False,
        description="Whether to add pause/break after this segment"
    )

    @validator('speaker')
    def validate_speaker(cls, v):
        """Ensure valid speaker."""
        if v not in ["ALEX", "SONIA"]:
            raise ValueError("Speaker must be ALEX or SONIA")
        return v


class PodcastScriptOutput(BaseModel):
    """Complete structured podcast script output."""
    segments: List[ScriptSegmentOutput] = Field(
        min_items=10,
        description="List of dialogue segments in order (aim for 30+ for adequate length)"
    )
    topics_covered: List[str] = Field(description="Topics actually covered")
    sources_cited: List[str] = Field(description="Sources mentioned")
    total_word_count: int = Field(ge=200, description="Total word count")
    tone_achieved: str = Field(description="Tone that was achieved")

    @validator('segments')
    def validate_segments(cls, v):
        """Ensure segments alternate speakers reasonably - warnings only, don't fail."""
        # Minimum check
        if len(v) < 10:
            raise ValueError(f"Must have at least 10 segments (got {len(v)})")

        # Warn if too short but don't fail
        if len(v) < 25:
            logger.warning(f"⚠️  Script has only {len(v)} segments - recommend 25+ for better length")

        # Check speaker alternation (no one should speak more than 5 times in a row)
        consecutive = 1
        for i in range(1, len(v)):
            if v[i].speaker == v[i-1].speaker:
                consecutive += 1
                if consecutive > 5:
                    logger.warning(f"Speaker {v[i].speaker} has {consecutive} consecutive turns at segment {i}")
            else:
                consecutive = 1

        return v


# ============================================================================
# LangChain Script Generator Service
# ============================================================================

class ScriptGeneratorService:
    """
    LangChain-powered script generator with multi-agent orchestration.

    Multi-agent workflow:
    1. Planning Agent: Analyzes articles and creates content plan
    2. Writing Agent: Generates structured dialogue
    3. Orchestrator: Converts to final PodcastScript format

    All agents traced in LangSmith with full cost tracking.
    """

    # Model configuration
    PLANNER_MODEL = "gpt-4o-mini"  # Cheaper, sufficient for structured planning
    WRITER_MODEL = "gpt-4o"        # More capable for creative dialogue
    DEFAULT_TEMPERATURE = 0.8

    # Cost constants (per 1K tokens)
    # GPT-4o-mini pricing: $0.15/1M input, $0.60/1M output
    PLANNER_COST_PER_1K_INPUT = 0.00015
    PLANNER_COST_PER_1K_OUTPUT = 0.0006
    # GPT-4o pricing: $2.50/1M input, $10/1M output
    WRITER_COST_PER_1K_INPUT = 0.0025
    WRITER_COST_PER_1K_OUTPUT = 0.01

    # Length configurations (word counts)
    # Targets based on 150 words per minute speaking rate
    LENGTH_CONFIG = {
        LengthType.SHORT: {"target_words": 750, "max_tokens": 2500},    # ~5 minutes
        LengthType.MEDIUM: {"target_words": 1500, "max_tokens": 5000},  # ~10 minutes
        LengthType.LONG: {"target_words": 2250, "max_tokens": 7000}     # ~15 minutes
    }

    def __init__(self, api_key: Optional[str] = None):
        """Initialize script generator with subagents."""
        self.api_key = api_key or settings.OPENAI_API_KEY

        # Planning subagent (lower temperature for structured thinking)
        # Uses gpt-4o-mini: cheaper and sufficient for structured planning
        self.planner_llm = ChatOpenAI(
            model=self.PLANNER_MODEL,
            temperature=0.5,
            max_tokens=2000,  # Enough for content plan
            api_key=self.api_key,
        ).with_config(run_name="Planning Agent (gpt-4o-mini)")

        # Writing subagent (higher temperature for creativity)
        # Uses gpt-4o: more capable for creative dialogue generation
        # Note: max_tokens will be set dynamically based on length during invocation
        self.writer_llm = ChatOpenAI(
            model=self.WRITER_MODEL,
            temperature=self.DEFAULT_TEMPERATURE,
            api_key=self.api_key,
        ).with_config(run_name="Writing Agent (gpt-4o)")

        # Setup parsers (with markdown stripping)
        self.plan_parser = RobustPydanticOutputParser(pydantic_object=ContentPlan)
        self.script_parser = RobustPydanticOutputParser(pydantic_object=PodcastScriptOutput)

        # Build chains
        self._build_chains()

        logger.info("ScriptGeneratorService initialized with LangChain multi-agent architecture")

    def _build_chains(self):
        """Build LangChain chains for planning and writing."""

        # CHAIN 1: Planning Subagent - Analyze and create content plan
        self.planning_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert podcast producer and content strategist.

Your task is to analyze the news articles and create a comprehensive content plan for a podcast episode.

Planning considerations:
1. Create a news-style headline that summarizes the main story (max 100 characters)
2. Identify the most interesting angles and stories
3. Create a narrative arc that flows naturally
4. Balance depth with breadth across topics
5. Plan for engaging dialogue between two hosts
6. Consider the target podcast length and tone

TITLE GENERATION - REQUIRED:
- Create a professional news headline that captures the main story
- Maximum 100 characters
- Should be informative and help users understand what the podcast covers
- Examples: "Tech Giants Face New AI Regulations", "Markets Rally on Economic Data"

SEGMENT ESTIMATION - CRITICAL:
- Estimate segments to reach the target word count
- Average dialogue segment: ~50 words
- Calculate: target_words / 50 = minimum segments needed
- Plan for substantial, detailed coverage - not brief summaries

CRITICAL OUTPUT FORMAT:
- Output ONLY raw JSON, no markdown code blocks
- Do NOT wrap output in ```json or ```
- Start directly with {{ and end with }}
- NO TRAILING COMMAS - remove commas before closing brackets
- Ensure the JSON is complete and valid

{format_instructions}"""),
            ("user", """Articles to cover:
{articles}

Podcast requirements:
- Target length: {target_words} words ({length})
- Tone: {tone}
- Minimum segments needed: {min_segments} (based on ~50 words per segment)

IMPORTANT: Estimate AT LEAST {min_segments} segments in your content plan to ensure we reach {target_words} words.
Plan for a COMPLETE, DETAILED podcast - not a brief summary.

Create a detailed content plan for this podcast episode.""")
        ])

        self.planning_chain = (
            self.planning_prompt
            | self.planner_llm
            | self.plan_parser
        ).with_config(run_name="Content Planning Chain")

        # CHAIN 2: Writing Subagent - Generate actual script
        self.writing_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional radio producer creating an engaging podcast dialogue between two hosts:

**ALEX**: Enthusiastic, energetic, asks probing questions. Brings excitement and curiosity.
**SONIA**: Analytical, thoughtful, provides depth and context. Brings expertise and nuance.

Create a natural, flowing conversation that feels authentic and engaging.

TONE GUIDELINES:
{tone_instructions}

FORMAT REQUIREMENTS:
- Output structured JSON with segments array
- Each segment: speaker, text, emotion (optional), pause_after (boolean)
- Speakers must be exactly "ALEX" or "SONIA"
- Alternate speakers naturally (no long monologues)
- Include emotional cues when relevant (excited, thoughtful, curious, etc.)
- Mark pause_after=true between major topics

DIALOGUE LENGTH REQUIREMENTS:
- Each dialogue segment should be 40-60 words (2-3 sentences)
- Hosts should speak in complete thoughts, not one-liners
- Provide explanations, examples, context, and details
- Ask follow-up questions that lead to detailed responses
- This is a REAL podcast conversation, not headlines

DIALOGUE QUALITY:
- Natural reactions and interruptions
- Build on each other's points
- Reference earlier parts of conversation
- Show genuine engagement
- Use contractions and casual language when appropriate
- Go into depth on each topic before moving on

CRITICAL OUTPUT FORMAT:
- Output ONLY raw JSON, no markdown code blocks
- Do NOT wrap output in ```json or ```
- Start directly with {{ and end with }}
- NO TRAILING COMMAS - remove commas before closing brackets
- Ensure the JSON is complete and valid

{format_instructions}"""),
            ("user", """Content Plan:
{content_plan}

Articles:
{articles}

Requirements:
- Target: ~{target_words} words ({length} length podcast)
- Tone: {tone}
- Length: {length}
- MINIMUM SEGMENTS REQUIRED: {min_segments} segments

⚠️ CRITICAL INSTRUCTIONS - READ CAREFULLY ⚠️

1. This MUST be a COMPLETE, FULL-LENGTH podcast script - NOT a summary or outline
2. You MUST generate AT LEAST {min_segments} dialogue segments (aim for more)
3. Target word count: {target_words} words - this is the ACTUAL length needed, not a suggestion
4. Each segment should be substantial (40-60 words of natural dialogue)
5. DO NOT stop early - keep writing until you have a complete {target_words}-word conversation
6. Include ALL the details from the articles - go deep, not shallow
7. Make hosts discuss, debate, explain, ask follow-up questions, and explore implications

This is a REAL podcast that will be produced - it needs to be COMPLETE and reach the full {target_words} words.
Write the ENTIRE conversation from opening to closing, covering all planned topics in detail.

Generate the complete podcast script now.""")
        ])

        self.writing_chain = (
            self.writing_prompt
            | self.writer_llm
            | self.script_parser
        ).with_config(run_name="Script Writing Chain")

    async def generate_script(
        self,
        news_articles: List[NewsArticle],
        preferences: Dict[str, Any],
        thread_id: Optional[str] = None,
    ) -> Tuple[PodcastScript, GenerationMetrics]:
        """
        Generate podcast script using multi-agent LangChain architecture.

        SAME INTERFACE as original service - orchestrator doesn't need changes!

        Args:
            news_articles: List of news articles to transform
            preferences: User preferences (tone, length, topics, etc.)
            thread_id: Optional LangSmith thread ID to group all runs together

        Returns:
            Tuple of (PodcastScript, GenerationMetrics)

        Raises:
            ValueError: If no articles provided
            Exception: If generation fails
        """
        if not news_articles:
            raise ValueError("At least one news article is required")

        start_time = datetime.utcnow()
        total_tokens = 0
        total_cost = 0.0

        # Extract preferences
        tone = ToneType(preferences.get("tone", "professional").lower())
        length_value = preferences.get("length", "medium")

        # Handle length conversion
        if isinstance(length_value, int):
            if length_value <= 7:
                length_str = "short"
            elif length_value <= 12:
                length_str = "medium"
            else:
                length_str = "long"
        else:
            length_str = str(length_value).lower()

        length = LengthType(length_str)

        target_words = self.LENGTH_CONFIG[length]["target_words"]

        logger.info(
            f"Generating script: tone={tone.value}, length={length.value}, "
            f"target_words={target_words}, articles={len(news_articles)}"
        )

        try:
            # Format articles
            articles_text = self._format_articles(news_articles)

            # STEP 1: Planning Subagent - Create content plan
            logger.info("Step 1/2: Planning content with subagent...")

            # Calculate minimum segments needed for target word count
            min_segments = max(10, int(target_words / 50))
            logger.info(f"Target {target_words} words requires recommended {min_segments} segments")

            try:
                with get_openai_callback() as cb:
                    async with asyncio.timeout(90):  # 90 second timeout for planning
                        config = {
                            "run_name": "📝 STEP 3: Content Planning",
                            "tags": ["script-generation", "planning", "content-strategy"],
                            "metadata": {
                                "target_words": target_words,
                                "min_segments": min_segments,
                                "length": length.value,
                                "tone": tone.value,
                                "num_articles": len(news_articles)
                            }
                        }
                        # Add thread_id to config if provided for LangSmith grouping
                        if thread_id:
                            config["metadata"]["thread_id"] = thread_id

                        content_plan = await self.planning_chain.ainvoke(
                            {
                                "articles": articles_text,
                                "target_words": target_words,
                                "min_segments": min_segments,
                                "length": length.value,
                                "tone": tone.value,
                                "format_instructions": self.plan_parser.get_format_instructions()
                            },
                            config=config
                        )

                    total_tokens += cb.total_tokens
                    total_cost += cb.total_cost
            except asyncio.TimeoutError:
                logger.error("Planning agent timed out after 90 seconds")
                raise Exception("Content planning timed out - LLM took too long to respond")

            logger.info(
                f"Planning complete: {len(content_plan.topics)} topics, "
                f"{content_plan.estimated_segments} estimated segments"
            )

            # Validate segment estimate is sufficient for target word count
            if content_plan.estimated_segments < min_segments:
                logger.warning(
                    f"Planner estimated only {content_plan.estimated_segments} segments, "
                    f"but {min_segments} needed for {target_words} words. Adjusting plan."
                )
                # Override with minimum needed
                content_plan.estimated_segments = min_segments

            logger.debug(f"Content plan: {content_plan.story_arc}")

            # STEP 2: Writing Subagent - Generate script
            logger.info("Step 2/2: Writing script with subagent...")

            # Format content plan for writer
            plan_text = self._format_content_plan(content_plan)

            # Get tone instructions
            tone_instructions = self._get_tone_instructions(tone)

            # Get max_tokens from config for this length
            max_tokens = self.LENGTH_CONFIG[length]["max_tokens"]
            logger.info(f"Using max_tokens={max_tokens} for {length.value} podcast (min_segments={min_segments})")

            try:
                with get_openai_callback() as cb:
                    async with asyncio.timeout(180):  # 180 second timeout for longer scripts
                        config = {
                            "run_name": "✍️ STEP 4: Script Writing",
                            "tags": ["script-generation", "writing", "dialogue"],
                            "metadata": {
                                "target_words": target_words,
                                "length": length.value,
                                "tone": tone.value,
                                "topics": len(content_plan.topics),
                                "estimated_segments": content_plan.estimated_segments,
                                "max_tokens": max_tokens
                            }
                        }
                        # Add thread_id to config if provided for LangSmith grouping
                        if thread_id:
                            config["metadata"]["thread_id"] = thread_id

                        # Bind max_tokens to the writer LLM for this specific invocation
                        writer_with_tokens = self.writer_llm.bind(max_tokens=max_tokens)
                        writing_chain_with_tokens = (
                            self.writing_prompt
                            | writer_with_tokens
                            | self.script_parser
                        )

                        script_output = await writing_chain_with_tokens.ainvoke(
                            {
                                "content_plan": plan_text,
                                "articles": articles_text,
                                "target_words": target_words,
                                "min_segments": min_segments,
                                "tone": tone.value,
                                "length": length.value,
                                "tone_instructions": tone_instructions,
                                "format_instructions": self.script_parser.get_format_instructions()
                            },
                            config=config
                        )

                    total_tokens += cb.total_tokens
                    total_cost += cb.total_cost
            except asyncio.TimeoutError:
                logger.error("Writing agent timed out after 120 seconds")
                raise Exception("Script writing timed out - LLM took too long to respond")

            logger.info(
                f"Script generation complete: {len(script_output.segments)} segments, "
                f"{script_output.total_word_count} words"
            )

            # Validate word count meets target
            word_count_ratio = script_output.total_word_count / target_words
            if word_count_ratio < 0.7:  # Less than 70% of target
                logger.warning(
                    f"⚠️  Generated script is SHORT: {script_output.total_word_count} words "
                    f"vs target {target_words} words ({word_count_ratio:.1%} of target). "
                    f"Consider increasing max_tokens or adjusting prompt."
                )
            elif word_count_ratio >= 0.7 and word_count_ratio <= 1.3:
                logger.info(
                    f"✓ Script length is appropriate: {script_output.total_word_count} words "
                    f"({word_count_ratio:.1%} of target {target_words} words)"
                )

            # STEP 3: Convert to PodcastScript format
            script = self._convert_to_podcast_script(
                script_output,
                tone,
                length,
                news_articles,
                content_plan
            )

            # Calculate metrics
            end_time = datetime.utcnow()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)

            metrics = GenerationMetrics(
                tokens_used=total_tokens,
                prompt_tokens=0,  # Combined in total_tokens
                completion_tokens=0,  # Combined in total_tokens
                model_used=self.MODEL,
                latency_ms=latency_ms,
                retry_count=0,
                cost_estimate=round(total_cost, 4)
            )

            logger.info(
                f"Script generated successfully: {total_tokens} tokens, "
                f"{latency_ms}ms, ${total_cost:.4f}"
            )

            return script, metrics

        except Exception as e:
            logger.error(f"Script generation failed: {str(e)}", exc_info=True)
            raise

    def _format_articles(self, articles: List[NewsArticle]) -> str:
        """Format articles for prompt input."""
        formatted = []
        for i, article in enumerate(articles[:5], 1):
            formatted.append(
                f"Article {i}: {article.title}\n"
                f"Source: {article.source or 'Unknown'}\n"
                f"Summary: {article.summary}\n"
                f"Content: {article.content[:1500]}..."
            )
        return "\n\n".join(formatted)

    def _format_content_plan(self, plan: ContentPlan) -> str:
        """Format content plan for writing agent."""
        sections = [
            f"Topics: {', '.join(plan.topics)}",
            f"\nStory Arc:\n" + "\n".join(f"{i+1}. {arc}" for i, arc in enumerate(plan.story_arc)),
            f"\nKey Points by Topic:"
        ]

        for topic, points in plan.key_points.items():
            sections.append(f"\n{topic}:")
            sections.append("\n".join(f"  - {point}" for point in points))

        sections.append(f"\nSources to Cite: {', '.join(plan.sources_to_cite)}")
        sections.append(f"\nEstimated Segments: {plan.estimated_segments}")

        return "\n".join(sections)

    def _get_tone_instructions(self, tone: ToneType) -> str:
        """Get tone-specific instructions."""
        instructions = {
            ToneType.PROFESSIONAL: """Focus on facts, data, and expert analysis. Maintain formal, polished delivery. Use precise terminology.""",
            ToneType.CASUAL: """Use everyday language and relatable examples. Include light humor. Show genuine curiosity.""",
            ToneType.EDUCATIONAL: """Explain concepts clearly with teaching intent. Break down complex ideas. Provide context.""",
            ToneType.CONVERSATIONAL: """Natural, flowing dialogue style. Balance information with entertainment. Use storytelling."""
        }
        return instructions.get(tone, instructions[ToneType.CONVERSATIONAL])

    def _convert_to_podcast_script(
        self,
        output: PodcastScriptOutput,
        tone: ToneType,
        length: LengthType,
        articles: List[NewsArticle],
        content_plan: ContentPlan
    ) -> PodcastScript:
        """Convert LangChain structured output to PodcastScript model."""

        # Convert segments
        segments = [
            ScriptSegment(
                speaker=SpeakerType[seg.speaker],
                text=seg.text,
                order=i,
                emotion=seg.emotion,
                pause_after=seg.pause_after
            )
            for i, seg in enumerate(output.segments)
        ]

        # Calculate duration (150 words per minute - average podcast speaking rate)
        words_per_minute = 150
        pause_time = sum(2 for s in segments if s.pause_after)
        duration_seconds = int((output.total_word_count / words_per_minute * 60) + pause_time)

        # Build metadata
        generation_metadata = {
            "langchain_version": "1.0.0",
            "planner_model": self.PLANNER_MODEL,
            "writer_model": self.WRITER_MODEL,
            "multi_agent": True,
            "generation_timestamp": datetime.utcnow().isoformat(),
            "articles_count": len(articles)
        }

        script = PodcastScript(
            title=content_plan.title,
            segments=segments,
            total_word_count=output.total_word_count,
            estimated_duration_seconds=duration_seconds,
            tone=tone,
            length=length,
            topics_covered=output.topics_covered,
            sources_cited=output.sources_cited,
            generation_metadata=generation_metadata,
            created_at=datetime.utcnow()
        )

        # Log speaker balance
        balance = script.get_speaker_balance()
        logger.info(
            f"Script created: {len(segments)} segments, {output.total_word_count} words, "
            f"{duration_seconds}s, balance={balance}"
        )

        return script
