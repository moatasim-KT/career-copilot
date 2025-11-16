"""Reusable harness for running job scrapers in live or fixture-backed modes."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import httpx

from app.schemas.job import JobCreate

from .scraper_manager import ScraperManager, ScrapingConfig


@dataclass
class ScraperRun:
	"""Defines a single scraper execution."""

	scraper: str
	keywords: str
	location: str = ""
	max_results: int = 5


@dataclass
class ScraperRunResult:
	"""Result returned by the harness for each scraper."""

	name: str
	success: bool
	jobs: List[JobCreate]
	error: Optional[str] = None


class ScraperHarness:
	"""Coordinates scraper execution for tests and manual scripts."""

	def __init__(
		self,
		config: ScrapingConfig,
		fixtures_dir: Optional[Path | str] = None,
		live_requests: bool = False,
	):
		self.config = config
		self.fixtures_dir = Path(fixtures_dir) if fixtures_dir else None
		self.live_requests = live_requests
		self.manager = ScraperManager(config)

	def _fixture_path(self, scraper_name: str) -> Optional[Path]:
		if not self.fixtures_dir:
			return None

		possible_extensions = [".xml", ".json", ".html"]
		for ext in possible_extensions:
			candidate = self.fixtures_dir / f"{scraper_name}{ext}"
			if candidate.exists():
				return candidate
		return None

	def _build_override(self, scraper_name: str):
		path = self._fixture_path(scraper_name)
		if not path:
			return None

		async def _override(url: str, kwargs: Dict[str, Any]):
			text = path.read_text(encoding="utf-8")
			request = httpx.Request("GET", url, headers=kwargs.get("headers"))
			return httpx.Response(200, request=request, content=text.encode("utf-8"))

		return _override

	async def _run_single(self, run: ScraperRun) -> ScraperRunResult:
		scraper = self.manager.scrapers.get(run.scraper)
		if not scraper:
			raise ValueError(f"Scraper '{run.scraper}' is not initialized in current configuration")

		override = None if self.live_requests else self._build_override(run.scraper)
		scraper.set_request_override(override)

		try:
			async with scraper:
				jobs = await scraper.search_jobs(run.keywords, run.location, run.max_results)
			return ScraperRunResult(name=run.scraper, success=True, jobs=jobs)
		except Exception as exc:  # pragma: no cover - surfaced to caller
			return ScraperRunResult(name=run.scraper, success=False, jobs=[], error=str(exc))
		finally:
			scraper.set_request_override(None)

	async def run_all(self, runs: Iterable[ScraperRun]) -> List[ScraperRunResult]:
		"""Execute multiple scrapers concurrently."""

		tasks = [self._run_single(run) for run in runs]
		return await asyncio.gather(*tasks)

	async def multi_site_search(self, keywords: str, location: str, max_total_results: int = 50):
		"""Run ScraperManager multi-site search respecting fixture overrides."""

		if not self.live_requests:
			for name, scraper in self.manager.scrapers.items():
				scraper.set_request_override(self._build_override(name))

		try:
			return await self.manager.search_all_sites(keywords, location, max_total_results)
		finally:
			for scraper in self.manager.scrapers.values():
				scraper.set_request_override(None)
