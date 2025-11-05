"""
Test EU Scrapers - Optimized for International Talent with Visa Sponsorship
Tests all scrapers with focus on EU countries and companies known for hiring international talent
"""

import asyncio
import logging
from typing import List

from app.services.scraping.adzuna_scraper import AdzunaScraper
from app.services.scraping.arbeitnow_scraper import ArbeitnowScraper
from app.services.scraping.firecrawl_scraper import FirecrawlScraper
from app.services.scraping.rapidapi_jsearch_scraper import RapidAPIJSearchScraper
from app.services.scraping.themuse_scraper import TheMuseScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_arbeitnow_visa():
	"""Test Arbeitnow with visa sponsorship filter"""
	print("\n" + "=" * 80)
	print("🇩🇪 ARBEITNOW - Germany Jobs with Visa Sponsorship")
	print("=" * 80)

	try:
		async with ArbeitnowScraper() as scraper:
			# Test 1: Data Science in Berlin
			print("\n📊 Test 1: Data Science jobs in Berlin")
			jobs = await scraper.search_jobs(keywords="Data Scientist", location="Berlin", max_results=5, visa_sponsorship=True)
			print(f"✅ Found {len(jobs)} jobs")
			for i, job in enumerate(jobs[:3], 1):
				print(f"\n{i}. {job.title}")
				print(f"   Company: {job.company}")
				print(f"   Location: {job.location}")

			# Test 2: Software Engineer in Munich
			print("\n\n💻 Test 2: Software Engineer jobs in Munich")
			jobs = await scraper.search_jobs(keywords="Software Engineer", location="Munich", max_results=5, visa_sponsorship=True)
			print(f"✅ Found {len(jobs)} jobs")
			for i, job in enumerate(jobs[:3], 1):
				print(f"\n{i}. {job.title}")
				print(f"   Company: {job.company}")
				print(f"   Location: {job.location}")

	except Exception as e:
		print(f"❌ Error: {e}")


async def test_adzuna_eu():
	"""Test Adzuna across multiple EU countries"""
	print("\n" + "=" * 80)
	print("🇪🇺 ADZUNA - Multi-Country EU Search")
	print("=" * 80)

	try:
		scraper = AdzunaScraper()

		# Test EU countries known for tech jobs and visa sponsorship
		eu_locations = [
			("Berlin, Germany", "de"),
			("Amsterdam, Netherlands", "nl"),
			("Stockholm, Sweden", "se"),
			("Dublin, Ireland", "ie"),
		]

		for location, country in eu_locations:
			print(f"\n📍 Testing: {location}")
			jobs = await scraper.search_jobs(keywords="Python Developer", location=location, max_results=3)
			print(f"✅ Found {len(jobs)} jobs in {location}")
			if jobs:
				job = jobs[0]
				print(f"   Sample: {job.title} @ {job.company}")

	except Exception as e:
		print(f"❌ Error: {e}")


async def test_themuse_eu():
	"""Test The Muse with EU location filters"""
	print("\n" + "=" * 80)
	print("🎨 THE MUSE - EU Tech Hubs")
	print("=" * 80)

	try:
		scraper = TheMuseScraper()

		# Test major EU tech hubs
		print("\n📊 Searching across EU tech hubs...")
		jobs = await scraper.search_jobs(
			keywords="Data Scientist",
			location="",  # Will search multiple EU locations
			max_results=10,
		)

		print(f"✅ Found {len(jobs)} jobs across EU")

		# Group by location
		locations = {}
		for job in jobs:
			loc = job.location or "Unknown"
			if loc not in locations:
				locations[loc] = []
			locations[loc].append(job)

		print(f"\n📍 Jobs by location:")
		for loc, loc_jobs in sorted(locations.items(), key=lambda x: len(x[1]), reverse=True):
			print(f"   {loc}: {len(loc_jobs)} jobs")
			if loc_jobs:
				print(f"      Example: {loc_jobs[0].title} @ {loc_jobs[0].company}")

	except Exception as e:
		print(f"❌ Error: {e}")


async def test_rapidapi_jsearch_eu():
	"""Test RapidAPI JSearch with optimized EU queries"""
	print("\n" + "=" * 80)
	print("🔍 RAPIDAPI JSEARCH - EU Job Aggregator")
	print("=" * 80)

	try:
		scraper = RapidAPIJSearchScraper()

		# Test optimized queries for EU
		test_queries = [
			("Data Scientist", "Berlin, Germany"),
			("Software Engineer", "Amsterdam, Netherlands"),
			("ML Engineer", "Stockholm, Sweden"),
		]

		for keywords, location in test_queries:
			print(f"\n📍 Query: {keywords} in {location}")
			jobs = await scraper.search_jobs(keywords=keywords, location=location, max_results=3)
			print(f"✅ Found {len(jobs)} jobs")
			if jobs:
				for i, job in enumerate(jobs[:2], 1):
					print(f"\n{i}. {job.title}")
					print(f"   Company: {job.company}")
					print(f"   Location: {job.location}")

	except Exception as e:
		print(f"❌ Error: {e}")


async def test_firecrawl_visa_sponsors():
	"""Test Firecrawl with companies known for visa sponsorship"""
	print("\n" + "=" * 80)
	print("🔥 FIRECRAWL - EU Companies with Visa Sponsorship")
	print("=" * 80)

	try:
		scraper = FirecrawlScraper()

		# Test a few top visa sponsor companies
		test_companies = [
			"spotify",
			"adyen",
			"n26",
			"revolut",
		]

		print(f"\n📋 Testing {len(test_companies)} companies known for visa sponsorship...")
		print("   Companies: Spotify, Adyen, N26, Revolut")

		jobs = await scraper.search_jobs(keywords="Data Science", location="EU", max_results=10, companies=test_companies)

		print(f"\n✅ Found {len(jobs)} jobs from visa sponsor companies")

		if jobs:
			# Group by company
			companies = {}
			for job in jobs:
				comp = job.company or "Unknown"
				if comp not in companies:
					companies[comp] = []
				companies[comp].append(job)

			print(f"\n📍 Jobs by company:")
			for comp, comp_jobs in sorted(companies.items(), key=lambda x: len(x[1]), reverse=True):
				print(f"   {comp}: {len(comp_jobs)} jobs")
				if comp_jobs:
					print(f"      Example: {comp_jobs[0].title}")

	except Exception as e:
		print(f"❌ Error: {e}")


async def test_visa_sponsorship_keywords():
	"""Test searches specifically for visa sponsorship keywords"""
	print("\n" + "=" * 80)
	print("🌍 VISA SPONSORSHIP - Keyword-based Search")
	print("=" * 80)

	try:
		# Test Adzuna with visa sponsorship keywords
		print("\n📊 Adzuna: Jobs with 'visa sponsorship' in Germany")
		scraper = AdzunaScraper()
		jobs = await scraper.search_jobs(keywords="Software Engineer visa sponsorship", location="Germany", max_results=5)
		print(f"✅ Found {len(jobs)} jobs")
		for i, job in enumerate(jobs[:3], 1):
			print(f"\n{i}. {job.title}")
			print(f"   Company: {job.company}")
			print(f"   Location: {job.location}")

	except Exception as e:
		print(f"❌ Error: {e}")


async def comprehensive_eu_test():
	"""Run comprehensive test of all EU scrapers"""
	print("\n" + "=" * 80)
	print("🎯 COMPREHENSIVE EU JOB SCRAPER TEST")
	print("Focus: International Talent & Visa Sponsorship")
	print("=" * 80)

	print("\n📋 Test Plan:")
	print("   1. Arbeitnow - Germany visa sponsorship jobs")
	print("   2. Adzuna - Multi-country EU search")
	print("   3. The Muse - EU tech hub locations")
	print("   4. RapidAPI JSearch - EU optimized queries")
	print("   5. Firecrawl - Visa sponsor companies")
	print("   6. Keyword-based visa sponsorship search")

	# Run all tests
	await test_arbeitnow_visa()
	await test_adzuna_eu()
	await test_themuse_eu()
	await test_rapidapi_jsearch_eu()
	await test_firecrawl_visa_sponsors()
	await test_visa_sponsorship_keywords()

	print("\n" + "=" * 80)
	print("✅ ALL TESTS COMPLETED")
	print("=" * 80)


if __name__ == "__main__":
	asyncio.run(comprehensive_eu_test())
