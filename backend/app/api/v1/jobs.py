"""Job management endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...models.user import User
from ...models.job import Job
from ...schemas.job import JobCreate, JobUpdate, JobResponse
from ...services.cache_service import cache_service

router = APIRouter(tags=["jobs"])


@router.get("/api/v1/jobs", response_model=List[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all jobs for the current user with pagination support.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100, max: 1000)
    
    Returns jobs ordered by created_at descending (newest first).
    """
    # Validate pagination parameters
    if skip < 0:
        raise HTTPException(status_code=400, detail="Skip parameter must be non-negative")
    
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
    
    try:
        jobs = (
            db.query(Job)
            .filter(Job.user_id == current_user.id)
            .order_by(Job.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving jobs: {str(e)}")


router = APIRouter(tags=["jobs"])


@router.post("/api/v1/jobs", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new job with validation for required fields.
    
    - **company**: Required company name
    - **title**: Required job title
    - **tech_stack**: Optional list of technologies (defaults to empty list)
    - **responsibilities**: Optional job responsibilities
    - **source**: Source of the job (manual, scraped, api) - defaults to "manual"
    """
    job_dict = job_data.model_dump()
    
    # Ensure tech_stack is a list (not None)
    if job_dict.get('tech_stack') is None:
        job_dict['tech_stack'] = []
    
    # Ensure source has a default value
    if not job_dict.get('source'):
        job_dict['source'] = 'manual'
    
    job = Job(**job_dict, user_id=current_user.id)
    db.add(job)
    db.commit()
    db.refresh(job)

    # Invalidate all recommendation caches since new job affects all users' recommendations
    cache_service.invalidate_all_recommendations()

    # Trigger real-time job matching for scraped jobs
    if job.source == 'scraped':
        try:
            from ...services.job_matching_service import get_job_matching_service
            matching_service = get_job_matching_service(db)
            await matching_service.process_new_jobs_for_matching([job])
        except Exception as e:
            # Don't fail job creation if matching fails
            from ...core.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error processing job matching for new job {job.id}: {e}")
    
    # Trigger dashboard update
    try:
        from ...services.dashboard_service import get_dashboard_service
        dashboard_service = get_dashboard_service(db)
        await dashboard_service.handle_job_update(current_user.id, job.id)
    except Exception as e:
        # Don't fail job creation if dashboard update fails
        from ...core.logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Error sending dashboard update for new job {job.id}: {e}")

    return job


@router.get("/api/v1/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific job by ID.
    
    - **job_id**: ID of the job to retrieve
    
    Returns 404 if the job doesn't exist or doesn't belong to the current user.
    """
    try:
        job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving job: {str(e)}")


@router.put("/api/v1/jobs/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a job with all fields supported.
    
    - Automatically updates the updated_at timestamp
    - Sets date_applied when status changes to "applied"
    - Validates that the job belongs to the current user
    """
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    update_data = job_data.model_dump(exclude_unset=True)
    
    # Track if status is being changed to 'applied'
    status_changed_to_applied = (
        "status" in update_data and 
        update_data["status"] == "applied" and 
        job.status != "applied"
    )
    
    # Apply all updates
    for key, value in update_data.items():
        setattr(job, key, value)

    # If status is being changed to 'applied', set the application date
    if status_changed_to_applied and job.date_applied is None:
        job.date_applied = datetime.utcnow()
    
    # Ensure updated_at is set (SQLAlchemy should handle this with onupdate, but being explicit)
    job.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(job)

    # Invalidate recommendations cache for this user since job details changed
    cache_service.invalidate_user_cache(current_user.id)
    
    # Trigger dashboard update
    try:
        from ...services.dashboard_service import get_dashboard_service
        dashboard_service = get_dashboard_service(db)
        await dashboard_service.handle_job_update(current_user.id, job.id)
    except Exception as e:
        # Don't fail job update if dashboard update fails
        from ...core.logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Error sending dashboard update for job {job.id}: {e}")

    return job


@router.delete("/api/v1/jobs/{job_id}", status_code=204)
async def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a job and all associated applications (cascade delete).
    
    - **job_id**: ID of the job to delete
    
    The cascade delete is configured in the Job model relationship,
    so all associated Application records will be automatically deleted.
    """
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        # Get count of applications that will be deleted
        app_count = len(job.applications)
        
        db.delete(job)
        db.commit()
        
        # Invalidate recommendations cache for this user since job was deleted
        cache_service.invalidate_user_cache(current_user.id)

        return {
            "message": "Job deleted successfully",
            "job_id": job_id,
            "applications_deleted": app_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting job: {str(e)}")


@router.get("/api/v1/jobs/sources/analytics")
async def get_job_source_analytics(
    timeframe_days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive analytics for all job sources.
    
    - **timeframe_days**: Number of days to analyze (default: 30)
    
    Returns quality scores, performance metrics, and recommendations for each job source.
    """
    try:
        from ...services.job_source_manager import JobSourceManager
        source_manager = JobSourceManager(db)
        
        analytics = source_manager.get_source_analytics(timeframe_days)
        user_preferences = source_manager.get_user_source_preferences(current_user.id)
        
        return {
            "analytics": analytics,
            "user_preferences": user_preferences,
            "timeframe_days": timeframe_days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving source analytics: {str(e)}")


@router.get("/api/v1/jobs/sources/recommendations")
async def get_source_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized job source recommendations for the current user.
    
    Returns recommended job sources based on user's historical success rates
    and overall source quality metrics.
    """
    try:
        from ...services.job_source_manager import JobSourceManager
        source_manager = JobSourceManager(db)
        
        user_data = source_manager.get_user_source_preferences(current_user.id)
        
        return {
            "recommended_sources": user_data.get("recommended_sources", []),
            "source_performance": user_data.get("source_preferences", {}),
            "user_id": current_user.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving source recommendations: {str(e)}")


@router.get("/api/v1/jobs/{job_id}/source-info")
async def get_job_source_info(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed source information for a specific job.
    
    - **job_id**: ID of the job to analyze
    
    Returns source quality metrics, reliability indicators, and enriched data.
    """
    try:
        job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        from ...services.job_source_manager import JobSourceManager
        source_manager = JobSourceManager(db)
        
        source_info = source_manager.enrich_job_with_source_data(job)
        
        return {
            "job_id": job_id,
            "source": job.source,
            "source_info": source_info
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving job source info: {str(e)}")


@router.post("/api/v1/jobs/scrape")
async def trigger_job_scraping(
    search_params: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger job scraping from multiple sources.
    
    - **search_params**: Dictionary of search parameters (e.g., {"what": "software engineer", "where": "remote"})
    
    Returns scraped jobs that were added to the user's job list.
    """
    try:
        from ...services.job_scraper_service import JobScraper
        scraper = JobScraper(db)
        
        new_jobs = await scraper.scrape_jobs(current_user.id, search_params)
        
        # Invalidate cache
        cache_service.invalidate_user_cache(current_user.id)
        
        return {
            "message": f"Successfully scraped {len(new_jobs)} new jobs",
            "jobs_added": len(new_jobs),
            "keywords": search_params.get("what"),
            "location": search_params.get("where"),
            "sources_used": "adzuna" # For now, only Adzuna is integrated
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error scraping jobs: {str(e)}")


@router.get("/api/v1/jobs/sources/available")
async def get_available_sources(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get information about all available job sources.
    
    Returns metadata, quality scores, and availability status for each source.
    """
    try:
        from ...services.job_source_manager import JobSourceManager
        source_manager = JobSourceManager(db)
        
        sources_info = source_manager.get_available_sources_info()
        user_preferences = source_manager.get_user_source_preferences(current_user.id)
        
        return {
            "sources": sources_info,
            "user_preferences": user_preferences.get("preferences", {}),
            "total_sources": len(sources_info),
            "active_sources": len([s for s in sources_info if s['is_active']])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving available sources: {str(e)}")


@router.get("/api/v1/jobs/sources/performance")
async def get_source_performance_summary(
    timeframe_days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive performance summary for all job sources.
    
    - **timeframe_days**: Number of days to analyze (default: 30)
    
    Returns performance rankings, quality metrics, and recommendations.
    """
    try:
        from ...services.job_source_manager import JobSourceManager
        source_manager = JobSourceManager(db)
        
        performance_summary = source_manager.get_source_performance_summary(current_user.id, timeframe_days)
        
        return performance_summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving source performance: {str(e)}")


@router.put("/api/v1/jobs/sources/preferences")
async def update_source_preferences(
    preferences_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user's job source preferences.
    
    - **preferred_sources**: List of preferred job sources
    - **disabled_sources**: List of disabled job sources  
    - **source_priorities**: Custom source priority weights
    - **auto_scraping_enabled**: Enable/disable automatic job scraping
    - **max_jobs_per_source**: Maximum jobs to fetch per source
    - **min_quality_threshold**: Minimum quality score to accept jobs
    """
    try:
        from ...services.job_source_manager import JobSourceManager
        source_manager = JobSourceManager(db)
        
        updated_prefs = source_manager.create_or_update_user_preferences(current_user.id, preferences_data)
        
        return {
            "message": "Source preferences updated successfully",
            "preferences": {
                "preferred_sources": updated_prefs.preferred_sources,
                "disabled_sources": updated_prefs.disabled_sources,
                "source_priorities": updated_prefs.source_priorities,
                "auto_scraping_enabled": updated_prefs.auto_scraping_enabled,
                "max_jobs_per_source": updated_prefs.max_jobs_per_source,
                "min_quality_threshold": updated_prefs.min_quality_threshold
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating source preferences: {str(e)}")


@router.get("/api/v1/jobs/{job_id}/enrichment")
async def get_job_enrichment_data(
    job_id: int,
    include_external: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get enriched data for a specific job including source quality and external data.
    
    - **job_id**: ID of the job to enrich
    - **include_external**: Whether to include external API data (slower)
    
    Returns comprehensive job enrichment data including source metrics and external insights.
    """
    try:
        job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        from ...services.job_source_manager import JobSourceManager
        source_manager = JobSourceManager(db)
        
        enrichment_data = source_manager.enrich_job_with_source_data(job, include_external)
        
        # If external data is requested, fetch it asynchronously
        if include_external:
            external_data = await source_manager.enrich_job_with_external_apis(job)
            enrichment_data['external_enrichment'] = external_data
        
        return {
            "job_id": job_id,
            "source": job.source,
            "enrichment_data": enrichment_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enriching job data: {str(e)}")
