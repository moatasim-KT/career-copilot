#!/usr/bin/env python3
"""
Final Test Consolidation - Move remaining backend tests to proper locations
"""

import shutil
from pathlib import Path

def final_consolidation():
    """Move remaining tests to proper locations and clean up"""
    root_path = Path(".")
    
    print("🔄 Final test consolidation...")
    
    # Move remaining backend tests to appropriate locations
    backend_tests = root_path / "tests" / "backend"
    
    if backend_tests.exists():
        for test_file in backend_tests.rglob("*.py"):
            if test_file.name == "conftest.py":
                continue  # Skip conftest files
                
            # Determine target directory based on file name/content
            if any(keyword in test_file.name for keyword in ["integration", "api", "service"]):
                target_dir = root_path / "tests" / "integration"
            elif any(keyword in test_file.name for keyword in ["auth", "security", "jwt"]):
                target_dir = root_path / "tests" / "security"  
            elif any(keyword in test_file.name for keyword in ["performance", "monitoring"]):
                target_dir = root_path / "tests" / "performance"
            else:
                target_dir = root_path / "tests" / "unit"
                
            # Create target directory if needed
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Move file if it doesn't already exist
            target_file = target_dir / test_file.name
            if not target_file.exists():
                shutil.move(str(test_file), str(target_file))
                print(f"Moved {test_file.name} to {target_dir.name}/")
    
    # Remove empty backend test directory
    if backend_tests.exists():
        try:
            shutil.rmtree(backend_tests)
            print("Removed empty tests/backend directory")
        except:
            pass
    
    # Remove deployment tests directory (redundant)
    deployment_tests = root_path / "tests" / "deployment"
    if deployment_tests.exists():
        shutil.rmtree(deployment_tests)
        print("Removed tests/deployment directory")
    
    # Clean up any remaining empty directories
    for test_dir in ["tests/unit", "tests/integration", "tests/e2e", "tests/performance", "tests/security"]:
        test_path = root_path / test_dir
        test_path.mkdir(parents=True, exist_ok=True)
    
    print("✅ Final consolidation completed!")

if __name__ == "__main__":
    final_consolidation()