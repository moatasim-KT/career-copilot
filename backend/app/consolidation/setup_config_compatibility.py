#!/usr/bin/env python3
"""
Setup configuration import compatibility mappings.

This script sets up the compatibility layer for configuration consolidation,
mapping old import paths to new consolidated modules.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from consolidation.compatibility_layer import get_compatibility_layer


def setup_configuration_mappings():
    """Setup import mappings for configuration consolidation."""
    layer = get_compatibility_layer()
    
    # Configuration mappings
    config_mappings = [
        # config_loader.py mappings
        {
            "old_module": "config.config_loader",
            "new_module": "app.core.config",
            "deprecation_message": "config.config_loader has been consolidated into app.core.config. Please update your imports.",
            "removal_version": "2.0.0"
        },
        {
            "old_module": "config.config_loader",
            "new_module": "app.core.config",
            "old_attribute": "get_config",
            "new_attribute": "get_config_value",
            "deprecation_message": "get_config from config.config_loader is now get_config_value in app.core.config",
            "removal_version": "2.0.0"
        },
        {
            "old_module": "config.config_loader",
            "new_module": "app.core.config",
            "old_attribute": "get_backend_config",
            "new_attribute": "get_config_value",
            "deprecation_message": "get_backend_config from config.config_loader is now get_config_value in app.core.config",
            "removal_version": "2.0.0"
        },
        
        # config_manager.py mappings
        {
            "old_module": "app.core.config_manager",
            "new_module": "app.core.config",
            "deprecation_message": "app.core.config_manager has been consolidated into app.core.config. Please update your imports.",
            "removal_version": "2.0.0"
        },
        {
            "old_module": "app.core.config_manager",
            "new_module": "app.core.config",
            "old_attribute": "get_config_manager",
            "new_attribute": "get_config_manager",
            "deprecation_message": "get_config_manager is now available in app.core.config",
            "removal_version": "2.0.0"
        },
        {
            "old_module": "app.core.config_manager",
            "new_module": "app.core.config",
            "old_attribute": "initialize_configuration",
            "new_attribute": "initialize_configuration",
            "deprecation_message": "initialize_configuration is now available in app.core.config",
            "removal_version": "2.0.0"
        },
        {
            "old_module": "app.core.config_manager",
            "new_module": "app.core.config",
            "old_attribute": "DeploymentMode",
            "new_attribute": "DeploymentMode",
            "deprecation_message": "DeploymentMode is now available in app.core.config",
            "removal_version": "2.0.0"
        },
        
        # config_validator.py mappings
        {
            "old_module": "app.core.config_validator",
            "new_module": "app.core.config",
            "deprecation_message": "app.core.config_validator has been consolidated into app.core.config. Please update your imports.",
            "removal_version": "2.0.0"
        },
        {
            "old_module": "app.core.config_validator",
            "new_module": "app.core.config",
            "old_attribute": "validate_configuration",
            "new_attribute": "validate_configuration",
            "deprecation_message": "validate_configuration is now available in app.core.config",
            "removal_version": "2.0.0"
        },
        
        # environment_config.py mappings
        {
            "old_module": "app.core.environment_config",
            "new_module": "app.core.config_advanced",
            "deprecation_message": "app.core.environment_config has been consolidated into app.core.config_advanced. Please update your imports.",
            "removal_version": "2.0.0"
        },
        {
            "old_module": "app.core.environment_config",
            "new_module": "app.core.config_advanced",
            "old_attribute": "get_environment_config_manager",
            "new_attribute": "get_environment_config_manager",
            "deprecation_message": "get_environment_config_manager is now available in app.core.config_advanced",
            "removal_version": "2.0.0"
        },
        {
            "old_module": "app.core.environment_config",
            "new_module": "app.core.config_advanced",
            "old_attribute": "setup_environment",
            "new_attribute": "setup_environment",
            "deprecation_message": "setup_environment is now available in app.core.config_advanced",
            "removal_version": "2.0.0"
        }
    ]
    
    # Add all mappings
    layer.add_batch_mappings(config_mappings)
    
    print(f"✅ Added {len(config_mappings)} configuration import mappings")
    return layer


if __name__ == "__main__":
    setup_configuration_mappings()