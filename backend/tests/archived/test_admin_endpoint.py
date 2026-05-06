#!/usr/bin/env python3
"""
Test script for the admin stats endpoint.
Verifies data structure and displays formatted results.
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any


# Configuration
API_BASE_URL = "http://localhost:8000"
ADMIN_STATS_ENDPOINT = f"{API_BASE_URL}/api/v1/admin/stats"


def print_separator(title: str = "") -> None:
    """Print a formatted separator line."""
    if title:
        print(f"\n{'='*80}")
        print(f"  {title}")
        print('='*80)
    else:
        print('-'*80)


def format_cost(cost: float) -> str:
    """Format cost as USD."""
    return f"${cost:.2f}"


def format_latency(ms: float) -> str:
    """Format latency from milliseconds."""
    seconds = ms / 1000
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    return f"{minutes}m {remaining_seconds:.0f}s"


def test_admin_endpoint(days: int = 30) -> None:
    """
    Test the admin stats endpoint and display results.

    Args:
        days: Number of days to query (default: 30)
    """
    print_separator("ADMIN STATS ENDPOINT TEST")
    print(f"Endpoint: {ADMIN_STATS_ENDPOINT}")
    print(f"Days: {days}")

    try:
        # Make request
        print("\n📡 Making request...")
        response = requests.get(
            ADMIN_STATS_ENDPOINT,
            params={"days": days},
            timeout=10
        )

        # Check status code
        print(f"Status Code: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return

        # Parse JSON
        data = response.json()

        # Display KPIs
        print_separator("📊 KPI SUMMARY")
        kpis = data.get("kpis", {})

        print(f"Total Podcasts:           {kpis.get('total_podcasts', 0):,}")
        print(f"Average Latency:          {format_latency(kpis.get('avg_latency_ms', 0))}")
        print(f"Total Cost:               {format_cost(kpis.get('total_cost_usd', 0))}")
        print(f"Success Rate:             {kpis.get('success_rate', 0):.1f}%")
        print(f"Total Tokens:             {kpis.get('total_tokens', 0):,}")
        print(f"Total Characters:         {kpis.get('total_characters', 0):,}")
        print(f"Firecrawl Searches:       {kpis.get('total_firecrawl_searches', 0):,}")
        print(f"Firecrawl Scrapes:        {kpis.get('total_firecrawl_scrapes', 0):,}")
        print(f"Firecrawl Cost:           {format_cost(kpis.get('total_firecrawl_cost', 0))}")

        # Cost breakdown
        print_separator("💰 COST BREAKDOWN")
        cost_breakdown = kpis.get('cost_breakdown', {})
        print(f"OpenAI:                   {format_cost(cost_breakdown.get('openai', 0))}")
        print(f"ElevenLabs:               {format_cost(cost_breakdown.get('elevenlabs', 0))}")
        print(f"Firecrawl:                {format_cost(cost_breakdown.get('firecrawl', 0))}")
        total = sum(cost_breakdown.values())
        print(f"TOTAL:                    {format_cost(total)}")

        # Volume data
        print_separator("📈 DAILY VOLUME DATA")
        volume_data = data.get("volume_data", [])
        print(f"Days with data: {len(volume_data)}")

        if volume_data:
            print("\nLast 5 days:")
            print(f"{'Date':<12} {'Total':>7} {'Completed':>10} {'Failed':>7} {'Pending':>8} {'Avg Latency':>12} {'Cost':>10}")
            print_separator()

            for day in volume_data[:5]:
                date = day.get('date', 'N/A')
                total = day.get('total', 0)
                completed = day.get('completed', 0)
                failed = day.get('failed', 0)
                pending = day.get('pending', 0)
                avg_latency = format_latency(day.get('avg_latency_ms', 0))
                cost = format_cost(day.get('total_cost_usd', 0))

                print(f"{date:<12} {total:>7} {completed:>10} {failed:>7} {pending:>8} {avg_latency:>12} {cost:>10}")

        # Recent podcasts
        print_separator("🎙️  RECENT PODCASTS")
        recent_podcasts = data.get("recent_podcasts", [])
        print(f"Recent podcasts: {len(recent_podcasts)}")

        if recent_podcasts:
            print("\nLast 5 podcasts:")
            print(f"{'ID':<10} {'Status':<12} {'Latency':>10} {'Cost':>8} {'Tokens':>8} {'Chars':>8} {'FC Search':>10} {'FC Scrape':>10}")
            print_separator()

            for podcast in recent_podcasts[:5]:
                pod_id = str(podcast.get('id', 'N/A'))[:8]
                status = podcast.get('status', 'N/A')
                latency = format_latency(podcast.get('latency_ms', 0)) if podcast.get('latency_ms') else 'N/A'
                cost = format_cost(podcast.get('cost_usd', 0)) if podcast.get('cost_usd') else 'N/A'
                tokens = f"{podcast.get('tokens_used', 0):,}" if podcast.get('tokens_used') else 'N/A'
                chars = f"{podcast.get('elevenlabs_characters', 0):,}" if podcast.get('elevenlabs_characters') else 'N/A'
                fc_search = podcast.get('firecrawl_searches') if podcast.get('firecrawl_searches') is not None else 'N/A'
                fc_scrape = podcast.get('firecrawl_scrapes') if podcast.get('firecrawl_scrapes') is not None else 'N/A'

                print(f"{pod_id:<10} {status:<12} {latency:>10} {cost:>8} {tokens:>8} {chars:>8} {fc_search:>10} {fc_scrape:>10}")

                if podcast.get('error_message'):
                    print(f"  ⚠️  Error: {podcast['error_message']}")

        # Metadata
        print_separator("ℹ️  METADATA")
        generated_at = data.get("generated_at", "N/A")
        print(f"Generated at: {generated_at}")

        # Status counts
        print_separator("📊 STATUS SUMMARY")
        if recent_podcasts:
            status_counts = {}
            for podcast in recent_podcasts:
                status = podcast.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1

            for status, count in sorted(status_counts.items()):
                print(f"{status.capitalize():<15} {count:>5}")

        # Data validation
        print_separator("✅ DATA VALIDATION")
        validations = []

        # Check required fields
        if "kpis" in data:
            validations.append("✓ KPIs present")
        else:
            validations.append("✗ KPIs missing")

        if "volume_data" in data:
            validations.append("✓ Volume data present")
        else:
            validations.append("✗ Volume data missing")

        if "recent_podcasts" in data:
            validations.append("✓ Recent podcasts present")
        else:
            validations.append("✗ Recent podcasts missing")

        # Check data consistency
        if kpis.get('total_podcasts', 0) >= len(recent_podcasts):
            validations.append("✓ Podcast count consistency")
        else:
            validations.append("✗ Podcast count mismatch")

        # Check cost calculation
        calculated_cost = sum(cost_breakdown.values())
        reported_cost = kpis.get('total_cost_usd', 0)
        if abs(calculated_cost - reported_cost) < 0.01:
            validations.append("✓ Cost breakdown matches total")
        else:
            validations.append(f"⚠️  Cost mismatch: {format_cost(calculated_cost)} vs {format_cost(reported_cost)}")

        for validation in validations:
            print(validation)

        print_separator("✨ TEST COMPLETED SUCCESSFULLY")

        # Save raw JSON for inspection
        print("\n💾 Saving raw JSON to 'admin_stats_response.json'...")
        with open('admin_stats_response.json', 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print("✓ Saved")

    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection Error: Could not connect to {API_BASE_URL}")
        print("   Make sure the backend server is running on port 8000")
    except requests.exceptions.Timeout:
        print("\n❌ Timeout Error: Request took too long")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request Error: {e}")
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON Decode Error: {e}")
        print(f"Response text: {response.text}")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()


def test_health_endpoint() -> bool:
    """Test if the API is reachable."""
    print_separator("🏥 HEALTH CHECK")
    health_url = f"{API_BASE_URL}/health"
    print(f"Endpoint: {health_url}")

    try:
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            print("✓ API is healthy and reachable")
            return True
        else:
            print(f"⚠️  API returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ API is not reachable: {e}")
        return False


if __name__ == "__main__":
    import sys

    # Parse command line arguments
    days = 30
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print(f"Invalid days argument: {sys.argv[1]}")
            print("Usage: python test_admin_endpoint.py [days]")
            sys.exit(1)

    # Run tests
    print("\n🚀 Starting Admin Endpoint Tests\n")

    # First check health
    if test_health_endpoint():
        # Then test admin endpoint
        test_admin_endpoint(days)
    else:
        print("\n⚠️  Skipping admin endpoint test - API not reachable")
        print("\nTo start the backend server:")
        print("  cd backend")
        print("  uvicorn app.main:app --reload")
