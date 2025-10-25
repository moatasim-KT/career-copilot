"""
Simple test to verify basic consolidation functionality.
"""

import tempfile
import logging
from pathlib import Path

from .backup_system import BackupSystem
from .compatibility_layer import CompatibilityLayer
from .tracking_system import ConsolidationTracker, ConsolidationType
from .file_mapping import FileMappingSystem, MappingType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_basic_functionality():
    """Test basic functionality without complex interactions."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Test backup system
        logger.info("Testing backup system...")
        backup_system = BackupSystem(str(temp_path / "backups"))
        
        test_file = temp_path / "test.py"
        test_file.write_text("print('hello')")
        
        backup_id = backup_system.create_backup(str(test_file), "test_phase")
        assert backup_id is not None, "Backup creation failed"
        logger.info("✓ Backup system works")
        
        # Test tracking system
        logger.info("Testing tracking system...")
        tracker = ConsolidationTracker(str(temp_path / "tracking.json"))
        tracker.initialize_project(100)
        
        phase_id = tracker.create_phase(
            "Test Phase", "Test description", 1, ConsolidationType.MODULE_CONSOLIDATION
        )
        assert phase_id is not None, "Phase creation failed"
        logger.info("✓ Tracking system works")
        
        # Test file mapping system
        logger.info("Testing file mapping system...")
        file_mapper = FileMappingSystem(str(temp_path / "mappings.json"))
        
        mapping_id = file_mapper.create_mapping(
            original_files=[str(test_file)],
            consolidated_files=[str(temp_path / "consolidated.py")],
            mapping_type=MappingType.MANY_TO_ONE,
            consolidation_phase="test_phase"
        )
        assert mapping_id is not None, "Mapping creation failed"
        logger.info("✓ File mapping system works")
        
        # Test compatibility layer
        logger.info("Testing compatibility layer...")
        compat_layer = CompatibilityLayer(str(temp_path / "compat.json"))
        compat_layer.add_mapping("old_module", "new_module")
        
        mappings = compat_layer.list_mappings()
        assert len(mappings) == 1, "Compatibility mapping failed"
        logger.info("✓ Compatibility layer works")
        
        logger.info("🎉 All basic tests passed!")
        return True


if __name__ == "__main__":
    try:
        test_basic_functionality()
        print("SUCCESS: All tests passed!")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()