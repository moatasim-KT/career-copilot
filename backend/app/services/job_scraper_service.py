from typing import Any, Dict, Optional, List
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models.job import Job
from app.schemas.job import JobCreate
from app.core.logging import get_logger
import httpx
import asyncio
logger = get_logger(__name__)

class JobScraperService:
    def __init__(self, db: Session, settings: Any = None):
        self.db = db
        self.settings = settings or get_settings()
        self.job_api_key = self.settings.job_api_key
        self.adzuna_app_id = self.settings.adzuna_app_id
        self.adzuna_app_key = self.settings.adzuna_app_key

        self.api_limits = {
            'adzuna': 1000,      # Free tier: 1000 requests/day
            'usajobs': 1000,     # Government API: generous limits
            'github_jobs': 500,  # No official limit, be conservative
            'remoteok': 100,     # Limited free usage
        }
        self.api_delays = {
            'adzuna': 0.1,       # 0.1 seconds between requests
            'usajobs': 0.5,      # 0.5 seconds between requests
            'github_jobs': 1.0,  # 1 second between requests
            'remoteok': 2.0,     # 2 seconds between requests
        }

    async def _make_api_request(self, url: str, params: Dict, headers: Optional[Dict] = None, api_name: str = "generic") -> Any:
        async with httpx.AsyncClient() as client:
            try:
                await asyncio.sleep(self.api_delays.get(api_name, 0.1)) # Respect API rate limits
                response = await client.get(url, params=params, headers=headers, timeout=10)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error for {api_name} API: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error for {api_name} API: {e}")
                raise

    async def search_adzuna(self, keywords: List[str], location: str, max_results: int = 20) -> List[JobCreate]:
        jobs = []
        if not self.adzuna_app_id or not self.adzuna_app_key:
            logger.warning("Adzuna API keys not configured. Skipping Adzuna search.")
            return []

        url = f"https://api.adzuna.com/v1/api/jobs/{self.settings.adzuna_country}/search/1"
        params = {
            "app_id": self.adzuna_app_id,
            "app_key": self.adzuna_app_key,
            "what": " ".join(keywords),
            "where": location,
            "results_per_page": min(max_results, 50), # Adzuna max is 50 per page
            "content-type": "application/json"
        }
        try:
            response_data = await self._make_api_request(url, params, api_name="adzuna")
            for job_data in response_data.get("results", [])[:max_results]:
                job = self._parse_adzuna_job(job_data)
                if job:
                    jobs.append(job)
            logger.info(f"Found {len(jobs)} jobs from Adzuna API")
        except Exception as e:
            logger.error(f"Error searching Adzuna API: {e}")
        return jobs

    async def search_usajobs(self, keywords: List[str], location: str, max_results: int = 20) -> List[JobCreate]:
        jobs = []
        headers = {
            'Host': 'data.usajobs.gov',
            'User-Agent': 'career-copilot@example.com'  # USAJobs requires email in User-Agent
        }
        params = {
            "Keyword": " ".join(keywords),
            "LocationName": location,
            "ResultsPerPage": min(max_results, 500) # USAJobs max is 500 per page
        }
        try:
            url = "https://data.usajobs.gov/api/search"
            response_data = await self._make_api_request(url, params, headers, api_name="usajobs")
            for item in response_data.get("SearchResult", {}).get("SearchResultItems", [])[:max_results]:
                job = self._parse_usajobs_job(item)
                if job:
                    jobs.append(job)
            logger.info(f"Found {len(jobs)} jobs from USAJobs API")
        except Exception as e:
            logger.error(f"Error searching USAJobs API: {e}")
        return jobs

    async def search_github_jobs(self, keywords: List[str], location: str, max_results: int = 20) -> List[JobCreate]:
        jobs = []
        params = {
            "description": " ".join(keywords),
            "location": location,
            "full_time": "true" if "full-time" in keywords else "false"
        }
        try:
            # GitHub Jobs API is deprecated, but sometimes still works for basic searches
            url = "https://jobs.github.com/positions.json"
            response_data = await self._make_api_request(url, params, api_name="github_jobs")
            for job_data in response_data[:max_results]:
                job = self._parse_github_job(job_data)
                if job:
                    jobs.append(job)
            logger.info(f"Found {len(jobs)} jobs from GitHub Jobs API")
        except Exception as e:
            logger.error(f"Error searching GitHub Jobs API: {e}")
        return jobs

    async def search_remoteok(self, keywords: List[str], max_results: int = 20) -> List[JobCreate]:
        jobs = []
        params = {
            "search": " ".join(keywords),
            "limit": min(max_results, 100) # RemoteOK max is 100
        }
        try:
            url = "https://remoteok.io/api"
            response_data = await self._make_api_request(url, params, api_name="remoteok")
            for job_data in response_data[1:]:  # First item is metadata
                job = self._parse_remoteok_job(job_data)
                if job:
                    jobs.append(job)
            logger.info(f"Found {len(jobs)} jobs from RemoteOK API")
        except Exception as e:
            logger.error(f"Error searching RemoteOK API: {e}")
        return jobs

    async def search_all_apis(self, keywords: List[str], location: str, max_results: int = 20) -> List[JobCreate]:
        """Search all available job APIs concurrently"""
        logger.info(f"Searching all job APIs for '{keywords}' in '{location}'")
        tasks = []
        
        # Adzuna
        tasks.append(self.search_adzuna(keywords, location, max_results // 4))
        # USAJobs (free government API)
        tasks.append(self.search_usajobs(keywords, location, max_results // 4))
        # GitHub Jobs (if still available)
        tasks.append(self.search_github_jobs(keywords, location, max_results // 4))
        # RemoteOK (for remote jobs, location is often ignored or assumed remote)
        tasks.append(self.search_remoteok(keywords, max_results // 4))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_jobs = []
        api_names = ['Adzuna', 'USAJobs', 'GitHub Jobs', 'RemoteOK']
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                logger.error(f"Error from {api_names[i]} API: {res}")
            else:
                all_jobs.extend(res)
                logger.info(f"Collected {len(res)} jobs from {api_names[i]}")

        unique_jobs = self._deduplicate_api_jobs(all_jobs)
        logger.info(f"API search completed: {len(unique_jobs)} unique jobs found")
        return unique_jobs[:max_results]

    def _deduplicate_api_jobs(self, jobs: List[JobCreate]) -> List[JobCreate]:
        """Remove duplicate jobs from API results based on title and company (case-insensitive)"""
        unique_jobs = []
        seen_keys = set()

        for job in jobs:
            key = f"{job.title.lower().strip()}|{job.company.lower().strip()}"
            if key not in seen_keys:
                unique_jobs.append(job)
                seen_keys.add(key)
            else:
                logger.debug(f"Duplicate job filtered: {job.title} at {job.company}")
        
        removed = len(jobs) - len(unique_jobs)
        if removed > 0:
            logger.info(f"Removed {removed} duplicate jobs from API results")
        return unique_jobs

    def deduplicate_against_db(self, new_jobs: List[JobCreate], user_id: int) -> List[JobCreate]:
        """Filter out new jobs that already exist in the database for the given user."""
        existing_jobs = self.db.query(Job).filter(Job.user_id == user_id).all()
        existing_job_keys = set()
        for job in existing_jobs:
            existing_job_keys.add(f"{job.title.lower().strip()}|{job.company.lower().strip()}")
        
        truly_unique_jobs = []
        removed_from_db_check = 0
        for job_data in new_jobs:
            key = f"{job_data.title.lower().strip()}|{job_data.company.lower().strip()}"
            if key not in existing_job_keys:
                truly_unique_jobs.append(job_data)
            else:
                removed_from_db_check += 1
        
        if removed_from_db_check > 0:
            logger.info(f"Removed {removed_from_db_check} jobs already in DB for user {user_id}")
        
        return truly_unique_jobs

    def _parse_adzuna_job(self, job_data: Dict[str, Any]) -> Optional[JobCreate]:
        try:
            title = job_data.get("title", "").replace("<b>", "").replace("</b>", "")
            description = job_data.get("description", "").replace("<b>", "").replace("</b>", "")
            return JobCreate(
                company=job_data.get("company", {}).get("display_name", "Unknown"),
                title=title,
                location=job_data.get("location", {}).get("display_name", "Unknown"),
                description=description,
                salary_range=f"{job_data.get("salary_min", 0)} - {job_data.get("salary_max", 0)}" if job_data.get("salary_min") else None,
                job_type=job_data.get("contract_type", "full-time"),
                remote_option="remote" if "remote" in job_data.get("location", {}).get("display_name", "").lower() else "onsite",
                tech_stack=job_data.get("category", {}).get("tag", "").split(",") if job_data.get("category") else [],
                link=job_data.get("redirect_url"),
                source="adzuna"
            )
        except Exception as e:
            logger.error(f"Error parsing Adzuna job: {e}")
            return None

    def _parse_usajobs_job(self, item: Dict[str, Any]) -> Optional[JobCreate]:
        try:
            job_data = item.get('MatchedObjectDescriptor', {})
            title = job_data.get('PositionTitle', '')
            company = job_data.get('OrganizationName', 'U.S. Government')
            location = self._extract_usajobs_location(job_data)
            description = job_data.get('QualificationSummary', '') or job_data.get('UserArea', {}).get('Details', {}).get('JobSummary', '')
            salary_info = self._extract_usajobs_salary(job_data)

            return JobCreate(
                company=company,
                title=title,
                location=location,
                description=description,
                salary_range=salary_info.get("salary_range"),
                job_type=job_data.get('PositionSchedule', [{}])[0].get('Name', 'full-time') if job_data.get('PositionSchedule') else 'full-time',
                remote_option="remote" if job_data.get('PositionRemuneration', [{}])[0].get('Description', '').lower() == 'remote' else 'onsite',
                tech_stack=[], # USAJobs doesn't provide tech stack directly
                link=job_data.get('PositionURI', ''),
                source="usajobs"
            )
        except Exception as e:
            logger.error(f"Error parsing USAJobs job: {e}")
            return None

    def _extract_usajobs_location(self, job_data: Dict[str, Any]) -> str:
        locations = job_data.get('PositionLocation', [])
        if locations:
            return ", ".join([loc.get('LocationName', '') for loc in locations])
        return "Unknown"

    def _extract_usajobs_salary(self, job_data: Dict[str, Any]) -> Dict[str, Optional[int]]:
        salary_min = None
        salary_max = None
        remuneration = job_data.get('PositionRemuneration', [])
        if remuneration:
            salary_min = remuneration[0].get('MinimumRange')
            salary_max = remuneration[0].get('MaximumRange')
        return {"salary_min": salary_min, "salary_max": salary_max, "salary_range": f"{salary_min} - {salary_max}" if salary_min else None}

    def _parse_github_job(self, job_data: Dict[str, Any]) -> Optional[JobCreate]:
        try:
            return JobCreate(
                title=job_data.get('title', ''),
                company=job_data.get('company', ''),
                location=job_data.get('location', ''),
                description=job_data.get('description', ''),
                job_type=job_data.get('type', 'full-time'),
                remote_option="remote" if "remote" in job_data.get('location', '').lower() else "onsite",
                tech_stack=[], # GitHub Jobs doesn't provide tech stack directly
                link=job_data.get('url', ''),
                source="github_jobs"
            )
        except Exception as e:
            logger.error(f"Error parsing GitHub job: {e}")
            return None

    def _parse_remoteok_job(self, job_data: Dict[str, Any]) -> Optional[JobCreate]:
        try:
            tags = job_data.get('tags', [])
            tech_stack = [tag for tag in tags if tag.lower() not in ["remote", "hiring"]]
            salary_min = job_data.get('salary_min')
            salary_max = job_data.get('salary_max')

            return JobCreate(
                title=job_data.get('position', ''),
                company=job_data.get('company', ''),
                location=job_data.get('location', 'Remote'),
                description=job_data.get('description', ''),
                salary_range=f"{salary_min} - {salary_max}" if salary_min else None,
                job_type="full-time", # RemoteOK primarily lists full-time
                remote_option="remote",
                tech_stack=tech_stack,
                link=job_data.get('url', ''),
                source="remoteok"
            )
        except Exception as e:
            logger.error(f"Error parsing RemoteOK job: {e}")
            return None
