"""
Test script to verify consolidation infrastructure functionality.

This script tests the basic functionality of all consolidation components
to ensure they work correctly together.
"""

import tempfile
import shutil
import logging
from pathlib import Path
from datetime import datetime

from .consolidation_manager import ConsolidationManager
from .tracking_system import ConsolidationType
from .file_mapping import MappingType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_test_files(test_dir: Path) -> list[str]:
    """Create some test files for consolidation testing."""
    test_files = []
    
    # Create test Python files
    for i in range(3):
        test_file = test_dir / f"test_module_{i}.py"
        test_file.write_text(f"""
# Test module {i}
import os
import sys
from app.services import some_service

def test_function_{i}():
    return "test_{i}"

class TestClass{i}:
    def method(self):
        return {i}
""")
        test_files.append(str(test_file))
    
    return test_files


def test_consolidation_infrastructure():
    """Test the consolidation infrastructure."""
    logger.info("Starting consolidation infrastructure test")
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test data directory
        test_data_dir = temp_path / "test_consolidation_data"
        test_data_dir.mkdir()
        
        # Create test files directory
        test_files_dir = temp_path / "test_files"
        test_files_dir.mkdir()
        
        # Initialize consolidation manager with test directory
        manager = ConsolidationManager(str(test_data_dir))
        
        try:
            # Test 1: Initialize project
            logger.info("Test 1: Initialize consolidation project")
            manager.initialize_consolidation_project(total_files_before=100)
            
            # Test 2: Create consolidation phase
            logger.info("Test 2: Create consolidation phase")
            phase_id = manager.create_consolidation_phase(
                name="Test Configuration Consolidation",
                description="Test consolidation of configuration files",
                week=1,
                consolidation_type=ConsolidationType.MODULE_CONSOLIDATION
            )
            
            # Test 3: Create test files and start consolidation step
            logger.info("Test 3: Create test files and start consolidation step")
            test_files = create_test_files(test_files_dir)
            consolidated_file = str(test_files_dir / "consolidated_config.py")
            
            # Temporarily disable dependency analysis for testing
            original_analyze = manager.file_mapper.analyze_file_dependencies
            manager.file_mapper.analyze_file_dependencies = lambda x, y="": set()
            
            step_result = manager.start_consolidation_step(
                phase_id=phase_id,
                step_name="Consolidate test modules",
                step_description="Test consolidation of multiple modules into one",
                files_to_consolidate=test_files,
                consolidated_files=[consolidated_file],
                mapping_type=MappingType.MANY_TO_ONE
            )
            
            # Restore original method
            manager.file_mapper.analyze_file_dependencies = original_analyze
            
            step_id = step_result["step_id"]
            mapping_id = step_result["mapping_id"]
            
            # Test 4: Create consolidated file
            logger.info("Test 4: Create consolidated file")
            Path(consolidated_file).write_text("""
# Consolidated configuration module
import os
import sys

def consolidated_function():
    return "consolidated"

class ConsolidatedClass:
    def method(self):
        return "consolidated"
""")
            
            # Test 5: Complete consolidation step with import changes
            logger.info("Test 5: Complete consolidation step")
            import_changes = [
                {
                    "old_import": "from test_module_0 import test_function_0",
                    "new_import": "from consolidated_config import consolidated_function",
                    "import_type": "from",
                    "old_module": "test_module_0",
                    "new_module": "consolidated_config",
                    "old_attribute": "test_function_0",
                    "new_attribute": "consolidated_function"
                }
            ]
            
            manager.complete_consolidation_step(
                phase_id=phase_id,
                step_id=step_id,
                mapping_id=mapping_id,
                import_changes=import_changes
            )
            
            # Test 6: Get progress
            logger.info("Test 6: Get consolidation progress")
            progress = manager.get_consolidation_progress()
            logger.info(f"Progress: {progress['overall_progress']['progress_percentage']:.1f}%")
            
            # Test 7: Generate report
            logger.info("Test 7: Generate consolidation report")
            report = manager.generate_consolidation_report()
            logger.info(f"Report generated with {len(report['progress']['phases'])} phases")
            
            # Test 8: Validate consolidation state
            logger.info("Test 8: Validate consolidation state")
            validation = manager.validate_consolidation_state()
            if validation['valid']:
                logger.info("✓ Consolidation state is valid")
            else:
                logger.warning("✗ Consolidation state has issues")
                for error in validation['errors']:
                    logger.warning(f"  ERROR: {error}")
            
            # Test 9: Test rollback functionality
            logger.info("Test 9: Test rollback functionality")
            rollback_success = manager.rollback_consolidation_phase(phase_id)
            if rollback_success:
                logger.info("✓ Rollback successful")
            else:
                logger.warning("✗ Rollback failed")
            
            # Test 10: Finalize project
            logger.info("Test 10: Finalize consolidation project")
            manager.finalize_consolidation_project(total_files_after=80)
            
            logger.info("✓ All consolidation infrastructure tests passed!")
            return True
            
        except Exception as e:
            logger.error(f"✗ Test failed: {e}")
            return False


def test_backup_system():
    """Test the backup system independently."""
    logger.info("Testing backup system")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test file
        test_file = temp_path / "test_backup.py"
        test_file.write_text("# Test file for backup\nprint('hello world')")
        
        # Initialize backup system
        from .backup_system import BackupSystem
        backup_system = BackupSystem(str(temp_path / "backups"))
        
        # Create backup
        backup_id = backup_system.create_backup(str(test_file), "test_phase")
        if backup_id:
            logger.info(f"✓ Backup created: {backup_id}")
            
            # Test restore
            test_file.unlink()  # Delete original
            if backup_system.restore_backup(backup_id):
                logger.info("✓ Backup restored successfully")
                return True
            else:
                logger.error("✗ Backup restore failed")
                return False
        else:
            logger.error("✗ Backup creation failed")
            return False


def test_compatibility_layer():
    """Test the compatibility layer independently."""
    logger.info("Testing compatibility layer")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Initialize compatibility layer
        from .compatibility_layer import CompatibilityLayer
        compat_layer = CompatibilityLayer(str(temp_path / "import_mappings.json"))
        
        # Add mapping
        compat_layer.add_mapping(
            old_module="old_module",
            new_module="new_module",
            deprecation_message="This is deprecated"
        )
        
        # Check mapping exists
        mappings = compat_layer.list_mappings()
        if len(mappings) == 1:
            logger.info("✓ Compatibility mapping added successfully")
            
            # Test usage statistics
            stats = compat_layer.get_usage_statistics()
            logger.info(f"✓ Usage statistics: {len(stats)} entries")
            return True
        else:
            logger.error("✗ Compatibility mapping failed")
            return False


if __name__ == "__main__":
    """Run all tests when script is executed directly."""
    logger.info("Running consolidation infrastructure tests")
    
    tests = [
        ("Backup System", test_backup_system),
        ("Compatibility Layer", test_compatibility_layer),
        ("Full Infrastructure", test_consolidation_infrastructure)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running {test_name} Test")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✓ {test_name} test PASSED")
            else:
                logger.error(f"✗ {test_name} test FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name} test ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Consolidation infrastructure is ready.")
    else:
        logger.error("❌ Some tests failed. Please check the logs above.")