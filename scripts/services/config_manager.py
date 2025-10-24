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
            print(f"✓ Configuration files generated in {config_dir}")
            print(f"  - {deployment_mode.value}.yaml")
            print(f"  - {deployment_mode.value}.env")
            
            # Show template requirements
            template_manager = get_template_manager()
            validation = template_manager.validate_template_requirements(deployment_mode.value)
            
            if validation.get("missing_required"):
                print("\n⚠ Required environment variables:")
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
            print("✗ Failed to generate configuration files")
            return 1
            
    except ValueError as e:
        print(f"✗ Invalid deployment mode: {args.mode}")
        print(f"Available modes: {', '.join([mode.value for mode in DeploymentMode])}")
        return 1
    except Exception as e:
        print(f"✗ Error initializing configuration: {e}")
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
        
        print("✓ Configuration loaded successfully")
        print(f"  Deployment mode: {config_manager.deployment_mode.value}")
        print(f"  Configuration sources: {len(config_manager.config_sources)}")
        print(f"  Configuration keys: {len(config_data)}")
        
        # Validate template requirements if mode specified
        if args.mode:
            template_manager = get_template_manager()
            validation = template_manager.validate_template_requirements(args.mode)
            
            if validation.get("missing_required"):
                print("\n⚠ Missing required environment variables:")
                for var in validation["missing_required"]:
                    print(f"  - {var}")
                return 1
            else:
                print("✓ All required environment variables are set")
        
        return 0
        
    except Exception as e:
        print(f"✗ Configuration validation failed: {e}")
        return 1


def show_config(args):
    """Show current configuration."""
    try:
        config_manager = get_config_manager()
        
        if not config_manager.config_data:
            initialize_configuration()
        
        if args.key:
            # Show specific key
            value = config_manager.get(args.key)
            if value is not None:
                if args.format == 'json':
                    print(json.dumps(value, indent=2))
                else:
                    print(f"{args.key}: {value}")
            else:
                print(f"Key '{args.key}' not found")
                return 1
        else:
            # Show all configuration
            if args.format == 'json':
                print(json.dumps(config_manager.config_data, indent=2))
            else:
                print(yaml.dump(config_manager.config_data, default_flow_style=False, indent=2))
        
        return 0
        
    except Exception as e:
        print(f"✗ Error showing configuration: {e}")
        return 1


def set_config_value(args):
    """Set a configuration value."""
    try:
        config_manager = get_config_manager()
        
        if not config_manager.config_data:
            initialize_configuration()
        
        # Parse value
        value = args.value
        if args.type == 'int':
            value = int(value)
        elif args.type == 'float':
            value = float(value)
        elif args.type == 'bool':
            value = value.lower() in ('true', '1', 'yes', 'on')
        elif args.type == 'json':
            value = json.loads(value)
        
        # Set value
        config_manager.set(args.key, value)
        print(f"✓ Set {args.key} = {value}")
        
        return 0
        
    except Exception as e:
        print(f"✗ Error setting configuration value: {e}")
        return 1


def list_templates(args):
    """List available configuration templates."""
    try:
        template_manager = get_template_manager()
        templates = template_manager.list_templates()
        
        print("Available configuration templates:")
        for template_name in templates:
            template = template_manager.get_template(template_name)
            print(f"  {template_name}: {template.description}")
        
        return 0
        
    except Exception as e:
        print(f"✗ Error listing templates: {e}")
        return 1


def migrate_config(args):
    """Migrate legacy configuration to enhanced system."""
    try:
        print("Migrating legacy configuration...")
        
        report = migrate_legacy_configuration()
        
        print("✓ Migration completed")
        print(f"  Status: {report['migration_status']}")
        print(f"  Legacy fields migrated: {report['legacy_fields_migrated']}")
        print(f"  Enhanced fields created: {report['enhanced_fields_created']}")
        
        if report.get('warnings'):
            print("\nWarnings:")
            for warning in report['warnings']:
                print(f"  ⚠ {warning}")
        
        if report.get('errors'):
            print("\nErrors:")
            for error in report['errors']:
                print(f"  ✗ {error}")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return 1


def watch_config(args):
    """Watch configuration files for changes."""
    try:
        print("Starting configuration file watcher...")
        
        config_manager = get_config_manager()
        if not config_manager.config_data:
            initialize_configuration()
        
        config_manager.start_watching()
        
        print("✓ Watching configuration files for changes")
        print("Press Ctrl+C to stop...")
        
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping configuration watcher...")
            config_manager.stop_watching()
            print("✓ Configuration watcher stopped")
        
        return 0
        
    except Exception as e:
        print(f"✗ Error watching configuration: {e}")
        return 1


def export_config(args):
    """Export configuration to file."""
    try:
        config_manager = get_config_manager()
        
        if not config_manager.config_data:
            initialize_configuration()
        
        output_path = Path(args.output)
        
        # Determine format from file extension if not specified
        if not args.format:
            if output_path.suffix == '.json':
                args.format = 'json'
            else:
                args.format = 'yaml'
        
        # Export configuration
        if args.format == 'json':
            config_str = json.dumps(config_manager.config_data, indent=2)
        else:
            config_str = yaml.dump(config_manager.config_data, default_flow_style=False, indent=2)
        
        with open(output_path, 'w') as f:
            f.write(config_str)
        
        print(f"✓ Configuration exported to {output_path}")
        return 0
        
    except Exception as e:
        print(f"✗ Error exporting configuration: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Configuration Management CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize configuration for deployment mode')
    init_parser.add_argument('mode', choices=[mode.value for mode in DeploymentMode],
                           help='Deployment mode')
    init_parser.add_argument('--config-dir', default='./config',
                           help='Configuration directory (default: ./config)')
    init_parser.set_defaults(func=init_config)
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate configuration')
    validate_parser.add_argument('--mode', choices=[mode.value for mode in DeploymentMode],
                               help='Deployment mode to validate against')
    validate_parser.set_defaults(func=validate_config)
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show configuration')
    show_parser.add_argument('--key', help='Specific configuration key to show')
    show_parser.add_argument('--format', choices=['yaml', 'json'], default='yaml',
                           help='Output format')
    show_parser.set_defaults(func=show_config)
    
    # Set command
    set_parser = subparsers.add_parser('set', help='Set configuration value')
    set_parser.add_argument('key', help='Configuration key (dot notation)')
    set_parser.add_argument('value', help='Configuration value')
    set_parser.add_argument('--type', choices=['str', 'int', 'float', 'bool', 'json'],
                          default='str', help='Value type')
    set_parser.set_defaults(func=set_config_value)
    
    # Templates command
    templates_parser = subparsers.add_parser('templates', help='List available templates')
    templates_parser.set_defaults(func=list_templates)
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Migrate legacy configuration')
    migrate_parser.set_defaults(func=migrate_config)
    
    # Watch command
    watch_parser = subparsers.add_parser('watch', help='Watch configuration files for changes')
    watch_parser.set_defaults(func=watch_config)
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export configuration to file')
    export_parser.add_argument('output', help='Output file path')
    export_parser.add_argument('--format', choices=['yaml', 'json'],
                             help='Output format (auto-detected from extension)')
    export_parser.set_defaults(func=export_config)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    try:
        return args.func(args)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())