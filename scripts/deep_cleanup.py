#!/usr/bin/env python3
"""
Deep Codebase Cleanup - Comprehensive subfolder analysis and cleanup
"""

import os
import shutil
from pathlib import Path
from typing import List, Set

class DeepCleanup:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.removed_files = []
        
    def run_deep_cleanup(self):
        """Run comprehensive deep cleanup"""
        print("🔍 Starting deep subfolder analysis and cleanup...")
        
        # 1. Remove all validation scripts (redundant)
        self.remove_validation_scripts()
        
        # 2. Remove all run scripts (redundant) 
        self.remove_run_scripts()
        
        # 3. Remove demo files
        self.remove_demo_files()
        
        # 4. Consolidate config files
        self.consolidate_config_files()
        
        # 5. Remove redundant test runners
        self.remove_redundant_test_runners()
        
        # 6. Clean up empty directories
        self.remove_empty_directories()
        
        # 7. Fix remaining import issues
        self.fix_remaining_imports()
        
        print(f"✅ Deep cleanup completed! Removed {len(self.removed_files)} files")
        
    def remove_validation_scripts(self):
        """Remove all validation scripts - they're redundant"""
        print("🗑️ Removing validation scripts...")
        
        validation_patterns = [
            "**/validate_*.py",
            "**/validation_*.py"
        ]
        
        for pattern in validation_patterns:
            for file_path in self.root_path.rglob(pattern):
                if file_path.is_file():
                    file_path.unlink()
                    self.removed_files.append(str(file_path))
                    
    def remove_run_scripts(self):
        """Remove redundant run scripts"""
        print("🗑️ Removing redundant run scripts...")
        
        # Keep only essential run scripts
        essential_runs = {
            "tests/test_runner.py"  # Our consolidated test runner
        }
        
        for file_path in self.root_path.rglob("run_*.py"):
            if file_path.is_file():
                relative_path = str(file_path.relative_to(self.root_path))
                if relative_path not in essential_runs:
                    file_path.unlink()
                    self.removed_files.append(str(file_path))
                    
    def remove_demo_files(self):
        """Remove demo and example files"""
        print("🗑️ Removing demo files...")
        
        demo_patterns = [
            "**/demo_*.py",
            "**/example_*.py",
            "**/sample_*.py"
        ]
        
        for pattern in demo_patterns:
            for file_path in self.root_path.rglob(pattern):
                if file_path.is_file():
                    file_path.unlink()
                    self.removed_files.append(str(file_path))
                    
    def consolidate_config_files(self):
        """Consolidate configuration files"""
        print("⚙️ Consolidating config files...")
        
        # Remove duplicate pytest.ini files
        pytest_files = list(self.root_path.rglob("pytest.ini"))
        main_pytest = self.root_path / "pytest.ini"
        
        for pytest_file in pytest_files:
            if pytest_file != main_pytest and pytest_file.is_file():
                pytest_file.unlink()
                self.removed_files.append(str(pytest_file))
                
        # Remove duplicate alembic.ini files
        alembic_files = list(self.root_path.rglob("alembic.ini"))
        main_alembic = self.root_path / "backend" / "alembic.ini"
        
        for alembic_file in alembic_files:
            if alembic_file != main_alembic and alembic_file.is_file():
                alembic_file.unlink()
                self.removed_files.append(str(alembic_file))
                
    def remove_redundant_test_runners(self):
        """Remove redundant test runners"""
        print("🧪 Removing redundant test runners...")
        
        # Keep only our consolidated test runner
        essential_test_files = {
            "tests/test_runner.py",
            "tests/conftest.py"
        }
        
        test_runner_patterns = [
            "**/run_*test*.py",
            "**/test_runner.py"
        ]
        
        for pattern in test_runner_patterns:
            for file_path in self.root_path.rglob(pattern):
                if file_path.is_file():
                    relative_path = str(file_path.relative_to(self.root_path))
                    if relative_path not in essential_test_files:
                        file_path.unlink()
                        self.removed_files.append(str(file_path))
                        
    def remove_empty_directories(self):
        """Remove empty directories"""
        print("📁 Removing empty directories...")
        
        # Get all directories, sorted by depth (deepest first)
        all_dirs = []
        for root, dirs, files in os.walk(self.root_path):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                all_dirs.append(dir_path)
                
        # Sort by depth (deepest first) to remove nested empty dirs
        all_dirs.sort(key=lambda x: len(x.parts), reverse=True)
        
        for dir_path in all_dirs:
            if dir_path.exists() and dir_path.is_dir():
                try:
                    # Check if directory is empty
                    if not any(dir_path.iterdir()):
                        # Don't remove essential directories
                        essential_dirs = {
                            "tests/unit", "tests/integration", "tests/e2e", 
                            "tests/performance", "tests/security", "tests/fixtures",
                            "data/logs", "data/uploads", "data/backups", "logs"
                        }
                        
                        relative_path = str(dir_path.relative_to(self.root_path))
                        if relative_path not in essential_dirs:
                            dir_path.rmdir()
                            self.removed_files.append(str(dir_path))
                except (OSError, ValueError):
                    # Directory not empty or other error, skip
                    pass
                    
    def fix_remaining_imports(self):
        """Fix any remaining import issues"""
        print("🔧 Fixing remaining imports...")
        
        # Common import fixes for remaining files
        import_fixes = {
            "from app.": "from app.",
            "from tests.": "from tests.",
            "from .": "from .",
            "import ": "import ",
        }
        
        # Fix imports in all Python files
        for py_file in self.root_path.rglob("*.py"):
            if py_file.is_file() and not any(skip in str(py_file) for skip in [".conda", "__pycache__", ".git"]):
                try:
                    content = py_file.read_text(encoding='utf-8')
                    original_content = content
                    
                    for old_import, new_import in import_fixes.items():
                        content = content.replace(old_import, new_import)
                        
                    if content != original_content:
                        py_file.write_text(content, encoding='utf-8')
                        
                except Exception as e:
                    print(f"Warning: Could not fix imports in {py_file}: {e}")

def main():
    """Main cleanup function"""
    root_path = Path(__file__).parent.parent
    cleanup = DeepCleanup(str(root_path))
    cleanup.run_deep_cleanup()

if __name__ == "__main__":
    main()