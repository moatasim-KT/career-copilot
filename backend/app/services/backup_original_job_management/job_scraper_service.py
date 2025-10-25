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
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import feedparser
from app.services.notification_service import NotificationService
from app.services.skill_matching_service import SkillMatchingService

class JobScraper:
    """Handles fetching jobs from external sources and saving them to the database."""

class JobScraperService:
    def __init__(self, db: Session = None):
        settings = get_settings()

        
        # API configurations
        self.apis = {
            'adzuna': {
                'enabled': bool(settings.ADZUNA_APP_ID and settings.ADZUNA_APP_KEY),
                'base_url': 'https://api.adzuna.com/v1/api/jobs',
                'app_id': settings.ADZUNA_APP_ID,
                'app_key': settings.ADZUNA_APP_KEY
            },
            'github': {
                'enabled': bool(settings.GITHUB_API_TOKEN),
                'base_url': 'https://api.github.com/search/issues',
                'token': settings.GITHUB_API_TOKEN
            },
            'weworkremotely': {
                'enabled': True,  # RSS feed doesn't require authentication
                'base_url': 'https://weworkremotely.com/categories/remote-programming-jobs.rss'
            },
            'stackoverflow': {
                'enabled': True,  # RSS feed doesn't require authentication
                'base_url': 'https://stackoverflow.com/jobs/feed'
            }
        }
        new_jobs = []
    
        async def scrape_jobs(self, user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
            """
            Scrape jobs from all configured sources.
            
            Args:
                user_preferences: Dictionary containing user preferences
                    - skills: List of skills
                    - locations: List of preferred locations
                    - experience_level: Experience level
                    - job_types: List of preferred job types
                    - remote_option: Remote work preference
                    
            Returns:
                List of job dictionaries
            """
            tasks = []
            
            # Create tasks for each enabled API
            if self.apis['adzuna']['enabled']:
                tasks.append(self._scrape_adzuna(user_preferences))
            if self.apis['github']['enabled']:
                tasks.append(self._scrape_github_issues(user_preferences))
            
            # RSS feeds
            tasks.append(self._scrape_weworkremotely(user_preferences))
            tasks.append(self._scrape_stackoverflow(user_preferences))
                
            # Run all scraping tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine and normalize results
            all_jobs = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error in job scraping: {str(result)}")
                    continue
                all_jobs.extend(result)
                
            return all_jobs
    
        async def _scrape_adzuna(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
            """Scrape jobs from Adzuna API."""
            try:
                async with aiohttp.ClientSession() as session:
                    params = {
                        'app_id': self.apis['adzuna']['app_id'],
                        'app_key': self.apis['adzuna']['app_key'],
                        'what': ' '.join(preferences['skills']),
                        'where': preferences['locations'][0],  # Primary location
                        'max_days_old': 30,
                        'results_per_page': 50
                    }
                    
                    url = f"{self.apis['adzuna']['base_url']}/gb/search/1"
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            return [self._normalize_adzuna_job(job) for job in data.get('results', [])]
                        else:
                            logger.error(f"Adzuna API error: {response.status}")
                            return []
                            
            except Exception as e:
                logger.error(f"Error scraping from Adzuna: {str(e)}")
                return []
    
        async def _scrape_github_issues(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
            """
            Scrape job postings from GitHub issues.
            Many companies post jobs as issues in their repos with 'job' label.
            """
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        'Authorization': f'token {self.apis["github"]["token"]}',
                        'Accept': 'application/vnd.github.v3+json'
                    }
                    
                    # Search for issues labeled as jobs with relevant skills
                    skills_query = ' OR '.join(preferences['skills'])
                    query = f'label:job type:issue state:open ({skills_query})'
                    
                    params = {
                        'q': query,
                        'sort': 'created',
                        'order': 'desc',
                        'per_page': 50
                    }
                    
                    url = self.apis['github']['base_url']
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            return [self._normalize_github_issue(issue) for issue in data.get('items', [])]
                        else:
                            logger.error(f"GitHub API error: {response.status}")
                            return []
                            
            except Exception as e:
                logger.error(f"Error scraping from GitHub: {str(e)}")
                return []
    
        async def _scrape_weworkremotely(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
            """Scrape jobs from WeWorkRemotely RSS feed."""
            try:
                async with aiohttp.ClientSession() as session:
                    url = self.apis['weworkremotely']['base_url']
                    async with session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            feed = feedparser.parse(content)
                            return [self._normalize_wwr_job(entry) for entry in feed.entries]
                        else:
                            logger.error(f"WWR feed error: {response.status}")
                            return []
                            
            except Exception as e:
                logger.error(f"Error scraping from WeWorkRemotely: {str(e)}")
                return []
    
        async def _scrape_stackoverflow(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
            """Scrape jobs from Stack Overflow RSS feed."""
            try:
                async with aiohttp.ClientSession() as session:
                    url = self.apis['stackoverflow']['base_url']
                    async with session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            feed = feedparser.parse(content)
                            return [self._normalize_stackoverflow_job(entry) for entry in feed.entries]
                        else:
                            logger.error(f"Stack Overflow feed error: {response.status}")
                            return []
                            
            except Exception as e:
                logger.error(f"Error scraping from Stack Overflow: {str(e)}")
                return []
    
        def _normalize_adzuna_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
            """Normalize Adzuna job data to common format."""
            return {
                'title': job.get('title'),
                'company': job.get('company', {}).get('display_name'),
                'location': job.get('location', {}).get('display_name'),
                'description': job.get('description'),
                'url': job.get('redirect_url'),
                'salary_min': job.get('salary_min'),
                'salary_max': job.get('salary_max'),
                'source': 'adzuna',
                'remote': 'remote' in job.get('description', '').lower(),
                'posted_at': job.get('created'),
                'original_data': job
            }
    
        def _normalize_github_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
            """Normalize GitHub issue job posting to common format."""
            return {
                'title': issue.get('title'),
                'company': self._extract_company_from_issue(issue),
                'location': self._extract_location_from_issue(issue),
                'description': issue.get('body'),
                'url': issue.get('html_url'),
                'salary_min': None,
                'salary_max': None,
                'source': 'github',
                'remote': 'remote' in issue.get('body', '').lower(),
                'posted_at': issue.get('created_at'),
                'original_data': issue
            }
    
        def _normalize_wwr_job(self, entry: Dict[str, Any]) -> Dict[str, Any]:
            """Normalize WeWorkRemotely job to common format."""
            return {
                'title': entry.get('title'),
                'company': self._extract_company_from_wwr(entry),
                'location': 'Remote',
                'description': entry.get('description'),
                'url': entry.get('link'),
                'salary_min': None,
                'salary_max': None,
                'source': 'weworkremotely',
                'remote': True,
                'posted_at': entry.get('published'),
                'original_data': entry
            }
    
        def _normalize_stackoverflow_job(self, entry: Dict[str, Any]) -> Dict[str, Any]:
            """Normalize Stack Overflow job to common format."""
            return {
                'title': entry.get('title'),
                'company': self._extract_company_from_so(entry),
                'location': self._extract_location_from_so(entry),
                'description': entry.get('description'),
                'url': entry.get('link'),
                'salary_min': None,
                'salary_max': None,
                'source': 'stackoverflow',
                'remote': 'remote' in entry.get('description', '').lower(),
                'posted_at': entry.get('published'),
                'original_data': entry
            }
    
        def _extract_company_from_issue(self, issue: Dict[str, Any]) -> str:
            """Extract company name from GitHub issue."""
            # Try to find company name in issue title or body
            title = issue.get('title', '').lower()
            body = issue.get('body', '').lower()
            
            # Common patterns in job posts
            patterns = [
                'at', 'with', 'for', '@'
            ]
            
            for pattern in patterns:
                if pattern in title:
                    parts = title.split(pattern)
                    if len(parts) > 1:
                        return parts[1].strip().title()
            
            # Default to repository owner if no company found
            return issue.get('repository', {}).get('owner', {}).get('login', 'Unknown')
    
        def _extract_location_from_issue(self, issue: Dict[str, Any]) -> str:
            """Extract location from GitHub issue."""
            body = issue.get('body', '').lower()
            
            # Look for common location patterns
            patterns = [
                'location:', 'based in:', 'position location:'
            ]
            
            for pattern in patterns:
                if pattern in body:
                    idx = body.find(pattern)
                    end_idx = body.find('\n', idx)
                    if end_idx == -1:
                        end_idx = len(body)
                    return body[idx + len(pattern):end_idx].strip().title()
            return 'Remote/Unspecified'
    
        def _extract_company_from_wwr(self, entry: Dict[str, Any]) -> str:
            """Extract company name from WeWorkRemotely entry."""
            title = entry.get('title', '')
            if ':' in title:
                return title.split(':')[0].strip()
            return 'Unknown'
    
        def _extract_company_from_so(self, entry: Dict[str, Any]) -> str:
            """Extract company name from Stack Overflow entry."""
            title = entry.get('title', '')
            if 'at' in title:
                return title.split('at')[1].strip()
            return 'Unknown'
    
        def _extract_location_from_so(self, entry: Dict[str, Any]) -> str:
            """Extract location from Stack Overflow entry."""
            title = entry.get('title', '')
            if '(' in title and ')' in title:
                return title[title.find('(')+1:title.find(')')].strip()
            return 'Remote/Unspecified'
    
        async def process_and_save_jobs(self, jobs: List[Dict[str, Any]], user_id: int) -> List[Job]:
            """Process and save jobs to database."""
            saved_jobs = []
            
            for job_data in jobs:
                # Check if job already exists
                existing_job = self.db.query(Job).filter(
                    Job.source == job_data['source'],
                    Job.source_url == job_data['url'],
                    Job.user_id == user_id
                ).first()
                
                if not existing_job:
                    job = Job(
                        user_id=user_id,
                        title=job_data['title'],
                        company=job_data['company'],
                        location=job_data['location'],
                        description=job_data['description'],
                        source_url=job_data['url'],
                        salary_min=job_data['salary_min'],
                        salary_max=job_data['salary_max'],
                        source=job_data['source'],
                        remote_option=job_data['remote'],
                        posted_at=job_data['posted_at'],
                        metadata=job_data['original_data']
                    )
                    
                    self.db.add(job)
                    self.db.flush()
                    
                    # Calculate match score
                    match_score = await self.skill_matcher.calculate_match_score(job, user_id)
                    job.match_score = match_score
                    
                    # If high match score, send notification
                    if match_score >= 75:
                        await self.notification_service.send_job_match_notification(
                            user_id=user_id,
                            job_id=job.id,
                            match_score=match_score
                        )
                    
                    saved_jobs.append(job)
            
            self.db.commit()
            return saved_jobs
    