"""
Predefined consolidation phases based on the consolidation plan.

This module contains predefined phases and steps that match the
consolidation tasks outlined in the specification.
"""

from typing import List, Dict, Any
from .tracking_system import ConsolidationType
from .file_mapping import MappingType


# Predefined consolidation phases based on the 8-week plan
CONSOLIDATION_PHASES = [
    # Week 1: Foundation
    {
        "name": "Configuration System Consolidation",
        "description": "Consolidate core configuration system",
        "week": 1,
        "consolidation_type": ConsolidationType.MODULE_CONSOLIDATION,
        "steps": [
            {
                "name": "Create unified configuration manager",
                "description": "Consolidate config.py, config_loader.py, config_manager.py, config_validator.py into single config.py",
                "original_files": [
                    "backend/app/core/config.py",
                    "backend/app/core/config_loader.py",
                    "backend/app/core/config_manager.py",
                    "backend/app/core/config_validator.py"
                ],
                "consolidated_files": ["backend/app/core/config.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            },
            {
                "name": "Implement advanced configuration features",
                "description": "Create config_advanced.py for hot reload, templates, and integrations functionality",
                "original_files": [
                    "backend/app/core/config_validation.py",
                    "backend/app/core/config_init.py",
                    "backend/app/core/config_integration.py",
                    "backend/app/core/config_templates.py",
                    "backend/app/core/config_hot_reload.py"
                ],
                "consolidated_files": ["backend/app/core/config_advanced.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            }
        ]
    },
    {
        "name": "Analytics Services Consolidation",
        "description": "Consolidate analytics services",
        "week": 1,
        "consolidation_type": ConsolidationType.SERVICE_CONSOLIDATION,
        "steps": [
            {
                "name": "Create core analytics service",
                "description": "Consolidate analytics.py, analytics_service.py, analytics_data_collection_service.py into analytics_service.py",
                "original_files": [
                    "backend/app/services/analytics.py",
                    "backend/app/services/analytics_service.py",
                    "backend/app/services/analytics_data_collection_service.py"
                ],
                "consolidated_files": ["backend/app/services/analytics_service.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            },
            {
                "name": "Implement specialized analytics features",
                "description": "Create analytics_specialized.py for domain-specific analytics",
                "original_files": [
                    "backend/app/services/advanced_user_analytics_service.py",
                    "backend/app/services/application_analytics_service.py",
                    "backend/app/services/email_analytics_service.py",
                    "backend/app/services/job_analytics_service.py",
                    "backend/app/services/slack_analytics_service.py"
                ],
                "consolidated_files": ["backend/app/services/analytics_specialized.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            }
        ]
    },
    {
        "name": "E2E Tests Cleanup",
        "description": "Clean up E2E tests",
        "week": 1,
        "consolidation_type": ConsolidationType.TEST_CONSOLIDATION,
        "steps": [
            {
                "name": "Remove redundant demo test files",
                "description": "Identify and remove all demo_*.py files from tests/e2e/ directory",
                "original_files": [
                    "tests/e2e/demo.py"
                ],
                "consolidated_files": [],
                "mapping_type": MappingType.MANY_TO_ONE
            }
        ]
    },
    
    # Weeks 2-3: Core Services
    {
        "name": "Job Management Services Consolidation",
        "description": "Consolidate job management services",
        "week": 2,
        "consolidation_type": ConsolidationType.SERVICE_CONSOLIDATION,
        "steps": [
            {
                "name": "Create core job service",
                "description": "Consolidate job_service.py, unified_job_service.py into single job_service.py",
                "original_files": [
                    "backend/app/services/job_service.py",
                    "backend/app/services/unified_job_service.py"
                ],
                "consolidated_files": ["backend/app/services/job_service.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            },
            {
                "name": "Implement job scraping service",
                "description": "Create job_scraping_service.py consolidating job scraping functionality",
                "original_files": [
                    "backend/app/services/job_scraper_service.py",
                    "backend/app/services/job_scraper.py",
                    "backend/app/services/job_ingestion_service.py",
                    "backend/app/services/job_ingestion.py",
                    "backend/app/services/job_api_service.py"
                ],
                "consolidated_files": ["backend/app/services/job_scraping_service.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            },
            {
                "name": "Implement job recommendation service",
                "description": "Create job_recommendation_service.py consolidating job matching functionality",
                "original_files": [
                    "backend/app/services/job_matching_service.py",
                    "backend/app/services/job_recommendation_feedback_service.py",
                    "backend/app/services/job_source_manager.py",
                    "backend/app/services/job_data_normalizer.py",
                    "backend/app/services/job_description_parser_service.py"
                ],
                "consolidated_files": ["backend/app/services/job_recommendation_service.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            }
        ]
    },
    {
        "name": "Authentication Services Consolidation",
        "description": "Consolidate authentication services",
        "week": 2,
        "consolidation_type": ConsolidationType.SERVICE_CONSOLIDATION,
        "steps": [
            {
                "name": "Create core authentication service",
                "description": "Consolidate authentication services into auth_service.py",
                "original_files": [
                    "backend/app/services/auth_service.py",
                    "backend/app/services/authentication_service.py",
                    "backend/app/services/authorization_service.py",
                    "backend/app/services/jwt_token_manager.py"
                ],
                "consolidated_files": ["backend/app/services/auth_service.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            },
            {
                "name": "Implement OAuth service",
                "description": "Create oauth_service.py consolidating OAuth functionality",
                "original_files": [
                    "backend/app/services/firebase_auth_service.py",
                    "backend/app/services/oauth_service.py"
                ],
                "consolidated_files": ["backend/app/services/oauth_service.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            }
        ]
    },
    {
        "name": "Database Management Consolidation",
        "description": "Consolidate database management",
        "week": 3,
        "consolidation_type": ConsolidationType.MODULE_CONSOLIDATION,
        "steps": [
            {
                "name": "Create core database manager",
                "description": "Consolidate database management into database.py",
                "original_files": [
                    "backend/app/core/database.py",
                    "backend/app/core/database_init.py",
                    "backend/app/core/database_simple.py"
                ],
                "consolidated_files": ["backend/app/core/database.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            },
            {
                "name": "Implement database optimization service",
                "description": "Create database_optimization.py for performance and backup management",
                "original_files": [
                    "backend/app/core/optimized_database.py",
                    "backend/app/core/database_backup.py",
                    "backend/app/core/database_migrations.py",
                    "backend/app/core/database_optimization.py",
                    "backend/app/core/database_performance.py"
                ],
                "consolidated_files": ["backend/app/core/database_optimization.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            }
        ]
    },
    
    # Weeks 4-5: Supporting Services
    {
        "name": "Email Services Consolidation",
        "description": "Consolidate email services",
        "week": 4,
        "consolidation_type": ConsolidationType.SERVICE_CONSOLIDATION,
        "steps": [
            {
                "name": "Create core email service",
                "description": "Consolidate email services into email_service.py",
                "original_files": [
                    "backend/app/services/email_service.py",
                    "backend/app/services/gmail_service.py",
                    "backend/app/services/smtp_service.py",
                    "backend/app/services/sendgrid_service.py"
                ],
                "consolidated_files": ["backend/app/services/email_service.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            },
            {
                "name": "Implement email template manager",
                "description": "Create email_template_manager.py for template management",
                "original_files": [
                    "backend/app/services/email_template_service.py",
                    "backend/app/services/email_template_manager.py",
                    "backend/app/services/email_analytics_service.py",
                    "backend/app/services/email_notification_optimizer.py"
                ],
                "consolidated_files": ["backend/app/services/email_template_manager.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            }
        ]
    },
    {
        "name": "Cache Services Consolidation",
        "description": "Consolidate cache services",
        "week": 4,
        "consolidation_type": ConsolidationType.SERVICE_CONSOLIDATION,
        "steps": [
            {
                "name": "Create core cache service",
                "description": "Consolidate cache services into cache_service.py",
                "original_files": [
                    "backend/app/services/cache_service.py",
                    "backend/app/services/session_cache_service.py",
                    "backend/app/services/recommendation_cache_service.py"
                ],
                "consolidated_files": ["backend/app/services/cache_service.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            },
            {
                "name": "Implement intelligent cache service",
                "description": "Create intelligent_cache_service.py for advanced caching",
                "original_files": [
                    "backend/app/services/intelligent_cache_service.py",
                    "backend/app/services/cache_invalidation_service.py",
                    "backend/app/services/cache_monitoring_service.py"
                ],
                "consolidated_files": ["backend/app/services/intelligent_cache_service.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            }
        ]
    },
    {
        "name": "LLM Services Consolidation",
        "description": "Consolidate LLM services",
        "week": 5,
        "consolidation_type": ConsolidationType.SERVICE_CONSOLIDATION,
        "steps": [
            {
                "name": "Create core LLM service",
                "description": "Consolidate LLM services into llm_service.py",
                "original_files": [
                    "backend/app/services/llm_manager.py",
                    "backend/app/services/llm_service_plugin.py",
                    "backend/app/services/llm_error_handler.py",
                    "backend/app/services/ai_service_manager.py",
                    "backend/app/services/unified_ai_service.py"
                ],
                "consolidated_files": ["backend/app/services/llm_service.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            },
            {
                "name": "Implement LLM configuration manager",
                "description": "Create llm_config_manager.py for LLM configuration",
                "original_files": [
                    "backend/app/services/llm_config_manager.py",
                    "backend/app/services/llm_cache_manager.py",
                    "backend/app/services/llm_benchmarking.py"
                ],
                "consolidated_files": ["backend/app/services/llm_config_manager.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            }
        ]
    },
    
    # Weeks 6-7: Infrastructure
    {
        "name": "Middleware Stack Consolidation",
        "description": "Consolidate middleware stack",
        "week": 6,
        "consolidation_type": ConsolidationType.MODULE_CONSOLIDATION,
        "steps": [
            {
                "name": "Consolidate authentication middleware",
                "description": "Consolidate authentication middleware into auth_middleware.py",
                "original_files": [
                    "backend/app/middleware/auth_middleware.py",
                    "backend/app/middleware/jwt_auth_middleware.py",
                    "backend/app/middleware/api_key_middleware.py"
                ],
                "consolidated_files": ["backend/app/middleware/auth_middleware.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            },
            {
                "name": "Consolidate security middleware",
                "description": "Consolidate security middleware into security_middleware.py",
                "original_files": [
                    "backend/app/middleware/security_middleware.py",
                    "backend/app/middleware/ai_security_middleware.py"
                ],
                "consolidated_files": ["backend/app/middleware/security_middleware.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            },
            {
                "name": "Consolidate error handling middleware",
                "description": "Consolidate error handling into error_handling.py",
                "original_files": [
                    "backend/app/middleware/error_handling.py",
                    "backend/app/middleware/global_error_handler.py"
                ],
                "consolidated_files": ["backend/app/middleware/error_handling.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            }
        ]
    },
    {
        "name": "Task Management Consolidation",
        "description": "Consolidate task management",
        "week": 6,
        "consolidation_type": ConsolidationType.MODULE_CONSOLIDATION,
        "steps": [
            {
                "name": "Consolidate analytics tasks",
                "description": "Consolidate analytics tasks into analytics_tasks.py",
                "original_files": [
                    "backend/app/tasks/analytics_tasks.py",
                    "backend/app/tasks/analytics_collection_tasks.py"
                ],
                "consolidated_files": ["backend/app/tasks/analytics_tasks.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            },
            {
                "name": "Consolidate scheduled tasks",
                "description": "Consolidate scheduled tasks into scheduled_tasks.py",
                "original_files": [
                    "backend/app/tasks/scheduled_tasks.py",
                    "backend/app/tasks/scheduler.py"
                ],
                "consolidated_files": ["backend/app/tasks/scheduled_tasks.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            }
        ]
    },
    {
        "name": "Monitoring System Consolidation",
        "description": "Consolidate monitoring system",
        "week": 7,
        "consolidation_type": ConsolidationType.MODULE_CONSOLIDATION,
        "steps": [
            {
                "name": "Create core monitoring service",
                "description": "Consolidate monitoring into monitoring.py",
                "original_files": [
                    "backend/app/core/monitoring.py",
                    "backend/app/core/monitoring_backup.py",
                    "backend/app/core/comprehensive_monitoring.py",
                    "backend/app/core/production_monitoring.py"
                ],
                "consolidated_files": ["backend/app/core/monitoring.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            },
            {
                "name": "Create performance metrics service",
                "description": "Consolidate performance metrics into performance_metrics.py",
                "original_files": [
                    "backend/app/core/performance_metrics.py",
                    "backend/app/core/performance_monitor.py",
                    "backend/app/core/performance_optimizer.py"
                ],
                "consolidated_files": ["backend/app/core/performance_metrics.py"],
                "mapping_type": MappingType.MANY_TO_ONE
            }
        ]
    },
    
    # Week 8: Cleanup
    {
        "name": "Configuration Files Consolidation",
        "description": "Consolidate configuration files",
        "week": 8,
        "consolidation_type": ConsolidationType.CONFIG_CONSOLIDATION,
        "steps": [
            {
                "name": "Unify environment configuration",
                "description": "Consolidate .env files into unified structure",
                "original_files": [
                    ".env",
                    ".env.development",
                    ".env.production",
                    ".env.testing",
                    ".env.example"
                ],
                "consolidated_files": [".env", ".env.example"],
                "mapping_type": MappingType.MANY_TO_ONE
            },
            {
                "name": "Streamline YAML configuration files",
                "description": "Consolidate YAML configuration files",
                "original_files": [
                    "config/backend.yaml",
                    "config/frontend.yaml",
                    "config/deployment.yaml",
                    "config/base.yaml"
                ],
                "consolidated_files": ["config/app.yaml", "config/deployment.yaml"],
                "mapping_type": MappingType.MANY_TO_ONE
            }
        ]
    },
    {
        "name": "Email Templates Consolidation",
        "description": "Consolidate email templates",
        "week": 8,
        "consolidation_type": ConsolidationType.FILE_MERGE,
        "steps": [
            {
                "name": "Unify email template location",
                "description": "Consolidate email templates into single location",
                "original_files": [
                    "backend/app/email_templates/",
                    "backend/app/templates/email/"
                ],
                "consolidated_files": ["backend/app/templates/email/"],
                "mapping_type": MappingType.MANY_TO_ONE
            }
        ]
    }
]


def get_predefined_phases() -> List[Dict[str, Any]]:
    """
    Get all predefined consolidation phases.
    
    Returns:
        List of predefined phase configurations
    """
    return CONSOLIDATION_PHASES


def get_phases_by_week(week: int) -> List[Dict[str, Any]]:
    """
    Get predefined phases for a specific week.
    
    Args:
        week: Week number (1-8)
        
    Returns:
        List of phases for the specified week
    """
    return [phase for phase in CONSOLIDATION_PHASES if phase["week"] == week]


def get_phase_by_name(name: str) -> Dict[str, Any]:
    """
    Get a predefined phase by name.
    
    Args:
        name: Phase name
        
    Returns:
        Phase configuration if found, empty dict otherwise
    """
    for phase in CONSOLIDATION_PHASES:
        if phase["name"] == name:
            return phase
    return {}


def create_all_predefined_phases(manager) -> List[str]:
    """
    Create all predefined phases in the consolidation manager.
    
    Args:
        manager: ConsolidationManager instance
        
    Returns:
        List of created phase IDs
    """
    phase_ids = []
    
    for phase_config in CONSOLIDATION_PHASES:
        phase_id = manager.create_consolidation_phase(
            name=phase_config["name"],
            description=phase_config["description"],
            week=phase_config["week"],
            consolidation_type=phase_config["consolidation_type"]
        )
        
        # Add steps to the phase
        for step_config in phase_config["steps"]:
            manager.tracker.add_step_to_phase(
                phase_id=phase_id,
                name=step_config["name"],
                description=step_config["description"],
                files_affected=step_config["original_files"]
            )
        
        phase_ids.append(phase_id)
    
    return phase_ids