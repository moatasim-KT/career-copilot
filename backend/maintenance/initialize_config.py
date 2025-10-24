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
        print(f"\u2713 Created directory: {directory}")


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
    print(f"\u2713 Detected deployment mode: {detected_mode.value}")
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
        print(f"\u2713 Configuration system initialized for {deployment_mode.value} mode")
        print(f"\u2713 Loaded {len(config_data)} configuration keys")
        
        # Start file watching for development
        if deployment_mode == DeploymentMode.DEVELOPMENT:
            config_manager = get_config_manager()
            config_manager.start_watching()
            print("\u2713 Started configuration file watching")
        
        return config_data
        
    except Exception as e:
        print(f"\u2717 Failed to initialize configuration system: {e}")
        raise


def create_env_template(deployment_mode: DeploymentMode):
    """Create environment file template for the deployment mode."""
    # ... (rest of the file remains unchanged)
