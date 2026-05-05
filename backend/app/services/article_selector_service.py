import logging
from typing import List, Dict, Any
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class ArticleSelectorService:
    """
    Service for selecting the most relevant articles using AI.
    Uses OpenAI GPT-4o-mini to analyze and select articles based on user preferences.
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"

    async def select_articles(
        self,
        candidates: List[Dict[str, Any]],
        interests: List[str],
        tone: str,
        length: str
    ) -> List[str]:
        """
        Select the 5 most relevant articles from candidates based on user preferences.

        Args:
            candidates: List of article dicts with title, description, url, source, date
            interests: List of user interests
            tone: Desired tone (professional/casual/educational/conversational)
            length: Desired length preference

        Returns:
            List of 5 selected article URLs
        """
        try:
            if not candidates:
                logger.warning("No candidate articles provided")
                return []

            if len(candidates) <= 5:
                logger.info(f"Only {len(candidates)} candidates, returning all")
                return [article["url"] for article in candidates]

            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(candidates, interests, tone, length)

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
            )

            result = response.choices[0].message.content
            import json
            parsed_result = json.loads(result)
            selected_urls = parsed_result.get("selected_urls", [])

            if len(selected_urls) != 5:
                logger.warning(f"Expected 5 URLs but got {len(selected_urls)}")
                selected_urls = selected_urls[:5] if len(selected_urls) > 5 else selected_urls

            logger.info(f"Successfully selected {len(selected_urls)} articles")
            return selected_urls

        except Exception as e:
            logger.error(f"Error selecting articles: {str(e)}")
            return [article["url"] for article in candidates[:5]]

    def _build_system_prompt(self) -> str:
        return """You are an expert content curator for a personalized podcast service.

Your task is to select exactly 5 articles from a list of candidates that will create the best podcast experience for the user.

Selection criteria (in priority order):
1. Relevance to user interests - Choose articles that closely match the user's stated interests
2. Source credibility - Prioritize reputable news sources and publications
3. Diversity - Ensure variety in topics, perspectives, and angles to create engaging content
4. Tone match - Select articles that align with the user's preferred tone
5. Recency - Prefer more recent articles when other factors are equal

Important guidelines:
- You MUST select exactly 5 articles
- Prioritize quality over quantity - choose the most impactful and relevant content
- Avoid redundant articles covering the same story
- Consider how the articles will flow together in a podcast format
- Balance depth with breadth across the user's interests

Return your selection as a JSON object with this exact format:
{
  "selected_urls": ["url1", "url2", "url3", "url4", "url5"]
}

Only include the URLs, nothing else in the array."""

    def _build_user_prompt(
        self,
        candidates: List[Dict[str, Any]],
        interests: List[str],
        tone: str,
        length: str
    ) -> str:
        articles_text = "\n\n".join([
            f"URL: {article['url']}\n"
            f"Title: {article['title']}\n"
            f"Source: {article['source']}\n"
            f"Date: {article['date']}\n"
            f"Description: {article['description']}"
            for article in candidates
        ])

        interests_text = ", ".join(interests) if interests else "general news"

        return f"""User Preferences:
- Interests: {interests_text}
- Preferred tone: {tone}
- Preferred length: {length}

Available Articles ({len(candidates)} total):

{articles_text}

Please select exactly 5 articles that would create the best personalized podcast for this user."""
