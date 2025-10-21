"""
Configuration Management API endpoints.

This module provides REST API endpoints for:
- Configuration status and health checks
- Feature flag management
- Configuration hot-reloading
- Environment information
- Configuration validation
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field

from ...core.logging import get_logger
from ...core.config_init import (
    get_configuration_status,
    get_configuration_summary,
    is_configuration_ready,
    reload_configuration_system
)
from ...core.config_hot_reload import (
    get_configuration_hot_reloader,
    ReloadTrigger,
    ReloadStatus
)
from ...core.feature_flags import (
    get_feature_flag_manager,
    UserContext,
    FeatureState,
    RolloutStrategy
)
from ...core.config_validation import validate_startup_configuration
from ...core.config_manager import get_config_manager

logger = get_logger(__name__)
router = APIRouter(tags=["Configuration Management"])


# Pydantic models for API requests/responses
class ConfigurationStatusResponse(BaseModel):
    """Configuration system status response."""
    environment: str
    config_loaded: bool
    validation_passed: bool
    feature_flags_loaded: bool
    hot_reload_enabled: bool
    errors: int
    warnings: int
    startup_time: float
    ready: bool


class ConfigurationSummaryResponse(BaseModel):
    """Configuration summary response."""
    environment: str
    api_port: Optional[int]
    database_type: str
    ai_providers: List[str]
    monitoring_enabled: bool
    hot_reload_enabled: bool
    feature_flags_loaded: bool
    validation_status: str
    errors: int
    warnings: int


class FeatureFlagResponse(BaseModel):
    """Feature flag information response."""
    name: str
    description: str
    state: str
    default_value: bool
    dependencies: List[str]
    tags: List[str]
    created_at: str
    updated_at: str
    created_by: Optional[str]
    metadata: Dict[str, Any]
    rollout_config: Optional[Dict[str, Any]]


class FeatureFlagListResponse(BaseModel):
    """Feature flags list response."""
    flags: Dict[str, Dict[str, Any]]
    total_count: int
    enabled_count: int
    disabled_count: int
    rollout_count: int


class FeatureFlagCheckRequest(BaseModel):
    """Feature flag check request."""
    flag_name: str
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class FeatureFlagCheckResponse(BaseModel):
    """Feature flag check response."""
    flag_name: str
    enabled: bool
    reason: str
    user_context: Optional[Dict[str, Any]] = None


class FeatureFlagUpdateRequest(BaseModel):
    """Feature flag update request."""
    state: FeatureState
    rollout_percentage: Optional[float] = None


class ConfigurationReloadResponse(BaseModel):
    """Configuration reload response."""
    success: bool
    timestamp: str
    trigger: str
    status: str
    changed_files: List[str]
    error_message: Optional[str]
    validation_errors: int
    validation_warnings: int
    reload_duration: float


class ValidationReportResponse(BaseModel):
    """Configuration validation report response."""
    environment: str
    timestamp: str
    errors: int
    warnings: int
    infos: int
    has_errors: bool
    summary: str
    results: List[Dict[str, Any]]


@router.get("/configuration/status", response_model=ConfigurationStatusResponse)
async def get_configuration_status():
    """Get current configuration system status."""
    try:
        status = get_configuration_status()
        
        if not status:
            raise HTTPException(
                status_code=503,
                detail="Configuration system not initialized"
            )
        
        return ConfigurationStatusResponse(
            environment=status.environment,
            config_loaded=status.config_loaded,
            validation_passed=status.validation_passed,
            feature_flags_loaded=status.feature_flags_loaded,
            hot_reload_enabled=status.hot_reload_enabled,
            errors=status.errors,
            warnings=status.warnings,
            startup_time=status.startup_time,
            ready=is_configuration_ready()
        )
    
    except Exception as e:
        logger.error(f"Failed to get configuration status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get configuration status: {str(e)}"
        )


@router.get("/configuration/summary", response_model=ConfigurationSummaryResponse)
async def get_configuration_summary():
    """Get configuration summary."""
    try:
        summary = get_configuration_summary()
        
        if not summary:
            raise HTTPException(
                status_code=503,
                detail="Configuration system not available"
            )
        
        return ConfigurationSummaryResponse(**summary)
    
    except Exception as e:
        logger.error(f"Failed to get configuration summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get configuration summary: {str(e)}"
        )


@router.post("/configuration/reload", response_model=ConfigurationReloadResponse)
async def reload_configuration():
    """Manually reload configuration."""
    try:
        success = await reload_configuration_system()
        
        # Get reload event details from hot reloader
        hot_reloader = get_configuration_hot_reloader()
        history = hot_reloader.get_reload_history(limit=1)
        
        if history:
            event = history[-1]
            return ConfigurationReloadResponse(
                success=success,
                timestamp=event.timestamp.isoformat(),
                trigger=event.trigger.value,
                status=event.status.value,
                changed_files=event.changed_files,
                error_message=event.error_message,
                validation_errors=event.validation_errors,
                validation_warnings=event.validation_warnings,
                reload_duration=event.reload_duration
            )
        else:
            return ConfigurationReloadResponse(
                success=success,
                timestamp=datetime.utcnow().isoformat(),
                trigger="api_request",
                status="success" if success else "failed",
                changed_files=[],
                error_message=None if success else "Reload failed",
                validation_errors=0,
                validation_warnings=0,
                reload_duration=0.0
            )
    
    except Exception as e:
        logger.error(f"Configuration reload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Configuration reload failed: {str(e)}"
        )


@router.get("/configuration/reload-history")
async def get_reload_history(limit: int = Query(20, ge=1, le=100)):
    """Get configuration reload history."""
    try:
        hot_reloader = get_configuration_hot_reloader()
        history = hot_reloader.get_reload_history(limit=limit)
        
        return {
            "history": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "trigger": event.trigger.value,
                    "status": event.status.value,
                    "changed_files": event.changed_files,
                    "error_message": event.error_message,
                    "validation_errors": event.validation_errors,
                    "validation_warnings": event.validation_warnings,
                    "reload_duration": event.reload_duration,
                    "config_hash": event.config_hash
                }
                for event in history
            ],
            "total_count": len(history)
        }
    
    except Exception as e:
        logger.error(f"Failed to get reload history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get reload history: {str(e)}"
        )


@router.get("/configuration/validate", response_model=ValidationReportResponse)
async def validate_configuration():
    """Validate current configuration."""
    try:
        config_manager = get_config_manager()
        
        if not config_manager.config_data:
            raise HTTPException(
                status_code=503,
                detail="No configuration data available"
            )
        
        # Get current environment
        status = get_configuration_status()
        environment = status.environment if status else "development"
        
        # Run validation
        report = validate_startup_configuration(config_manager.config_data, environment)
        
        return ValidationReportResponse(
            environment=report.environment,
            timestamp=report.timestamp.isoformat(),
            errors=report.errors,
            warnings=report.warnings,
            infos=report.infos,
            has_errors=report.has_errors(),
            summary=report.get_summary(),
            results=[
                {
                    "level": result.level.value,
                    "category": result.category.value,
                    "field": result.field,
                    "message": result.message,
                    "suggestion": result.suggestion,
                    "current_value": result.current_value,
                    "expected_format": result.expected_format,
                    "documentation_link": result.documentation_link
                }
                for result in report.results
            ]
        )
    
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Configuration validation failed: {str(e)}"
        )


@router.get("/feature-flags", response_model=FeatureFlagListResponse)
async def list_feature_flags(tags: Optional[List[str]] = Query(None)):
    """List all feature flags."""
    try:
        ff_manager = get_feature_flag_manager()
        flags = await ff_manager.list_flags(tags=tags)
        
        # Count flags by state
        enabled_count = sum(1 for flag in flags.values() if flag.get('state') == 'enabled')
        disabled_count = sum(1 for flag in flags.values() if flag.get('state') == 'disabled')
        rollout_count = sum(1 for flag in flags.values() if flag.get('state') in ['rollout', 'testing'])
        
        return FeatureFlagListResponse(
            flags=flags,
            total_count=len(flags),
            enabled_count=enabled_count,
            disabled_count=disabled_count,
            rollout_count=rollout_count
        )
    
    except Exception as e:
        logger.error(f"Failed to list feature flags: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list feature flags: {str(e)}"
        )


@router.get("/feature-flags/{flag_name}", response_model=FeatureFlagResponse)
async def get_feature_flag(flag_name: str):
    """Get detailed information about a specific feature flag."""
    try:
        ff_manager = get_feature_flag_manager()
        flag_info = await ff_manager.get_flag_info(flag_name)
        
        if not flag_info:
            raise HTTPException(
                status_code=404,
                detail=f"Feature flag '{flag_name}' not found"
            )
        
        return FeatureFlagResponse(**flag_info)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get feature flag '{flag_name}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get feature flag: {str(e)}"
        )


@router.post("/feature-flags/{flag_name}/check", response_model=FeatureFlagCheckResponse)
async def check_feature_flag(flag_name: str, request: FeatureFlagCheckRequest):
    """Check if a feature flag is enabled for a specific user context."""
    try:
        ff_manager = get_feature_flag_manager()
        
        # Create user context
        user_context = UserContext(
            user_id=request.user_id,
            email=request.email,
            role=request.role,
            attributes=request.attributes
        )
        
        # Check flag
        enabled = await ff_manager.is_enabled(flag_name, user_context)
        
        # Determine reason
        flag_info = await ff_manager.get_flag_info(flag_name)
        if not flag_info:
            reason = "Flag not found, using default value"
        elif flag_info['state'] == 'enabled':
            reason = "Flag is globally enabled"
        elif flag_info['state'] == 'disabled':
            reason = "Flag is globally disabled"
        elif flag_info['state'] in ['rollout', 'testing']:
            reason = "Flag is in rollout/testing mode"
        else:
            reason = "Using default value"
        
        return FeatureFlagCheckResponse(
            flag_name=flag_name,
            enabled=enabled,
            reason=reason,
            user_context={
                "user_id": user_context.user_id,
                "email": user_context.email,
                "role": user_context.role,
                "attributes": user_context.attributes
            }
        )
    
    except Exception as e:
        logger.error(f"Failed to check feature flag '{flag_name}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check feature flag: {str(e)}"
        )


@router.put("/feature-flags/{flag_name}/state")
async def update_feature_flag_state(flag_name: str, request: FeatureFlagUpdateRequest):
    """Update the state of a feature flag."""
    try:
        ff_manager = get_feature_flag_manager()
        
        # Update flag state
        success = await ff_manager.update_flag_state(flag_name, request.state)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Feature flag '{flag_name}' not found"
            )
        
        # Update rollout percentage if provided
        if request.rollout_percentage is not None and request.state in [FeatureState.ROLLOUT, FeatureState.TESTING]:
            rollout_success = await ff_manager.set_rollout_percentage(flag_name, request.rollout_percentage)
            if not rollout_success:
                logger.warning(f"Failed to set rollout percentage for '{flag_name}'")
        
        return {
            "success": True,
            "message": f"Feature flag '{flag_name}' updated to state '{request.state.value}'",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update feature flag '{flag_name}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update feature flag: {str(e)}"
        )


@router.post("/feature-flags/{flag_name}/rollout")
async def set_feature_flag_rollout(
    flag_name: str,
    percentage: float = Body(..., ge=0, le=100, description="Rollout percentage (0-100)")
):
    """Set rollout percentage for a feature flag."""
    try:
        ff_manager = get_feature_flag_manager()
        
        success = await ff_manager.set_rollout_percentage(flag_name, percentage)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Feature flag '{flag_name}' not found"
            )
        
        return {
            "success": True,
            "message": f"Feature flag '{flag_name}' rollout set to {percentage}%",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set rollout for feature flag '{flag_name}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set rollout: {str(e)}"
        )


@router.delete("/feature-flags/cache")
async def clear_feature_flags_cache():
    """Clear the feature flags cache."""
    try:
        ff_manager = get_feature_flag_manager()
        ff_manager.clear_cache()
        
        return {
            "success": True,
            "message": "Feature flags cache cleared",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to clear feature flags cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/configuration/snapshots")
async def get_configuration_snapshots():
    """Get available configuration snapshots."""
    try:
        hot_reloader = get_configuration_hot_reloader()
        snapshots = hot_reloader.get_snapshots_info()
        
        return {
            "snapshots": snapshots,
            "total_count": len(snapshots)
        }
    
    except Exception as e:
        logger.error(f"Failed to get configuration snapshots: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get snapshots: {str(e)}"
        )


@router.post("/configuration/rollback")
async def rollback_configuration(snapshot_index: int = Body(-1, description="Snapshot index (-1 for latest)")):
    """Rollback configuration to a previous snapshot."""
    try:
        hot_reloader = get_configuration_hot_reloader()
        success = hot_reloader.rollback_to_snapshot(snapshot_index)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Configuration rollback failed"
            )
        
        return {
            "success": True,
            "message": f"Configuration rolled back to snapshot {snapshot_index}",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Configuration rollback failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Rollback failed: {str(e)}"
        )


@router.get("/configuration/environment")
async def get_environment_info():
    """Get current environment information."""
    try:
        from ...core.environment_config import get_environment_config_manager
        
        env_manager = get_environment_config_manager()
        config = env_manager.get_config()
        
        return {
            "environment": env_manager.get_environment().value,
            "is_development": env_manager.is_development(),
            "is_production": env_manager.is_production(),
            "is_testing": env_manager.is_testing(),
            "config": {
                "debug": config.debug,
                "log_level": config.log_level,
                "enable_monitoring": config.enable_monitoring,
                "enable_security": config.enable_security,
                "enable_auth": config.enable_auth,
                "database_pool_size": config.database_pool_size,
                "worker_count": config.worker_count,
                "rate_limit_enabled": config.rate_limit_enabled,
                "file_upload_max_size": config.file_upload_max_size,
                "session_timeout": config.session_timeout
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get environment info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get environment info: {str(e)}"
        )