"""
SQLAlchemy database models for the Career Copilot application.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    BigInteger,
    DECIMAL,
    Index,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, INET, ARRAY as PG_ARRAY
from sqlalchemy.types import TypeDecorator, String as SQLString
import json
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


# Compatibility types for SQLite
class UUID(TypeDecorator):
    """UUID type that works with both PostgreSQL and SQLite."""
    impl = SQLString
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(SQLString(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return str(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return uuid.UUID(value) if isinstance(value, str) else value


class ARRAY(TypeDecorator):
    """Array type that works with both PostgreSQL and SQLite."""
    impl = Text
    cache_ok = True
    
    def __init__(self, item_type):
        self.item_type = item_type
        super().__init__()
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_ARRAY(self.item_type))
        else:
            return dialect.type_descriptor(Text)
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return json.dumps(value) if value else '[]'
    
    def process_result_value(self, value, dialect):
        if value is None:
            return []
        elif dialect.name == 'postgresql':
            return value
        else:
            try:
                return json.loads(value) if value else []
            except (json.JSONDecodeError, TypeError):
                return []


class JSONB_COMPAT(TypeDecorator):
    """JSONB type that works with both PostgreSQL and SQLite."""
    impl = Text
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB)
        else:
            return dialect.type_descriptor(JSON)
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return json.dumps(value) if value else '{}'
    
    def process_result_value(self, value, dialect):
        if value is None:
            return {}
        elif dialect.name == 'postgresql':
            return value
        else:
            try:
                return json.loads(value) if value else {}
            except (json.JSONDecodeError, TypeError):
                return {}


class INET_COMPAT(TypeDecorator):
    """INET type that works with both PostgreSQL and SQLite."""
    impl = String
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(INET)
        else:
            return dialect.type_descriptor(String(45))  # IPv6 max length
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value)
    
    def process_result_value(self, value, dialect):
        return value


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Authentication and security fields
    password_hash = Column(String(255), nullable=False)  # bcrypt hash
    roles = Column(ARRAY(String), default=[], nullable=False)
    permissions = Column(ARRAY(String), default=[], nullable=False)
    security_level = Column(String(20), default="standard", nullable=False)
    
    # MFA fields
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(32), nullable=True)
    backup_codes = Column(ARRAY(String), default=[], nullable=True)
    
    # Session and login tracking
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String(45), nullable=True)
    last_login_user_agent = Column(Text, nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Account status
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String(255), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    contract_analyses = relationship("ContractAnalysis", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class APIKey(Base):
    """API key model for programmatic access."""
    
    __tablename__ = "api_keys"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key_name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, index=True)
    permissions = Column(ARRAY(String), default=[], nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    # Indexes
    __table_args__ = (
        Index("idx_api_keys_user_id", "user_id"),
        Index("idx_api_keys_key_hash", "key_hash"),
    )
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, key_name='{self.key_name}', user_id={self.user_id})>"


class ContractAnalysis(Base):
    """Contract analysis model for storing analysis results."""
    
    __tablename__ = "contract_analyses"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    contract_text = Column(Text, nullable=True)  # Store extracted text
    analysis_status = Column(String(50), default="pending", nullable=False)
    risk_score = Column(DECIMAL(3, 2), nullable=True)  # Overall risk score 0.00-1.00
    risky_clauses = Column(JSONB_COMPAT(), nullable=True)  # JSON array of risky clauses
    suggested_redlines = Column(JSONB_COMPAT(), nullable=True)  # JSON array of redline suggestions
    email_draft = Column(Text, nullable=True)  # Generated email draft
    processing_time_seconds = Column(DECIMAL(10, 3), nullable=True)  # Processing time
    error_message = Column(Text, nullable=True)  # Error details if analysis failed
    workflow_state = Column(JSONB_COMPAT(), nullable=True)  # LangGraph workflow state
    ai_model_used = Column(String(100), nullable=True)  # Which AI model was used
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="contract_analyses")
    analysis_history = relationship("AnalysisHistory", back_populates="contract_analysis", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_contract_analyses_user_id", "user_id"),
        Index("idx_contract_analyses_status", "analysis_status"),
        Index("idx_contract_analyses_created_at", "created_at"),
        Index("idx_contract_analyses_file_hash", "file_hash"),
    )
    
    def __repr__(self):
        return f"<ContractAnalysis(id={self.id}, filename='{self.filename}', status='{self.analysis_status}')>"


class AuditLog(Base):
    """Audit log model for security and compliance tracking."""
    
    __tablename__ = "audit_logs"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String(100), nullable=False, index=True)
    event_data = Column(JSONB_COMPAT(), nullable=True)  # Additional event details
    resource_type = Column(String(50), nullable=True)  # Type of resource accessed
    resource_id = Column(String(255), nullable=True)  # ID of resource accessed
    action = Column(String(50), nullable=True)  # Action performed (CREATE, READ, UPDATE, DELETE)
    result = Column(String(20), nullable=True)  # SUCCESS, FAILURE, ERROR
    ip_address = Column(INET_COMPAT(), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True)
    request_id = Column(String(255), nullable=True)  # For request correlation
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    # Indexes
    __table_args__ = (
        Index("idx_audit_logs_user_id", "user_id"),
        Index("idx_audit_logs_event_type", "event_type"),
        Index("idx_audit_logs_created_at", "created_at"),
        Index("idx_audit_logs_resource_type", "resource_type"),
        Index("idx_audit_logs_action", "action"),
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type='{self.event_type}', user_id={self.user_id})>"


class UserSession(Base):
    """User session model for JWT session management."""
    
    __tablename__ = "user_sessions"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    token_family = Column(String(255), nullable=False)  # For refresh token rotation
    
    # Session metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_info = Column(JSONB_COMPAT(), nullable=True)
    
    # Session status
    is_active = Column(Boolean, default=True, nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_sessions_user_id", "user_id"),
        Index("idx_user_sessions_session_id", "session_id"),
        Index("idx_user_sessions_active", "is_active"),
        Index("idx_user_sessions_expires_at", "expires_at"),
    )


class RoleAssignment(Base):
    """Role assignment model for RBAC."""
    
    __tablename__ = "role_assignments"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)
    
    # Assignment metadata
    assigned_by = Column(UUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Assignment context
    context = Column(JSONB_COMPAT(), nullable=True)  # Additional context for role assignment
    reason = Column(Text, nullable=True)  # Reason for assignment
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])
    
    # Indexes
    __table_args__ = (
        Index("idx_role_assignments_user_id", "user_id"),
        Index("idx_role_assignments_role", "role"),
        Index("idx_role_assignments_active", "is_active"),
        Index("idx_role_assignments_expires_at", "expires_at"),
    )


class PermissionGrant(Base):
    """Permission grant model for fine-grained access control."""
    
    __tablename__ = "permission_grants"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    permission = Column(String(100), nullable=False)
    
    # Grant metadata
    granted_by = Column(UUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    granted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Grant context
    resource_type = Column(String(50), nullable=True)  # Type of resource
    resource_id = Column(String(255), nullable=True)  # Specific resource ID
    conditions = Column(JSONB_COMPAT(), nullable=True)  # Conditions for permission
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    granted_by_user = relationship("User", foreign_keys=[granted_by])
    
    # Indexes
    __table_args__ = (
        Index("idx_permission_grants_user_id", "user_id"),
        Index("idx_permission_grants_permission", "permission"),
        Index("idx_permission_grants_active", "is_active"),
        Index("idx_permission_grants_resource", "resource_type", "resource_id"),
    )


class SecurityEvent(Base):
    """Security event model for audit and monitoring."""
    
    __tablename__ = "security_events"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Event details
    event_type = Column(String(50), nullable=False, index=True)
    event_category = Column(String(30), nullable=False)  # authentication, authorization, etc.
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    
    # Event context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True)
    request_id = Column(String(255), nullable=True)
    
    # Event data
    action = Column(String(255), nullable=False)
    resource = Column(String(255), nullable=True)
    result = Column(String(20), nullable=True)  # success, failure, error
    details = Column(JSONB_COMPAT(), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index("idx_security_events_user_id", "user_id"),
        Index("idx_security_events_type", "event_type"),
        Index("idx_security_events_category", "event_category"),
        Index("idx_security_events_severity", "severity"),
        Index("idx_security_events_created_at", "created_at"),
        Index("idx_security_events_result", "result"),
    )


# Additional indexes for performance optimization
Index("idx_users_active", User.is_active)
Index("idx_users_roles", User.roles)
Index("idx_users_security_level", User.security_level)
Index("idx_users_mfa_enabled", User.mfa_enabled)
Index("idx_users_last_login", User.last_login)
Index("idx_api_keys_active", APIKey.is_active)
Index("idx_contract_analyses_risk_score", ContractAnalysis.risk_score)
Index("idx_audit_logs_result", AuditLog.result)


class UserNotificationPreference(Base):
    """User notification preference model for storing user-specific notification settings."""

    __tablename__ = "user_notification_preferences"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    notification_type = Column(String(100), nullable=False)
    channel_id = Column(String(100), nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")

    __table_args__ = (
        Index("idx_user_notification_preferences_user_id_type", "user_id", "notification_type"),
        Index("idx_user_notification_preferences_user_id", "user_id"),
        Index("idx_user_notification_preferences_notification_type", "notification_type"),
    )

    def __repr__(self):
        return f"<UserNotificationPreference(id={self.id}, user_id='{self.user_id}', notification_type='{self.notification_type}')>"


class DocuSignEnvelope(Base):
    """DocuSign envelope model for tracking signing workflows."""

    __tablename__ = "docusign_envelopes"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    envelope_id = Column(String(255), nullable=False, unique=True, index=True)
    contract_analysis_id = Column(UUID(), ForeignKey("contract_analyses.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), nullable=False, index=True)
    recipients = Column(JSONB_COMPAT(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    contract_analysis = relationship("ContractAnalysis")

    def __repr__(self):
        return f"<DocuSignEnvelope(id={self.id}, envelope_id='{self.envelope_id}', status='{self.status}')>"


class EmailDeliveryStatus(Base):
    """Email delivery status model for tracking sent emails."""

    __tablename__ = "email_delivery_statuses"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    message_id = Column(String(255), nullable=False, index=True)
    recipient = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<EmailDeliveryStatus(id={self.id}, message_id='{self.message_id}', status='{self.status}')>"


class UserSettings(Base):
    """User settings model for storing user preferences and configuration."""

    __tablename__ = "user_settings"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # AI Model Preferences
    ai_model_preference = Column(String(100), nullable=False, default="gpt-3.5-turbo")
    analysis_depth = Column(String(50), nullable=False, default="normal")
    
    # Notification Preferences
    email_notifications_enabled = Column(Boolean, nullable=False, default=True)
    slack_notifications_enabled = Column(Boolean, nullable=False, default=True)
    docusign_notifications_enabled = Column(Boolean, nullable=False, default=True)
    
    # Risk Assessment Preferences
    risk_threshold_low = Column(DECIMAL(3, 2), nullable=False, default=0.30)
    risk_threshold_medium = Column(DECIMAL(3, 2), nullable=False, default=0.60)
    risk_threshold_high = Column(DECIMAL(3, 2), nullable=False, default=0.80)
    
    # Analysis Preferences
    auto_generate_redlines = Column(Boolean, nullable=False, default=True)
    auto_generate_email_drafts = Column(Boolean, nullable=False, default=True)
    
    # UI/UX Preferences
    preferred_language = Column(String(10), nullable=False, default="en")
    timezone = Column(String(50), nullable=False, default="UTC")
    theme_preference = Column(String(20), nullable=False, default="light")
    dashboard_layout = Column(JSONB_COMPAT(), nullable=True)
    
    # Integration Settings
    integration_settings = Column(JSONB_COMPAT(), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="settings")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_settings_user_id", "user_id"),
        Index("idx_user_settings_ai_model", "ai_model_preference"),
    )
    
    def __repr__(self):
        return f"<UserSettings(id={self.id}, user_id={self.user_id}, ai_model='{self.ai_model_preference}')>"


class ContractEmbedding(Base):
    """Contract embedding model for storing vector embeddings metadata."""

    __tablename__ = "contract_embeddings"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    contract_analysis_id = Column(UUID(), ForeignKey("contract_analyses.id", ondelete="CASCADE"), nullable=False)
    embedding_id = Column(String(255), nullable=False, unique=True, index=True)  # ChromaDB embedding ID
    
    # Chunk information
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_size = Column(Integer, nullable=False)
    total_chunks = Column(Integer, nullable=False)
    
    # Embedding metadata
    embedding_model = Column(String(100), nullable=False, default="text-embedding-ada-002")
    processing_time_ms = Column(DECIMAL(10, 3), nullable=True)
    
    # Contract metadata for search optimization
    contract_type = Column(String(100), nullable=True, index=True)
    risk_level = Column(String(50), nullable=True, index=True)
    jurisdiction = Column(String(100), nullable=True, index=True)
    contract_category = Column(String(100), nullable=True, index=True)
    
    # Legal context
    parties = Column(ARRAY(String), default=[], nullable=True)
    key_terms = Column(ARRAY(String), default=[], nullable=True)
    
    # Additional metadata
    additional_metadata = Column(JSONB_COMPAT(), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    contract_analysis = relationship("ContractAnalysis")
    
    # Indexes
    __table_args__ = (
        Index("idx_contract_embeddings_analysis_id", "contract_analysis_id"),
        Index("idx_contract_embeddings_embedding_id", "embedding_id"),
        Index("idx_contract_embeddings_contract_type", "contract_type"),
        Index("idx_contract_embeddings_risk_level", "risk_level"),
        Index("idx_contract_embeddings_jurisdiction", "jurisdiction"),
        Index("idx_contract_embeddings_category", "contract_category"),
        Index("idx_contract_embeddings_chunk_index", "chunk_index"),
        Index("idx_contract_embeddings_created_at", "created_at"),
    )
    
    def __repr__(self):
        return f"<ContractEmbedding(id={self.id}, embedding_id='{self.embedding_id}', chunk_index={self.chunk_index})>"


class LegalPrecedent(Base):
    """Legal precedent model for storing case law and legal references."""

    __tablename__ = "legal_precedents"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    
    # Case information
    case_name = Column(String(500), nullable=False, index=True)
    case_number = Column(String(100), nullable=True, index=True)
    court = Column(String(200), nullable=True, index=True)
    jurisdiction = Column(String(100), nullable=False, index=True)
    
    # Case details
    decision_date = Column(DateTime(timezone=True), nullable=True, index=True)
    case_summary = Column(Text, nullable=True)
    legal_principles = Column(ARRAY(String), default=[], nullable=True)
    key_holdings = Column(ARRAY(String), default=[], nullable=True)
    
    # Citation information
    citation = Column(String(200), nullable=True, index=True)
    reporter = Column(String(100), nullable=True)
    volume = Column(String(50), nullable=True)
    page = Column(String(50), nullable=True)
    
    # Content
    full_text = Column(Text, nullable=True)
    relevant_excerpts = Column(ARRAY(String), default=[], nullable=True)
    
    # Categorization
    practice_areas = Column(ARRAY(String), default=[], nullable=True, index=True)
    legal_topics = Column(ARRAY(String), default=[], nullable=True)
    contract_types = Column(ARRAY(String), default=[], nullable=True)
    
    # Relevance and quality
    relevance_score = Column(DECIMAL(3, 2), nullable=True)  # 0.00-1.00
    authority_level = Column(String(50), nullable=True)  # supreme_court, appellate, trial, etc.
    
    # Source information
    source_url = Column(String(500), nullable=True)
    source_database = Column(String(100), nullable=True)
    last_verified = Column(DateTime(timezone=True), nullable=True)
    
    # Embedding information
    embedding_id = Column(String(255), nullable=True, unique=True, index=True)  # ChromaDB embedding ID
    embedding_model = Column(String(100), nullable=True)
    
    # Additional metadata
    additional_metadata = Column(JSONB_COMPAT(), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index("idx_legal_precedents_case_name", "case_name"),
        Index("idx_legal_precedents_jurisdiction", "jurisdiction"),
        Index("idx_legal_precedents_court", "court"),
        Index("idx_legal_precedents_decision_date", "decision_date"),
        Index("idx_legal_precedents_citation", "citation"),
        Index("idx_legal_precedents_practice_areas", "practice_areas"),
        Index("idx_legal_precedents_authority_level", "authority_level"),
        Index("idx_legal_precedents_relevance_score", "relevance_score"),
        Index("idx_legal_precedents_embedding_id", "embedding_id"),
        Index("idx_legal_precedents_created_at", "created_at"),
    )
    
    def __repr__(self):
        return f"<LegalPrecedent(id={self.id}, case_name='{self.case_name}', jurisdiction='{self.jurisdiction}')>"


class SimilaritySearchLog(Base):
    """Log model for tracking similarity searches for analytics and optimization."""

    __tablename__ = "similarity_search_logs"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Search parameters
    query_text = Column(Text, nullable=False)
    search_type = Column(String(50), nullable=False, index=True)  # contract, precedent, etc.
    similarity_threshold = Column(DECIMAL(3, 2), nullable=False)
    max_results = Column(Integer, nullable=False)
    
    # Filters applied
    metadata_filters = Column(JSONB_COMPAT(), nullable=True)
    contract_types = Column(ARRAY(String), default=[], nullable=True)
    risk_levels = Column(ARRAY(String), default=[], nullable=True)
    jurisdictions = Column(ARRAY(String), default=[], nullable=True)
    
    # Results
    results_count = Column(Integer, nullable=False)
    top_similarity_score = Column(DECIMAL(3, 2), nullable=True)
    
    # Performance metrics
    search_time_ms = Column(DECIMAL(10, 3), nullable=False)
    embedding_time_ms = Column(DECIMAL(10, 3), nullable=True)
    
    # Context
    session_id = Column(String(255), nullable=True)
    request_id = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index("idx_similarity_search_logs_user_id", "user_id"),
        Index("idx_similarity_search_logs_search_type", "search_type"),
        Index("idx_similarity_search_logs_created_at", "created_at"),
        Index("idx_similarity_search_logs_search_time", "search_time_ms"),
        Index("idx_similarity_search_logs_results_count", "results_count"),
    )
    
    def __repr__(self):
        return f"<SimilaritySearchLog(id={self.id}, search_type='{self.search_type}', results_count={self.results_count})>"


class AnalysisHistory(Base):
    """Analysis history model for audit trail and tracking analysis results over time."""

    __tablename__ = "analysis_history"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(), ForeignKey("contract_analyses.id", ondelete="CASCADE"), nullable=False)
    analysis_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    risk_score = Column(DECIMAL(3, 2), nullable=True)
    processing_time = Column(DECIMAL(10, 3), nullable=True)
    
    # Results and metadata
    risk_level = Column(String(20), nullable=True, index=True)
    risky_clauses_count = Column(Integer, nullable=True, default=0)
    recommendations_count = Column(Integer, nullable=True, default=0)
    model_used = Column(String(100), nullable=True, index=True)
    total_tokens = Column(Integer, nullable=True)
    total_cost = Column(DECIMAL(10, 4), nullable=True)
    
    # Agent tracking
    completed_agents = Column(ARRAY(String), default=[], nullable=True)
    failed_agents = Column(ARRAY(String), default=[], nullable=True)
    agent_count = Column(Integer, nullable=True, default=0)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    fallback_used = Column(Boolean, nullable=False, default=False)
    
    # Additional metadata
    analysis_metadata = Column(JSONB_COMPAT(), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Soft delete for audit trail
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    contract_analysis = relationship("ContractAnalysis")
    agent_executions = relationship("AgentExecution", back_populates="analysis_history", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_analysis_history_contract_id", "contract_id"),
        Index("idx_analysis_history_analysis_type", "analysis_type"),
        Index("idx_analysis_history_status", "status"),
        Index("idx_analysis_history_risk_score", "risk_score"),
        Index("idx_analysis_history_risk_level", "risk_level"),
        Index("idx_analysis_history_model_used", "model_used"),
        Index("idx_analysis_history_created_at", "created_at"),
        Index("idx_analysis_history_completed_at", "completed_at"),
        Index("idx_analysis_history_processing_time", "processing_time"),
        Index("idx_analysis_history_total_cost", "total_cost"),
        Index("idx_analysis_history_deleted_at", "deleted_at"),
        # Composite indexes for common queries
        Index("idx_analysis_history_contract_status", "contract_id", "status"),
        Index("idx_analysis_history_type_created", "analysis_type", "created_at"),
        Index("idx_analysis_history_status_created", "status", "created_at"),
    )
    
    def __repr__(self):
        return f"<AnalysisHistory(id={self.id}, contract_id={self.contract_id}, status='{self.status}')>"


class AgentExecution(Base):
    """Agent execution model for performance tracking and monitoring."""

    __tablename__ = "agent_executions"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(), ForeignKey("analysis_history.id", ondelete="CASCADE"), nullable=False)
    agent_name = Column(String(50), nullable=False, index=True)
    agent_type = Column(String(50), nullable=True, index=True)
    status = Column(String(20), nullable=False, index=True)
    
    # Performance metrics
    execution_time = Column(DECIMAL(10, 3), nullable=True)
    token_usage = Column(Integer, nullable=True)
    cost = Column(DECIMAL(10, 4), nullable=True)
    
    # LLM provider information
    llm_provider = Column(String(50), nullable=True, index=True)
    model_name = Column(String(100), nullable=True, index=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    
    # Error handling and retry information
    retry_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    error_type = Column(String(100), nullable=True, index=True)
    fallback_used = Column(Boolean, nullable=False, default=False)
    fallback_provider = Column(String(50), nullable=True)
    
    # Circuit breaker information
    circuit_breaker_triggered = Column(Boolean, nullable=False, default=False)
    circuit_breaker_state = Column(String(20), nullable=True)
    
    # Request correlation
    correlation_id = Column(String(255), nullable=True, index=True)
    request_id = Column(String(255), nullable=True)
    session_id = Column(String(255), nullable=True)
    
    # Result information
    result_size_bytes = Column(Integer, nullable=True)
    result_quality_score = Column(DECIMAL(3, 2), nullable=True)
    
    # Additional metadata
    execution_metadata = Column(JSONB_COMPAT(), nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    analysis_history = relationship("AnalysisHistory", back_populates="agent_executions")
    
    # Indexes
    __table_args__ = (
        Index("idx_agent_executions_analysis_id", "analysis_id"),
        Index("idx_agent_executions_agent_name", "agent_name"),
        Index("idx_agent_executions_agent_type", "agent_type"),
        Index("idx_agent_executions_status", "status"),
        Index("idx_agent_executions_llm_provider", "llm_provider"),
        Index("idx_agent_executions_model_name", "model_name"),
        Index("idx_agent_executions_execution_time", "execution_time"),
        Index("idx_agent_executions_token_usage", "token_usage"),
        Index("idx_agent_executions_cost", "cost"),
        Index("idx_agent_executions_error_type", "error_type"),
        Index("idx_agent_executions_correlation_id", "correlation_id"),
        Index("idx_agent_executions_started_at", "started_at"),
        Index("idx_agent_executions_completed_at", "completed_at"),
        Index("idx_agent_executions_created_at", "created_at"),
        # Composite indexes for performance analysis
        Index("idx_agent_executions_analysis_agent", "analysis_id", "agent_name"),
        Index("idx_agent_executions_agent_status", "agent_name", "status"),
        Index("idx_agent_executions_provider_model", "llm_provider", "model_name"),
        Index("idx_agent_executions_status_started", "status", "started_at"),
        Index("idx_agent_executions_agent_time", "agent_name", "execution_time"),
        Index("idx_agent_executions_provider_cost", "llm_provider", "cost"),
        # Performance monitoring indexes
        Index("idx_agent_executions_perf_monitoring", "agent_name", "status", "started_at", "execution_time"),
        Index("idx_agent_executions_cost_analysis", "llm_provider", "model_name", "cost", "token_usage"),
        Index("idx_agent_executions_error_analysis", "error_type", "agent_name", "retry_count", "started_at"),
    )
    
    def __repr__(self):
        return f"<AgentExecution(id={self.id}, agent_name='{self.agent_name}', status='{self.status}')>"