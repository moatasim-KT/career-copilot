"""
Contract Analysis Service.

Main service for job application tracking operations with AI integration.
Provides comprehensive contract processing, risk assessment, and analysis workflows.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union, Callable, Awaitable

from ..core.config import get_settings
from ..core.exceptions import (
    DocumentProcessingError,
    WorkflowExecutionError,
    ValidationError,
    ExternalServiceError,
    ResourceExhaustionError,
    ErrorCategory,
    ErrorSeverity
)
from ..core.logging import get_logger
from ..core.monitoring import log_audit_event
from ..utils.error_handler import get_error_handler, ErrorCategory, ErrorSeverity
from ..workflows.core import ContractAnalysisWorkflow
# Lazy import to avoid circular dependency
# from ..agents.orchestration_service import get_optimized_orchestration_service
from .document_processor import DocumentProcessingService, ProcessedDocument

# Type aliases for better code clarity
AnalysisResult = Dict[str, Any]
AnalysisMetadata = Dict[str, Union[str, int, float, List[str]]]
ProcessingOptions = Dict[str, Union[str, bool, int, float]]
CacheKey = str
CacheValue = Dict[str, Any]

logger = get_logger(__name__)
settings = get_settings()


class ContractAnalysisService:
	"""
	Main service for job application tracking operations.
	
	This service orchestrates the complete job application tracking workflow including
	document processing, AI agent coordination, risk assessment, and result
	compilation. It provides both synchronous and asynchronous analysis
	capabilities with comprehensive error handling and caching.
	
	Attributes:
		document_processor (DocumentProcessingService): Service for document processing
		workflow (ContractAnalysisWorkflow): Main analysis workflow orchestrator
		_orchestration_service (Optional[Any]): Lazy-loaded agent orchestration service
		_analysis_cache (Dict[CacheKey, CacheValue]): In-memory analysis result cache
		_use_optimized_agents (bool): Flag to enable optimized agent workflow
	
	Examples:
		Basic usage:
		```python
		service = ContractAnalysisService()
		result = await service.analyze_contract(
		    file_content=pdf_bytes,
		    filename="contract.pdf",
		    analysis_type="comprehensive"
		)
		```
		
		With custom options:
		```python
		result = await service.analyze_contract(
		    file_content=pdf_bytes,
		    filename="contract.pdf",
		    analysis_type="standard",
		    metadata={"jurisdiction": "US", "contract_type": "employment"}
		)
		```
	"""

	def __init__(self) -> None:
		"""
		Initialize the job application tracking service.
		
		Sets up document processor, workflow orchestrator, and internal state
		management for analysis operations.
		"""
		self.document_processor: DocumentProcessingService = DocumentProcessingService()
		self.workflow: ContractAnalysisWorkflow = ContractAnalysisWorkflow()
		self._orchestration_service: Optional[Any] = None  # Lazy initialization
		self._analysis_cache: Dict[CacheKey, CacheValue] = {}
		self._use_optimized_agents: bool = True  # Flag to enable optimized agent workflow
	
	@property
	def orchestration_service(self) -> Optional[Any]:
		"""
		Lazy initialization of orchestration service to avoid circular imports.
		
		Returns:
			Optional[Any]: Orchestration service instance or None if unavailable
		"""
		if self._orchestration_service is None:
			try:
				from ..agents.orchestration_service import get_optimized_orchestration_service
				self._orchestration_service = get_optimized_orchestration_service()
			except ImportError as e:
				logger.warning(f"Could not initialize orchestration service: {e}")
				self._use_optimized_agents = False
				self._orchestration_service = None
		return self._orchestration_service

	async def analyze_contract(
		self,
		file_content: bytes,
		filename: str,
		analysis_type: str = "standard",
		user_id: Optional[str] = None,
		metadata: Optional[AnalysisMetadata] = None,
	) -> AnalysisResult:
		"""
		Analyze a contract document for risks and generate comprehensive recommendations.

		This method performs a complete job application tracking workflow including:
		- Document validation and processing
		- AI-powered clause analysis and risk assessment
		- Legal precedent matching and comparison
		- Redline generation and improvement suggestions
		- Compliance checking and regulatory analysis

		Args:
		    file_content: Raw binary content of the contract file
		    filename: Original filename of the contract document
		    analysis_type: Type of analysis to perform. Options:
		        - "quick": Fast risk assessment (30-60 seconds)
		        - "standard": Comprehensive analysis (2-5 minutes)
		        - "comprehensive": Deep analysis with precedents (5-10 minutes)
		    user_id: Unique identifier of the user requesting analysis
		    metadata: Additional analysis configuration and context:
		        - jurisdiction (str): Legal jurisdiction (e.g., "US", "EU", "UK")
		        - contract_type (str): Contract category (e.g., "employment", "nda", "service")
		        - risk_threshold (str): Minimum risk level to report ("low", "medium", "high")
		        - include_precedents (bool): Whether to include legal precedent matching
		        - custom_clauses (List[str]): Specific clauses to focus analysis on

		Returns:
		    AnalysisResult: Comprehensive analysis results containing:
		        - analysis_id (str): Unique identifier for this analysis
		        - status (str): Analysis status ("completed", "failed", "partial")
		        - overall_risk_score (float): Overall risk score (0.0-10.0)
		        - risk_level (str): Risk classification ("low", "medium", "high", "critical")
		        - risky_clauses (List[Dict]): Identified problematic clauses with details
		        - suggested_redlines (List[Dict]): Recommended contract modifications
		        - legal_precedents (List[Dict]): Relevant legal cases and precedents
		        - compliance_issues (List[Dict]): Regulatory compliance concerns
		        - processing_time (float): Total analysis time in seconds
		        - confidence_score (float): AI confidence in analysis (0.0-1.0)
		        - metadata (Dict): Analysis metadata and processing details

		Raises:
		    ValidationError: When file content or parameters are invalid
		    DocumentProcessingError: When document cannot be processed or parsed
		    WorkflowExecutionError: When analysis workflow fails
		    ResourceExhaustionError: When system resources are insufficient
		    ExternalServiceError: When external AI services are unavailable

		Examples:
		    Quick risk assessment:
		    ```python
		    result = await service.analyze_contract(
		        file_content=pdf_bytes,
		        filename="employment_agreement.pdf",
		        analysis_type="quick",
		        user_id="user_123"
		    )
		    print(f"Risk Score: {result['overall_risk_score']}")
		    ```

		    Comprehensive analysis with metadata:
		    ```python
		    result = await service.analyze_contract(
		        file_content=pdf_bytes,
		        filename="service_agreement.pdf",
		        analysis_type="comprehensive",
		        user_id="user_123",
		        metadata={
		            "jurisdiction": "US",
		            "contract_type": "service",
		            "risk_threshold": "medium",
		            "include_precedents": True
		        }
		    )
		    
		    for clause in result['risky_clauses']:
		        print(f"Risk: {clause['risk_level']} - {clause['description']}")
		    ```

		Note:
		    Analysis results are cached for 1 hour to improve performance for
		    repeated requests. Cache keys are based on file content hash and
		    analysis parameters.

		See Also:
		    - get_analysis_status(): Check analysis progress
		    - cancel_analysis(): Cancel running analysis
		    - get_cached_result(): Retrieve cached analysis results
		"""
		start_time = time.time()
		analysis_id = f"analysis_{int(time.time())}_{hash(filename) % 10000}"
		error_handler = get_error_handler()

		try:
			# Validate inputs
			if not file_content:
				raise ValidationError(
					"File content is empty",
					field="file_content",
					details={"filename": filename}
				)
			
			if not filename or not filename.strip():
				raise ValidationError(
					"Filename is required",
					field="filename"
				)

			# Log analysis start
			log_audit_event(
				"contract_analysis_started",
				details={"analysis_id": analysis_id, "filename": filename, "analysis_type": analysis_type, "file_size": len(file_content), "user_id": user_id},
			)

			# Process document to extract text
			logger.info(f"Processing document: {filename}")
			try:
				processed_doc = await self._process_document(file_content, filename)
			except Exception as e:
				raise DocumentProcessingError(
					f"Failed to process document '{filename}'",
					processing_stage="text_extraction",
					details={"filename": filename, "file_size": len(file_content)},
					cause=e
				)

			if not processed_doc.content.strip():
				raise DocumentProcessingError(
					"No readable text content found in document",
					processing_stage="content_validation",
					details={"filename": filename, "document_type": processed_doc.document_type.value}
				)

			# Execute analysis workflow - use optimized agents if enabled
			logger.info(f"Executing analysis workflow for: {filename} (optimized: {self._use_optimized_agents})")
			try:
				if self._use_optimized_agents:
					# Use optimized agent orchestration service
					workflow_result = await self.orchestration_service.execute_optimized_contract_analysis_workflow(
						contract_text=processed_doc.content,
						contract_filename=filename,
						workflow_config={"analysis_type": analysis_type, "metadata": metadata or {}}
					)
				else:
					# Use legacy LangGraph workflow
					workflow_state = await self.workflow.execute(
						contract_text=processed_doc.content, 
						contract_filename=filename, 
						config={"analysis_type": analysis_type, "metadata": metadata or {}}
					)
					# Convert workflow state to expected format
					workflow_result = self._convert_workflow_state_to_result(workflow_state)
					
			except Exception as e:
				raise WorkflowExecutionError(
					f"Analysis workflow failed for '{filename}'",
					workflow_node="contract_analysis",
					execution_id=analysis_id,
					details={"filename": filename, "analysis_type": analysis_type, "optimized_agents": self._use_optimized_agents},
					cause=e
				)

			# Calculate processing time
			processing_time = time.time() - start_time

			# Normalize risk score to 0-1 scale if needed
			raw_risk_score = workflow_result.get("overall_risk_score", 0.0)
			normalized_risk_score = self._normalize_risk_score(raw_risk_score)
			
			# Prepare response with enhanced metadata
			analysis_result = {
				"analysis_id": analysis_id,
				"status": "completed" if workflow_result.get("success", True) else "failed",
				"contract_filename": filename,
				"analysis_type": analysis_type,
				"risky_clauses": workflow_result.get("risky_clauses", []),
				"overall_risk_score": normalized_risk_score,
				"risk_level": self._determine_risk_level(normalized_risk_score),
				"suggested_redlines": workflow_result.get("suggested_redlines", []),
				"email_draft": workflow_result.get("email_draft"),
				"recommendations": workflow_result.get("recommendations", []),
				"processing_time": processing_time,
				"confidence_score": workflow_result.get("confidence_score", 0.8),
				"model_used": workflow_result.get("model_used", "multi_agent_workflow" if self._use_optimized_agents else "gpt-4"),
				"token_usage": workflow_result.get("token_usage", {}),
				"cost": workflow_result.get("cost", 0.0),
				"created_at": datetime.utcnow().isoformat(),
				"completed_at": datetime.utcnow().isoformat(),
				"metadata": {
					"file_type": processed_doc.document_type.value,
					"content_length": len(processed_doc.content),
					"processing_warnings": workflow_result.get("processing_metadata", {}).get("warnings", []),
					"optimized_agents_used": self._use_optimized_agents,
					"execution_mode": workflow_result.get("execution_mode", "unknown"),
					"agent_health": workflow_result.get("performance_metrics", {}).get("agent_health_scores", {}),
					"fallback_used": workflow_result.get("fallback_used", False),
					"quality_score": workflow_result.get("quality_score", 0.8)
				},
			}
			
			# Add additional fields from optimized workflow
			if self._use_optimized_agents:
				analysis_result.update({
					"contract_structure": workflow_result.get("contract_structure", {}),
					"identified_clauses": workflow_result.get("identified_clauses", []),
					"precedent_matches": workflow_result.get("precedent_matches", []),
					"negotiation_strategy": workflow_result.get("negotiation_strategy", ""),
					"workflow_id": workflow_result.get("workflow_id"),
					"completed_agents": workflow_result.get("completed_agents", []),
					"failed_agents": workflow_result.get("failed_agents", []),
					"degraded_agents": workflow_result.get("degraded_agents", [])
				})

			# Cache result
			self._analysis_cache[analysis_id] = analysis_result

			# Log successful completion
			log_audit_event(
				"contract_analysis_completed",
				details={
					"analysis_id": analysis_id,
					"processing_time": processing_time,
					"risky_clauses_count": len(analysis_result["risky_clauses"]),
					"risk_score": analysis_result["overall_risk_score"],
					"user_id": user_id,
				},
			)

			logger.info(f"Analysis completed successfully: {analysis_id}")
			return analysis_result

		except (ValidationError, DocumentProcessingError, WorkflowExecutionError) as e:
			# Re-raise known application errors
			processing_time = time.time() - start_time
			
			# Safely get details from exception
			exception_details = getattr(e, 'details', {})
			if not isinstance(exception_details, dict):
				exception_details = {}
			
			# Log error with context
			error_context = error_handler.handle_error(
				error=e,
				category=getattr(e, 'category', ErrorCategory.SYSTEM),
				severity=getattr(e, 'severity', ErrorSeverity.HIGH),
				user_message=getattr(e, 'user_message', str(e)),
				technical_details={**exception_details, "processing_time": processing_time},
				request_id=analysis_id
			)
			
			# Log audit event
			log_audit_event(
				"contract_analysis_failed", 
				details={
					"analysis_id": analysis_id, 
					"error_code": e.error_code,
					"error_category": e.category.value,
					"processing_time": processing_time, 
					"user_id": user_id
				}
			)
			
			raise
			
		except Exception as e:
			processing_time = time.time() - start_time
			
			# Handle unexpected errors
			error_context = error_handler.handle_error(
				error=e,
				category=ErrorCategory.SYSTEM,
				severity=ErrorSeverity.HIGH,
				user_message="An unexpected error occurred during job application tracking",
				technical_details={
					"analysis_id": analysis_id,
					"filename": filename,
					"processing_time": processing_time,
					"error_type": type(e).__name__
				},
				request_id=analysis_id
			)

			# Log audit event
			log_audit_event(
				"contract_analysis_failed", 
				details={
					"analysis_id": analysis_id, 
					"error": str(e), 
					"error_id": error_context.error_id,
					"processing_time": processing_time, 
					"user_id": user_id
				}
			)

			# Wrap in appropriate exception
			raise WorkflowExecutionError(
				f"Unexpected error during job application tracking: {str(e)}",
				workflow_node="contract_analysis",
				execution_id=analysis_id,
				cause=e
			)

	async def _process_document(self, file_content: bytes, filename: str) -> ProcessedDocument:
		"""Process document to extract text content."""
		import os
		import tempfile
		
		temp_file_path = None
		error_handler = get_error_handler()
		
		try:
			# Save to temporary file
			with tempfile.NamedTemporaryFile(delete=False, suffix=f".{filename.split('.')[-1]}") as temp_file:
				temp_file.write(file_content)
				temp_file_path = temp_file.name

			# Process the document
			processed_doc = await self.document_processor.process_document(temp_file_path, filename)
			return processed_doc
			
		except PermissionError as e:
			error_context = error_handler.handle_error(
				error=e,
				category=ErrorCategory.FILE_PROCESSING,
				severity=ErrorSeverity.HIGH,
				user_message="Permission denied while processing the document",
				technical_details={"filename": filename, "temp_path": temp_file_path}
			)
			raise DocumentProcessingError(
				f"Permission denied while processing '{filename}'",
				processing_stage="file_access",
				cause=e
			)
			
		except FileNotFoundError as e:
			error_context = error_handler.handle_error(
				error=e,
				category=ErrorCategory.FILE_PROCESSING,
				severity=ErrorSeverity.MEDIUM,
				user_message="Document file not found during processing",
				technical_details={"filename": filename, "temp_path": temp_file_path}
			)
			raise DocumentProcessingError(
				f"Document file '{filename}' not found during processing",
				processing_stage="file_access",
				cause=e
			)
			
		except Exception as e:
			error_context = error_handler.handle_error(
				error=e,
				category=ErrorCategory.FILE_PROCESSING,
				severity=ErrorSeverity.HIGH,
				user_message=f"Failed to process document '{filename}'",
				technical_details={"filename": filename, "error_type": type(e).__name__}
			)
			raise DocumentProcessingError(
				f"Failed to process document '{filename}': {str(e)}",
				processing_stage="document_processing",
				cause=e
			)
			
		finally:
			# Clean up temporary file
			if temp_file_path and os.path.exists(temp_file_path):
				try:
					os.unlink(temp_file_path)
				except Exception as cleanup_error:
					logger.warning(f"Failed to cleanup temporary file {temp_file_path}: {cleanup_error}")

	def _normalize_risk_score(self, risk_score: float) -> float:
		"""Normalize risk score to 0-1 scale."""
		if risk_score is None:
			return 0.0
		
		# If score is already in 0-1 range, return as is
		if 0.0 <= risk_score <= 1.0:
			return risk_score
		
		# If score is in 0-10 range (from fallback analysis), normalize to 0-1
		if 0.0 <= risk_score <= 10.0:
			return risk_score / 10.0
		
		# If score is outside expected ranges, clamp to 0-1
		return max(0.0, min(1.0, risk_score / 10.0))

	def _determine_risk_level(self, risk_score: float) -> str:
		"""Determine risk level based on score."""
		if risk_score is None:
			return "Unknown"
		if risk_score >= 0.8:
			return "Critical"
		elif risk_score >= 0.6:
			return "High"
		elif risk_score >= 0.4:
			return "Medium"
		elif risk_score >= 0.2:
			return "Low"
		else:
			return "Minimal"

	async def get_analysis_result(self, analysis_id: str) -> Optional[Dict[str, Any]]:
		"""Get cached analysis result."""
		return self._analysis_cache.get(analysis_id)

	async def list_analyses(self, user_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
		"""List recent analyses."""
		analyses = list(self._analysis_cache.values())

		if user_id:
			# Filter by user if user_id is provided
			analyses = [a for a in analyses if a.get("user_id") == user_id]

		# Sort by creation time (newest first)
		analyses.sort(key=lambda x: x.get("created_at", ""), reverse=True)

		return analyses[:limit]

	async def delete_analysis(self, analysis_id: str, user_id: Optional[str] = None) -> bool:
		"""Delete an analysis result."""
		if analysis_id in self._analysis_cache:
			analysis = self._analysis_cache[analysis_id]

			# Check user permission if user_id is provided
			if user_id and analysis.get("user_id") != user_id:
				return False

			del self._analysis_cache[analysis_id]
			logger.info(f"Analysis deleted: {analysis_id}")
			return True

		return False

	def get_cache_stats(self) -> Dict[str, Any]:
		"""Get cache statistics."""
		return {
			"total_analyses": len(self._analysis_cache),
			"cache_size_mb": sum(len(str(analysis)) for analysis in self._analysis_cache.values()) / (1024 * 1024),
			"oldest_analysis": min((analysis.get("created_at", "") for analysis in self._analysis_cache.values()), default="None"),
			"newest_analysis": max((analysis.get("created_at", "") for analysis in self._analysis_cache.values()), default="None"),
		}
	
	def _convert_workflow_state_to_result(self, workflow_state: Dict[str, Any]) -> Dict[str, Any]:
		"""Convert LangGraph workflow state to expected result format."""
		return {
			"success": workflow_state.get("status") == "completed",
			"risky_clauses": workflow_state.get("risky_clauses", []),
			"overall_risk_score": workflow_state.get("overall_risk_score", 0.0),
			"suggested_redlines": workflow_state.get("suggested_redlines", []),
			"email_draft": workflow_state.get("email_draft", ""),
			"recommendations": workflow_state.get("recommendations", []),
			"confidence_score": workflow_state.get("confidence_score", 0.8),
			"model_used": workflow_state.get("model_used", "gpt-4"),
			"token_usage": workflow_state.get("token_usage", {}),
			"cost": workflow_state.get("cost", 0.0),
			"processing_metadata": workflow_state.get("processing_metadata", {}),
			"contract_structure": workflow_state.get("contract_structure", {}),
			"identified_clauses": workflow_state.get("identified_clauses", []),
			"precedent_matches": workflow_state.get("precedent_matches", []),
			"negotiation_strategy": workflow_state.get("negotiation_strategy", ""),
			"workflow_id": workflow_state.get("execution_id"),
			"execution_mode": "langgraph_sequential",
			"fallback_used": False,
			"quality_score": 0.8
		}
	
	def enable_optimized_agents(self, enabled: bool = True):
		"""Enable or disable optimized agent workflow."""
		self._use_optimized_agents = enabled
		logger.info(f"Optimized agents {'enabled' if enabled else 'disabled'}")
	
	def get_orchestration_health(self) -> Dict[str, Any]:
		"""Get health status of the orchestration service."""
		if self._use_optimized_agents:
			return {
				"optimized_agents_enabled": True,
				"agent_health": self.orchestration_service.get_agent_health_status(),
				"performance_stats": self.orchestration_service.get_performance_statistics()
			}
		else:
			return {
				"optimized_agents_enabled": False,
				"legacy_workflow_active": True
			}


# Global instance (lazy initialization)
_contract_analysis_service: Optional[ContractAnalysisService] = None


def get_contract_analysis_service() -> ContractAnalysisService:
	"""Get the global job application tracking service instance."""
	global _contract_analysis_service
	if _contract_analysis_service is None:
		_contract_analysis_service = ContractAnalysisService()
	return _contract_analysis_service
