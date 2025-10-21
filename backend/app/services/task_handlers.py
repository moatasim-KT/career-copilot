"""
Task handlers for different types of background tasks.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, Optional

from ..core.logging import get_logger
from ..models.task_models import (
    TaskDefinition, TaskProgress, TaskType,
    ContractAnalysisTaskPayload, DocumentProcessingTaskPayload,
    BatchProcessingTaskPayload
)
from ..services.task_queue_service import TaskStorage

logger = get_logger(__name__)


async def update_task_progress(
    task_id: str,
    storage: TaskStorage,
    step: str,
    percentage: float,
    message: str,
    details: Optional[Dict[str, Any]] = None
):
    """Helper function to update task progress."""
    progress = TaskProgress(
        task_id=task_id,
        current_step=step,
        progress_percentage=percentage,
        message=message,
        details=details,
        updated_at=datetime.utcnow()
    )
    await storage.update_progress(progress)


async def handle_contract_analysis_task(
    task: TaskDefinition,
    storage: TaskStorage
) -> Dict[str, Any]:
    """Handle job application tracking background task."""
    logger.info(f"Starting job application tracking task {task.task_id}")
    
    try:
        # Parse payload
        payload = ContractAnalysisTaskPayload(**task.payload)
        
        # Update progress - initialization
        await update_task_progress(
            task.task_id, storage, "initializing", 5.0,
            "Initializing job application tracking"
        )
        
        # Import services (avoid circular imports)
        from ..agents.orchestration_service import get_orchestration_service
        from ..services.contract_analysis_service import get_contract_analysis_service
        
        # Get services
        orchestration_service = get_orchestration_service()
        analysis_service = get_contract_analysis_service()
        
        # Update progress - document processing
        await update_task_progress(
            task.task_id, storage, "processing_document", 15.0,
            "Processing contract document"
        )
        
        # Prepare analysis request
        analysis_request = {
            "contract_text": payload.contract_text,
            "filename": payload.contract_filename,
            "analysis_options": payload.analysis_options,
            "user_preferences": payload.user_preferences
        }
        
        # Update progress - AI analysis
        await update_task_progress(
            task.task_id, storage, "ai_analysis", 30.0,
            "Running AI analysis on contract"
        )
        
        # Execute job application tracking
        analysis_result = await analysis_service.analyze_contract_comprehensive(
            contract_text=payload.contract_text,
            filename=payload.contract_filename,
            enable_risk_assessment=payload.enable_risk_assessment,
            enable_precedent_search=payload.enable_precedent_search,
            enable_redline_generation=payload.enable_redline_generation,
            enable_negotiation_suggestions=payload.enable_negotiation_suggestions
        )
        
        # Update progress - risk assessment
        if payload.enable_risk_assessment:
            await update_task_progress(
                task.task_id, storage, "risk_assessment", 50.0,
                "Performing risk assessment"
            )
        
        # Update progress - precedent search
        if payload.enable_precedent_search:
            await update_task_progress(
                task.task_id, storage, "precedent_search", 65.0,
                "Searching for legal precedents"
            )
        
        # Update progress - redline generation
        if payload.enable_redline_generation:
            await update_task_progress(
                task.task_id, storage, "redline_generation", 80.0,
                "Generating redline suggestions"
            )
        
        # Update progress - report generation
        if payload.generate_report:
            await update_task_progress(
                task.task_id, storage, "report_generation", 90.0,
                "Generating analysis report"
            )
            
            # Generate report
            from ..services.report_generation_service import generate_analysis_report
            report_data = await generate_analysis_report(analysis_result, payload.contract_filename)
            analysis_result["report"] = report_data
        
        # Send email notifications if requested
        if payload.send_email_notification and payload.email_recipients:
            await update_task_progress(
                task.task_id, storage, "email_notification", 95.0,
                "Sending email notifications"
            )
            
            try:
                from ..services.email_service import get_email_service
                email_service = get_email_service()
                
                for recipient in payload.email_recipients:
                    await email_service.send_analysis_complete_notification(
                        recipient_email=recipient,
                        contract_name=payload.contract_filename,
                        analysis_result=analysis_result
                    )
            except Exception as e:
                logger.warning(f"Failed to send email notifications: {e}")
        
        # Final result
        result = {
            "contract_id": payload.contract_id,
            "analysis_result": analysis_result,
            "processing_metadata": {
                "task_id": task.task_id,
                "processed_at": datetime.utcnow().isoformat(),
                "analysis_options": payload.analysis_options,
                "features_enabled": {
                    "risk_assessment": payload.enable_risk_assessment,
                    "precedent_search": payload.enable_precedent_search,
                    "redline_generation": payload.enable_redline_generation,
                    "negotiation_suggestions": payload.enable_negotiation_suggestions
                }
            }
        }
        
        logger.info(f"Contract analysis task {task.task_id} completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Contract analysis task {task.task_id} failed: {e}", exc_info=True)
        raise


async def handle_document_processing_task(
    task: TaskDefinition,
    storage: TaskStorage
) -> Dict[str, Any]:
    """Handle document processing background task."""
    logger.info(f"Starting document processing task {task.task_id}")
    
    try:
        # Parse payload
        payload = DocumentProcessingTaskPayload(**task.payload)
        
        # Update progress - initialization
        await update_task_progress(
            task.task_id, storage, "initializing", 10.0,
            f"Starting {payload.processing_type} processing"
        )
        
        # Import document processor
        from ..services.document_processor import get_document_processor
        processor = get_document_processor()
        
        result = {}
        
        if payload.processing_type == "ocr":
            await update_task_progress(
                task.task_id, storage, "ocr_processing", 30.0,
                "Performing OCR on document"
            )
            
            ocr_result = await processor.perform_ocr(
                document_path=payload.document_path,
                options=payload.options
            )
            result["ocr_text"] = ocr_result
            
        elif payload.processing_type == "table_extraction":
            await update_task_progress(
                task.task_id, storage, "table_extraction", 40.0,
                "Extracting tables from document"
            )
            
            tables = await processor.extract_tables(
                document_path=payload.document_path,
                options=payload.options
            )
            result["tables"] = tables
            
        elif payload.processing_type == "structure_analysis":
            await update_task_progress(
                task.task_id, storage, "structure_analysis", 50.0,
                "Analyzing document structure"
            )
            
            structure = await processor.analyze_structure(
                document_path=payload.document_path,
                options=payload.options
            )
            result["structure"] = structure
        
        # Update progress - finalizing
        await update_task_progress(
            task.task_id, storage, "finalizing", 90.0,
            "Finalizing processing results"
        )
        
        # Add metadata
        result["processing_metadata"] = {
            "document_id": payload.document_id,
            "processing_type": payload.processing_type,
            "processed_at": datetime.utcnow().isoformat(),
            "options": payload.options
        }
        
        logger.info(f"Document processing task {task.task_id} completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Document processing task {task.task_id} failed: {e}", exc_info=True)
        raise


async def handle_batch_processing_task(
    task: TaskDefinition,
    storage: TaskStorage
) -> Dict[str, Any]:
    """Handle batch processing background task."""
    logger.info(f"Starting batch processing task {task.task_id}")
    
    try:
        # Parse payload
        payload = BatchProcessingTaskPayload(**task.payload)
        
        # Update progress - initialization
        await update_task_progress(
            task.task_id, storage, "initializing", 5.0,
            f"Starting batch processing of {len(payload.item_ids)} items"
        )
        
        results = []
        errors = []
        total_items = len(payload.item_ids)
        
        # Process items in batches
        semaphore = asyncio.Semaphore(payload.max_concurrent_items)
        
        async def process_item(item_id: str, index: int) -> Dict[str, Any]:
            async with semaphore:
                try:
                    # Update progress
                    progress_percentage = 10 + (index / total_items) * 80
                    await update_task_progress(
                        task.task_id, storage, "processing_items", progress_percentage,
                        f"Processing item {index + 1} of {total_items}: {item_id}"
                    )
                    
                    # Process based on type
                    if payload.processing_type == "contract_analysis":
                        # Get contract data and analyze
                        from ..services.contract_analysis_service import get_contract_analysis_service
                        analysis_service = get_contract_analysis_service()
                        
                        # This would need to be implemented based on how items are stored
                        item_result = await analysis_service.analyze_contract_by_id(item_id)
                        
                    elif payload.processing_type == "document_processing":
                        # Process document
                        from ..services.document_processor import get_document_processor
                        processor = get_document_processor()
                        
                        item_result = await processor.process_document_by_id(item_id)
                        
                    else:
                        raise ValueError(f"Unknown batch processing type: {payload.processing_type}")
                    
                    return {
                        "item_id": item_id,
                        "status": "completed",
                        "result": item_result
                    }
                    
                except Exception as e:
                    error_result = {
                        "item_id": item_id,
                        "status": "failed",
                        "error": str(e)
                    }
                    
                    if payload.continue_on_error:
                        logger.warning(f"Item {item_id} failed in batch {task.task_id}: {e}")
                        return error_result
                    else:
                        raise e
        
        # Process all items
        tasks = [
            process_item(item_id, index)
            for index, item_id in enumerate(payload.item_ids)
        ]
        
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Separate results and errors
        for result in batch_results:
            if isinstance(result, Exception):
                errors.append(str(result))
            elif result["status"] == "completed":
                results.append(result)
            else:
                errors.append(result)
        
        # Update progress - finalizing
        await update_task_progress(
            task.task_id, storage, "finalizing", 95.0,
            "Finalizing batch processing results"
        )
        
        # Send completion notification if requested
        if payload.notify_on_completion:
            try:
                from ..services.notification_manager import get_notification_manager
                notification_manager = get_notification_manager()
                
                await notification_manager.send_batch_completion_notification(
                    batch_id=payload.batch_id,
                    total_items=total_items,
                    successful_items=len(results),
                    failed_items=len(errors)
                )
            except Exception as e:
                logger.warning(f"Failed to send batch completion notification: {e}")
        
        # Final result
        final_result = {
            "batch_id": payload.batch_id,
            "processing_type": payload.processing_type,
            "total_items": total_items,
            "successful_items": len(results),
            "failed_items": len(errors),
            "results": results,
            "errors": errors,
            "processing_metadata": {
                "task_id": task.task_id,
                "processed_at": datetime.utcnow().isoformat(),
                "batch_options": payload.batch_options,
                "max_concurrent_items": payload.max_concurrent_items,
                "continue_on_error": payload.continue_on_error
            }
        }
        
        logger.info(f"Batch processing task {task.task_id} completed: {len(results)} successful, {len(errors)} failed")
        return final_result
        
    except Exception as e:
        logger.error(f"Batch processing task {task.task_id} failed: {e}", exc_info=True)
        raise


async def handle_report_generation_task(
    task: TaskDefinition,
    storage: TaskStorage
) -> Dict[str, Any]:
    """Handle report generation background task."""
    logger.info(f"Starting report generation task {task.task_id}")
    
    try:
        # Update progress - initialization
        await update_task_progress(
            task.task_id, storage, "initializing", 10.0,
            "Initializing report generation"
        )
        
        # Parse payload
        report_type = task.payload.get("report_type", "analysis_report")
        report_data = task.payload.get("report_data", {})
        output_format = task.payload.get("output_format", "pdf")
        
        # Update progress - data preparation
        await update_task_progress(
            task.task_id, storage, "data_preparation", 30.0,
            "Preparing report data"
        )
        
        # Import report service
        from ..services.report_generation_service import get_report_generation_service
        report_service = get_report_generation_service()
        
        # Update progress - report generation
        await update_task_progress(
            task.task_id, storage, "generating_report", 60.0,
            f"Generating {report_type} in {output_format} format"
        )
        
        # Generate report based on type
        if report_type == "analysis_report":
            report_result = await report_service.generate_analysis_report(
                analysis_data=report_data,
                output_format=output_format
            )
        elif report_type == "batch_report":
            report_result = await report_service.generate_batch_report(
                batch_data=report_data,
                output_format=output_format
            )
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        # Update progress - finalizing
        await update_task_progress(
            task.task_id, storage, "finalizing", 90.0,
            "Finalizing report"
        )
        
        result = {
            "report_type": report_type,
            "output_format": output_format,
            "report_data": report_result,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Report generation task {task.task_id} completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Report generation task {task.task_id} failed: {e}", exc_info=True)
        raise


async def handle_email_notification_task(
    task: TaskDefinition,
    storage: TaskStorage
) -> Dict[str, Any]:
    """Handle email notification background task."""
    logger.info(f"Starting email notification task {task.task_id}")
    
    try:
        # Update progress - initialization
        await update_task_progress(
            task.task_id, storage, "initializing", 10.0,
            "Preparing email notification"
        )
        
        # Parse payload
        email_type = task.payload.get("email_type", "notification")
        recipients = task.payload.get("recipients", [])
        email_data = task.payload.get("email_data", {})
        
        # Update progress - email preparation
        await update_task_progress(
            task.task_id, storage, "preparing_email", 30.0,
            f"Preparing {email_type} email for {len(recipients)} recipients"
        )
        
        # Import email service
        from ..services.email_service import get_email_service
        email_service = get_email_service()
        
        sent_emails = []
        failed_emails = []
        
        # Send emails to all recipients
        for i, recipient in enumerate(recipients):
            try:
                # Update progress
                progress_percentage = 30 + (i / len(recipients)) * 60
                await update_task_progress(
                    task.task_id, storage, "sending_emails", progress_percentage,
                    f"Sending email to {recipient} ({i + 1}/{len(recipients)})"
                )
                
                # Send email based on type
                if email_type == "analysis_complete":
                    await email_service.send_analysis_complete_notification(
                        recipient_email=recipient,
                        **email_data
                    )
                elif email_type == "risk_alert":
                    await email_service.send_risk_alert_notification(
                        recipient_email=recipient,
                        **email_data
                    )
                elif email_type == "batch_complete":
                    await email_service.send_batch_complete_notification(
                        recipient_email=recipient,
                        **email_data
                    )
                else:
                    await email_service.send_generic_notification(
                        recipient_email=recipient,
                        **email_data
                    )
                
                sent_emails.append(recipient)
                
            except Exception as e:
                logger.warning(f"Failed to send email to {recipient}: {e}")
                failed_emails.append({"recipient": recipient, "error": str(e)})
        
        # Update progress - finalizing
        await update_task_progress(
            task.task_id, storage, "finalizing", 95.0,
            "Finalizing email notifications"
        )
        
        result = {
            "email_type": email_type,
            "total_recipients": len(recipients),
            "sent_count": len(sent_emails),
            "failed_count": len(failed_emails),
            "sent_emails": sent_emails,
            "failed_emails": failed_emails,
            "sent_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Email notification task {task.task_id} completed: {len(sent_emails)} sent, {len(failed_emails)} failed")
        return result
        
    except Exception as e:
        logger.error(f"Email notification task {task.task_id} failed: {e}", exc_info=True)
        raise


# Task handler registry
TASK_HANDLERS = {
    TaskType.CONTRACT_ANALYSIS: handle_contract_analysis_task,
    TaskType.DOCUMENT_PROCESSING: handle_document_processing_task,
    TaskType.BATCH_PROCESSING: handle_batch_processing_task,
    TaskType.REPORT_GENERATION: handle_report_generation_task,
    TaskType.EMAIL_NOTIFICATION: handle_email_notification_task,
}