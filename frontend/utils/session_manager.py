"""
Session management utilities for the Streamlit frontend.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import streamlit as st


class SessionManager:
	"""Manages Streamlit session state for the contract analyzer."""

	def __init__(self):
		"""Initialize session manager."""
		self.initialize_session_state()

	def initialize_session_state(self):
		"""Initialize all session state variables with default values."""
		default_state = {
			# Analysis state
			"analysis_results": None,
			"analysis_in_progress": False,
			"task_id": None,
			"progress_data": None,
			# Error handling
			"error_message": None,
			"last_error_timestamp": None,
			# File upload state
			"uploaded_file": None,
			"file_validation_passed": False,
			# UI state
			"show_advanced_options": False,
			"selected_tab": "upload",
			"show_email_preview": False,
			# Analysis options
			"analysis_timeout": 300,
			"analysis_priority": "normal",
			"enable_progress_tracking": True,
			# Results state
			"results_expanded": True,
			"email_edited": False,
			"edited_email_content": "",
			# History
			"analysis_history": [],
			"last_analysis_timestamp": None,
			# Backend connection
			"backend_status": "unknown",
			"last_health_check": None,
		}

		for key, default_value in default_state.items():
			if key not in st.session_state:
				st.session_state[key] = default_value

	def reset_analysis_state(self):
		"""Reset analysis-related session state."""
		st.session_state.analysis_results = None
		st.session_state.analysis_in_progress = False
		st.session_state.task_id = None
		st.session_state.progress_data = None
		st.session_state.error_message = None

	def set_analysis_in_progress(self, task_id: str):
		"""Set analysis as in progress with task ID."""
		st.session_state.analysis_in_progress = True
		st.session_state.task_id = task_id
		st.session_state.error_message = None
		st.session_state.analysis_results = None

	def set_analysis_complete(self, results: Dict[str, Any]):
		"""Set analysis as complete with results."""
		st.session_state.analysis_in_progress = False
		st.session_state.analysis_results = results
		st.session_state.last_analysis_timestamp = datetime.now()

		# Add to history
		self.add_to_analysis_history(results)

	def set_analysis_error(self, error_message: str):
		"""Set analysis error state."""
		st.session_state.analysis_in_progress = False
		st.session_state.error_message = error_message
		st.session_state.last_error_timestamp = datetime.now()
		st.session_state.analysis_results = None

	def update_progress(self, progress_data: Dict[str, Any]):
		"""Update analysis progress data."""
		st.session_state.progress_data = progress_data

	def set_file_uploaded(self, uploaded_file, validation_passed: bool = True):
		"""Set uploaded file state."""
		st.session_state.uploaded_file = uploaded_file
		st.session_state.file_validation_passed = validation_passed

	def clear_file_upload(self):
		"""Clear file upload state."""
		st.session_state.uploaded_file = None
		st.session_state.file_validation_passed = False

	def set_analysis_options(self, timeout: int = 300, priority: str = "normal", enable_progress: bool = True):
		"""Set analysis options."""
		st.session_state.analysis_timeout = timeout
		st.session_state.analysis_priority = priority
		st.session_state.enable_progress_tracking = enable_progress

	def get_analysis_options(self) -> Dict[str, Any]:
		"""Get current analysis options."""
		return {
			"timeout_seconds": st.session_state.analysis_timeout,
			"priority": st.session_state.analysis_priority,
			"enable_progress_tracking": st.session_state.enable_progress_tracking,
		}

	def set_email_edited(self, edited_content: str):
		"""Set email as edited with new content."""
		st.session_state.email_edited = True
		st.session_state.edited_email_content = edited_content

	def get_email_content(self) -> str:
		"""Get current email content (edited or original)."""
		if st.session_state.email_edited and st.session_state.edited_email_content:
			return st.session_state.edited_email_content
		elif st.session_state.analysis_results:
			return st.session_state.analysis_results.get("email_draft", "")
		return ""

	def add_to_analysis_history(self, results: Dict[str, Any]):
		"""Add analysis results to history."""
		history_entry = {
			"timestamp": datetime.now().isoformat(),
			"filename": getattr(st.session_state.uploaded_file, "name", "Unknown"),
			"risk_score": results.get("overall_risk_score"),
			"risky_clauses_count": len(results.get("risky_clauses", [])),
			"redlines_count": len(results.get("suggested_redlines", [])),
			"status": results.get("status", "unknown"),
		}

		# Keep only last 10 analyses
		if len(st.session_state.analysis_history) >= 10:
			st.session_state.analysis_history.pop(0)

		st.session_state.analysis_history.append(history_entry)

	def get_analysis_history(self) -> List[Dict[str, Any]]:
		"""Get analysis history."""
		return st.session_state.analysis_history

	def clear_analysis_history(self):
		"""Clear analysis history."""
		st.session_state.analysis_history = []

	def set_backend_status(self, status: str, health_data: Optional[Dict] = None):
		"""Set backend connection status."""
		st.session_state.backend_status = status
		st.session_state.last_health_check = datetime.now()

		if health_data:
			st.session_state.backend_health_data = health_data

	def is_backend_healthy(self) -> bool:
		"""Check if backend is healthy."""
		return st.session_state.backend_status == "healthy"

	def get_backend_status(self) -> Dict[str, Any]:
		"""Get backend status information."""
		return {
			"status": st.session_state.backend_status,
			"last_check": st.session_state.last_health_check,
			"health_data": getattr(st.session_state, "backend_health_data", None),
		}

	def should_check_backend_health(self) -> bool:
		"""Check if backend health should be checked."""
		if not st.session_state.last_health_check:
			return True

		# Check every 5 minutes
		time_since_check = datetime.now() - st.session_state.last_health_check
		return time_since_check > timedelta(minutes=5)

	def set_ui_state(self, **kwargs):
		"""Set UI state variables."""
		for key, value in kwargs.items():
			if hasattr(st.session_state, key):
				setattr(st.session_state, key, value)

	def get_ui_state(self, key: str, default: Any = None) -> Any:
		"""Get UI state variable."""
		return getattr(st.session_state, key, default)

	def export_session_data(self) -> Dict[str, Any]:
		"""Export session data for debugging or persistence."""
		exportable_keys = [
			"analysis_history",
			"analysis_timeout",
			"analysis_priority",
			"enable_progress_tracking",
			"backend_status",
			"last_analysis_timestamp",
		]

		export_data = {}
		for key in exportable_keys:
			if hasattr(st.session_state, key):
				value = getattr(st.session_state, key)
				# Convert datetime objects to strings
				if isinstance(value, datetime):
					value = value.isoformat()
				export_data[key] = value

		return export_data

	def import_session_data(self, data: Dict[str, Any]):
		"""Import session data from exported data."""
		for key, value in data.items():
			if key in ["last_analysis_timestamp", "last_health_check"]:
				# Convert ISO strings back to datetime
				if isinstance(value, str):
					try:
						value = datetime.fromisoformat(value)
					except ValueError:
						continue

			setattr(st.session_state, key, value)

	def cleanup_old_data(self):
		"""Clean up old session data."""
		# Remove old history entries (older than 24 hours)
		if st.session_state.analysis_history:
			cutoff_time = datetime.now() - timedelta(hours=24)

			filtered_history = []
			for entry in st.session_state.analysis_history:
				try:
					entry_time = datetime.fromisoformat(entry["timestamp"])
					if entry_time > cutoff_time:
						filtered_history.append(entry)
				except (ValueError, KeyError):
					# Keep entries with invalid timestamps
					filtered_history.append(entry)

			st.session_state.analysis_history = filtered_history

	def get_session_summary(self) -> Dict[str, Any]:
		"""Get a summary of current session state."""
		return {
			"has_uploaded_file": st.session_state.uploaded_file is not None,
			"analysis_in_progress": st.session_state.analysis_in_progress,
			"has_results": st.session_state.analysis_results is not None,
			"has_error": st.session_state.error_message is not None,
			"backend_healthy": self.is_backend_healthy(),
			"history_count": len(st.session_state.analysis_history),
			"current_task_id": st.session_state.task_id,
		}

	def reset_session(self):
		"""Reset entire session state."""
		# Clear all session state
		for key in list(st.session_state.keys()):
			del st.session_state[key]

		# Reinitialize
		self.initialize_session_state()


# Global session manager instance
session_manager = SessionManager()
