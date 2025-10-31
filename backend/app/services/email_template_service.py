"""
DEPRECATED: This module is deprecated and will be removed in a future version.

This file has been consolidated into email_template_manager.py which provides
all the functionality of this service plus additional features like:
- Notification batching and optimization
- Advanced caching strategies
- Template analytics
- Smart rate limiting

Please update your imports:
    OLD: from app.services.email_template_service import EnhancedEmailTemplateService
    NEW: from app.services.email_template_manager import EmailTemplateManager

For backward compatibility, this module re-exports EmailTemplateManager as
EnhancedEmailTemplateService and EmailTemplateService.

Deprecation Date: October 29, 2025
Removal Target: Q1 2026
"""

import warnings
from .email_template_manager import (
    EmailTemplateManager,
    TemplateType,
    TemplateStatus,
    TemplateCategory,
    TemplateFormat,
    NotificationPriority,
    BatchingStrategy,
    EmailTemplate,
)

# Show deprecation warning when this module is imported
warnings.warn(
    "email_template_service module is deprecated and will be removed in a future version. "
    "Please use email_template_manager.EmailTemplateManager instead.",
    DeprecationWarning,
    stacklevel=2
)

# Backward compatibility aliases
EnhancedEmailTemplateService = EmailTemplateManager
EmailTemplateService = EmailTemplateManager

__all__ = [
    "EmailTemplateManager",
    "EnhancedEmailTemplateService",
    "EmailTemplateService",
    "TemplateType",
    "TemplateStatus",
    "TemplateCategory",
    "TemplateFormat",
    "NotificationPriority",
    "BatchingStrategy",
    "EmailTemplate",
]
