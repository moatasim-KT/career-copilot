"""
Feature Flag Service for managing feature flags and rollouts.
"""

import json
from typing import Dict, Any, Optional
from ..core.config import get_settings

class FeatureFlagService:
    """Service for managing feature flags."""

    def __init__(self):
        self.settings = get_settings()
        self.flags = self._load_flags()

    def _load_flags(self) -> Dict[str, Any]:
        """Load feature flags from a file."""
        try:
            with open(self.settings.feature_flags_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def is_enabled(self, feature_name: str, user_id: Optional[str] = None) -> bool:
        """Check if a feature is enabled."""
        feature = self.flags.get(feature_name)
        if not feature:
            return False

        if not feature.get("enabled", False):
            return False

        if user_id and feature.get("users") and user_id not in feature["users"]:
            return False

        return True

_service = None

def get_feature_flag_service() -> "FeatureFlagService":
    """Get the feature flag service."""
    global _service
    if _service is None:
        _service = FeatureFlagService()
    return _service
