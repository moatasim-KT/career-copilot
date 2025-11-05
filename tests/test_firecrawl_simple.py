"""
Simple Firecrawl test - one company only
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scraping.firecrawl_scraper import FirecrawlScraper


async def test_single_company():
    """Test Firecrawl with just one company"""

    api_key = os.getenv("FIRECRAWL_API_KEY", "fc-6fb4bec6ff1b49a1ac8fccd5243d714d")
    print(f"Using API key: {api_key[:10]}...{api_key[-4:]}\n")

    async with FirecrawlScraper(api_key=api_key) as scraper:
        print("✅ Scraper initialized\n")

        # Test EU companies with international hiring track record
        print("=" * 80)
        print("Testing: Spotify (Stockholm/Amsterdam)")
        print("URL: https://www.lifeatspotify.com/jobs")
        print("Known for: Visa sponsorship, international talent")
        print("=" * 80)

        jobs = await scraper.search_jobs(
            keywords="Data Science Machine Learning",
            location="Europe",
            max_results=10,
            companies=["spotify"],  # Test Spotify - strong international hiring
        )

        print(f"\n✅ Found {len(jobs)} jobs from Spotify\n")

        for i, job in enumerate(jobs[:5], 1):
            print(f"  Job {i}:")
            print(f"    Title: {job.title}")
            print(f"    Company: {job.company}")
            print(f"    Location: {job.location}")
            print(f"    Type: {job.job_type}")
            print(f"    Remote: {job.remote_option}")
            print(
                f"    Visa Sponsorship: {getattr(job, 'requires_visa_sponsorship', 'Unknown')}"
            )
            if job.application_url:
                print(f"    URL: {job.application_url[:60]}...")
            print()

        return jobs


if __name__ == "__main__":
    print("🚀 Starting Simple Firecrawl Test...\n")
    jobs = asyncio.run(test_single_company())
    print(f"✅ Test completed! Found {len(jobs)} total jobs")
