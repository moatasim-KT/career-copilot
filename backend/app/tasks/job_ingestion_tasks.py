"""
Enhanced Celery tasks for job ingestion with monitoring and error handling
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from celery import current_task
from celery.exceptions import Retry, MaxRetriesExceededError
from sqlalchemy.orm import Session

from app.celery import celery_app
from app.core.database import get_db
from app.models.user import User
from app.services.job_ingestion_service import JobIngestionService
from app.tasks.monitoring import TaskMonitor


logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True, 
    name="app.tasks.job_ingestion_tasks.ingest_jobs_enhanced",
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    soft_time_limit=1800,  # 30 minutes
    time_limit=2100        # 35 minutes
)
def ingest_jobs_enhanced(self, user_ids: List[int] = None, max_jobs_per_user: int = 50) -> Dict[str, Any]:
    """
    Enhanced Celery task to ingest jobs with comprehensive error handling and monitoring
    
    Args:
        user_ids: List of specific user IDs to process. If None, processes all active users.
        max_jobs_per_user: Maximum number of jobs to ingest per user
    """
    task_id = current_task.request.id
    start_time = datetime.utcnow()
    
    # Initialize results structure
    results = {
        'task_id': task_id,
        'start_time': start_time.isoformat(),
        'users_processed': 0,
        'total_jobs_found': 0,
        'total_jobs_saved': 0,
        'errors': [],
        'user_results': [],
        'retry_count': self.request.retries
    }
    
    try:
        logger.info(f"Starting enhanced job ingestion task {task_id} (retry {self.request.retries})")
        
        # Get database session with error handling
        try:
            db: Session = next(get_db())
        except Exception as e:
            error_msg = f"Failed to get database connection: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            raise self.retry(countdown=120, exc=e)
        
        try:
            # Get users to process
            if user_ids:
                users = db.query(User).filter(User.id.in_(user_ids)).all()
                logger.info(f"Processing specific users: {user_ids}")
            else:
                # Get all active users (users who have logged in within last 30 days)
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                users = db.query(User).filter(User.last_active >= cutoff_date).all()
                logger.info(f"Processing all active users since {cutoff_date}")
            
            if not users:
                logger.warning("No users found to process")
                results['message'] = "No users found to process"
                return results
            
            logger.info(f"Processing job ingestion for {len(users)} users")
            
            # Initialize job ingestion service
            try:
                ingestion_service = JobIngestionService(db)
            except Exception as e:
                error_msg = f"Failed to initialize job ingestion service: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                raise self.retry(countdown=60, exc=e)
            
            # Process each user with individual error handling
            for i, user in enumerate(users):
                try:
                    # Update task progress
                    progress = int((i / len(users)) * 100)
                    current_task.update_state(
                        state='PROGRESS',
                        meta={
                            'current': i + 1,
                            'total': len(users),
                            'progress': progress,
                            'status': f'Processing user {user.id}',
                            'users_processed': results['users_processed'],
                            'jobs_saved': results['total_jobs_saved']
                        }
                    )
                    
                    logger.info(f"Processing job ingestion for user {user.id} ({i+1}/{len(users)})")
                    
                    # Perform job ingestion for user with timeout handling
                    try:
                        user_result = ingestion_service.ingest_jobs_for_user(
                            user_id=user.id,
                            max_jobs=max_jobs_per_user
                        )
                        
                        # Validate user result
                        if not isinstance(user_result, dict):
                            raise ValueError(f"Invalid result format from ingestion service: {type(user_result)}")
                        
                        # Update results
                        results['users_processed'] += 1
                        results['total_jobs_found'] += user_result.get('jobs_found', 0)
                        results['total_jobs_saved'] += user_result.get('jobs_saved', 0)
                        
                        user_result_summary = {
                            'user_id': user.id,
                            'jobs_found': user_result.get('jobs_found', 0),
                            'jobs_saved': user_result.get('jobs_saved', 0),
                            'duplicates_filtered': user_result.get('duplicates_filtered', 0),
                            'errors': user_result.get('errors', []),
                            'processing_time': user_result.get('processing_time', 0)
                        }
                        results['user_results'].append(user_result_summary)
                        
                        # Add user-specific errors to overall errors
                        if user_result.get('errors'):
                            for error in user_result['errors']:
                                results['errors'].append(f"User {user.id}: {error}")
                        
                        logger.info(f"Completed job ingestion for user {user.id}: "
                                   f"{user_result.get('jobs_saved', 0)} jobs saved")
                        
                    except Exception as user_error:
                        error_msg = f"Error processing user {user.id}: {str(user_error)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        
                        # Add failed user to results
                        results['user_results'].append({
                            'user_id': user.id,
                            'error': str(user_error),
                            'jobs_found': 0,
                            'jobs_saved': 0
                        })
                        
                        # Continue with next user instead of failing entire task
                        continue
                
                except Exception as e:
                    error_msg = f"Unexpected error processing user {user.id}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    continue
            
            # Calculate final statistics
            end_time = datetime.utcnow()
            results['end_time'] = end_time.isoformat()
            results['total_duration'] = (end_time - start_time).total_seconds()
            results['success_rate'] = (results['users_processed'] / len(users)) * 100 if users else 0
            
            logger.info(f"Job ingestion task completed: "
                       f"{results['users_processed']}/{len(users)} users processed, "
                       f"{results['total_jobs_saved']} jobs saved, "
                       f"{len(results['errors'])} errors")
            
            return results
            
        finally:
            db.close()
            
    except MaxRetriesExceededError:
        error_msg = f"Job ingestion task failed after {self.request.retries} retries"
        logger.error(error_msg)
        results['errors'].append(error_msg)
        results['status'] = 'failed_max_retries'
        return results
        
    except Exception as e:
        error_msg = f"Job ingestion task failed: {str(e)}"
        logger.error(error_msg)
        results['errors'].append(error_msg)
        
        # Retry on certain types of errors
        if isinstance(e, (ConnectionError, TimeoutError)) and self.request.retries < 3:
            logger.info(f"Retrying job ingestion task due to {type(e).__name__}")
            raise self.retry(countdown=120, exc=e)
        
        results['status'] = 'failed'
        return results


@celery_app.task(
    bind=True,
    name="app.tasks.job_ingestion_tasks.ingest_jobs_for_user_enhanced",
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 2, 'countdown': 30},
    soft_time_limit=600,   # 10 minutes
    time_limit=720         # 12 minutes
)
def ingest_jobs_for_user_enhanced(self, user_id: int, max_jobs: int = 50) -> Dict[str, Any]:
    """
    Enhanced Celery task to ingest jobs for a specific user with error handling
    
    Args:
        user_id: ID of the user to process
        max_jobs: Maximum number of jobs to ingest
    """
    task_id = current_task.request.id
    start_time = datetime.utcnow()
    
    logger.info(f"Starting enhanced job ingestion for user {user_id} (task {task_id})")
    
    try:
        # Get database session
        db: Session = next(get_db())
        
        try:
            # Verify user exists
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                error_msg = f"User {user_id} not found"
                logger.error(error_msg)
                return {
                    'user_id': user_id,
                    'error': error_msg,
                    'jobs_found': 0,
                    'jobs_saved': 0
                }
            
            # Perform job ingestion
            ingestion_service = JobIngestionService(db)
            result = ingestion_service.ingest_jobs_for_user(user_id, max_jobs)
            
            # Add timing information
            end_time = datetime.utcnow()
            result['task_id'] = task_id
            result['start_time'] = start_time.isoformat()
            result['end_time'] = end_time.isoformat()
            result['processing_time'] = (end_time - start_time).total_seconds()
            result['retry_count'] = self.request.retries
            
            logger.info(f"Job ingestion completed for user {user_id}: "
                       f"{result.get('jobs_saved', 0)} jobs saved in {result['processing_time']:.2f}s")
            
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"Job ingestion failed for user {user_id}: {str(e)}"
        logger.error(error_msg)
        
        # Retry on certain errors
        if isinstance(e, (ConnectionError, TimeoutError)) and self.request.retries < 2:
            logger.info(f"Retrying job ingestion for user {user_id} due to {type(e).__name__}")
            raise self.retry(countdown=60, exc=e)
        
        return {
            'user_id': user_id,
            'task_id': task_id,
            'error': error_msg,
            'jobs_found': 0,
            'jobs_saved': 0,
            'retry_count': self.request.retries
        }


@celery_app.task(name="app.tasks.job_ingestion_tasks.test_job_sources")
def test_job_sources() -> Dict[str, Any]:
    """
    Test all job ingestion sources to verify they're working
    """
    logger.info("Starting job sources test")
    
    try:
        db: Session = next(get_db())
        
        try:
            ingestion_service = JobIngestionService(db)
            result = ingestion_service.test_job_ingestion()
            
            logger.info("Job sources test completed successfully")
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"Job sources test failed: {str(e)}"
        logger.error(error_msg)
        return {
            'error': error_msg,
            'timestamp': datetime.utcnow().isoformat(),
            'scraper_tests': {},
            'test_search': {}
        }


@celery_app.task(name="app.tasks.job_ingestion_tasks.get_ingestion_statistics")
def get_ingestion_statistics(user_id: Optional[int] = None, days: int = 7) -> Dict[str, Any]:
    """
    Get job ingestion statistics for monitoring
    
    Args:
        user_id: Specific user ID, or None for all users
        days: Number of days to look back
    """
    try:
        db: Session = next(get_db())
        
        try:
            from app.models.job import Job
            from sqlalchemy import func
            
            # Calculate date range
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Base query
            query = db.query(Job).filter(Job.date_added >= cutoff_date)
            
            if user_id:
                query = query.filter(Job.user_id == user_id)
            
            # Get statistics
            total_jobs = query.count()
            
            # Jobs by source
            jobs_by_source = db.query(
                Job.source,
                func.count(Job.id).label('count')
            ).filter(Job.date_added >= cutoff_date)
            
            if user_id:
                jobs_by_source = jobs_by_source.filter(Job.user_id == user_id)
            
            jobs_by_source = jobs_by_source.group_by(Job.source).all()
            
            # Jobs by day
            jobs_by_day = db.query(
                func.date(Job.date_added).label('date'),
                func.count(Job.id).label('count')
            ).filter(Job.date_added >= cutoff_date)
            
            if user_id:
                jobs_by_day = jobs_by_day.filter(Job.user_id == user_id)
            
            jobs_by_day = jobs_by_day.group_by(func.date(Job.date_added)).all()
            
            statistics = {
                'period_days': days,
                'user_id': user_id,
                'total_jobs': total_jobs,
                'jobs_by_source': {source: count for source, count in jobs_by_source},
                'jobs_by_day': {str(date): count for date, count in jobs_by_day},
                'average_per_day': total_jobs / days if days > 0 else 0,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return statistics
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"Failed to get ingestion statistics: {str(e)}"
        logger.error(error_msg)
        return {
            'error': error_msg,
            'timestamp': datetime.utcnow().isoformat()
        }


@celery_app.task(name="app.tasks.job_ingestion_tasks.cleanup_old_jobs")
def cleanup_old_jobs(days_to_keep: int = 90) -> Dict[str, Any]:
    """
    Clean up old job postings to prevent database bloat
    
    Args:
        days_to_keep: Number of days of job data to retain
    """
    logger.info(f"Starting cleanup of jobs older than {days_to_keep} days")
    
    try:
        db: Session = next(get_db())
        
        try:
            from app.models.job import Job
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Only delete jobs that haven't been applied to
            old_jobs = db.query(Job).filter(
                Job.date_added < cutoff_date,
                Job.status == 'not_applied'
            )
            
            count_to_delete = old_jobs.count()
            
            if count_to_delete > 0:
                old_jobs.delete()
                db.commit()
                logger.info(f"Cleaned up {count_to_delete} old job postings")
            else:
                logger.info("No old jobs to clean up")
            
            return {
                'deleted_count': count_to_delete,
                'cutoff_date': cutoff_date.isoformat(),
                'days_kept': days_to_keep,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"Job cleanup failed: {str(e)}"
        logger.error(error_msg)
        return {
            'error': error_msg,
            'timestamp': datetime.utcnow().isoformat()
        }