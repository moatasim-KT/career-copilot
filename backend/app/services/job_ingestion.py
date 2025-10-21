"""
Celery tasks for job ingestion
"""

import logging
from typing import Dict, Any, List

from celery import current_task
from sqlalchemy.orm import Session

from app.celery import celery_app
from app.core.database import get_db
from app.models.user import User
from app.services.job_ingestion_service import JobIngestionService


logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.services.job_ingestion.ingest_jobs")
def ingest_jobs(self, user_ids: List[int] = None, max_jobs_per_user: int = 50) -> Dict[str, Any]:
    """
    Celery task to ingest jobs for users
    
    Args:
        user_ids: List of specific user IDs to process. If None, processes all active users.
        max_jobs_per_user: Maximum number of jobs to ingest per user
    """
    task_id = current_task.request.id
    logger.info(f"Starting job ingestion task {task_id}")
    
    results = {
        'task_id': task_id,
        'users_processed': 0,
        'total_jobs_found': 0,
        'total_jobs_saved': 0,
        'errors': [],
        'user_results': []
    }
    
    try:
        # Get database session
        db: Session = next(get_db())
        
        try:
            # Get users to process
            if user_ids:
                users = db.query(User).filter(User.id.in_(user_ids)).all()
            else:
                # Get all active users (users who have logged in within last 30 days)
                from datetime import datetime, timedelta
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                users = db.query(User).filter(User.last_active >= cutoff_date).all()
            
            logger.info(f"Processing job ingestion for {len(users)} users")
            
            # Process each user
            ingestion_service = JobIngestionService(db)
            
            for i, user in enumerate(users):
                try:
                    # Update task progress
                    current_task.update_state(
                        state='PROGRESS',
                        meta={
                            'current': i + 1,
                            'total': len(users),
                            'status': f'Processing user {user.id}'
                        }
                    )
                    
                    logger.info(f"Processing job ingestion for user {user.id}")
                    
                    # Perform job ingestion for user
                    user_result = ingestion_service.ingest_jobs_for_user(
                        user_id=user.id,
                        max_jobs=max_jobs_per_user
                    )
                    
                    # Update results
                    results['users_processed'] += 1
                    results['total_jobs_found'] += user_result['jobs_found']
                    results['total_jobs_saved'] += user_result['jobs_saved']
                    results['user_results'].append({
                        'user_id': user.id,
                        'jobs_found': user_result['jobs_found'],
                        'jobs_saved': user_result['jobs_saved'],
                        'duplicates_filtered': user_result['duplicates_filtered'],
                        'errors': user_result['errors']
                    })
                    
                    # Add user errors to overall errors
                    if user_result['errors']:
                        results['errors'].extend([
                            f"User {user.id}: {error}" 
                            for error in user_result['errors']
                        ])
                    
                    logger.info(f"Completed job ingestion for user {user.id}: "
                               f"{user_result['jobs_saved']} jobs saved")
                    
                except Exception as e:
                    error_msg = f"Error processing user {user.id}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            logger.info(f"Job ingestion task completed: "
                       f"{results['users_processed']} users processed, "
                       f"{results['total_jobs_saved']} jobs saved")
            
            return results
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"Job ingestion task failed: {str(e)}"
        logger.error(error_msg)
        results['errors'].append(error_msg)
        return results


@celery_app.task(name="app.services.job_ingestion.ingest_jobs_for_user")
def ingest_jobs_for_user(user_id: int, max_jobs: int = 50) -> Dict[str, Any]:
    """
    Celery task to ingest jobs for a specific user
    
    Args:
        user_id: ID of the user to process
        max_jobs: Maximum number of jobs to ingest
    """
    logger.info(f"Starting job ingestion for user {user_id}")
    
    try:
        # Get database session
        db: Session = next(get_db())
        
        try:
            # Perform job ingestion
            ingestion_service = JobIngestionService(db)
            result = ingestion_service.ingest_jobs_for_user(user_id, max_jobs)
            
            logger.info(f"Job ingestion completed for user {user_id}: "
                       f"{result['jobs_saved']} jobs saved")
            
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"Job ingestion failed for user {user_id}: {str(e)}"
        logger.error(error_msg)
        return {
            'user_id': user_id,
            'error': error_msg,
            'jobs_found': 0,
            'jobs_saved': 0
        }


@celery_app.task(name="app.services.job_ingestion.test_scrapers")
def test_scrapers() -> Dict[str, Any]:
    """
    Celery task to test all scrapers
    """
    logger.info("Starting scraper test task")
    
    try:
        # Get database session
        db: Session = next(get_db())
        
        try:
            # Test job ingestion
            ingestion_service = JobIngestionService(db)
            result = ingestion_service.test_job_ingestion()
            
            logger.info("Scraper test completed successfully")
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"Scraper test failed: {str(e)}"
        logger.error(error_msg)
        return {
            'error': error_msg,
            'scraper_tests': {},
            'test_search': {}
        }


@celery_app.task(name="app.services.job_ingestion.get_ingestion_stats")
def get_ingestion_stats(user_id: int) -> Dict[str, Any]:
    """
    Celery task to get ingestion statistics for a user
    
    Args:
        user_id: ID of the user
    """
    try:
        # Get database session
        db: Session = next(get_db())
        
        try:
            # Get ingestion stats
            ingestion_service = JobIngestionService(db)
            result = ingestion_service.get_ingestion_stats(user_id)
            
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"Error getting ingestion stats for user {user_id}: {str(e)}"
        logger.error(error_msg)
        return {
            'user_id': user_id,
            'error': error_msg
        }