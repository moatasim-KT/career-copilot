"""
Scraper manager to coordinate multiple job board scrapers
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from .base_scraper import BaseScraper, RateLimiter
from .indeed_scraper import IndeedScraper
from .linkedin_scraper import LinkedInScraper
from .adzuna_scraper import AdzunaScraper
from app.schemas.job import JobCreate


logger = logging.getLogger(__name__)


@dataclass
class ScrapingConfig:
    """Configuration for scraping operations"""
    max_results_per_site: int = 25
    max_concurrent_scrapers: int = 2
    enable_indeed: bool = True
    enable_linkedin: bool = True
    enable_adzuna: bool = True
    rate_limit_min_delay: float = 1.0
    rate_limit_max_delay: float = 3.0
    deduplication_enabled: bool = True


class ScraperManager:
    """Manages multiple job board scrapers"""
    
    def __init__(self, config: Optional[ScrapingConfig] = None):
        self.config = config or ScrapingConfig()
        self.scrapers = self._initialize_scrapers()
        
    def _initialize_scrapers(self) -> Dict[str, BaseScraper]:
        """Initialize available scrapers based on configuration"""
        scrapers = {}
        
        # Create rate limiter
        rate_limiter = RateLimiter(
            min_delay=self.config.rate_limit_min_delay,
            max_delay=self.config.rate_limit_max_delay
        )
        
        if self.config.enable_indeed:
            scrapers['indeed'] = IndeedScraper(rate_limiter=rate_limiter)
            
        if self.config.enable_linkedin:
            scrapers['linkedin'] = LinkedInScraper()  # LinkedIn uses its own rate limiter
            
        if self.config.enable_adzuna:
            scrapers['adzuna'] = AdzunaScraper(rate_limiter=rate_limiter)
            
            
        logger.info(f"Initialized {len(scrapers)} scrapers: {list(scrapers.keys())}")
        return scrapers
    
    async def search_all_sites(
        self, 
        keywords: str, 
        location: str = "",
        max_total_results: int = 100
    ) -> List[JobCreate]:
        """Search for jobs across all enabled job boards"""
        if not self.scrapers:
            logger.warning("No scrapers available")
            return []
        
        logger.info(f"Starting multi-site job search: '{keywords}' in '{location}'")
        
        # Calculate results per site
        results_per_site = min(
            self.config.max_results_per_site,
            max_total_results // len(self.scrapers)
        )
        
        # Create scraping tasks
        tasks = []
        for site_name, scraper in self.scrapers.items():
            task = self._scrape_site(
                site_name, 
                scraper, 
                keywords, 
                location, 
                results_per_site
            )
            tasks.append(task)
        
        # Run scrapers with concurrency limit
        semaphore = asyncio.Semaphore(self.config.max_concurrent_scrapers)
        results = await asyncio.gather(*[
            self._run_with_semaphore(semaphore, task) 
            for task in tasks
        ], return_exceptions=True)
        
        # Collect all jobs
        all_jobs = []
        for i, result in enumerate(results):
            site_name = list(self.scrapers.keys())[i]
            
            if isinstance(result, Exception):
                logger.error(f"Error scraping {site_name}: {result}")
                continue
            
            if isinstance(result, list):
                all_jobs.extend(result)
                logger.info(f"Collected {len(result)} jobs from {site_name}")
        
        # Deduplicate if enabled
        if self.config.deduplication_enabled:
            all_jobs = self._deduplicate_jobs(all_jobs)
        
        # Limit total results
        final_jobs = all_jobs[:max_total_results]
        
        logger.info(f"Multi-site search completed: {len(final_jobs)} unique jobs found")
        return final_jobs
    
    async def _run_with_semaphore(self, semaphore: asyncio.Semaphore, coro):
        """Run coroutine with semaphore for concurrency control"""
        async with semaphore:
            return await coro
    
    async def _scrape_site(
        self, 
        site_name: str, 
        scraper: BaseScraper, 
        keywords: str, 
        location: str, 
        max_results: int
    ) -> List[JobCreate]:
        """Scrape a single job site"""
        try:
            async with scraper:
                jobs = await scraper.search_jobs(keywords, location, max_results)
                logger.info(f"Successfully scraped {len(jobs)} jobs from {site_name}")
                return jobs
        except Exception as e:
            logger.error(f"Error scraping {site_name}: {e}")
            return []
    
    def _deduplicate_jobs(self, jobs: List[JobCreate]) -> List[JobCreate]:
        """Remove duplicate jobs based on title and company"""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            # Create a key for deduplication
            key = self._create_dedup_key(job)
            
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
            else:
                logger.debug(f"Duplicate job filtered: {job.title} at {job.company}")
        
        removed_count = len(jobs) - len(unique_jobs)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate jobs")
        
        return unique_jobs
    
    def _create_dedup_key(self, job: JobCreate) -> str:
        """Create a key for job deduplication"""
        # Normalize title and company for comparison
        title = self._normalize_text(job.title)
        company = self._normalize_text(job.company)
        location = self._normalize_text(job.location or "")
        
        return f"{title}|{company}|{location}"
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        
        # Convert to lowercase and remove extra whitespace
        normalized = ' '.join(text.lower().strip().split())
        
        # Remove common variations
        replacements = {
            'inc.': 'inc',
            'corp.': 'corp',
            'llc.': 'llc',
            'ltd.': 'ltd',
            '&': 'and',
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized
    
    async def test_scrapers(self) -> Dict[str, bool]:
        """Test all scrapers with a simple search"""
        results = {}
        
        for site_name, scraper in self.scrapers.items():
            try:
                async with scraper:
                    # Simple test search
                    jobs = await scraper.search_jobs("software engineer", "remote", 5)
                    results[site_name] = len(jobs) > 0
                    logger.info(f"Scraper test for {site_name}: {'PASS' if results[site_name] else 'FAIL'}")
            except Exception as e:
                results[site_name] = False
                logger.error(f"Scraper test for {site_name} failed: {e}")
        
        return results
    
    def get_available_scrapers(self) -> List[str]:
        """Get list of available scraper names"""
        return list(self.scrapers.keys())
    
    def is_scraper_enabled(self, scraper_name: str) -> bool:
        """Check if a specific scraper is enabled"""
        return scraper_name in self.scrapers