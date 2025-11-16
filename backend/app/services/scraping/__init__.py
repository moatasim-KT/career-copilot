"""
Web scraping services for job boards
"""

from .aijobs_scraper import AIJobsNetScraper
from .base_scraper import BaseScraper
from .datacareer_scraper import DataCareerScraper
from .eu_company_playwright_scraper import EUCompanyPlaywrightScraper
from .eurotechjobs_scraper import EuroTechJobsScraper
from .eutechjobs_scraper import EUTechJobsScraper
from .indeed_scraper import IndeedScraper
from .landingjobs_scraper import LandingJobsScraper
from .scraper_manager import ScraperManager, ScrapingConfig

__all__ = [
	"AIJobsNetScraper",
	"BaseScraper",
	"DataCareerScraper",
	"EUCompanyPlaywrightScraper",
	"EUTechJobsScraper",
	"EuroTechJobsScraper",
	"IndeedScraper",
	"LandingJobsScraper",
	"ScraperManager",
	"ScrapingConfig",
]
