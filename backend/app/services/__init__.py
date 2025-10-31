"""
Services package - Business logic and external service integrations.

Phase 1 consolidation note:
- Avoid importing submodules at package import time to keep the package import-safe,
  even if individual services contain experimental or WIP code.
- Consumers should import concrete services directly, e.g.:
    from app.services.scheduled_notification_service import scheduled_notification_service
    from app.services.email_service import EmailService

This prevents cyclic/early imports and allows partial usage of the package while
other modules are under development.
"""

# Intentionally do not import submodules here.
# Submodules can be imported directly by consumers as needed.

__all__: list[str] = []
