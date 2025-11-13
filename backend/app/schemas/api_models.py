"""
Pydantic models for API requests and responses.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, EmailStr

class UserSettingsResponse(BaseModel):
    daily_application_goal: int
    preferred_industries: List[str]
    preferred_locations: List[str]
    experience_level: str

class UserSettingsUpdate(BaseModel):
    daily_application_goal: int
    preferred_industries: List[str]
    preferred_locations: List[str]
    experience_level: str

class UserProfileUpdate(BaseModel):
    username: str
    email: EmailStr

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class SuccessResponse(BaseModel):
    message: str
    data: Dict[str, Any]

class IntegrationSettingsResponse(BaseModel):
    integration_settings: Dict[str, Any]

class AIModelPreferenceResponse(BaseModel):
    ai_model_preference: str

class NotificationPreferencesResponse(BaseModel):
    notification_preferences: Dict[str, Any]

class RiskThresholdsResponse(BaseModel):
    risk_thresholds: Dict[str, Any]

class NotificationPreferences(BaseModel):
    email: bool
    push: bool
    sms: bool


class ErrorResponse(BaseModel):
    """Standardized error response model.

    Fields:
    - request_id: correlation/request id for tracing
    - timestamp: ISO timestamp of error
    - error_code: short error code string
    - detail: human readable detail
    - field_errors: optional dict of field -> messages
    - suggestions: optional list of suggestions for remediation
    """
    request_id: str
    timestamp: str
    error_code: str
    detail: Any
    field_errors: Dict[str, Any] | None = None
    suggestions: List[str] | None = None
