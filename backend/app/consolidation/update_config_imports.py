#!/usr/bin/env python3
"""
Update configuration import paths to use consolidated modules.

This script updates all files that import from old configuration modules
to use the new consolidated modules.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from consolidation.compatibility_layer import activate_compatibility_layer


def get_import_replacements() -> Dict[str, str]:
    """Get mapping of old imports to new imports."""
    return {
        # config_loader imports
        "from app.core.config import get_config_value": 
            "from app.core.config import get_config_value",
        "from app.core.config import get_config_value as get_config": 
            "from app.core.config import get_config_value as get_config",
        "from app.core.config import get_config_value as get_backend_config": 
            "from app.core.config import get_config_value as get_backend_config",
        
        # config_manager imports
        "from app.core.config import get_config_manager": 
            "from app.core.config import get_config_manager",
        "from app.core.config import initialize_configuration": 
            "from app.core.config import initialize_configuration",
        "from app.core.config import DeploymentMode": 
            "from app.core.config import DeploymentMode",
        "from app.core.config import (": 
            "from app.core.config import (",
        
        # config_validator imports
        "from app.core.config import validate_configuration": 
            "from app.core.config import validate_configuration",
        
        # environment_config imports
        "from app.core.config_advanced import get_environment_config_manager": 
            "from app.core.config_advanced import get_environment_config_manager",
        "from app.core.config_advanced import setup_environment": 
            "from app.core.config_advanced import setup_environment",
        
        # Import statements without specific functions
        "import app.core.config as config_loader": 
            "import app.core.config as config_loader",
        "import app.core.config as config_manager": 
            "import app.core.config as config_manager",
        "import app.core.config as config_validator": 
            "import app.core.config as config_validator",
        "import app.core.config_advanced as environment_config": 
            "import app.core.config_advanced as environment_config",
    }


def update_file_imports(file_path: Path, replacements: Dict[str, str]) -> bool:
    """
    Update import statements in a single file.
    
    Args:
        file_path: Path to the file to update
        replacements: Dictionary of old -> new import statements
        
    Returns:
        True if file was modified, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        modified = False
        
        # Apply replacements
        for old_import, new_import in replacements.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                modified = True
                print(f"  ✓ Updated: {old_import} -> {new_import}")
        
        # Handle multi-line imports from config_manager
        multiline_pattern = r'from app\.core\.config_manager import \(\s*([^)]+)\s*\)'
        def replace_multiline(match):
            imports = match.group(1)
            return f"from app.core.config import (\n{imports}\n)"
        
        new_content = re.sub(multiline_pattern, replace_multiline, content, flags=re.DOTALL)
        if new_content != content:
            content = new_content
            modified = True
            print(f"  ✓ Updated multi-line import from config_manager")
        
        # Write back if modified
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ Error updating {file_path}: {e}")
        return False


def find_files_with_config_imports() -> List[Path]:
    """Find all files that import from old configuration modules."""
    files_to_update = []
    
    # Search patterns for old imports
    patterns = [
        "config.config_loader",
        "app.core.config_manager",
        "app.core.config_validator", 
        "app.core.environment_config"
    ]
    
    # Search in backend directory
    backend_root = Path(__file__).parent.parent.parent
    
    for root, dirs, files in os.walk(backend_root):
        # Skip certain directories
        skip_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.mypy_cache'}
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check if file contains any of the old import patterns
                    for pattern in patterns:
                        if pattern in content:
                            files_to_update.append(file_path)
                            break
                            
                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}")
    
    return files_to_update


def update_all_imports():
    """Update all configuration imports in the codebase."""
    print("🔄 Updating configuration import paths...")
    
    # Activate compatibility layer first
    print("📦 Activating compatibility layer...")
    activate_compatibility_layer()
    
    # Get replacement mappings
    replacements = get_import_replacements()
    
    # Find files to update
    print("🔍 Finding files with old configuration imports...")
    files_to_update = find_files_with_config_imports()
    
    if not files_to_update:
        print("✅ No files found with old configuration imports")
        return
    
    print(f"📝 Found {len(files_to_update)} files to update:")
    
    updated_count = 0
    for file_path in files_to_update:
        print(f"\n📄 Updating {file_path}...")
        if update_file_imports(file_path, replacements):
            updated_count += 1
        else:
            print(f"  ℹ️  No changes needed")
    
    print(f"\n✅ Updated {updated_count} files successfully")
    print("🔧 Compatibility layer is active for gradual migration")


if __name__ == "__main__":
    update_all_imports()