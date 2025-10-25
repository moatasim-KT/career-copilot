#!/usr/bin/env python3
"""
Fix configuration function calls after import path updates.

This script updates function calls to use the correct function names
after consolidating configuration imports.
"""

import os
import re
from pathlib import Path
from typing import Dict, List


def get_function_call_replacements() -> Dict[str, str]:
    """Get mapping of old function calls to new function calls."""
    return {
        # get_config_value() calls should become get_config_value()
        r'\bget_config\(': 'get_config_value(',
        r'\bget_backend_config\(': 'get_config_value(',
        
        # Handle cases where functions are aliased
        r'get_config_value': 'get_config_value',
        r'get_config_value': 'get_config_value',
    }


def update_function_calls_in_file(file_path: Path, replacements: Dict[str, str]) -> bool:
    """
    Update function calls in a single file.
    
    Args:
        file_path: Path to the file to update
        replacements: Dictionary of old -> new function call patterns
        
    Returns:
        True if file was modified, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        modified = False
        
        # Apply regex replacements
        for old_pattern, new_replacement in replacements.items():
            new_content = re.sub(old_pattern, new_replacement, content)
            if new_content != content:
                content = new_content
                modified = True
                print(f"  ✓ Updated function calls: {old_pattern} -> {new_replacement}")
        
        # Write back if modified
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ Error updating {file_path}: {e}")
        return False


def find_files_with_config_calls() -> List[Path]:
    """Find all files that call old configuration functions."""
    files_to_update = []
    
    # Search patterns for old function calls
    patterns = [
        r'\bget_config\(',
        r'\bget_backend_config\(',
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
                    
                    # Check if file contains any of the old function call patterns
                    for pattern in patterns:
                        if re.search(pattern, content):
                            files_to_update.append(file_path)
                            break
                            
                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}")
    
    return files_to_update


def fix_all_function_calls():
    """Fix all configuration function calls in the codebase."""
    print("🔧 Fixing configuration function calls...")
    
    # Get replacement mappings
    replacements = get_function_call_replacements()
    
    # Find files to update
    print("🔍 Finding files with old configuration function calls...")
    files_to_update = find_files_with_config_calls()
    
    if not files_to_update:
        print("✅ No files found with old configuration function calls")
        return
    
    print(f"📝 Found {len(files_to_update)} files to update:")
    
    updated_count = 0
    for file_path in files_to_update:
        print(f"\n📄 Updating {file_path}...")
        if update_function_calls_in_file(file_path, replacements):
            updated_count += 1
        else:
            print(f"  ℹ️  No changes needed")
    
    print(f"\n✅ Updated {updated_count} files successfully")


if __name__ == "__main__":
    fix_all_function_calls()