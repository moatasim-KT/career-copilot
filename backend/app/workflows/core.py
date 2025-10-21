"""
Core LangGraph Workflow Implementation

This module implements the base workflow structure for job application tracking
using LangGraph's StateGraph functionality.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Literal

import structlog
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .analyzer import analyzer_node
from .communicator import create_communicator_node
from .negotiator import create_negotiator_node
from .state import ContractAnalysisState, WorkflowStatus, add_warning, create_initial_state, update_state_status, validate_state

logger = logging.getLogger(__name__)
structured_logger = structlog.get_logger(__name__)


class ContractAnalysisWorkflow:
	"""
	Main workflow class that orchestrates the job application tracking process.

	This class sets up the LangGraph workflow with proper entry and exit points,
	state management, and error handling.
	"""

	def __init__(self, config: Dict[str, Any] | None = None):
		"""
		Initialize the workflow with configuration.

		Args:
		    config: Optional configuration dictionary
		"""
		self.config = config or {}
		self.graph = None
		self.checkpointer = MemorySaver()

		# Initialize LLM for nodes that need it
		from langchain_openai import ChatOpenAI

		from ..core.config import get_settings

		settings = get_settings()
		self.llm = ChatOpenAI(
			model=settings.openai_model, temperature=settings.openai_temperature, api_key=settings.openai_api_key.get_secret_value()
		)

		self._build_graph()

	def _build_graph(self) -> None:
		"""Build the LangGraph workflow structure with enhanced conditional routing."""
		# Create the state graph
		workflow = StateGraph(ContractAnalysisState)

		# Add nodes
		workflow.add_node("validate_input", self._validate_input_node)
		workflow.add_node("analyzer", analyzer_node)
		workflow.add_node("negotiator", create_negotiator_node())
		workflow.add_node("communicator", create_communicator_node())
		workflow.add_node("error_recovery", self._error_recovery_node)
		workflow.add_node("finalize", self._finalize_node)

		# Set entry point
		workflow.set_entry_point("validate_input")

		# Add conditional edges with enhanced routing logic
		workflow.add_conditional_edges("validate_input", self._route_from_validation, {"continue": "analyzer", "error": "error_recovery", "end": END})

		workflow.add_conditional_edges(
			"analyzer",
			self._route_from_analyzer,
			{"negotiate": "negotiator", "skip_negotiation": "communicator", "error": "error_recovery", "retry": "analyzer"},
		)

		workflow.add_conditional_edges(
			"negotiator", self._route_from_negotiator, {"communicate": "communicator", "error": "error_recovery", "retry": "negotiator"}
		)

		workflow.add_conditional_edges(
			"communicator", self._route_from_communicator, {"finalize": "finalize", "error": "error_recovery", "retry": "communicator"}
		)

		workflow.add_conditional_edges(
			"error_recovery",
			self._route_from_error_recovery,
			{"retry_analyzer": "analyzer", "retry_negotiator": "negotiator", "retry_communicator": "communicator", "end": END},
		)

		workflow.add_edge("finalize", END)

		# Compile the graph
		self.graph = workflow.compile(checkpointer=self.checkpointer)

	def _validate_input_node(self, state: ContractAnalysisState) -> ContractAnalysisState:
		"""
		Validate input data and prepare for analysis.

		Args:
		    state: Current workflow state

		Returns:
		    ContractAnalysisState: Updated state after validation
		"""
		# Update status
		state = update_state_status(state, WorkflowStatus.INITIALIZED, "validate_input")

		# Validate the state
		validation_errors = validate_state(state)

		if validation_errors:
			error_msg = f"Input validation failed: {'; '.join(validation_errors)}"
			return update_state_status(state, WorkflowStatus.FAILED, "validate_input", error_msg)

		# Add validation success warning
		state = add_warning(state, "Input validation completed successfully")

		# Prepare for analysis
		state = update_state_status(state, WorkflowStatus.ANALYZING, "validate_input")

		return state

	def _finalize_node(self, state: ContractAnalysisState) -> ContractAnalysisState:
		"""
		Finalize the workflow and prepare results.

		Args:
		    state: Current workflow state

		Returns:
		    ContractAnalysisState: Final state
		"""
		# Compile final results
		final_results = self._compile_workflow_results(state)

		# Update state with compiled results
		state.update(final_results)

		# Update status to completed
		state = update_state_status(state, WorkflowStatus.COMPLETED, "finalize")

		# Add completion warning with summary
		risky_clauses_count = len(state.get("risky_clauses", []))
		redlines_count = len(state.get("suggested_redlines", []))

		completion_msg = f"Workflow completed successfully: {risky_clauses_count} risky clauses identified, {redlines_count} redlines generated"
		state = add_warning(state, completion_msg)

		return state

	def _error_recovery_node(self, state: ContractAnalysisState) -> ContractAnalysisState:
		"""
		Handle error recovery and determine retry strategy.

		Args:
		    state: Current workflow state with error

		Returns:
		    ContractAnalysisState: Updated state with recovery information
		"""
		current_node = state.get("current_node", "unknown")
		last_error = state.get("last_error", "Unknown error")
		error_count = state.get("processing_metadata", {}).get("error_count", 0)

		# Log the error recovery attempt
		recovery_msg = f"Attempting error recovery for node '{current_node}' (attempt {error_count + 1})"
		state = add_warning(state, recovery_msg)

		# Implement recovery strategies based on error type
		if self._is_retryable_error(state):
			# Clear the failed status to allow retry
			state["status"] = WorkflowStatus.INITIALIZED
			state = add_warning(state, f"Error is retryable, preparing to retry {current_node}")
		else:
			# Mark as permanently failed
			state = update_state_status(state, WorkflowStatus.FAILED, "error_recovery", f"Non-retryable error in {current_node}: {last_error}")

		return state

	def _compile_workflow_results(self, state: ContractAnalysisState) -> Dict[str, Any]:
		"""
		Compile and validate final workflow results.

		Args:
		    state: Current workflow state

		Returns:
		    Dict[str, Any]: Compiled results
		"""
		results = {}

		# Ensure all required fields are present with defaults
		results["risky_clauses"] = state.get("risky_clauses", [])
		results["suggested_redlines"] = state.get("suggested_redlines", [])
		results["email_draft"] = state.get("email_draft", "")
		results["overall_risk_score"] = state.get("overall_risk_score", 0.0)
		results["precedent_context"] = state.get("precedent_context", [])

		# Add workflow completion metadata
		processing_metadata = state.get("processing_metadata", {})
		processing_metadata["completion_timestamp"] = datetime.utcnow()
		processing_metadata["total_nodes_executed"] = len(
			set(warning.split(":")[0] for warning in processing_metadata.get("warnings", []) if "node completed" in warning.lower())
		)

		results["processing_metadata"] = processing_metadata

		return results

	def _is_retryable_error(self, state: ContractAnalysisState) -> bool:
		"""
		Determine if an error is retryable based on error type and conditions.

		Args:
		    state: Current workflow state

		Returns:
		    bool: True if error is retryable, False otherwise
		"""
		last_error = state.get("last_error", "")
		if last_error is None:
			last_error = ""
		last_error = last_error.lower()

		# Define retryable error patterns
		retryable_patterns = ["timeout", "rate limit", "connection", "temporary", "service unavailable", "openai", "api", "network"]

		# Define non-retryable error patterns
		non_retryable_patterns = ["validation", "invalid input", "authentication", "permission denied", "not found", "malformed"]

		# Check for non-retryable patterns first
		for pattern in non_retryable_patterns:
			if pattern in last_error:
				return False

		# Check for retryable patterns
		for pattern in retryable_patterns:
			if pattern in last_error:
				return True

		# Default to retryable for unknown errors (with retry limit)
		error_count = state.get("processing_metadata", {}).get("error_count", 0)
		return error_count < self.config.get("max_retries", 3)

	def _validate_analysis_results(self, state: ContractAnalysisState) -> bool:
		"""
		Validate analysis results for completeness and correctness.

		Args:
		    state: Current workflow state

		Returns:
		    bool: True if results are valid, False otherwise
		"""
		risky_clauses = state.get("risky_clauses", [])

		# Check if risky_clauses is a list
		if not isinstance(risky_clauses, list):
			return False

		# Validate each risky clause structure
		for clause in risky_clauses:
			if not isinstance(clause, dict):
				return False

			required_fields = ["clause_text", "risk_explanation", "risk_level", "clause_index"]
			if not all(field in clause for field in required_fields):
				return False

			# Validate risk level
			if clause.get("risk_level") not in ["Low", "Medium", "High"]:
				return False

		# Validate overall risk score if present
		risk_score = state.get("overall_risk_score")
		if risk_score is not None and (not isinstance(risk_score, (int, float)) or risk_score < 0 or risk_score > 10):
			return False

		return True

	def _validate_negotiation_results(self, state: ContractAnalysisState) -> bool:
		"""
		Validate negotiation results for completeness and correctness.

		Args:
		    state: Current workflow state

		Returns:
		    bool: True if results are valid, False otherwise
		"""
		suggested_redlines = state.get("suggested_redlines", [])

		# Check if suggested_redlines is a list
		if not isinstance(suggested_redlines, list):
			return False

		# Validate each redline suggestion structure
		for redline in suggested_redlines:
			if not isinstance(redline, dict):
				return False

			required_fields = ["original_clause", "suggested_redline", "risk_explanation", "clause_index"]
			if not all(field in redline for field in required_fields):
				return False

		return True

	def _validate_communication_results(self, state: ContractAnalysisState) -> bool:
		"""
		Validate communication results for completeness and correctness.

		Args:
		    state: Current workflow state

		Returns:
		    bool: True if results are valid, False otherwise
		"""
		email_draft = state.get("email_draft", "")

		# Check if email draft exists and has minimum content
		if not isinstance(email_draft, str) or len(email_draft.strip()) < 50:
			return False

		# Basic email structure validation
		if "Subject:" not in email_draft:
			return False

		return True

	def _route_from_validation(self, state: ContractAnalysisState) -> Literal["continue", "error", "end"]:
		"""
		Route from validation node based on state and error conditions.

		Args:
		    state: Current workflow state

		Returns:
		    str: Next node to execute
		"""
		if state.get("status") == WorkflowStatus.FAILED:
			# Check if this is a recoverable error
			error_count = state.get("processing_metadata", {}).get("error_count", 0)
			if error_count >= self.config.get("max_retries", 3):
				return "end"
			return "error"
		return "continue"

	def _route_from_analyzer(self, state: ContractAnalysisState) -> Literal["negotiate", "skip_negotiation", "error", "retry"]:
		"""
		Route from analyzer node based on analysis results and error conditions.

		Args:
		    state: Current workflow state

		Returns:
		    str: Next node to execute
		"""
		if state.get("status") == WorkflowStatus.FAILED:
			# Check retry conditions
			error_count = state.get("processing_metadata", {}).get("error_count", 0)
			max_retries = self.config.get("max_retries", 3)

			if error_count < max_retries and self._is_retryable_error(state):
				return "retry"
			return "error"

		risky_clauses = state.get("risky_clauses", [])

		# Check if analysis produced valid results
		if not self._validate_analysis_results(state):
			return "error"

		if risky_clauses:
			return "negotiate"
		else:
			return "skip_negotiation"

	def _route_from_negotiator(self, state: ContractAnalysisState) -> Literal["communicate", "error", "retry"]:
		"""
		Route from negotiator node based on negotiation results and error conditions.

		Args:
		    state: Current workflow state

		Returns:
		    str: Next node to execute
		"""
		if state.get("status") == WorkflowStatus.FAILED:
			error_count = state.get("processing_metadata", {}).get("error_count", 0)
			max_retries = self.config.get("max_retries", 3)

			if error_count < max_retries and self._is_retryable_error(state):
				return "retry"
			return "error"

		# Validate negotiation results
		if not self._validate_negotiation_results(state):
			return "error"

		return "communicate"

	def _route_from_communicator(self, state: ContractAnalysisState) -> Literal["finalize", "error", "retry"]:
		"""
		Route from communicator node based on communication results and error conditions.

		Args:
		    state: Current workflow state

		Returns:
		    str: Next node to execute
		"""
		if state.get("status") == WorkflowStatus.FAILED:
			error_count = state.get("processing_metadata", {}).get("error_count", 0)
			max_retries = self.config.get("max_retries", 3)

			if error_count < max_retries and self._is_retryable_error(state):
				return "retry"
			return "error"

		# Validate communication results
		if not self._validate_communication_results(state):
			return "error"

		return "finalize"

	def _route_from_error_recovery(self, state: ContractAnalysisState) -> Literal["retry_analyzer", "retry_negotiator", "retry_communicator", "end"]:
		"""
		Route from error recovery node based on recovery strategy.

		Args:
		    state: Current workflow state

		Returns:
		    str: Next node to execute or end workflow
		"""
		current_node = state.get("current_node", "")
		error_count = state.get("processing_metadata", {}).get("error_count", 0)
		max_retries = self.config.get("max_retries", 3)

		# If we've exceeded max retries, end the workflow
		if error_count >= max_retries:
			return "end"

		# Determine which node to retry based on where the error occurred
		if current_node == "analyzer" and self._is_retryable_error(state):
			return "retry_analyzer"
		elif current_node == "negotiator" and self._is_retryable_error(state):
			return "retry_negotiator"
		elif current_node == "communicator" and self._is_retryable_error(state):
			return "retry_communicator"
		else:
			return "end"

	async def execute(self, contract_text: str, contract_filename: str, config: Dict[str, Any] | None = None) -> ContractAnalysisState:
		"""
		Execute the complete workflow for job application tracking with enhanced monitoring.

		Args:
		    contract_text: The contract text to analyze
		    contract_filename: Name of the contract file
		    config: Optional configuration parameters

		Returns:
		    ContractAnalysisState: Final workflow state with results
		"""
		# Generate unique execution ID for tracking
		execution_id = str(uuid.uuid4())
		thread_id = f"contract_analysis_{execution_id}"

		# Create initial state with execution tracking
		merged_config = {**self.config, **(config or {}), "execution_id": execution_id}
		initial_state = create_initial_state(contract_text=contract_text, contract_filename=contract_filename, config=merged_config)

		# Use structured logging
		structured_logger.info(
			"Starting workflow execution", execution_id=execution_id, contract_filename=contract_filename, contract_length=len(contract_text)
		)

		try:
			# Import monitoring components
			from ..core.monitoring import metrics_collector

			# Execute the workflow with monitoring
			start_time = datetime.utcnow()

			# Use monitoring context
			async with metrics_collector.trace_workflow(
				"contract_analysis", execution_id, contract_filename=contract_filename, contract_length=len(contract_text)
			):
				result = await self.graph.ainvoke(
					initial_state, config={"configurable": {"thread_id": thread_id}, "recursion_limit": self.config.get("recursion_limit", 50)}
				)

			end_time = datetime.utcnow()
			execution_duration = (end_time - start_time).total_seconds()

			# Log execution completion with structured logging
			status = result.get("status", "unknown")
			structured_logger.info(
				"Workflow execution completed",
				execution_id=execution_id,
				status=status,
				duration=execution_duration,
				risky_clauses_count=len(result.get("risky_clauses", [])),
				redlines_count=len(result.get("suggested_redlines", [])),
			)

			# Record execution metrics
			self._record_execution_metrics(execution_id, result, execution_duration, success=(status == WorkflowStatus.COMPLETED))

			return result

		except Exception as e:
			# Handle workflow execution errors with detailed logging
			error_msg = f"Workflow execution failed: {e!s}"
			structured_logger.error("Workflow execution failed", execution_id=execution_id, error=error_msg, exc_info=True)

			# Create error state with proper error handling
			error_state = update_state_status(initial_state, WorkflowStatus.FAILED, "workflow_execution", error_msg)
			error_state["last_error"] = error_msg

			# Update processing metadata
			processing_metadata = error_state.get("processing_metadata", {})
			processing_metadata["error_count"] = processing_metadata.get("error_count", 0) + 1
			processing_metadata["end_time"] = datetime.utcnow()
			error_state["processing_metadata"] = processing_metadata

			# Record failed execution metrics
			self._record_execution_metrics(execution_id, error_state, 0, success=False)

			return error_state

	def execute_sync(self, contract_text: str, contract_filename: str, config: Dict[str, Any] | None = None) -> ContractAnalysisState:
		"""
		Execute the workflow synchronously with enhanced monitoring.

		Args:
		    contract_text: The contract text to analyze
		    contract_filename: Name of the contract file
		    config: Optional configuration parameters

		Returns:
		    ContractAnalysisState: Final workflow state with results
		"""
		# Generate unique execution ID for tracking
		execution_id = str(uuid.uuid4())
		thread_id = f"contract_analysis_sync_{execution_id}"

		# Create initial state with execution tracking
		merged_config = {**self.config, **(config or {}), "execution_id": execution_id}
		initial_state = create_initial_state(contract_text=contract_text, contract_filename=contract_filename, config=merged_config)

		logger.info(f"Starting synchronous workflow execution {execution_id} for contract: {contract_filename}")

		try:
			# Execute the workflow synchronously with monitoring
			start_time = datetime.utcnow()

			result = self.graph.invoke(
				initial_state, config={"configurable": {"thread_id": thread_id}, "recursion_limit": self.config.get("recursion_limit", 50)}
			)

			end_time = datetime.utcnow()
			execution_duration = (end_time - start_time).total_seconds()

			# Log execution completion
			status = result.get("status", "unknown")
			logger.info(f"Synchronous workflow execution {execution_id} completed with status: {status} in {execution_duration:.2f}s")

			# Record execution metrics
			self._record_execution_metrics(execution_id, result, execution_duration, success=(status == WorkflowStatus.COMPLETED))

			return result

		except Exception as e:
			# Handle workflow execution errors with detailed logging
			error_msg = f"Workflow execution failed: {e!s}"
			logger.error(f"Synchronous workflow execution {execution_id} failed: {error_msg}", exc_info=True)

			error_state = update_state_status(initial_state, WorkflowStatus.FAILED, "workflow_execution", error_msg)

			# Record failed execution metrics
			self._record_execution_metrics(execution_id, error_state, 0, success=False)

			return error_state

	def get_workflow_status(self, thread_id: str = "contract_analysis") -> Dict[str, Any]:
		"""
		Get the current status of a workflow execution with enhanced details.

		Args:
		    thread_id: Thread ID for the workflow execution

		Returns:
		    Dict[str, Any]: Current workflow status information
		"""
		try:
			# Get the latest checkpoint
			config = {"configurable": {"thread_id": thread_id}}
			checkpoint = self.checkpointer.get(config)

			if checkpoint and checkpoint.channel_values:
				state = checkpoint.channel_values
				processing_metadata = state.get("processing_metadata", {})

				return {
					"status": state.get("status", "unknown"),
					"current_node": state.get("current_node", "unknown"),
					"execution_id": state.get("config", {}).get("execution_id", "unknown"),
					"error_count": processing_metadata.get("error_count", 0),
					"warnings": processing_metadata.get("warnings", []),
					"last_error": state.get("last_error"),
					"start_time": processing_metadata.get("start_time"),
					"end_time": processing_metadata.get("end_time"),
					"processing_duration": processing_metadata.get("processing_duration"),
					"risky_clauses_count": len(state.get("risky_clauses", [])),
					"redlines_count": len(state.get("suggested_redlines", [])),
					"overall_risk_score": state.get("overall_risk_score"),
					"contract_filename": state.get("contract_filename", "unknown"),
				}
			else:
				return {
					"status": "not_found",
					"current_node": "none",
					"execution_id": "unknown",
					"error_count": 0,
					"warnings": [],
					"last_error": None,
					"risky_clauses_count": 0,
					"redlines_count": 0,
				}

		except Exception as e:
			return {
				"status": "error",
				"current_node": "unknown",
				"execution_id": "unknown",
				"error_count": 1,
				"warnings": [],
				"last_error": f"Failed to get workflow status: {e!s}",
				"risky_clauses_count": 0,
				"redlines_count": 0,
			}

	def _record_execution_metrics(self, execution_id: str, final_state: ContractAnalysisState, duration: float, success: bool) -> None:
		"""
		Record execution metrics for monitoring and analysis.

		Args:
		    execution_id: Unique execution identifier
		    final_state: Final workflow state
		    duration: Execution duration in seconds
		    success: Whether execution was successful
		"""
		try:
			from .utils import default_metrics

			# Record metrics using the utils module
			default_metrics.record_execution(execution_id, final_state, success)

			# Log key metrics
			processing_metadata = final_state.get("processing_metadata", {})
			risky_clauses_count = len(final_state.get("risky_clauses", []))
			redlines_count = len(final_state.get("suggested_redlines", []))
			error_count = processing_metadata.get("error_count", 0)

			logger.info(
				f"Execution metrics - ID: {execution_id}, Success: {success}, "
				f"Duration: {duration:.2f}s, Risky Clauses: {risky_clauses_count}, "
				f"Redlines: {redlines_count}, Errors: {error_count}"
			)

		except Exception as e:
			logger.warning(f"Failed to record execution metrics for {execution_id}: {e!s}")

	def get_execution_metrics(self, time_window_hours: int = 24) -> Dict[str, Any]:
		"""
		Get execution metrics for monitoring dashboard.

		Args:
		    time_window_hours: Time window for metrics calculation

		Returns:
		    Dict[str, Any]: Execution metrics summary
		"""
		try:
			from .utils import default_metrics

			return {
				"success_rate": default_metrics.get_success_rate(time_window_hours),
				"average_duration": default_metrics.get_average_duration(time_window_hours),
				"error_summary": default_metrics.get_error_summary(time_window_hours),
				"time_window_hours": time_window_hours,
			}

		except Exception as e:
			logger.error(f"Failed to get execution metrics: {e!s}")
			return {
				"success_rate": 0.0,
				"average_duration": None,
				"error_summary": {"total_executions": 0, "failed_executions": 0},
				"time_window_hours": time_window_hours,
				"error": str(e),
			}


# Factory function for creating workflow instances
def create_workflow(config: Dict[str, Any] | None = None) -> ContractAnalysisWorkflow:
	"""
	Factory function to create a new workflow instance.

	Args:
	    config: Optional configuration dictionary

	Returns:
	    ContractAnalysisWorkflow: New workflow instance
	"""
	return ContractAnalysisWorkflow(config)
