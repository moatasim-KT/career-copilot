"""Scheduled tasks for automation"""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..core.database import SessionLocal
from ..models.user import User
from ..models.job import Job
from ..models.application import Application
from ..services.job_scraper import JobScraperService
from ..services.recommendation_engine import RecommendationEngine
from ..services.notification_service import NotificationService
import os

logger = logging.getLogger(__name__)


def ingest_jobs():
    """Nightly job ingestion task - Run at 4 AM"""
    db = SessionLocal()
    try:
        from ..core.config import get_settings
        settings = get_settings()
        
        # Check if job scraping is enabled
        if not settings.enable_job_scraping:
            print("Job scraping is disabled. Skipping job ingestion.")
            return
        
        scraper = JobScraperService(db=db, settings=settings)
        
        # Query all users with skills and preferred_locations
        users = db.query(User).filter(
            User.skills.isnot(None),
            User.preferred_locations.isnot(None)
        ).all()
        
        total_jobs_added = 0
        
        for user in users:
            # Skip users without skills or preferred locations
            if not user.skills or not user.preferred_locations:
                print(f"Skipping user {user.username} - missing skills or preferred locations")
                continue
            
            try:
                # Scrape jobs based on user preferences
                print(f"Scraping jobs for user {user.username} with skills: {user.skills[:3]} and locations: {user.preferred_locations[:2]}")
                new_jobs = scraper.scrape_jobs(
                    skills=user.skills,
                    preferred_locations=user.preferred_locations,
                    limit=20
                )
                
                if not new_jobs:
                    print(f"No new jobs found for user {user.username}")
                    continue
                
                # Deduplicate against existing jobs for this user
                unique_jobs = scraper.deduplicate_jobs(new_jobs, user_id=user.id)
                
                # Create Job entities with source="scraped"
                jobs_added = 0
                for job_data in unique_jobs:
                    try:
                        job = Job(
                            user_id=user.id,
                            company=job_data["company"],
                            title=job_data["title"],
                            location=job_data.get("location"),
                            description=job_data.get("description"),
                            requirements=job_data.get("requirements"),
                            tech_stack=job_data.get("tech_stack", []),
                            responsibilities=job_data.get("responsibilities"),
                            salary_range=job_data.get("salary_range"),
                            job_type=job_data.get("job_type"),
                            remote_option=job_data.get("remote_option"),
                            link=job_data.get("link"),
                            source="scraped",
                            status="not_applied"
                        )
                        db.add(job)
                        jobs_added += 1
                    except Exception as e:
                        print(f"Error creating job for user {user.username}: {str(e)}")
                        continue
                
                # Commit jobs for this user
                db.commit()
                total_jobs_added += jobs_added
                
                # Log number of jobs added per user
                print(f"Added {jobs_added} new jobs for user {user.username}")
                
            except Exception as e:
                print(f"Error processing jobs for user {user.username}: {str(e)}")
                db.rollback()
                continue
        
        print(f"Job ingestion completed. Total jobs added: {total_jobs_added}")
    
    except Exception as e:
        print(f"Error in job ingestion task: {str(e)}")
        db.rollback()
    finally:
        db.close()


def send_morning_briefing():
    """Morning recommendation task - Run at 8 AM"""
    db = SessionLocal()
    try:
        from ..core.config import get_settings
        settings = get_settings()
        
        # Initialize notification service with settings
        notification_service = NotificationService(db=db, settings=settings)
        
        # Query all users
        users = db.query(User).all()
        
        total_sent = 0
        total_failed = 0
        
        for user in users:
            try:
                # Skip users without email
                if not user.email:
                    logger.warning(f"User {user.username} has no email. Skipping morning briefing.")
                    continue
                
                # Get top 5 recommendations using RecommendationEngine
                recommendation_engine = RecommendationEngine(db)
                recommendations = recommendation_engine.get_recommendations(user, limit=5)
                
                # Send email via NotificationService
                success = notification_service.send_morning_briefing(user, recommendations)
                
                if success:
                    total_sent += 1
                    logger.info(f"Morning briefing sent successfully to {user.email}")
                else:
                    total_failed += 1
                    logger.error(f"Failed to send morning briefing to {user.email}")
                    
            except Exception as e:
                total_failed += 1
                logger.error(f"Error sending morning briefing to user {user.username}: {str(e)}")
                continue
        
        # Log overall results
        logger.info(f"Morning briefing task completed. Sent: {total_sent}, Failed: {total_failed}")
        print(f"Morning briefing task completed. Sent: {total_sent}, Failed: {total_failed}")
    
    except Exception as e:
        logger.error(f"Error in morning briefing task: {str(e)}")
        print(f"Error in morning briefing task: {str(e)}")
    finally:
        db.close()


def send_evening_summary():
    """Evening summary task - Run at 8 PM"""
    db = SessionLocal()
    try:
        from ..core.config import get_settings
        from ..services.job_analytics_service import JobAnalyticsService
        settings = get_settings()
        
        # Initialize notification service with settings
        notification_service = NotificationService(db=db, settings=settings)
        
        # Query all users
        users = db.query(User).all()
        today = datetime.now().date()
        
        total_sent = 0
        total_failed = 0
        
        for user in users:
            try:
                # Skip users without email
                if not user.email:
                    logger.warning(f"User {user.username} has no email. Skipping evening summary.")
                    continue
                
                # Calculate daily statistics using JobAnalyticsService
                analytics_service = JobAnalyticsService(db)
                analytics_summary = analytics_service.get_summary_metrics(user)
                
                # Add applications_today count (applications created today)
                from ..models.application import Application
                applications_today = db.query(Application).filter(
                    Application.user_id == user.id,
                    Application.applied_date >= datetime.combine(today, datetime.min.time())
                ).count()
                
                # Update analytics summary with today's data
                analytics_summary["applications_today"] = applications_today
                analytics_summary["jobs_saved"] = analytics_summary["total_jobs"]
                
                # Send email via NotificationService
                success = notification_service.send_evening_summary(user, analytics_summary)
                
                if success:
                    total_sent += 1
                    logger.info(f"Evening summary sent successfully to {user.email}")
                else:
                    total_failed += 1
                    logger.error(f"Failed to send evening summary to {user.email}")
                    
            except Exception as e:
                total_failed += 1
                logger.error(f"Error sending evening summary to user {user.username}: {str(e)}")
                continue
        
        # Log overall results
        logger.info(f"Evening summary task completed. Sent: {total_sent}, Failed: {total_failed}")
        print(f"Evening summary task completed. Sent: {total_sent}, Failed: {total_failed}")
    
    except Exception as e:
        logger.error(f"Error in evening summary task: {str(e)}")
        print(f"Error in evening summary task: {str(e)}")
    finally:
        db.close()
