"""
API v1 package - Career Copilot REST API endpoints.
"""

from .contracts import router as contracts_router
from .contract_results import router as contract_results_router
from .health import router as health_router
from .monitoring import router as monitoring_router
from .security import router as security_router
from .email import router as email_router
from .performance import router as performance_router
from .precedents import router as precedents_router
from .production_health import router as production_health
from .health_analytics import router as health_analytics
from .external_services import router as external_services_router
from .analysis_history import router as analysis_history_router
from .migrations import router as migrations_router
from .file_storage import router as file_storage_router
from .email_templates import router as email_templates_router
from . import progress
from . import cache
from . import file_storage

__all__ = [
    "contracts_router",
    "contract_results_router",
    "health_router", 
    "monitoring_router",
    "security_router",
    "email_router",
    "performance_router",
    "precedents_router",
    "production_health",
    "health_analytics",
    "external_services_router",
    "analysis_history_router",
    "migrations_router",
    "file_storage_router",
    "email_templates_router",
    "progress",
    "cache",
    "file_storage",
]
