"""
Database and API models package.
"""

# Database models
from .database_models import (
    User,
    APIKey,
    ContractAnalysis,
    AuditLog,
    Base,
)

# API models
from .api_models import (
    # User models
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    UserLoginResponse,
    PasswordChange,
    
    # API Key models
    APIKeyCreate,
    APIKeyResponse,
    APIKeyCreateResponse,
    
    # Contract analysis models
    RiskyClause,
    RedlineSuggestion,
    AnalysisResponse,
    ProgressUpdate,
    AnalysisStatusResponse,
    AsyncAnalysisRequest,
    AsyncAnalysisResponse,
    ContractAnalysisCreate,
    ContractAnalysisResponse,
    ContractAnalysisListResponse,
    
    # Audit models
    AuditLogResponse,
    AuditLogListResponse,
    
    # Statistics models
    UserStatistics,
    AnalysisStatistics,
    AuditStatistics,
    
    # Pagination and search models
    PaginationParams,
    UserSearchParams,
    AnalysisSearchParams,
    AuditSearchParams,
    
    # Standard response models
    ErrorResponse,
    SuccessResponse,
    HealthResponse,
)

# Validation models
from .validation_models import (
    # Base classes
    BaseRequestModel,
    FileContentValidator,
    ValidationError,
    
    # Enums
    FileType,
    Priority,
    AnalysisDepth,
    RiskLevel,
    NotificationType,
    
    # File upload models
    FileUploadRequest,
    ChunkedUploadInitiateRequest,
    ChunkUploadRequest,
    
    # Analysis models
    ContractAnalysisRequest,
    BulkAnalysisRequest,
    
    # User management models
    UserRegistrationRequest,
    UserLoginRequest,
    PasswordChangeRequest,
    
    # Notification models
    EmailNotificationRequest,
    SlackNotificationRequest,
    
    # Search models
    SearchRequest,
    
    # Configuration models
    SystemConfigurationRequest,
    WebhookRequest,
)

# Model converters
from .converters import (
    ModelConverter,
    user_to_dict,
    contract_analysis_to_dict,
    audit_log_to_dict,
    validate_uuid,
    validate_pagination_params,
    calculate_pagination_info,
)

__all__ = [
    # Database models
    "User",
    "APIKey", 
    "ContractAnalysis",
    "AuditLog",
    "Base",
    
    # User API models
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "UserLoginResponse",
    "PasswordChange",
    
    # API Key models
    "APIKeyCreate",
    "APIKeyResponse",
    "APIKeyCreateResponse",
    
    # Contract analysis models
    "RiskyClause",
    "RedlineSuggestion",
    "AnalysisResponse",
    "ProgressUpdate",
    "AnalysisStatusResponse",
    "AsyncAnalysisRequest",
    "AsyncAnalysisResponse",
    "ContractAnalysisCreate",
    "ContractAnalysisResponse",
    "ContractAnalysisListResponse",
    
    # Audit models
    "AuditLogResponse",
    "AuditLogListResponse",
    
    # Statistics models
    "UserStatistics",
    "AnalysisStatistics",
    "AuditStatistics",
    
    # Pagination and search models
    "PaginationParams",
    "UserSearchParams",
    "AnalysisSearchParams",
    "AuditSearchParams",
    
    # Standard response models
    "ErrorResponse",
    "SuccessResponse",
    "HealthResponse",
    
    # Validation models
    "BaseRequestModel",
    "FileContentValidator",
    "ValidationError",
    "FileType",
    "Priority",
    "AnalysisDepth",
    "RiskLevel",
    "NotificationType",
    "FileUploadRequest",
    "ChunkedUploadInitiateRequest",
    "ChunkUploadRequest",
    "ContractAnalysisRequest",
    "BulkAnalysisRequest",
    "UserRegistrationRequest",
    "UserLoginRequest",
    "PasswordChangeRequest",
    "EmailNotificationRequest",
    "SlackNotificationRequest",
    "SearchRequest",
    "SystemConfigurationRequest",
    "WebhookRequest",
    
    # Model converters
    "ModelConverter",
    "user_to_dict",
    "contract_analysis_to_dict",
    "audit_log_to_dict",
    "validate_uuid",
    "validate_pagination_params",
    "calculate_pagination_info",
]