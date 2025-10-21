"""
Contract Analysis Workflow State Management

This module defines the state structure for the LangGraph workflow
that manages job application tracking, negotiation, and communication.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict


class WorkflowStatus(str, Enum):
	"""Workflow execution status enumeration"""

	INITIALIZED = "initialized"
	ANALYZING = "analyzing"
	NEGOTIATING = "negotiating"
	COMMUNICATING = "communicating"
	COMPLETED = "completed"
	FAILED = "failed"


class RiskLevel(str, Enum):
	"""Risk level enumeration for clauses"""

	LOW = "Low"
	MEDIUM = "Medium"
	HIGH = "High"


class RiskyClause(TypedDict):
	"""Structure for risky clause information"""

	clause_text: str
	risk_explanation: str
	risk_level: RiskLevel
	precedent_reference: Optional[str]
	clause_index: int


class RedlineSuggestion(TypedDict):
	"""Structure for redline suggestions"""

	original_clause: str
	suggested_redline: str
	risk_explanation: str
	clause_index: int
	change_rationale: str
	risk_mitigated: Optional[bool]


class ProcessingMetadata(TypedDict):
	"""Metadata for workflow processing"""

	start_time: datetime
	end_time: Optional[datetime]
	processing_duration: Optional[float]
	model_version: str
	workflow_version: str
	error_count: int
	warnings: List[str]


class ContractAnalysisState(TypedDict):
	"""
	Main state structure for the job application tracking workflow.

	This TypedDict defines all the state variables that are passed
	between nodes in the LangGraph workflow.
	"""

	# Input data
	contract_text: str
	contract_filename: str

	# Analysis results
	risky_clauses: List[RiskyClause]
	overall_risk_score: Optional[float]

	# Negotiation results
	suggested_redlines: List[RedlineSuggestion]

	# Communication results
	email_draft: str

	# Supporting data
	precedent_context: List[str]

	# Workflow management
	status: WorkflowStatus
	current_node: str
	processing_metadata: ProcessingMetadata

	# Error handling
	errors: List[str]
	last_error: Optional[str]

	# Configuration
	config: Dict[str, Any]


def create_initial_state(contract_text: str, contract_filename: str, config: Optional[Dict[str, Any]] = None) -> ContractAnalysisState:
	"""
	Create an initial workflow state with default values.

	Args:
	    contract_text: The contract text to analyze
	    contract_filename: Name of the contract file
	    config: Optional configuration parameters

	Returns:
	    ContractAnalysisState: Initial state for workflow execution
	"""
	return ContractAnalysisState(
		# Input data
		contract_text=contract_text,
		contract_filename=contract_filename,
		# Analysis results (empty initially)
		risky_clauses=[],
		overall_risk_score=None,
		# Negotiation results (empty initially)
		suggested_redlines=[],
		# Communication results (empty initially)
		email_draft="",
		# Supporting data (empty initially)
		precedent_context=[],
		# Workflow management
		status=WorkflowStatus.INITIALIZED,
		current_node="start",
		processing_metadata=ProcessingMetadata(
			start_time=datetime.utcnow(),
			end_time=None,
			processing_duration=None,
			model_version="1.0.0",
			workflow_version="1.0.0",
			error_count=0,
			warnings=[],
		),
		# Error handling
		errors=[],
		last_error=None,
		# Configuration
		config=config or {},
	)


def validate_state(state: ContractAnalysisState) -> List[str]:
	"""
	Validate the workflow state for consistency and completeness.

	Args:
	    state: The workflow state to validate

	Returns:
	    List[str]: List of validation errors (empty if valid)
	"""
	errors = []

	# Validate required fields
	if not state.get("contract_text"):
		errors.append("contract_text is required and cannot be empty")

	if not state.get("contract_filename"):
		errors.append("contract_filename is required and cannot be empty")

	# Validate status
	if state.get("status") not in [status.value for status in WorkflowStatus]:
		errors.append(f"Invalid status: {state.get('status')}")

	# Validate risky clauses structure
	risky_clauses = state.get("risky_clauses", [])
	for i, clause in enumerate(risky_clauses):
		if not isinstance(clause, dict):
			errors.append(f"risky_clauses[{i}] must be a dictionary")
			continue

		required_fields = ["clause_text", "risk_explanation", "risk_level", "clause_index"]
		for field in required_fields:
			if field not in clause:
				errors.append(f"risky_clauses[{i}] missing required field: {field}")

		# Validate risk level
		if clause.get("risk_level") not in [level.value for level in RiskLevel]:
			errors.append(f"risky_clauses[{i}] has invalid risk_level: {clause.get('risk_level')}")

	# Validate redline suggestions structure
	redlines = state.get("suggested_redlines", [])
	for i, redline in enumerate(redlines):
		if not isinstance(redline, dict):
			errors.append(f"suggested_redlines[{i}] must be a dictionary")
			continue

		required_fields = ["original_clause", "suggested_redline", "risk_explanation", "clause_index"]
		for field in required_fields:
			if field not in redline:
				errors.append(f"suggested_redlines[{i}] missing required field: {field}")

	# Validate processing metadata
	metadata = state.get("processing_metadata", {})
	if not isinstance(metadata, dict):
		errors.append("processing_metadata must be a dictionary")
	elif "start_time" not in metadata:
		errors.append("processing_metadata missing required field: start_time")

	return errors


def update_state_status(
	state: ContractAnalysisState, new_status: WorkflowStatus, current_node: str, error: Optional[str] = None
) -> ContractAnalysisState:
	"""
	Update the workflow state with new status and node information.

	Args:
	    state: Current workflow state
	    new_status: New status to set
	    current_node: Current node being executed
	    error: Optional error message

	Returns:
	    ContractAnalysisState: Updated state
	"""
	# Create a copy of the state to avoid mutation
	updated_state = state.copy()

	# Update status and node
	updated_state["status"] = new_status
	updated_state["current_node"] = current_node

	# Handle error if provided
	if error:
		updated_state["last_error"] = error
		updated_state["errors"].append(error)
		updated_state["processing_metadata"]["error_count"] += 1

	# Update end time if workflow is completed or failed
	if new_status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
		end_time = datetime.utcnow()
		updated_state["processing_metadata"]["end_time"] = end_time

		start_time = updated_state["processing_metadata"]["start_time"]
		duration = (end_time - start_time).total_seconds()
		updated_state["processing_metadata"]["processing_duration"] = duration

	return updated_state


def add_warning(state: ContractAnalysisState, warning: str) -> ContractAnalysisState:
	"""
	Add a warning to the workflow state.

	Args:
	    state: Current workflow state
	    warning: Warning message to add

	Returns:
	    ContractAnalysisState: Updated state with warning
	"""
	updated_state = state.copy()
	updated_state["processing_metadata"]["warnings"].append(warning)
	return updated_state
