from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.logging import get_logger
from app.models.job import Job
from app.schemas.job import JobCreate
from app.core.config import get_settings
from datetime import datetime
import httpx

logger = get_logger(__name__)
settings = get_settings()

class JobScraper:
    """Handles fetching jobs from external sources and saving them to the database."""

    def __init__(self, db: Session):
        self.db = db
        self.adzuna_api_url = "https://api.adzuna.com/v1/api/jobs/us/search/1"
        self.adzuna_app_id = settings.adzuna_app_id
        self.adzuna_app_key = settings.adzuna_app_key

    async def scrape_jobs(self, user_id: int, search_params: Dict[str, Any]) -> List[Job]:
        """Scrapes jobs from configured sources based on user preferences and search parameters."""
        new_jobs = []
        logger.info(f"Starting job scraping for user {user_id} with params: {search_params}")

        # Placeholder for fetching jobs from Adzuna
        adzuna_jobs = await self._fetch_from_adzuna(search_params)
        if adzuna_jobs:
            logger.info(f"Fetched {len(adzuna_jobs)} jobs from Adzuna.")
            for job_data in adzuna_jobs:
                job = self._process_adzuna_job(job_data, user_id)
                if job and not self._is_duplicate(job):
                    self.db.add(job)
                    new_jobs.append(job)
        
        self.db.commit()
        for job in new_jobs:
            self.db.refresh(job)
        logger.info(f"Finished job scraping for user {user_id}. Added {len(new_jobs)} new jobs.")
        return new_jobs

    async def _fetch_from_adzuna(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetches job listings from the Adzuna API."""
        if not self.adzuna_app_id or not self.adzuna_app_key:
            logger.warning("Adzuna API credentials not configured. Skipping Adzuna scraping.")
            return []

        params = {
            "app_id": self.adzuna_app_id,
            "app_key": self.adzuna_app_key,
            "results_per_page": 50, # Max results per page
            "what": search_params.get("what", "python developer"),
            "where": search_params.get("where", "london"),
            "distance": search_params.get("distance", "10"),
            "max_salary": search_params.get("max_salary"),
            "salary_min": search_params.get("salary_min"),
            "full_time": 1 if search_params.get("full_time") else 0,
            "part_time": 1 if search_params.get("part_time") else 0,
            "permanent": 1 if search_params.get("permanent") else 0,
            "contract": 1 if search_params.get("contract") else 0,
            "sort_by": search_params.get("sort_by", "relevance"),
            **search_params # Allow overriding default params
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.adzuna_api_url, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])
        except httpx.RequestError as e:
            logger.error(f"Adzuna API request failed: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Adzuna API returned HTTP error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during Adzuna scraping: {e}")
        return []

    def _process_adzuna_job(self, job_data: Dict[str, Any], user_id: int) -> Optional[Job]:
        """Processes raw job data from Adzuna into a Job model instance."""
        try:
            # Extract and transform data
            title = job_data.get("title")
            company = job_data.get("company", {}).get("display_name")
            location = job_data.get("location", {}).get("display_name")
            description = job_data.get("description")
            link = job_data.get("redirect_url")
            salary_min = job_data.get("salary_min")
            salary_max = job_data.get("salary_max")

            job_type = "Full-time" # Default
            if contract_time == "part_time":
                job_type = "Part-time"
            elif contract_type == "contract":
                job_type = "Contract"

            # Basic tech stack extraction (can be improved with NLP)
            tech_stack = []
            if description:
                description_lower = description.lower()
                common_tech = ["python", "java", "javascript", "react", "angular", "vue", "aws", "azure", "gcp", "docker", "kubernetes", "sql", "nosql"]
                for tech in common_tech:
                    if tech in description_lower:
                        tech_stack.append(tech)

            job_create = JobCreate(
                title=title,
                company=company,
                location=location,
                description=description,
                link=link,
                source="adzuna",
                user_id=user_id,
                salary_min=salary_min,
                salary_max=salary_max,
                job_type=job_type,
                remote=False, # Adzuna has a separate field for remote, need to check
                tech_stack=tech_stack,
                created_at=datetime.utcnow()
            )
            return Job(**job_create.model_dump())
        except Exception as e:
            logger.error(f"Error processing Adzuna job data: {e}", exc_info=True)
            return None

    def _is_duplicate(self, job: Job) -> bool:
        """Checks if a job already exists in the database based on title, company, and link."""
        existing_job = self.db.query(Job).filter(
            Job.title == job.title,
            Job.company == job.company,
            Job.link == job.link
        ).first()
        return existing_job is not None

    def get_user_job_preferences(self, user_id: int) -> Dict[str, Any]:
        """Fetches user's job preferences to tailor scraping queries."""
        # This would ideally come from UserJobPreferences model
        # For now, return a placeholder
        return {
            "keywords": ["software engineer", "backend", "fastapi"],
            "locations": ["remote", "new york"],
            "max_salary": None,
            "min_salary": None,
            "job_types": [],
            "experience_level": None
        }