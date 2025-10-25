"""
File mapping system to track original to consolidated file relationships.

This module provides functionality to map original files to their consolidated
counterparts, track dependencies, and manage import path changes.
"""

import json
import logging
import os
import ast
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class MappingType(Enum):
    """Type of file mapping."""
    ONE_TO_ONE = "one_to_one"          # Single file to single file
    MANY_TO_ONE = "many_to_one"        # Multiple files to single file
    ONE_TO_MANY = "one_to_many"        # Single file to multiple files
    SPLIT_MERGE = "split_merge"        # Complex reorganization


@dataclass
class ImportChange:
    """Represents a change in import statement."""
    old_import: str
    new_import: str
    import_type: str  # "module", "from", "attribute"
    line_number: Optional[int] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ImportChange':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class FileMapping:
    """Mapping from original file(s) to consolidated file(s)."""
    mapping_id: str
    mapping_type: MappingType
    original_files: List[str]
    consolidated_files: List[str]
    consolidation_phase: str
    created_at: datetime
    dependencies: List[str]
    import_changes: List[ImportChange]
    backup_ids: List[str]
    notes: Optional[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.import_changes is None:
            self.import_changes = []
        if self.backup_ids is None:
            self.backup_ids = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['mapping_type'] = self.mapping_type.value
        data['created_at'] = self.created_at.isoformat()
        data['import_changes'] = [change.to_dict() for change in self.import_changes]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FileMapping':
        """Create from dictionary."""
        data['mapping_type'] = MappingType(data['mapping_type'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['import_changes'] = [ImportChange.from_dict(change_data) for change_data in data.get('import_changes', [])]
        return cls(**data)


class FileMappingSystem:
    """System for tracking file mappings and import changes."""
    
    def __init__(self, mapping_file: str = "data/consolidation_backups/file_mappings.json"):
        """
        Initialize file mapping system.
        
        Args:
            mapping_file: Path to file mappings data file
        """
        self.mapping_file = Path(mapping_file)
        self.mapping_file.parent.mkdir(parents=True, exist_ok=True)
        
        # File mappings
        self.mappings: Dict[str, FileMapping] = {}
        
        # Reverse lookup: consolidated file -> original files
        self.reverse_mappings: Dict[str, List[str]] = {}
        
        # Import dependency graph
        self.dependency_graph: Dict[str, Set[str]] = {}
        
        # Load existing mappings
        self._load_mappings()
    
    def _load_mappings(self) -> None:
        """Load file mappings from file."""
        if self.mapping_file.exists():
            try:
                with open(self.mapping_file, 'r') as f:
                    data = json.load(f)
                    self.mappings = {
                        mapping_id: FileMapping.from_dict(mapping_data)
                        for mapping_id, mapping_data in data.get('mappings', {}).items()
                    }
                    self.dependency_graph = {
                        file_path: set(deps)
                        for file_path, deps in data.get('dependency_graph', {}).items()
                    }
                
                # Rebuild reverse mappings
                self._rebuild_reverse_mappings()
                
                logger.info(f"Loaded {len(self.mappings)} file mappings")
            except Exception as e:
                logger.error(f"Failed to load file mappings: {e}")
                self.mappings = {}
                self.dependency_graph = {}
    
    def _save_mappings(self) -> None:
        """Save file mappings to file."""
        try:
            data = {
                'mappings': {
                    mapping_id: mapping.to_dict()
                    for mapping_id, mapping in self.mappings.items()
                },
                'dependency_graph': {
                    file_path: list(deps)
                    for file_path, deps in self.dependency_graph.items()
                }
            }
            
            with open(self.mapping_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("Saved file mappings")
        except Exception as e:
            logger.error(f"Failed to save file mappings: {e}")
    
    def _rebuild_reverse_mappings(self) -> None:
        """Rebuild reverse mappings from consolidated to original files."""
        self.reverse_mappings = {}
        
        for mapping in self.mappings.values():
            for consolidated_file in mapping.consolidated_files:
                if consolidated_file not in self.reverse_mappings:
                    self.reverse_mappings[consolidated_file] = []
                self.reverse_mappings[consolidated_file].extend(mapping.original_files)
    
    def _generate_mapping_id(self, original_files: List[str], consolidated_files: List[str]) -> str:
        """Generate a unique mapping ID."""
        content = f"{sorted(original_files)}_{sorted(consolidated_files)}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def analyze_file_imports(self, file_path: str) -> List[str]:
        """
        Analyze imports in a Python file.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            List of imported modules
        """
        imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the AST
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
        except Exception as e:
            logger.warning(f"Failed to analyze imports in {file_path}: {e}")
        
        return imports
    
    def analyze_file_dependencies(self, file_path: str, project_root: str = "backend/app") -> Set[str]:
        """
        Analyze dependencies of a file within the project.
        
        Args:
            file_path: Path to the file to analyze
            project_root: Root directory of the project
            
        Returns:
            Set of project files that this file depends on
        """
        dependencies = set()
        
        # Skip analysis if file doesn't exist to avoid recursion issues
        if not Path(file_path).exists():
            return dependencies
        
        project_root_path = Path(project_root)
        
        try:
            imports = self.analyze_file_imports(file_path)
            
            for import_module in imports:
                # Check if this is a relative import within the project
                if import_module.startswith('app.') or import_module.startswith('backend.app.'):
                    # Convert module path to file path
                    module_parts = import_module.replace('backend.app.', '').replace('app.', '').split('.')
                    if len(module_parts) > 0:
                        potential_file = project_root_path / '/'.join(module_parts[:-1]) / f"{module_parts[-1]}.py"
                        
                        if potential_file.exists() and str(potential_file) != file_path:  # Avoid self-reference
                            dependencies.add(str(potential_file))
                        else:
                            # Try as a package
                            potential_package = project_root_path / '/'.join(module_parts) / "__init__.py"
                            if potential_package.exists() and str(potential_package) != file_path:
                                dependencies.add(str(potential_package))
        
        except Exception as e:
            logger.warning(f"Failed to analyze dependencies for {file_path}: {e}")
        
        return dependencies
    
    def create_mapping(
        self,
        original_files: List[str],
        consolidated_files: List[str],
        mapping_type: MappingType,
        consolidation_phase: str,
        backup_ids: Optional[List[str]] = None,
        notes: Optional[str] = None
    ) -> str:
        """
        Create a new file mapping.
        
        Args:
            original_files: List of original file paths
            consolidated_files: List of consolidated file paths
            mapping_type: Type of mapping
            consolidation_phase: Phase this mapping belongs to
            backup_ids: List of backup IDs for original files
            notes: Optional notes about the mapping
            
        Returns:
            Mapping ID
        """
        mapping_id = self._generate_mapping_id(original_files, consolidated_files)
        
        # Analyze dependencies for original files (simplified to avoid recursion in tests)
        all_dependencies = set()
        try:
            for file_path in original_files:
                if Path(file_path).exists():
                    deps = self.analyze_file_dependencies(file_path)
                    all_dependencies.update(deps)
        except Exception as e:
            logger.warning(f"Failed to analyze dependencies during mapping creation: {e}")
            # Continue without dependencies to avoid blocking the mapping creation
        
        # Create mapping
        mapping = FileMapping(
            mapping_id=mapping_id,
            mapping_type=mapping_type,
            original_files=original_files,
            consolidated_files=consolidated_files,
            consolidation_phase=consolidation_phase,
            created_at=datetime.now(),
            dependencies=list(all_dependencies),
            import_changes=[],
            backup_ids=backup_ids or [],
            notes=notes
        )
        
        self.mappings[mapping_id] = mapping
        
        # Update dependency graph
        for file_path in original_files:
            if file_path not in self.dependency_graph:
                self.dependency_graph[file_path] = set()
            self.dependency_graph[file_path].update(all_dependencies)
        
        # Rebuild reverse mappings
        self._rebuild_reverse_mappings()
        
        # Save changes
        self._save_mappings()
        
        logger.info(f"Created file mapping {mapping_id}: {len(original_files)} -> {len(consolidated_files)} files")
        return mapping_id
    
    def add_import_change(
        self,
        mapping_id: str,
        old_import: str,
        new_import: str,
        import_type: str,
        line_number: Optional[int] = None
    ) -> None:
        """
        Add an import change to a mapping.
        
        Args:
            mapping_id: ID of the mapping
            old_import: Old import statement
            new_import: New import statement
            import_type: Type of import ("module", "from", "attribute")
            line_number: Line number where import occurs
        """
        if mapping_id not in self.mappings:
            raise ValueError(f"Mapping not found: {mapping_id}")
        
        import_change = ImportChange(
            old_import=old_import,
            new_import=new_import,
            import_type=import_type,
            line_number=line_number
        )
        
        self.mappings[mapping_id].import_changes.append(import_change)
        self._save_mappings()
        
        logger.debug(f"Added import change to mapping {mapping_id}: {old_import} -> {new_import}")
    
    def find_mappings_for_file(self, file_path: str) -> List[FileMapping]:
        """
        Find all mappings that involve a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of mappings involving the file
        """
        mappings = []
        
        for mapping in self.mappings.values():
            if (file_path in mapping.original_files or 
                file_path in mapping.consolidated_files):
                mappings.append(mapping)
        
        return mappings
    
    def get_consolidated_file(self, original_file: str) -> Optional[str]:
        """
        Get the consolidated file for an original file.
        
        Args:
            original_file: Path to the original file
            
        Returns:
            Path to consolidated file if found, None otherwise
        """
        for mapping in self.mappings.values():
            if original_file in mapping.original_files:
                # Return the first consolidated file (most mappings are many-to-one)
                if mapping.consolidated_files:
                    return mapping.consolidated_files[0]
        
        return None
    
    def get_original_files(self, consolidated_file: str) -> List[str]:
        """
        Get the original files for a consolidated file.
        
        Args:
            consolidated_file: Path to the consolidated file
            
        Returns:
            List of original file paths
        """
        return self.reverse_mappings.get(consolidated_file, [])
    
    def get_import_changes_for_file(self, file_path: str) -> List[ImportChange]:
        """
        Get all import changes that affect a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of import changes
        """
        import_changes = []
        
        # Find mappings that involve this file
        mappings = self.find_mappings_for_file(file_path)
        
        for mapping in mappings:
            import_changes.extend(mapping.import_changes)
        
        return import_changes
    
    def generate_import_migration_script(self, target_file: str) -> List[str]:
        """
        Generate a script to update imports in a target file.
        
        Args:
            target_file: Path to the file to update
            
        Returns:
            List of sed commands to update imports
        """
        import_changes = self.get_import_changes_for_file(target_file)
        sed_commands = []
        
        for change in import_changes:
            # Escape special characters for sed
            old_escaped = change.old_import.replace('/', r'\/')
            new_escaped = change.new_import.replace('/', r'\/')
            
            sed_command = f"sed -i 's/{old_escaped}/{new_escaped}/g' {target_file}"
            sed_commands.append(sed_command)
        
        return sed_commands
    
    def find_affected_files(self, original_files: List[str]) -> Set[str]:
        """
        Find all files that might be affected by consolidating the given files.
        
        Args:
            original_files: List of files being consolidated
            
        Returns:
            Set of files that import from the original files
        """
        affected_files = set()
        
        # Look through dependency graph to find files that depend on the original files
        for file_path, dependencies in self.dependency_graph.items():
            if any(orig_file in dependencies for orig_file in original_files):
                affected_files.add(file_path)
        
        return affected_files
    
    def validate_mapping(self, mapping_id: str) -> Dict[str, Any]:
        """
        Validate a file mapping.
        
        Args:
            mapping_id: ID of the mapping to validate
            
        Returns:
            Validation results
        """
        if mapping_id not in self.mappings:
            return {"valid": False, "error": "Mapping not found"}
        
        mapping = self.mappings[mapping_id]
        results = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Check if original files exist (in backups)
        for original_file in mapping.original_files:
            if not any(backup_id for backup_id in mapping.backup_ids):
                results["warnings"].append(f"No backup found for original file: {original_file}")
        
        # Check if consolidated files exist
        for consolidated_file in mapping.consolidated_files:
            if not Path(consolidated_file).exists():
                results["errors"].append(f"Consolidated file does not exist: {consolidated_file}")
        
        # Check for circular dependencies
        # (This is a simplified check - a full implementation would need more sophisticated cycle detection)
        
        if results["errors"]:
            results["valid"] = False
        
        return results
    
    def get_mapping_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about file mappings.
        
        Returns:
            Dictionary with mapping statistics
        """
        if not self.mappings:
            return {
                "total_mappings": 0,
                "mapping_types": {},
                "total_original_files": 0,
                "total_consolidated_files": 0,
                "consolidation_phases": {},
                "average_consolidation_ratio": 0.0
            }
        
        mapping_types = {}
        phases = {}
        total_original = 0
        total_consolidated = 0
        
        for mapping in self.mappings.values():
            # Count mapping types
            mapping_type = mapping.mapping_type.value
            if mapping_type not in mapping_types:
                mapping_types[mapping_type] = 0
            mapping_types[mapping_type] += 1
            
            # Count phases
            phase = mapping.consolidation_phase
            if phase not in phases:
                phases[phase] = {"mappings": 0, "original_files": 0, "consolidated_files": 0}
            phases[phase]["mappings"] += 1
            phases[phase]["original_files"] += len(mapping.original_files)
            phases[phase]["consolidated_files"] += len(mapping.consolidated_files)
            
            # Count files
            total_original += len(mapping.original_files)
            total_consolidated += len(mapping.consolidated_files)
        
        # Calculate average consolidation ratio
        avg_ratio = total_consolidated / total_original if total_original > 0 else 0
        
        return {
            "total_mappings": len(self.mappings),
            "mapping_types": mapping_types,
            "total_original_files": total_original,
            "total_consolidated_files": total_consolidated,
            "consolidation_phases": phases,
            "average_consolidation_ratio": avg_ratio,
            "file_reduction_percentage": ((total_original - total_consolidated) / total_original * 100) if total_original > 0 else 0
        }
    
    def export_mappings(self, export_file: str) -> None:
        """
        Export mappings to a file.
        
        Args:
            export_file: Path to export file
        """
        try:
            data = {
                "exported_at": datetime.now().isoformat(),
                "mappings": [mapping.to_dict() for mapping in self.mappings.values()],
                "statistics": self.get_mapping_statistics()
            }
            
            with open(export_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Exported {len(self.mappings)} mappings to {export_file}")
        except Exception as e:
            logger.error(f"Failed to export mappings: {e}")
    
    def list_mappings(self, consolidation_phase: Optional[str] = None) -> List[FileMapping]:
        """
        List all mappings, optionally filtered by phase.
        
        Args:
            consolidation_phase: Optional phase filter
            
        Returns:
            List of file mappings
        """
        mappings = list(self.mappings.values())
        
        if consolidation_phase:
            mappings = [m for m in mappings if m.consolidation_phase == consolidation_phase]
        
        # Sort by creation time (newest first)
        mappings.sort(key=lambda x: x.created_at, reverse=True)
        return mappings
    
    def get_mapping(self, mapping_id: str) -> Optional[FileMapping]:
        """
        Get a specific file mapping.
        
        Args:
            mapping_id: ID of the mapping
            
        Returns:
            File mapping if found, None otherwise
        """
        return self.mappings.get(mapping_id)