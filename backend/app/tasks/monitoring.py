"""
Celery task monitoring and error handling
"""

import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from celery import current_task
from celery.signals import task_prerun, task_postrun, task_failure, task_retry
from sqlalchemy.orm import Session

from app.celery import celery_app
from app.core.database import get_db
from app.models.analytics import Analytics
from app.services.notification_service import notification_service


logger = logging.getLogger(__name__)


class TaskMonitor:
    """Task monitoring and error handling utilities"""
    
    @staticmethod
    def log_task_start(task_name: str, task_id: str, args: tuple = None, kwargs: dict = None):
        """Log task start with context"""
        logger.info(f"Task {task_name} [{task_id}] started", extra={
            'task_name': task_name,
            'task_id': task_id,
            'args': args,
            'kwargs': kwargs,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @staticmethod
    def log_task_success(task_name: str, task_id: str, result: Any, runtime: float):
        """Log successful task completion"""
        logger.info(f"Task {task_name} [{task_id}] completed successfully in {runtime:.2f}s", extra={
            'task_name': task_name,
            'task_id': task_id,
            'result': str(result)[:500],  # Truncate long results
            'runtime': runtime,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @staticmethod
    def log_task_failure(task_name: str, task_id: str, error: Exception, traceback_str: str):
        """Log task failure with full context"""
        logger.error(f"Task {task_name} [{task_id}] failed: {str(error)}", extra={
            'task_name': task_name,
            'task_id': task_id,
            'error': str(error),
            'traceback': traceback_str,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @staticmethod
    def save_task_metrics(db: Session, task_name: str, task_id: str, 
                         status: str, runtime: float = None, error: str = None):
        """Save task execution metrics to database"""
        try:
            metrics_data = {
                'task_id': task_id,
                'status': status,
                'timestamp': datetime.utcnow().isoformat(),
                'runtime': runtime,
                'error': error
            }
            
            analytics = Analytics(
                user_id=None,  # System-level analytics
                type=f"task_metrics_{task_name}",
                data=metrics_data
            )
            
            db.add(analytics)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to save task metrics: {str(e)}")
            db.rollback()


# Celery signal handlers
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Handle task pre-run signal"""
    TaskMonitor.log_task_start(task.name, task_id, args, kwargs)


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, 
                        retval=None, state=None, **kwds):
    """Handle task post-run signal"""
    if hasattr(task, '_start_time'):
        runtime = (datetime.utcnow() - task._start_time).total_seconds()
    else:
        runtime = 0
    
    if state == 'SUCCESS':
        TaskMonitor.log_task_success(task.name, task_id, retval, runtime)
        
        # Save metrics to database
        try:
            db = next(get_db())
            try:
                TaskMonitor.save_task_metrics(db, task.name, task_id, 'SUCCESS', runtime)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to save success metrics: {str(e)}")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """Handle task failure signal"""
    task_name = sender.name if sender else 'unknown'
    traceback_str = str(traceback) if traceback else str(einfo)
    
    TaskMonitor.log_task_failure(task_name, task_id, exception, traceback_str)
    
    # Save failure metrics to database
    try:
        db = next(get_db())
        try:
            TaskMonitor.save_task_metrics(db, task_name, task_id, 'FAILURE', error=str(exception))
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to save failure metrics: {str(e)}")
    
    # Send alert for critical failures
    if is_critical_task(task_name):
        send_failure_alert(task_name, task_id, exception)


@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kwds):
    """Handle task retry signal"""
    task_name = sender.name if sender else 'unknown'
    logger.warning(f"Task {task_name} [{task_id}] retrying: {reason}")


def is_critical_task(task_name: str) -> bool:
    """Determine if a task is critical and requires immediate attention"""
    critical_tasks = [
        'app.services.job_ingestion.ingest_jobs',
        'send_morning_briefings',
        'generate_skill_gap_analysis'
    ]
    return task_name in critical_tasks


def send_failure_alert(task_name: str, task_id: str, exception: Exception):
    """Send failure alert for critical tasks"""
    try:
        # In a real implementation, this would send to admin email or Slack
        logger.critical(f"CRITICAL TASK FAILURE: {task_name} [{task_id}] - {str(exception)}")
        
        # Could also save to a special alerts table or send email
        # notification_service.send_admin_alert(task_name, task_id, str(exception))
        
    except Exception as e:
        logger.error(f"Failed to send failure alert: {str(e)}")


@celery_app.task(name="monitor_task_health")
def monitor_task_health() -> Dict[str, Any]:
    """Monitor overall task system health"""
    try:
        db = next(get_db())
        try:
            # Get task metrics from last 24 hours
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            # Query task metrics
            recent_metrics = db.query(Analytics).filter(
                Analytics.type.like('task_metrics_%'),
                Analytics.generated_at >= cutoff_time
            ).all()
            
            # Analyze metrics
            total_tasks = len(recent_metrics)
            failed_tasks = len([m for m in recent_metrics if m.data.get('status') == 'FAILURE'])
            success_rate = ((total_tasks - failed_tasks) / total_tasks * 100) if total_tasks > 0 else 100
            
            # Calculate average runtime for successful tasks
            successful_tasks = [m for m in recent_metrics if m.data.get('status') == 'SUCCESS' and m.data.get('runtime')]
            avg_runtime = sum(m.data['runtime'] for m in successful_tasks) / len(successful_tasks) if successful_tasks else 0
            
            # Group by task type
            task_stats = {}
            for metric in recent_metrics:
                task_type = metric.type.replace('task_metrics_', '')
                if task_type not in task_stats:
                    task_stats[task_type] = {'total': 0, 'failed': 0, 'avg_runtime': 0}
                
                task_stats[task_type]['total'] += 1
                if metric.data.get('status') == 'FAILURE':
                    task_stats[task_type]['failed'] += 1
                
                if metric.data.get('runtime'):
                    task_stats[task_type]['avg_runtime'] += metric.data['runtime']
            
            # Calculate averages
            for task_type, stats in task_stats.items():
                if stats['total'] > 0:
                    stats['success_rate'] = ((stats['total'] - stats['failed']) / stats['total']) * 100
                    stats['avg_runtime'] = stats['avg_runtime'] / stats['total']
                else:
                    stats['success_rate'] = 100
            
            health_report = {
                'timestamp': datetime.utcnow().isoformat(),
                'period_hours': 24,
                'overall_stats': {
                    'total_tasks': total_tasks,
                    'failed_tasks': failed_tasks,
                    'success_rate': success_rate,
                    'avg_runtime': avg_runtime
                },
                'task_stats': task_stats,
                'health_status': 'healthy' if success_rate >= 95 else 'degraded' if success_rate >= 85 else 'unhealthy'
            }
            
            # Save health report
            health_analytics = Analytics(
                user_id=None,
                type='task_system_health',
                data=health_report
            )
            db.add(health_analytics)
            db.commit()
            
            logger.info(f"Task health check completed: {health_report['health_status']} "
                       f"({success_rate:.1f}% success rate)")
            
            return health_report
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"Task health monitoring failed: {str(e)}"
        logger.error(error_msg)
        return {
            'error': error_msg,
            'timestamp': datetime.utcnow().isoformat(),
            'health_status': 'unknown'
        }


@celery_app.task(name="cleanup_task_metrics")
def cleanup_task_metrics() -> Dict[str, Any]:
    """Clean up old task metrics (keep last 30 days)"""
    try:
        db = next(get_db())
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=30)
            
            # Delete old task metrics
            deleted_count = db.query(Analytics).filter(
                Analytics.type.like('task_metrics_%'),
                Analytics.generated_at < cutoff_time
            ).delete()
            
            db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old task metrics")
            
            return {
                'deleted_count': deleted_count,
                'cutoff_date': cutoff_time.isoformat(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"Task metrics cleanup failed: {str(e)}"
        logger.error(error_msg)
        return {
            'error': error_msg,
            'timestamp': datetime.utcnow().isoformat()
        }


@celery_app.task(name="get_task_status")
def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get status of a specific task"""
    try:
        # Get task result from Celery
        result = celery_app.AsyncResult(task_id)
        
        status_info = {
            'task_id': task_id,
            'status': result.status,
            'result': result.result if result.ready() else None,
            'traceback': result.traceback if result.failed() else None,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Get additional info from database if available
        try:
            db = next(get_db())
            try:
                task_metrics = db.query(Analytics).filter(
                    Analytics.type.like('task_metrics_%'),
                    Analytics.data['task_id'].astext == task_id
                ).first()
                
                if task_metrics:
                    status_info['metrics'] = task_metrics.data
                    
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Could not fetch task metrics from database: {str(e)}")
        
        return status_info
        
    except Exception as e:
        error_msg = f"Failed to get task status: {str(e)}"
        logger.error(error_msg)
        return {
            'task_id': task_id,
            'error': error_msg,
            'timestamp': datetime.utcnow().isoformat()
        }


@celery_app.task(name="system_health_check")
def system_health_check() -> Dict[str, Any]:
    """Comprehensive system health check task"""
    try:
        import psutil
        import redis
        from sqlalchemy import text
        
        health_report = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy',
            'components': {}
        }
        
        # System resources check
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_report['components']['system'] = {
                'status': 'healthy',
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent
            }
            
            # Alert on high resource usage
            if cpu_percent > 80 or memory.percent > 85 or disk.percent > 90:
                health_report['components']['system']['status'] = 'warning'
                health_report['overall_status'] = 'degraded'
                
        except Exception as e:
            health_report['components']['system'] = {
                'status': 'error',
                'error': str(e)
            }
            health_report['overall_status'] = 'unhealthy'
        
        # Database check
        try:
            db = next(get_db())
            try:
                start_time = datetime.utcnow()
                db.execute(text("SELECT 1"))
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                health_report['components']['database'] = {
                    'status': 'healthy',
                    'response_time_seconds': response_time
                }
                
                if response_time > 2.0:
                    health_report['components']['database']['status'] = 'warning'
                    health_report['overall_status'] = 'degraded'
                    
            finally:
                db.close()
                
        except Exception as e:
            health_report['components']['database'] = {
                'status': 'error',
                'error': str(e)
            }
            health_report['overall_status'] = 'unhealthy'
        
        # Redis check
        try:
            r = redis.from_url(settings.REDIS_URL)
            start_time = datetime.utcnow()
            r.ping()
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            health_report['components']['redis'] = {
                'status': 'healthy',
                'response_time_seconds': response_time
            }
            
        except Exception as e:
            health_report['components']['redis'] = {
                'status': 'degraded',
                'error': str(e)
            }
            if health_report['overall_status'] == 'healthy':
                health_report['overall_status'] = 'degraded'
        
        # Save health report
        try:
            db = next(get_db())
            try:
                health_analytics = Analytics(
                    user_id=None,
                    type='system_health_check',
                    data=health_report
                )
                db.add(health_analytics)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to save health report: {str(e)}")
        
        logger.info(f"System health check completed: {health_report['overall_status']}")
        return health_report
        
    except Exception as e:
        error_msg = f"System health check failed: {str(e)}"
        logger.error(error_msg)
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'error',
            'error': error_msg
        }


@celery_app.task(name="automated_backup")
def automated_backup(include_files: bool = True, compress: bool = True) -> Dict[str, Any]:
    """Automated backup task"""
    try:
        from app.services.backup_service import backup_service
        
        logger.info("Starting automated backup")
        
        backup_info = backup_service.create_full_backup(
            include_files=include_files,
            compress=compress
        )
        
        # Clean up old backups (keep last 7 days for automated backups)
        cleanup_info = backup_service.cleanup_old_backups(keep_days=7)
        backup_info['cleanup'] = cleanup_info
        
        logger.info(f"Automated backup completed: {backup_info.get('backup_id')}")
        return backup_info
        
    except Exception as e:
        error_msg = f"Automated backup failed: {str(e)}"
        logger.error(error_msg)
        return {
            'error': error_msg,
            'timestamp': datetime.utcnow().isoformat()
        }


@celery_app.task(name="log_rotation")
def log_rotation() -> Dict[str, Any]:
    """Rotate and compress old log files"""
    try:
        from pathlib import Path
        import gzip
        import shutil
        
        logs_dir = Path("logs")
        if not logs_dir.exists():
            return {'message': 'No logs directory found'}
        
        rotated_files = []
        
        # Rotate log files older than 1 day
        cutoff_time = datetime.utcnow() - timedelta(days=1)
        
        for log_file in logs_dir.glob("*.log"):
            if log_file.is_file():
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                
                if file_time < cutoff_time:
                    # Compress and rotate
                    compressed_name = f"{log_file.stem}_{file_time.strftime('%Y%m%d')}.log.gz"
                    compressed_path = logs_dir / compressed_name
                    
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(compressed_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # Remove original
                    log_file.unlink()
                    
                    rotated_files.append({
                        'original': str(log_file),
                        'compressed': str(compressed_path),
                        'size_reduction': log_file.stat().st_size - compressed_path.stat().st_size
                    })
        
        # Clean up old compressed logs (keep 30 days)
        old_cutoff = datetime.utcnow() - timedelta(days=30)
        deleted_files = []
        
        for compressed_file in logs_dir.glob("*.log.gz"):
            if compressed_file.is_file():
                file_time = datetime.fromtimestamp(compressed_file.stat().st_mtime)
                
                if file_time < old_cutoff:
                    compressed_file.unlink()
                    deleted_files.append(str(compressed_file))
        
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'rotated_files': rotated_files,
            'deleted_files': deleted_files,
            'total_rotated': len(rotated_files),
            'total_deleted': len(deleted_files)
        }
        
        logger.info(f"Log rotation completed: {len(rotated_files)} rotated, {len(deleted_files)} deleted")
        return result
        
    except Exception as e:
        error_msg = f"Log rotation failed: {str(e)}"
        logger.error(error_msg)
        return {
            'error': error_msg,
            'timestamp': datetime.utcnow().isoformat()
        }