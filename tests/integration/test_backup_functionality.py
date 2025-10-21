#!/usr/bin/env python3
"""
Test backup functionality
"""

import os
import shutil
import sqlite3
import tempfile
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_backup():
    """Test database backup functionality"""
    logger.info("Testing database backup...")
    
    # Create a test database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        test_db_path = tmp_db.name
    
    try:
        # Create test database with data
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE test_contracts (
                id INTEGER PRIMARY KEY,
                name TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute(
            "INSERT INTO test_contracts (name, content) VALUES (?, ?)",
            ("Test Contract", "This is test contract content")
        )
        
        conn.commit()
        conn.close()
        
        # Create backup
        backup_path = test_db_path + '.backup'
        shutil.copy2(test_db_path, backup_path)
        
        # Verify backup
        backup_conn = sqlite3.connect(backup_path)
        backup_cursor = backup_conn.cursor()
        backup_cursor.execute("SELECT COUNT(*) FROM test_contracts")
        count = backup_cursor.fetchone()[0]
        backup_conn.close()
        
        logger.info(f"Backup test: Original DB has data, backup has {count} records")
        
        # Test restoration
        os.remove(test_db_path)  # Simulate data loss
        shutil.copy2(backup_path, test_db_path)  # Restore
        
        # Verify restoration
        restored_conn = sqlite3.connect(test_db_path)
        restored_cursor = restored_conn.cursor()
        restored_cursor.execute("SELECT name FROM test_contracts")
        restored_name = restored_cursor.fetchone()[0]
        restored_conn.close()
        
        logger.info(f"Restoration test: Restored contract name: {restored_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"Database backup test failed: {e}")
        return False
    finally:
        # Cleanup
        for path in [test_db_path, backup_path]:
            if os.path.exists(path):
                os.remove(path)

def test_file_backup():
    """Test file backup functionality"""
    logger.info("Testing file backup...")
    
    try:
        # Create test directory structure
        test_dir = Path('test_backup_source')
        backup_dir = Path('test_backup_destination')
        
        test_dir.mkdir(exist_ok=True)
        backup_dir.mkdir(exist_ok=True)
        
        # Create test files
        (test_dir / 'test1.txt').write_text('Test file 1 content')
        (test_dir / 'subdir').mkdir(exist_ok=True)
        (test_dir / 'subdir' / 'test2.txt').write_text('Test file 2 content')
        
        # Perform backup
        shutil.copytree(test_dir, backup_dir / 'source', dirs_exist_ok=True)
        
        # Verify backup
        backup_files = list((backup_dir / 'source').rglob('*.txt'))
        logger.info(f"File backup test: {len(backup_files)} files backed up")
        
        # Test restoration
        shutil.rmtree(test_dir)  # Simulate data loss
        shutil.copytree(backup_dir / 'source', test_dir)  # Restore
        
        # Verify restoration
        restored_files = list(test_dir.rglob('*.txt'))
        logger.info(f"File restoration test: {len(restored_files)} files restored")
        
        return len(backup_files) == len(restored_files) == 2
        
    except Exception as e:
        logger.error(f"File backup test failed: {e}")
        return False
    finally:
        # Cleanup
        for path in [test_dir, backup_dir]:
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)

def main():
    """Run backup functionality tests"""
    logger.info("Starting backup functionality tests...")
    
    db_test_passed = test_database_backup()
    file_test_passed = test_file_backup()
    
    logger.info(f"Database backup test: {'PASSED' if db_test_passed else 'FAILED'}")
    logger.info(f"File backup test: {'PASSED' if file_test_passed else 'FAILED'}")
    
    overall_passed = db_test_passed and file_test_passed
    logger.info(f"Overall backup tests: {'PASSED' if overall_passed else 'FAILED'}")
    
    return overall_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)