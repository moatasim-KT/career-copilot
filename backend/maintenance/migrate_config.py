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

from app.core.config_advanced import (
    ConfigMigrator,
    migrate_legacy_configuration
)
from app.core.config import get_config_manager


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
            print(f"\u2713 Backed up {source} to {backup_path}")
    
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
            report_lines.append(f"  \u26a0 {warning}")
        report_lines.append("")
    
    if report.get('errors'):
        report_lines.append("Errors:")
        for error in report['errors']:
            report_lines.append(f"  \u2717 {error}")
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
    print(f"\u2713 Migration report saved to {report_file}")

# ... (rest of the file remains unchanged)
