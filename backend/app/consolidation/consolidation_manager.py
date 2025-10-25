"""
Main consolidation manager that coordinates all consolidation systems.

This module provides a unified interface for managing the entire
consolidation process, coordinating backup, tracking, mapping, and
compatibility systems.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .backup_system import BackupSystem
from .compatibility_layer import CompatibilityLayer
from .tracking_system import ConsolidationTracker, ConsolidationType, ConsolidationStatus
from .file_mapping import FileMappingSystem, MappingType

logger = logging.getLogger(__name__)


class ConsolidationManager:
    """Main manager for coordinating consolidation operations."""
    
    def __init__(self, data_root: str = "data/consolidation_backups"):
        """
        Initialize consolidation manager.
        
        Args:
            data_root: Root directory for consolidation data
        """
        self.data_root = Path(data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)
        
        # Initialize subsystems
        self.backup_system = BackupSystem(str(self.data_root))
        self.compatibility_layer = CompatibilityLayer(str(self.data_root / "import_mappings.json"))
        self.tracker = ConsolidationTracker(str(self.data_root / "consolidation_tracking.json"))
        self.file_mapper = FileMappingSystem(str(self.data_root / "file_mappings.json"))
        
        logger.info("Initialized consolidation manager")
    
    def initialize_consolidation_project(self, total_files_before: int) -> None:
        """
        Initialize the consolidation project.
        
        Args:
            total_files_before: Total number of files before consolidation
        """
        self.tracker.initialize_project(total_files_before)
        self.compatibility_layer.activate()
        
        logger.info(f"Initialized consolidation project with {total_files_before} files")
    
    def create_consolidation_phase(
        self,
        name: str,
        description: str,
        week: int,
        consolidation_type: ConsolidationType
    ) -> str:
        """
        Create a new consolidation phase.
        
        Args:
            name: Phase name
            description: Phase description
            week: Week number
            consolidation_type: Type of consolidation
            
        Returns:
            Phase ID
        """
        phase_id = self.tracker.create_phase(name, description, week, consolidation_type)
        logger.info(f"Created consolidation phase: {name}")
        return phase_id
    
    def start_consolidation_step(
        self,
        phase_id: str,
        step_name: str,
        step_description: str,
        files_to_consolidate: List[str],
        consolidated_files: List[str],
        mapping_type: MappingType
    ) -> Dict[str, str]:
        """
        Start a consolidation step.
        
        Args:
            phase_id: ID of the phase
            step_name: Name of the step
            step_description: Description of the step
            files_to_consolidate: List of files to consolidate
            consolidated_files: List of consolidated files
            mapping_type: Type of file mapping
            
        Returns:
            Dictionary with step_id and mapping_id
        """
        # Add step to phase
        step_id = self.tracker.add_step_to_phase(
            phase_id, step_name, step_description, files_to_consolidate
        )
        
        # Start the step
        self.tracker.start_step(phase_id, step_id)
        
        # Create backups for original files
        phase = self.tracker.get_phase(phase_id)
        backup_results = self.backup_system.create_batch_backup(
            files_to_consolidate, phase.name if phase else "unknown"
        )
        
        backup_ids = [backup_id for backup_id in backup_results.values() if backup_id is not None]
        
        # Create file mapping
        mapping_id = self.file_mapper.create_mapping(
            original_files=files_to_consolidate,
            consolidated_files=consolidated_files,
            mapping_type=mapping_type,
            consolidation_phase=phase.name if phase else "unknown",
            backup_ids=backup_ids,
            notes=f"Step: {step_name}"
        )
        
        logger.info(f"Started consolidation step: {step_name} (Step ID: {step_id}, Mapping ID: {mapping_id})")
        
        return {
            "step_id": step_id,
            "mapping_id": mapping_id,
            "backup_ids": backup_ids
        }
    
    def complete_consolidation_step(
        self,
        phase_id: str,
        step_id: str,
        mapping_id: str,
        import_changes: Optional[List[Dict]] = None
    ) -> None:
        """
        Complete a consolidation step.
        
        Args:
            phase_id: ID of the phase
            step_id: ID of the step
            mapping_id: ID of the file mapping
            import_changes: List of import changes made
        """
        # Add import changes to mapping
        if import_changes:
            for change in import_changes:
                self.file_mapper.add_import_change(
                    mapping_id=mapping_id,
                    old_import=change["old_import"],
                    new_import=change["new_import"],
                    import_type=change["import_type"],
                    line_number=change.get("line_number")
                )
                
                # Add to compatibility layer
                self.compatibility_layer.add_mapping(
                    old_module=change["old_module"],
                    new_module=change["new_module"],
                    old_attribute=change.get("old_attribute"),
                    new_attribute=change.get("new_attribute"),
                    deprecation_message=change.get("deprecation_message"),
                    removal_version=change.get("removal_version")
                )
        
        # Get backup IDs from mapping
        mapping = self.file_mapper.get_mapping(mapping_id)
        backup_ids = mapping.backup_ids if mapping else []
        
        # Complete the step
        self.tracker.complete_step(phase_id, step_id, backup_ids)
        
        logger.info(f"Completed consolidation step: {step_id}")
    
    def fail_consolidation_step(
        self,
        phase_id: str,
        step_id: str,
        error_message: str
    ) -> None:
        """
        Mark a consolidation step as failed.
        
        Args:
            phase_id: ID of the phase
            step_id: ID of the step
            error_message: Error message
        """
        self.tracker.fail_step(phase_id, step_id, error_message)
        logger.error(f"Consolidation step failed: {step_id} - {error_message}")
    
    def rollback_consolidation_phase(self, phase_id: str) -> bool:
        """
        Rollback a consolidation phase.
        
        Args:
            phase_id: ID of the phase to rollback
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get backup IDs from tracker
            backup_ids = self.tracker.rollback_phase(phase_id)
            
            # Restore backups
            success_count = 0
            for backup_id in backup_ids:
                if self.backup_system.restore_backup(backup_id):
                    success_count += 1
            
            logger.info(f"Rolled back phase {phase_id}: restored {success_count}/{len(backup_ids)} backups")
            return success_count == len(backup_ids)
            
        except Exception as e:
            logger.error(f"Failed to rollback phase {phase_id}: {e}")
            return False
    
    def get_consolidation_progress(self) -> Dict[str, Any]:
        """
        Get overall consolidation progress.
        
        Returns:
            Progress information
        """
        overall_progress = self.tracker.get_overall_progress()
        mapping_stats = self.file_mapper.get_mapping_statistics()
        backup_stats = self.backup_system.get_backup_statistics()
        usage_stats = self.compatibility_layer.get_usage_statistics()
        
        return {
            "overall_progress": overall_progress,
            "mapping_statistics": mapping_stats,
            "backup_statistics": backup_stats,
            "compatibility_usage": len(usage_stats),
            "generated_at": datetime.now().isoformat()
        }
    
    def generate_consolidation_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive consolidation report.
        
        Returns:
            Detailed consolidation report
        """
        progress_report = self.tracker.generate_progress_report()
        migration_report = self.compatibility_layer.generate_migration_report()
        mapping_stats = self.file_mapper.get_mapping_statistics()
        backup_stats = self.backup_system.get_backup_statistics()
        
        return {
            "report_generated_at": datetime.now().isoformat(),
            "progress": progress_report,
            "migration": migration_report,
            "mappings": mapping_stats,
            "backups": backup_stats,
            "summary": {
                "total_phases": len(self.tracker.phases),
                "completed_phases": sum(1 for p in self.tracker.phases.values() if p.status == ConsolidationStatus.COMPLETED),
                "total_mappings": len(self.file_mapper.mappings),
                "total_backups": len(self.backup_system.backups),
                "compatibility_mappings": len(self.compatibility_layer.mappings)
            }
        }
    
    def validate_consolidation_state(self) -> Dict[str, Any]:
        """
        Validate the current state of consolidation.
        
        Returns:
            Validation results
        """
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "mapping_validations": {},
            "backup_validations": {}
        }
        
        # Validate all mappings
        for mapping_id in self.file_mapper.mappings:
            mapping_validation = self.file_mapper.validate_mapping(mapping_id)
            validation_results["mapping_validations"][mapping_id] = mapping_validation
            
            if not mapping_validation["valid"]:
                validation_results["valid"] = False
                validation_results["errors"].extend(mapping_validation.get("errors", []))
            
            validation_results["warnings"].extend(mapping_validation.get("warnings", []))
        
        # Check backup integrity
        for backup_id, backup_metadata in self.backup_system.backups.items():
            backup_path = Path(backup_metadata.backup_path)
            if not backup_path.exists():
                validation_results["valid"] = False
                validation_results["errors"].append(f"Backup file missing: {backup_path}")
        
        return validation_results
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> Dict[str, int]:
        """
        Clean up old consolidation data.
        
        Args:
            days_to_keep: Number of days to keep data
            
        Returns:
            Cleanup statistics
        """
        backup_cleanup = self.backup_system.cleanup_old_backups(days_to_keep)
        
        # Clear old usage statistics
        self.compatibility_layer.clear_usage_statistics()
        
        return {
            "backups_cleaned": backup_cleanup,
            "usage_stats_cleared": True
        }
    
    def finalize_consolidation_project(self, total_files_after: int) -> None:
        """
        Finalize the consolidation project.
        
        Args:
            total_files_after: Total number of files after consolidation
        """
        self.tracker.finalize_project(total_files_after)
        
        # Deactivate compatibility layer (optional - can be done manually)
        # self.compatibility_layer.deactivate()
        
        logger.info(f"Finalized consolidation project: {total_files_after} files remaining")
    
    def export_consolidation_data(self, export_dir: str) -> None:
        """
        Export all consolidation data.
        
        Args:
            export_dir: Directory to export data to
        """
        export_path = Path(export_dir)
        export_path.mkdir(parents=True, exist_ok=True)
        
        # Export mappings
        self.file_mapper.export_mappings(str(export_path / "file_mappings.json"))
        
        # Export progress report
        report = self.generate_consolidation_report()
        with open(export_path / "consolidation_report.json", 'w') as f:
            import json
            json.dump(report, f, indent=2)
        
        logger.info(f"Exported consolidation data to {export_dir}")


# Global consolidation manager instance
_consolidation_manager: Optional[ConsolidationManager] = None


def get_consolidation_manager() -> ConsolidationManager:
    """Get the global consolidation manager instance."""
    global _consolidation_manager
    if _consolidation_manager is None:
        _consolidation_manager = ConsolidationManager()
    return _consolidation_manager