"""
Background tasks for content generation
"""

from celery import current_task
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import traceback

from app.core.celery_app import celery_app
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.content_generation import ContentGeneration
from app.models.job import Job
from app.models.user import User
from app.services.content_generator_service import ContentGeneratorService
from app.services.cache_service import cache_service

logger = get_logger(__name__)


@celery_app.task(bind=True, name="app.tasks.content_generation_tasks.generate_cover_letter_async")
def generate_cover_letter_async(
    self, 
    user_id: int, 
    job_id: int, 
    tone: str = "professional", 
    custom_instructions: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a cover letter asynchronously
    
    Args:
        user_id: ID of the user
        job_id: ID of the job
        tone: Tone of the cover letter
        custom_instructions: Additional instructions
        
    Returns:
        Dictionary with generation results
    """
    db = next(get_db())
    
    try:
        # Update task progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 10, "total": 100, "status": "Loading user and job data..."}
        )
        
        # Get user and job
        user = db.query(User).filter(User.id == user_id).first()
        job = db.query(Job).filter(Job.id == job_id).first()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Initialize content generator
        content_service = ContentGeneratorService()
        
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 30, "total": 100, "status": "Generating cover letter..."}
        )
        
        # Generate cover letter
        content_generation = await content_service.generate_cover_letter(
            user=user,
            job=job,
            tone=tone,
            custom_instructions=custom_instructions,
            db=db
        )
        
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 90, "total": 100, "status": "Finalizing generation..."}
        )
        
        self.update_state(
            state="SUCCESS",
            meta={"current": 100, "total": 100, "status": "Cover letter generated successfully"}
        )
        
        logger.info(f"Successfully generated cover letter for user {user_id} and job {job_id}")
        
        return {
            "status": "success",
            "content_generation_id": content_generation.id,
            "content": content_generation.generated_content,
            "message": "Cover letter generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error generating cover letter for user {user_id}, job {job_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        self.update_state(
            state="FAILURE",
            meta={"current": 0, "total": 100, "status": f"Error: {str(e)}"}
        )
        
        raise self.retry(exc=e, countdown=60, max_retries=2)
    
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.content_generation_tasks.generate_resume_tailoring_async")
def generate_resume_tailoring_async(
    self, 
    user_id: int, 
    job_id: int, 
    resume_sections: Dict[str, str]
) -> Dict[str, Any]:
    """
    Generate resume tailoring suggestions asynchronously
    
    Args:
        user_id: ID of the user
        job_id: ID of the job
        resume_sections: Dictionary of resume sections
        
    Returns:
        Dictionary with generation results
    """
    db = next(get_db())
    
    try:
        # Update task progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 10, "total": 100, "status": "Loading user and job data..."}
        )
        
        # Get user and job
        user = db.query(User).filter(User.id == user_id).first()
        job = db.query(Job).filter(Job.id == job_id).first()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Initialize content generator
        content_service = ContentGeneratorService()
        
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 30, "total": 100, "status": "Analyzing resume and job requirements..."}
        )
        
        # Generate resume tailoring
        content_generation = await content_service.generate_resume_tailoring(
            user=user,
            job=job,
            resume_sections=resume_sections,
            db=db
        )
        
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 90, "total": 100, "status": "Finalizing suggestions..."}
        )
        
        self.update_state(
            state="SUCCESS",
            meta={"current": 100, "total": 100, "status": "Resume tailoring completed successfully"}
        )
        
        logger.info(f"Successfully generated resume tailoring for user {user_id} and job {job_id}")
        
        return {
            "status": "success",
            "content_generation_id": content_generation.id,
            "content": content_generation.generated_content,
            "message": "Resume tailoring generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error generating resume tailoring for user {user_id}, job {job_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        self.update_state(
            state="FAILURE",
            meta={"current": 0, "total": 100, "status": f"Error: {str(e)}"}
        )
        
        raise self.retry(exc=e, countdown=60, max_retries=2)
    
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.content_generation_tasks.batch_generate_content")
def batch_generate_content(
    self, 
    content_requests: list
) -> Dict[str, Any]:
    """
    Generate multiple pieces of content in batch
    
    Args:
        content_requests: List of content generation requests
        Each request should have: user_id, job_id, content_type, and additional params
        
    Returns:
        Dictionary with batch generation results
    """
    try:
        total_requests = len(content_requests)
        processed = 0
        successful = 0
        failed = 0
        results = []
        
        for i, request in enumerate(content_requests):
            try:
                # Update progress
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i + 1,
                        "total": total_requests,
                        "status": f"Processing request {i + 1} of {total_requests}",
                        "successful": successful,
                        "failed": failed
                    }
                )
                
                content_type = request.get("content_type")
                user_id = request.get("user_id")
                job_id = request.get("job_id")
                
                if content_type == "cover_letter":
                    result = generate_cover_letter_async.delay(
                        user_id=user_id,
                        job_id=job_id,
                        tone=request.get("tone", "professional"),
                        custom_instructions=request.get("custom_instructions")
                    )
                elif content_type == "resume_tailoring":
                    result = generate_resume_tailoring_async.delay(
                        user_id=user_id,
                        job_id=job_id,
                        resume_sections=request.get("resume_sections", {})
                    )
                else:
                    raise ValueError(f"Unsupported content type: {content_type}")
                
                # Wait for result (with timeout)
                try:
                    task_result = result.get(timeout=300)  # 5 minutes timeout
                    results.append({
                        "request_index": i,
                        "status": "success",
                        "result": task_result
                    })
                    successful += 1
                except Exception as e:
                    logger.error(f"Batch content generation failed for request {i}: {e}")
                    results.append({
                        "request_index": i,
                        "status": "failed",
                        "error": str(e)
                    })
                    failed += 1
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Error in batch processing request {i}: {e}")
                results.append({
                    "request_index": i,
                    "status": "failed",
                    "error": str(e)
                })
                failed += 1
                processed += 1
        
        self.update_state(
            state="SUCCESS",
            meta={
                "current": total_requests,
                "total": total_requests,
                "status": "Batch content generation completed",
                "successful": successful,
                "failed": failed
            }
        )
        
        logger.info(f"Batch content generation completed: {successful} successful, {failed} failed")
        
        return {
            "status": "success",
            "total": total_requests,
            "processed": processed,
            "successful": successful,
            "failed": failed,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in batch content generation: {e}")
        
        self.update_state(
            state="FAILURE",
            meta={"status": f"Batch processing failed: {str(e)}"}
        )
        
        raise


@celery_app.task(name="app.tasks.content_generation_tasks.cleanup_old_content")
def cleanup_old_content(days_old: int = 90):
    """
    Clean up old generated content to save database space
    
    Args:
        days_old: Delete content older than this many days
    """
    db = next(get_db())
    
    try:
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Find old content generations
        old_content = db.query(ContentGeneration).filter(
            ContentGeneration.created_at < cutoff_date,
            ContentGeneration.status.in_(["generated", "user_modified"])
        ).all()
        
        deleted_count = 0
        
        for content in old_content:
            try:
                # Optionally archive important content before deletion
                if content.user_modifications:
                    # Keep user-modified content longer
                    continue
                
                db.delete(content)
                deleted_count += 1
                
            except Exception as e:
                logger.error(f"Error deleting content {content.id}: {e}")
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted_count} old content generations")
        return {"deleted": deleted_count}
        
    except Exception as e:
        logger.error(f"Error cleaning up old content: {e}")
        return {"error": str(e)}
    
    finally:
        db.close()


@celery_app.task(name="app.tasks.content_generation_tasks.pregenerate_popular_content")
def pregenerate_popular_content():
    """
    Pre-generate content for popular job/user combinations to improve response times
    """
    db = next(get_db())
    
    try:
        # Find popular job/user combinations
        # This is a simplified example - you might want more sophisticated logic
        
        from sqlalchemy import func
        
        # Get jobs with the most applications
        popular_jobs = db.query(Job).join(Job.applications).group_by(Job.id).order_by(
            func.count(Job.applications).desc()
        ).limit(10).all()
        
        # Get active users
        active_users = db.query(User).filter(
            User.skills.isnot(None)
        ).limit(20).all()
        
        generated_count = 0
        
        for job in popular_jobs:
            for user in active_users:
                try:
                    # Check if content already exists
                    existing_content = db.query(ContentGeneration).filter(
                        ContentGeneration.user_id == user.id,
                        ContentGeneration.job_id == job.id,
                        ContentGeneration.content_type == "cover_letter"
                    ).first()
                    
                    if existing_content:
                        continue
                    
                    # Generate cover letter in background
                    generate_cover_letter_async.delay(
                        user_id=user.id,
                        job_id=job.id,
                        tone="professional"
                    )
                    
                    generated_count += 1
                    
                    # Limit to avoid overwhelming the system
                    if generated_count >= 50:
                        break
                        
                except Exception as e:
                    logger.error(f"Error pre-generating content for user {user.id}, job {job.id}: {e}")
            
            if generated_count >= 50:
                break
        
        logger.info(f"Submitted {generated_count} pre-generation tasks")
        return {"submitted": generated_count}
        
    except Exception as e:
        logger.error(f"Error in pre-generating content: {e}")
        return {"error": str(e)}
    
    finally:
        db.close()