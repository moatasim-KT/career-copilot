"""
API request and response models for job application tracking.
"""

import asyncio
from datetime import datetime
from typing import List, Optional, Any, Dict
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, EmailStr


class BaseResponse(BaseModel):
    """Base response model for all API responses."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    suggestions: Optional[List[str]] = Field(None, description="Suggested solutions")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class User(BaseModel):
	"""User model for API responses."""
	
	id: int
	username: str
	email: EmailStr
	is_active: bool = True
	created_at: datetime = Field(default_factory=datetime.utcnow)


class RiskyClause(BaseModel):
	"""Model for a risky clause identified in a contract."""

	clause_text: str = Field(..., description="The text of the risky clause")
	risk_explanation: str = Field(..., description="Explanation of why this clause is risky")
	risk_level: str = Field(..., description="Risk level: Low, Medium, or High")
	precedent_reference: Optional[str] = Field(None, description="Reference to relevant precedent")
	clause_index: int = Field(..., description="Index of the clause in the contract")

	@field_validator("risk_level")
	@classmethod
	def validate_risk_level(cls, v):
		if v not in ["Low", "Medium", "High"]:
			raise ValueError("Risk level must be Low, Medium, or High")
		return v


class RedlineSuggestion(BaseModel):
	"""Model for a suggested redline/alternative clause."""

	original_clause: str = Field(..., description="The original risky clause text")
	suggested_redline: str = Field(..., description="Suggested alternative language")
	risk_explanation: str = Field(..., description="Explanation of the risk being addressed")
	clause_index: int = Field(..., description="Index of the clause in the contract")
	change_rationale: str = Field("", description="Rationale for the suggested change")
	risk_mitigated: Optional[bool] = Field(None, description="Whether the risk is mitigated by the change")


class AnalysisResponse(BaseModel):
	"""Response model for job application tracking results."""

	model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

	risky_clauses: List[RiskyClause] = Field(default_factory=list, description="List of identified risky clauses")
	suggested_redlines: List[RedlineSuggestion] = Field(default_factory=list, description="List of suggested redlines")
	email_draft: str = Field("", description="Draft email for negotiation communication")
	processing_time: Optional[float] = Field(None, description="Time taken to process the contract in seconds")
	analysis_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the analysis was completed")
	status: str = Field(..., description="Analysis status")
	overall_risk_score: Optional[float] = Field(None, description="Overall risk score for the contract")
	warnings: List[str] = Field(default_factory=list, description="Processing warnings")
	errors: List[str] = Field(default_factory=list, description="Processing errors")


class ProgressUpdate(BaseModel):
	"""Model for progress updates during analysis."""

	node: str = Field(..., description="Current workflow node")
	progress_percentage: float = Field(..., description="Progress percentage (0-100)")
	message: str = Field(..., description="Progress message")
	timestamp: datetime = Field(default_factory=datetime.utcnow, description="Update timestamp")
	estimated_remaining_seconds: Optional[int] = Field(None, description="Estimated remaining time")


class AnalysisStatusResponse(BaseModel):
	"""Response model for analysis status checks."""

	model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

	status: str = Field(..., description="Current analysis status")
	current_node: str = Field(..., description="Current workflow node")
	execution_id: str = Field(..., description="Unique execution identifier")
	error_count: int = Field(0, description="Number of errors encountered")
	warnings: List[str] = Field(default_factory=list, description="Processing warnings")
	last_error: Optional[str] = Field(None, description="Last error message")
	start_time: Optional[datetime] = Field(None, description="Analysis start time")
	end_time: Optional[datetime] = Field(None, description="Analysis end time")
	processing_duration: Optional[float] = Field(None, description="Processing duration in seconds")
	risky_clauses_count: int = Field(0, description="Number of risky clauses found")
	redlines_count: int = Field(0, description="Number of redlines generated")
	overall_risk_score: Optional[float] = Field(None, description="Overall risk score")
	contract_filename: str = Field("unknown", description="Contract filename")
	progress_updates: List[ProgressUpdate] = Field(default_factory=list, description="Progress tracking updates")
	resource_usage: Optional[dict] = Field(None, description="Resource usage metrics")


class AsyncAnalysisRequest(BaseModel):
	"""Request model for asynchronous analysis with comprehensive validation."""

	timeout_seconds: Optional[int] = Field(
		300,
		description="Timeout for analysis in seconds",
		ge=30,  # Minimum 30 seconds
		le=3600,  # Maximum 1 hour
	)
	priority: Optional[str] = Field("normal", description="Analysis priority: low, normal, high")
	callback_url: Optional[str] = Field(None, description="URL to call when analysis is complete")
	enable_progress_tracking: bool = Field(True, description="Enable real-time progress tracking")

	@field_validator("priority")
	@classmethod
	def validate_priority(cls, v):
		if v not in ["low", "normal", "high"]:
			raise ValueError("Priority must be one of: low, normal, high")
		return v

	@field_validator("callback_url")
	@classmethod
	def validate_callback_url(cls, v):
		if v is not None:
			import re

			# Basic URL validation
			url_pattern = re.compile(
				r"^https?://"  # http:// or https://
				r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
				r"localhost|"  # localhost...
				r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
				r"(?::\d+)?"  # optional port
				r"(?:/?|[/?]\S+)$",
				re.IGNORECASE,
			)

			if not url_pattern.match(v):
				raise ValueError("Invalid callback URL format. Must be a valid HTTP/HTTPS URL")

			# Security check - don't allow localhost/private IPs in production
			if any(host in v.lower() for host in ["localhost", "127.0.0.1", "0.0.0.0"]):
				import os

				if os.getenv("ENVIRONMENT", "development") == "production":
					raise ValueError("Localhost URLs not allowed in production")

		return v

	@field_validator("timeout_seconds")
	@classmethod
	def validate_timeout(cls, v):
		if v is not None:
			if v < 30:
				raise ValueError("Timeout must be at least 30 seconds")
			if v > 3600:
				raise ValueError("Timeout cannot exceed 1 hour (3600 seconds)")
		return v


class AsyncAnalysisResponse(BaseModel):
	"""Response model for asynchronous analysis initiation."""

	model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

	task_id: str = Field(..., description="Unique task identifier")
	status: str = Field(..., description="Initial task status")
	estimated_completion_time: Optional[datetime] = Field(None, description="Estimated completion time")
	status_url: str = Field(..., description="URL to check task status")


# Task management for async processing
class AnalysisTask:
	"""Internal task management for asynchronous analysis."""

	def __init__(self, task_id: str, contract_text: str, contract_filename: str, timeout_seconds: int = 60):
		self.task_id = task_id
		self.contract_text = contract_text
		self.contract_filename = contract_filename
		self.timeout_seconds = timeout_seconds
		self.status = "pending"
		self.result = None
		self.error = None
		self.start_time = datetime.utcnow()
		self.end_time = None
		self.future: Optional[asyncio.Future] = None

	def to_status_response(self) -> AnalysisStatusResponse:
		"""Convert task to status response."""
		processing_duration = None
		if self.end_time:
			processing_duration = (self.end_time - self.start_time).total_seconds()

		return AnalysisStatusResponse(
			status=self.status,
			current_node="task_manager",
			execution_id=self.task_id,
			error_count=1 if self.error else 0,
			warnings=[],
			last_error=self.error,
			start_time=self.start_time,
			end_time=self.end_time,
			processing_duration=processing_duration,
			risky_clauses_count=len(self.result.get("risky_clauses", [])) if self.result else 0,
			redlines_count=len(self.result.get("suggested_redlines", [])) if self.result else 0,
			overall_risk_score=self.result.get("overall_risk_score") if self.result else None,
			contract_filename=self.contract_filename,
		)


class ErrorResponse(BaseModel):
	"""Standard error response model."""

	model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

	error_type: str = Field(..., description="Type of error that occurred")
	message: str = Field(..., description="Human-readable error message")
	details: Optional[dict] = Field(None, description="Additional error details")
	timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the error occurred")
	request_id: Optional[str] = Field(None, description="Unique request identifier for tracking")


class SuccessResponse(BaseModel):
	"""Standard success response model."""

	model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

	message: str = Field(..., description="Success message")
	data: Optional[dict] = Field(None, description="Response data")
	timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the response was generated")
	request_id: Optional[str] = Field(None, description="Unique request identifier for tracking")


class HealthResponse(BaseModel):
	"""Health check response model."""

	model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

	status: str = Field(..., description="Service status")
	timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
	version: str = Field(..., description="API version")
	dependencies: dict = Field(default_factory=dict, description="Status of external dependencies")


# User Management Models
class UserCreate(BaseModel):
	"""Model for creating a new user."""
	
	username: str = Field(..., min_length=3, max_length=50, description="Unique username")
	email: EmailStr = Field(..., description="User email address")
	password: str = Field(..., min_length=8, description="User password")
	is_superuser: bool = Field(False, description="Whether user has admin privileges")
	
	@field_validator("username")
	@classmethod
	def validate_username(cls, v):
		if not v.isalnum() and "_" not in v and "-" not in v:
			raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
		return v.lower()
	
	@field_validator("password")
	@classmethod
	def validate_password(cls, v):
		if len(v) < 8:
			raise ValueError("Password must be at least 8 characters long")
		if not any(c.isupper() for c in v):
			raise ValueError("Password must contain at least one uppercase letter")
		if not any(c.islower() for c in v):
			raise ValueError("Password must contain at least one lowercase letter")
		if not any(c.isdigit() for c in v):
			raise ValueError("Password must contain at least one digit")
		return v


class UserUpdate(BaseModel):
	"""Model for updating user information."""
	
	username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
	email: Optional[EmailStr] = Field(None, description="Email address")
	is_active: Optional[bool] = Field(None, description="Whether user is active")
	is_superuser: Optional[bool] = Field(None, description="Whether user has admin privileges")


class UserResponse(BaseModel):
	"""Response model for user information."""
	
	model_config = ConfigDict(from_attributes=True, json_encoders={datetime: lambda v: v.isoformat()})
	
	id: UUID = Field(..., description="User UUID")
	username: str = Field(..., description="Username")
	email: str = Field(..., description="Email address")
	is_active: bool = Field(..., description="Whether user is active")
	is_superuser: bool = Field(..., description="Whether user has admin privileges")
	created_at: datetime = Field(..., description="Account creation timestamp")
	updated_at: datetime = Field(..., description="Last update timestamp")


class UserLogin(BaseModel):
	"""Model for user login."""
	
	username_or_email: str = Field(..., description="Username or email address")
	password: str = Field(..., description="User password")


class UserLoginResponse(BaseModel):
	"""Response model for successful login."""
	
	model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
	
	access_token: str = Field(..., description="JWT access token")
	refresh_token: str = Field(..., description="JWT refresh token")
	token_type: str = Field("bearer", description="Token type")
	expires_in: int = Field(..., description="Token expiration time in seconds")
	user: UserResponse = Field(..., description="User information")


class PasswordChange(BaseModel):
	"""Model for password change."""
	
	current_password: str = Field(..., description="Current password")
	new_password: str = Field(..., min_length=8, description="New password")
	
	@field_validator("new_password")
	@classmethod
	def validate_new_password(cls, v):
		if len(v) < 8:
			raise ValueError("Password must be at least 8 characters long")
		if not any(c.isupper() for c in v):
			raise ValueError("Password must contain at least one uppercase letter")
		if not any(c.islower() for c in v):
			raise ValueError("Password must contain at least one lowercase letter")
		if not any(c.isdigit() for c in v):
			raise ValueError("Password must contain at least one digit")
		return v


# API Key Management Models
class APIKeyCreate(BaseModel):
	"""Model for creating an API key."""
	
	key_name: str = Field(..., min_length=1, max_length=100, description="Descriptive name for the API key")
	permissions: List[str] = Field(default_factory=list, description="List of permissions")
	expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="Expiration in days (optional)")


class APIKeyResponse(BaseModel):
	"""Response model for API key information."""
	
	model_config = ConfigDict(from_attributes=True, json_encoders={datetime: lambda v: v.isoformat()})
	
	id: UUID = Field(..., description="API key UUID")
	key_name: str = Field(..., description="API key name")
	permissions: List[str] = Field(..., description="List of permissions")
	is_active: bool = Field(..., description="Whether API key is active")
	last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
	expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
	created_at: datetime = Field(..., description="Creation timestamp")


class APIKeyCreateResponse(BaseModel):
	"""Response model for API key creation (includes the actual key)."""
	
	model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
	
	api_key: str = Field(..., description="The actual API key (only shown once)")
	key_info: APIKeyResponse = Field(..., description="API key information")


# Contract Analysis Models (Enhanced)
class ContractAnalysisCreate(BaseModel):
	"""Model for creating a job application tracking."""
	
	filename: str = Field(..., min_length=1, max_length=255, description="Contract filename")
	file_size: int = Field(..., gt=0, description="File size in bytes")
	analysis_options: Optional[dict] = Field(None, description="Analysis configuration options")


class ContractAnalysisResponse(BaseModel):
	"""Response model for job application tracking information."""
	
	model_config = ConfigDict(from_attributes=True, json_encoders={datetime: lambda v: v.isoformat()})
	
	id: UUID = Field(..., description="Analysis UUID")
	filename: str = Field(..., description="Contract filename")
	file_hash: str = Field(..., description="File hash")
	file_size: int = Field(..., description="File size in bytes")
	analysis_status: str = Field(..., description="Analysis status")
	risk_score: Optional[float] = Field(None, description="Overall risk score")
	risky_clauses: Optional[List[dict]] = Field(None, description="Risky clauses found")
	suggested_redlines: Optional[List[dict]] = Field(None, description="Redline suggestions")
	email_draft: Optional[str] = Field(None, description="Generated email draft")
	processing_time_seconds: Optional[float] = Field(None, description="Processing time")
	error_message: Optional[str] = Field(None, description="Error message if failed")
	ai_model_used: Optional[str] = Field(None, description="AI model used for analysis")
	created_at: datetime = Field(..., description="Creation timestamp")
	completed_at: Optional[datetime] = Field(None, description="Completion timestamp")


class ContractAnalysisListResponse(BaseModel):
	"""Response model for listing contract analyses."""
	
	analyses: List[ContractAnalysisResponse] = Field(..., description="List of analyses")
	total_count: int = Field(..., description="Total number of analyses")
	page: int = Field(..., description="Current page number")
	page_size: int = Field(..., description="Number of items per page")
	has_next: bool = Field(..., description="Whether there are more pages")


# Audit Log Models
class AuditLogResponse(BaseModel):
	"""Response model for audit log entries."""
	
	model_config = ConfigDict(from_attributes=True, json_encoders={datetime: lambda v: v.isoformat()})
	
	id: UUID = Field(..., description="Audit log UUID")
	event_type: str = Field(..., description="Type of event")
	event_data: Optional[dict] = Field(None, description="Additional event data")
	resource_type: Optional[str] = Field(None, description="Type of resource")
	resource_id: Optional[str] = Field(None, description="Resource identifier")
	action: Optional[str] = Field(None, description="Action performed")
	result: Optional[str] = Field(None, description="Result of action")
	ip_address: Optional[str] = Field(None, description="Client IP address")
	user_agent: Optional[str] = Field(None, description="Client user agent")
	session_id: Optional[str] = Field(None, description="Session identifier")
	request_id: Optional[str] = Field(None, description="Request correlation ID")
	created_at: datetime = Field(..., description="Event timestamp")


class AuditLogListResponse(BaseModel):
	"""Response model for listing audit logs."""
	
	logs: List[AuditLogResponse] = Field(..., description="List of audit logs")
	total_count: int = Field(..., description="Total number of logs")
	page: int = Field(..., description="Current page number")
	page_size: int = Field(..., description="Number of items per page")
	has_next: bool = Field(..., description="Whether there are more pages")


# Statistics and Analytics Models
class UserStatistics(BaseModel):
	"""Model for user statistics."""
	
	total_users: int = Field(..., description="Total number of users")
	active_users: int = Field(..., description="Number of active users")
	inactive_users: int = Field(..., description="Number of inactive users")
	superusers: int = Field(..., description="Number of superusers")


class AnalysisStatistics(BaseModel):
	"""Model for analysis statistics."""
	
	total_analyses: int = Field(..., description="Total number of analyses")
	completed_analyses: int = Field(..., description="Number of completed analyses")
	failed_analyses: int = Field(..., description="Number of failed analyses")
	pending_analyses: int = Field(..., description="Number of pending analyses")
	success_rate: float = Field(..., description="Success rate (0.0-1.0)")
	average_processing_time_seconds: float = Field(..., description="Average processing time")
	average_risk_score: float = Field(..., description="Average risk score")
	period_days: int = Field(..., description="Period covered by statistics")


class AuditStatistics(BaseModel):
	"""Model for audit statistics."""
	
	total_events: int = Field(..., description="Total number of events")
	events_by_type: dict = Field(..., description="Events grouped by type")
	events_by_result: dict = Field(..., description="Events grouped by result")
	unique_users: int = Field(..., description="Number of unique users")
	unique_ip_addresses: int = Field(..., description="Number of unique IP addresses")
	period_days: int = Field(..., description="Period covered by statistics")


# Pagination Models
class PaginationParams(BaseModel):
	"""Model for pagination parameters."""
	
	page: int = Field(1, ge=1, description="Page number (1-based)")
	page_size: int = Field(20, ge=1, le=100, description="Number of items per page")
	
	@property
	def offset(self) -> int:
		"""Calculate offset for database queries."""
		return (self.page - 1) * self.page_size


# Search and Filter Models
class UserSearchParams(BaseModel):
	"""Model for user search parameters."""
	
	search_term: Optional[str] = Field(None, description="Search term for username or email")
	is_active: Optional[bool] = Field(None, description="Filter by active status")
	is_superuser: Optional[bool] = Field(None, description="Filter by superuser status")


class AnalysisSearchParams(BaseModel):
	"""Model for analysis search parameters."""
	
	filename_pattern: Optional[str] = Field(None, description="Filename pattern to search for")
	status: Optional[str] = Field(None, description="Filter by analysis status")
	min_risk_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum risk score")
	max_risk_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Maximum risk score")
	date_from: Optional[datetime] = Field(None, description="Filter analyses created after this date")
	date_to: Optional[datetime] = Field(None, description="Filter analyses created before this date")


class AuditSearchParams(BaseModel):
	"""Model for audit log search parameters."""
	
	event_type: Optional[str] = Field(None, description="Filter by event type")
	resource_type: Optional[str] = Field(None, description="Filter by resource type")
	action: Optional[str] = Field(None, description="Filter by action")
	result: Optional[str] = Field(None, description="Filter by result")
	ip_address: Optional[str] = Field(None, description="Filter by IP address")
	date_from: Optional[datetime] = Field(None, description="Filter logs created after this date")
	date_to: Optional[datetime] = Field(None, description="Filter logs created before this date")

class UserSettings(BaseModel):
    """Model for user settings and preferences."""

    # AI Model Preferences
    ai_model_preference: str = Field("gpt-3.5-turbo", description="Preferred AI model for analysis")
    analysis_depth: str = Field("normal", description="Analysis depth: shallow, normal, deep")
    
    # Notification Preferences
    email_notifications_enabled: bool = Field(True, description="Enable email notifications")
    slack_notifications_enabled: bool = Field(True, description="Enable Slack notifications")
    docusign_notifications_enabled: bool = Field(True, description="Enable DocuSign notifications")
    
    # Risk Assessment Preferences
    risk_threshold_low: float = Field(0.30, ge=0.0, le=1.0, description="Low risk threshold (0.0-1.0)")
    risk_threshold_medium: float = Field(0.60, ge=0.0, le=1.0, description="Medium risk threshold (0.0-1.0)")
    risk_threshold_high: float = Field(0.80, ge=0.0, le=1.0, description="High risk threshold (0.0-1.0)")
    
    # Analysis Preferences
    auto_generate_redlines: bool = Field(True, description="Automatically generate redline suggestions")
    auto_generate_email_drafts: bool = Field(True, description="Automatically generate email drafts")
    
    # UI/UX Preferences
    preferred_language: str = Field("en", description="Preferred language code (e.g., en, es, fr)")
    timezone: str = Field("UTC", description="User timezone")
    theme_preference: str = Field("light", description="UI theme: light, dark, auto")
    dashboard_layout: Optional[dict] = Field(None, description="Custom dashboard layout configuration")
    
    # Integration Settings
    integration_settings: Optional[dict] = Field(None, description="Integration-specific settings")
    
    @field_validator("ai_model_preference")
    @classmethod
    def validate_ai_model(cls, v):
        allowed_models = [
            "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o",
            "claude-3-haiku", "claude-3-sonnet", "claude-3-opus",
            "claude-3-5-sonnet", "ollama-llama2", "ollama-mistral"
        ]
        if v not in allowed_models:
            raise ValueError(f"AI model must be one of: {', '.join(allowed_models)}")
        return v
    
    @field_validator("analysis_depth")
    @classmethod
    def validate_analysis_depth(cls, v):
        if v not in ["shallow", "normal", "deep"]:
            raise ValueError("Analysis depth must be: shallow, normal, or deep")
        return v
    
    @field_validator("theme_preference")
    @classmethod
    def validate_theme(cls, v):
        if v not in ["light", "dark", "auto"]:
            raise ValueError("Theme must be: light, dark, or auto")
        return v
    
    @field_validator("preferred_language")
    @classmethod
    def validate_language(cls, v):
        # Basic language code validation
        if len(v) < 2 or len(v) > 5:
            raise ValueError("Language code must be 2-5 characters")
        return v.lower()
    
    @field_validator("risk_threshold_medium")
    @classmethod
    def validate_medium_threshold(cls, v, info):
        if "risk_threshold_low" in info.data and v <= info.data["risk_threshold_low"]:
            raise ValueError("Medium risk threshold must be higher than low threshold")
        return v
    
    @field_validator("risk_threshold_high")
    @classmethod
    def validate_high_threshold(cls, v, info):
        if "risk_threshold_medium" in info.data and v <= info.data["risk_threshold_medium"]:
            raise ValueError("High risk threshold must be higher than medium threshold")
        return v


class UserSettingsResponse(BaseModel):
    """Response model for user settings."""
    
    model_config = ConfigDict(from_attributes=True, json_encoders={datetime: lambda v: v.isoformat()})
    
    id: UUID = Field(..., description="Settings UUID")
    user_id: UUID = Field(..., description="User UUID")
    
    # AI Model Preferences
    ai_model_preference: str = Field(..., description="Preferred AI model")
    analysis_depth: str = Field(..., description="Analysis depth setting")
    
    # Notification Preferences
    email_notifications_enabled: bool = Field(..., description="Email notifications enabled")
    slack_notifications_enabled: bool = Field(..., description="Slack notifications enabled")
    docusign_notifications_enabled: bool = Field(..., description="DocuSign notifications enabled")
    
    # Risk Assessment Preferences
    risk_threshold_low: float = Field(..., description="Low risk threshold")
    risk_threshold_medium: float = Field(..., description="Medium risk threshold")
    risk_threshold_high: float = Field(..., description="High risk threshold")
    
    # Analysis Preferences
    auto_generate_redlines: bool = Field(..., description="Auto-generate redlines")
    auto_generate_email_drafts: bool = Field(..., description="Auto-generate email drafts")
    
    # UI/UX Preferences
    preferred_language: str = Field(..., description="Preferred language")
    timezone: str = Field(..., description="User timezone")
    theme_preference: str = Field(..., description="UI theme preference")
    dashboard_layout: Optional[dict] = Field(None, description="Dashboard layout")
    
    # Integration Settings
    integration_settings: Optional[dict] = Field(None, description="Integration settings")
    
    created_at: datetime = Field(..., description="Settings creation timestamp")
    updated_at: datetime = Field(..., description="Settings last update timestamp")


class UserSettingsUpdate(BaseModel):
    """Model for updating user settings (all fields optional)."""
    
    # AI Model Preferences
    ai_model_preference: Optional[str] = Field(None, description="Preferred AI model")
    analysis_depth: Optional[str] = Field(None, description="Analysis depth")
    
    # Notification Preferences
    email_notifications_enabled: Optional[bool] = Field(None, description="Email notifications")
    slack_notifications_enabled: Optional[bool] = Field(None, description="Slack notifications")
    docusign_notifications_enabled: Optional[bool] = Field(None, description="DocuSign notifications")
    
    # Risk Assessment Preferences
    risk_threshold_low: Optional[float] = Field(None, ge=0.0, le=1.0, description="Low risk threshold")
    risk_threshold_medium: Optional[float] = Field(None, ge=0.0, le=1.0, description="Medium risk threshold")
    risk_threshold_high: Optional[float] = Field(None, ge=0.0, le=1.0, description="High risk threshold")
    
    # Analysis Preferences
    auto_generate_redlines: Optional[bool] = Field(None, description="Auto-generate redlines")
    auto_generate_email_drafts: Optional[bool] = Field(None, description="Auto-generate email drafts")
    
    # UI/UX Preferences
    preferred_language: Optional[str] = Field(None, description="Preferred language")
    timezone: Optional[str] = Field(None, description="User timezone")
    theme_preference: Optional[str] = Field(None, description="UI theme")
    dashboard_layout: Optional[dict] = Field(None, description="Dashboard layout")
    
    # Integration Settings
    integration_settings: Optional[dict] = Field(None, description="Integration settings")
    
    @field_validator("ai_model_preference")
    @classmethod
    def validate_ai_model(cls, v):
        if v is not None:
            allowed_models = [
                "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o",
                "claude-3-haiku", "claude-3-sonnet", "claude-3-opus",
                "claude-3-5-sonnet", "ollama-llama2", "ollama-mistral"
            ]
            if v not in allowed_models:
                raise ValueError(f"AI model must be one of: {', '.join(allowed_models)}")
        return v
    
    @field_validator("analysis_depth")
    @classmethod
    def validate_analysis_depth(cls, v):
        if v is not None and v not in ["shallow", "normal", "deep"]:
            raise ValueError("Analysis depth must be: shallow, normal, or deep")
        return v
    
    @field_validator("theme_preference")
    @classmethod
    def validate_theme(cls, v):
        if v is not None and v not in ["light", "dark", "auto"]:
            raise ValueError("Theme must be: light, dark, or auto")
        return v


class UserProfileUpdate(BaseModel):
    """Model for updating user profile information."""
    
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    email: Optional[EmailStr] = Field(None, description="Email address")
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if v is not None:
            if not v.replace("_", "").replace("-", "").isalnum():
                raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        return v.lower() if v else v


class EmailDeliveryStatus(BaseModel):
    """Model for email delivery status."""

    model_config = ConfigDict(from_attributes=True, json_encoders={datetime: lambda v: v.isoformat()})

    id: UUID = Field(..., description="Email delivery status UUID")
    message_id: str = Field(..., description="Email message ID")
    recipient: str = Field(..., description="Email recipient")
    status: str = Field(..., description="Delivery status")
    error_message: Optional[str] = Field(None, description="Error message if delivery failed")
    sent_at: datetime = Field(..., description="Timestamp when the email was sent")
    delivered_at: Optional[datetime] = Field(None, description="Timestamp when the email was delivered")
