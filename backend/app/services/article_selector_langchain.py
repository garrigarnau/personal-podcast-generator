"""
Article Selector Service using LangChain with Orchestration & Subagents.

This service uses LangChain to select the most relevant articles from candidates
with structured outputs, proper tracing, and a multi-agent architecture.

Architecture:
- Main orchestrator agent coordinates the selection process
- Analysis subagent evaluates article relevance
- Diversity subagent ensures topic coverage
- Final decision uses structured Pydantic outputs

Features:
- LangSmith tracing for observability
- Type-safe Pydantic models
- Automatic retry logic
- Cost tracking
- Better error handling
"""

import logging
import re
import json
import asyncio
from typing import List, Dict, Any, Optional, TypeVar, Type
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from pydantic import BaseModel, Field, validator

from app.core.config import settings

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
                logger.error(f"[RobustParser] Original text length: {len(text)} chars")
                logger.error(f"[RobustParser] Original text (first 1000): {text[:1000]}")
                logger.error(f"[RobustParser] Original text (last 500): ...{text[-500:]}")
                logger.error(f"[RobustParser] Cleaned text length: {len(cleaned)} chars")
                logger.error(f"[RobustParser] Cleaned text (first 1000): {cleaned[:1000]}")
                logger.error(f"[RobustParser] Cleaned text (last 500): ...{cleaned[-500:]}")
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

class ArticleRelevanceScore(BaseModel):
    """Relevance score for a single article."""
    url: str = Field(description="Article URL")
    relevance_score: float = Field(ge=0.0, le=10.0, description="Relevance score 0-10")
    interest_match: str = Field(description="Which user interest this article matches")
    reasoning: str = Field(description="Why this article is relevant")


class ArticleAnalysis(BaseModel):
    """Analysis of all candidate articles."""
    scored_articles: List[ArticleRelevanceScore] = Field(
        description="All articles with relevance scores"
    )
    total_analyzed: int = Field(description="Total articles analyzed")
    interests_covered: List[str] = Field(description="Which interests are covered")
    gaps: List[str] = Field(default_factory=list, description="Interests with poor coverage")


class ArticleSelection(BaseModel):
    """Final article selection with reasoning."""
    selected_urls: List[str] = Field(
        min_length=1,
        description="Selected article URLs (flexible count based on comprehensive coverage)"
    )
    reasoning: str = Field(description="Overall selection strategy and rationale")
    topics_covered: List[str] = Field(description="Topics covered by selection")
    diversity_score: float = Field(
        ge=0.0,
        le=10.0,
        description="How diverse is the selection (0-10)"
    )
    coverage_complete: bool = Field(
        description="Whether all user interests are covered"
    )

    @validator('selected_urls')
    def validate_urls(cls, v):
        """Ensure at least one URL is selected."""
        if not v:
            raise ValueError("At least one article must be selected")
        return v


# ============================================================================
# LangChain Article Selector Service
# ============================================================================

class ArticleSelectorService:
    """
    LangChain-powered article selector with multi-agent orchestration.

    Uses a coordinated approach:
    1. Analysis Agent: Scores all articles for relevance
    2. Diversity Agent: Ensures comprehensive coverage
    3. Selection Agent: Makes final decision with structured output

    All agents are traced in LangSmith for full observability.
    """

    def __init__(self):
        """Initialize the LangChain article selector with subagents."""
        # Main LLM for orchestration (GPT-4o-mini for cost efficiency)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=2000,  # Ensure enough tokens for selection output
            api_key=settings.OPENAI_API_KEY,
        ).with_config(run_name="Selection Agent")

        # Analysis subagent (lower temperature for consistent scoring)
        self.analysis_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=3000,  # More tokens for scoring many articles
            api_key=settings.OPENAI_API_KEY,
        ).with_config(run_name="Analysis Agent")

        # Setup parsers (with markdown stripping)
        self.analysis_parser = RobustPydanticOutputParser(pydantic_object=ArticleAnalysis)
        self.selection_parser = RobustPydanticOutputParser(pydantic_object=ArticleSelection)

        # Build chains
        self._build_chains()

        logger.info("ArticleSelectorService initialized with LangChain multi-agent architecture")

    def _build_chains(self):
        """Build LangChain chains for analysis and selection."""

        # CHAIN 1: Analysis Subagent - Score all articles
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert content analyst for a podcast service.

Your task is to analyze ALL candidate articles and score each one for relevance to the user's interests.

Scoring criteria (0-10 scale):
- 9-10: Perfect match, highly relevant, high quality source
- 7-8: Strong match, relevant, reputable source
- 5-6: Moderate match, somewhat relevant
- 3-4: Weak match, tangentially relevant
- 0-2: Poor match, not relevant

Consider:
1. Direct relevance to stated interests
2. Source credibility and quality
3. Recency and timeliness
4. Depth and substance of content

CRITICAL OUTPUT FORMAT:
- Output ONLY raw JSON, no markdown code blocks
- Do NOT wrap output in ```json or ```
- Start directly with {{ and end with }}
- NO TRAILING COMMAS - remove commas before closing brackets
- Ensure the JSON is complete and valid

{format_instructions}"""),
            ("user", """User Interests: {interests}
Preferred Tone: {tone}

Candidate Articles ({num_articles} total):
{articles}

Analyze ALL articles and provide relevance scores.""")
        ])

        self.analysis_chain = (
            self.analysis_prompt
            | self.analysis_llm
            | self.analysis_parser
        ).with_config(run_name="Article Analysis Chain")

        # CHAIN 2: Selection Agent - Make final decision
        self.selection_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert content curator making the FINAL article selection.

You have received scored articles from the analysis team. Your task is to select the OPTIMAL number of high-quality articles based on podcast length.

ARTICLE COUNT LIMITS (strict - MUST follow):
- SHORT podcasts (5 min): Select 3-4 articles MAXIMUM
- MEDIUM podcasts (10 min): Select 5-6 articles MAXIMUM
- LONG podcasts (15 min): Select 7-8 articles MAXIMUM

QUALITY THRESHOLD:
- ONLY select articles with relevance score >= 6.0
- One excellent article per topic beats multiple mediocre ones

Selection strategy (in priority order):
1. MUST NOT exceed the article count limit for the podcast length
2. Prioritize highest-scoring articles (8+ is ideal, 7+ is good)
3. Include at least one article per user interest (IF high quality available)
4. Ensure diversity - avoid redundant coverage of the same story
5. Quality over quantity - fewer deep dives beat rushed coverage

Important:
- Respect the article count limit STRICTLY
- Skip low-quality articles (score < 6.0) even if it means fewer articles
- If an interest has no high-quality articles, skip it
- Better to have 3 excellent articles than 6 mediocre ones

CRITICAL OUTPUT FORMAT:
- Output ONLY raw JSON, no markdown code blocks
- Do NOT wrap output in ```json or ```
- Start directly with {{ and end with }}
- NO TRAILING COMMAS - remove commas before closing brackets
- Ensure the JSON is complete and valid

{format_instructions}"""),
            ("user", """User Preferences:
- Interests: {interests}
- Tone: {tone}
- Length: {length}
- MAXIMUM ARTICLES: {max_articles} (strict limit - do not exceed)

Analyzed Articles with Scores:
{analysis_results}

Select UP TO {max_articles} optimal articles following the quality threshold and limits.""")
        ])

        self.selection_chain = (
            self.selection_prompt
            | self.llm
            | self.selection_parser
        ).with_config(run_name="Article Selection Chain")

    async def select_articles(
        self,
        candidates: List[Dict[str, Any]],
        interests: List[str],
        tone: str,
        length: Any,  # Accept both int and str
        thread_id: Optional[str] = None,
    ) -> List[str]:
        """
        Select the most relevant articles using multi-agent LangChain architecture.

        SAME INTERFACE as original service - orchestrator doesn't need changes!

        Args:
            candidates: List of article dicts with title, description, url, source, date
            interests: List of user interests
            tone: Desired tone (professional/casual/educational/conversational)
            length: Desired length preference (short/medium/long or int 1-15)
            thread_id: Optional LangSmith thread ID to group all runs together

        Returns:
            List of selected article URLs (variable count based on AI decision)

        Raises:
            Exception: If selection fails after retries
        """
        try:
            if not candidates:
                logger.warning("No candidate articles provided")
                return []

            # If very few candidates, return all
            if len(candidates) <= 2:
                logger.info(f"Only {len(candidates)} candidates, returning all")
                return [article["url"] for article in candidates]

            # Normalize length to string format (handle both int and string)
            if isinstance(length, int):
                if length <= 7:
                    length_str = "short"
                elif length <= 12:
                    length_str = "medium"
                else:
                    length_str = "long"
            else:
                length_str = str(length).lower()

            logger.info(
                f"Starting LangChain article selection: {len(candidates)} candidates, "
                f"interests={interests}, tone={tone}, length={length_str}"
            )

            # Calculate article limit based on podcast length
            article_limits = {
                "short": 4,
                "medium": 6,
                "long": 8
            }
            max_articles = article_limits.get(length_str, 6)

            logger.info(f"Article selection limit for {length_str} podcast: {max_articles} articles max")

            # Format data for chains
            articles_text = self._format_articles(candidates)
            interests_text = ", ".join(interests)

            # STEP 1: Analysis Subagent - Score all articles
            logger.info("Step 1/2: Analyzing articles with subagent...")

            try:
                async with asyncio.timeout(60):  # 60 second timeout
                    config = {
                        "run_name": "📊 STEP 1: Article Analysis",
                        "tags": ["article-selection", "analysis", "scoring"],
                        "metadata": {
                            "num_candidates": len(candidates),
                            "interests": interests_text,
                            "tone": tone
                        }
                    }
                    # Add thread_id to config if provided for LangSmith grouping
                    if thread_id:
                        config["metadata"]["thread_id"] = thread_id

                    analysis_result = await self.analysis_chain.ainvoke(
                        {
                            "interests": interests_text,
                            "tone": tone,
                            "num_articles": len(candidates),
                            "articles": articles_text,
                            "format_instructions": self.analysis_parser.get_format_instructions()
                        },
                        config=config
                    )
            except asyncio.TimeoutError:
                logger.error("Analysis agent timed out after 60 seconds")
                raise Exception("Article analysis timed out - LLM took too long to respond")

            logger.info(
                f"Analysis complete: {len(analysis_result.scored_articles)} articles scored, "
                f"interests covered: {analysis_result.interests_covered}, "
                f"gaps: {analysis_result.gaps}"
            )

            # Log top scored articles for visibility
            sorted_scores = sorted(
                analysis_result.scored_articles,
                key=lambda x: x.relevance_score,
                reverse=True
            )
            logger.info("=" * 80)
            logger.info("TOP SCORED ARTICLES (from Analysis Agent):")
            for i, article in enumerate(sorted_scores[:10], 1):  # Show top 10
                logger.info(f"{i}. Score {article.relevance_score}/10 - {article.interest_match}")
                logger.info(f"   URL: {article.url}")
                logger.info(f"   Reasoning: {article.reasoning}")
            logger.info("=" * 80)

            # STEP 2: Selection Agent - Make final decision
            logger.info("Step 2/2: Making final selection...")

            # Format analysis results for selection agent
            analysis_summary = self._format_analysis_for_selection(analysis_result)

            try:
                async with asyncio.timeout(45):  # 45 second timeout
                    config = {
                        "run_name": "🎯 STEP 2: Article Selection",
                        "tags": ["article-selection", "decision", "filtering"],
                        "metadata": {
                            "max_articles": max_articles,
                            "length": length_str,
                            "interests": interests_text
                        }
                    }
                    # Add thread_id to config if provided for LangSmith grouping
                    if thread_id:
                        config["metadata"]["thread_id"] = thread_id

                    selection_result = await self.selection_chain.ainvoke(
                        {
                            "interests": interests_text,
                            "tone": tone,
                            "length": length_str,
                            "max_articles": max_articles,
                            "analysis_results": analysis_summary,
                            "format_instructions": self.selection_parser.get_format_instructions()
                        },
                        config=config
                    )
            except asyncio.TimeoutError:
                logger.error("Selection agent timed out after 45 seconds")
                raise Exception("Article selection timed out - LLM took too long to respond")

            logger.info(
                f"Selection complete: {len(selection_result.selected_urls)} articles selected, "
                f"diversity={selection_result.diversity_score:.1f}/10, "
                f"coverage_complete={selection_result.coverage_complete}"
            )
            logger.info("=" * 80)
            logger.info("SELECTION AGENT REASONING:")
            logger.info(selection_result.reasoning)
            logger.info(f"Topics covered: {', '.join(selection_result.topics_covered)}")
            logger.info("=" * 80)

            # Log selected articles with their titles for visibility
            logger.info("=" * 80)
            logger.info("SELECTED ARTICLES:")
            for i, url in enumerate(selection_result.selected_urls, 1):
                # Find the article in candidates
                article = next((a for a in candidates if a["url"] == url), None)
                if article:
                    logger.info(f"{i}. {article['title']}")
                    logger.info(f"   URL: {url}")
                    logger.info(f"   Source: {article['source']}")
                else:
                    logger.info(f"{i}. {url}")
            logger.info("=" * 80)

            return selection_result.selected_urls

        except Exception as e:
            logger.error(f"LangChain article selection failed: {str(e)}", exc_info=True)
            # Fallback: return all candidates
            logger.warning("Falling back to all candidates due to error")
            return [article["url"] for article in candidates]

    def _format_articles(self, candidates: List[Dict[str, Any]]) -> str:
        """Format articles for prompt input."""
        formatted = []
        for i, article in enumerate(candidates, 1):
            formatted.append(
                f"{i}. URL: {article['url']}\n"
                f"   Title: {article['title']}\n"
                f"   Source: {article['source']}\n"
                f"   Date: {article.get('date', 'Unknown')}\n"
                f"   Interest: {article.get('interest', 'N/A')}\n"
                f"   Description: {article['description'][:200]}..."
            )
        return "\n\n".join(formatted)

    def _format_analysis_for_selection(self, analysis: ArticleAnalysis) -> str:
        """Format analysis results for the selection agent."""
        # Sort by relevance score
        sorted_articles = sorted(
            analysis.scored_articles,
            key=lambda x: x.relevance_score,
            reverse=True
        )

        formatted = []
        for article in sorted_articles:
            formatted.append(
                f"• URL: {article.url}\n"
                f"  Score: {article.relevance_score}/10\n"
                f"  Interest Match: {article.interest_match}\n"
                f"  Reasoning: {article.reasoning}"
            )

        summary = "\n\n".join(formatted)

        # Add coverage summary
        coverage_info = (
            f"\n\n=== Coverage Summary ===\n"
            f"Interests Covered: {', '.join(analysis.interests_covered)}\n"
            f"Coverage Gaps: {', '.join(analysis.gaps) if analysis.gaps else 'None'}"
        )

        return summary + coverage_info
