"""
Test script to verify all EU job scrapers are working
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scraping import ScraperManager, ScrapingConfig


async def test_eu_scrapers():
    """Test all EU visa-sponsorship scrapers"""

    print("=" * 80)
    print("Testing EU Visa-Sponsorship Job Scrapers")
    print("=" * 80)

    # Create scraper manager with all EU scrapers enabled
    config = ScrapingConfig(
        max_results_per_site=5,  # Small test
        max_concurrent_scrapers=2,
        enable_arbeitnow=True,
        enable_berlinstartupjobs=True,
        enable_relocateme=True,
        enable_eures=True,
        enable_indeed=False,  # Disable others for this test
        enable_adzuna=False,
        enable_themuse=False,
        enable_rapidapi_jsearch=False,
    )

    manager = ScraperManager(config)

    print(f"\n✅ Initialized {len(manager.get_available_scrapers())} scrapers")
    print(f"   Available: {manager.get_available_scrapers()}\n")

    # Test each scraper individually
    scrapers_to_test = {
        "arbeitnow": {
            "keywords": "Data Science",
            "location": "Germany",
        },
        "berlinstartupjobs": {
            "keywords": "AI",
            "location": "Berlin",
        },
        "relocateme": {
            "keywords": "Machine Learning",
            "location": "Europe",
        },
        "eures": {
            "keywords": "Data Scientist",
            "location": "DE",
        },
    }

    results = {}

    for scraper_name, search_params in scrapers_to_test.items():
        if scraper_name not in manager.scrapers:
            print(f"⚠️  {scraper_name}: Not initialized")
            continue

        print(f"\n{'=' * 80}")
        print(f"Testing: {scraper_name.upper()}")
        print(f"  Keywords: {search_params['keywords']}")
        print(f"  Location: {search_params['location']}")
        print(f"{'=' * 80}")

        try:
            scraper = manager.scrapers[scraper_name]

            async with scraper:
                jobs = await scraper.search_jobs(
                    keywords=search_params["keywords"],
                    location=search_params["location"],
                    max_results=5,
                )

                results[scraper_name] = {
                    "success": True,
                    "job_count": len(jobs),
                    "jobs": jobs,
                }

                print(f"\n✅ {scraper_name}: Found {len(jobs)} jobs")

                # Display first 2 jobs
                for i, job in enumerate(jobs[:2], 1):
                    print(f"\n  Job {i}:")
                    print(f"    Title: {job.title}")
                    print(f"    Company: {job.company}")
                    print(f"    Location: {job.location}")
                    print(f"    URL: {job.url[:60]}...")
                    print(f"    Visa Sponsor: {job.requires_visa_sponsorship}")

        except Exception as e:
            print(f"\n❌ {scraper_name}: ERROR - {e}")
            results[scraper_name] = {
                "success": False,
                "error": str(e),
            }

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")

    total_jobs = 0
    successful = 0
    failed = 0

    for scraper_name, result in results.items():
        if result.get("success"):
            successful += 1
            job_count = result.get("job_count", 0)
            total_jobs += job_count
            status = f"✅ {job_count} jobs"
        else:
            failed += 1
            status = f"❌ {result.get('error', 'Unknown error')}"

        print(f"{scraper_name:25s}: {status}")

    print(f"\n{'=' * 80}")
    print(f"Total Jobs Found: {total_jobs}")
    print(f"Successful Scrapers: {successful}/{len(scrapers_to_test)}")
    print(f"Failed Scrapers: {failed}/{len(scrapers_to_test)}")
    print(f"{'=' * 80}\n")

    return results


async def test_multi_site_search():
    """Test multi-site search with all EU scrapers"""

    print("\n" + "=" * 80)
    print("Testing Multi-Site Search (All EU Scrapers)")
    print("=" * 80)

    config = ScrapingConfig(
        max_results_per_site=10,
        max_concurrent_scrapers=2,
        enable_arbeitnow=True,
        enable_berlinstartupjobs=True,
        enable_relocateme=True,
        enable_eures=True,
        enable_indeed=False,
        enable_adzuna=False,
        enable_themuse=False,
        enable_rapidapi_jsearch=False,
        deduplication_enabled=True,
    )

    manager = ScraperManager(config)

    print("\nSearching for: 'Data Science' jobs in 'Europe'")
    print("Please wait...\n")

    jobs = await manager.search_all_sites(
        keywords="Data Science",
        location="Europe",
        max_total_results=50,
    )

    print("\n✅ Multi-site search completed!")
    print(f"   Total unique jobs: {len(jobs)}")

    # Group by source
    by_source = {}
    for job in jobs:
        source = job.source
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(job)

    print("\n   Jobs by source:")
    for source, source_jobs in by_source.items():
        print(f"     - {source}: {len(source_jobs)} jobs")

    # Show sample jobs with visa sponsorship
    visa_jobs = [j for j in jobs if j.requires_visa_sponsorship]
    print(f"\n   Jobs with visa sponsorship: {len(visa_jobs)}/{len(jobs)}")

    print(f"\n{'=' * 80}")
    print("Sample Jobs with Visa Sponsorship:")
    print(f"{'=' * 80}")

    for i, job in enumerate(visa_jobs[:5], 1):
        print(f"\n{i}. {job.title}")
        print(f"   Company: {job.company}")
        print(f"   Location: {job.location}")
        print(f"   Source: {job.source}")
        print(f"   URL: {job.url[:60]}...")

    return jobs


if __name__ == "__main__":
    print("\n🚀 Starting EU Job Scraper Tests...\n")

    # Run individual scraper tests
    results = asyncio.run(test_eu_scrapers())

    # Run multi-site search test
    jobs = asyncio.run(test_multi_site_search())

    print("\n✅ All tests completed!\n")
