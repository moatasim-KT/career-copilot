"""Scheduled tasks for automation"""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..core.database import SessionLocal
from ..models.user import User
from ..models.job import Job
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
        notification_service = NotificationService(
            smtp_host=os.getenv("SMTP_HOST"),
            smtp_port=int(os.getenv("SMTP_PORT", 587)),
            smtp_user=os.getenv("SMTP_USER"),
            smtp_password=os.getenv("SMTP_PASSWORD")
        )
        
        users = db.query(User).all()
        
        for user in users:
            recommendations = RecommendationEngine.get_recommendations(db, user, limit=5)
            
            if recommendations:
                notification_service.send_morning_briefing(user.email, recommendations)
                print(f"Sent morning briefing to {user.email}")
    
    finally:
        db.close()


def send_evening_summary():
    """Evening summary task - Run at 8 PM"""
    db = SessionLocal()
    try:
        notification_service = NotificationService(
            smtp_host=os.getenv("SMTP_HOST"),
            smtp_port=int(os.getenv("SMTP_PORT", 587)),
            smtp_user=os.getenv("SMTP_USER"),
            smtp_password=os.getenv("SMTP_PASSWORD")
        )
        
        users = db.query(User).all()
        today = datetime.now().date()
        
        for user in users:
            # Calculate today's stats
            jobs_today = db.query(Job).filter(
                Job.user_id == user.id,
                Job.date_applied >= datetime.combine(today, datetime.min.time())
            ).count()
            
            total_jobs = db.query(Job).filter(
                Job.user_id == user.id,
                Job.status == "applied"
            ).count()
            
            stats = {
                "applications_today": jobs_today,
                "total_applications": total_jobs,
                "jobs_saved": db.query(Job).filter(Job.user_id == user.id).count()
            }
            
            notification_service.send_evening_summary(user.email, stats)
            print(f"Sent evening summary to {user.email}")
    
    finally:
        db.close()
