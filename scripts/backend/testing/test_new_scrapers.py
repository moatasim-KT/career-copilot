#!/usr/bin/env python3
"""Quick harness-powered script to verify scraper integrations."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path when executed directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.services.scraping.harness import ScraperHarness
from app.services.scraping.scraper_manager import ScrapingConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = BACKEND_ROOT / "tests" / "fixtures" / "scrapers"


def _available_fixture_scrapers() -> set[str]:
	if not FIXTURES_DIR.exists():
		return set()
	return {path.stem for path in FIXTURES_DIR.iterdir() if path.is_file()}


def _build_config(live_requests: bool) -> ScrapingConfig:
	settings = get_settings()
	fixture_scrapers = _available_fixture_scrapers()

	def enabled(flag: bool, scraper_slug: str) -> bool:
		if not flag:
			return False
		return live_requests or scraper_slug in fixture_scrapers

	return ScrapingConfig(
		max_results_per_site=10,
		enable_indeed=False,
		enable_linkedin=False,
		enable_adzuna=enabled(bool(settings.adzuna_app_id and settings.adzuna_app_key), "adzuna"),
		enable_themuse=enabled(bool(settings.themuse_base_url), "themuse"),
		enable_rapidapi_jsearch=enabled(bool(settings.rapidapi_jsearch_key), "rapidapi_jsearch"),
		enable_arbeitnow=enabled(settings.SCRAPING_ENABLE_ARBEITNOW, "arbeitnow"),
		enable_berlinstartupjobs=enabled(settings.SCRAPING_ENABLE_BERLINSTARTUPJOBS, "berlinstartupjobs"),
		enable_relocateme=enabled(settings.SCRAPING_ENABLE_RELOCATEME, "relocateme"),
		enable_eures=enabled(settings.SCRAPING_ENABLE_EURES, "eures"),
		enable_landingjobs=enabled(settings.SCRAPING_ENABLE_LANDINGJOBS, "landingjobs"),
		enable_eutechjobs=enabled(settings.SCRAPING_ENABLE_EUTECHJOBS, "eutechjobs"),
		enable_eurotechjobs=enabled(settings.SCRAPING_ENABLE_EUROTECHJOBS, "eurotechjobs"),
		enable_aijobsnet=enabled(settings.SCRAPING_ENABLE_AIJOBSNET, "aijobsnet"),
		enable_datacareer=enabled(settings.SCRAPING_ENABLE_DATACAREER, "datacareer"),
		enable_firecrawl=enabled(bool(settings.firecrawl_api_key), "firecrawl"),
		enable_eu_company_playwright=enabled(settings.SCRAPING_ENABLE_EU_PLAYWRIGHT, "eu_company_playwright"),
	)


def _log_api_configuration():
	settings = get_settings()
	logger.info("\n📋 API Configuration:")
	logger.info(f"  Adzuna: {'✓ Configured' if settings.adzuna_app_id and settings.adzuna_app_key else '✗ Missing'}")
	logger.info(f"  The Muse: {'✓ Configured' if settings.themuse_base_url else '✗ Missing'} (API key optional)")
	logger.info(f"  RapidAPI JSearch: {'✓ Configured' if settings.rapidapi_jsearch_key else '✗ Missing'}")
	logger.info(f"  Firecrawl: {'✓ Configured' if settings.firecrawl_api_key else '✗ Missing'}")


async def test_scrapers(live_requests: bool = False):
	"""Test the scrapers using the harness"""
	logger.info("=" * 60)
	logger.info("Testing Job Scrapers Integration")
	logger.info("=" * 60)

	mode = "LIVE" if live_requests else "FIXTURE"
	logger.info(f"\n🌐 Mode: {mode}")
	_log_api_configuration()

	config = _build_config(live_requests)
	harness = ScraperHarness(config, fixtures_dir=FIXTURES_DIR, live_requests=live_requests)
	available_scrapers = list(harness.manager.scrapers.keys())

	logger.info(f"\n🔧 Initialized Scrapers: {available_scrapers}")
	if not available_scrapers:
		logger.error("❌ No scrapers available! Check your .env or provide fixtures")
		return

	search_queries = [
		("Data Scientist", "Germany"),
		("Data Analyst", "Netherlands"),
		("ML Engineer", "France"),
		("AI Engineer", "United Kingdom"),
	]

	all_jobs = []

	for keywords, location in search_queries:
		logger.info(f"\n🔍 Searching for '{keywords}' in '{location}'...")
		try:
			jobs = await harness.multi_site_search(keywords=keywords, location=location, max_total_results=15)
			all_jobs.extend(jobs)
			logger.info(f"   Found {len(jobs)} jobs")
		except Exception as exc:  # pragma: no cover - CLI output only
			logger.error(f"   ❌ Search failed for {keywords} in {location}: {exc}")
			continue

	if all_jobs:
		logger.info(f"\n✅ Total jobs found across all searches: {len(all_jobs)}")
		logger.info("\n📊 Top Results (showing first 10):")
		for i, job in enumerate(all_jobs[:10], 1):
			logger.info(f"\n  {i}. {job.title}")
			logger.info(f"     Company: {job.company}")
			logger.info(f"     Location: {job.location}")
			logger.info(f"     Source: {job.source}")
			logger.info(f"     Remote: {job.remote_option or 'n/a'}")
			if (job.salary_min is not None) or (job.salary_max is not None):
				min_part = f"{job.salary_min:,}" if job.salary_min is not None else "?"
				max_part = f"{job.salary_max:,}" if job.salary_max is not None else "+"
				logger.info(f"     Salary: {min_part}-{max_part} {job.currency or ''}")
			if job.application_url:
				logger.info(f"     Apply: {job.application_url}")

		if len(all_jobs) > 10:
			logger.info(f"\n  ... and {len(all_jobs) - 10} more jobs")

		logger.info("\n" + "=" * 60)
		logger.info("✅ Integration test PASSED!")
		logger.info("=" * 60)
	else:
		logger.warning("\n⚠️  No jobs found!")
		logger.info("\n" + "=" * 60)
		logger.info("⚠️  Integration test completed with no results")
		logger.info("=" * 60)


def _parse_args():
	parser = argparse.ArgumentParser(description="Run scraper integration test")
	parser.add_argument("--live", action="store_true", help="Use live network requests instead of fixtures")
	return parser.parse_args()


if __name__ == "__main__":
	args = _parse_args()
	asyncio.run(test_scrapers(live_requests=args.live))
