"""
Frontend configuration management with environment-specific settings.
Consolidated configuration for all frontend components.
"""

import os
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Environment(Enum):
    """Supported environments."""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"
    STAGING = "staging"


@dataclass
class SecurityConfig:
    """Security configuration settings."""
    # File security settings
    max_file_size_mb: int = 50
    allowed_file_types: List[str] = None
    quarantine_suspicious_files: bool = True
    scan_file_content: bool = True
    
    # Input validation settings
    max_input_length: int = 10000
    enable_sql_injection_detection: bool = True
    enable_xss_detection: bool = True
    enable_command_injection_detection: bool = True
    enable_path_traversal_detection: bool = True
    
    # API security settings
    enable_rate_limiting: bool = True
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    require_api_key: bool = False
    enable_request_signing: bool = False
    
    # Session settings
    session_timeout_minutes: int = 60
    enable_csrf_protection: bool = True
    
    # Audit logging settings
    enable_audit_logging: bool = True
    log_level: str = "INFO"
    log_retention_days: int = 30
    log_sensitive_data: bool = False
    
    # Memory management settings
    max_memory_mb: int = 500
    cleanup_interval_seconds: int = 300
    temp_file_ttl_hours: int = 24
    enable_secure_deletion: bool = True
    
    # Encryption settings
    enable_encryption: bool = True
    encryption_key_file: str = "security/encryption.key"
    
    # Security headers
    enable_security_headers: bool = True
    content_security_policy: str = "default-src 'self'"
    x_frame_options: str = "DENY"
    x_content_type_options: str = "nosniff"
    x_xss_protection: str = "1; mode=block"
    
    def __post_init__(self):
        if self.allowed_file_types is None:
            self.allowed_file_types = ["pdf", "docx", "txt"]


@dataclass
class PerformanceConfig:
    """Performance optimization settings."""
    enable_compression: bool = True
    enable_minification: bool = True
    lazy_loading: bool = True
    image_optimization: bool = True
    chunk_size_mb: int = 10
    max_concurrent_requests: int = 5
    
    # Cache settings
    cache_ttl_seconds: int = 300
    cache_max_entries: int = 1000
    enable_file_cache: bool = True
    enable_api_cache: bool = True


@dataclass
class UIConfig:
    """UI configuration settings."""
    theme: str = "light"
    enable_dark_mode: bool = True
    mobile_breakpoint: int = 768
    tablet_breakpoint: int = 1024
    enable_animations: bool = True
    enable_haptic_feedback: bool = True
    
    # Display settings
    results_expander_expanded: bool = True
    error_display_duration: int = 5
    show_upload_progress: bool = True
    show_file_metadata: bool = True


@dataclass
class AnalyticsConfig:
    """Analytics configuration settings."""
    enable_user_tracking: bool = True
    enable_performance_tracking: bool = True
    enable_error_tracking: bool = True
    retention_days: int = 30
    batch_size: int = 100


@dataclass
class WebSocketConfig:
    """WebSocket configuration settings."""
    enable_real_time: bool = True
    polling_interval_seconds: int = 5
    connection_timeout_seconds: int = 30
    max_reconnect_attempts: int = 5
    heartbeat_interval_seconds: int = 30


class FrontendConfig:
    """Frontend configuration settings with environment awareness."""

    def __init__(self):
        # Environment Detection
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        self.DEVELOPMENT_MODE: bool = os.getenv("DEVELOPMENT_MODE", "true").lower() == "true"
        self.PRODUCTION_MODE: bool = os.getenv("PRODUCTION_MODE", "false").lower() == "true"

        # Backend API Configuration
        self.BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8002")
        self.API_TIMEOUT_SECONDS: int = int(os.getenv("API_TIMEOUT_SECONDS", "30"))
        self.API_RETRY_ATTEMPTS: int = int(os.getenv("API_RETRY_ATTEMPTS", "3"))

        # UI Configuration
        self.PAGE_TITLE: str = "Career Copilot"
        self.PAGE_ICON: str = "📄"
        self.LAYOUT: str = "wide"

        # File Upload Configuration
        self.MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
        self.ALLOWED_FILE_TYPES: List[str] = ["pdf", "docx", "txt"]
        self.MAX_FILES_PER_UPLOAD: int = int(os.getenv("MAX_FILES_PER_UPLOAD", "10"))
        self.ENABLE_FILE_PREVIEW: bool = os.getenv("ENABLE_FILE_PREVIEW", "true").lower() == "true"
        self.ENABLE_DRAG_DROP: bool = os.getenv("ENABLE_DRAG_DROP", "true").lower() == "true"
        self.ENABLE_REAL_TIME_VALIDATION: bool = os.getenv("ENABLE_REAL_TIME_VALIDATION", "true").lower() == "true"
        
        # Performance Configuration
        self.CHUNK_SIZE_KB: int = int(os.getenv("CHUNK_SIZE_KB", "1024"))
        self.MAX_PREVIEW_SIZE_KB: int = int(os.getenv("MAX_PREVIEW_SIZE_KB", "100"))

        # Feature Flags
        self.FEATURE_FLAGS: Dict[str, bool] = {
            "real_time_updates": os.getenv("FEATURE_REAL_TIME_UPDATES", "true").lower() == "true",
            "advanced_analytics": os.getenv("FEATURE_ADVANCED_ANALYTICS", "true").lower() == "true",
            "mobile_optimizations": os.getenv("FEATURE_MOBILE_OPTIMIZATIONS", "true").lower() == "true",
            "error_recovery": os.getenv("FEATURE_ERROR_RECOVERY", "true").lower() == "true",
            "performance_monitoring": os.getenv("FEATURE_PERFORMANCE_MONITORING", "true").lower() == "true",
            "user_feedback": os.getenv("FEATURE_USER_FEEDBACK", "true").lower() == "true",
            "dark_mode": os.getenv("FEATURE_DARK_MODE", "true").lower() == "true",
            "offline_mode": os.getenv("FEATURE_OFFLINE_MODE", "false").lower() == "true",
            "beta_features": os.getenv("FEATURE_BETA_FEATURES", "false").lower() == "true"
        }

        # Logging Configuration
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.ENABLE_FILE_LOGGING: bool = os.getenv("ENABLE_FILE_LOGGING", "true").lower() == "true"
        self.LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "logs/frontend.log")

        # Initialize sub-configurations
        self.security = self._load_security_config()
        self.performance = self._load_performance_config()
        self.ui = self._load_ui_config()
        self.analytics = self._load_analytics_config()
        self.websocket = self._load_websocket_config()

    def _load_security_config(self) -> SecurityConfig:
        """Load security configuration from environment variables."""
        return SecurityConfig(
            max_file_size_mb=int(os.getenv("SEC_MAX_FILE_SIZE_MB", str(self.MAX_FILE_SIZE_MB))),
            allowed_file_types=os.getenv("SEC_ALLOWED_FILE_TYPES", ",".join(self.ALLOWED_FILE_TYPES)).split(","),
            quarantine_suspicious_files=os.getenv("SEC_QUARANTINE_FILES", "true").lower() == "true",
            scan_file_content=os.getenv("SEC_SCAN_CONTENT", "true").lower() == "true",
            max_input_length=int(os.getenv("SEC_MAX_INPUT_LENGTH", "10000")),
            enable_sql_injection_detection=os.getenv("SEC_DETECT_SQL", "true").lower() == "true",
            enable_xss_detection=os.getenv("SEC_DETECT_XSS", "true").lower() == "true",
            enable_command_injection_detection=os.getenv("SEC_DETECT_CMD", "true").lower() == "true",
            enable_path_traversal_detection=os.getenv("SEC_DETECT_PATH", "true").lower() == "true",
            enable_rate_limiting=os.getenv("SEC_RATE_LIMITING", "true").lower() == "true",
            max_requests_per_minute=int(os.getenv("SEC_RATE_LIMIT_MINUTE", "60")),
            max_requests_per_hour=int(os.getenv("SEC_RATE_LIMIT_HOUR", "1000")),
            require_api_key=os.getenv("SEC_REQUIRE_API_KEY", "false").lower() == "true",
            enable_request_signing=os.getenv("SEC_REQUEST_SIGNING", "false").lower() == "true",
            session_timeout_minutes=int(os.getenv("SESSION_TIMEOUT_MINUTES", "60")),
            enable_csrf_protection=os.getenv("SEC_CSRF_PROTECTION", "true").lower() == "true",
            enable_audit_logging=os.getenv("SEC_AUDIT_LOGGING", "true").lower() == "true",
            log_level=os.getenv("SEC_LOG_LEVEL", self.LOG_LEVEL),
            log_retention_days=int(os.getenv("SEC_LOG_RETENTION_DAYS", "30")),
            log_sensitive_data=os.getenv("SEC_LOG_SENSITIVE", "false").lower() == "true",
            max_memory_mb=int(os.getenv("SEC_MAX_MEMORY_MB", "500")),
            cleanup_interval_seconds=int(os.getenv("SEC_CLEANUP_INTERVAL", "300")),
            temp_file_ttl_hours=int(os.getenv("SEC_TEMP_FILE_TTL", "24")),
            enable_secure_deletion=os.getenv("SEC_SECURE_DELETION", "true").lower() == "true",
            enable_encryption=os.getenv("SEC_ENCRYPTION", "true").lower() == "true",
            encryption_key_file=os.getenv("SEC_ENCRYPTION_KEY_FILE", "./secrets/encryption.key"),
            enable_security_headers=os.getenv("SEC_HEADERS", "true").lower() == "true",
            content_security_policy=os.getenv("SEC_CSP", "default-src 'self'"),
            x_frame_options=os.getenv("SEC_X_FRAME_OPTIONS", "DENY"),
            x_content_type_options=os.getenv("SEC_X_CONTENT_TYPE_OPTIONS", "nosniff"),
            x_xss_protection=os.getenv("SEC_X_XSS_PROTECTION", "1; mode=block")
        )

    def _load_performance_config(self) -> PerformanceConfig:
        """Load performance configuration from environment variables."""
        return PerformanceConfig(
            enable_compression=os.getenv("PERF_COMPRESSION", "true").lower() == "true",
            enable_minification=os.getenv("PERF_MINIFICATION", "true").lower() == "true",
            lazy_loading=os.getenv("PERF_LAZY_LOADING", "true").lower() == "true",
            image_optimization=os.getenv("PERF_IMAGE_OPTIMIZATION", "true").lower() == "true",
            chunk_size_mb=int(os.getenv("PERF_CHUNK_SIZE_MB", "10")),
            max_concurrent_requests=int(os.getenv("MAX_CONCURRENT_REQUESTS", "5")),
            cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "300")),
            cache_max_entries=int(os.getenv("CACHE_MAX_ENTRIES", "1000")),
            enable_file_cache=os.getenv("CACHE_ENABLE_FILE", "true").lower() == "true",
            enable_api_cache=os.getenv("CACHE_ENABLE_API", "true").lower() == "true"
        )

    def _load_ui_config(self) -> UIConfig:
        """Load UI configuration from environment variables."""
        return UIConfig(
            theme=os.getenv("UI_THEME", "light"),
            enable_dark_mode=os.getenv("UI_DARK_MODE", "true").lower() == "true",
            mobile_breakpoint=int(os.getenv("UI_MOBILE_BREAKPOINT", "768")),
            tablet_breakpoint=int(os.getenv("UI_TABLET_BREAKPOINT", "1024")),
            enable_animations=os.getenv("UI_ANIMATIONS", "true").lower() == "true",
            enable_haptic_feedback=os.getenv("UI_HAPTIC_FEEDBACK", "true").lower() == "true",
            results_expander_expanded=os.getenv("UI_RESULTS_EXPANDED", "true").lower() == "true",
            error_display_duration=int(os.getenv("UI_ERROR_DURATION", "5")),
            show_upload_progress=os.getenv("UI_SHOW_UPLOAD_PROGRESS", "true").lower() == "true",
            show_file_metadata=os.getenv("UI_SHOW_FILE_METADATA", "true").lower() == "true"
        )

    def _load_analytics_config(self) -> AnalyticsConfig:
        """Load analytics configuration from environment variables."""
        return AnalyticsConfig(
            enable_user_tracking=os.getenv("ANALYTICS_USER_TRACKING", "true").lower() == "true",
            enable_performance_tracking=os.getenv("ANALYTICS_PERFORMANCE_TRACKING", "true").lower() == "true",
            enable_error_tracking=os.getenv("ANALYTICS_ERROR_TRACKING", "true").lower() == "true",
            retention_days=int(os.getenv("ANALYTICS_RETENTION_DAYS", "30")),
            batch_size=int(os.getenv("ANALYTICS_BATCH_SIZE", "100"))
        )

    def _load_websocket_config(self) -> WebSocketConfig:
        """Load WebSocket configuration from environment variables."""
        return WebSocketConfig(
            enable_real_time=os.getenv("WS_ENABLE_REAL_TIME", "true").lower() == "true",
            polling_interval_seconds=int(os.getenv("WS_POLLING_INTERVAL", "5")),
            connection_timeout_seconds=int(os.getenv("WS_CONNECTION_TIMEOUT", "30")),
            max_reconnect_attempts=int(os.getenv("WS_MAX_RECONNECT_ATTEMPTS", "5")),
            heartbeat_interval_seconds=int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))
        )

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == "development" or self.DEVELOPMENT_MODE

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == "production" or self.PRODUCTION_MODE

    def is_staging(self) -> bool:
        """Check if running in staging mode."""
        return self.ENVIRONMENT == "staging"

    def get_environment_specific_config(self) -> Dict[str, Any]:
        """Get environment-specific configuration."""
        if self.is_production():
            return {
                "debug": False,
                "show_debug_info": False,
                "enable_file_preview": False,
                "max_file_size_mb": 25,
                "session_timeout": 30 * 60,  # 30 minutes
                "enable_analytics": True
            }
        elif self.is_development():
            return {
                "debug": True,
                "show_debug_info": True,
                "enable_file_preview": True,
                "max_file_size_mb": 50,
                "session_timeout": 60 * 60,  # 1 hour
                "enable_analytics": False
            }
        elif self.is_staging():
            return {
                "debug": False,
                "show_debug_info": True,
                "enable_file_preview": True,
                "max_file_size_mb": 35,
                "session_timeout": 45 * 60,  # 45 minutes
                "enable_analytics": True
            }
        else:  # testing
            return {
                "debug": False,
                "show_debug_info": False,
                "enable_file_preview": False,
                "max_file_size_mb": 10,
                "session_timeout": 5 * 60,  # 5 minutes
                "enable_analytics": False
            }

    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers based on configuration."""
        if not self.security.enable_security_headers:
            return {}

        headers = {
            "X-Frame-Options": self.security.x_frame_options,
            "X-Content-Type-Options": self.security.x_content_type_options,
            "X-XSS-Protection": self.security.x_xss_protection,
            "Content-Security-Policy": self.security.content_security_policy,
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        }

        return headers

    def validate_security_config(self) -> List[str]:
        """Validate security configuration for potential issues."""
        issues = []

        # Check for insecure defaults
        if self.security.max_file_size_mb > 100:
            issues.append("File size limit is very high, consider reducing for security")

        if "*" in self.security.allowed_file_types:
            issues.append("Wildcard file types allowed, consider restricting to specific types")

        if not self.security.quarantine_suspicious_files:
            issues.append("File quarantine is disabled, suspicious files will not be isolated")

        if not self.security.scan_file_content:
            issues.append("File content scanning is disabled, malicious content may not be detected")

        if self.security.max_input_length > 50000:
            issues.append("Input length limit is very high, consider reducing to prevent DoS")

        if not self.security.enable_rate_limiting:
            issues.append("Rate limiting is disabled, API may be vulnerable to DoS attacks")

        if self.security.max_requests_per_minute > 1000:
            issues.append("Rate limit is very high, consider reducing to prevent abuse")

        if not self.security.enable_audit_logging:
            issues.append("Audit logging is disabled, security monitoring will be limited")

        if self.security.log_retention_days < 7:
            issues.append("Log retention period is very short, consider increasing for compliance")

        if self.security.max_memory_mb > 2000:
            issues.append("Memory limit is very high, consider reducing to prevent resource exhaustion")

        if not self.security.enable_secure_deletion:
            issues.append("Secure deletion is disabled, sensitive data may persist on disk")

        if not self.security.enable_encryption:
            issues.append("Encryption is disabled, sensitive data may be stored in plain text")

        if not self.security.enable_security_headers:
            issues.append("Security headers are disabled, browser security features will not be enforced")

        return issues

    def create_security_directories(self):
        """Create necessary security directories."""
        directories = ["./secrets", "logs/audit", "data/temp/secure", "data/quarantine"]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            # Set restrictive permissions
            os.chmod(directory, 0o700)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "environment": self.ENVIRONMENT,
            "development_mode": self.DEVELOPMENT_MODE,
            "production_mode": self.PRODUCTION_MODE,
            "backend_url": self.BACKEND_URL,
            "api_timeout_seconds": self.API_TIMEOUT_SECONDS,
            "api_retry_attempts": self.API_RETRY_ATTEMPTS,
            "page_title": self.PAGE_TITLE,
            "page_icon": self.PAGE_ICON,
            "layout": self.LAYOUT,
            "max_file_size_mb": self.MAX_FILE_SIZE_MB,
            "allowed_file_types": self.ALLOWED_FILE_TYPES,
            "max_files_per_upload": self.MAX_FILES_PER_UPLOAD,
            "enable_file_preview": self.ENABLE_FILE_PREVIEW,
            "enable_drag_drop": self.ENABLE_DRAG_DROP,
            "enable_real_time_validation": self.ENABLE_REAL_TIME_VALIDATION,
            "chunk_size_kb": self.CHUNK_SIZE_KB,
            "max_preview_size_kb": self.MAX_PREVIEW_SIZE_KB,
            "feature_flags": self.FEATURE_FLAGS,
            "log_level": self.LOG_LEVEL,
            "enable_file_logging": self.ENABLE_FILE_LOGGING,
            "log_file_path": self.LOG_FILE_PATH,
            "security": {
                "max_file_size_mb": self.security.max_file_size_mb,
                "allowed_file_types": self.security.allowed_file_types,
                "quarantine_suspicious_files": self.security.quarantine_suspicious_files,
                "scan_file_content": self.security.scan_file_content,
                "max_input_length": self.security.max_input_length,
                "enable_sql_injection_detection": self.security.enable_sql_injection_detection,
                "enable_xss_detection": self.security.enable_xss_detection,
                "enable_command_injection_detection": self.security.enable_command_injection_detection,
                "enable_path_traversal_detection": self.security.enable_path_traversal_detection,
                "enable_rate_limiting": self.security.enable_rate_limiting,
                "max_requests_per_minute": self.security.max_requests_per_minute,
                "max_requests_per_hour": self.security.max_requests_per_hour,
                "require_api_key": self.security.require_api_key,
                "enable_request_signing": self.security.enable_request_signing,
                "session_timeout_minutes": self.security.session_timeout_minutes,
                "enable_csrf_protection": self.security.enable_csrf_protection,
                "enable_audit_logging": self.security.enable_audit_logging,
                "log_level": self.security.log_level,
                "log_retention_days": self.security.log_retention_days,
                "log_sensitive_data": self.security.log_sensitive_data,
                "max_memory_mb": self.security.max_memory_mb,
                "cleanup_interval_seconds": self.security.cleanup_interval_seconds,
                "temp_file_ttl_hours": self.security.temp_file_ttl_hours,
                "enable_secure_deletion": self.security.enable_secure_deletion,
                "enable_encryption": self.security.enable_encryption,
                "encryption_key_file": self.security.encryption_key_file,
                "enable_security_headers": self.security.enable_security_headers,
                "content_security_policy": self.security.content_security_policy,
                "x_frame_options": self.security.x_frame_options,
                "x_content_type_options": self.security.x_content_type_options,
                "x_xss_protection": self.security.x_xss_protection
            },
            "performance": {
                "enable_compression": self.performance.enable_compression,
                "enable_minification": self.performance.enable_minification,
                "lazy_loading": self.performance.lazy_loading,
                "image_optimization": self.performance.image_optimization,
                "chunk_size_mb": self.performance.chunk_size_mb,
                "max_concurrent_requests": self.performance.max_concurrent_requests,
                "cache_ttl_seconds": self.performance.cache_ttl_seconds,
                "cache_max_entries": self.performance.cache_max_entries,
                "enable_file_cache": self.performance.enable_file_cache,
                "enable_api_cache": self.performance.enable_api_cache
            },
            "ui": {
                "theme": self.ui.theme,
                "enable_dark_mode": self.ui.enable_dark_mode,
                "mobile_breakpoint": self.ui.mobile_breakpoint,
                "tablet_breakpoint": self.ui.tablet_breakpoint,
                "enable_animations": self.ui.enable_animations,
                "enable_haptic_feedback": self.ui.enable_haptic_feedback,
                "results_expander_expanded": self.ui.results_expander_expanded,
                "error_display_duration": self.ui.error_display_duration,
                "show_upload_progress": self.ui.show_upload_progress,
                "show_file_metadata": self.ui.show_file_metadata
            },
            "analytics": {
                "enable_user_tracking": self.analytics.enable_user_tracking,
                "enable_performance_tracking": self.analytics.enable_performance_tracking,
                "enable_error_tracking": self.analytics.enable_error_tracking,
                "retention_days": self.analytics.retention_days,
                "batch_size": self.analytics.batch_size
            },
            "websocket": {
                "enable_real_time": self.websocket.enable_real_time,
                "polling_interval_seconds": self.websocket.polling_interval_seconds,
                "connection_timeout_seconds": self.websocket.connection_timeout_seconds,
                "max_reconnect_attempts": self.websocket.max_reconnect_attempts,
                "heartbeat_interval_seconds": self.websocket.heartbeat_interval_seconds
            }
        }


# Global config instance
config = FrontendConfig()


def get_config() -> FrontendConfig:
    """Get the current configuration."""
    return config


def update_config(**kwargs) -> None:
    """Update configuration with new values."""
    global config
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)


def reload_config() -> FrontendConfig:
    """Reload configuration from environment."""
    global config
    config = FrontendConfig()
    return config