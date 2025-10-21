"""
Security Validation API endpoints for Career Copilot.
Provides endpoints for security configuration validation and monitoring.
"""

from typing import Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, status, Depends
from pydantic import BaseModel

from ...core.security_validator import get_security_validator, validate_security_configuration
from ...core.logging import get_logger
from ...core.audit import audit_logger, AuditEventType, AuditSeverity
from ...middleware.auth_middleware import require_auth, require_roles

logger = get_logger(__name__)

router = APIRouter(prefix="/security", tags=["security-validation"])


class SecurityValidationResponse(BaseModel):
    """Response model for security validation."""
    security_score: int
    max_score: int
    score_percentage: float
    security_level: str
    validation_results: List[Dict[str, Any]]
    recommendations: List[Dict[str, str]]
    critical_issues: List[Dict[str, Any]]
    environment: str
    timestamp: datetime


class SecurityCheckResponse(BaseModel):
    """Response model for individual security check."""
    category: str
    check: str
    passed: bool
    weight: int
    severity: str


class SecurityRecommendationResponse(BaseModel):
    """Response model for security recommendation."""
    category: str
    check: str
    severity: str
    recommendation: str


@router.get("/validate", response_model=SecurityValidationResponse)
@require_auth
@require_roles("admin")
async def validate_security_configuration_endpoint(
    current_user: Dict[str, Any] = None
) -> SecurityValidationResponse:
    """
    Perform comprehensive security configuration validation.
    
    This endpoint validates all security settings and provides
    recommendations for improvement. Admin access required.
    """
    try:
        # Perform security validation
        validation_results = validate_security_configuration()
        
        # Log security validation request
        audit_logger.log_event(
            event_type=AuditEventType.SECURITY_AUDIT,
            action="Security configuration validation requested",
            severity=AuditSeverity.MEDIUM,
            user_id=current_user.get("uid"),
            details={
                "security_level": validation_results["security_level"],
                "score_percentage": validation_results["score_percentage"]
            }
        )
        
        return SecurityValidationResponse(
            security_score=validation_results["security_score"],
            max_score=validation_results["max_score"],
            score_percentage=validation_results["score_percentage"],
            security_level=validation_results["security_level"],
            validation_results=validation_results["validation_results"],
            recommendations=validation_results["recommendations"],
            critical_issues=validation_results["critical_issues"],
            environment=validation_results["environment"],
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error during security validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Security validation failed"
        )


@router.get("/status")
@require_auth
async def get_security_status(
    current_user: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Get basic security status information.
    
    Returns high-level security status without detailed validation.
    Available to all authenticated users.
    """
    try:
        validator = get_security_validator()
        
        # Perform quick validation
        results = validator.validate_all_security_settings()
        
        # Return basic status
        return {
            "security_level": results["security_level"],
            "score_percentage": results["score_percentage"],
            "critical_issues_count": len(results["critical_issues"]),
            "environment": results["environment"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting security status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security status"
        )


@router.get("/recommendations", response_model=List[SecurityRecommendationResponse])
@require_auth
@require_roles("admin")
async def get_security_recommendations(
    current_user: Dict[str, Any] = None
) -> List[SecurityRecommendationResponse]:
    """
    Get security recommendations based on current configuration.
    
    Returns actionable recommendations to improve security posture.
    Admin access required.
    """
    try:
        validation_results = validate_security_configuration()
        
        recommendations = []
        for rec in validation_results["recommendations"]:
            recommendations.append(SecurityRecommendationResponse(
                category=rec["category"],
                check=rec["check"],
                severity=rec["severity"],
                recommendation=rec["recommendation"]
            ))
        
        # Log recommendations request
        audit_logger.log_event(
            event_type=AuditEventType.SECURITY_AUDIT,
            action="Security recommendations requested",
            severity=AuditSeverity.LOW,
            user_id=current_user.get("uid"),
            details={"recommendations_count": len(recommendations)}
        )
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error getting security recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security recommendations"
        )


@router.get("/critical-issues")
@require_auth
@require_roles("admin")
async def get_critical_security_issues(
    current_user: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Get critical security issues that need immediate attention.
    
    Returns high-priority security issues that should be addressed urgently.
    Admin access required.
    """
    try:
        validation_results = validate_security_configuration()
        
        critical_issues = validation_results["critical_issues"]
        
        # Log critical issues request
        audit_logger.log_event(
            event_type=AuditEventType.SECURITY_AUDIT,
            action="Critical security issues requested",
            severity=AuditSeverity.HIGH if critical_issues else AuditSeverity.LOW,
            user_id=current_user.get("uid"),
            details={"critical_issues_count": len(critical_issues)}
        )
        
        return {
            "critical_issues": critical_issues,
            "count": len(critical_issues),
            "security_level": validation_results["security_level"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting critical security issues: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get critical security issues"
        )


@router.get("/checks", response_model=List[SecurityCheckResponse])
@require_auth
@require_roles("admin")
async def get_security_checks(
    category: str = None,
    current_user: Dict[str, Any] = None
) -> List[SecurityCheckResponse]:
    """
    Get detailed security check results.
    
    Returns detailed results of all security checks, optionally filtered by category.
    Admin access required.
    
    Args:
        category: Optional category filter (e.g., "Authentication", "CORS", etc.)
    """
    try:
        validation_results = validate_security_configuration()
        
        checks = validation_results["validation_results"]
        
        # Filter by category if specified
        if category:
            checks = [check for check in checks if check["category"].lower() == category.lower()]
        
        response_checks = []
        for check in checks:
            response_checks.append(SecurityCheckResponse(
                category=check["category"],
                check=check["check"],
                passed=check["passed"],
                weight=check["weight"],
                severity=check["severity"]
            ))
        
        # Log security checks request
        audit_logger.log_event(
            event_type=AuditEventType.SECURITY_AUDIT,
            action=f"Security checks requested{f' for category: {category}' if category else ''}",
            severity=AuditSeverity.LOW,
            user_id=current_user.get("uid"),
            details={"checks_count": len(response_checks), "category": category}
        )
        
        return response_checks
        
    except Exception as e:
        logger.error(f"Error getting security checks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security checks"
        )


@router.get("/categories")
@require_auth
@require_roles("admin")
async def get_security_categories(
    current_user: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Get available security check categories.
    
    Returns list of security categories that can be used for filtering.
    Admin access required.
    """
    try:
        validation_results = validate_security_configuration()
        
        categories = set()
        for check in validation_results["validation_results"]:
            categories.add(check["category"])
        
        return {
            "categories": sorted(list(categories)),
            "count": len(categories),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting security categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security categories"
        )


@router.post("/validate/refresh")
@require_auth
@require_roles("admin")
async def refresh_security_validation(
    current_user: Dict[str, Any] = None
) -> Dict[str, str]:
    """
    Refresh security validation cache.
    
    Forces a fresh security validation and clears any cached results.
    Admin access required.
    """
    try:
        # Create new validator instance to force refresh
        from ...core.security_validator import SecurityConfigurationValidator
        validator = SecurityConfigurationValidator()
        results = validator.validate_all_security_settings()
        
        # Log validation refresh
        audit_logger.log_event(
            event_type=AuditEventType.SECURITY_AUDIT,
            action="Security validation cache refreshed",
            severity=AuditSeverity.MEDIUM,
            user_id=current_user.get("uid"),
            details={
                "security_level": results["security_level"],
                "score_percentage": results["score_percentage"]
            }
        )
        
        return {
            "message": "Security validation refreshed successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error refreshing security validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh security validation"
        )


@router.get("/health")
async def security_validation_health() -> Dict[str, str]:
    """Security validation system health check."""
    try:
        # Quick validation to ensure system is working
        validator = get_security_validator()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Security validation health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Security validation system unhealthy"
        )