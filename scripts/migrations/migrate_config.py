#!/usr/bin/env python3
"""
Configuration Migration Script.

This script migrates from the legacy Pydantic-based configuration
to the new enhanced configuration system.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config_integration import (
    ConfigMigrator,
    migrate_legacy_configuration
)
from app.core.config_manager import get_config_manager


def backup_current_config():
    """Backup current configuration files."""
    backup_dir = Path("config/backup")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    config_files = [
        ".env",
        "config/base.yaml",
        "config/development.yaml",
        "config/production.yaml"
    ]
    
    backed_up = []
    
    for config_file in config_files:
        source = Path(config_file)
        if source.exists():
            backup_path = backup_dir / source.name
            
            # Add timestamp if backup already exists
            if backup_path.exists():
                import time
                timestamp = int(time.time())
                backup_path = backup_dir / f"{source.stem}_{timestamp}{source.suffix}"
            
            import shutil
            shutil.copy2(source, backup_path)
            backed_up.append(str(backup_path))
            print(f"✓ Backed up {source} to {backup_path}")
    
    return backed_up


def create_migration_report(report: Dict[str, Any]) -> str:
    """Create a detailed migration report."""
    report_lines = [
        "Configuration Migration Report",
        "=" * 40,
        f"Status: {report['migration_status']}",
        f"Legacy fields migrated: {report['legacy_fields_migrated']}",
        f"Enhanced fields created: {report['enhanced_fields_created']}",
        ""
    ]
    
    if report.get('warnings'):
        report_lines.append("Warnings:")
        for warning in report['warnings']:
            report_lines.append(f"  ⚠ {warning}")
        report_lines.append("")
    
    if report.get('errors'):
        report_lines.append("Errors:")
        for error in report['errors']:
            report_lines.append(f"  ✗ {error}")
        report_lines.append("")
    
    # Add recommendations
    report_lines.extend([
        "Post-Migration Steps:",
        "1. Review the migrated configuration values",
        "2. Update environment variables as needed",
        "3. Test the application with the new configuration",
        "4. Remove backup files once migration is confirmed working",
        ""
    ])
    
    return "\n".join(report_lines)


def save_migration_report(report: Dict[str, Any]):
    """Save migration report to file."""
    report_content = create_migration_report(report)
    
    # Save to file
    report_file = Path("config/migration_report.txt")
    with open(report_file, 'w') as f:
        f.write(report_content)
    
    print(f"✓ Migration report saved to {report_file}")
    
    # Also save as JSON for programmatic access
    json_report_file = Path("config/migration_report.json")
    with open(json_report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✓ Migration report (JSON) saved to {json_report_file}")


def verify_migration():
    """Verify that the migration was successful."""
    try:
        config_manager = get_config_manager()
        
        # Check if configuration loads
        if not config_manager.config_data:
            from app.core.config_manager import initialize_configuration
            initialize_configuration()
        
        # Check key configuration values
        key_checks = [
            ("api.host", "API host configuration"),
            ("api.port", "API port configuration"),
            ("ai.openai.api_key", "OpenAI API key"),
            ("database.url", "Database URL"),
            ("logging.level", "Logging level")
        ]
        
        missing_configs = []
        for key, description in key_checks:
            value = config_manager.get(key)
            if value is None:
                missing_configs.append(f"{description} ({key})")
        
        if missing_configs:
            print("⚠ Migration verification warnings:")
            for missing in missing_configs:
                print(f"  - {missing} is not set")
            return False
        else:
            print("✓ Migration verification passed")
            return True
            
    except Exception as e:
        print(f"✗ Migration verification failed: {e}")
        return False


def interactive_migration():
    """Run interactive migration with user prompts."""
    print("Interactive Configuration Migration")
    print("=" * 40)
    
    # Check if backup should be created
    response = input("Create backup of current configuration? (Y/n): ").strip().lower()
    if response != 'n':
        backup_files = backup_current_config()
        print(f"✓ Created {len(backup_files)} backup files")
    
    # Confirm migration
    response = input("Proceed with migration? (Y/n): ").strip().lower()
    if response == 'n':
        print("Migration cancelled")
        return 1
    
    try:
        # Run migration
        print("Running configuration migration...")
        report = migrate_legacy_configuration()
        
        # Save report
        save_migration_report(report)
        
        # Print summary
        print("\nMigration Summary:")
        print(f"  Status: {report['migration_status']}")
        print(f"  Legacy fields: {report['legacy_fields_migrated']}")
        print(f"  Enhanced fields: {report['enhanced_fields_created']}")
        
        if report.get('warnings'):
            print(f"  Warnings: {len(report['warnings'])}")
        
        if report.get('errors'):
            print(f"  Errors: {len(report['errors'])}")
            return 1
        
        # Verify migration
        print("\nVerifying migration...")
        if verify_migration():
            print("✓ Migration completed successfully!")
            
            # Show next steps
            print("\nNext Steps:")
            print("1. Review the migration report in config/migration_report.txt")
            print("2. Test your application with the new configuration")
            print("3. Update any custom configuration as needed")
            
            return 0
        else:
            print("⚠ Migration completed with warnings")
            return 1
            
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return 1


def automatic_migration():
    """Run automatic migration without user interaction."""
    print("Automatic Configuration Migration")
    print("=" * 40)
    
    try:
        # Create backup
        backup_files = backup_current_config()
        print(f"✓ Created {len(backup_files)} backup files")
        
        # Run migration
        print("Running configuration migration...")
        report = migrate_legacy_configuration()
        
        # Save report
        save_migration_report(report)
        
        # Verify migration
        if verify_migration():
            print("✓ Automatic migration completed successfully!")
            return 0
        else:
            print("⚠ Automatic migration completed with warnings")
            return 1
            
    except Exception as e:
        print(f"✗ Automatic migration failed: {e}")
        return 1


def main():
    """Main migration function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Configuration Migration Tool")
    parser.add_argument(
        "--auto", 
        action="store_true", 
        help="Run automatic migration without prompts"
    )
    parser.add_argument(
        "--verify-only", 
        action="store_true", 
        help="Only verify existing migration"
    )
    
    args = parser.parse_args()
    
    if args.verify_only:
        print("Verifying existing migration...")
        return 0 if verify_migration() else 1
    elif args.auto:
        return automatic_migration()
    else:
        return interactive_migration()


if __name__ == '__main__':
    sys.exit(main())