"""
Pydantic schemas for request/response validation
"""

from app.schemas.auth import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    Token,
    TokenData,
    RefreshToken,
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm
)

from app.schemas.job import (
    JobBase,
    JobCreate,
    JobUpdate,
    JobResponse,
    JobStatusUpdate,
    JobFilter,
    JobListResponse,
    JobStats
)

from app.schemas.document import (
    DocumentBase,
    DocumentCreate,
    DocumentUpdate,
    Document,
    DocumentWithVersions,
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentSearchFilters,
    DocumentUsageStats,
    DocumentAnalysis,
    DOCUMENT_TYPES,
    SUPPORTED_MIME_TYPES
)

from app.schemas.profile import (
    SkillBase,
    LocationPreference,
    CareerPreferences,
    CareerGoals,
    NotificationSettings,
    UIPreferences,
    UserProfileUpdate,
    UserSettingsUpdate,
    UserProfileResponse,
    ApplicationHistoryItem,
    ApplicationHistoryResponse,
    ProgressTrackingStats,
    DocumentSummary,
    DocumentManagementResponse
)

__all__ = [
    # Auth schemas
    "UserBase",
    "UserCreate", 
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "Token",
    "TokenData",
    "RefreshToken",
    "PasswordChange",
    "PasswordReset",
    "PasswordResetConfirm",
    # Job schemas
    "JobBase",
    "JobCreate",
    "JobUpdate",
    "JobResponse",
    "JobStatusUpdate",
    "JobFilter",
    "JobListResponse",
    "JobStats",
    # Document schemas
    "DocumentBase",
    "DocumentCreate",
    "DocumentUpdate",
    "Document",
    "DocumentWithVersions",
    "DocumentUploadResponse",
    "DocumentListResponse",
    "DocumentSearchFilters",
    "DocumentUsageStats",
    "DocumentAnalysis",
    "DOCUMENT_TYPES",
    "SUPPORTED_MIME_TYPES",
    # Profile schemas
    "SkillBase",
    "LocationPreference",
    "CareerPreferences",
    "CareerGoals",
    "NotificationSettings",
    "UIPreferences",
    "UserProfileUpdate",
    "UserSettingsUpdate",
    "UserProfileResponse",
    "ApplicationHistoryItem",
    "ApplicationHistoryResponse",
    "ProgressTrackingStats",
    "DocumentSummary",
    "DocumentManagementResponse"
]