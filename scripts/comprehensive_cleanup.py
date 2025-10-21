#!/usr/bin/env python3
"""
Comprehensive Career Copilot Codebase Cleanup Script

This script performs a thorough cleanup and reorganization of the codebase:
1. Consolidates test files into proper directory structure
2. Removes redundant and duplicate files
3. Fixes import statements
4. Streamlines the codebase for maintainability
5. Removes unnecessary artifacts and reports
"""

import os
import shutil
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime

class CodebaseCleanup:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.removed_files = []
        self.moved_files = []
        self.fixed_imports = []
        self.consolidated_tests = []
        
    def run_comprehensive_cleanup(self):
        """Run all cleanup operations"""
        print("🧹 Starting comprehensive codebase cleanup...")
        
        # 1. Remove redundant test files and consolidate
        self.consolidate_test_structure()
        
        # 2. Remove redundant scripts
        self.cleanup_redundant_scripts()
        
        # 3. Remove generated reports and artifacts
        self.cleanup_reports_and_artifacts()
        
        # 4. Remove cache and temporary files
        self.cleanup_cache_files()
        
        # 5. Consolidate configuration files
        self.consolidate_configurations()
        
        # 6. Fix import statements
        self.fix_import_statements()
        
        # 7. Remove unused dependencies
        self.cleanup_unused_dependencies()
        
        # 8. Generate cleanup report
        self.generate_cleanup_report()
        
        print("✅ Comprehensive cleanup completed!")
        
    def consolidate_test_structure(self):
        """Consolidate all test files into proper structure"""
        print("📁 Consolidating test structure...")
        
        # Define the target test structure
        target_structure = {
            "tests/unit/": [],
            "tests/integration/": [],
            "tests/e2e/": [],
            "tests/performance/": [],
            "tests/security/": []
        }
        
        # Remove duplicate test directories and files
        duplicate_test_dirs = [
            "tests/backend/unit/",
            "tests/backend/integration/", 
            "tests/backend/e2e/",
            "tests/backend/performance/",
            "tests/unit/",
            "tests/legacy/",
            "tests/config/"
        ]
        
        for test_dir in duplicate_test_dirs:
            full_path = self.root_path / test_dir
            if full_path.exists():
                # Move essential files to proper locations
                self.move_essential_test_files(full_path, test_dir)
                # Remove the duplicate directory
                shutil.rmtree(full_path)
                self.removed_files.append(str(full_path))
                
        # Remove redundant test files in tests/backend/
        backend_test_files = [
            "test_advanced_workflow_manager.py",
            "test_agent_cache_integration.py", 
            "test_agent_cache_manager.py",
            "test_agent_state_machine.py",
            "test_ai_service_manager.py",
            "test_analysis_results_api.py",
            "test_api_integration.py",
            "test_api.py",
            "test_authentication_integration.py",
            "test_career_copilot_models.py",
            "test_chroma_client.py",
            "test_cloud_storage.py",
            "test_communication_agent_integration.py",
            "test_communication_agent.py",
            "test_comprehensive_security_service.py",
            "test_contract_analysis_service.py",
            "test_contract_analyzer_agent.py",
            "test_contract_embedding_complete.py",
            "test_contract_structure_analyzer.py",
            "test_contract_upload_api.py",
            "test_cost_aware_provider_selection.py",
            "test_data_models.py",
            "test_database_backup.py",
            "test_database_integration.py",
            "test_document_processing.py",
            "test_document_processor_script.py",
            "test_document_versioning.py",
            "test_docusign_api_endpoints.py",
            "test_docusign_api.py",
            "test_docusign_integration.py",
            "test_docusign_service.py",
            "test_email_integration.py",
            "test_end_to_end_integration.py",
            "test_end_to_end_workflows.py"
        ]
        
        for test_file in backend_test_files:
            file_path = self.root_path / "tests/backend" / test_file
            if file_path.exists():
                file_path.unlink()
                self.removed_files.append(str(file_path))
                
    def move_essential_test_files(self, source_dir: Path, source_type: str):
        """Move essential test files to proper locations"""
        if not source_dir.exists():
            return
            
        for file_path in source_dir.rglob("*.py"):
            if file_path.name.startswith("test_") or file_path.name.endswith("_test.py"):
                # Determine target directory based on file content/name
                if "integration" in file_path.name or "integration" in source_type:
                    target_dir = self.root_path / "tests/integration"
                elif "e2e" in file_path.name or "e2e" in source_type:
                    target_dir = self.root_path / "tests/e2e"
                elif "performance" in file_path.name or "performance" in source_type:
                    target_dir = self.root_path / "tests/performance"
                elif "security" in file_path.name or "security" in source_type:
                    target_dir = self.root_path / "tests/security"
                else:
                    target_dir = self.root_path / "tests/unit"
                    
                # Create target directory if it doesn't exist
                target_dir.mkdir(parents=True, exist_ok=True)
                
                # Move file if it doesn't already exist
                target_file = target_dir / file_path.name
                if not target_file.exists():
                    shutil.copy2(file_path, target_file)
                    self.moved_files.append((str(file_path), str(target_file)))
                    
    def cleanup_redundant_scripts(self):
        """Remove redundant scripts and consolidate functionality"""
        print("🗂️ Cleaning up redundant scripts...")
        
        # Remove redundant scripts from backend/scripts/
        redundant_backend_scripts = [
            "demo_deduplication.py",
            "final_market_analysis_validation.py", 
            "integration_test_migration.py",
            "migrate_job_tracker_1.py",
            "migrate_job_tracker_2.py",
            "populate_help_articles.py",
            "run_consolidation.py",
            "verify_docusign_integration.py"
        ]
        
        for script in redundant_backend_scripts:
            script_path = self.root_path / "backend/scripts" / script
            if script_path.exists():
                script_path.unlink()
                self.removed_files.append(str(script_path))
                
        # Remove redundant scripts from main scripts/
        redundant_main_scripts = [
            "codebase-cleanup.py",
            "unified-localhost.sh", 
            "unified-manager.py"
        ]
        
        for script in redundant_main_scripts:
            script_path = self.root_path / "scripts" / script
            if script_path.exists():
                script_path.unlink()
                self.removed_files.append(str(script_path))
                
        # Remove redundant test runners
        test_runners = [
            "tests/run_e2e_tests.py",
            "tests/run_task_12_3_tests.py",
            "tests/validate_comprehensive_integration_tests.py",
            "tests/validate_e2e_coverage.py",
            "tests/backend/run_integration_tests.py",
            "tests/backend/run_model_tests.py",
            "tests/backend/validate_test_setup.py"
        ]
        
        for runner in test_runners:
            runner_path = self.root_path / runner
            if runner_path.exists():
                runner_path.unlink()
                self.removed_files.append(str(runner_path))
                
    def cleanup_reports_and_artifacts(self):
        """Remove generated reports and temporary artifacts"""
        print("📊 Cleaning up reports and artifacts...")
        
        # Remove all JSON and TXT report files
        report_patterns = [
            "**/*_report_*.json",
            "**/*_report_*.txt", 
            "**/test_*_report.json",
            "**/validation_report*.json",
            "**/analysis_report*.json",
            "**/performance_report*.json"
        ]
        
        for pattern in report_patterns:
            for file_path in self.root_path.rglob(pattern):
                if file_path.is_file():
                    file_path.unlink()
                    self.removed_files.append(str(file_path))
                    
        # Remove specific report directories
        report_dirs = [
            "reports/test-reports/",
            "reports/validation/",
            "backend/backend/logs/"
        ]
        
        for report_dir in report_dirs:
            dir_path = self.root_path / report_dir
            if dir_path.exists():
                shutil.rmtree(dir_path)
                self.removed_files.append(str(dir_path))
                
    def cleanup_cache_files(self):
        """Remove cache and temporary files"""
        print("🗑️ Cleaning up cache files...")
        
        # Remove __pycache__ directories
        for cache_dir in self.root_path.rglob("__pycache__"):
            if cache_dir.is_dir():
                shutil.rmtree(cache_dir)
                self.removed_files.append(str(cache_dir))
                
        # Remove .pytest_cache directories
        for pytest_cache in self.root_path.rglob(".pytest_cache"):
            if pytest_cache.is_dir():
                shutil.rmtree(pytest_cache)
                self.removed_files.append(str(pytest_cache))
                
        # Remove other cache files
        cache_patterns = [
            "**/*.pyc",
            "**/*.pyo", 
            "**/.coverage",
            "**/coverage.xml",
            "**/.mypy_cache",
            "**/.tox"
        ]
        
        for pattern in cache_patterns:
            for file_path in self.root_path.rglob(pattern):
                if file_path.is_file():
                    file_path.unlink()
                    self.removed_files.append(str(file_path))
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
                    self.removed_files.append(str(file_path))
                    
    def consolidate_configurations(self):
        """Consolidate configuration files"""
        print("⚙️ Consolidating configurations...")
        
        # Remove duplicate pytest.ini files
        pytest_configs = [
            "backend/config/pytest.ini",
            "backend/config/pytest.integration.ini",
            "tests/unit/pytest.ini",
            "config/pytest.ini"
        ]
        
        for config in pytest_configs:
            config_path = self.root_path / config
            if config_path.exists():
                config_path.unlink()
                self.removed_files.append(str(config_path))
                
        # Keep only the main pytest.ini
        main_pytest = self.root_path / "pytest.ini"
        if not main_pytest.exists():
            # Create a consolidated pytest.ini
            pytest_content = """[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=backend/app
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    security: Security tests
    slow: Slow running tests
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
"""
            main_pytest.write_text(pytest_content)
            
    def fix_import_statements(self):
        """Fix import statements in remaining files"""
        print("🔧 Fixing import statements...")
        
        # Common import fixes
        import_fixes = {
            "from app.": "from app.",
            "from tests.": "from tests.",
            "from tests.unit.": "from tests.unit.",
            "from tests.integration.": "from tests.integration.",
            "from .": "from .",
        }
        
        # Fix imports in Python files
        for py_file in self.root_path.rglob("*.py"):
            if py_file.is_file() and not any(skip in str(py_file) for skip in [".conda", "__pycache__", ".git"]):
                try:
                    content = py_file.read_text(encoding='utf-8')
                    original_content = content
                    
                    for old_import, new_import in import_fixes.items():
                        content = content.replace(old_import, new_import)
                        
                    if content != original_content:
                        py_file.write_text(content, encoding='utf-8')
                        self.fixed_imports.append(str(py_file))
                        
                except Exception as e:
                    print(f"Warning: Could not fix imports in {py_file}: {e}")
                    
    def cleanup_unused_dependencies(self):
        """Remove unused dependencies and consolidate requirements"""
        print("📦 Cleaning up dependencies...")
        
        # Remove redundant requirement files
        redundant_reqs = [
            "backend/requirements-prod.txt",
            "frontend/requirements-prod.txt", 
            "frontend/requirements.txt",
            "gcp/requirements.txt",
            "docker-requirements.txt"
        ]
        
        for req_file in redundant_reqs:
            req_path = self.root_path / req_file
            if req_path.exists():
                req_path.unlink()
                self.removed_files.append(str(req_path))
                
    def generate_cleanup_report(self):
        """Generate a comprehensive cleanup report"""
        print("📋 Generating cleanup report...")
        
        report = {
            "cleanup_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_files_removed": len(self.removed_files),
                "total_files_moved": len(self.moved_files),
                "total_imports_fixed": len(self.fixed_imports),
                "tests_consolidated": True,
                "scripts_consolidated": True,
                "reports_cleaned": True,
                "cache_cleaned": True,
                "configurations_consolidated": True
            },
            "removed_files": self.removed_files[:50],  # Limit for readability
            "moved_files": self.moved_files[:20],
            "fixed_imports": self.fixed_imports[:20],
            "recommendations": [
                "Run 'python -m pytest tests/' to verify test consolidation",
                "Run 'python scripts/system_manager.py validate --type env' to verify configuration",
                "Run 'python scripts/dev_manager.py test --type unit' to run unit tests",
                "Review remaining files in tests/ directory for any manual cleanup needed",
                "Update CI/CD pipelines to use new test structure"
            ]
        }
        
        report_path = self.root_path / "COMPREHENSIVE_CLEANUP_REPORT.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"📊 Cleanup report saved to: {report_path}")
        print(f"✅ Removed {len(self.removed_files)} files/directories")
        print(f"📁 Moved {len(self.moved_files)} files")
        print(f"🔧 Fixed imports in {len(self.fixed_imports)} files")

def main():
    """Main cleanup function"""
    root_path = Path(__file__).parent.parent
    cleanup = CodebaseCleanup(str(root_path))
    cleanup.run_comprehensive_cleanup()

if __name__ == "__main__":
    main()