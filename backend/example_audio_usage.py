"""
Example usage of the ElevenLabs Audio Generation Service.

This script demonstrates how to use the audio service to generate
high-quality podcast audio from a script.
"""

import asyncio
from uuid import uuid4

from app.services.script_service import (
    ScriptGeneratorService,
    NewsArticle,
    SpeakerType,
    ScriptSegment,
    PodcastScript,
    ToneType,
    LengthType,
)
from app.services.audio_service import ElevenLabsAudioService
from app.schemas.audio import VoiceSettings


async def example_simple_usage():
    """
    Simple example: Generate audio from a pre-defined script.
    """
    print("=" * 80)
    print("EXAMPLE 1: Simple Audio Generation")
    print("=" * 80)

    # Create a simple script manually
    segments = [
        ScriptSegment(
            speaker=SpeakerType.ALEX,
            text="Welcome to today's podcast! We've got some exciting news to discuss.",
            order=0,
            emotion="enthusiastic",
            pause_after=False,
        ),
        ScriptSegment(
            speaker=SpeakerType.SONIA,
            text="Thanks, Alex! Yes, we're diving into the latest developments in AI technology.",
            order=1,
            emotion="professional",
            pause_after=True,  # Add a break after this
        ),
        ScriptSegment(
            speaker=SpeakerType.ALEX,
            text="Let's start with the breakthrough everyone's talking about...",
            order=2,
            emotion="curious",
            pause_after=False,
        ),
    ]

    script = PodcastScript(
        segments=segments,
        total_word_count=50,
        estimated_duration_seconds=30,
        tone=ToneType.CASUAL,
        length=LengthType.SHORT,
        topics_covered=["AI", "Technology"],
        sources_cited=["Example Source"],
        generation_metadata={"example": True},
    )

    # Generate audio
    podcast_id = str(uuid4())

    async with ElevenLabsAudioService() as audio_service:
        print(f"\nGenerating audio for podcast: {podcast_id}")
        print(f"Segments: {len(script.segments)}")

        response = await audio_service.generate_audio(
            script=script,
            podcast_id=podcast_id,
        )

        if response.success:
            print("\n✓ Audio generation successful!")
            print(f"  File: {response.audio_file.file_path}")
            print(f"  Duration: {response.audio_file.duration_seconds:.1f}s")
            print(f"  Size: {response.audio_file.file_size_bytes / 1024:.1f} KB")
            print(f"  Characters: {response.audio_file.metrics.total_characters}")
            print(f"  Cost: ${response.audio_file.metrics.cost_estimate:.4f}")
            print(f"  Latency: {response.audio_file.metrics.total_latency_ms}ms")
        else:
            print(f"\n✗ Audio generation failed: {response.error_message}")


async def example_with_custom_voices():
    """
    Advanced example: Generate audio with custom voice settings.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Custom Voice Settings")
    print("=" * 80)

    # Custom voice settings for each speaker
    custom_voices = {
        "ALEX": VoiceSettings(
            stability=0.6,  # More stable for professional tone
            similarity_boost=0.8,
            style=0.2,  # Slight style enhancement
            use_speaker_boost=True,
        ),
        "SONIA": VoiceSettings(
            stability=0.7,  # Very stable for analytical content
            similarity_boost=0.85,
            style=0.1,  # Minimal style
            use_speaker_boost=True,
        ),
    }

    # Create script with longer content
    segments = [
        ScriptSegment(
            speaker=SpeakerType.ALEX,
            text="In today's episode, we're exploring the fascinating intersection of artificial intelligence and healthcare.",
            order=0,
            pause_after=False,
        ),
        ScriptSegment(
            speaker=SpeakerType.SONIA,
            text="That's right. Recent studies show AI can now detect certain diseases with accuracy rivaling expert physicians.",
            order=1,
            pause_after=True,
        ),
        ScriptSegment(
            speaker=SpeakerType.ALEX,
            text="Incredible! Can you break down how this technology actually works?",
            order=2,
            pause_after=False,
        ),
        ScriptSegment(
            speaker=SpeakerType.SONIA,
            text="Of course. These systems use deep learning algorithms trained on millions of medical images and patient records.",
            order=3,
            pause_after=True,
        ),
    ]

    script = PodcastScript(
        segments=segments,
        total_word_count=100,
        estimated_duration_seconds=60,
        tone=ToneType.BALANCED,
        length=LengthType.MEDIUM,
        topics_covered=["AI", "Healthcare", "Technology"],
        sources_cited=["Medical Journal"],
    )

    podcast_id = str(uuid4())

    async with ElevenLabsAudioService() as audio_service:
        print(f"\nGenerating audio with custom voice settings...")
        print(f"Podcast ID: {podcast_id}")

        response = await audio_service.generate_audio(
            script=script,
            podcast_id=podcast_id,
            voice_settings=custom_voices,
        )

        if response.success:
            print("\n✓ Audio generation successful!")
            print(f"  File: {response.audio_file.file_path}")
            print(f"  Duration: {response.audio_file.duration_seconds:.1f}s")
            print(f"  API Calls: {response.audio_file.metrics.api_calls}")
            print(f"  Total Cost: ${response.audio_file.metrics.cost_estimate:.4f}")

            print("\n  Segment Breakdown:")
            for seg_metric in response.audio_file.metrics.segment_metrics:
                status = "✓" if seg_metric.success else "✗"
                print(
                    f"    {status} Segment {seg_metric.segment_index}: "
                    f"{seg_metric.speaker or 'BREAK'} - "
                    f"{seg_metric.character_count} chars, "
                    f"{seg_metric.latency_ms}ms"
                )
        else:
            print(f"\n✗ Failed: {response.error_message}")


async def example_full_pipeline():
    """
    Complete example: Generate script from news, then create audio.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Full Pipeline (Script → Audio)")
    print("=" * 80)

    # Sample news article
    article = NewsArticle(
        title="AI Breakthrough in Climate Modeling",
        summary="Scientists develop new AI system that dramatically improves weather predictions.",
        content="""
        Researchers at a leading university have developed an artificial intelligence
        system that can predict weather patterns with unprecedented accuracy. The system
        uses advanced machine learning techniques to analyze vast amounts of atmospheric
        data, improving forecast accuracy by 40% compared to traditional methods.

        The breakthrough could have significant implications for climate science,
        agriculture, and disaster preparedness. The team plans to make the model
        available to weather agencies worldwide.
        """,
        source="Science Daily",
        category="Technology",
    )

    # Generate script
    script_service = ScriptGeneratorService()
    print("\n1. Generating script from news article...")

    script, script_metrics = await script_service.generate_script(
        news_articles=[article],
        preferences={"tone": "balanced", "length": "short"},
    )

    print(f"   ✓ Script generated: {script.total_word_count} words")
    print(f"   ✓ Segments: {len(script.segments)}")
    print(f"   ✓ Script cost: ${script_metrics.cost_estimate:.4f}")

    # Generate audio
    podcast_id = str(uuid4())
    print(f"\n2. Generating audio for podcast: {podcast_id}...")

    async with ElevenLabsAudioService() as audio_service:
        response = await audio_service.generate_audio(
            script=script,
            podcast_id=podcast_id,
        )

        if response.success:
            print(f"   ✓ Audio generated successfully!")

            total_cost = script_metrics.cost_estimate + response.audio_file.metrics.cost_estimate
            print(f"\n3. Pipeline Summary:")
            print(f"   Script tokens: {script_metrics.tokens_used}")
            print(f"   Audio characters: {response.audio_file.metrics.total_characters}")
            print(f"   Total duration: {response.audio_file.duration_seconds:.1f}s")
            print(f"   Total cost: ${total_cost:.4f}")
            print(f"   Output file: {response.audio_file.file_path}")
        else:
            print(f"   ✗ Audio generation failed: {response.error_message}")


async def main():
    """Run all examples."""
    print("\n" + "🎙️  " * 20)
    print("ElevenLabs Audio Service Examples")
    print("🎙️  " * 20 + "\n")

    try:
        # Run examples
        await example_simple_usage()
        await example_with_custom_voices()
        await example_full_pipeline()

        print("\n" + "=" * 80)
        print("All examples completed!")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
