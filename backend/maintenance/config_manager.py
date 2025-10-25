#!/usr/bin/env python3
"""
Configuration Management CLI Tool.

This script provides command-line utilities for managing the enhanced configuration system.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

import yaml

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import (
    DeploymentMode,
    get_config_manager,
    initialize_configuration
)
from app.core.config_advanced import (
    get_template_manager,
    generate_config_for_deployment,
    initialize_configuration_system
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def init_config(args):
    """Initialize configuration for a deployment mode."""
    try:
        deployment_mode = DeploymentMode(args.mode)
        config_dir = Path(args.config_dir)
        
        print(f"Initializing configuration for {deployment_mode.value} mode...")
        
        # Generate configuration files
        success = generate_config_for_deployment(deployment_mode, config_dir)
        
        if success:
            print(f"\u2713 Configuration files generated in {config_dir}")
            print(f"  - {deployment_mode.value}.yaml")
            print(f"  - {deployment_mode.value}.env")
            
            # Show template requirements
            template_manager = get_template_manager()
            validation = template_manager.validate_template_requirements(deployment_mode.value)
            
            if validation.get("missing_required"):
                print("\n\u26a0 Required environment variables:")
                for var in validation["missing_required"]:
                    print(f"  - {var}")
            
            if validation.get("missing_optional"):
                print("\nOptional environment variables:")
                for var in validation["missing_optional"]:
                    print(f"  - {var}")
            
            if validation.get("recommendations"):
                print("\nRecommendations:")
                for rec in validation["recommendations"]:
                    print(f"  - {rec}")
        else:
            print("\u2717 Failed to generate configuration files")
            return 1
            
    except ValueError as e:
        print(f"\u2717 Invalid deployment mode: {args.mode}")
        print(f"Available modes: {', '.join([mode.value for mode in DeploymentMode])}")
        return 1
    except Exception as e:
        print(f"\u2717 Error initializing configuration: {e}")
        return 1
    
    return 0


def validate_config(args):
    """Validate configuration for a deployment mode."""
    try:
        deployment_mode = DeploymentMode(args.mode) if args.mode else None
        
        print("Validating configuration...")
        
        # Initialize configuration
        config_data = initialize_configuration(deployment_mode)
        config_manager = get_config_manager()
        
        print("\u2713 Configuration loaded successfully")
        print(f"  Deployment mode: {config_manager.deployment_mode.value}")
        print(f"  Configuration sources: {len(config_manager.config_sources)}")
        print(f"  Configuration keys: {len(config_data)}")
        
        # Validate template requirements if mode specified
        if args.mode:
            template_manager = get_template_manager()
            validation = template_manager.validate_template_requirements(deployment_mode.value)
            
            if validation.get("missing_required"):
                print("\n\u26a0 Required environment variables:")
                for var in validation["missing_required"]:
                    print(f"  - {var}")
            
            if validation.get("missing_optional"):
                print("\nOptional environment variables:")
                for var in validation["missing_optional"]:
                    print(f"  - {var}")
            
            if validation.get("recommendations"):
                print("\nRecommendations:")
                for rec in validation["recommendations"]:
                    print(f"  - {rec}")
        
        print("\nConfiguration validation complete.")
        return 0
    except Exception as e:
        print(f"\u2717 Error validating configuration: {e}")
        return 1


def migrate_config(args):
    """Migrate legacy configuration to new format."""
    try:
        legacy_config_path = Path(args.legacy_config)
        output_path = Path(args.output)
        
        print(f"Migrating legacy configuration from {legacy_config_path}...")
        
        migrated = migrate_legacy_configuration(legacy_config_path, output_path)
        if migrated:
            print(f"\u2713 Legacy configuration migrated to {output_path}")
        else:
            print("\u2717 Migration failed")
            return 1
    except Exception as e:
        print(f"\u2717 Error migrating configuration: {e}")
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(description="Configuration Management CLI Tool")
    subparsers = parser.add_subparsers(dest="command")

    # Init config
    parser_init = subparsers.add_parser("init", help="Initialize configuration for a deployment mode")
    parser_init.add_argument("--mode", required=True, help="Deployment mode (dev, staging, prod)")
    parser_init.add_argument("--config-dir", required=True, help="Directory to store configuration files")
    parser_init.set_defaults(func=init_config)

    # Validate config
    parser_validate = subparsers.add_parser("validate", help="Validate configuration for a deployment mode")
    parser_validate.add_argument("--mode", required=False, help="Deployment mode (dev, staging, prod)")
    parser_validate.set_defaults(func=validate_config)

    # Migrate config
    parser_migrate = subparsers.add_parser("migrate", help="Migrate legacy configuration to new format")
    parser_migrate.add_argument("--legacy-config", required=True, help="Path to legacy configuration file")
    parser_migrate.add_argument("--output", required=True, help="Path to output migrated configuration file")
    parser_migrate.set_defaults(func=migrate_config)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        exit_code = args.func(args)
        sys.exit(exit_code)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
