"""
Import compatibility layer to handle deprecated imports during transition.

This module provides functionality to maintain backward compatibility
while transitioning from old import paths to new consolidated modules.
"""

import sys
import warnings
import importlib
import logging
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class ImportMapping:
    """Mapping from old import path to new import path."""
    old_module: str
    new_module: str
    old_attribute: Optional[str] = None
    new_attribute: Optional[str] = None
    deprecation_message: Optional[str] = None
    removal_version: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "old_module": self.old_module,
            "new_module": self.new_module,
            "old_attribute": self.old_attribute,
            "new_attribute": self.new_attribute,
            "deprecation_message": self.deprecation_message,
            "removal_version": self.removal_version
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ImportMapping':
        """Create from dictionary."""
        return cls(**data)


class CompatibilityLayer:
    """Manages import compatibility during consolidation transition."""
    
    def __init__(self, config_file: str = "data/consolidation_backups/import_mappings.json"):
        """
        Initialize compatibility layer.
        
        Args:
            config_file: Path to import mappings configuration file
        """
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Import mappings
        self.mappings: List[ImportMapping] = []
        
        # Track usage for analytics
        self.usage_stats: Dict[str, int] = {}
        
        # Active compatibility modules
        self.active_modules: Set[str] = set()
        
        # Load configuration
        self._load_mappings()
        
        # Install import hooks
        self._install_import_hooks()
    
    def _load_mappings(self) -> None:
        """Load import mappings from configuration file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.mappings = [
                        ImportMapping.from_dict(mapping_data)
                        for mapping_data in data.get('mappings', [])
                    ]
                    self.usage_stats = data.get('usage_stats', {})
                logger.info(f"Loaded {len(self.mappings)} import mappings")
            except Exception as e:
                logger.error(f"Failed to load import mappings: {e}")
                self.mappings = []
                self.usage_stats = {}
    
    def _save_mappings(self) -> None:
        """Save import mappings to configuration file."""
        try:
            data = {
                'mappings': [mapping.to_dict() for mapping in self.mappings],
                'usage_stats': self.usage_stats
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug("Saved import mappings")
        except Exception as e:
            logger.error(f"Failed to save import mappings: {e}")
    
    def add_mapping(
        self,
        old_module: str,
        new_module: str,
        old_attribute: Optional[str] = None,
        new_attribute: Optional[str] = None,
        deprecation_message: Optional[str] = None,
        removal_version: Optional[str] = None
    ) -> None:
        """
        Add a new import mapping.
        
        Args:
            old_module: Old module path
            new_module: New module path
            old_attribute: Old attribute name (if mapping specific attribute)
            new_attribute: New attribute name (if different from old)
            deprecation_message: Custom deprecation message
            removal_version: Version when old import will be removed
        """
        mapping = ImportMapping(
            old_module=old_module,
            new_module=new_module,
            old_attribute=old_attribute,
            new_attribute=new_attribute or old_attribute,
            deprecation_message=deprecation_message,
            removal_version=removal_version
        )
        
        self.mappings.append(mapping)
        self._save_mappings()
        
        logger.info(f"Added import mapping: {old_module} -> {new_module}")
    
    def add_batch_mappings(self, mappings: List[Dict]) -> None:
        """
        Add multiple import mappings at once.
        
        Args:
            mappings: List of mapping dictionaries
        """
        for mapping_data in mappings:
            mapping = ImportMapping.from_dict(mapping_data)
            self.mappings.append(mapping)
        
        self._save_mappings()
        logger.info(f"Added {len(mappings)} import mappings")
    
    def _find_mapping(self, module_name: str, attribute: Optional[str] = None) -> Optional[ImportMapping]:
        """
        Find import mapping for given module and attribute.
        
        Args:
            module_name: Module name to find mapping for
            attribute: Optional attribute name
            
        Returns:
            Import mapping if found, None otherwise
        """
        for mapping in self.mappings:
            if mapping.old_module == module_name:
                if attribute is None or mapping.old_attribute is None:
                    return mapping
                elif mapping.old_attribute == attribute:
                    return mapping
        return None
    
    def _create_compatibility_module(self, mapping: ImportMapping) -> Any:
        """
        Create a compatibility module that redirects imports.
        
        Args:
            mapping: Import mapping to create module for
            
        Returns:
            Compatibility module
        """
        try:
            # Import the new module
            new_module = importlib.import_module(mapping.new_module)
            
            # Create compatibility wrapper
            class CompatibilityModule:
                def __init__(self, target_module, mapping_info, usage_stats_ref):
                    self._target_module = target_module
                    self._mapping = mapping_info
                    self._usage_stats = usage_stats_ref
                
                def __getattr__(self, name):
                    # Track usage
                    usage_key = f"{self._mapping.old_module}.{name}"
                    self._track_usage(usage_key)
                    
                    # Show deprecation warning
                    self._show_deprecation_warning(name)
                    
                    # Handle attribute mapping
                    if self._mapping.old_attribute == name and self._mapping.new_attribute:
                        target_name = self._mapping.new_attribute
                    else:
                        target_name = name
                    
                    try:
                        return getattr(self._target_module, target_name)
                    except AttributeError:
                        raise AttributeError(
                            f"Module '{self._mapping.old_module}' has no attribute '{name}'. "
                            f"This module has been consolidated into '{self._mapping.new_module}'. "
                            f"Please update your imports."
                        )
                
                def _track_usage(self, usage_key):
                    """Track usage statistics."""
                    if usage_key not in self._usage_stats:
                        self._usage_stats[usage_key] = 0
                    self._usage_stats[usage_key] += 1
                
                def _show_deprecation_warning(self, attribute_name):
                    """Show deprecation warning."""
                    if self._mapping.deprecation_message:
                        message = self._mapping.deprecation_message
                    else:
                        message = (
                            f"Importing '{attribute_name}' from '{self._mapping.old_module}' is deprecated. "
                            f"Use '{self._mapping.new_module}' instead."
                        )
                    
                    if self._mapping.removal_version:
                        message += f" This will be removed in version {self._mapping.removal_version}."
                    
                    warnings.warn(
                        message,
                        DeprecationWarning,
                        stacklevel=3
                    )
            
            return CompatibilityModule(new_module, mapping, self.usage_stats)
            
        except ImportError as e:
            logger.error(f"Failed to import new module {mapping.new_module}: {e}")
            return None
    
    def _install_import_hooks(self) -> None:
        """Install import hooks to intercept deprecated imports."""
        # Store original import function
        import builtins
        self._original_import = builtins.__import__
        
        def compatibility_import(name, globals=None, locals=None, fromlist=(), level=0):
            """Custom import function that handles deprecated imports."""
            # Check if this is a deprecated import
            mapping = self._find_mapping(name)
            
            if mapping and name not in self.active_modules:
                # Track usage
                usage_key = f"module:{name}"
                if usage_key not in self.usage_stats:
                    self.usage_stats[usage_key] = 0
                self.usage_stats[usage_key] += 1
                
                # Create compatibility module
                compat_module = self._create_compatibility_module(mapping)
                if compat_module:
                    # Add to sys.modules to cache it
                    sys.modules[name] = compat_module
                    self.active_modules.add(name)
                    
                    logger.debug(f"Created compatibility module for {name}")
                    return compat_module
            
            # Fall back to original import
            return self._original_import(name, globals, locals, fromlist, level)
        
        # Replace built-in import
        builtins.__import__ = compatibility_import
    
    def _uninstall_import_hooks(self) -> None:
        """Uninstall import hooks and restore original import."""
        if hasattr(self, '_original_import'):
            import builtins
            builtins.__import__ = self._original_import
            logger.info("Uninstalled import hooks")
    
    def activate(self) -> None:
        """Activate the compatibility layer."""
        self._install_import_hooks()
        logger.info("Activated compatibility layer")
    
    def deactivate(self) -> None:
        """Deactivate the compatibility layer."""
        self._uninstall_import_hooks()
        
        # Remove compatibility modules from sys.modules
        for module_name in list(self.active_modules):
            if module_name in sys.modules:
                del sys.modules[module_name]
        
        self.active_modules.clear()
        logger.info("Deactivated compatibility layer")
    
    def get_usage_statistics(self) -> Dict[str, int]:
        """
        Get usage statistics for deprecated imports.
        
        Returns:
            Dictionary mapping import paths to usage counts
        """
        return self.usage_stats.copy()
    
    def clear_usage_statistics(self) -> None:
        """Clear usage statistics."""
        self.usage_stats.clear()
        self._save_mappings()
        logger.info("Cleared usage statistics")
    
    def generate_migration_report(self) -> Dict:
        """
        Generate a report of deprecated import usage.
        
        Returns:
            Migration report with usage statistics and recommendations
        """
        report = {
            "total_mappings": len(self.mappings),
            "active_modules": len(self.active_modules),
            "usage_statistics": self.usage_stats.copy(),
            "recommendations": []
        }
        
        # Generate recommendations based on usage
        for usage_key, count in self.usage_stats.items():
            if usage_key.startswith("module:"):
                module_name = usage_key[7:]  # Remove "module:" prefix
                mapping = self._find_mapping(module_name)
                if mapping:
                    report["recommendations"].append({
                        "old_import": f"import {mapping.old_module}",
                        "new_import": f"import {mapping.new_module}",
                        "usage_count": count,
                        "priority": "high" if count > 10 else "medium" if count > 5 else "low"
                    })
            else:
                # Attribute-level usage
                parts = usage_key.split(".")
                if len(parts) >= 2:
                    module_name = ".".join(parts[:-1])
                    attribute_name = parts[-1]
                    mapping = self._find_mapping(module_name, attribute_name)
                    if mapping:
                        old_import = f"from {mapping.old_module} import {attribute_name}"
                        new_import = f"from {mapping.new_module} import {mapping.new_attribute or attribute_name}"
                        report["recommendations"].append({
                            "old_import": old_import,
                            "new_import": new_import,
                            "usage_count": count,
                            "priority": "high" if count > 10 else "medium" if count > 5 else "low"
                        })
        
        return report
    
    def remove_mapping(self, old_module: str, old_attribute: Optional[str] = None) -> bool:
        """
        Remove an import mapping.
        
        Args:
            old_module: Old module path
            old_attribute: Old attribute name (if removing specific attribute mapping)
            
        Returns:
            True if mapping was removed, False if not found
        """
        for i, mapping in enumerate(self.mappings):
            if (mapping.old_module == old_module and 
                mapping.old_attribute == old_attribute):
                del self.mappings[i]
                self._save_mappings()
                logger.info(f"Removed import mapping: {old_module}")
                return True
        
        logger.warning(f"Import mapping not found: {old_module}")
        return False
    
    def list_mappings(self) -> List[ImportMapping]:
        """
        List all import mappings.
        
        Returns:
            List of import mappings
        """
        return self.mappings.copy()


# Global compatibility layer instance
_compatibility_layer: Optional[CompatibilityLayer] = None


def get_compatibility_layer() -> CompatibilityLayer:
    """Get the global compatibility layer instance."""
    global _compatibility_layer
    if _compatibility_layer is None:
        _compatibility_layer = CompatibilityLayer()
    return _compatibility_layer


def activate_compatibility_layer() -> None:
    """Activate the global compatibility layer."""
    layer = get_compatibility_layer()
    layer.activate()


def deactivate_compatibility_layer() -> None:
    """Deactivate the global compatibility layer."""
    layer = get_compatibility_layer()
    layer.deactivate()


def add_import_mapping(
    old_module: str,
    new_module: str,
    old_attribute: Optional[str] = None,
    new_attribute: Optional[str] = None,
    deprecation_message: Optional[str] = None,
    removal_version: Optional[str] = None
) -> None:
    """
    Add an import mapping to the global compatibility layer.
    
    Args:
        old_module: Old module path
        new_module: New module path
        old_attribute: Old attribute name
        new_attribute: New attribute name
        deprecation_message: Custom deprecation message
        removal_version: Version when old import will be removed
    """
    layer = get_compatibility_layer()
    layer.add_mapping(
        old_module=old_module,
        new_module=new_module,
        old_attribute=old_attribute,
        new_attribute=new_attribute,
        deprecation_message=deprecation_message,
        removal_version=removal_version
    )