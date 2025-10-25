"""
Job ingestion service that coordinates job discovery from multiple sources
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
settings = get_settings()
from app.models.user import User
from app.models.job import Job
from app.services.scraping import ScraperManager, ScrapingConfig
from app.services.rss_feed_service import RSSFeedService
from app.services.job_api_service import JobAPIService
from app.services.quota_manager import QuotaManager
# Removed circular import - JobService is now JobManagementSystem
from app.schemas.job import JobCreate


logger = logging.getLogger(__name__)


class JobIngestionService:
    """Service for ingesting jobs from multiple sources"""
    
    def __init__(self, db: Session):
        self.db = db
        # Job service will be injected when needed to avoid circular imports
        self.job_service = None
        self.scraper_manager = None
        self.quota_manager = QuotaManager()
        
    def _get_scraper_manager(self) -> ScraperManager:
        """Get or create scraper manager"""
        if not self.scraper_manager:
            config = ScrapingConfig(
                max_results_per_site=settings.SCRAPING_MAX_RESULTS_PER_SITE,
                max_concurrent_scrapers=settings.SCRAPING_MAX_CONCURRENT,
                enable_indeed=settings.SCRAPING_ENABLE_INDEED,
                enable_linkedin=settings.SCRAPING_ENABLE_LINKEDIN,
                rate_limit_min_delay=settings.SCRAPING_RATE_LIMIT_MIN,
                rate_limit_max_delay=settings.SCRAPING_RATE_LIMIT_MAX,
                deduplication_enabled=True
            )
            self.scraper_manager = ScraperManager(config)
        return self.scraper_manager
    
    async def ingest_jobs_for_user(
        self, 
        user_id: int, 
        max_jobs: int = 50
    ) -> Dict[str, Any]:
        """Ingest jobs for a specific user based on their preferences"""
        try:
            # Get user and preferences
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            logger.info(f"Starting multi-source job ingestion for user {user_id}")
            
            # Extract search parameters from user profile
            search_params = self._extract_search_params(user)
            
            # Track ingestion results
            ingestion_results = {
                'user_id': user_id,
                'started_at': datetime.utcnow(),
                'search_params': search_params,
                'sources_used': [],
                'jobs_by_source': {},
                'jobs_found': 0,
                'jobs_saved': 0,
                'duplicates_filtered': 0,
                'errors': []
            }
            
            # Determine job category for optimal source selection
            job_category = self._determine_job_category(search_params)
            
            # Get all jobs from multiple sources
            all_jobs = []
            
            # Source 1: RSS Feeds
            rss_jobs = await self._ingest_from_rss_feeds(search_params, max_jobs // 4)
            if rss_jobs:
                all_jobs.extend(rss_jobs)
                ingestion_results['sources_used'].append('rss_feeds')
                ingestion_results['jobs_by_source']['rss_feeds'] = len(rss_jobs)
            
            # Source 2: Job APIs
            api_jobs = await self._ingest_from_apis(search_params, job_category, max_jobs // 4)
            if api_jobs:
                all_jobs.extend(api_jobs)
                ingestion_results['sources_used'].append('job_apis')
                ingestion_results['jobs_by_source']['job_apis'] = len(api_jobs)
            
            # Source 3: Web Scraping (fallback)
            if len(all_jobs) < max_jobs // 2:  # Only scrape if we don't have enough jobs
                scraper_jobs = await self._ingest_from_scrapers(search_params, max_jobs // 2)
                if scraper_jobs:
                    all_jobs.extend(scraper_jobs)
                    ingestion_results['sources_used'].append('web_scraping')
                    ingestion_results['jobs_by_source']['web_scraping'] = len(scraper_jobs)
            
            ingestion_results['jobs_found'] = len(all_jobs)
            
            # Filter out jobs that already exist for this user
            new_jobs = await self._filter_existing_jobs(user_id, all_jobs)
            ingestion_results['duplicates_filtered'] = len(all_jobs) - len(new_jobs)
            
            # Save new jobs to database
            saved_jobs = []
            for job_data in new_jobs:
                try:
                    # Add user_id to job data
                    job_dict = job_data.model_dump()
                    job_dict['user_id'] = user_id
                    
                    # Create job in database directly
                    from app.models.job import Job
                    job = Job(**job_dict)
                    self.db.add(job)
                    self.db.flush()
                    self.db.refresh(job)
                    saved_jobs.append(job)
                    
                except Exception as e:
                    error_msg = f"Error saving job '{job_data.title}' at '{job_data.company}': {str(e)}"
                    logger.error(error_msg)
                    ingestion_results['errors'].append(error_msg)
            
            ingestion_results['jobs_saved'] = len(saved_jobs)
            ingestion_results['completed_at'] = datetime.utcnow()
            
            # Update user's last ingestion timestamp
            user.profile = user.profile or {}
            user.profile['last_job_ingestion'] = datetime.utcnow().isoformat()
            self.db.commit()
            
            logger.info(f"Multi-source job ingestion completed for user {user_id}: "
                       f"{ingestion_results['jobs_saved']} new jobs saved from "
                       f"{len(ingestion_results['sources_used'])} sources")
            
            return ingestion_results
            
        except Exception as e:
            logger.error(f"Job ingestion failed for user {user_id}: {str(e)}")
            raise
    
    def _extract_search_params(self, user: User) -> Dict[str, List[str]]:
        """Extract search parameters from user profile"""
        profile = user.profile or {}
        
        # Default keywords based on user skills or generic terms
        keywords = []
        
        # Use user skills as keywords
        user_skills = profile.get('skills', [])
        if user_skills:
            # Combine skills into search terms
            keywords.extend(user_skills[:3])  # Use top 3 skills
        
        # Add job titles from preferences
        preferred_titles = profile.get('preferences', {}).get('job_titles', [])
        keywords.extend(preferred_titles)
        
        # Default keywords if none specified
        if not keywords:
            keywords = ['software engineer', 'developer', 'programmer']
        
        # Locations
        locations = []
        
        # Use preferred locations
        preferred_locations = profile.get('locations', [])
        locations.extend(preferred_locations)
        
        # Add remote as an option
        if not any('remote' in loc.lower() for loc in locations):
            locations.append('remote')
        
        # Default location if none specified
        if not locations:
            locations = ['remote', 'united states']
        
        return {
            'keywords': keywords[:5],  # Limit to 5 keywords
            'locations': locations[:3]  # Limit to 3 locations
        }
    
    async def _filter_existing_jobs(
        self, 
        user_id: int, 
        jobs: List[JobCreate]
    ) -> List[JobCreate]:
        """Filter out jobs that already exist for the user"""
        if not jobs:
            return []
        
        # Get existing jobs for user from last 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        existing_jobs = self.db.query(Job).filter(
            Job.user_id == user_id,
            Job.created_at >= cutoff_date
        ).all()
        
        # Create set of existing job keys
        existing_keys = set()
        for job in existing_jobs:
            key = self._create_job_key(job.title, job.company, job.location)
            existing_keys.add(key)
        
        # Filter new jobs
        new_jobs = []
        for job in jobs:
            key = self._create_job_key(job.title, job.company, job.location)
            if key not in existing_keys:
                new_jobs.append(job)
        
        logger.info(f"Filtered {len(jobs) - len(new_jobs)} existing jobs")
        return new_jobs
    
    def _create_job_key(self, title: str, company: str, location: str = None) -> str:
        """Create a normalized key for job comparison"""
        # Normalize text
        title = ' '.join(title.lower().strip().split()) if title else ""
        company = ' '.join(company.lower().strip().split()) if company else ""
        location = ' '.join(location.lower().strip().split()) if location else ""
        
        return f"{title}|{company}|{location}"
    
    async def test_job_ingestion(self, keywords: str = "python developer", location: str = "remote") -> Dict[str, Any]:
        """Test job ingestion functionality"""
        try:
            logger.info(f"Testing job ingestion with '{keywords}' in '{location}'")
            
            scraper_manager = self._get_scraper_manager()
            
            # Test scraper availability
            scraper_tests = await scraper_manager.test_scrapers()
            
            # Perform a small test search
            jobs = await scraper_manager.search_all_sites(
                keywords=keywords,
                location=location,
                max_total_results=10
            )
            
            return {
                'scraper_tests': scraper_tests,
                'test_search': {
                    'keywords': keywords,
                    'location': location,
                    'jobs_found': len(jobs),
                    'sample_jobs': [
                        {
                            'title': job.title,
                            'company': job.company,
                            'location': job.location,
                            'source': job.source
                        }
                        for job in jobs[:3]  # Show first 3 jobs
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Job ingestion test failed: {str(e)}")
            return {
                'error': str(e),
                'scraper_tests': {},
                'test_search': {}
            }
    
    def _determine_job_category(self, search_params: Dict[str, List[str]]) -> str:
        """Determine job category based on search parameters"""
        keywords = ' '.join(search_params.get('keywords', [])).lower()
        
        if any(term in keywords for term in ['government', 'federal', 'public', 'civil']):
            return 'government_jobs'
        elif any(term in keywords for term in ['remote', 'work from home']):
            return 'remote_jobs'
        elif any(term in keywords for term in ['startup', 'early stage']):
            return 'startup_jobs'
        elif any(term in keywords for term in ['enterprise', 'fortune', 'large company']):
            return 'enterprise_jobs'
        elif any(term in keywords for term in ['developer', 'engineer', 'programmer', 'software', 'tech']):
            return 'tech_jobs'
        else:
            return 'general_jobs'
    
    async def _ingest_from_rss_feeds(
        self, 
        search_params: Dict[str, List[str]], 
        max_jobs: int
    ) -> List[JobCreate]:
        """Ingest jobs from RSS feeds"""
        if not self.quota_manager.can_make_request('rss_feeds'):
            logger.warning("RSS feeds quota exhausted, skipping")
            return []
        
        try:
            async with RSSFeedService() as rss_service:
                # Get default RSS feeds
                feed_urls = rss_service.get_default_feed_urls()
                
                # Add company-specific feeds if user has preferred companies
                profile = search_params.get('profile', {})
                preferred_companies = profile.get('preferences', {}).get('companies', [])
                if preferred_companies:
                    company_domains = [f"{company.lower().replace(' ', '')}.com" for company in preferred_companies]
                    discovered_feeds = await rss_service.discover_company_feeds(company_domains)
                    feed_urls.extend(discovered_feeds)
                
                # Monitor feeds
                jobs = await rss_service.monitor_feeds(
                    feed_urls=feed_urls[:10],  # Limit to 10 feeds
                    keywords=search_params.get('keywords', []),
                    max_concurrent=3
                )
                
                # Record quota usage
                self.quota_manager.record_request('rss_feeds', success=True)
                
                logger.info(f"Ingested {len(jobs)} jobs from RSS feeds")
                return jobs[:max_jobs]
                
        except Exception as e:
            logger.error(f"Error ingesting from RSS feeds: {e}")
            self.quota_manager.record_request('rss_feeds', success=False)
            return []
    
    async def _ingest_from_apis(
        self, 
        search_params: Dict[str, List[str]], 
        job_category: str,
        max_jobs: int
    ) -> List[JobCreate]:
        """Ingest jobs from external APIs"""
        # Get optimal API sources based on category and quota
        available_apis = self.quota_manager.get_fallback_sources(job_category)
        api_sources = [source for source in available_apis if 'api' in source or source in ['usajobs', 'github_jobs', 'remoteok']]
        
        if not api_sources:
            logger.warning("No API sources available")
            return []
        
        try:
            async with JobAPIService() as api_service:
                all_jobs = []
                
                for keywords in search_params['keywords'][:2]:  # Limit to 2 keywords
                    for location in search_params['locations'][:2]:  # Limit to 2 locations
                        try:
                            # Search all available APIs
                            jobs = await api_service.search_all_apis(
                                keywords=keywords,
                                location=location,
                                max_results=max_jobs // (len(search_params['keywords']) * len(search_params['locations']))
                            )
                            
                            all_jobs.extend(jobs)
                            
                            # Record successful requests for each API
                            for api_name in ['usajobs', 'github_jobs', 'remoteok']:
                                if self.quota_manager.can_make_request(api_name):
                                    self.quota_manager.record_request(api_name, success=True)
                            
                        except Exception as e:
                            logger.error(f"Error searching APIs for '{keywords}' in '{location}': {e}")
                            # Record failures
                            for api_name in api_sources:
                                self.quota_manager.record_request(api_name, success=False)
                
                logger.info(f"Ingested {len(all_jobs)} jobs from APIs")
                return all_jobs[:max_jobs]
                
        except Exception as e:
            logger.error(f"Error ingesting from APIs: {e}")
            return []
    
    async def _ingest_from_scrapers(
        self, 
        search_params: Dict[str, List[str]], 
        max_jobs: int
    ) -> List[JobCreate]:
        """Ingest jobs from web scrapers (fallback method)"""
        # Check if scraping is available
        scraper_sources = ['indeed_scraper', 'linkedin_scraper']
        available_scrapers = [s for s in scraper_sources if self.quota_manager.can_make_request(s)]
        
        if not available_scrapers:
            logger.warning("No scrapers available due to quota limits")
            return []
        
        try:
            scraper_manager = self._get_scraper_manager()
            all_jobs = []
            
            for keywords in search_params['keywords'][:2]:  # Limit keywords
                for location in search_params['locations'][:2]:  # Limit locations
                    try:
                        logger.info(f"Scraping for '{keywords}' in '{location}'")
                        
                        jobs = await scraper_manager.search_all_sites(
                            keywords=keywords,
                            location=location,
                            max_total_results=max_jobs // (len(search_params['keywords']) * len(search_params['locations']))
                        )
                        
                        all_jobs.extend(jobs)
                        
                        # Record scraper usage
                        for scraper in available_scrapers:
                            self.quota_manager.record_request(scraper, success=True)
                        
                        # Add delay between scraping sessions
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        error_msg = f"Error scraping '{keywords}' in '{location}': {str(e)}"
                        logger.error(error_msg)
                        
                        # Record failures
                        for scraper in available_scrapers:
                            self.quota_manager.record_request(scraper, success=False)
            
            logger.info(f"Scraped {len(all_jobs)} jobs from web sources")
            return all_jobs[:max_jobs]
            
        except Exception as e:
            logger.error(f"Error ingesting from scrapers: {e}")
            return []
    
    async def get_ingestion_stats(self, user_id: int) -> Dict[str, Any]:
        """Get ingestion statistics for a user"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {'error': 'User not found'}
            
            profile = user.profile or {}
            
            # Get job counts by source
            job_counts = self.db.query(Job.source, self.db.func.count(Job.id)).filter(
                Job.user_id == user_id
            ).group_by(Job.source).all()
            
            # Get recent jobs (last 7 days)
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            recent_jobs_count = self.db.query(Job).filter(
                Job.user_id == user_id,
                Job.created_at >= recent_cutoff
            ).count()
            
            return {
                'user_id': user_id,
                'last_ingestion': profile.get('last_job_ingestion'),
                'total_jobs': sum(count for _, count in job_counts),
                'jobs_by_source': dict(job_counts),
                'recent_jobs_count': recent_jobs_count,
                'available_scrapers': self._get_scraper_manager().get_available_scrapers(),
                'quota_status': self.quota_manager.get_quota_summary(),
                'health_status': self.quota_manager.get_health_status()
            }
            
        except Exception as e:
            logger.error(f"Error getting ingestion stats for user {user_id}: {str(e)}")
            return {'error': str(e)}
    
    async def test_all_sources(self) -> Dict[str, Any]:
        """Test all job ingestion sources"""
        test_results = {
            'rss_feeds': {},
            'job_apis': {},
            'web_scrapers': {},
            'quota_status': self.quota_manager.get_quota_summary()
        }
        
        # Test RSS feeds
        try:
            async with RSSFeedService() as rss_service:
                feed_urls = rss_service.get_default_feed_urls()[:3]  # Test first 3 feeds
                jobs = await rss_service.monitor_feeds(feed_urls, ['software engineer'], max_concurrent=2)
                test_results['rss_feeds'] = {
                    'status': 'success',
                    'feeds_tested': len(feed_urls),
                    'jobs_found': len(jobs)
                }
        except Exception as e:
            test_results['rss_feeds'] = {'status': 'error', 'error': str(e)}
        
        # Test job APIs
        try:
            async with JobAPIService() as api_service:
                api_tests = await api_service.test_apis()
                test_results['job_apis'] = api_tests
        except Exception as e:
            test_results['job_apis'] = {'status': 'error', 'error': str(e)}
        
        # Test web scrapers
        try:
            scraper_manager = self._get_scraper_manager()
            scraper_tests = await scraper_manager.test_scrapers()
            test_results['web_scrapers'] = scraper_tests
        except Exception as e:
            test_results['web_scrapers'] = {'status': 'error', 'error': str(e)}
        
        return test_results