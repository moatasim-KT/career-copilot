"""
Command-line interface for consolidation management.

This module provides CLI commands for managing the consolidation process,
including initialization, progress tracking, and rollback operations.
"""

import click
import json
import logging
from pathlib import Path
from typing import List, Optional

from .consolidation_manager import get_consolidation_manager
from .tracking_system import ConsolidationType
from .file_mapping import MappingType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@click.group()
def consolidation():
    """Consolidation management CLI."""
    pass


@consolidation.command()
@click.option('--total-files', type=int, required=True, help='Total number of files before consolidation')
def init(total_files: int):
    """Initialize the consolidation project."""
    manager = get_consolidation_manager()
    manager.initialize_consolidation_project(total_files)
    click.echo(f"Initialized consolidation project with {total_files} files")


@consolidation.command()
@click.option('--name', required=True, help='Phase name')
@click.option('--description', required=True, help='Phase description')
@click.option('--week', type=int, required=True, help='Week number')
@click.option('--type', 'consolidation_type', 
              type=click.Choice(['file_merge', 'module_consolidation', 'service_consolidation', 'config_consolidation', 'test_consolidation']),
              required=True, help='Consolidation type')
def create_phase(name: str, description: str, week: int, consolidation_type: str):
    """Create a new consolidation phase."""
    manager = get_consolidation_manager()
    
    # Convert string to enum
    type_mapping = {
        'file_merge': ConsolidationType.FILE_MERGE,
        'module_consolidation': ConsolidationType.MODULE_CONSOLIDATION,
        'service_consolidation': ConsolidationType.SERVICE_CONSOLIDATION,
        'config_consolidation': ConsolidationType.CONFIG_CONSOLIDATION,
        'test_consolidation': ConsolidationType.TEST_CONSOLIDATION
    }
    
    phase_id = manager.create_consolidation_phase(
        name=name,
        description=description,
        week=week,
        consolidation_type=type_mapping[consolidation_type]
    )
    
    click.echo(f"Created phase: {name} (ID: {phase_id})")


@consolidation.command()
@click.option('--phase-id', required=True, help='Phase ID')
@click.option('--step-name', required=True, help='Step name')
@click.option('--step-description', required=True, help='Step description')
@click.option('--original-files', required=True, help='Comma-separated list of original files')
@click.option('--consolidated-files', required=True, help='Comma-separated list of consolidated files')
@click.option('--mapping-type', 
              type=click.Choice(['one_to_one', 'many_to_one', 'one_to_many', 'split_merge']),
              default='many_to_one', help='Mapping type')
def start_step(phase_id: str, step_name: str, step_description: str, 
               original_files: str, consolidated_files: str, mapping_type: str):
    """Start a consolidation step."""
    manager = get_consolidation_manager()
    
    # Parse file lists
    original_file_list = [f.strip() for f in original_files.split(',')]
    consolidated_file_list = [f.strip() for f in consolidated_files.split(',')]
    
    # Convert string to enum
    type_mapping = {
        'one_to_one': MappingType.ONE_TO_ONE,
        'many_to_one': MappingType.MANY_TO_ONE,
        'one_to_many': MappingType.ONE_TO_MANY,
        'split_merge': MappingType.SPLIT_MERGE
    }
    
    result = manager.start_consolidation_step(
        phase_id=phase_id,
        step_name=step_name,
        step_description=step_description,
        files_to_consolidate=original_file_list,
        consolidated_files=consolidated_file_list,
        mapping_type=type_mapping[mapping_type]
    )
    
    click.echo(f"Started step: {step_name}")
    click.echo(f"Step ID: {result['step_id']}")
    click.echo(f"Mapping ID: {result['mapping_id']}")
    click.echo(f"Backups created: {len(result['backup_ids'])}")


@consolidation.command()
@click.option('--phase-id', required=True, help='Phase ID')
@click.option('--step-id', required=True, help='Step ID')
@click.option('--mapping-id', required=True, help='Mapping ID')
@click.option('--import-changes', help='JSON file with import changes')
def complete_step(phase_id: str, step_id: str, mapping_id: str, import_changes: Optional[str]):
    """Complete a consolidation step."""
    manager = get_consolidation_manager()
    
    changes = None
    if import_changes and Path(import_changes).exists():
        with open(import_changes, 'r') as f:
            changes = json.load(f)
    
    manager.complete_consolidation_step(
        phase_id=phase_id,
        step_id=step_id,
        mapping_id=mapping_id,
        import_changes=changes
    )
    
    click.echo(f"Completed step: {step_id}")


@consolidation.command()
@click.option('--phase-id', required=True, help='Phase ID')
@click.option('--step-id', required=True, help='Step ID')
@click.option('--error-message', required=True, help='Error message')
def fail_step(phase_id: str, step_id: str, error_message: str):
    """Mark a consolidation step as failed."""
    manager = get_consolidation_manager()
    
    manager.fail_consolidation_step(
        phase_id=phase_id,
        step_id=step_id,
        error_message=error_message
    )
    
    click.echo(f"Marked step as failed: {step_id}")


@consolidation.command()
@click.option('--phase-id', required=True, help='Phase ID to rollback')
@click.confirmation_option(prompt='Are you sure you want to rollback this phase?')
def rollback(phase_id: str):
    """Rollback a consolidation phase."""
    manager = get_consolidation_manager()
    
    success = manager.rollback_consolidation_phase(phase_id)
    
    if success:
        click.echo(f"Successfully rolled back phase: {phase_id}")
    else:
        click.echo(f"Failed to rollback phase: {phase_id}", err=True)


@consolidation.command()
def progress():
    """Show consolidation progress."""
    manager = get_consolidation_manager()
    
    progress_data = manager.get_consolidation_progress()
    
    overall = progress_data['overall_progress']
    
    click.echo("=== Consolidation Progress ===")
    click.echo(f"Total phases: {overall['total_phases']}")
    click.echo(f"Completed phases: {overall['completed_phases']}")
    click.echo(f"Failed phases: {overall['failed_phases']}")
    click.echo(f"In progress phases: {overall['in_progress_phases']}")
    click.echo(f"Progress: {overall['progress_percentage']:.1f}%")
    click.echo(f"Files: {overall['current_files']}/{overall['total_files_before']} ({overall['overall_reduction_percentage']:.1f}% reduction)")
    
    if overall['duration_seconds']:
        hours = overall['duration_seconds'] / 3600
        click.echo(f"Duration: {hours:.1f} hours")


@consolidation.command()
@click.option('--output', help='Output file for the report')
def report(output: Optional[str]):
    """Generate a consolidation report."""
    manager = get_consolidation_manager()
    
    report_data = manager.generate_consolidation_report()
    
    if output:
        with open(output, 'w') as f:
            json.dump(report_data, f, indent=2)
        click.echo(f"Report saved to: {output}")
    else:
        click.echo(json.dumps(report_data, indent=2))


@consolidation.command()
def validate():
    """Validate the current consolidation state."""
    manager = get_consolidation_manager()
    
    validation = manager.validate_consolidation_state()
    
    if validation['valid']:
        click.echo("✓ Consolidation state is valid")
    else:
        click.echo("✗ Consolidation state has errors", err=True)
        
        for error in validation['errors']:
            click.echo(f"  ERROR: {error}", err=True)
    
    if validation['warnings']:
        click.echo("Warnings:")
        for warning in validation['warnings']:
            click.echo(f"  WARNING: {warning}")


@consolidation.command()
@click.option('--days', type=int, default=30, help='Days to keep data')
def cleanup(days: int):
    """Clean up old consolidation data."""
    manager = get_consolidation_manager()
    
    cleanup_stats = manager.cleanup_old_data(days)
    
    click.echo(f"Cleaned up {cleanup_stats['backups_cleaned']} old backups")
    if cleanup_stats['usage_stats_cleared']:
        click.echo("Cleared usage statistics")


@consolidation.command()
@click.option('--total-files', type=int, required=True, help='Total number of files after consolidation')
def finalize(total_files: int):
    """Finalize the consolidation project."""
    manager = get_consolidation_manager()
    
    manager.finalize_consolidation_project(total_files)
    click.echo(f"Finalized consolidation project with {total_files} files")


@consolidation.command()
@click.option('--export-dir', required=True, help='Directory to export data to')
def export(export_dir: str):
    """Export consolidation data."""
    manager = get_consolidation_manager()
    
    manager.export_consolidation_data(export_dir)
    click.echo(f"Exported consolidation data to: {export_dir}")


@consolidation.command()
def list_phases():
    """List all consolidation phases."""
    manager = get_consolidation_manager()
    
    phases = manager.tracker.list_phases()
    
    if not phases:
        click.echo("No phases found")
        return
    
    click.echo("=== Consolidation Phases ===")
    for phase in phases:
        status_icon = {
            'not_started': '○',
            'in_progress': '◐',
            'completed': '●',
            'failed': '✗',
            'rolled_back': '↶'
        }.get(phase.status.value, '?')
        
        click.echo(f"{status_icon} {phase.name} (Week {phase.week})")
        click.echo(f"   ID: {phase.phase_id}")
        click.echo(f"   Type: {phase.consolidation_type.value}")
        click.echo(f"   Status: {phase.status.value}")
        click.echo(f"   Steps: {len(phase.steps)}")
        
        if phase.files_before and phase.files_after:
            click.echo(f"   Files: {phase.files_before} → {phase.files_after} ({phase.reduction_percentage:.1f}% reduction)")
        
        click.echo()


@consolidation.command()
@click.option('--old-module', required=True, help='Old module path')
@click.option('--new-module', required=True, help='New module path')
@click.option('--old-attribute', help='Old attribute name')
@click.option('--new-attribute', help='New attribute name')
@click.option('--deprecation-message', help='Custom deprecation message')
@click.option('--removal-version', help='Version when old import will be removed')
def add_import_mapping(old_module: str, new_module: str, old_attribute: Optional[str],
                      new_attribute: Optional[str], deprecation_message: Optional[str],
                      removal_version: Optional[str]):
    """Add an import mapping to the compatibility layer."""
    manager = get_consolidation_manager()
    
    manager.compatibility_layer.add_mapping(
        old_module=old_module,
        new_module=new_module,
        old_attribute=old_attribute,
        new_attribute=new_attribute,
        deprecation_message=deprecation_message,
        removal_version=removal_version
    )
    
    click.echo(f"Added import mapping: {old_module} → {new_module}")


if __name__ == '__main__':
    consolidation()