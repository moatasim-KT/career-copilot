"""
Job ingestion API endpoints
"""

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.job_ingestion_service import JobIngestionService
from app.services.rss_feed_service import RSSFeedService
from app.services.job_api_service import JobAPIService
from app.services.quota_manager import QuotaManager
from app.services import job_ingestion as job_ingestion_tasks


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ingest", response_model=Dict[str, Any])
async def trigger_job_ingestion(
    background_tasks: BackgroundTasks,
    max_jobs: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger job ingestion for the current user
    """
    try:
        logger.info(f"Triggering job ingestion for user {current_user.id}")
        
        # Add background task
        background_tasks.add_task(
            job_ingestion_tasks.ingest_jobs_for_user.delay,
            current_user.id,
            max_jobs
        )
        
        return {
            "message": "Job ingestion started",
            "user_id": current_user.id,
            "max_jobs": max_jobs,
            "status": "queued"
        }
        
    except Exception as e:
        logger.error(f"Error triggering job ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/immediate", response_model=Dict[str, Any])
async def immediate_job_ingestion(
    max_jobs: int = 25,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform immediate job ingestion for the current user (synchronous)
    """
    try:
        logger.info(f"Starting immediate job ingestion for user {current_user.id}")
        
        # Create ingestion service
        ingestion_service = JobIngestionService(db)
        
        # Perform ingestion
        result = await ingestion_service.ingest_jobs_for_user(
            user_id=current_user.id,
            max_jobs=max_jobs
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in immediate job ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=Dict[str, Any])
async def get_ingestion_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get job ingestion statistics for the current user
    """
    try:
        ingestion_service = JobIngestionService(db)
        stats = await ingestion_service.get_ingestion_stats(current_user.id)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting ingestion stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test", response_model=Dict[str, Any])
async def test_job_ingestion(
    keywords: str = "python developer",
    location: str = "remote",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test job ingestion functionality
    """
    try:
        logger.info(f"Testing job ingestion for user {current_user.id}")
        
        ingestion_service = JobIngestionService(db)
        result = await ingestion_service.test_job_ingestion(keywords, location)
        
        return result
        
    except Exception as e:
        logger.error(f"Error testing job ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/ingest-all", response_model=Dict[str, Any])
async def trigger_ingestion_for_all_users(
    background_tasks: BackgroundTasks,
    max_jobs_per_user: int = 50,
    user_ids: Optional[List[int]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger job ingestion for all users (admin only)
    """
    # Note: In a real application, you'd want to add admin role checking here
    try:
        logger.info("Triggering job ingestion for all users")
        
        # Add background task
        background_tasks.add_task(
            job_ingestion_tasks.ingest_jobs.delay,
            user_ids,
            max_jobs_per_user
        )
        
        return {
            "message": "Job ingestion started for all users",
            "max_jobs_per_user": max_jobs_per_user,
            "user_ids": user_ids,
            "status": "queued"
        }
        
    except Exception as e:
        logger.error(f"Error triggering ingestion for all users: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scrapers/status", response_model=Dict[str, Any])
async def get_scraper_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get status of available scrapers
    """
    try:
        ingestion_service = JobIngestionService(db)
        scraper_manager = ingestion_service._get_scraper_manager()
        
        # Test scrapers
        scraper_tests = await scraper_manager.test_scrapers()
        
        return {
            "available_scrapers": scraper_manager.get_available_scrapers(),
            "scraper_tests": scraper_tests,
            "all_scrapers_working": all(scraper_tests.values())
        }
        
    except Exception as e:
        logger.error(f"Error getting scraper status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-all-sources", response_model=Dict[str, Any])
async def test_all_sources(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test all job ingestion sources (RSS, APIs, scrapers)"""
    try:
        service = JobIngestionService(db)
        result = await service.test_all_sources()
        return result
    except Exception as e:
        logger.error(f"All sources test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rss-feeds/test", response_model=Dict[str, Any])
async def test_rss_feeds(
    keywords: str = "software engineer",
    max_feeds: int = 3,
    current_user: User = Depends(get_current_user)
):
    """Test RSS feed monitoring"""
    try:
        async with RSSFeedService() as rss_service:
            feed_urls = rss_service.get_default_feed_urls()[:max_feeds]
            jobs = await rss_service.monitor_feeds(
                feed_urls=feed_urls,
                keywords=[keywords],
                max_concurrent=2
            )
            
            return {
                'feeds_tested': len(feed_urls),
                'jobs_found': len(jobs),
                'sample_jobs': [
                    {
                        'title': job.title,
                        'company': job.company,
                        'location': job.location,
                        'source': job.source
                    }
                    for job in jobs[:5]
                ]
            }
    except Exception as e:
        logger.error(f"RSS feed test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/apis/test", response_model=Dict[str, Any])
async def test_job_apis(
    keywords: str = "software engineer",
    location: str = "remote",
    current_user: User = Depends(get_current_user)
):
    """Test job API integrations"""
    try:
        async with JobAPIService() as api_service:
            result = await api_service.test_apis()
            return result
    except Exception as e:
        logger.error(f"Job API test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quota-status", response_model=Dict[str, Any])
async def get_quota_status(
    current_user: User = Depends(get_current_user)
):
    """Get current quota status for all job sources"""
    try:
        quota_manager = QuotaManager()
        return {
            'quota_summary': quota_manager.get_quota_summary(),
            'health_status': quota_manager.get_health_status()
        }
    except Exception as e:
        logger.error(f"Error getting quota status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quota/reset/{api_name}", response_model=Dict[str, str])
async def reset_api_quota(
    api_name: str,
    current_user: User = Depends(get_current_user)
):
    """Reset quota for a specific API (admin function)"""
    try:
        quota_manager = QuotaManager()
        quota_manager.reset_api_quota(api_name)
        return {"message": f"Quota reset for {api_name}"}
    except Exception as e:
        logger.error(f"Error resetting quota for {api_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rss-feeds/discover", response_model=Dict[str, Any])
async def discover_company_feeds(
    companies: str,  # Comma-separated company names
    current_user: User = Depends(get_current_user)
):
    """Discover RSS feeds for company career pages"""
    try:
        company_list = [c.strip() for c in companies.split(',')]
        company_domains = [f"{company.lower().replace(' ', '')}.com" for company in company_list]
        
        async with RSSFeedService() as rss_service:
            discovered_feeds = await rss_service.discover_company_feeds(company_domains)
            
            return {
                'companies_searched': company_list,
                'feeds_discovered': discovered_feeds,
                'total_found': len(discovered_feeds)
            }
    except Exception as e:
        logger.error(f"Error discovering company feeds: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources/health", response_model=Dict[str, Any])
async def get_sources_health(
    current_user: User = Depends(get_current_user)
):
    """Get health status of all job sources"""
    try:
        quota_manager = QuotaManager()
        health_status = quota_manager.get_health_status()
        
        # Add additional health checks
        health_status['recommendations'] = []
        
        if health_status['health_percentage'] < 50:
            health_status['recommendations'].append("Consider reducing ingestion frequency")
        
        if health_status['blocked'] > 0:
            health_status['recommendations'].append("Some sources are blocked due to rate limiting")
        
        if health_status['exhausted'] > health_status['total_sources'] // 2:
            health_status['recommendations'].append("Most sources have exhausted quotas - wait for reset")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error getting sources health: {e}")
        raise HTTPException(status_code=500, detail=str(e))