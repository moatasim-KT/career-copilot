"""
Google Cloud Functions entry point for Career Copilot API.
Enhanced with comprehensive monitoring, logging, and error tracking.
"""

import functions_framework
import asyncio
import time
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.main import app
from .monitoring_integration import (
    monitor_cloud_function,
    monitor_async_cloud_function,
    track_job_metrics,
    track_email_metrics,
    track_api_metrics,
    initialize_monitoring,
    get_monitoring_health
)
from .enhanced_logging_config import logger, log_business_event, log_performance_metric
from .enhanced_error_tracking import error_tracker, performance_monitor
from .enhanced_monitoring import monitoring

# Initialize monitoring system on module load
initialize_monitoring()


@functions_framework.http
def monitoring_health_check(request):
    """Health check endpoint for monitoring system."""
    try:
        health_status = get_monitoring_health()
        
        # Log health check request
        log_business_event('monitoring_health_check_requested',
                          status=health_status.get('status', 'unknown'))
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': health_status
        }
        
    except Exception as e:
        logger.error("Health check failed", error=e)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': {'status': 'error', 'error': str(e)}
        }


@functions_framework.http
@monitor_cloud_function('career_copilot_api')
def career_copilot_api(request):
    """HTTP Cloud Function entry point for main API with comprehensive monitoring."""
    try:
        # Create WSGI environment
        environ = request.environ.copy()
        environ['REQUEST_METHOD'] = request.method
        environ['PATH_INFO'] = request.path
        environ['QUERY_STRING'] = request.query_string
        
        # Log API request details
        log_business_event('api_request_received',
                          method=request.method,
                          path=request.path,
                          query_string=request.query_string)
        
        # Handle the request through FastAPI
        from app.main import app
        response = app(environ, lambda status, headers: None)
        
        # Log successful API response
        log_business_event('api_request_completed',
                          method=request.method,
                          path=request.path,
                          status='success')
        
        return response
        
    except Exception as e:
        # Log API error
        log_business_event('api_request_failed',
                          method=request.method,
                          path=request.path,
                          error_type=type(e).__name__,
                          error_message=str(e))
        raise


@functions_framework.http
@monitor_cloud_function('job_ingestion_scheduler')
def job_ingestion_scheduler(request):
    """Scheduled job ingestion function with comprehensive monitoring."""
    
    async def run_ingestion():
        from app.core.database import get_db
        from app.services.job_ingestion_service import JobIngestionService
        from app.models.user import User
        
        # Get all active users
        db = next(get_db())
        try:
            users = db.query(User).filter(User.is_active == True).all()
            
            total_results = {
                'users_processed': 0,
                'jobs_found': 0,
                'jobs_saved': 0,
                'errors': []
            }
            
            # Log ingestion start
            log_business_event('job_ingestion_started',
                             total_users=len(users))
            
            for user in users:
                try:
                    service = JobIngestionService(db)
                    result = await service.ingest_jobs_for_user(user.id, max_jobs=50)
                    
                    total_results['users_processed'] += 1
                    total_results['jobs_found'] += result.get('jobs_found', 0)
                    total_results['jobs_saved'] += result.get('jobs_saved', 0)
                    
                    # Log per-user metrics
                    log_performance_metric('jobs_per_user', result.get('jobs_saved', 0), 'count',
                                         user_id=user.id)
                    
                except Exception as e:
                    error_msg = f"Error ingesting jobs for user {user.id}: {str(e)}"
                    total_results['errors'].append(error_msg)
                    logger.error(error_msg, user_id=user.id)
            
            # Track comprehensive metrics
            track_job_metrics(
                total_results['jobs_found'], 
                total_results['jobs_found'], 
                total_results['jobs_saved'],
                'scheduled_ingestion'
            )
            
            # Log ingestion completion
            log_business_event('job_ingestion_completed',
                             users_processed=total_results['users_processed'],
                             jobs_found=total_results['jobs_found'],
                             jobs_saved=total_results['jobs_saved'],
                             error_count=len(total_results['errors']))
            
            return total_results
            
        finally:
            db.close()
    
    try:
        result = asyncio.run(run_ingestion())
        return {
            'statusCode': 200,
            'body': f"Job ingestion completed: {result.get('jobs_saved', 0)} jobs saved for {result.get('users_processed', 0)} users"
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Job ingestion failed: {str(e)}"
        }


@functions_framework.http
@monitor_cloud_function('morning_briefing_scheduler')
def morning_briefing_scheduler(request):
    """Scheduled morning briefing function with comprehensive monitoring."""
    
    async def send_briefings():
        from app.core.database import get_db
        from app.services.briefing_service import briefing_service
        from app.services.sendgrid_service import SendGridService
        from app.models.user import User
        
        db = next(get_db())
        try:
            # Get users with morning briefing enabled
            users = db.query(User).filter(
                User.is_active == True,
                User.settings['email_notifications']['morning_briefing'].astext.cast(db.Boolean) == True
            ).all()
            
            sendgrid_service = SendGridService()
            results = {
                'recipient_count': len(users),
                'success_count': 0,
                'errors': []
            }
            
            # Log briefing start
            log_business_event('morning_briefing_started',
                             recipient_count=results['recipient_count'])
            
            for user in users:
                try:
                    # Generate briefing data
                    briefing_data = briefing_service.generate_morning_briefing_data(db, user.id)
                    
                    # Track email generation time
                    start_time = time.time()
                    await sendgrid_service.send_morning_briefing(user.email, briefing_data)
                    email_duration = time.time() - start_time
                    
                    results['success_count'] += 1
                    
                    # Log per-email metrics
                    log_performance_metric('email_send_duration', email_duration * 1000, 'ms',
                                         email_type='morning_briefing',
                                         user_id=user.id)
                    
                except Exception as e:
                    error_msg = f"Error sending briefing to user {user.id}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg, user_id=user.id, email_type='morning_briefing')
            
            # Track comprehensive email metrics
            track_email_metrics('morning_briefing', results['recipient_count'], results['success_count'])
            
            # Log briefing completion
            log_business_event('morning_briefing_completed',
                             recipient_count=results['recipient_count'],
                             success_count=results['success_count'],
                             error_count=len(results['errors']),
                             delivery_rate=results['success_count'] / results['recipient_count'] if results['recipient_count'] > 0 else 0)
            
            return results
            
        finally:
            db.close()
    
    try:
        result = asyncio.run(send_briefings())
        return {
            'statusCode': 200,
            'body': f"Morning briefings sent: {result.get('success_count', 0)}/{result.get('recipient_count', 0)} delivered"
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Morning briefing failed: {str(e)}"
        }


@functions_framework.http
@monitor_cloud_function('evening_update_scheduler')
def evening_update_scheduler(request):
    """Scheduled evening update function with comprehensive monitoring."""
    
    async def send_updates():
        from app.core.database import get_db
        from app.services.briefing_service import briefing_service
        from app.services.sendgrid_service import SendGridService
        from app.models.user import User
        from app.models.application import JobApplication
        from datetime import datetime, timedelta
        
        db = next(get_db())
        try:
            # Get users who applied to jobs today and have evening updates enabled
            today = datetime.now().date()
            users_with_applications = db.query(User).join(JobApplication).filter(
                User.is_active == True,
                User.settings['email_notifications']['evening_summary'].astext.cast(db.Boolean) == True,
                db.func.date(JobApplication.applied_at) == today
            ).distinct().all()
            
            sendgrid_service = SendGridService()
            results = {
                'recipient_count': len(users_with_applications),
                'success_count': 0,
                'errors': []
            }
            
            # Log evening update start
            log_business_event('evening_update_started',
                             recipient_count=results['recipient_count'],
                             date=today.isoformat())
            
            for user in users_with_applications:
                try:
                    # Generate summary data
                    summary_data = briefing_service.generate_evening_summary_data(db, user.id)
                    
                    # Track email generation time
                    start_time = time.time()
                    await sendgrid_service.send_evening_summary(user.email, summary_data)
                    email_duration = time.time() - start_time
                    
                    results['success_count'] += 1
                    
                    # Log per-email metrics
                    log_performance_metric('email_send_duration', email_duration * 1000, 'ms',
                                         email_type='evening_summary',
                                         user_id=user.id)
                    
                except Exception as e:
                    error_msg = f"Error sending summary to user {user.id}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg, user_id=user.id, email_type='evening_summary')
            
            # Track comprehensive email metrics
            track_email_metrics('evening_update', results['recipient_count'], results['success_count'])
            
            # Log evening update completion
            log_business_event('evening_update_completed',
                             recipient_count=results['recipient_count'],
                             success_count=results['success_count'],
                             error_count=len(results['errors']),
                             delivery_rate=results['success_count'] / results['recipient_count'] if results['recipient_count'] > 0 else 0)
            
            return results
            
        finally:
            db.close()
    
    try:
        result = asyncio.run(send_updates())
        return {
            'statusCode': 200,
            'body': f"Evening updates sent: {result.get('success_count', 0)}/{result.get('recipient_count', 0)} delivered"
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Evening update failed: {str(e)}"
        }