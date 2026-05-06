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
        Select the most relevant articles from candidates based on user preferences.
        The AI determines the optimal number of articles to comprehensively cover all user interests.

        Args:
            candidates: List of article dicts with title, description, url, source, date
            interests: List of user interests
            tone: Desired tone (professional/casual/educational/conversational)
            length: Desired length preference

        Returns:
            List of selected article URLs (variable count based on AI decision)
        """
        try:
            if not candidates:
                logger.warning("No candidate articles provided")
                return []

            system_prompt = self._build_system_prompt(interests)
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

            if not selected_urls:
                logger.warning("No URLs selected by AI, falling back to all candidates")
                selected_urls = [article["url"] for article in candidates]

            logger.info(f"Successfully selected {len(selected_urls)} articles")
            return selected_urls

        except Exception as e:
            logger.error(f"Error selecting articles: {str(e)}")
            return [article["url"] for article in candidates]

    def _build_system_prompt(self, interests: List[str]) -> str:
        interests_text = ", ".join(interests) if interests else "general news"
        return f"""You are an expert content curator for a personalized podcast service.

Your task is to select AS MANY articles as needed to comprehensively cover ALL user interests from the list of candidates. The goal is to create the best, most complete podcast experience for the user.

Selection criteria (in priority order):
1. Comprehensive coverage - Ensure at least one article per interest: {interests_text}
2. Relevance to user interests - Choose articles that closely match the user's stated interests
3. Source credibility - Prioritize reputable news sources and publications
4. Diversity - Ensure variety in topics, perspectives, and angles to create engaging content
5. Tone match - Select articles that align with the user's preferred tone
6. Recency - Prefer more recent articles when other factors are equal

Important guidelines:
- Select AS MANY articles as needed to comprehensively cover ALL user interests
- Prioritize diversity and relevance over quantity
- Ensure at least one article per user interest when possible
- Avoid redundant articles covering the same story
- Consider how the articles will flow together in a podcast format
- Balance depth with breadth across the user's interests
- It's acceptable to select fewer articles if candidates are limited or redundant
- It's acceptable to select more articles if needed for comprehensive coverage

Return your selection as a JSON object with this exact format:
{{
  "selected_urls": ["url1", "url2", "url3", ...]
}}

Only include the URLs, nothing else in the array. The number of URLs is flexible based on comprehensive coverage needs."""

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

Please select AS MANY articles as needed to comprehensively cover all of the user's interests. Ensure diverse, relevant coverage rather than limiting to an arbitrary number."""
