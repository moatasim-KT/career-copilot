#!/usr/bin/env python3
"""
Quick test script to verify new job scrapers are integrated correctly.

Usage:
    cd backend
    source venv/bin/activate
    python -m scripts.test_new_scrapers
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.services.scraping.scraper_manager import (ScraperManager,
                                                   ScrapingConfig)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_scrapers():
	"""Test the new scrapers"""
	settings = get_settings()
	
	logger.info("=" * 60)
	logger.info("Testing Job Scrapers Integration")
	logger.info("=" * 60)
	
	# Check which API keys are configured
	logger.info("\n📋 API Configuration:")
	logger.info(f"  Adzuna: {'✓ Configured' if settings.adzuna_app_id and settings.adzuna_app_key else '✗ Missing'}")
	logger.info(f"  The Muse: {'✓ Configured' if settings.themuse_base_url else '✗ Missing'} (API key optional)")
	logger.info(f"  RapidAPI JSEarch: {'✓ Configured' if settings.rapidapi_jsearch_key else '✗ Missing'}")
	
	# Create scraper manager with all scrapers enabled
	config = ScrapingConfig(
		max_results_per_site=10,  # Get more results for broader search
		enable_adzuna=bool(settings.adzuna_app_id and settings.adzuna_app_key),
		enable_themuse=True,  # Always available (no key required)
		enable_rapidapi_jsearch=bool(settings.rapidapi_jsearch_key),
		enable_indeed=False,  # Disabled - deprecated API
		enable_linkedin=False,  # Disabled - requires setup
	)
	
	manager = ScraperManager(config=config)
	
	logger.info(f"\n🔧 Initialized Scrapers: {list(manager.scrapers.keys())}")
	
	if not manager.scrapers:
		logger.error("❌ No scrapers available! Check your API keys in backend/.env")
		return
	
	# Test search for data science roles in Europe
	# Search multiple job titles and EU countries
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
			jobs = await manager.search_all_sites(
				keywords=keywords,
				location=location,
				max_total_results=15
			)
			
			all_jobs.extend(jobs)
			logger.info(f"   Found {len(jobs)} jobs")
			
		except Exception as e:
			logger.error(f"   ❌ Search failed for {keywords} in {location}: {e}")
			continue
	
	# Display results
	if all_jobs:
		logger.info(f"\n✅ Total jobs found across all searches: {len(all_jobs)}")
		logger.info(f"\n📊 Top Results (showing first 10):")
		
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


if __name__ == "__main__":
	asyncio.run(test_scrapers())
