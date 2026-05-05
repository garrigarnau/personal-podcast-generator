"""
Test script for generating audio from a pre-written script.

This script demonstrates how to use the /generate-from-script endpoint
to bypass news fetching and script generation, going directly to audio generation.
"""

import asyncio
import httpx


# Sample script provided by user
SAMPLE_SCRIPT = """[ALEX] (enthusiastic): Welcome back to our tech insights podcast! Today, we're diving into some truly intriguing developments in the world of artificial intelligence. Sonia, have you seen the latest headlines on AI advancements?

[SONIA] (thoughtful): Absolutely, Alex. There's quite a bit to unpack. Let's start with the news from China regarding Nvidia's B300 servers. Due to heightened demand and stringent US curbs on chip exports, these servers are now priced at a staggering one million dollars each.

[ALEX] (amazed): Wow, that's incredible! The demand for such advanced AI computing equipment is clearly soaring. What does this tell us about the current landscape of AI technology in China?

[SONIA]: Well, it underscores China's relentless pursuit of cutting-edge technology despite international trade restrictions. This situation highlights not just economic implications but also geopolitical ones as countries vie for technological dominance.

[BREAK]

[ALEX]: Speaking of technological advancements, did you catch the Wall Street Journal's report on Anthropic's new AI agents? They're specifically designed for financial services firms. What impact do you think this could have on that industry?

[SONIA]: It's a significant development, Alex. These AI agents are engineered to handle complex data analytics and decision-making processes within financial institutions. They promise to increase efficiency and accuracy in operations like trading, risk assessment, and customer service.

[ALEX] (intrigued): It sounds like a game-changer for financial services. But do you think there are any potential risks or challenges associated with implementing such advanced AI systems?

[SONIA] (analytical): Absolutely, there are challenges. Integrating these systems requires robust cybersecurity measures to protect sensitive data and ensure compliance with regulatory standards. Moreover, there's the ongoing concern about AI transparency and the need for human oversight in decision-making processes.

[BREAK]

[ALEX]: Transitioning from financial services to startups, Forbes recently published their 2026 AI 50 List highlighting top companies reshaping industries with AI innovations. What's your take on these emerging players?

[SONIA] (insightful): The list showcases how rapidly startups are transforming ambitious ideas into viable businesses across various sectors including law, software engineering, and even music. This reflects a broader trend where venture capital is heavily investing in AI as a cornerstone of future growth.

[ALEX]: That's fascinating! It seems like we're witnessing a new era where AI isn't just an add-on but an integral part of business strategies.

[SONIA]: Precisely. The adoption curve for AI is steepening as companies realize its potential to drive innovation and competitive advantage.

[BREAK]

[ALEX]: Finally, let's touch on privacy concerns highlighted by Tech Funding News. With companies utilizing cookies and tracking technologies extensively, what does this mean for consumer privacy?

[SONIA] (concerned): It's a critical issue that needs addressing as AI technologies evolve. Consumers must be informed about data collection practices and have control over their personal information. Transparency should be at the forefront of how businesses leverage data-driven tools.

[ALEX]: Agreed! It's clear that while AI offers remarkable opportunities, it also necessitates responsible handling of ethical considerations.

[SONIA]: Indeed, Alex. Balancing technological progress with ethical responsibility is essential as we continue to integrate AI into daily life.

[CLOSING]

[ALEX] (optimistic): What an enlightening discussion today! We've covered everything from skyrocketing server prices in China to innovative startups leading the charge in AI applications.

[SONIA]: Absolutely! As always, it's about staying informed and critically examining how these trends shape our future.

[ALEX]: Thanks for tuning in everyone! Join us next time as we continue exploring how technology transforms our world.

[END]"""


async def test_script_to_audio():
    """Test the script-to-audio endpoint."""

    # API configuration
    base_url = "http://localhost:8000"

    # Get auth token (you need to login first or use an existing token)
    # For demo purposes, you'd need to authenticate first
    token = "YOUR_AUTH_TOKEN_HERE"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Request payload
    payload = {
        "script_text": SAMPLE_SCRIPT,
        "tone": "professional",
        "length": "medium",
        "mock_audio": False  # Set to True to skip actual ElevenLabs calls
    }

    async with httpx.AsyncClient() as client:
        # Generate audio from script
        print("🎙️  Sending script to audio generation endpoint...")
        response = await client.post(
            f"{base_url}/api/v1/podcasts/generate-from-script",
            json=payload,
            headers=headers,
            timeout=30.0
        )

        if response.status_code == 202:
            result = response.json()
            podcast_id = result["id"]
            print(f"✅ Audio generation started! Podcast ID: {podcast_id}")
            print(f"   Status: {result['status']}")

            # Poll for completion
            print("\n⏳ Polling for completion...")
            while True:
                await asyncio.sleep(3)

                status_response = await client.get(
                    f"{base_url}/api/v1/podcasts/{podcast_id}/status",
                    headers=headers
                )

                status_data = status_response.json()
                print(f"   Status: {status_data['status']} (Progress: {status_data.get('progress', 0)}%)")

                if status_data["status"] in ["completed", "failed"]:
                    break

            # Final result
            if status_data["status"] == "completed":
                print(f"\n🎉 Audio generation completed!")
                print(f"   Audio URL: {status_data.get('audio_url')}")
            else:
                print(f"\n❌ Audio generation failed!")
                print(f"   Error: {status_data.get('error_message')}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   {response.text}")


if __name__ == "__main__":
    print("=" * 70)
    print("Script-to-Audio Test")
    print("=" * 70)
    print("\nThis test demonstrates generating audio directly from a script,")
    print("bypassing news fetching and script generation.\n")

    asyncio.run(test_script_to_audio())
