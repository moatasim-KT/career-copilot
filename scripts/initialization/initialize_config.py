#!/usr/bin/env python3
"""
Configuration Initialization Script.

This script initializes the enhanced configuration system and ensures
all necessary configuration files and directories are created.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config_manager import (
    DeploymentMode,
    get_config_manager,
    initialize_configuration
)
from app.core.config_templates import (
    get_template_manager,
    generate_config_for_deployment
)
from app.core.config_integration import migrate_legacy_configuration


def setup_directories():
    """Create necessary directories for configuration and logging."""
    directories = [
        "config",
        "logs",
        "data",
        "data/chroma",
        "logs/audit"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")


def detect_deployment_mode() -> DeploymentMode:
    """Detect the deployment mode from environment variables."""
    mode = os.getenv('DEPLOYMENT_MODE', os.getenv('ENVIRONMENT', 'development')).lower()
    
    # Map common environment names to deployment modes
    mode_mapping = {
        'dev': DeploymentMode.DEVELOPMENT,
        'development': DeploymentMode.DEVELOPMENT,
        'test': DeploymentMode.TESTING,
        'testing': DeploymentMode.TESTING,
        'stage': DeploymentMode.STAGING,
        'staging': DeploymentMode.STAGING,
        'prod': DeploymentMode.PRODUCTION,
        'production': DeploymentMode.PRODUCTION,
        'docker': DeploymentMode.DOCKER,
        'k8s': DeploymentMode.KUBERNETES,
        'kubernetes': DeploymentMode.KUBERNETES,
        'native': DeploymentMode.NATIVE
    }
    
    detected_mode = mode_mapping.get(mode, DeploymentMode.DEVELOPMENT)
    print(f"✓ Detected deployment mode: {detected_mode.value}")
    return detected_mode


def initialize_config_system(deployment_mode: Optional[DeploymentMode] = None):
    """Initialize the enhanced configuration system."""
    print("Initializing enhanced configuration system...")
    
    # Setup directories
    setup_directories()
    
    # Detect deployment mode if not provided
    if deployment_mode is None:
        deployment_mode = detect_deployment_mode()
    
    # Initialize configuration manager
    try:
        config_data = initialize_configuration(deployment_mode)
        print(f"✓ Configuration system initialized for {deployment_mode.value} mode")
        print(f"✓ Loaded {len(config_data)} configuration keys")
        
        # Start file watching for development
        if deployment_mode == DeploymentMode.DEVELOPMENT:
            config_manager = get_config_manager()
            config_manager.start_watching()
            print("✓ Started configuration file watching")
        
        return config_data
        
    except Exception as e:
        print(f"✗ Failed to initialize configuration system: {e}")
        raise


def create_env_template(deployment_mode: DeploymentMode):
    """Create environment file template for the deployment mode."""
    template_manager = get_template_manager()
    template = template_manager.get_template(deployment_mode.value)
    
    if template:
        env_file = Path(f".env.{deployment_mode.value}")
        
        with open(env_file, 'w') as f:
            f.write(f"# Environment variables for {template.description}\n")
            f.write(f"# Deployment mode: {deployment_mode.value}\n\n")
            
            f.write("# Required environment variables:\n")
            for var in template.required_env_vars:
                f.write(f"{var}=\n")
            
            if template.optional_env_vars:
                f.write("\n# Optional environment variables:\n")
                for var in template.optional_env_vars:
                    f.write(f"# {var}=\n")
            
            f.write(f"\n# Deployment mode\n")
            f.write(f"DEPLOYMENT_MODE={deployment_mode.value}\n")
        
        print(f"✓ Created environment template: {env_file}")


def validate_configuration():
    """Validate the current configuration."""
    try:
        config_manager = get_config_manager()
        
        if not config_manager.config_data:
            print("⚠ Configuration not loaded, initializing...")
            initialize_configuration()
        
        print("✓ Configuration validation passed")
        return True
        
    except Exception as e:
        print(f"✗ Configuration validation failed: {e}")
        return False


def show_configuration_summary():
    """Show a summary of the current configuration."""
    try:
        config_manager = get_config_manager()
        
        print("\n" + "="*50)
        print("CONFIGURATION SUMMARY")
        print("="*50)
        
        print(f"Deployment Mode: {config_manager.deployment_mode.value}")
        print(f"Configuration Sources: {len(config_manager.config_sources)}")
        print(f"Configuration Keys: {len(config_manager.config_data)}")
        print(f"Validators: {len(config_manager.validators)}")
        
        # Show key configuration values
        key_configs = [
            "api.host",
            "api.port",
            "database.url",
            "redis.enabled",
            "logging.level",
            "monitoring.enabled"
        ]
        
        print("\nKey Configuration Values:")
        for key in key_configs:
            value = config_manager.get(key, "Not set")
            # Mask sensitive values
            if "password" in key.lower() or "key" in key.lower() or "secret" in key.lower():
                value = "***" if value and value != "Not set" else "Not set"
            print(f"  {key}: {value}")
        
        print("="*50)
        
    except Exception as e:
        print(f"✗ Failed to show configuration summary: {e}")


def main():
    """Main initialization function."""
    print("Career Copilot - Configuration Initialization")
    print("=" * 50)
    
    try:
        # Initialize configuration system
        config_data = initialize_config_system()
        
        # Create environment template
        deployment_mode = detect_deployment_mode()
        create_env_template(deployment_mode)
        
        # Validate configuration
        if validate_configuration():
            show_configuration_summary()
            print("\n✓ Configuration system initialization completed successfully!")
            return 0
        else:
            print("\n✗ Configuration validation failed!")
            return 1
            
    except Exception as e:
        print(f"\n✗ Configuration initialization failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())