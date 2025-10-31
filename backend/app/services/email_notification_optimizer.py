"""
DEPRECATED: This module is deprecated and will be removed in a future version.

This file has been consolidated into email_template_manager.py which provides
all the functionality of this service plus additional features:

Functionality Available in EmailTemplateManager:
- Notification queuing with priority levels (CRITICAL, HIGH, NORMAL, LOW, BULK)
- Smart batching strategies (time-based, recipient-based, template-based, priority-based, smart)
- Rate limiting (per minute, per hour)
- Template rendering and caching
- Notification analytics and tracking
- Background batch processing
- Recipient preference management

Features Previously in This Service:
- DeliveryWindow configuration → Use scheduled_at in queue_notification
- SecurityConfiguration → Use email_service security features
- Spam filtering → Handled by email delivery services (SendGrid, AWS SES)
- Content scanning → Handled by email delivery services

Migration Guide:
    OLD:
        from app.services.email_notification_optimizer import EmailNotificationOptimizer
        optimizer = EmailNotificationOptimizer()
        await optimizer.initialize()
        notification_id = await optimizer.queue_notification(
            recipient="user@example.com",
            subject="Test",
            body_html="<h1>Test</h1>",
            priority=NotificationPriority.HIGH
        )
    
    NEW:
        from app.services.email_template_manager import EmailTemplateManager, NotificationPriority
        manager = EmailTemplateManager()
        await manager.initialize()
        notification_id = await manager.queue_notification(
            recipient="user@example.com",
            subject="Test",
            body_html="<h1>Test</h1>",
            priority=NotificationPriority.HIGH
        )

For backward compatibility, this module re-exports EmailTemplateManager and related classes.

Deprecation Date: October 29, 2025
Removal Target: Q1 2026
Service Consolidation: Phase 1 - Email Services
"""

import warnings
from .email_template_manager import (
    EmailTemplateManager,
    NotificationPriority,
    BatchingStrategy,
    BatchConfiguration,
    EmailNotification,
)

# Show deprecation warning when this module is imported
warnings.warn(
    "email_notification_optimizer module is deprecated and will be removed in a future version. "
    "Please use email_template_manager.EmailTemplateManager instead. "
    "See module docstring for migration guide.",
    DeprecationWarning,
    stacklevel=2
)

# Backward compatibility aliases
EmailNotificationOptimizer = EmailTemplateManager
EnhancedEmailNotificationOptimizer = EmailTemplateManager

# Note: DeliveryWindow and SecurityConfiguration classes were service-specific
# and are not re-exported. If you need delivery windows, use scheduled_at parameter.
# Security features are now handled by the underlying email delivery services.

__all__ = [
    "EmailNotificationOptimizer",
    "EnhancedEmailNotificationOptimizer",
    "EmailTemplateManager",
    "NotificationPriority",
    "BatchingStrategy",
    "BatchConfiguration",
    "EmailNotification",
]
