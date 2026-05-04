"""
Integration Example: News Fetching + Script Generation

This example demonstrates the complete pipeline from fetching news articles
to generating a podcast script.

Usage:
    python backend/example_integration.py
"""

import asyncio
from datetime import datetime

# Import services
from app.services.news_service import FirecrawlNewsService, FetchedNewsArticle
from app.services.script_service import (
    ScriptGeneratorService,
    NewsArticle,
    ToneType,
    LengthType,
)


async def convert_news_to_script_articles(
    news_articles: list[FetchedNewsArticle]
) -> list[NewsArticle]:
    """
    Convert FetchedNewsArticle (from news service) to NewsArticle (for script service).

    Args:
        news_articles: List of fetched news articles

    Returns:
        List of NewsArticle objects ready for script generation
    """
    script_articles = []

    for article in news_articles:
        # Convert the Firecrawl article to the format expected by script service
        script_article = NewsArticle(
            title=article.title,
            summary=article.summary or article.content[:200] + "...",
            content=article.content,
            source=article.source,
            url=str(article.url),
            published_at=article.published_date,
            category=article.topics[0] if article.topics else "General"
        )
        script_articles.append(script_article)

    return script_articles


async def full_pipeline_example():
    """
    Complete example: Fetch news → Generate script → Display results
    """
    print("\n" + "="*80)
    print("FULL PIPELINE EXAMPLE: News Fetching + Script Generation")
    print("="*80 + "\n")

    # Step 1: Fetch News Articles
    print("📰 Step 1: Fetching news articles...")
    print("-" * 80)

    news_service = FirecrawlNewsService()

    # Define user preferences
    user_interests = {
        "topics": ["technology", "artificial intelligence", "climate"],
        "sources": ["techcrunch.com", "wired.com", "theverge.com"],
        "max_age_days": 7
    }

    try:
        # Fetch articles (this would normally use actual Firecrawl API)
        # For demo purposes, we'll create sample articles
        print(f"  Searching for: {', '.join(user_interests['topics'])}")
        print(f"  Max age: {user_interests['max_age_days']} days")

        # In production, you would call:
        # news_articles, news_metrics = await news_service.fetch_news(
        #     query=" OR ".join(user_interests['topics']),
        #     preferences=user_interests
        # )

        # For this example, create sample articles
        sample_news = [
            FetchedNewsArticle(
                title="AI Breakthrough: New Model Achieves Human-Level Reasoning",
                content="""
                Researchers at Stanford University have announced a significant breakthrough
                in artificial intelligence. Their new model, called "ReasonNet," demonstrates
                reasoning capabilities that match or exceed human performance on complex
                logical tasks.

                The model uses a novel architecture that combines symbolic reasoning with
                neural networks, allowing it to handle abstract concepts and multi-step
                logical deduction. In benchmark tests, ReasonNet scored 95% on advanced
                reasoning tasks, compared to 89% for the previous state-of-the-art model.

                Dr. Emily Chen, lead researcher on the project, explains: "What makes
                ReasonNet special is its ability to explain its reasoning process. It doesn't
                just give you an answer; it shows you how it arrived at that conclusion,
                step by step."

                The breakthrough has significant implications for fields ranging from
                scientific research to legal analysis. However, researchers caution that
                the technology is still in early stages and requires careful ethical
                consideration before widespread deployment.

                Industry experts predict this could accelerate the development of more
                trustworthy and interpretable AI systems, addressing one of the key
                concerns about current AI technology.
                """,
                summary="Stanford researchers develop AI model with human-level reasoning capabilities and explainable logic.",
                source="TechCrunch",
                author="Sarah Johnson",
                published_date=datetime(2026, 5, 3, 10, 30),
                url="https://techcrunch.example.com/ai-reasoning-breakthrough",
                relevance_score=0.95,
                topics=["Artificial Intelligence", "Technology", "Research"],
                word_count=0  # Will be calculated by validator
            ),
            FetchedNewsArticle(
                title="Major Climate Action: EU Announces €200B Green Energy Plan",
                content="""
                The European Union has unveiled an ambitious €200 billion green energy
                plan aimed at achieving carbon neutrality by 2035. The comprehensive
                package includes investments in renewable energy infrastructure, electric
                vehicle charging networks, and sustainable technology research.

                EU Commission President Maria Schmidt announced the plan during a press
                conference in Brussels, calling it "the most significant climate action
                in European history." The initiative will be funded through a combination
                of member state contributions, EU bonds, and private sector partnerships.

                Key components of the plan include:
                - €80 billion for wind and solar energy expansion
                - €50 billion for electric vehicle infrastructure
                - €40 billion for green hydrogen development
                - €30 billion for climate research and innovation

                Environmental groups have cautiously welcomed the announcement while
                emphasizing the importance of implementation. Greenpeace EU director
                claimed: "This is a step in the right direction, but the real test will
                be whether these commitments translate into concrete action."

                The plan also includes provisions for "just transition" support to help
                workers and communities dependent on fossil fuel industries adapt to the
                green economy. Critics argue the timeline may be too aggressive, while
                climate activists say it doesn't go far enough.
                """,
                summary="EU commits €200B to green energy infrastructure in ambitious climate neutrality plan.",
                source="The Guardian",
                author="Marco Rossi",
                published_date=datetime(2026, 5, 2, 14, 15),
                url="https://theguardian.example.com/eu-green-energy-plan",
                relevance_score=0.88,
                topics=["Climate", "Environment", "Policy"],
                word_count=0
            ),
            FetchedNewsArticle(
                title="Tech Giants Face New AI Regulation Proposals",
                content="""
                Lawmakers in the United States and Europe are proposing new regulations
                for artificial intelligence systems, focusing on transparency, accountability,
                and consumer protection. The proposed legislation could significantly
                impact how tech companies develop and deploy AI products.

                The US proposal, introduced by Senator Jane Martinez, includes requirements
                for AI systems to disclose when users are interacting with AI, mandatory
                impact assessments for high-risk applications, and substantial penalties
                for violations. Similar legislation is being considered by the European
                Parliament.

                Tech industry representatives have expressed concerns about the potential
                impact on innovation. A spokesperson for the Technology Industry Association
                stated: "While we support responsible AI development, overly restrictive
                regulations could hamper American competitiveness in this critical field."

                Consumer advocacy groups, however, argue that regulation is overdue.
                "AI systems are already making decisions that affect people's lives—from
                loan applications to job hiring to healthcare. People have a right to
                understand and challenge these decisions," says consumer rights advocate
                David Park.

                The proposals include provisions for algorithmic audits, data protection
                requirements, and restrictions on certain high-risk AI applications such
                as facial recognition in public spaces. If passed, the legislation would
                take effect in 2027, giving companies a transition period to comply.
                """,
                summary="US and EU lawmakers propose comprehensive AI regulations focusing on transparency and accountability.",
                source="Wired",
                author="Alex Chen",
                published_date=datetime(2026, 5, 1, 9, 45),
                url="https://wired.example.com/ai-regulation-proposals",
                relevance_score=0.92,
                topics=["Technology", "Policy", "Artificial Intelligence"],
                word_count=0
            )
        ]

        print(f"\n✓ Fetched {len(sample_news)} articles")
        for i, article in enumerate(sample_news, 1):
            print(f"  {i}. {article.title}")
            print(f"     Source: {article.source} | Score: {article.relevance_score}")

    except Exception as e:
        print(f"✗ Error fetching news: {str(e)}")
        return

    # Step 2: Convert Articles
    print("\n🔄 Step 2: Converting articles for script generation...")
    print("-" * 80)

    script_articles = await convert_news_to_script_articles(sample_news)
    print(f"✓ Converted {len(script_articles)} articles")

    # Step 3: Generate Podcast Script
    print("\n🎙️  Step 3: Generating podcast script...")
    print("-" * 80)

    script_service = ScriptGeneratorService()

    try:
        # Generate script with balanced tone, medium length
        script, metrics = await script_service.generate_script(
            news_articles=script_articles,
            preferences={
                "tone": "balanced",
                "length": "medium"
            }
        )

        print(f"✓ Script generated successfully!")
        print(f"\n📊 Script Details:")
        print(f"  - Word count: {script.total_word_count}")
        print(f"  - Segments: {len(script.segments)}")
        print(f"  - Duration: {script.estimated_duration_seconds // 60}m {script.estimated_duration_seconds % 60}s")
        print(f"  - Tone: {script.tone.value}")
        print(f"  - Topics: {', '.join(script.topics_covered)}")

        balance = script.get_speaker_balance()
        print(f"\n🎭 Speaker Balance:")
        print(f"  - Alex: {balance['alex_percentage']}%")
        print(f"  - Sonia: {balance['sonia_percentage']}%")

        print(f"\n💰 Generation Metrics:")
        print(f"  - Tokens used: {metrics.tokens_used}")
        print(f"  - Latency: {metrics.latency_ms}ms")
        print(f"  - Cost: ${metrics.cost_estimate}")
        print(f"  - Retries: {metrics.retry_count}")

        # Step 4: Display Script Preview
        print("\n📝 Script Preview (first 3 segments):")
        print("-" * 80)
        for i, segment in enumerate(script.segments[:3]):
            emotion = f" ({segment.emotion})" if segment.emotion else ""
            print(f"\n[{segment.speaker.value}]{emotion}:")
            print(f"  {segment.text}")
            if segment.pause_after:
                print("  [BREAK]")

        # Step 5: Save Results (simulation)
        print("\n💾 Step 5: Saving to database (simulation)...")
        print("-" * 80)

        # In production, you would save to database:
        # from app.models import Podcast, Metrics
        # podcast = Podcast(...)
        # metrics_record = Metrics(...)

        print("✓ Script saved to database")
        print("✓ Metrics recorded")

        print("\n" + "="*80)
        print("✅ PIPELINE COMPLETED SUCCESSFULLY!")
        print("="*80)

        return script, metrics

    except Exception as e:
        print(f"✗ Error generating script: {str(e)}")
        import traceback
        traceback.print_exc()


async def quick_example():
    """
    Quick example with minimal setup.
    """
    print("\n" + "="*80)
    print("QUICK EXAMPLE: Generate Script from Sample Article")
    print("="*80 + "\n")

    # Create a single sample article
    article = NewsArticle(
        title="Revolutionary Solar Panel Technology Doubles Efficiency",
        summary="New breakthrough in solar panel design achieves 47% efficiency, potentially transforming renewable energy.",
        content="""
        Scientists at the National Renewable Energy Laboratory have achieved a major
        breakthrough in solar panel technology. Their new design achieves 47% efficiency
        in converting sunlight to electricity, more than double the efficiency of
        current commercial panels.

        The breakthrough uses a multi-layer approach that captures different wavelengths
        of light more effectively. Traditional solar panels waste a lot of energy because
        they're only optimized for certain wavelengths. The new design uses specialized
        layers that each target different parts of the light spectrum.

        Dr. Robert Kim, lead researcher, explains: "Think of it like having multiple
        filters that each capture what the others miss. Together, they capture nearly
        half of the sun's energy that hits them."

        While the technology is promising, commercial production is still several years
        away. The manufacturing process is complex and expensive, but researchers are
        confident they can scale it up cost-effectively.
        """,
        source="Science Daily",
        url="https://sciencedaily.example.com/solar-breakthrough",
        published_at=datetime(2026, 5, 4, 8, 0),
        category="Technology"
    )

    # Generate script quickly
    from app.services.script_service import generate_podcast_script

    script, metrics = await generate_podcast_script(
        articles=[article],
        tone="casual",
        length="short"
    )

    print(f"✓ Generated {script.total_word_count}-word script in {metrics.latency_ms}ms")
    print(f"💰 Cost: ${metrics.cost_estimate}")
    print(f"\n📝 Full Script:\n")
    print(script.get_full_text())


async def main():
    """Run examples."""
    print("\n" + "="*80)
    print("🎙️  PODCAST GENERATION SERVICE - INTEGRATION EXAMPLES")
    print("="*80)

    # Choose which example to run
    print("\nAvailable examples:")
    print("1. Full Pipeline (News Fetching + Script Generation)")
    print("2. Quick Example (Single Article)")
    print("3. Both")

    # For automated demo, run both
    choice = "3"

    if choice in ["1", "3"]:
        try:
            await full_pipeline_example()
        except Exception as e:
            print(f"\n✗ Full pipeline error: {str(e)}")

    if choice in ["2", "3"]:
        print("\n" + "="*80)
        try:
            await quick_example()
        except Exception as e:
            print(f"\n✗ Quick example error: {str(e)}")

    print("\n" + "="*80)
    print("Examples completed!")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Note: You need a valid OPENAI_API_KEY in your .env file to run this
    asyncio.run(main())
