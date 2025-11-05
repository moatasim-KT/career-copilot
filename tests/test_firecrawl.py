"""
Test Firecrawl scraper with actual API key
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scraping.firecrawl_scraper import FirecrawlScraper


async def test_firecrawl():
    """Test Firecrawl scraper with real API"""

    print("=" * 80)
    print("Testing Firecrawl Scraper")
    print("=" * 80)

    # Get API key from environment
    api_key = os.getenv("FIRECRAWL_API_KEY", "fc-e0560gb8d98a445ea925dc3abbe06ec1")
    print(f"Using API key: {api_key[:10]}...{api_key[-4:]}")

    # Test company career pages
    test_companies = [
        {
            "name": "Google",
            "url": "https://careers.google.com/jobs/results/?q=Data%20Scientist",
            "keywords": "Data Scientist",
        },
        {
            "name": "Anthropic",
            "url": "https://www.anthropic.com/careers",
            "keywords": "AI",
        },
    ]

    try:
        async with FirecrawlScraper(api_key=api_key) as scraper:
            print("\n✅ Firecrawl scraper initialized")
            print(f"   API Key: {scraper.api_key[:10]}...{scraper.api_key[-4:]}")

            # Test one company
            company = test_companies[0]
            print(f"\n{'=' * 80}")
            print(f"Testing: {company['name']}")
            print(f"URL: {company['url']}")
            print(f"{'=' * 80}")

            jobs = await scraper.search_jobs(
                keywords=company["keywords"], location="Europe", max_results=10
            )

            print(f"\n✅ Found {len(jobs)} jobs from {company['name']}")

            # Display jobs
            for i, job in enumerate(jobs[:3], 1):
                print(f"\n  Job {i}:")
                print(f"    Title: {job.title}")
                print(f"    Company: {job.company}")
                print(f"    Location: {job.location}")
                print(f"    URL: {job.url[:70]}...")
                print(f"    Source: {job.source}")
                print(f"    Visa: {job.requires_visa_sponsorship}")

            return jobs

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return []


if __name__ == "__main__":
    print("\n🚀 Starting Firecrawl Test...\n")
    jobs = asyncio.run(test_firecrawl())
    print(f"\n✅ Test completed! Found {len(jobs)} total jobs\n")
