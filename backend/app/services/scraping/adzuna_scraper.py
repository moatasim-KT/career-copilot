import logging
from typing import List, Dict, Any, Optional

from .base_scraper import BaseScraper
from app.schemas.job import JobCreate
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class AdzunaScraper(BaseScraper):
    """Scraper for Adzuna API"""

    def __init__(self, rate_limiter=None):
        super().__init__(rate_limiter)
        self.base_url = "https://api.adzuna.com/v1/api/jobs"
        self.app_id = settings.adzuna_app_id
        self.app_key = settings.adzuna_app_key
        self.country = settings.adzuna_country
        self.name = "adzuna"

        if not self.app_id or not self.app_key:
            logger.error("Adzuna API keys (ADZUNA_APP_ID, ADZUNA_APP_KEY) are not set.")
            raise ValueError("Adzuna API keys are required.")

    def _build_search_url(self, keywords: str, location: str, page: int = 1) -> str:
        """Build search URL for Adzuna API"""
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": 50,  # Max results per page for Adzuna
            "what": keywords,
            "where": location,
            "country": self.country,
            "content-type": "application/json",
            "page": page,
        }
        # Filter out empty parameters
        params = {k: v for k, v in params.items() if v}
        return f"{self.base_url}/search/{self.country}/?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

    async def search_jobs(self, keywords: str, location: str = "", max_results: int = 50) -> List[JobCreate]:
        """Search for jobs on Adzuna"""
        jobs: List[JobCreate] = []
        page = 1
        total_pages = 1

        while len(jobs) < max_results and page <= total_pages:
            url = self._build_search_url(keywords, location, page)
            response = await self._make_request(url)

            if response and response.status_code == 200:
                data = await response.json()
                total_results = data.get("count", 0)
                if total_results > 0:
                    # Adzuna API returns max 50 results per page
                    total_pages = (total_results + 49) // 50
                    for job_data in data.get("results", []):
                        parsed_job = self._parse_job_listing(job_data)
                        if parsed_job:
                            job_create_obj = self._create_job_object(parsed_job)
                            if job_create_obj:
                                jobs.append(job_create_obj)
                                if len(jobs) >= max_results:
                                    break
                else:
                    logger.info(f"No jobs found on Adzuna for keywords: {keywords}, location: {location}")
                    break
            else:
                logger.error(f"Failed to fetch jobs from Adzuna. Response: {response.text if response else 'No response'}")
                break
            page += 1

        return jobs

    def _parse_job_listing(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a single job listing from Adzuna API response"""
        try:
            salary_min = job_data.get("salary_min")
            salary_max = job_data.get("salary_max")
            salary_string = ""
            if salary_min is not None and salary_max is not None:
                salary_string = f"${salary_min:,.0f}-${salary_max:,.0f}"
            elif salary_min is not None:
                salary_string = f"${salary_min:,.0f}+"



            return {
                "title": job_data.get("title"),
                "company": job_data.get("company", {}).get("display_name", ""),
                "location": job_data.get("location", {}).get("display_name", ""),
                "description": job_data.get("description"),
                "url": job_data.get("redirect_url"),
                "salary": salary_string, # Pass salary as a string for _extract_salary
                "job_type": job_data.get("contract_type", "").replace("_", "-"),
                "remote": "remote" in job_data.get("category", {}).get("label", "").lower() or \
                          "remote" in job_data.get("description", "").lower(),
                "tech_stack": [], # Adzuna doesn't provide tech stack directly, can be extracted from description later
                "responsibilities": job_data.get("description"), # Adzuna description often contains responsibilities
                "source": self.name,
                "currency": "USD",
                "requirements": "" # Adzuna doesn't have a direct requirements field, default to empty string
            }
        except Exception as e:
            logger.error(f"Error parsing Adzuna job listing: {e}")
            return None
