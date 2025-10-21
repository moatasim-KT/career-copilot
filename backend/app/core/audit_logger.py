"""
Advanced Audit Logging System
"""

import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AuditLogger:
	"""Advanced audit logging system with structured logging and rotation"""

	def __init__(self, log_path: str = "logs/audit"):
		self.log_path = Path(log_path)
		self.log_path.mkdir(parents=True, exist_ok=True)

		# Setup structured logging
		self.logger = logging.getLogger("audit")
		self.logger.setLevel(logging.INFO)

		# Clear existing handlers to avoid duplicates
		self.logger.handlers.clear()

		# File handler with rotation
		handler = RotatingFileHandler(
			self.log_path / "audit.log",
			maxBytes=10 * 1024 * 1024,  # 10MB
			backupCount=5,
		)

		formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
		handler.setFormatter(formatter)
		self.logger.addHandler(handler)

		# Console handler for development
		if os.getenv("ENVIRONMENT") == "development":
			console_handler = logging.StreamHandler()
			console_handler.setFormatter(formatter)
			self.logger.addHandler(console_handler)

	def log_event(self, event_type: str, user_id: str = None, details: Dict[str, Any] = None, level: str = "INFO"):
		"""Log an audit event"""
		audit_data = {
			"event_type": event_type,
			"user_id": user_id,
			"timestamp": datetime.now(timezone.utc).isoformat(),
			"details": details or {},
			"level": level,
		}

		self.logger.info(f"AUDIT: {event_type} | {json.dumps(audit_data)}")

	def log_security_event(self, event_type: str, user_id: str = None, details: Dict[str, Any] = None):
		"""Log a security-related event"""
		self.log_event(event_type, user_id, details, "WARNING")

	def log_business_event(self, event_type: str, user_id: str = None, details: Dict[str, Any] = None):
		"""Log a business-related event"""
		self.log_event(event_type, user_id, details, "INFO")

	def log_error_event(self, event_type: str, user_id: str = None, details: Dict[str, Any] = None):
		"""Log an error event"""
		self.log_event(event_type, user_id, details, "ERROR")

	def log_performance_event(self, event_type: str, user_id: str = None, details: Dict[str, Any] = None):
		"""Log a performance-related event"""
		self.log_event(event_type, user_id, details, "INFO")

	def get_logs(
		self,
		start_time: Optional[datetime] = None,
		end_time: Optional[datetime] = None,
		event_type: Optional[str] = None,
		user_id: Optional[str] = None,
		limit: int = 100,
	) -> List[Dict[str, Any]]:
		"""Get audit logs with filtering"""
		# In a real implementation, this would query the log files
		# For now, return sample data
		return [
			{
				"timestamp": datetime.now(timezone.utc).isoformat(),
				"event_type": event_type or "sample_event",
				"user_id": user_id or "sample_user",
				"level": "INFO",
				"message": "Sample audit log entry",
			}
		]

	def get_statistics(self) -> Dict[str, Any]:
		"""Get audit log statistics"""
		return {"total_events": 0, "events_by_type": {}, "events_by_user": {}, "last_24_hours": 0}


# Create global audit logger instance
audit_logger = AuditLogger()


# Convenience function
def get_audit_logger() -> AuditLogger:
	"""Get the global audit logger instance"""
	return audit_logger
