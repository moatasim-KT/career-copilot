"""
Workflow Execution Utilities

This module provides utility functions for workflow execution,
state persistence, and error handling.
"""

import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .state import ContractAnalysisState, ProcessingMetadata, WorkflowStatus


class WorkflowExecutionError(Exception):
	"""Custom exception for workflow execution errors."""

	def __init__(self, message: str, state: Optional[ContractAnalysisState] = None):
		super().__init__(message)
		self.state = state


class WorkflowStateManager:
	"""
	Manages workflow state persistence and retrieval.

	This class provides utilities for saving and loading workflow states,
	which can be useful for debugging, monitoring, and recovery.
	"""

	def __init__(self, storage_path: str = "/tmp/workflow_states"):
		"""
		Initialize the state manager.

		Args:
		    storage_path: Path where workflow states will be stored
		"""
		self.storage_path = Path(storage_path)
		self.storage_path.mkdir(parents=True, exist_ok=True)

	def save_state(self, state: ContractAnalysisState, execution_id: str, format: str = "json") -> str:
		"""
		Save workflow state to storage.

		Args:
		    state: Workflow state to save
		    execution_id: Unique identifier for this execution
		    format: Storage format ("json" or "pickle")

		Returns:
		    str: Path to saved state file
		"""
		timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
		filename = f"{execution_id}_{timestamp}.{format}"
		filepath = self.storage_path / filename

		try:
			if format == "json":
				# Convert datetime objects to strings for JSON serialization
				serializable_state = self._make_json_serializable(state)
				with open(filepath, "w") as f:
					json.dump(serializable_state, f, indent=2)
			elif format == "pickle":
				with open(filepath, "wb") as f:
					pickle.dump(state, f)
			else:
				raise ValueError(f"Unsupported format: {format}")

			return str(filepath)

		except Exception as e:
			raise WorkflowExecutionError(f"Failed to save state: {e!s}", state)

	def load_state(self, filepath: str) -> ContractAnalysisState:
		"""
		Load workflow state from storage.

		Args:
		    filepath: Path to saved state file

		Returns:
		    ContractAnalysisState: Loaded workflow state
		"""
		filepath = Path(filepath)

		try:
			if filepath.suffix == ".json":
				with open(filepath, "r") as f:
					data = json.load(f)
				return self._restore_from_json(data)
			elif filepath.suffix == ".pickle":
				with open(filepath, "rb") as f:
					return pickle.load(f)
			else:
				raise ValueError(f"Unsupported file format: {filepath.suffix}")

		except Exception as e:
			raise WorkflowExecutionError(f"Failed to load state: {e!s}")

	def list_saved_states(self, execution_id: Optional[str] = None) -> List[Dict[str, Any]]:
		"""
		List all saved workflow states.

		Args:
		    execution_id: Optional filter by execution ID

		Returns:
		    List[Dict[str, Any]]: List of saved state information
		"""
		states = []

		for filepath in self.storage_path.glob("*.json"):
			try:
				parts = filepath.stem.split("_")
				if len(parts) >= 3:
					file_execution_id = "_".join(parts[:-2])
					timestamp_str = "_".join(parts[-2:])

					if execution_id and file_execution_id != execution_id:
						continue

					# Parse timestamp
					timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

					states.append(
						{
							"filepath": str(filepath),
							"execution_id": file_execution_id,
							"timestamp": timestamp,
							"format": "json",
							"size": filepath.stat().st_size,
						}
					)
			except Exception:
				# Skip files that don't match expected format
				continue

		# Sort by timestamp (newest first)
		states.sort(key=lambda x: x["timestamp"], reverse=True)
		return states

	def cleanup_old_states(self, max_age_days: int = 7) -> int:
		"""
		Clean up old workflow states.

		Args:
		    max_age_days: Maximum age in days for keeping states

		Returns:
		    int: Number of files cleaned up
		"""
		cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
		cleaned_count = 0

		for filepath in self.storage_path.glob("*"):
			try:
				if filepath.stat().st_mtime < cutoff_date.timestamp():
					filepath.unlink()
					cleaned_count += 1
			except Exception:
				# Skip files that can't be processed
				continue

		return cleaned_count

	def _make_json_serializable(self, state: ContractAnalysisState) -> Dict[str, Any]:
		"""Convert state to JSON-serializable format."""
		serializable = dict(state)

		# Convert datetime objects in processing_metadata
		metadata = serializable.get("processing_metadata", {})
		if "start_time" in metadata and isinstance(metadata["start_time"], datetime):
			metadata["start_time"] = metadata["start_time"].isoformat()
		if "end_time" in metadata and isinstance(metadata["end_time"], datetime):
			metadata["end_time"] = metadata["end_time"].isoformat()

		return serializable

	def _restore_from_json(self, data: Dict[str, Any]) -> ContractAnalysisState:
		"""Restore state from JSON format."""
		# Convert datetime strings back to datetime objects
		metadata = data.get("processing_metadata", {})
		if "start_time" in metadata and isinstance(metadata["start_time"], str):
			metadata["start_time"] = datetime.fromisoformat(metadata["start_time"])
		if "end_time" in metadata and isinstance(metadata["end_time"], str):
			metadata["end_time"] = datetime.fromisoformat(metadata["end_time"])

		return ContractAnalysisState(data)


class WorkflowMetrics:
	"""
	Collects and manages workflow execution metrics.
	"""

	def __init__(self):
		"""Initialize metrics collector."""
		self.executions: List[Dict[str, Any]] = []

	def record_execution(self, execution_id: str, state: ContractAnalysisState, success: bool) -> None:
		"""
		Record a workflow execution for metrics.

		Args:
		    execution_id: Unique identifier for the execution
		    state: Final workflow state
		    success: Whether execution was successful
		"""
		metadata = state.get("processing_metadata", {})

		execution_record = {
			"execution_id": execution_id,
			"timestamp": datetime.utcnow(),
			"success": success,
			"status": state.get("status"),
			"duration": metadata.get("processing_duration"),
			"error_count": metadata.get("error_count", 0),
			"warning_count": len(metadata.get("warnings", [])),
			"risky_clauses_found": len(state.get("risky_clauses", [])),
			"redlines_generated": len(state.get("suggested_redlines", [])),
			"contract_length": len(state.get("contract_text", "")),
			"final_node": state.get("current_node"),
		}

		self.executions.append(execution_record)

	def get_success_rate(self, time_window_hours: Optional[int] = None) -> float:
		"""
		Calculate workflow success rate.

		Args:
		    time_window_hours: Optional time window for calculation

		Returns:
		    float: Success rate as percentage (0-100)
		"""
		executions = self._filter_by_time_window(time_window_hours)

		if not executions:
			return 0.0

		successful = sum(1 for ex in executions if ex["success"])
		return (successful / len(executions)) * 100

	def get_average_duration(self, time_window_hours: Optional[int] = None) -> Optional[float]:
		"""
		Calculate average execution duration.

		Args:
		    time_window_hours: Optional time window for calculation

		Returns:
		    Optional[float]: Average duration in seconds, None if no data
		"""
		executions = self._filter_by_time_window(time_window_hours)
		durations = [ex["duration"] for ex in executions if ex["duration"] is not None]

		if not durations:
			return None

		return sum(durations) / len(durations)

	def get_error_summary(self, time_window_hours: Optional[int] = None) -> Dict[str, Any]:
		"""
		Get summary of errors and warnings.

		Args:
		    time_window_hours: Optional time window for calculation

		Returns:
		    Dict[str, Any]: Error summary statistics
		"""
		executions = self._filter_by_time_window(time_window_hours)

		total_errors = sum(ex["error_count"] for ex in executions)
		total_warnings = sum(ex["warning_count"] for ex in executions)
		failed_executions = sum(1 for ex in executions if not ex["success"])

		return {
			"total_executions": len(executions),
			"failed_executions": failed_executions,
			"total_errors": total_errors,
			"total_warnings": total_warnings,
			"average_errors_per_execution": total_errors / len(executions) if executions else 0,
			"average_warnings_per_execution": total_warnings / len(executions) if executions else 0,
		}

	def _filter_by_time_window(self, time_window_hours: Optional[int]) -> List[Dict[str, Any]]:
		"""Filter executions by time window."""
		if time_window_hours is None:
			return self.executions

		cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
		return [ex for ex in self.executions if ex["timestamp"] >= cutoff_time]


# Global instances for convenience
default_state_manager = WorkflowStateManager()
default_metrics = WorkflowMetrics()


def save_workflow_state(state: ContractAnalysisState, execution_id: str, format: str = "json") -> str:
	"""
	Convenience function to save workflow state.

	Args:
	    state: Workflow state to save
	    execution_id: Unique identifier for this execution
	    format: Storage format ("json" or "pickle")

	Returns:
	    str: Path to saved state file
	"""
	return default_state_manager.save_state(state, execution_id, format)


def load_workflow_state(filepath: str) -> ContractAnalysisState:
	"""
	Convenience function to load workflow state.

	Args:
	    filepath: Path to saved state file

	Returns:
	    ContractAnalysisState: Loaded workflow state
	"""
	return default_state_manager.load_state(filepath)


def record_workflow_execution(execution_id: str, state: ContractAnalysisState, success: bool) -> None:
	"""
	Convenience function to record workflow execution metrics.

	Args:
	    execution_id: Unique identifier for the execution
	    state: Final workflow state
	    success: Whether execution was successful
	"""
	default_metrics.record_execution(execution_id, state, success)
