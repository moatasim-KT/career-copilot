"""
Quick test of AngelList integration - no database required.
"""

import asyncio

from app.services.scraping.angellist_scraper import AngelListScraper


async def main():
	print("🚀 Testing AngelList Scraper (Quick Test)")
	print("=" * 60)

	scraper = AngelListScraper()

	print("\n📡 Searching for jobs...")

	# Note: AngelList public API may have limitations
	# This demonstrates the scraper is working
	jobs = await scraper.search_jobs(query="software engineer", location="")

	print(f"\n✅ Scraper executed successfully")
	print(f"Found: {len(jobs)} jobs")

	if jobs:
		job = jobs[0]
		print(f"\n📋 Sample Job:")
		print(f"   Title: {job.title}")
		print(f"   Company: {job.company}")
		print(f"   Location: {job.location}")
		print(f"   Equity: {job.equity_range or 'N/A'}")
		print(f"   Tech Stack: {', '.join(job.tech_stack[:3]) if job.tech_stack else 'N/A'}")

	await scraper.close()
	print("\n✅ Integration test complete!")


if __name__ == "__main__":
	asyncio.run(main())
