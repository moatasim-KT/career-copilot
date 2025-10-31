"""
Web scraping services for job boards
"""

from .base_scraper import BaseScraper
from .indeed_scraper import IndeedScraper

from .scraper_manager import ScraperManager, ScrapingConfig

__all__ = ["BaseScraper", "IndeedScraper", "ScraperManager", "ScrapingConfig"]
