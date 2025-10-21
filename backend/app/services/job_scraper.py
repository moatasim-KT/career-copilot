"""Job scraping service"""

import requests
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.job import Job
from ..core.config import Settings

logger = logging.getLogger(__name__)

class JobScraperService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.job_api_key = settings.job_api_key

    def scrape_jobs(self, skills: List[str], preferred_locations: List[str], limit: int = 20) -> List[Dict[str, Any]]:
        """
        Scrapes jobs from an external API based on user skills and preferred locations.
        This is a placeholder implementation with configurable job API support.
        
        Args:
            skills: List of user skills to search for
            preferred_locations: List of preferred locations
            limit: Maximum number of jobs to return
            
        Returns:
            List of job dictionaries
        """
        if not self.job_api_key:
            logger.info("Job API key not configured. Skipping job scraping.")
            return []

        if not skills or not preferred_locations:
            logger.info("User skills or preferred locations not provided. Skipping job scraping.")
            return []

        scraped_jobs = []
        
        # Iterate through skills and locations to create search combinations
        for skill in skills[:3]:  # Limit to top 3 skills to avoid too many API calls
            for location in preferred_locations[:2]:  # Limit to top 2 locations
                try:
                    jobs = self._fetch_jobs_from_api(skill, location, limit // (len(skills[:3]) * len(preferred_locations[:2])))
                    scraped_jobs.extend(jobs)
                except Exception as e:
                    logger.error(f"Error fetching jobs for skill '{skill}' in location '{location}': {str(e)}")
                    continue

        # For now, return mock data as placeholder for actual API integration
        mock_jobs = self._generate_mock_jobs(skills, preferred_locations, limit)
        return mock_jobs

    def _fetch_jobs_from_api(self, keyword: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """
        Placeholder for actual API integration (Adzuna, Indeed, etc.)
        This method should be implemented with actual API calls.
        """
        # TODO: Implement actual API integration
        # Example for Adzuna API:
        # url = f"https://api.adzuna.com/v1/api/jobs/{country}/search"
        # params = {
        #     "app_id": self.settings.adzuna_app_id,
        #     "app_key": self.job_api_key,
        #     "what": keyword,
        #     "where": location,
        #     "results_per_page": limit
        # }
        # response = requests.get(url, params=params)
        # return self._parse_api_response(response.json())
        
        return []

    def _generate_mock_jobs(self, skills: List[str], preferred_locations: List[str], limit: int) -> List[Dict[str, Any]]:
        """
        Generate mock job data for testing purposes.
        This should be removed when actual API integration is implemented.
        """
        mock_companies = ["TechCorp", "InnovateLabs", "DataSystems", "CloudWorks", "DevStudio"]
        mock_job_types = ["Software Engineer", "Developer", "Senior Developer", "Lead Developer", "Full Stack Developer"]
        
        mock_jobs = []
        for i in range(min(limit, 10)):  # Generate up to 10 mock jobs
            skill = skills[i % len(skills)] if skills else "Python"
            location = preferred_locations[i % len(preferred_locations)] if preferred_locations else "Remote"
            company = mock_companies[i % len(mock_companies)]
            job_type = mock_job_types[i % len(mock_job_types)]
            
            mock_jobs.append({
                "company": company,
                "title": f"{skill} {job_type}",
                "location": location,
                "description": f"Exciting opportunity for a {skill} developer at {company}. Join our innovative team!",
                "requirements": f"Strong experience with {skill} and related technologies.",
                "tech_stack": [skill] + skills[:2],  # Include the main skill plus up to 2 others
                "responsibilities": f"Develop and maintain {skill} applications, collaborate with team members, participate in code reviews.",
                "salary_range": "$80,000 - $120,000",
                "job_type": "full-time",
                "remote_option": "hybrid" if i % 2 == 0 else "remote",
                "link": f"https://example.com/jobs/{company.lower()}-{i}",
                "source": "scraped"
            })
        
        return mock_jobs

    def deduplicate_jobs(self, new_jobs: List[Dict[str, Any]], user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Deduplicates new jobs against existing jobs in the database
        based on company and title (case-insensitive comparison).
        
        Args:
            new_jobs: List of new job dictionaries to deduplicate
            user_id: Optional user ID to limit deduplication scope to user's jobs
            
        Returns:
            List of unique job dictionaries
        """
        # Query existing jobs - either for specific user or all jobs
        query = self.db.query(Job)
        if user_id:
            query = query.filter(Job.user_id == user_id)
        
        existing_jobs = query.all()
        
        # Create set of existing job keys (company, title) in lowercase
        existing_job_keys = set()
        for job in existing_jobs:
            key = (job.company.lower().strip(), job.title.lower().strip())
            existing_job_keys.add(key)

        # Filter out duplicates from new jobs
        unique_new_jobs = []
        seen_new_keys = set()  # Track duplicates within new_jobs list
        
        for job_data in new_jobs:
            company = job_data.get("company", "").lower().strip()
            title = job_data.get("title", "").lower().strip()
            
            if not company or not title:
                logger.warning(f"Skipping job with missing company or title: {job_data}")
                continue
                
            key = (company, title)
            
            # Check against existing jobs and already processed new jobs
            if key not in existing_job_keys and key not in seen_new_keys:
                unique_new_jobs.append(job_data)
                seen_new_keys.add(key)
            else:
                logger.debug(f"Duplicate job found: {job_data.get('company')} - {job_data.get('title')}")

        logger.info(f"Deduplicated {len(new_jobs)} jobs down to {len(unique_new_jobs)} unique jobs")
        return unique_new_jobs
