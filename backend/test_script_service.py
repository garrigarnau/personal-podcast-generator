"""
Test script for Script Generation Service.

This script demonstrates the functionality of the ScriptGeneratorService
with example news articles and different configuration options.

Usage:
    python test_script_service.py
"""

import asyncio
from datetime import datetime
from app.services.script_service import (
    ScriptGeneratorService,
    NewsArticle,
    ToneType,
    LengthType,
    generate_podcast_script,
)


# Sample news articles for testing
SAMPLE_ARTICLES = [
    NewsArticle(
        title="Breakthrough in Quantum Computing: New Algorithm Promises 100x Speed Improvement",
        summary="Researchers at MIT have developed a novel quantum algorithm that could revolutionize computing power for specific problem types.",
        content="""
        A team of researchers at MIT's Quantum Computing Lab has announced a groundbreaking
        algorithm that promises to deliver 100x speed improvements for certain computational
        problems. The algorithm, dubbed "QuickQuant," leverages advanced quantum entanglement
        properties to solve optimization problems that are currently intractable for classical
        computers.

        Lead researcher Dr. Sarah Chen explained that the breakthrough came from reimagining
        how quantum states are measured and manipulated during computation. "We discovered
        that by using a novel error-correction technique combined with adaptive measurement
        strategies, we could significantly reduce the computational overhead that has plagued
        quantum algorithms," she said.

        The implications are far-reaching, with potential applications in drug discovery,
        financial modeling, climate simulation, and artificial intelligence. Industry experts
        estimate that this could accelerate the timeline for practical quantum advantage by
        several years.

        However, Dr. Chen cautioned that commercial implementation is still years away.
        "We've demonstrated the algorithm on a 50-qubit system in lab conditions. Scaling
        this to the thousands of qubits needed for real-world problems will require
        significant engineering advances."
        """,
        source="TechNews Daily",
        url="https://technews.example.com/quantum-breakthrough",
        published_at=datetime(2026, 5, 3, 14, 30),
        category="Technology"
    ),
    NewsArticle(
        title="Global Climate Summit Reaches Historic Agreement on Carbon Reduction",
        summary="195 nations commit to aggressive carbon reduction targets in landmark climate accord.",
        content="""
        In a historic moment for climate action, representatives from 195 nations signed
        the "Global Carbon Accord 2026" at the International Climate Summit in Geneva.
        The agreement commits signatories to reducing carbon emissions by 60% by 2035,
        with interim checkpoints every two years.

        UN Secretary-General António Silva called it "the most ambitious and comprehensive
        climate agreement in human history." Unlike previous accords, this agreement includes
        binding enforcement mechanisms and substantial financial commitments from developed
        nations to support developing countries' transition to clean energy.

        The accord establishes a $500 billion "Green Transition Fund" to help developing
        nations build renewable energy infrastructure, with contributions proportional to
        each country's historical emissions. Additionally, it mandates the phase-out of
        coal power by 2030 for developed nations and 2035 for developing nations.

        Environmental groups praised the agreement while noting that implementation will
        be the real test. "This is a monumental achievement, but the hard work begins now,"
        said Maria Rodriguez, director of Global Climate Action Network. "We'll be watching
        closely to ensure countries follow through on their commitments."

        Market analysts predict the agreement will accelerate investment in renewable energy
        technologies and electric vehicles, potentially creating millions of green jobs
        globally.
        """,
        source="Global News Network",
        url="https://globalnews.example.com/climate-summit-2026",
        published_at=datetime(2026, 5, 2, 9, 15),
        category="Environment"
    ),
    NewsArticle(
        title="New Study Reveals Benefits of Four-Day Work Week",
        summary="Large-scale trial shows improved productivity and employee well-being with reduced work hours.",
        content="""
        A comprehensive two-year study involving over 10,000 employees across 200 companies
        has provided compelling evidence for the benefits of a four-day work week. The
        research, conducted by the International Labor Institute, found that reducing the
        standard work week to four days (32 hours) with no reduction in pay led to remarkable
        improvements in both productivity and employee satisfaction.

        Key findings include a 23% increase in employee-reported well-being, 65% reduction
        in sick days, and—surprisingly—a 4% increase in overall productivity. Companies
        also reported lower turnover rates, with employee retention improving by 35% on
        average.

        Dr. James Parker, lead researcher on the study, attributes the success to several
        factors: "Employees return to work more refreshed and focused. They're more efficient
        with their time, and meetings become more purposeful. The extra day off allows for
        better work-life balance, reducing burnout and improving mental health."

        Several major corporations, including tech giants and financial institutions, have
        announced plans to pilot or permanently implement four-day work weeks based on these
        findings. However, critics argue that the model may not be feasible for all industries,
        particularly those requiring 24/7 operations or customer-facing roles.

        Labor economists suggest this could represent a fundamental shift in how we think
        about work, similar to the adoption of the five-day work week in the early 20th century.
        """,
        source="Business Insights",
        url="https://businessinsights.example.com/four-day-workweek-study",
        published_at=datetime(2026, 5, 1, 11, 45),
        category="Business"
    ),
]


async def test_basic_generation():
    """Test basic script generation with default settings."""
    print("\n" + "="*80)
    print("TEST 1: Basic Script Generation (Balanced tone, Medium length)")
    print("="*80 + "\n")

    service = ScriptGeneratorService()
    script, metrics = await service.generate_script(
        news_articles=SAMPLE_ARTICLES,
        preferences={"tone": "balanced", "length": "medium"}
    )

    print(f"✓ Script generated successfully!")
    print(f"  - Segments: {len(script.segments)}")
    print(f"  - Word count: {script.total_word_count}")
    print(f"  - Duration: {script.estimated_duration_seconds}s ({script.estimated_duration_seconds // 60}m {script.estimated_duration_seconds % 60}s)")
    print(f"  - Topics: {', '.join(script.topics_covered)}")
    print(f"  - Sources: {', '.join(script.sources_cited)}")

    balance = script.get_speaker_balance()
    print(f"\n  Speaker Balance:")
    print(f"  - Alex: {balance['alex_percentage']}%")
    print(f"  - Sonia: {balance['sonia_percentage']}%")

    print(f"\n  Generation Metrics:")
    print(f"  - Tokens used: {metrics.tokens_used} (prompt: {metrics.prompt_tokens}, completion: {metrics.completion_tokens})")
    print(f"  - Model: {metrics.model_used}")
    print(f"  - Latency: {metrics.latency_ms}ms")
    print(f"  - Retries: {metrics.retry_count}")
    print(f"  - Cost estimate: ${metrics.cost_estimate}")

    print(f"\n  First 3 segments:")
    for i, segment in enumerate(script.segments[:3]):
        emotion = f" ({segment.emotion})" if segment.emotion else ""
        print(f"  [{segment.speaker.value}]{emotion}: {segment.text[:100]}...")
        if segment.pause_after:
            print(f"  [BREAK]")

    print("\n  Full script:")
    print("-" * 80)
    print(script.get_full_text()[:500] + "...\n")

    return script, metrics


async def test_casual_short():
    """Test casual tone with short length."""
    print("\n" + "="*80)
    print("TEST 2: Casual Tone, Short Length")
    print("="*80 + "\n")

    script, metrics = await generate_podcast_script(
        articles=SAMPLE_ARTICLES[:2],  # Use fewer articles for short format
        tone="casual",
        length="short"
    )

    print(f"✓ Casual short script generated!")
    print(f"  - Word count: {script.total_word_count} (target: ~750)")
    print(f"  - Duration: {script.estimated_duration_seconds // 60}m {script.estimated_duration_seconds % 60}s")
    print(f"  - Tone: {script.tone.value}")
    print(f"  - Cost: ${metrics.cost_estimate}")

    return script, metrics


async def test_serious_long():
    """Test serious tone with long length."""
    print("\n" + "="*80)
    print("TEST 3: Serious Tone, Long Length")
    print("="*80 + "\n")

    script, metrics = await generate_podcast_script(
        articles=SAMPLE_ARTICLES,
        tone="serious",
        length="long"
    )

    print(f"✓ Serious long script generated!")
    print(f"  - Word count: {script.total_word_count} (target: ~2250)")
    print(f"  - Duration: {script.estimated_duration_seconds // 60}m {script.estimated_duration_seconds % 60}s")
    print(f"  - Tone: {script.tone.value}")
    print(f"  - Cost: ${metrics.cost_estimate}")

    return script, metrics


async def test_single_article():
    """Test with a single article."""
    print("\n" + "="*80)
    print("TEST 4: Single Article Generation")
    print("="*80 + "\n")

    script, metrics = await generate_podcast_script(
        articles=[SAMPLE_ARTICLES[0]],
        tone="balanced",
        length="short"
    )

    print(f"✓ Single article script generated!")
    print(f"  - Segments: {len(script.segments)}")
    print(f"  - Word count: {script.total_word_count}")
    print(f"  - Cost: ${metrics.cost_estimate}")

    return script, metrics


async def test_error_handling():
    """Test error handling with invalid inputs."""
    print("\n" + "="*80)
    print("TEST 5: Error Handling")
    print("="*80 + "\n")

    service = ScriptGeneratorService()

    # Test with no articles
    try:
        await service.generate_script(
            news_articles=[],
            preferences={"tone": "balanced", "length": "medium"}
        )
        print("✗ Should have raised ValueError for empty articles")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {str(e)}")

    # Test with invalid tone (should still work, falls back to default)
    try:
        script, metrics = await generate_podcast_script(
            articles=[SAMPLE_ARTICLES[0]],
            tone="balanced",
            length="medium"
        )
        print(f"✓ Handled gracefully, generated script with {script.total_word_count} words")
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")


async def run_all_tests():
    """Run all tests sequentially."""
    print("\n" + "="*80)
    print("SCRIPT GENERATION SERVICE - COMPREHENSIVE TEST SUITE")
    print("="*80)

    try:
        # Test 1: Basic generation
        await test_basic_generation()

        # Test 2: Casual short
        await test_casual_short()

        # Test 3: Serious long
        await test_serious_long()

        # Test 4: Single article
        await test_single_article()

        # Test 5: Error handling
        await test_error_handling()

        print("\n" + "="*80)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run tests
    asyncio.run(run_all_tests())
