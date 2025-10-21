"""
Monitoring integration module for Career Co-Pilot Cloud Functions.
Provides comprehensive monitoring, logging, and error tracking integration.
"""

import os
import sys
import time
import functools
from typing import Any, Dict, Optional, Callable
from datetime import datetime

# Add backend path for imports
from pathlib import Path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from .enhanced_logging_config import (
    logger, 
    set_correlation_id, 
    generate_correlation_id,
    log_function_start,
    log_function_end,
    log_error,
    log_performance_metric,
    log_business_event
)
from .enhanced_error_tracking import (
    monitor_function,
    monitor_async_function,
    track_business_metric,
    track_api_call,
    track_job_ingestion,
    track_email_delivery,
    error_tracker,
    performance_monitor
)
from .enhanced_monitoring import (
    monitoring,
    track_function_performance,
    setup_comprehensive_monitoring
)


class CareerCopilotMonitoring:
    """Comprehensive monitoring integration for Career Co-Pilot functions."""
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.function_name = os.getenv('FUNCTION_NAME', 'unknown')
        self.initialized = False
        
    def initialize(self) -> bool:
        """Initialize comprehensive monitoring system."""
        if self.initialized:
            return True
            
        try:
            logger.info("Initializing Career Co-Pilot monitoring system",
                       project_id=self.project_id,
                       environment=self.environment,
                       function_name=self.function_name)
            
            # Setup comprehensive monitoring in production
            if self.environment == 'production':
                setup_results = setup_comprehensive_monitoring()
                if not setup_results.get('overall_success', False):
                    logger.warning("Monitoring setup had issues", setup_results=setup_results)
            
            self.initialized = True
            logger.info("Career Co-Pilot monitoring system initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize monitoring system", error=e)
            return False
    
    def monitor_cloud_function(self, operation_name: Optional[str] = None):
        """Decorator for monitoring Cloud Functions with comprehensive tracking."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(request, *args, **kwargs):
                # Initialize monitoring if not done
                if not self.initialized:
                    self.initialize()
                
                # Generate correlation ID
                correlation_id = generate_correlation_id()
                set_correlation_id(correlation_id)
                
                # Extract request information
                method = getattr(request, 'method', 'UNKNOWN')
                path = getattr(request, 'path', '/')
                
                op_name = operation_name or func.__name__
                
                # Start performance tracking
                start_time = time.time()
                timer_id = performance_monitor.start_timer(
                    op_name,
                    context={
                        'function_name': self.function_name,
                        'method': method,
                        'path': path,
                        'correlation_id': correlation_id
                    }
                )
                
                # Log function start
                log_function_start(op_name,
                                 method=method,
                                 path=path,
                                 correlation_id=correlation_id,
                                 function_name=self.function_name)
                
                try:
                    # Execute function
                    result = func(request, *args, **kwargs)
                    
                    # Calculate duration
                    duration = time.time() - start_time
                    
                    # End performance tracking
                    performance_monitor.end_timer(timer_id, {'status': 'success'}, success=True)
                    
                    # Log function completion
                    log_function_end(op_name, duration,
                                   method=method,
                                   path=path,
                                   status='success',
                                   correlation_id=correlation_id)
                    
                    # Track business metrics
                    track_business_metric('function_executions', 1, {
                        'function_name': self.function_name,
                        'operation': op_name,
                        'status': 'success'
                    })
                    
                    return result
                    
                except Exception as e:
                    duration = time.time() - start_time
                    
                    # End performance tracking with error
                    performance_monitor.end_timer(timer_id, {'status': 'error'}, success=False)
                    
                    # Report error
                    error_tracker.report_error(e, {
                        'function_name': self.function_name,
                        'operation': op_name,
                        'method': method,
                        'path': path,
                        'correlation_id': correlation_id,
                        'duration': duration
                    })
                    
                    # Log error
                    log_error(op_name, e,
                             method=method,
                             path=path,
                             duration=duration,
                             correlation_id=correlation_id)
                    
                    # Track error metrics
                    track_business_metric('function_errors', 1, {
                        'function_name': self.function_name,
                        'operation': op_name,
                        'error_type': type(e).__name__
                    })
                    
                    raise
            
            return wrapper
        return decorator
    
    def monitor_async_cloud_function(self, operation_name: Optional[str] = None):
        """Decorator for monitoring async Cloud Functions."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(request, *args, **kwargs):
                # Initialize monitoring if not done
                if not self.initialized:
                    self.initialize()
                
                # Generate correlation ID
                correlation_id = generate_correlation_id()
                set_correlation_id(correlation_id)
                
                # Extract request information
                method = getattr(request, 'method', 'UNKNOWN')
                path = getattr(request, 'path', '/')
                
                op_name = operation_name or func.__name__
                
                # Start performance tracking
                start_time = time.time()
                timer_id = performance_monitor.start_timer(
                    op_name,
                    context={
                        'function_name': self.function_name,
                        'method': method,
                        'path': path,
                        'correlation_id': correlation_id,
                        'async': True
                    }
                )
                
                # Log function start
                log_function_start(op_name,
                                 method=method,
                                 path=path,
                                 correlation_id=correlation_id,
                                 function_name=self.function_name,
                                 async_function=True)
                
                try:
                    # Execute function
                    result = await func(request, *args, **kwargs)
                    
                    # Calculate duration
                    duration = time.time() - start_time
                    
                    # End performance tracking
                    performance_monitor.end_timer(timer_id, {'status': 'success', 'async': 'true'}, success=True)
                    
                    # Log function completion
                    log_function_end(op_name, duration,
                                   method=method,
                                   path=path,
                                   status='success',
                                   correlation_id=correlation_id,
                                   async_function=True)
                    
                    # Track business metrics
                    track_business_metric('async_function_executions', 1, {
                        'function_name': self.function_name,
                        'operation': op_name,
                        'status': 'success'
                    })
                    
                    return result
                    
                except Exception as e:
                    duration = time.time() - start_time
                    
                    # End performance tracking with error
                    performance_monitor.end_timer(timer_id, {'status': 'error', 'async': 'true'}, success=False)
                    
                    # Report error
                    error_tracker.report_error(e, {
                        'function_name': self.function_name,
                        'operation': op_name,
                        'method': method,
                        'path': path,
                        'correlation_id': correlation_id,
                        'duration': duration,
                        'async': True
                    })
                    
                    # Log error
                    log_error(op_name, e,
                             method=method,
                             path=path,
                             duration=duration,
                             correlation_id=correlation_id,
                             async_function=True)
                    
                    # Track error metrics
                    track_business_metric('async_function_errors', 1, {
                        'function_name': self.function_name,
                        'operation': op_name,
                        'error_type': type(e).__name__
                    })
                    
                    raise
            
            return wrapper
        return decorator
    
    def track_job_ingestion_metrics(self, jobs_found: int, jobs_processed: int, 
                                   jobs_saved: int, source: str = 'unknown'):
        """Track job ingestion metrics with comprehensive logging."""
        try:
            # Track detailed metrics
            track_job_ingestion(jobs_found, jobs_processed, jobs_saved, source)
            
            # Log business event
            log_business_event('job_ingestion_completed',
                             jobs_found=jobs_found,
                             jobs_processed=jobs_processed,
                             jobs_saved=jobs_saved,
                             source=source,
                             processing_rate=jobs_processed / jobs_found if jobs_found > 0 else 0,
                             save_rate=jobs_saved / jobs_processed if jobs_processed > 0 else 0)
            
            # Track individual metrics
            track_business_metric('jobs_found_total', jobs_found, {'source': source})
            track_business_metric('jobs_processed_total', jobs_processed, {'source': source})
            track_business_metric('jobs_saved_total', jobs_saved, {'source': source})
            
        except Exception as e:
            logger.error("Failed to track job ingestion metrics", error=e)
    
    def track_email_delivery_metrics(self, email_type: str, recipient_count: int, 
                                   success_count: int, bounce_count: int = 0, 
                                   complaint_count: int = 0):
        """Track email delivery metrics with comprehensive logging."""
        try:
            # Track detailed metrics
            track_email_delivery(email_type, recipient_count, success_count, 
                               bounce_count, complaint_count)
            
            # Log business event
            log_business_event('email_delivery_completed',
                             email_type=email_type,
                             recipient_count=recipient_count,
                             success_count=success_count,
                             bounce_count=bounce_count,
                             complaint_count=complaint_count,
                             delivery_rate=success_count / recipient_count if recipient_count > 0 else 0)
            
            # Track individual metrics
            track_business_metric('emails_sent_total', recipient_count, {'email_type': email_type})
            track_business_metric('emails_delivered_total', success_count, {'email_type': email_type})
            
        except Exception as e:
            logger.error("Failed to track email delivery metrics", error=e)
    
    def track_api_call_metrics(self, api_name: str, success: bool, 
                              duration_ms: float, status_code: Optional[int] = None):
        """Track external API call metrics."""
        try:
            # Track API call
            track_api_call(api_name, success, duration_ms, status_code)
            
            # Log performance metric
            log_performance_metric('api_call_duration', duration_ms, 'ms',
                                 api_name=api_name,
                                 success=success,
                                 status_code=status_code)
            
        except Exception as e:
            logger.error("Failed to track API call metrics", error=e)
    
    def get_monitoring_health(self) -> Dict[str, Any]:
        """Get comprehensive monitoring system health."""
        try:
            health_status = {
                'monitoring_initialized': self.initialized,
                'project_id': self.project_id,
                'environment': self.environment,
                'function_name': self.function_name,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Get monitoring system health if available
            if hasattr(monitoring, 'get_monitoring_health'):
                health_status['gcp_monitoring'] = monitoring.get_monitoring_health()
            
            return health_status
            
        except Exception as e:
            logger.error("Failed to get monitoring health", error=e)
            return {'status': 'error', 'error': str(e)}


# Global monitoring instance
career_copilot_monitoring = CareerCopilotMonitoring()

# Convenience decorators
def monitor_cloud_function(operation_name: Optional[str] = None):
    """Convenience decorator for monitoring Cloud Functions."""
    return career_copilot_monitoring.monitor_cloud_function(operation_name)

def monitor_async_cloud_function(operation_name: Optional[str] = None):
    """Convenience decorator for monitoring async Cloud Functions."""
    return career_copilot_monitoring.monitor_async_cloud_function(operation_name)

# Convenience functions
def track_job_metrics(jobs_found: int, jobs_processed: int, jobs_saved: int, source: str = 'unknown'):
    """Convenience function for tracking job ingestion metrics."""
    career_copilot_monitoring.track_job_ingestion_metrics(jobs_found, jobs_processed, jobs_saved, source)

def track_email_metrics(email_type: str, recipient_count: int, success_count: int, 
                       bounce_count: int = 0, complaint_count: int = 0):
    """Convenience function for tracking email delivery metrics."""
    career_copilot_monitoring.track_email_delivery_metrics(email_type, recipient_count, success_count, 
                                                          bounce_count, complaint_count)

def track_api_metrics(api_name: str, success: bool, duration_ms: float, status_code: Optional[int] = None):
    """Convenience function for tracking API call metrics."""
    career_copilot_monitoring.track_api_call_metrics(api_name, success, duration_ms, status_code)

def get_monitoring_health() -> Dict[str, Any]:
    """Get monitoring system health."""
    return career_copilot_monitoring.get_monitoring_health()

def initialize_monitoring() -> bool:
    """Initialize monitoring system."""
    return career_copilot_monitoring.initialize()