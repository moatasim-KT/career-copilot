"""
Model conversion utilities between database and API models.
"""

from typing import List, Optional
from uuid import UUID

from .api_models import (
    UserResponse,
    APIKeyResponse,
    ContractAnalysisResponse,
    AuditLogResponse,
    UserStatistics,
    AnalysisStatistics,
    AuditStatistics,
)
from .database_models import User, APIKey, ContractAnalysis, AuditLog


class ModelConverter:
    """Utility class for converting between database and API models."""
    
    @staticmethod
    def user_to_response(user: User) -> UserResponse:
        """
        Convert User database model to UserResponse API model.
        
        Args:
            user: User database model instance
            
        Returns:
            UserResponse API model instance
        """
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    @staticmethod
    def users_to_response_list(users: List[User]) -> List[UserResponse]:
        """
        Convert list of User database models to list of UserResponse API models.
        
        Args:
            users: List of User database model instances
            
        Returns:
            List of UserResponse API model instances
        """
        return [ModelConverter.user_to_response(user) for user in users]
    
    @staticmethod
    def api_key_to_response(api_key: APIKey) -> APIKeyResponse:
        """
        Convert APIKey database model to APIKeyResponse API model.
        
        Args:
            api_key: APIKey database model instance
            
        Returns:
            APIKeyResponse API model instance
        """
        return APIKeyResponse(
            id=api_key.id,
            key_name=api_key.key_name,
            permissions=api_key.permissions,
            is_active=api_key.is_active,
            last_used_at=api_key.last_used_at,
            expires_at=api_key.expires_at,
            created_at=api_key.created_at
        )
    
    @staticmethod
    def api_keys_to_response_list(api_keys: List[APIKey]) -> List[APIKeyResponse]:
        """
        Convert list of APIKey database models to list of APIKeyResponse API models.
        
        Args:
            api_keys: List of APIKey database model instances
            
        Returns:
            List of APIKeyResponse API model instances
        """
        return [ModelConverter.api_key_to_response(api_key) for api_key in api_keys]
    
    @staticmethod
    def contract_analysis_to_response(analysis: ContractAnalysis) -> ContractAnalysisResponse:
        """
        Convert ContractAnalysis database model to ContractAnalysisResponse API model.
        
        Args:
            analysis: ContractAnalysis database model instance
            
        Returns:
            ContractAnalysisResponse API model instance
        """
        return ContractAnalysisResponse(
            id=analysis.id,
            filename=analysis.filename,
            file_hash=analysis.file_hash,
            file_size=analysis.file_size,
            analysis_status=analysis.analysis_status,
            risk_score=analysis.risk_score,
            risky_clauses=analysis.risky_clauses,
            suggested_redlines=analysis.suggested_redlines,
            email_draft=analysis.email_draft,
            processing_time_seconds=analysis.processing_time_seconds,
            error_message=analysis.error_message,
            ai_model_used=analysis.ai_model_used,
            created_at=analysis.created_at,
            completed_at=analysis.completed_at
        )
    
    @staticmethod
    def contract_analyses_to_response_list(analyses: List[ContractAnalysis]) -> List[ContractAnalysisResponse]:
        """
        Convert list of ContractAnalysis database models to list of ContractAnalysisResponse API models.
        
        Args:
            analyses: List of ContractAnalysis database model instances
            
        Returns:
            List of ContractAnalysisResponse API model instances
        """
        return [ModelConverter.contract_analysis_to_response(analysis) for analysis in analyses]
    
    @staticmethod
    def audit_log_to_response(audit_log: AuditLog) -> AuditLogResponse:
        """
        Convert AuditLog database model to AuditLogResponse API model.
        
        Args:
            audit_log: AuditLog database model instance
            
        Returns:
            AuditLogResponse API model instance
        """
        return AuditLogResponse(
            id=audit_log.id,
            event_type=audit_log.event_type,
            event_data=audit_log.event_data,
            resource_type=audit_log.resource_type,
            resource_id=audit_log.resource_id,
            action=audit_log.action,
            result=audit_log.result,
            ip_address=str(audit_log.ip_address) if audit_log.ip_address else None,
            user_agent=audit_log.user_agent,
            session_id=audit_log.session_id,
            request_id=audit_log.request_id,
            created_at=audit_log.created_at
        )
    
    @staticmethod
    def audit_logs_to_response_list(audit_logs: List[AuditLog]) -> List[AuditLogResponse]:
        """
        Convert list of AuditLog database models to list of AuditLogResponse API models.
        
        Args:
            audit_logs: List of AuditLog database model instances
            
        Returns:
            List of AuditLogResponse API model instances
        """
        return [ModelConverter.audit_log_to_response(audit_log) for audit_log in audit_logs]
    
    @staticmethod
    def dict_to_user_statistics(stats_dict: dict) -> UserStatistics:
        """
        Convert dictionary to UserStatistics API model.
        
        Args:
            stats_dict: Dictionary with user statistics
            
        Returns:
            UserStatistics API model instance
        """
        return UserStatistics(
            total_users=stats_dict.get("total_users", 0),
            active_users=stats_dict.get("active_users", 0),
            inactive_users=stats_dict.get("inactive_users", 0),
            superusers=stats_dict.get("superusers", 0)
        )
    
    @staticmethod
    def dict_to_analysis_statistics(stats_dict: dict) -> AnalysisStatistics:
        """
        Convert dictionary to AnalysisStatistics API model.
        
        Args:
            stats_dict: Dictionary with analysis statistics
            
        Returns:
            AnalysisStatistics API model instance
        """
        return AnalysisStatistics(
            total_analyses=stats_dict.get("total_analyses", 0),
            completed_analyses=stats_dict.get("completed_analyses", 0),
            failed_analyses=stats_dict.get("failed_analyses", 0),
            pending_analyses=stats_dict.get("pending_analyses", 0),
            success_rate=stats_dict.get("success_rate", 0.0),
            average_processing_time_seconds=stats_dict.get("average_processing_time_seconds", 0.0),
            average_risk_score=stats_dict.get("average_risk_score", 0.0),
            period_days=stats_dict.get("period_days", 30)
        )
    
    @staticmethod
    def dict_to_audit_statistics(stats_dict: dict) -> AuditStatistics:
        """
        Convert dictionary to AuditStatistics API model.
        
        Args:
            stats_dict: Dictionary with audit statistics
            
        Returns:
            AuditStatistics API model instance
        """
        return AuditStatistics(
            total_events=stats_dict.get("total_events", 0),
            events_by_type=stats_dict.get("events_by_type", {}),
            events_by_result=stats_dict.get("events_by_result", {}),
            unique_users=stats_dict.get("unique_users", 0),
            unique_ip_addresses=stats_dict.get("unique_ip_addresses", 0),
            period_days=stats_dict.get("period_days", 30)
        )


# Convenience functions for common conversions
def user_to_dict(user: User) -> dict:
    """
    Convert User model to dictionary.
    
    Args:
        user: User database model instance
        
    Returns:
        Dictionary representation of user
    """
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat()
    }


def contract_analysis_to_dict(analysis: ContractAnalysis) -> dict:
    """
    Convert ContractAnalysis model to dictionary.
    
    Args:
        analysis: ContractAnalysis database model instance
        
    Returns:
        Dictionary representation of job application tracking
    """
    return {
        "id": str(analysis.id),
        "filename": analysis.filename,
        "file_hash": analysis.file_hash,
        "file_size": analysis.file_size,
        "analysis_status": analysis.analysis_status,
        "risk_score": float(analysis.risk_score) if analysis.risk_score else None,
        "risky_clauses": analysis.risky_clauses,
        "suggested_redlines": analysis.suggested_redlines,
        "email_draft": analysis.email_draft,
        "processing_time_seconds": float(analysis.processing_time_seconds) if analysis.processing_time_seconds else None,
        "error_message": analysis.error_message,
        "ai_model_used": analysis.ai_model_used,
        "created_at": analysis.created_at.isoformat(),
        "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None
    }


def audit_log_to_dict(audit_log: AuditLog) -> dict:
    """
    Convert AuditLog model to dictionary.
    
    Args:
        audit_log: AuditLog database model instance
        
    Returns:
        Dictionary representation of audit log
    """
    return {
        "id": str(audit_log.id),
        "user_id": str(audit_log.user_id) if audit_log.user_id else None,
        "event_type": audit_log.event_type,
        "event_data": audit_log.event_data,
        "resource_type": audit_log.resource_type,
        "resource_id": audit_log.resource_id,
        "action": audit_log.action,
        "result": audit_log.result,
        "ip_address": str(audit_log.ip_address) if audit_log.ip_address else None,
        "user_agent": audit_log.user_agent,
        "session_id": audit_log.session_id,
        "request_id": audit_log.request_id,
        "created_at": audit_log.created_at.isoformat()
    }


# Validation helpers
def validate_uuid(uuid_string: str) -> bool:
    """
    Validate UUID string format.
    
    Args:
        uuid_string: String to validate as UUID
        
    Returns:
        True if valid UUID, False otherwise
    """
    try:
        UUID(uuid_string)
        return True
    except (ValueError, TypeError):
        return False


def validate_pagination_params(page: int, page_size: int) -> tuple[int, int]:
    """
    Validate and normalize pagination parameters.
    
    Args:
        page: Page number (1-based)
        page_size: Number of items per page
        
    Returns:
        Tuple of (validated_page, validated_page_size)
        
    Raises:
        ValueError: If parameters are invalid
    """
    if page < 1:
        raise ValueError("Page number must be 1 or greater")
    
    if page_size < 1:
        raise ValueError("Page size must be 1 or greater")
    
    if page_size > 100:
        raise ValueError("Page size cannot exceed 100")
    
    return page, page_size


def calculate_pagination_info(total_count: int, page: int, page_size: int) -> dict:
    """
    Calculate pagination information.
    
    Args:
        total_count: Total number of items
        page: Current page number (1-based)
        page_size: Number of items per page
        
    Returns:
        Dictionary with pagination information
    """
    total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
    has_next = page < total_pages
    has_prev = page > 1
    
    return {
        "total_count": total_count,
        "total_pages": total_pages,
        "current_page": page,
        "page_size": page_size,
        "has_next": has_next,
        "has_prev": has_prev,
        "start_index": (page - 1) * page_size + 1 if total_count > 0 else 0,
        "end_index": min(page * page_size, total_count)
    }