"""
SQLAlchemy database models for analysis history and agent execution.
"""

from uuid import uuid4

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship

from ..core.database import Base
from ..utils import utc_now


class AnalysisHistory(Base):
	"""Analysis history database model."""

	__tablename__ = "analysis_history"

	id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
	contract_id = Column(PostgresUUID(as_uuid=True), nullable=False)
	analysis_type = Column(String(100), nullable=False)
	status = Column(String(50), nullable=False, default="pending")
	risk_level = Column(String(50))
	model_used = Column(String(100))
	processing_time = Column(Numeric(10, 3))  # seconds
	total_cost = Column(Numeric(10, 6))  # dollars
	total_tokens = Column(Integer)
	analysis_results = Column(JSON)
	analysis_metadata = Column(JSON)

	# Timestamps
	created_at = Column(DateTime, default=utc_now, nullable=False)
	updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
	completed_at = Column(DateTime)
	deleted_at = Column(DateTime)

	# Relationships
	agent_executions = relationship("AgentExecution", back_populates="analysis", cascade="all, delete-orphan")


class AgentExecution(Base):
	"""Agent execution database model."""

	__tablename__ = "agent_executions"

	id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
	analysis_id = Column(PostgresUUID(as_uuid=True), ForeignKey("analysis_history.id"), nullable=False)
	agent_name = Column(String(100), nullable=False)
	agent_type = Column(String(50), nullable=False)
	agent_id = Column(String(100))
	status = Column(String(50), nullable=False, default="running")

	# LLM details
	llm_provider = Column(String(50))  # openai, anthropic, etc.
	model_name = Column(String(100))
	provider = Column(String(50))  # alias for llm_provider for compatibility

	# Execution details
	started_at = Column(DateTime, default=utc_now, nullable=False)
	completed_at = Column(DateTime)
	execution_time = Column(Numeric(10, 3))  # seconds
	duration = Column(Numeric(10, 3))  # alias for execution_time for compatibility

	# Cost and usage
	cost = Column(Numeric(10, 6))  # dollars
	token_usage = Column(Integer)

	# Data
	input_data = Column(JSON)
	output_data = Column(JSON)

	# Error handling
	error_message = Column(Text)
	error_type = Column(String(100))
	retry_count = Column(Integer, default=0)
	fallback_used = Column(Boolean, default=False)
	circuit_breaker_triggered = Column(Boolean, default=False)

	# Metadata
	execution_metadata = Column(JSON)

	# Timestamps
	created_at = Column(DateTime, default=utc_now, nullable=False)
	updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

	# Relationships
	analysis = relationship("AnalysisHistory", back_populates="agent_executions")


class UserSettings(Base):
	"""User settings database model."""

	__tablename__ = "user_settings"

	id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
	user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
	daily_application_goal = Column(Integer, default=10, nullable=False)
	preferred_industries = Column(JSON, default=list, nullable=False)
	preferred_locations = Column(JSON, default=list, nullable=False)
	experience_level = Column(String(50), nullable=True)
	risk_thresholds = Column(JSON, default=dict, nullable=False)
	notification_preferences = Column(JSON, default=dict, nullable=False)
	ai_model_preference = Column(String(50), default="groq", nullable=False)

	# Timestamps
	created_at = Column(DateTime, default=utc_now, nullable=False)
	updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

	# Relationships
	user = relationship("User", back_populates="settings")


class AuditLog(Base):
	"""Audit log database model."""

	__tablename__ = "audit_logs"

	id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
	user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
	event_type = Column(String(100), nullable=False, index=True)
	event_description = Column(Text, nullable=False)
	ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
	user_agent = Column(Text, nullable=True)
	session_id = Column(String(255), nullable=True)
	resource_type = Column(String(100), nullable=True)
	resource_id = Column(String(255), nullable=True)
	old_values = Column(JSON, nullable=True)
	new_values = Column(JSON, nullable=True)
	event_metadata = Column(JSON, nullable=True)
	severity = Column(String(20), default="info", nullable=False)

	# Timestamps
	created_at = Column(DateTime, default=utc_now, nullable=False)


class SecurityEvent(Base):
	"""Security event database model."""

	__tablename__ = "security_events"

	id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
	user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
	event_type = Column(String(100), nullable=False, index=True)
	description = Column(Text, nullable=False)
	ip_address = Column(String(45), nullable=True)
	user_agent = Column(Text, nullable=True)
	session_id = Column(String(255), nullable=True)
	risk_score = Column(Integer, default=0, nullable=False)
	blocked = Column(Boolean, default=False, nullable=False)
	event_metadata = Column(JSON, nullable=True)

	# Timestamps
	created_at = Column(DateTime, default=utc_now, nullable=False)


class ContractAnalysis(Base):
	"""Contract analysis database model (placeholder for compatibility)."""

	__tablename__ = "contract_analyses"

	id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
	contract_id = Column(PostgresUUID(as_uuid=True), nullable=False)
	analysis_type = Column(String(100), nullable=False)
	status = Column(String(50), nullable=False, default="pending")
	results = Column(JSON)

	# Timestamps
	created_at = Column(DateTime, default=utc_now, nullable=False)
	updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
