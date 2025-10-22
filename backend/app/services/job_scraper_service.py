from typing import Any, Dict, Optional, List
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models.job import Job
from app.schemas.job import JobCreate
from app.core.logging import get_logger
from app.services.job_data_normalizer import JobDataNormalizer
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
        self.normalizer = JobDataNormalizer()

        self.api_limits = {
            'adzuna': 1000,      # Free tier: 1000 requests/day
            'usajobs': 1000,     # Government API: generous limits
            'github_jobs': 500,  # No official limit, be conservative
            'remoteok': 100,     # Limited free usage
            'linkedin': 500,     # LinkedIn API rate limits
            'indeed': 1000,      # Indeed API limits
            'glassdoor': 500,    # Glassdoor API limits
        }
        self.api_delays = {
            'adzuna': 0.1,       # 0.1 seconds between requests
            'usajobs': 0.5,      # 0.5 seconds between requests
            'github_jobs': 1.0,  # 1 second between requests
            'remoteok': 2.0,     # 2 seconds between requests
            'linkedin': 1.0,     # LinkedIn API rate limiting
            'indeed': 0.5,       # Indeed API rate limiting
            'glassdoor': 1.5,    # Glassdoor API rate limiting
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

    async def search_linkedin(self, keywords: List[str], location: str, max_results: int = 20) -> List[JobCreate]:
        """Search LinkedIn Jobs API for job postings"""
        jobs = []
        if not self.settings.linkedin_api_access_token:
            logger.warning("LinkedIn API access token not configured. Skipping LinkedIn search.")
            return []

        headers = {
            "Authorization": f"Bearer {self.settings.linkedin_api_access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        # LinkedIn Jobs API parameters
        params = {
            "keywords": " ".join(keywords),
            "locationFallback": location,
            "count": min(max_results, 50),  # LinkedIn API max per request
            "start": 0,
            "sortBy": "DD"  # Sort by date descending
        }
        
        try:
            # LinkedIn Jobs Search API endpoint
            url = "https://api.linkedin.com/v2/jobSearch"
            response_data = await self._make_api_request(url, params, headers, api_name="linkedin")
            
            if "elements" in response_data:
                for job_data in response_data["elements"][:max_results]:
                    job = await self._parse_linkedin_job(job_data)
                    if job:
                        jobs.append(job)
            
            logger.info(f"Found {len(jobs)} jobs from LinkedIn API")
        except Exception as e:
            logger.error(f"Error searching LinkedIn API: {e}")
        return jobs

    async def _parse_linkedin_job(self, job_data: Dict[str, Any]) -> Optional[JobCreate]:
        """Parse LinkedIn job data into JobCreate schema"""
        try:
            # Extract salary information if available
            salary_range = None
            if "salaryInsights" in job_data:
                salary_info = job_data["salaryInsights"]
                if "baseCompensationRange" in salary_info:
                    comp_range = salary_info["baseCompensationRange"]
                    min_salary = comp_range.get("min", {}).get("amount")
                    max_salary = comp_range.get("max", {}).get("amount")
                    if min_salary and max_salary:
                        salary_range = f"${min_salary:,} - ${max_salary:,}"
            
            raw_data = {
                'company': job_data.get("companyDetails", {}).get("company", {}).get("name", ""),
                'title': job_data.get("title", ""),
                'location': job_data.get("formattedLocation", ""),
                'description': job_data.get("description", {}).get("text", ""),
                'salary_range': salary_range,
                'job_type': self._normalize_employment_type(job_data.get("employmentType", "FULL_TIME")),
                'remote_option': self._normalize_workplace_type(job_data.get("workplaceTypes", ["ON_SITE"])),
                'link': f"https://www.linkedin.com/jobs/view/{job_data.get('jobPostingId', '')}"
            }
            return self.normalizer.normalize_job_data(raw_data, "linkedin")
        except Exception as e:
            logger.error(f"Error parsing LinkedIn job: {e}")
            return None

    def _normalize_employment_type(self, employment_type: str) -> str:
        """Normalize LinkedIn employment type to standard format"""
        type_mapping = {
            "FULL_TIME": "full-time",
            "PART_TIME": "part-time",
            "CONTRACT": "contract",
            "TEMPORARY": "temporary",
            "INTERNSHIP": "internship",
            "VOLUNTEER": "volunteer"
        }
        return type_mapping.get(employment_type, "full-time")

    def _normalize_workplace_type(self, workplace_types: List[str]) -> str:
        """Normalize LinkedIn workplace type to remote option"""
        if "REMOTE" in workplace_types:
            return "remote"
        elif "HYBRID" in workplace_types:
            return "hybrid"
        else:
            return "onsite"

    def _extract_tech_stack_from_description(self, description: str) -> List[str]:
        """Extract technology skills from job description using keyword matching"""
        # Common technology keywords to look for
        tech_keywords = [
            # Programming Languages
            "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "php", "ruby", "swift", "kotlin",
            # Web Technologies
            "react", "angular", "vue", "node.js", "express", "django", "flask", "spring", "laravel",
            # Databases
            "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb",
            # Cloud Platforms
            "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "terraform",
            # Data & Analytics
            "pandas", "numpy", "tensorflow", "pytorch", "spark", "hadoop", "kafka",
            # DevOps & Tools
            "git", "jenkins", "gitlab", "github", "jira", "confluence"
        ]
        
        found_skills = []
        description_lower = description.lower()
        
        for skill in tech_keywords:
            if skill in description_lower:
                found_skills.append(skill.title())
        
        return list(set(found_skills))  # Remove duplicates

    async def search_indeed(self, keywords: List[str], location: str, max_results: int = 20) -> List[JobCreate]:
        """Search Indeed API for job postings"""
        jobs = []
        if not self.settings.indeed_publisher_id:
            logger.warning("Indeed Publisher ID not configured. Skipping Indeed search.")
            return []

        params = {
            "publisher": self.settings.indeed_publisher_id,
            "q": " ".join(keywords),
            "l": location,
            "limit": min(max_results, 25),  # Indeed API max per request
            "format": "json",
            "v": "2",  # API version
            "userip": "1.2.3.4",  # Required by Indeed API
            "useragent": "Mozilla/5.0 (compatible; Career-Copilot/1.0)"
        }
        
        try:
            url = "https://api.indeed.com/ads/apisearch"
            response_data = await self._make_api_request(url, params, api_name="indeed")
            
            if "results" in response_data:
                for job_data in response_data["results"][:max_results]:
                    job = self._parse_indeed_job(job_data)
                    if job:
                        jobs.append(job)
            
            logger.info(f"Found {len(jobs)} jobs from Indeed API")
        except Exception as e:
            logger.error(f"Error searching Indeed API: {e}")
        return jobs

    def _parse_indeed_job(self, job_data: Dict[str, Any]) -> Optional[JobCreate]:
        """Parse Indeed job data into JobCreate schema"""
        try:
            raw_data = {
                'company': job_data.get("company", ""),
                'title': job_data.get("jobtitle", ""),
                'location': f"{job_data.get('city', '')}, {job_data.get('state', '')}".strip(", "),
                'description': job_data.get("snippet", ""),
                'salary_range': job_data.get("salary"),
                'link': job_data.get("url", "")
            }
            return self.normalizer.normalize_job_data(raw_data, "indeed")
        except Exception as e:
            logger.error(f"Error parsing Indeed job: {e}")
            return None

    async def search_glassdoor(self, keywords: List[str], location: str, max_results: int = 20) -> List[JobCreate]:
        """Search Glassdoor API for job postings and company data"""
        jobs = []
        if not self.settings.glassdoor_partner_id or not self.settings.glassdoor_api_key:
            logger.warning("Glassdoor API credentials not configured. Skipping Glassdoor search.")
            return []

        params = {
            "t.p": self.settings.glassdoor_partner_id,
            "t.k": self.settings.glassdoor_api_key,
            "action": "jobs-prog",
            "q": " ".join(keywords),
            "l": location,
            "ps": min(max_results, 20),  # Glassdoor API max per request
            "format": "json",
            "v": "1"
        }
        
        try:
            url = "https://api.glassdoor.com/api/api.htm"
            response_data = await self._make_api_request(url, params, api_name="glassdoor")
            
            if "response" in response_data and "jobs" in response_data["response"]:
                for job_data in response_data["response"]["jobs"][:max_results]:
                    job = await self._parse_glassdoor_job(job_data)
                    if job:
                        jobs.append(job)
            
            logger.info(f"Found {len(jobs)} jobs from Glassdoor API")
        except Exception as e:
            logger.error(f"Error searching Glassdoor API: {e}")
        return jobs

    async def _parse_glassdoor_job(self, job_data: Dict[str, Any]) -> Optional[JobCreate]:
        """Parse Glassdoor job data into JobCreate schema with company enrichment"""
        try:
            # Extract salary information
            salary_range = None
            if "salaryEstimate" in job_data:
                salary_range = job_data["salaryEstimate"]
            elif "estimatedSalary" in job_data:
                est_salary = job_data["estimatedSalary"]
                if "min" in est_salary and "max" in est_salary:
                    salary_range = f"${est_salary['min']:,} - ${est_salary['max']:,}"
            
            # Enrich with company data if available
            company_name = job_data.get("employer", {}).get("name", "")
            company_info = await self._get_glassdoor_company_info(company_name)
            
            raw_data = {
                'company': company_name,
                'title': job_data.get("jobTitle", ""),
                'location': job_data.get("location", ""),
                'description': job_data.get("jobDescription", ""),
                'salary_range': salary_range,
                'link': job_data.get("jobUrl", ""),
                'requirements': company_info.get("industry", "") if company_info else ""
            }
            return self.normalizer.normalize_job_data(raw_data, "glassdoor")
        except Exception as e:
            logger.error(f"Error parsing Glassdoor job: {e}")
            return None

    async def _get_glassdoor_company_info(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Get additional company information from Glassdoor API"""
        try:
            params = {
                "t.p": self.settings.glassdoor_partner_id,
                "t.k": self.settings.glassdoor_api_key,
                "action": "employers",
                "q": company_name,
                "format": "json",
                "v": "1"
            }
            
            url = "https://api.glassdoor.com/api/api.htm"
            response_data = await self._make_api_request(url, params, api_name="glassdoor")
            
            if "response" in response_data and "employers" in response_data["response"]:
                employers = response_data["response"]["employers"]
                if employers:
                    return employers[0]  # Return first match
            
        except Exception as e:
            logger.debug(f"Could not fetch company info for {company_name}: {e}")
        
        return None

    async def search_all_apis(self, keywords: List[str], location: str, max_results: int = 20) -> List[JobCreate]:
        """Search all available job APIs concurrently"""
        logger.info(f"Searching all job APIs for '{keywords}' in '{location}'")
        tasks = []
        
        # Calculate results per API (distribute evenly across available APIs)
        num_apis = 7  # Total number of APIs
        results_per_api = max(1, max_results // num_apis)
        
        # Adzuna
        tasks.append(self.search_adzuna(keywords, location, results_per_api))
        # USAJobs (free government API)
        tasks.append(self.search_usajobs(keywords, location, results_per_api))
        # GitHub Jobs (if still available)
        tasks.append(self.search_github_jobs(keywords, location, results_per_api))
        # RemoteOK (for remote jobs, location is often ignored or assumed remote)
        tasks.append(self.search_remoteok(keywords, results_per_api))
        # LinkedIn Jobs
        tasks.append(self.search_linkedin(keywords, location, results_per_api))
        # Indeed Jobs
        tasks.append(self.search_indeed(keywords, location, results_per_api))
        # Glassdoor Jobs
        tasks.append(self.search_glassdoor(keywords, location, results_per_api))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_jobs = []
        api_names = ['Adzuna', 'USAJobs', 'GitHub Jobs', 'RemoteOK', 'LinkedIn', 'Indeed', 'Glassdoor']
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                logger.error(f"Error from {api_names[i]} API: {res}")
            else:
                all_jobs.extend(res)
                logger.info(f"Collected {len(res)} jobs from {api_names[i]}")

        # Use normalizer for intelligent deduplication and merging
        unique_jobs = self.normalizer.merge_duplicate_jobs(all_jobs)
        logger.info(f"API search completed: {len(unique_jobs)} unique jobs found after intelligent merging")
        return unique_jobs[:max_results]

    def _deduplicate_api_jobs(self, jobs: List[JobCreate]) -> List[JobCreate]:
        """Remove duplicate jobs from API results with intelligent merging across sources"""
        unique_jobs = []
        job_map = {}  # key -> job with best data
        source_priority = {
            'linkedin': 5,    # Highest priority - most comprehensive data
            'glassdoor': 4,   # High priority - good salary and company data
            'indeed': 3,      # Medium-high priority - good coverage
            'adzuna': 2,      # Medium priority - decent data quality
            'usajobs': 2,     # Medium priority - government jobs
            'github_jobs': 1, # Low priority - deprecated API
            'remoteok': 1     # Low priority - limited data
        }

        for job in jobs:
            # Create a normalized key for deduplication
            key = f"{job.title.lower().strip()}|{job.company.lower().strip()}"
            
            if key not in job_map:
                job_map[key] = job
            else:
                # Keep the job from the higher priority source, or merge data
                existing_job = job_map[key]
                existing_priority = source_priority.get(existing_job.source, 0)
                new_priority = source_priority.get(job.source, 0)
                
                if new_priority > existing_priority:
                    # Replace with higher priority source
                    job_map[key] = job
                elif new_priority == existing_priority:
                    # Merge data from same priority sources
                    merged_job = self._merge_job_data(existing_job, job)
                    job_map[key] = merged_job
                # If new priority is lower, keep existing job
                
                logger.debug(f"Duplicate job handled: {job.title} at {job.company} (sources: {existing_job.source}, {job.source})")
        
        unique_jobs = list(job_map.values())
        removed = len(jobs) - len(unique_jobs)
        if removed > 0:
            logger.info(f"Removed {removed} duplicate jobs from API results")
        return unique_jobs

    def _merge_job_data(self, job1: JobCreate, job2: JobCreate) -> JobCreate:
        """Merge data from two job postings of the same position"""
        # Use the more complete data from either job
        merged_data = {
            "company": job1.company or job2.company,
            "title": job1.title or job2.title,
            "location": job1.location or job2.location,
            "description": job1.description if len(job1.description or "") > len(job2.description or "") else job2.description,
            "salary_range": job1.salary_range or job2.salary_range,
            "job_type": job1.job_type or job2.job_type,
            "remote_option": job1.remote_option or job2.remote_option,
            "tech_stack": list(set((job1.tech_stack or []) + (job2.tech_stack or []))),  # Combine and deduplicate
            "requirements": job1.requirements or job2.requirements,
            "link": job1.link or job2.link,
            "source": f"{job1.source},{job2.source}"  # Track multiple sources
        }
        
        return JobCreate(**merged_data)

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
            raw_data = {
                'company': job_data.get("company", {}).get("display_name", ""),
                'title': job_data.get("title", "").replace("<b>", "").replace("</b>", ""),
                'location': job_data.get("location", {}).get("display_name", ""),
                'description': job_data.get("description", "").replace("<b>", "").replace("</b>", ""),
                'salary_range': f"{job_data.get('salary_min', 0)} - {job_data.get('salary_max', 0)}" if job_data.get("salary_min") else None,
                'job_type': job_data.get("contract_type", ""),
                'tech_stack': job_data.get("category", {}).get("tag", "").split(",") if job_data.get("category") else [],
                'link': job_data.get("redirect_url")
            }
            return self.normalizer.normalize_job_data(raw_data, "adzuna")
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
