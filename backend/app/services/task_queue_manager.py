"""
Task Queue Manager for coordinating background job processing
"""

from typing import Dict, Any, List, Optional
from celery.result import AsyncResult
from datetime import datetime, timedelta
import json

from app.core.celery_app import celery_app
from app.core.logging import get_logger
from app.services.cache_service import cache_service

logger = get_logger(__name__)


class TaskQueueManager:
    """Manager for background task queues and job monitoring"""
    
    def __init__(self):
        self.celery_app = celery_app
    
    # Resume Parsing Tasks
    
    def submit_resume_parsing(
        self, 
        resume_upload_id: int, 
        file_path: str, 
        filename: str, 
        user_id: int,
        priority: str = "normal"
    ) -> str:
        """
        Submit a resume parsing task
        
        Args:
            resume_upload_id: ID of the ResumeUpload record
            file_path: Path to the uploaded file
            filename: Original filename
            user_id: ID of the user
            priority: Task priority (high, normal, low)
            
        Returns:
            Task ID
        """
        from app.tasks.resume_parsing_tasks import parse_resume_async
        
        # Set task options based on priority
        task_options = self._get_task_options(priority)
        
        result = parse_resume_async.apply_async(
            args=[resume_upload_id, file_path, filename, user_id],
            **task_options
        )
        
        # Store task metadata
        self._store_task_metadata(result.id, {
            "type": "resume_parsing",
            "user_id": user_id,
            "resume_upload_id": resume_upload_id,
            "filename": filename,
            "priority": priority,
            "submitted_at": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Submitted resume parsing task {result.id} for user {user_id}")
        return result.id
    
    def submit_batch_resume_parsing(self, resume_upload_ids: List[int]) -> str:
        """Submit batch resume parsing task"""
        from app.tasks.resume_parsing_tasks import batch_parse_resumes
        
        result = batch_parse_resumes.delay(resume_upload_ids)
        
        self._store_task_metadata(result.id, {
            "type": "batch_resume_parsing",
            "resume_count": len(resume_upload_ids),
            "submitted_at": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Submitted batch resume parsing task {result.id} for {len(resume_upload_ids)} resumes")
        return result.id
    
    # Content Generation Tasks
    
    def submit_cover_letter_generation(
        self,
        user_id: int,
        job_id: int,
        tone: str = "professional",
        custom_instructions: Optional[str] = None,
        priority: str = "normal"
    ) -> str:
        """Submit cover letter generation task"""
        from app.tasks.content_generation_tasks import generate_cover_letter_async
        
        task_options = self._get_task_options(priority)
        
        result = generate_cover_letter_async.apply_async(
            args=[user_id, job_id, tone, custom_instructions],
            **task_options
        )
        
        self._store_task_metadata(result.id, {
            "type": "cover_letter_generation",
            "user_id": user_id,
            "job_id": job_id,
            "tone": tone,
            "priority": priority,
            "submitted_at": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Submitted cover letter generation task {result.id} for user {user_id}, job {job_id}")
        return result.id
    
    def submit_resume_tailoring(
        self,
        user_id: int,
        job_id: int,
        resume_sections: Dict[str, str],
        priority: str = "normal"
    ) -> str:
        """Submit resume tailoring task"""
        from app.tasks.content_generation_tasks import generate_resume_tailoring_async
        
        task_options = self._get_task_options(priority)
        
        result = generate_resume_tailoring_async.apply_async(
            args=[user_id, job_id, resume_sections],
            **task_options
        )
        
        self._store_task_metadata(result.id, {
            "type": "resume_tailoring",
            "user_id": user_id,
            "job_id": job_id,
            "priority": priority,
            "submitted_at": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Submitted resume tailoring task {result.id} for user {user_id}, job {job_id}")
        return result.id
    
    def submit_batch_content_generation(self, content_requests: List[Dict]) -> str:
        """Submit batch content generation task"""
        from app.tasks.content_generation_tasks import batch_generate_content
        
        result = batch_generate_content.delay(content_requests)
        
        self._store_task_metadata(result.id, {
            "type": "batch_content_generation",
            "request_count": len(content_requests),
            "submitted_at": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Submitted batch content generation task {result.id} for {len(content_requests)} requests")
        return result.id
    
    # Job Scraping Tasks
    
    def submit_job_scraping_for_user(self, user_id: int, priority: str = "low") -> str:
        """Submit job scraping task for a specific user"""
        from app.tasks.job_scraping_tasks import scrape_jobs_for_user_async
        
        task_options = self._get_task_options(priority)
        
        result = scrape_jobs_for_user_async.apply_async(
            args=[user_id],
            **task_options
        )
        
        self._store_task_metadata(result.id, {
            "type": "job_scraping",
            "user_id": user_id,
            "priority": priority,
            "submitted_at": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Submitted job scraping task {result.id} for user {user_id}")
        return result.id
    
    def submit_batch_job_scraping(self, user_ids: List[int]) -> str:
        """Submit batch job scraping task"""
        from app.tasks.job_scraping_tasks import batch_scrape_jobs
        
        result = batch_scrape_jobs.delay(user_ids)
        
        self._store_task_metadata(result.id, {
            "type": "batch_job_scraping",
            "user_count": len(user_ids),
            "submitted_at": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Submitted batch job scraping task {result.id} for {len(user_ids)} users")
        return result.id
    
    # Notification Tasks
    
    def submit_email_notification(
        self,
        user_id: int,
        subject: str,
        content: str,
        email_type: str = "general",
        priority: str = "normal"
    ) -> str:
        """Submit email notification task"""
        from app.tasks.notification_tasks import send_email_async
        
        task_options = self._get_task_options(priority)
        
        result = send_email_async.apply_async(
            args=[user_id, subject, content, email_type],
            **task_options
        )
        
        self._store_task_metadata(result.id, {
            "type": "email_notification",
            "user_id": user_id,
            "email_type": email_type,
            "priority": priority,
            "submitted_at": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Submitted email notification task {result.id} for user {user_id}")
        return result.id
    
    def submit_job_alerts(self, user_id: int, job_matches: List[Dict]) -> str:
        """Submit job alerts task"""
        from app.tasks.notification_tasks import send_job_alerts_async
        
        result = send_job_alerts_async.delay(user_id, job_matches)
        
        self._store_task_metadata(result.id, {
            "type": "job_alerts",
            "user_id": user_id,
            "match_count": len(job_matches),
            "submitted_at": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Submitted job alerts task {result.id} for user {user_id} with {len(job_matches)} matches")
        return result.id
    
    # Analytics Tasks
    
    def submit_user_analytics_generation(self, user_id: int) -> str:
        """Submit user analytics generation task"""
        from app.tasks.analytics_tasks import generate_user_analytics
        
        result = generate_user_analytics.delay(user_id)
        
        self._store_task_metadata(result.id, {
            "type": "user_analytics",
            "user_id": user_id,
            "submitted_at": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Submitted user analytics task {result.id} for user {user_id}")
        return result.id
    
    def submit_system_analytics_generation(self) -> str:
        """Submit system analytics generation task"""
        from app.tasks.analytics_tasks import generate_system_analytics
        
        result = generate_system_analytics.delay()
        
        self._store_task_metadata(result.id, {
            "type": "system_analytics",
            "submitted_at": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Submitted system analytics task {result.id}")
        return result.id
    
    # Task Monitoring and Management
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the status of a specific task"""
        try:
            result = AsyncResult(task_id, app=self.celery_app)
            
            # Get task metadata
            metadata = self._get_task_metadata(task_id)
            
            status_info = {
                "task_id": task_id,
                "status": result.status,
                "result": result.result if result.ready() else None,
                "metadata": metadata,
                "traceback": result.traceback if result.failed() else None
            }
            
            # Add progress info if available
            if result.status == "PROGRESS" and hasattr(result, 'info'):
                status_info["progress"] = result.info
            
            return status_info
            
        except Exception as e:
            logger.error(f"Error getting task status for {task_id}: {e}")
            return {
                "task_id": task_id,
                "status": "UNKNOWN",
                "error": str(e)
            }
    
    def get_user_tasks(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent tasks for a specific user"""
        try:
            # Get task metadata from cache
            pattern = f"task_metadata:*"
            # This is a simplified implementation - in production you might want a more efficient approach
            
            user_tasks = []
            
            # In a real implementation, you'd store task-user relationships in a database
            # For now, we'll return a placeholder
            
            return user_tasks
            
        except Exception as e:
            logger.error(f"Error getting user tasks for {user_id}: {e}")
            return []
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        try:
            self.celery_app.control.revoke(task_id, terminate=True)
            logger.info(f"Cancelled task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get statistics about task queues"""
        try:
            # Get active tasks
            active_tasks = self.celery_app.control.inspect().active()
            
            # Get scheduled tasks
            scheduled_tasks = self.celery_app.control.inspect().scheduled()
            
            # Get reserved tasks
            reserved_tasks = self.celery_app.control.inspect().reserved()
            
            # Count tasks by queue
            queue_stats = {}
            
            if active_tasks:
                for worker, tasks in active_tasks.items():
                    for task in tasks:
                        queue = task.get('delivery_info', {}).get('routing_key', 'default')
                        if queue not in queue_stats:
                            queue_stats[queue] = {"active": 0, "scheduled": 0, "reserved": 0}
                        queue_stats[queue]["active"] += 1
            
            if scheduled_tasks:
                for worker, tasks in scheduled_tasks.items():
                    for task in tasks:
                        queue = task.get('delivery_info', {}).get('routing_key', 'default')
                        if queue not in queue_stats:
                            queue_stats[queue] = {"active": 0, "scheduled": 0, "reserved": 0}
                        queue_stats[queue]["scheduled"] += 1
            
            if reserved_tasks:
                for worker, tasks in reserved_tasks.items():
                    for task in tasks:
                        queue = task.get('delivery_info', {}).get('routing_key', 'default')
                        if queue not in queue_stats:
                            queue_stats[queue] = {"active": 0, "scheduled": 0, "reserved": 0}
                        queue_stats[queue]["reserved"] += 1
            
            return {
                "queue_stats": queue_stats,
                "total_active": sum(len(tasks) for tasks in (active_tasks or {}).values()),
                "total_scheduled": sum(len(tasks) for tasks in (scheduled_tasks or {}).values()),
                "total_reserved": sum(len(tasks) for tasks in (reserved_tasks or {}).values()),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {"error": str(e)}
    
    def cleanup_completed_tasks(self, days_old: int = 7) -> int:
        """Clean up completed task results older than specified days"""
        try:
            # This would typically involve cleaning up task results from the result backend
            # For now, we'll just clean up our metadata cache
            
            cutoff_time = datetime.utcnow() - timedelta(days=days_old)
            cleaned_count = 0
            
            # Clean up task metadata (simplified implementation)
            # In production, you'd want a more efficient approach
            
            logger.info(f"Cleaned up {cleaned_count} old task records")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up completed tasks: {e}")
            return 0
    
    # Helper methods
    
    def _get_task_options(self, priority: str) -> Dict[str, Any]:
        """Get task options based on priority"""
        options = {}
        
        if priority == "high":
            options["priority"] = 9
            options["queue"] = "high_priority"
        elif priority == "low":
            options["priority"] = 1
            options["queue"] = "low_priority"
        else:  # normal
            options["priority"] = 5
        
        return options
    
    def _store_task_metadata(self, task_id: str, metadata: Dict[str, Any]):
        """Store task metadata in cache"""
        try:
            cache_key = f"task_metadata:{task_id}"
            cache_service.set(cache_key, metadata, ttl=86400 * 7)  # Keep for 7 days
        except Exception as e:
            logger.error(f"Error storing task metadata for {task_id}: {e}")
    
    def _get_task_metadata(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task metadata from cache"""
        try:
            cache_key = f"task_metadata:{task_id}"
            return cache_service.get(cache_key)
        except Exception as e:
            logger.error(f"Error getting task metadata for {task_id}: {e}")
            return None


# Global task queue manager instance
task_queue_manager = TaskQueueManager()