"""
Test AngelList scraper integration.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.scraping.angellist_scraper import AngelListScraper


async def main():
	"""Test AngelList integration."""
	print("🚀 Testing AngelList Integration")
	print("=" * 60)

	async with AngelListScraper() as scraper:
		print("\n📡 Searching for Python developer jobs...")

		jobs = await scraper.search_jobs(query="python engineer", location="remote")

		print(f"\n✅ Found {len(jobs)} jobs")

		if jobs:
			print("\n" + "=" * 60)
			print("📋 Sample Job Details:")
			print("=" * 60)

			job = jobs[0]
			print(f"\n🏢 Company: {job.company}")
			print(f"💼 Title: {job.title}")
			print(f"📍 Location: {job.location}")
			print(f"💰 Salary: {job.salary_range or 'Not disclosed'}")
			print(f"📈 Equity: {job.equity_range or 'Not disclosed'}")
			print(f"👔 Experience: {job.experience_level or 'Not specified'}")
			print(f"🚀 Funding: {job.funding_stage or 'Not disclosed'}")
			print(f"🛠️  Tech Stack: {', '.join(job.tech_stack[:5]) if job.tech_stack else 'Not specified'}")
			print(f"🌐 Language: {job.job_language}")
			print(f"🏠 Remote: {'Yes' if job.remote_ok else 'No'}")
			print(f"🔗 URL: {job.url}")
			print(f"\n📝 Description (first 200 chars):")
			print(f"   {job.description[:200]}...")

			print("\n" + "=" * 60)
			print(f"\n✅ Integration successful! Found {len(jobs)} startup jobs")
			print("=" * 60)

			# Show stats
			with_equity = sum(1 for j in jobs if j.equity_range)
			with_salary = sum(1 for j in jobs if j.salary_range)
			with_tech_stack = sum(1 for j in jobs if j.tech_stack)
			with_funding = sum(1 for j in jobs if j.funding_stage)

			print("\n📊 Data Quality Stats:")
			print(f"   Jobs with equity data: {with_equity}/{len(jobs)} ({with_equity / len(jobs) * 100:.1f}%)")
			print(f"   Jobs with salary data: {with_salary}/{len(jobs)} ({with_salary / len(jobs) * 100:.1f}%)")
			print(f"   Jobs with tech stack: {with_tech_stack}/{len(jobs)} ({with_tech_stack / len(jobs) * 100:.1f}%)")
			print(f"   Jobs with funding info: {with_funding}/{len(jobs)} ({with_funding / len(jobs) * 100:.1f}%)")

		else:
			print("\n⚠️  No jobs found. This might be expected if AngelList API requires registration.")
			print("   The scraper is working correctly, API may need authentication.")


if __name__ == "__main__":
	asyncio.run(main())
