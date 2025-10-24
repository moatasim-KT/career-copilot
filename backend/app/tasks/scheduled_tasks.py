"""Scheduled tasks for automation"""

import logging
import traceback
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..core.database import SessionLocal
from ..models.user import User
from ..models.job import Job
from ..models.application import Application
from ..services.job_scraper_service import JobScraper
from ..services.recommendation_engine import RecommendationEngine
from ..services.notification_service import NotificationService
from ..services.job_matching_service import get_job_matching_service
from ..services.websocket_service import websocket_service
from ..services.scraping.scraper_manager import ScraperManager, ScrapingConfig
from ..services.job_service import JobService
import os

logger = logging.getLogger(__name__)


async def ingest_jobs():
    """Nightly job ingestion task - Run at 4 AM"""
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info(f"Starting job ingestion task at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    db = SessionLocal()
    try:
        from ..core.config import get_settings
        settings = get_settings()
        
        # Check if job scraping is enabled
        if not settings.enable_job_scraping:
            logger.info("Job scraping is disabled. Skipping job ingestion.")
            return
        
        from ..services.scraping.scraper_manager import ScraperManager, ScrapingConfig
        from ..services.job_service import JobService

        # Initialize ScraperManager
        scraping_config = ScrapingConfig(
            enable_indeed=settings.enable_indeed,
            enable_linkedin=settings.enable_linkedin,
            enable_adzuna=settings.enable_adzuna,
        )
        scraper_manager = ScraperManager(config=scraping_config)
        job_service = JobService(db)

        # Query all users with skills and preferred_locations
        users = db.query(User).filter(
            User.skills.isnot(None),
            User.preferred_locations.isnot(None)
        ).all()
        
        logger.info(f"Found {len(users)} users with skills and preferred locations")
        
        total_jobs_added = 0
        users_processed = 0
        users_failed = 0
        
        for user in users:
            # Skip users without skills or preferred locations
            if not user.skills or not user.preferred_locations:
                logger.warning(f"Skipping user {user.username} - missing skills or preferred locations")
                continue
            
            try:
                # Send WebSocket update
                await websocket_service.send_system_notification(
                    message=f"Starting job ingestion for {user.username}...",
                    target_users={user.id}
                )

                # Prepare search parameters based on user preferences
                keywords = " ".join(user.skills)
                location = " ".join(user.preferred_locations)

                # Scrape jobs based on user preferences
                logger.info(f"Scraping jobs for user {user.username} with keywords: {keywords}, location: {location}")
                scraped_jobs = await scraper_manager.search_all_sites(keywords, location, max_total_results=50)
                
                if not scraped_jobs:
                    logger.info(f"No new jobs found for user {user.username}")
                    await websocket_service.send_system_notification(
                        message=f"No new jobs found for {user.username}.",
                        target_users={user.id}
                    )
                    users_processed += 1
                    continue
                
                # Save new jobs to the database and perform duplicate checking
                new_jobs_count = 0
                for job_create_obj in scraped_jobs:
                    existing_job = job_service.get_job_by_unique_fields(user.id, job_create_obj.title, job_create_obj.company, job_create_obj.location)
                    if not existing_job:
                        job_service.create_job(user.id, job_create_obj)
                        new_jobs_count += 1
                db.commit() # Commit after all jobs for a user are processed

                total_jobs_added += new_jobs_count
                users_processed += 1
                
                # Log number of jobs added per user
                logger.info(f"✓ Added {new_jobs_count} new jobs for user {user.username}")
                await websocket_service.send_system_notification(
                    message=f"Added {new_jobs_count} new jobs for {user.username}.",
                    target_users={user.id}
                )

                # Process real-time job matching for new jobs
                if new_jobs_count > 0:
                    try:
                        # Fetch the newly added jobs for matching
                        newly_added_jobs = job_service.get_latest_jobs_for_user(user.id, limit=new_jobs_count)
                        matching_service = get_job_matching_service(db)
                        await matching_service.process_new_jobs_for_matching(newly_added_jobs)
                    except Exception as e:
                        logger.error(f"Error processing job matching for user {user.username}: {e}")

                # Invalidate all recommendation caches since new jobs affect all users
                try:
                    from ..services.cache_service import cache_service
                    cache_service.invalidate_user_cache(user.id)
                except ImportError:
                    # Fallback if cache service not available
                    pass
                
            except Exception as e:
                users_failed += 1
                logger.error(f"✗ Error processing jobs for user {user.username}: {str(e)}", exc_info=True)
                logger.error(f"Stack trace: {traceback.format_exc()}")
                db.rollback()
                await websocket_service.send_system_notification(
                    message=f"Error processing jobs for {user.username}: {e}",
                    notification_type="error",
                    target_users={user.id}
                )
                continue
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=" * 80)
        logger.info(f"Job ingestion task completed at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Users processed: {users_processed}, Failed: {users_failed}")
        logger.info(f"Total jobs added: {total_jobs_added}")
        logger.info("=" * 80)
        await websocket_service.send_system_notification(
            message=f"Job ingestion task completed. Total jobs added: {total_jobs_added}.",
            notification_type="info"
        )

    except Exception as e:
        logger.error(f"Critical error in job ingestion task: {str(e)}", exc_info=True)
        logger.error(f"Stack trace: {traceback.format_exc()}")
        db.rollback()
    finally:
        db.close()


async def send_morning_briefing():
    """Morning recommendation task - Run at 8 AM"""
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info(f"Starting morning briefing task at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    db = SessionLocal()
    try:
        from ..core.config import get_settings
        settings = get_settings()
        
        # Initialize notification service with settings
        notification_service = NotificationService(db=db, settings=settings)
        
        # Query all users
        users = db.query(User).all()
        logger.info(f"Found {len(users)} users to process")
        
        total_sent = 0
        total_failed = 0
        total_skipped = 0
        
        for user in users:
            try:
                # Skip users without email
                if not user.email:
                    logger.warning(f"User {user.username} has no email. Skipping morning briefing.")
                    total_skipped += 1
                    continue
                
                # Get top 5 recommendations using RecommendationEngine
                logger.debug(f"Generating recommendations for user {user.username}")
                recommendation_engine = RecommendationEngine(db)
                recommendations = recommendation_engine.get_recommendations(user, limit=5)
                
                logger.info(f"Generated {len(recommendations)} recommendations for user {user.username}")
                
                # Send email via NotificationService
                success = notification_service.send_morning_briefing(user, recommendations)
                
                if success:
                    total_sent += 1
                    logger.info(f"✓ Morning briefing sent successfully to {user.email}")
                    await websocket_service.send_system_notification(
                        message="Morning briefing sent successfully!",
                        target_users={user.id}
                    )
                else:
                    total_failed += 1
                    logger.error(f"✗ Failed to send morning briefing to {user.email}")
                    await websocket_service.send_system_notification(
                        message="Failed to send morning briefing.",
                        notification_type="error",
                        target_users={user.id}
                    )
                    
            except Exception as e:
                total_failed += 1
                logger.error(f"✗ Error sending morning briefing to user {user.username}: {str(e)}", exc_info=True)
                logger.error(f"Stack trace: {traceback.format_exc()}")
                continue
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Log overall results
        logger.info("=" * 80)
        logger.info(f"Morning briefing task completed at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Sent: {total_sent}, Failed: {total_failed}, Skipped: {total_skipped}")
        logger.info("=" * 80)
    
    except Exception as e:
        logger.error(f"Critical error in morning briefing task: {str(e)}", exc_info=True)
        logger.error(f"Stack trace: {traceback.format_exc()}")
    finally:
        db.close()


async def send_evening_summary():
    """Evening summary task - Run at 8 PM"""
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info(f"Starting evening summary task at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    db = SessionLocal()
    try:
        from ..core.config import get_settings
        from ..services.analytics import AnalyticsService
        settings = get_settings()
        
        # Initialize notification service with settings
        notification_service = NotificationService(db=db, settings=settings)
        
        # Query all users
        users = db.query(User).all()
        today = datetime.now().date()
        logger.info(f"Found {len(users)} users to process")
        
        total_sent = 0
        total_failed = 0
        total_skipped = 0
        
        for user in users:
            try:
                # Skip users without email
                if not user.email:
                    logger.warning(f"User {user.username} has no email. Skipping evening summary.")
                    total_skipped += 1
                    continue
                
                # Calculate daily statistics using AnalyticsService
                logger.debug(f"Calculating analytics for user {user.username}")
                from ..services.analytics_service import AnalyticsService
                analytics_service = AnalyticsService(db)
                analytics_summary = analytics_service.get_user_analytics(user)
                
                # Add applications_today count (applications created today)
                from ..models.application import Application
                applications_today = db.query(Application).filter(
                    Application.user_id == user.id,
                    Application.applied_date >= datetime.combine(today, datetime.min.time())
                ).count()
                
                # Update analytics summary with today's data
                analytics_summary["applications_today"] = applications_today
                analytics_summary["jobs_saved"] = analytics_summary["total_jobs"]
                
                logger.info(f"Analytics for {user.username}: {applications_today} applications today, {analytics_summary['total_jobs']} total jobs")
                
                # Send email via NotificationService
                success = notification_service.send_evening_summary(user, analytics_summary)
                
                if success:
                    total_sent += 1
                    logger.info(f"✓ Evening summary sent successfully to {user.email}")
                    await websocket_service.send_system_notification(
                        message="Evening summary sent successfully!",
                        target_users={user.id}
                    )
                else:
                    total_failed += 1
                    logger.error(f"✗ Failed to send evening summary to {user.email}")
                    await websocket_service.send_system_notification(
                        message="Failed to send evening summary.",
                        notification_type="error",
                        target_users={user.id}
                    )
                    
            except Exception as e:
                total_failed += 1
                logger.error(f"✗ Error sending evening summary to user {user.username}: {str(e)}", exc_info=True)
                logger.error(f"Stack trace: {traceback.format_exc()}")
                continue
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Log overall results
        logger.info("=" * 80)
        logger.info(f"Evening summary task completed at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Sent: {total_sent}, Failed: {total_failed}, Skipped: {total_skipped}")
        logger.info("=" * 80)
    
    except Exception as e:
        logger.error(f"Critical error in evening summary task: {str(e)}", exc_info=True)
        logger.error(f"Stack trace: {traceback.format_exc()}")
    finally:
        db.close()
