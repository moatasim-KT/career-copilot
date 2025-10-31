"""
Alerting system for the Career Copilot.
"""

import logging
from typing import Dict, List, Any
from .monitoring import alert_manager, AlertSeverity

logger = logging.getLogger(__name__)


class AlertRule:
	"""Represents an alert rule."""

	def __init__(self, name: str, condition: str, severity: AlertSeverity, description: str = ""):
		self.name = name
		self.condition = condition
		self.severity = severity
		self.description = description
		self.enabled = True

	def to_dict(self) -> Dict[str, Any]:
		"""Convert alert rule to dictionary."""
		return {
			"name": self.name,
			"condition": self.condition,
			"severity": self.severity.value,
			"description": self.description,
			"enabled": self.enabled,
		}


def initialize_default_alert_rules():
	"""Initialize default alert rules for the system."""

	default_rules = [
		AlertRule(name="High CPU Usage", condition="cpu_usage > 80", severity=AlertSeverity.HIGH, description="CPU usage is above 80%"),
		AlertRule(name="High Memory Usage", condition="memory_usage > 85", severity=AlertSeverity.HIGH, description="Memory usage is above 85%"),
		AlertRule(name="Low Disk Space", condition="disk_usage > 90", severity=AlertSeverity.CRITICAL, description="Disk usage is above 90%"),
		AlertRule(
			name="High Response Time",
			condition="response_time > 2000",
			severity=AlertSeverity.MEDIUM,
			description="API response time is above 2 seconds",
		),
		AlertRule(name="High Error Rate", condition="error_rate > 5", severity=AlertSeverity.HIGH, description="Error rate is above 5%"),
		AlertRule(
			name="Database Connection Issues",
			condition="db_connection_errors > 0",
			severity=AlertSeverity.CRITICAL,
			description="Database connection errors detected",
		),
		AlertRule(
			name="AI Service Unavailable",
			condition="ai_service_health == false",
			severity=AlertSeverity.HIGH,
			description="AI service is not responding",
		),
		AlertRule(
			name="File Upload Failures",
			condition="file_upload_failures > 10",
			severity=AlertSeverity.MEDIUM,
			description="Multiple file upload failures detected",
		),
		AlertRule(
			name="Security Violations",
			condition="security_violations > 0",
			severity=AlertSeverity.CRITICAL,
			description="Security violations detected",
		),
		AlertRule(
			name="Rate Limit Exceeded",
			condition="rate_limit_violations > 100",
			severity=AlertSeverity.MEDIUM,
			description="Rate limit violations detected",
		),
		AlertRule(
			name="Cache Miss Rate High", condition="cache_miss_rate > 50", severity=AlertSeverity.LOW, description="Cache miss rate is above 50%"
		),
		AlertRule(
			name="Queue Backlog", condition="queue_size > 1000", severity=AlertSeverity.MEDIUM, description="Processing queue has large backlog"
		),
		AlertRule(
			name="External Service Timeout",
			condition="external_service_timeouts > 5",
			severity=AlertSeverity.MEDIUM,
			description="External service timeouts detected",
		),
		AlertRule(
			name="Webhook Delivery Failures",
			condition="webhook_failures > 10",
			severity=AlertSeverity.LOW,
			description="Webhook delivery failures detected",
		),
		AlertRule(
			name="Log Processing Delays",
			condition="log_processing_delay > 300",
			severity=AlertSeverity.LOW,
			description="Log processing is delayed by more than 5 minutes",
		),
		AlertRule(
			name="Backup Failures", condition="backup_failures > 0", severity=AlertSeverity.HIGH, description="Backup process failures detected"
		),
		AlertRule(
			name="SSL Certificate Expiry",
			condition="ssl_cert_expires_in_days < 30",
			severity=AlertSeverity.MEDIUM,
			description="SSL certificate expires in less than 30 days",
		),
	]

	# Add rules to the alert manager
	for rule in default_rules:
		alert_manager.alert_rules.append(rule)

	logger.info(f"Initialized {len(default_rules)} default alert rules")
	return len(default_rules)


def create_alert(name: str, message: str, severity: AlertSeverity, details: Dict[str, Any] | None = None):
	"""Create a new alert."""
	alert = {
		"name": name,
		"message": message,
		"severity": severity.value,
		"timestamp": "now",  # In a real system, use proper timestamp
		"details": details or {},
	}

	alert_manager.alerts.append(alert)
	logger.warning(f"Alert created: {name} - {message}")
	return alert


def get_active_alerts() -> List[Dict[str, Any]]:
	"""Get all active alerts."""
	return alert_manager.alerts


def get_alert_rules() -> List[Dict[str, Any]]:
	"""Get all alert rules."""
	return [rule.to_dict() for rule in alert_manager.alert_rules]


def clear_alerts():
	"""Clear all active alerts."""
	count = len(alert_manager.alerts)
	alert_manager.alerts.clear()
	logger.info(f"Cleared {count} alerts")
	return count


def evaluate_alert_rules():
	"""Evaluate all alert rules (placeholder for actual implementation)."""
	# In a real system, this would evaluate conditions against actual metrics
	logger.debug("Evaluating alert rules...")
	return {"evaluated": len(alert_manager.alert_rules), "triggered": 0}
