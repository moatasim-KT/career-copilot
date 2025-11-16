"""CLI utility to exercise EU scrapers in live or fixture-backed mode."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Dict

# Ensure backend package is importable when running as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scraping import ScrapingConfig
from app.services.scraping.harness import ScraperHarness, ScraperRun

SCRAPER_RUNS = {
	"eurotechjobs": {"keywords": "Machine Learning", "location": "Germany"},
	"aijobsnet": {"keywords": "AI", "location": "Netherlands"},
	"datacareer": {"keywords": "Data", "location": "Switzerland"},
	"arbeitnow": {"keywords": "Data Science", "location": "Germany"},
	"berlinstartupjobs": {"keywords": "AI", "location": "Berlin"},
	"relocateme": {"keywords": "Machine Learning", "location": "Europe"},
	"eures": {"keywords": "Data Scientist", "location": "DE"},
}

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "backend" / "tests" / "fixtures" / "scrapers"


def _build_config() -> ScrapingConfig:
	return ScrapingConfig(
		max_results_per_site=5,
		max_concurrent_scrapers=2,
		enable_arbeitnow=True,
		enable_berlinstartupjobs=True,
		enable_relocateme=True,
		enable_eures=True,
		enable_eurotechjobs=True,
		enable_aijobsnet=True,
		enable_datacareer=True,
		enable_indeed=False,
		enable_adzuna=False,
		enable_themuse=False,
		enable_rapidapi_jsearch=False,
	)


async def run_scraper_suite(live_requests: bool = False):
	print("=" * 80)
	print("Testing EU Visa-Sponsorship Job Scrapers")
	print("=" * 80)

	harness = ScraperHarness(_build_config(), fixtures_dir=FIXTURES_DIR, live_requests=live_requests)
	runs = [
		ScraperRun(
			scraper=name,
			keywords=params["keywords"],
			location=params["location"],
		)
		for name, params in SCRAPER_RUNS.items()
		if name in harness.manager.scrapers
	]

	results = await harness.run_all(runs)
	_summary(results)
	return results


def _summary(results):
	total_jobs = sum(len(result.jobs) for result in results if result.success)
	successes = [res for res in results if res.success]
	failures = [res for res in results if not res.success]

	print(f"\n{'=' * 80}")
	print("SUMMARY")
	print(f"{'=' * 80}")
	for result in results:
		status = f"✅ {len(result.jobs)} jobs" if result.success else f"❌ {result.error}"
		print(f"{result.name:25s}: {status}")

	print(f"\nTotal Jobs Found: {total_jobs}")
	print(f"Successful Scrapers: {len(successes)}/{len(results)}")
	print(f"Failed Scrapers: {len(failures)}")
	print(f"{'=' * 80}\n")


async def run_multi_site_search(live_requests: bool = False):
	print("\n" + "=" * 80)
	print("Testing Multi-Site Search (All EU Scrapers)")
	print("=" * 80)

	harness = ScraperHarness(_build_config(), fixtures_dir=FIXTURES_DIR, live_requests=live_requests)
	jobs = await harness.multi_site_search("Data Science", "Europe", max_total_results=50)

	print(f"\n✅ Multi-site search completed! Total unique jobs: {len(jobs)}")
	by_source: Dict[str, int] = {}
	for job in jobs:
		by_source[job.source] = by_source.get(job.source, 0) + 1

	print("\n   Jobs by source:")
	for source, count in by_source.items():
		print(f"     - {source}: {count} jobs")

	return jobs


def _parse_args():
	parser = argparse.ArgumentParser(description="Run EU scraper harness")
	parser.add_argument("--live", action="store_true", help="Use live network requests instead of fixtures")
	return parser.parse_args()


if __name__ == "__main__":
	args = _parse_args()
	mode = "LIVE" if args.live else "FIXTURE"
	print(f"\n🚀 Starting EU Job Scraper Tests in {mode} mode...\n")

	asyncio.run(run_scraper_suite(live_requests=args.live))
	asyncio.run(run_multi_site_search(live_requests=args.live))

	print("\n✅ All tests completed!\n")
