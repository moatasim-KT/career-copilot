"""
Job API service for integrating with external job APIs
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from app.schemas.job import JobCreate
from app.core.config import settings


logger = logging.getLogger(__name__)


class JobAPIService:
    """Service for integrating with external job APIs"""
    
    def __init__(self):
        self.session = None
        self.api_quotas = {}
        self.last_request_times = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers=self._get_headers()
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.aclose()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            'User-Agent': 'Career-Copilot Job Aggregator 1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
    
    async def _make_api_request(
        self, 
        url: str, 
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        api_name: str = "unknown"
    ) -> Optional[Dict[str, Any]]:
        """Make a rate-limited API request with quota management"""
        try:
            # Check quota limits
            if not self._check_quota(api_name):
                logger.warning(f"API quota exceeded for {api_name}")
                return None
            
            # Apply rate limiting
            await self._apply_rate_limit(api_name)
            
            # Prepare request
            request_headers = self._get_headers()
            if headers:
                request_headers.update(headers)
            
            logger.debug(f"Making API request to {api_name}: {url}")
            
            response = await self.session.get(url, params=params, headers=request_headers)
            response.raise_for_status()
            
            # Update quota tracking
            self._update_quota(api_name)
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for {api_name} API: {e.response.status_code}")
            if e.response.status_code == 429:  # Rate limited
                self._handle_rate_limit(api_name)
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error for {api_name} API: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {api_name} API: {e}")
            return None
    
    def _check_quota(self, api_name: str) -> bool:
        """Check if API quota allows more requests"""
        quota_info = self.api_quotas.get(api_name, {})
        
        # Reset daily quotas
        today = datetime.utcnow().date()
        if quota_info.get('date') != today:
            quota_info = {'date': today, 'requests': 0, 'blocked_until': None}
            self.api_quotas[api_name] = quota_info
        
        # Check if blocked
        if quota_info.get('blocked_until'):
            if datetime.utcnow() < quota_info['blocked_until']:
                return False
            else:
                quota_info['blocked_until'] = None
        
        # Check daily limits
        daily_limits = {
            'adzuna': 1000,      # Free tier: 1000/month
            'jobspresso': 100,   # Free tier: 100/day
            'usajobs': 1000,     # Government API: generous limits
            'github_jobs': 500,  # No official limit, be conservative
            'remoteok': 100,     # No official API, be very conservative
        }
        
        limit = daily_limits.get(api_name, 100)
        return quota_info.get('requests', 0) < limit
    
    def _update_quota(self, api_name: str):
        """Update quota tracking after successful request"""
        if api_name not in self.api_quotas:
            self.api_quotas[api_name] = {'date': datetime.utcnow().date(), 'requests': 0}
        
        self.api_quotas[api_name]['requests'] += 1
        self.last_request_times[api_name] = datetime.utcnow()
    
    async def _apply_rate_limit(self, api_name: str):
        """Apply rate limiting between requests"""
        last_request = self.last_request_times.get(api_name)
        if not last_request:
            return
        
        # Rate limits per API
        rate_limits = {
            'adzuna': 1.0,       # 1 second between requests
            'jobspresso': 2.0,   # 2 seconds between requests
            'usajobs': 0.5,      # 0.5 seconds between requests
            'github_jobs': 1.0,  # 1 second between requests
            'remoteok': 3.0,     # 3 seconds between requests (be respectful)
        }
        
        min_interval = rate_limits.get(api_name, 1.0)
        elapsed = (datetime.utcnow() - last_request).total_seconds()
        
        if elapsed < min_interval:
            wait_time = min_interval - elapsed
            logger.debug(f"Rate limiting {api_name}: waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
    
    def _handle_rate_limit(self, api_name: str):
        """Handle rate limit responses"""
        # Block API for 1 hour
        self.api_quotas[api_name] = self.api_quotas.get(api_name, {})
        self.api_quotas[api_name]['blocked_until'] = datetime.utcnow() + timedelta(hours=1)
        logger.warning(f"API {api_name} blocked for 1 hour due to rate limiting")
    
    async def search_adzuna(
        self, 
        keywords: str, 
        location: str = "", 
        max_results: int = 50
    ) -> List[JobCreate]:
        """Search jobs using Adzuna API"""
        jobs = []
        
        try:
            # Adzuna requires API key and app ID (would need to be configured)
            # For now, return empty list as this requires API credentials
            logger.info("Adzuna API integration requires API credentials")
            return jobs
            
            # Example implementation (commented out):
            # app_id = settings.ADZUNA_APP_ID
            # api_key = settings.ADZUNA_API_KEY
            # 
            # if not app_id or not api_key:
            #     logger.warning("Adzuna API credentials not configured")
            #     return jobs
            # 
            # params = {
            #     'app_id': app_id,
            #     'app_key': api_key,
            #     'what': keywords,
            #     'where': location,
            #     'results_per_page': min(max_results, 50),
            #     'content-type': 'application/json'
            # }
            # 
            # url = "https://api.adzuna.com/v1/api/jobs/us/search/1"
            # response = await self._make_api_request(url, params, api_name="adzuna")
            # 
            # if response and 'results' in response:
            #     for job_data in response['results']:
            #         job = self._parse_adzuna_job(job_data)
            #         if job:
            #             jobs.append(job)
            
        except Exception as e:
            logger.error(f"Error searching Adzuna API: {e}")
        
        return jobs
    
    async def search_usajobs(
        self, 
        keywords: str, 
        location: str = "", 
        max_results: int = 50
    ) -> List[JobCreate]:
        """Search jobs using USAJobs API (free government API)"""
        jobs = []
        
        try:
            params = {
                'Keyword': keywords,
                'LocationName': location,
                'ResultsPerPage': min(max_results, 500),
                'SortField': 'OpenDate',
                'SortDirection': 'Desc'
            }
            
            headers = {
                'Host': 'data.usajobs.gov',
                'User-Agent': 'career-copilot@example.com'  # USAJobs requires email in User-Agent
            }
            
            url = "https://data.usajobs.gov/api/search"
            response = await self._make_api_request(url, params, headers, "usajobs")
            
            if response and 'SearchResult' in response and 'SearchResultItems' in response['SearchResult']:
                for item in response['SearchResult']['SearchResultItems']:
                    job = self._parse_usajobs_job(item)
                    if job:
                        jobs.append(job)
            
            logger.info(f"Found {len(jobs)} jobs from USAJobs API")
            
        except Exception as e:
            logger.error(f"Error searching USAJobs API: {e}")
        
        return jobs
    
    async def search_github_jobs(
        self, 
        keywords: str, 
        location: str = "", 
        max_results: int = 50
    ) -> List[JobCreate]:
        """Search jobs using GitHub Jobs API (deprecated but may still work)"""
        jobs = []
        
        try:
            params = {
                'description': keywords,
                'location': location,
                'full_time': 'true'
            }
            
            url = "https://jobs.github.com/positions.json"
            response = await self._make_api_request(url, params, api_name="github_jobs")
            
            if response and isinstance(response, list):
                for job_data in response[:max_results]:
                    job = self._parse_github_job(job_data)
                    if job:
                        jobs.append(job)
            
            logger.info(f"Found {len(jobs)} jobs from GitHub Jobs API")
            
        except Exception as e:
            logger.error(f"Error searching GitHub Jobs API: {e}")
        
        return jobs
    
    async def search_remoteok(
        self, 
        keywords: str, 
        max_results: int = 50
    ) -> List[JobCreate]:
        """Search remote jobs using RemoteOK API"""
        jobs = []
        
        try:
            # RemoteOK has a simple JSON API
            url = "https://remoteok.io/api"
            response = await self._make_api_request(url, api_name="remoteok")
            
            if response and isinstance(response, list):
                # Filter jobs by keywords
                keyword_list = keywords.lower().split()
                
                for job_data in response[1:]:  # First item is metadata
                    if self._matches_keywords_remoteok(job_data, keyword_list):
                        job = self._parse_remoteok_job(job_data)
                        if job:
                            jobs.append(job)
                            if len(jobs) >= max_results:
                                break
            
            logger.info(f"Found {len(jobs)} jobs from RemoteOK API")
            
        except Exception as e:
            logger.error(f"Error searching RemoteOK API: {e}")
        
        return jobs
    
    def _parse_usajobs_job(self, item: Dict[str, Any]) -> Optional[JobCreate]:
        """Parse USAJobs API response item"""
        try:
            job_data = item.get('MatchedObjectDescriptor', {})
            
            title = job_data.get('PositionTitle', '')
            company = job_data.get('OrganizationName', 'U.S. Government')
            location = self._extract_usajobs_location(job_data)
            description = job_data.get('QualificationSummary', '') or job_data.get('UserArea', {}).get('Details', {}).get('JobSummary', '')
            
            # Extract salary
            salary_info = self._extract_usajobs_salary(job_data)
            
            return JobCreate(
                title=title,
                company=company,
                location=location,
                description=description,
                salary_min=salary_info.get('min'),
                salary_max=salary_info.get('max'),
                currency="USD",
                application_url=job_data.get('PositionURI', ''),
                source="api",
                requirements={
                    'security_clearance': job_data.get('SecurityClearanceRequired', ''),
                    'grade': job_data.get('JobGrade', [{}])[0].get('Code', '') if job_data.get('JobGrade') else ''
                },
                tags=['government', 'federal']
            )
            
        except Exception as e:
            logger.error(f"Error parsing USAJobs job: {e}")
            return None
    
    def _parse_github_job(self, job_data: Dict[str, Any]) -> Optional[JobCreate]:
        """Parse GitHub Jobs API response item"""
        try:
            return JobCreate(
                title=job_data.get('title', ''),
                company=job_data.get('company', ''),
                location=job_data.get('location', ''),
                description=job_data.get('description', ''),
                application_url=job_data.get('url', ''),
                source="api",
                requirements={},
                tags=['tech', 'remote' if 'remote' in job_data.get('location', '').lower() else '']
            )
            
        except Exception as e:
            logger.error(f"Error parsing GitHub job: {e}")
            return None
    
    def _parse_remoteok_job(self, job_data: Dict[str, Any]) -> Optional[JobCreate]:
        """Parse RemoteOK API response item"""
        try:
            # Extract tags
            tags = job_data.get('tags', [])
            if isinstance(tags, list):
                tags = [tag for tag in tags if isinstance(tag, str)]
            else:
                tags = []
            
            # Extract salary
            salary_min = job_data.get('salary_min')
            salary_max = job_data.get('salary_max')
            
            return JobCreate(
                title=job_data.get('position', ''),
                company=job_data.get('company', ''),
                location=job_data.get('location', 'Remote'),
                description=job_data.get('description', ''),
                salary_min=int(salary_min) if salary_min else None,
                salary_max=int(salary_max) if salary_max else None,
                currency="USD",
                application_url=job_data.get('url', ''),
                source="api",
                requirements={'skills': tags},
                tags=['remote'] + tags[:5]  # Limit tags
            )
            
        except Exception as e:
            logger.error(f"Error parsing RemoteOK job: {e}")
            return None
    
    def _extract_usajobs_location(self, job_data: Dict[str, Any]) -> str:
        """Extract location from USAJobs data"""
        locations = job_data.get('PositionLocation', [])
        if locations and isinstance(locations, list):
            location = locations[0]
            city = location.get('CityName', '')
            state = location.get('StateCode', '')
            return f"{city}, {state}".strip(', ')
        return ""
    
    def _extract_usajobs_salary(self, job_data: Dict[str, Any]) -> Dict[str, Optional[int]]:
        """Extract salary from USAJobs data"""
        salary_info = {"min": None, "max": None}
        
        remuneration = job_data.get('PositionRemuneration', [])
        if remuneration and isinstance(remuneration, list):
            salary_data = remuneration[0]
            min_range = salary_data.get('MinimumRange')
            max_range = salary_data.get('MaximumRange')
            
            try:
                if min_range:
                    salary_info['min'] = int(float(min_range))
                if max_range:
                    salary_info['max'] = int(float(max_range))
            except (ValueError, TypeError):
                pass
        
        return salary_info
    
    def _matches_keywords_remoteok(self, job_data: Dict[str, Any], keywords: List[str]) -> bool:
        """Check if RemoteOK job matches keywords"""
        if not keywords:
            return True
        
        searchable_text = f"{job_data.get('position', '')} {job_data.get('company', '')} {job_data.get('description', '')}".lower()
        
        return any(keyword in searchable_text for keyword in keywords)
    
    async def search_all_apis(
        self, 
        keywords: str, 
        location: str = "", 
        max_results: int = 100
    ) -> List[JobCreate]:
        """Search all available job APIs concurrently"""
        logger.info(f"Searching all job APIs for '{keywords}' in '{location}'")
        
        # Create tasks for each API
        tasks = []
        
        # USAJobs (free government API)
        tasks.append(self.search_usajobs(keywords, location, max_results // 4))
        
        # GitHub Jobs (if still available)
        tasks.append(self.search_github_jobs(keywords, location, max_results // 4))
        
        # RemoteOK (for remote jobs)
        if not location or 'remote' in location.lower():
            tasks.append(self.search_remoteok(keywords, max_results // 4))
        
        # Adzuna (requires API key)
        tasks.append(self.search_adzuna(keywords, location, max_results // 4))
        
        # Execute all searches concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect all jobs
        all_jobs = []
        api_names = ['USAJobs', 'GitHub Jobs', 'RemoteOK', 'Adzuna']
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error with {api_names[i]} API: {result}")
                continue
            
            if isinstance(result, list):
                all_jobs.extend(result)
                logger.info(f"Collected {len(result)} jobs from {api_names[i]}")
        
        # Remove duplicates
        unique_jobs = self._deduplicate_api_jobs(all_jobs)
        
        logger.info(f"API search completed: {len(unique_jobs)} unique jobs found")
        return unique_jobs[:max_results]
    
    def _deduplicate_api_jobs(self, jobs: List[JobCreate]) -> List[JobCreate]:
        """Remove duplicate jobs from API results"""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            # Create deduplication key
            key = f"{job.title.lower().strip()}|{job.company.lower().strip()}"
            
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        removed = len(jobs) - len(unique_jobs)
        if removed > 0:
            logger.info(f"Removed {removed} duplicate jobs from API results")
        
        return unique_jobs
    
    def get_quota_status(self) -> Dict[str, Any]:
        """Get current quota status for all APIs"""
        status = {}
        
        for api_name in ['adzuna', 'jobspresso', 'usajobs', 'github_jobs', 'remoteok']:
            quota_info = self.api_quotas.get(api_name, {})
            status[api_name] = {
                'requests_today': quota_info.get('requests', 0),
                'blocked_until': quota_info.get('blocked_until'),
                'available': self._check_quota(api_name)
            }
        
        return status
    
    async def test_apis(self) -> Dict[str, Any]:
        """Test all job APIs with a simple search"""
        test_results = {}
        
        # Test each API individually
        apis_to_test = [
            ('usajobs', self.search_usajobs),
            ('github_jobs', self.search_github_jobs),
            ('remoteok', self.search_remoteok),
            ('adzuna', self.search_adzuna)
        ]
        
        for api_name, search_func in apis_to_test:
            try:
                logger.info(f"Testing {api_name} API")
                
                if api_name == 'remoteok':
                    jobs = await search_func("python", 5)
                else:
                    jobs = await search_func("software engineer", "remote", 5)
                
                test_results[api_name] = {
                    'status': 'success',
                    'jobs_found': len(jobs),
                    'sample_job': {
                        'title': jobs[0].title,
                        'company': jobs[0].company,
                        'location': jobs[0].location
                    } if jobs else None
                }
                
            except Exception as e:
                test_results[api_name] = {
                    'status': 'error',
                    'error': str(e),
                    'jobs_found': 0
                }
        
        return test_results