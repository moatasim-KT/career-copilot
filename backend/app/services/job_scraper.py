"""
Job scraping service for multiple job boards.

Supports:
- LinkedIn Jobs API
- Indeed API
- Glassdoor API
- ZipRecruiter API
"""

from typing import List, Dict, Optional
import aiohttp
import asyncio
from datetime import datetime
from ..core.logging import get_logger
from ..models.job import Job
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import text
from ..core.config import get_settings

logger = get_logger(__name__)


class JobListing(BaseModel):
    """Pydantic model for scraped job listings."""
    title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    salary_range: Optional[str] = None
    requirements: List[str] = []
    url: Optional[str] = None
    source: Optional[str] = None
    posted_date: Optional[datetime] = None
    scraped_date: datetime = datetime.utcnow()


class JobScraperService:
    """Service for scraping jobs from multiple sources."""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_keys = {
            'linkedin': self.settings.LINKEDIN_API_KEY,
            'indeed': self.settings.INDEED_API_KEY,
            'glassdoor': self.settings.GLASSDOOR_API_KEY,
            'ziprecruiter': self.settings.ZIPRECRUITER_API_KEY
        }

    async def scrape_linkedin(self, keywords: str, location: str, limit: int = 100) -> List[Dict]:
        """Scrape jobs from LinkedIn."""
        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': f'Bearer {self.api_keys["linkedin"]}',
                'Accept': 'application/json',
            }
            params = {
                'keywords': keywords,
                'location': location,
                'limit': limit
            }
            url = 'https://api.linkedin.com/v2/jobs-search'
            try:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"LinkedIn API error: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"LinkedIn scraping error: {str(e)}")
                return []

    async def scrape_indeed(self, query: str, location: str, limit: int = 100) -> List[Dict]:
        """Scrape jobs from Indeed."""
        async with aiohttp.ClientSession() as session:
            headers = {'Authorization': f'Bearer {self.api_keys["indeed"]}'}
            params = {
                'q': query,
                'l': location,
                'limit': limit
            }
            url = 'https://api.indeed.com/ads/apisearch'
            try:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Indeed API error: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"Indeed scraping error: {str(e)}")
                return []

    async def scrape_all_sources(self, query: str, location: str, limit_per_source: int = 100) -> List[JobListing]:
        """Scrape jobs from all configured sources."""
        tasks = [
            self.scrape_linkedin(query, location, limit_per_source),
            self.scrape_indeed(query, location, limit_per_source)
            # Add more sources as needed
        ]
        
        results = await asyncio.gather(*tasks)
        processed_jobs = []
        
        for source_jobs in results:
            for job in source_jobs:
                processed_jobs.append(
                    JobListing(
                        title=job.get('title'),
                        company=job.get('company'),
                        location=job.get('location'),
                        description=job.get('description'),
                        salary_range=job.get('salary_range'),
                        requirements=job.get('requirements', []),
                        url=job.get('url'),
                        source=job.get('source'),
                        posted_date=job.get('posted_date'),
                        scraped_date=datetime.utcnow()
                    )
                )
        
        return processed_jobs

    async def run_scheduled_scraping(self, saved_searches: List[Dict]):
        """Run scheduled scraping for saved searches."""
        for search in saved_searches:
            jobs = await self.scrape_all_sources(
                query=search['keywords'],
                location=search['location'],
                limit_per_source=search.get('limit', 100)
            )
            await self._save_and_notify(jobs, search['user_id'])

    async def _save_and_notify(self, jobs: List[JobListing], user_id: int):
        """Save scraped jobs and notify user of new matches."""
        from ..core.database import get_database_manager
        from ..models.user import User
        from ..services.notification_service import NotificationService
        
        if not jobs:
            logger.info(f"No jobs to save for user {user_id}")
            return
        
        db_manager = get_database_manager()
        notification_service = NotificationService()
        new_jobs_count = 0
        
        try:
            async with db_manager.get_async_session() as session:
                # Get user for notifications
                user = await session.get(User, user_id)
                if not user:
                    logger.error(f"User {user_id} not found")
                    return
                
                # Save jobs to database
                for job_listing in jobs:
                    # Check if job already exists (avoid duplicates)
                    existing_job = await session.execute(
                        text("SELECT id FROM jobs WHERE title = :title AND company = :company AND user_id = :user_id"),
                        {
                            "title": job_listing.title,
                            "company": job_listing.company,
                            "user_id": user_id
                        }
                    )
                    
                    if existing_job.first():
                        continue  # Skip duplicate
                    
                    # Create new job record
                    job = Job(
                        user_id=user_id,
                        title=job_listing.title,
                        company=job_listing.company,
                        location=job_listing.location,
                        description=job_listing.description,
                        salary_range=job_listing.salary_range,
                        requirements="\n".join(job_listing.requirements) if job_listing.requirements else None,
                        source_url=job_listing.url,
                        source="scraped",
                        status="not_applied",
                        created_at=datetime.utcnow()
                    )
                    
                    session.add(job)
                    new_jobs_count += 1
                
                await session.commit()
                
                # Send notification if new jobs were found
                if new_jobs_count > 0:
                    logger.info(f"Saved {new_jobs_count} new jobs for user {user_id}")
                    
                    # Prepare job data for notification
                    job_data = [
                        {
                            "title": job.title,
                            "company": job.company,
                            "location": job.location or "Remote/Not specified",
                            "salary_range": job.salary_range or "Not specified",
                            "url": job.source_url
                        }
                        for job in jobs[:5]  # Limit to first 5 jobs for email
                    ]
                    
                    # Send notification email
                    try:
                        notification_service.send_job_alert(user, job_data, new_jobs_count)
                        logger.info(f"Job alert notification sent to user {user_id}")
                    except Exception as e:
                        logger.error(f"Failed to send job alert notification: {e}")
                        # Continue execution - notification failure shouldn't stop job saving
                
                else:
                    logger.info(f"No new jobs found for user {user_id} (all were duplicates)")
                    
        except Exception as e:
            logger.error(f"Error saving jobs for user {user_id}: {e}")
            raise