"""
Background tasks for resume parsing
"""

from celery import current_task
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import os
import traceback

from app.core.celery_app import celery_app
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.resume_upload import ResumeUpload
from app.services.resume_parser_service import ResumeParserService
from app.services.cache_service import cache_service

logger = get_logger(__name__)


@celery_app.task(bind=True, name="app.tasks.resume_parsing_tasks.parse_resume_async")
def parse_resume_async(self, resume_upload_id: int, file_path: str, filename: str, user_id: int) -> Dict[str, Any]:
    """
    Parse a resume file asynchronously
    
    Args:
        resume_upload_id: ID of the ResumeUpload record
        file_path: Path to the uploaded file
        filename: Original filename
        user_id: ID of the user who uploaded the resume
        
    Returns:
        Dictionary with parsing results
    """
    db = next(get_db())
    
    try:
        # Update status to processing
        resume_upload = db.query(ResumeUpload).filter(ResumeUpload.id == resume_upload_id).first()
        if not resume_upload:
            raise ValueError(f"ResumeUpload {resume_upload_id} not found")
        
        resume_upload.parsing_status = "processing"
        db.commit()
        
        # Update task progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 10, "total": 100, "status": "Starting resume parsing..."}
        )
        
        # Initialize parser service
        parser_service = ResumeParserService()
        
        # Validate file
        self.update_state(
            state="PROGRESS",
            meta={"current": 20, "total": 100, "status": "Validating file..."}
        )
        
        is_valid, error_message = parser_service.validate_resume_file(file_path)
        if not is_valid:
            resume_upload.parsing_status = "failed"
            resume_upload.error_message = error_message
            db.commit()
            raise ValueError(f"File validation failed: {error_message}")
        
        # Parse the resume
        self.update_state(
            state="PROGRESS",
            meta={"current": 50, "total": 100, "status": "Parsing resume content..."}
        )
        
        parsed_data = await parser_service.parse_resume(file_path, filename, user_id)
        
        # Update database with results
        self.update_state(
            state="PROGRESS",
            meta={"current": 80, "total": 100, "status": "Saving parsed data..."}
        )
        
        resume_upload.parsed_data = parsed_data
        resume_upload.parsing_status = "completed"
        resume_upload.extracted_skills = parsed_data.get("skills", [])
        resume_upload.extracted_experience = parsed_data.get("experience_level")
        db.commit()
        
        # Clean up temporary file if needed
        if os.path.exists(file_path) and "/tmp/" in file_path:
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not clean up temporary file {file_path}: {e}")
        
        self.update_state(
            state="SUCCESS",
            meta={"current": 100, "total": 100, "status": "Resume parsing completed successfully"}
        )
        
        logger.info(f"Successfully parsed resume {filename} for user {user_id}")
        
        return {
            "status": "success",
            "resume_upload_id": resume_upload_id,
            "parsed_data": parsed_data,
            "message": "Resume parsed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error parsing resume {filename}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Update database with error
        try:
            resume_upload = db.query(ResumeUpload).filter(ResumeUpload.id == resume_upload_id).first()
            if resume_upload:
                resume_upload.parsing_status = "failed"
                resume_upload.error_message = str(e)
                db.commit()
        except Exception as db_error:
            logger.error(f"Error updating database with failure status: {db_error}")
        
        # Update task state
        self.update_state(
            state="FAILURE",
            meta={"current": 0, "total": 100, "status": f"Error: {str(e)}"}
        )
        
        raise self.retry(exc=e, countdown=60, max_retries=2)
    
    finally:
        db.close()


@celery_app.task(name="app.tasks.resume_parsing_tasks.process_resume_parsing_queue")
def process_resume_parsing_queue():
    """
    Process pending resume parsing requests
    """
    db = next(get_db())
    
    try:
        # Find pending resume uploads
        pending_uploads = db.query(ResumeUpload).filter(
            ResumeUpload.parsing_status == "pending"
        ).limit(10).all()
        
        if not pending_uploads:
            logger.debug("No pending resume uploads found")
            return {"processed": 0}
        
        processed_count = 0
        
        for upload in pending_uploads:
            try:
                # Check if file still exists
                if not os.path.exists(upload.file_path):
                    upload.parsing_status = "failed"
                    upload.error_message = "File not found"
                    db.commit()
                    continue
                
                # Submit parsing task
                parse_resume_async.delay(
                    resume_upload_id=upload.id,
                    file_path=upload.file_path,
                    filename=upload.filename,
                    user_id=upload.user_id
                )
                
                processed_count += 1
                logger.info(f"Submitted resume parsing task for upload {upload.id}")
                
            except Exception as e:
                logger.error(f"Error submitting parsing task for upload {upload.id}: {e}")
                upload.parsing_status = "failed"
                upload.error_message = f"Task submission failed: {str(e)}"
                db.commit()
        
        logger.info(f"Processed {processed_count} resume parsing requests")
        return {"processed": processed_count}
        
    except Exception as e:
        logger.error(f"Error processing resume parsing queue: {e}")
        return {"error": str(e)}
    
    finally:
        db.close()


@celery_app.task(name="app.tasks.resume_parsing_tasks.cleanup_old_resume_files")
def cleanup_old_resume_files(days_old: int = 30):
    """
    Clean up old resume files to save disk space
    
    Args:
        days_old: Delete files older than this many days
    """
    db = next(get_db())
    
    try:
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Find old resume uploads
        old_uploads = db.query(ResumeUpload).filter(
            ResumeUpload.created_at < cutoff_date,
            ResumeUpload.parsing_status.in_(["completed", "failed"])
        ).all()
        
        deleted_count = 0
        
        for upload in old_uploads:
            try:
                if os.path.exists(upload.file_path):
                    os.remove(upload.file_path)
                    deleted_count += 1
                    logger.info(f"Deleted old resume file: {upload.file_path}")
                
                # Optionally delete the database record too
                # db.delete(upload)
                
            except Exception as e:
                logger.error(f"Error deleting file {upload.file_path}: {e}")
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted_count} old resume files")
        return {"deleted": deleted_count}
        
    except Exception as e:
        logger.error(f"Error cleaning up old resume files: {e}")
        return {"error": str(e)}
    
    finally:
        db.close()


@celery_app.task(bind=True, name="app.tasks.resume_parsing_tasks.batch_parse_resumes")
def batch_parse_resumes(self, resume_upload_ids: list) -> Dict[str, Any]:
    """
    Parse multiple resumes in batch
    
    Args:
        resume_upload_ids: List of ResumeUpload IDs to process
        
    Returns:
        Dictionary with batch processing results
    """
    db = next(get_db())
    
    try:
        total_resumes = len(resume_upload_ids)
        processed = 0
        successful = 0
        failed = 0
        
        for i, upload_id in enumerate(resume_upload_ids):
            try:
                # Update progress
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i + 1,
                        "total": total_resumes,
                        "status": f"Processing resume {i + 1} of {total_resumes}",
                        "successful": successful,
                        "failed": failed
                    }
                )
                
                # Get upload record
                upload = db.query(ResumeUpload).filter(ResumeUpload.id == upload_id).first()
                if not upload:
                    failed += 1
                    continue
                
                # Submit individual parsing task
                result = parse_resume_async.delay(
                    resume_upload_id=upload.id,
                    file_path=upload.file_path,
                    filename=upload.filename,
                    user_id=upload.user_id
                )
                
                # Wait for result (with timeout)
                try:
                    result.get(timeout=300)  # 5 minutes timeout
                    successful += 1
                except Exception as e:
                    logger.error(f"Batch parsing failed for upload {upload_id}: {e}")
                    failed += 1
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Error in batch processing upload {upload_id}: {e}")
                failed += 1
                processed += 1
        
        self.update_state(
            state="SUCCESS",
            meta={
                "current": total_resumes,
                "total": total_resumes,
                "status": "Batch processing completed",
                "successful": successful,
                "failed": failed
            }
        )
        
        logger.info(f"Batch resume parsing completed: {successful} successful, {failed} failed")
        
        return {
            "status": "success",
            "total": total_resumes,
            "processed": processed,
            "successful": successful,
            "failed": failed
        }
        
    except Exception as e:
        logger.error(f"Error in batch resume parsing: {e}")
        
        self.update_state(
            state="FAILURE",
            meta={"status": f"Batch processing failed: {str(e)}"}
        )
        
        raise
    
    finally:
        db.close()