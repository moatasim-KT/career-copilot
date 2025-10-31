"""
SQLAlchemy database models for analysis history and agent execution.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Text, Integer, Numeric, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from ..core.database import Base
from sqlalchemy.orm import relationship


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
	created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
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
	started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
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
	created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

	# Relationships
	analysis = relationship("AnalysisHistory", back_populates="agent_executions")


class ContractAnalysis(Base):
	"""Contract analysis database model (placeholder for compatibility)."""

	__tablename__ = "contract_analyses"

	id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
	contract_id = Column(PostgresUUID(as_uuid=True), nullable=False)
	analysis_type = Column(String(100), nullable=False)
	status = Column(String(50), nullable=False, default="pending")
	results = Column(JSON)

	# Timestamps
	created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
