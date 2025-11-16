import asyncio
from pathlib import Path

import pytest

from app.services.scraping import ScrapingConfig
from app.services.scraping.harness import ScraperHarness, ScraperRun

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "scrapers"


def _harness_config() -> ScrapingConfig:
	return ScrapingConfig(
		enable_eurotechjobs=True,
		enable_aijobsnet=True,
		enable_datacareer=True,
		enable_arbeitnow=False,
		enable_berlinstartupjobs=False,
		enable_relocateme=False,
		enable_eures=False,
		enable_landingjobs=False,
		enable_eutechjobs=False,
		enable_indeed=False,
		enable_adzuna=False,
		enable_themuse=False,
		enable_rapidapi_jsearch=False,
		enable_firecrawl=False,
	)


@pytest.mark.asyncio
async def test_scraper_harness_with_fixtures():
	harness = ScraperHarness(_harness_config(), fixtures_dir=FIXTURES_DIR, live_requests=False)
	runs = [
		ScraperRun(scraper="eurotechjobs", keywords="Machine Learning", location="Germany", max_results=2),
		ScraperRun(scraper="aijobsnet", keywords="AI", location="Netherlands", max_results=2),
		ScraperRun(scraper="datacareer", keywords="Data", location="Switzerland", max_results=2),
	]

	results = await harness.run_all(runs)
	assert all(result.success for result in results)
	assert all(result.jobs for result in results)
	assert {result.name for result in results} == {run.scraper for run in runs}


@pytest.mark.asyncio
async def test_multi_site_search_uses_fixture_data():
	harness = ScraperHarness(_harness_config(), fixtures_dir=FIXTURES_DIR, live_requests=False)
	jobs = await harness.multi_site_search("Data", "", max_total_results=10)

	assert jobs  # harness should surface fixture jobs
	sources = {job.source for job in jobs}
	assert sources.issubset({"scraped"})
