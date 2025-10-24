"""
Audit logging for security monitoring and compliance.
"""

import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class SecurityEventType(Enum):
	"""Types of security events to log."""

	FILE_UPLOAD = "file_upload"
	FILE_VALIDATION = "file_validation"
	FILE_QUARANTINE = "file_quarantine"
	API_REQUEST = "api_request"
	API_RESPONSE = "api_response"
	AUTHENTICATION = "authentication"
	AUTHORIZATION = "authorization"
	INJECTION_ATTEMPT = "injection_attempt"
	SUSPICIOUS_ACTIVITY = "suspicious_activity"
	SYSTEM_ERROR = "system_error"
	DATA_ACCESS = "data_access"
	CONFIGURATION_CHANGE = "configuration_change"


class SecurityLevel(Enum):
	"""Security levels for events."""

	LOW = "low"
	MEDIUM = "medium"
	HIGH = "high"
	CRITICAL = "critical"


class AuditLogger:
	"""Comprehensive audit logging for security monitoring."""

	def __init__(self, log_dir: Optional[str] = None):
		self.logger = logging.getLogger(__name__)
		self.session_id = str(uuid.uuid4())

		# Set up log directory
		if log_dir:
			self.log_dir = Path(log_dir)
		else:
			self.log_dir = Path("logs/audit")

		self.log_dir.mkdir(parents=True, exist_ok=True)

		# Set up file handlers for different log types
		self._setup_log_handlers()

		# In-memory buffer for real-time monitoring
		self.event_buffer: List[Dict[str, Any]] = []
		self.max_buffer_size = 1000

	def _setup_log_handlers(self):
		"""Set up file handlers for different types of logs."""
		# Security events log
		security_handler = logging.FileHandler(self.log_dir / "security_events.log", mode="a")
		security_handler.setLevel(logging.INFO)
		security_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
		security_handler.setFormatter(security_formatter)

		# Audit trail log
		audit_handler = logging.FileHandler(self.log_dir / "audit_trail.log", mode="a")
		audit_handler.setLevel(logging.INFO)
		audit_formatter = logging.Formatter("%(asctime)s - AUDIT - %(message)s")
		audit_handler.setFormatter(audit_formatter)

		# Error log
		error_handler = logging.FileHandler(self.log_dir / "security_errors.log", mode="a")
		error_handler.setLevel(logging.ERROR)
		error_formatter = logging.Formatter("%(asctime)s - ERROR - %(message)s")
		error_handler.setFormatter(error_formatter)

		# Add handlers to logger
		self.logger.addHandler(security_handler)
		self.logger.addHandler(audit_handler)
		self.logger.addHandler(error_handler)

	def log_security_event(
		self,
		event_type: SecurityEventType,
		level: SecurityLevel,
		message: str,
		details: Optional[Dict[str, Any]] = None,
		user_id: Optional[str] = None,
		ip_address: Optional[str] = None,
		user_agent: Optional[str] = None,
	):
		"""
		Log a security event.

		Args:
		    event_type: Type of security event
		    level: Security level of the event
		    message: Event message
		    details: Additional event details
		    user_id: User identifier (if available)
		    ip_address: Client IP address
		    user_agent: Client user agent
		"""
		event_data = {
			"timestamp": datetime.now(timezone.utc).isoformat(),
			"session_id": self.session_id,
			"event_type": event_type.value,
			"security_level": level.value,
			"message": message,
			"user_id": user_id,
			"ip_address": ip_address,
			"user_agent": user_agent,
			"details": details or {},
		}

		# Add to buffer
		self.event_buffer.append(event_data)
		if len(self.event_buffer) > self.max_buffer_size:
			self.event_buffer.pop(0)

		# Log based on security level
		log_message = self._format_log_message(event_data)

		if level == SecurityLevel.CRITICAL:
			self.logger.critical(log_message)
		elif level == SecurityLevel.HIGH:
			self.logger.error(log_message)
		elif level == SecurityLevel.MEDIUM:
			self.logger.warning(log_message)
		else:
			self.logger.info(log_message)

		# Write to JSON audit file
		self._write_json_audit(event_data)

	def log_file_upload(
		self,
		filename: str,
		file_size: int,
		file_hash: str,
		validation_result: Dict[str, Any],
		user_id: Optional[str] = None,
		ip_address: Optional[str] = None,
	):
		"""Log file upload event."""
		level = SecurityLevel.LOW
		if not validation_result.get("is_secure", False):
			level = SecurityLevel.HIGH

		self.log_security_event(
			event_type=SecurityEventType.FILE_UPLOAD,
			level=level,
			message=f"File upload: {filename} ({file_size} bytes)",
			details={"filename": filename, "file_size": file_size, "file_hash": file_hash, "validation_result": validation_result},
			user_id=user_id,
			ip_address=ip_address,
		)

	def log_file_quarantine(
		self, filename: str, file_hash: str, reason: str, threats_detected: List[str], user_id: Optional[str] = None, ip_address: Optional[str] = None
	):
		"""Log file quarantine event."""
		self.log_security_event(
			event_type=SecurityEventType.FILE_QUARANTINE,
			level=SecurityLevel.HIGH,
			message=f"File quarantined: {filename} - {reason}",
			details={"filename": filename, "file_hash": file_hash, "reason": reason, "threats_detected": threats_detected},
			user_id=user_id,
			ip_address=ip_address,
		)

	def log_injection_attempt(
		self, attack_type: str, input_data: str, pattern_detected: str, user_id: Optional[str] = None, ip_address: Optional[str] = None
	):
		"""Log injection attack attempt."""
		self.log_security_event(
			event_type=SecurityEventType.INJECTION_ATTEMPT,
			level=SecurityLevel.CRITICAL,
			message=f"Injection attempt detected: {attack_type}",
			details={
				"attack_type": attack_type,
				"input_data": input_data[:500],  # Limit size
				"pattern_detected": pattern_detected,
			},
			user_id=user_id,
			ip_address=ip_address,
		)

	def log_api_request(
		self,
		endpoint: str,
		method: str,
		request_data: Optional[Dict[str, Any]] = None,
		user_id: Optional[str] = None,
		ip_address: Optional[str] = None,
	):
		"""Log API request."""
		self.log_security_event(
			event_type=SecurityEventType.API_REQUEST,
			level=SecurityLevel.LOW,
			message=f"API request: {method} {endpoint}",
			details={"endpoint": endpoint, "method": method, "request_data": self._sanitize_sensitive_data(request_data)},
			user_id=user_id,
			ip_address=ip_address,
		)

	def log_api_response(
		self, endpoint: str, status_code: int, response_time: float, user_id: Optional[str] = None, ip_address: Optional[str] = None
	):
		"""Log API response."""
		level = SecurityLevel.LOW
		if status_code >= 400:
			level = SecurityLevel.MEDIUM
		if status_code >= 500:
			level = SecurityLevel.HIGH

		self.log_security_event(
			event_type=SecurityEventType.API_RESPONSE,
			level=level,
			message=f"API response: {status_code} for {endpoint}",
			details={"endpoint": endpoint, "status_code": status_code, "response_time": response_time},
			user_id=user_id,
			ip_address=ip_address,
		)

	def log_suspicious_activity(self, activity: str, details: Dict[str, Any], user_id: Optional[str] = None, ip_address: Optional[str] = None):
		"""Log suspicious activity."""
		self.log_security_event(
			event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
			level=SecurityLevel.HIGH,
			message=f"Suspicious activity: {activity}",
			details=details,
			user_id=user_id,
			ip_address=ip_address,
		)

	def log_system_error(self, error: str, error_type: str, stack_trace: Optional[str] = None, user_id: Optional[str] = None):
		"""Log system error."""
		self.log_security_event(
			event_type=SecurityEventType.SYSTEM_ERROR,
			level=SecurityLevel.MEDIUM,
			message=f"System error: {error_type}",
			details={"error": error, "error_type": error_type, "stack_trace": stack_trace},
			user_id=user_id,
		)

	def _format_log_message(self, event_data: Dict[str, Any]) -> str:
		"""Format event data for logging."""
		return json.dumps(event_data, default=str)

	def _write_json_audit(self, event_data: Dict[str, Any]):
		"""Write event to JSON audit file."""
		try:
			audit_file = self.log_dir / "audit_events.jsonl"
			with open(audit_file, "a", encoding="utf-8") as f:
				f.write(json.dumps(event_data, default=str) + "\n")
		except Exception as e:
			self.logger.error(f"Failed to write JSON audit: {e!s}")

	def _sanitize_sensitive_data(self, data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
		"""Remove sensitive data from logs."""
		if not data:
			return data

		sensitive_keys = {"password", "passwd", "pwd", "secret", "token", "key", "api_key", "access_token", "refresh_token", "authorization", "auth"}

		sanitized = {}
		for key, value in data.items():
			if any(sensitive in key.lower() for sensitive in sensitive_keys):
				sanitized[key] = "[REDACTED]"
			elif isinstance(value, dict):
				sanitized[key] = self._sanitize_sensitive_data(value)
			else:
				sanitized[key] = value

		return sanitized

	def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
		"""Get recent security events from buffer."""
		return self.event_buffer[-limit:]

	def get_events_by_type(self, event_type: SecurityEventType, limit: int = 100) -> List[Dict[str, Any]]:
		"""Get events filtered by type."""
		filtered_events = [event for event in self.event_buffer if event.get("event_type") == event_type.value]
		return filtered_events[-limit:]

	def get_events_by_level(self, level: SecurityLevel, limit: int = 100) -> List[Dict[str, Any]]:
		"""Get events filtered by security level."""
		filtered_events = [event for event in self.event_buffer if event.get("security_level") == level.value]
		return filtered_events[-limit:]

	def generate_security_report(self) -> Dict[str, Any]:
		"""Generate a security report from recent events."""
		total_events = len(self.event_buffer)

		# Count events by type
		event_counts = {}
		for event in self.event_buffer:
			event_type = event.get("event_type", "unknown")
			event_counts[event_type] = event_counts.get(event_type, 0) + 1

		# Count events by level
		level_counts = {}
		for event in self.event_buffer:
			level = event.get("security_level", "unknown")
			level_counts[level] = level_counts.get(level, 0) + 1

		# Get recent critical events
		critical_events = self.get_events_by_level(SecurityLevel.CRITICAL, limit=10)

		return {
			"report_timestamp": datetime.now(timezone.utc).isoformat(),
			"total_events": total_events,
			"event_counts_by_type": event_counts,
			"event_counts_by_level": level_counts,
			"recent_critical_events": critical_events,
			"session_id": self.session_id,
		}

	def clear_buffer(self):
		"""Clear the event buffer."""
		self.event_buffer.clear()

	def export_events(self, file_path: str, event_types: Optional[List[SecurityEventType]] = None):
		"""Export events to a file."""
		try:
			events_to_export = self.event_buffer

			if event_types:
				event_type_values = [et.value for et in event_types]
				events_to_export = [event for event in self.event_buffer if event.get("event_type") in event_type_values]

			with open(file_path, "w", encoding="utf-8") as f:
				json.dump(events_to_export, f, indent=2, default=str)

			self.logger.info(f"Exported {len(events_to_export)} events to {file_path}")

		except Exception as e:
			self.logger.error(f"Failed to export events: {e!s}")
