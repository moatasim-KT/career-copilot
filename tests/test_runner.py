#!/usr/bin/env python3
"""
Consolidated Test Runner for Career Copilot

This script provides a unified interface for running all types of tests:
- Unit tests
- Integration tests  
- End-to-end tests
- Performance tests
- Security tests
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional

class TestRunner:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.tests_path = self.root_path / "tests"
        
    def run_unit_tests(self, verbose: bool = False) -> bool:
        """Run unit tests"""
        print("🧪 Running unit tests...")
        
        cmd = ["python", "-m", "pytest", "tests/unit/"]
        if verbose:
            cmd.append("-v")
        cmd.extend(["--tb=short", "--disable-warnings"])
        
        try:
            result = subprocess.run(cmd, cwd=self.root_path, capture_output=False)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Unit tests failed: {e}")
            return False
    
    def run_integration_tests(self, verbose: bool = False) -> bool:
        """Run integration tests"""
        print("🔗 Running integration tests...")
        
        cmd = ["python", "-m", "pytest", "tests/integration/"]
        if verbose:
            cmd.append("-v")
        cmd.extend(["--tb=short", "--disable-warnings"])
        
        try:
            result = subprocess.run(cmd, cwd=self.root_path, capture_output=False)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Integration tests failed: {e}")
            return False
    
    def run_e2e_tests(self, verbose: bool = False) -> bool:
        """Run end-to-end tests"""
        print("🎯 Running end-to-end tests...")
        
        cmd = ["python", "-m", "pytest", "tests/e2e/"]
        if verbose:
            cmd.append("-v")
        cmd.extend(["--tb=short", "--disable-warnings"])
        
        try:
            result = subprocess.run(cmd, cwd=self.root_path, capture_output=False)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ E2E tests failed: {e}")
            return False
    
    def run_performance_tests(self, verbose: bool = False) -> bool:
        """Run performance tests"""
        print("⚡ Running performance tests...")
        
        cmd = ["python", "-m", "pytest", "tests/performance/"]
        if verbose:
            cmd.append("-v")
        cmd.extend(["--tb=short", "--disable-warnings"])
        
        try:
            result = subprocess.run(cmd, cwd=self.root_path, capture_output=False)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Performance tests failed: {e}")
            return False
    
    def run_security_tests(self, verbose: bool = False) -> bool:
        """Run security tests"""
        print("🔒 Running security tests...")
        
        cmd = ["python", "-m", "pytest", "tests/security/"]
        if verbose:
            cmd.append("-v")
        cmd.extend(["--tb=short", "--disable-warnings"])
        
        try:
            result = subprocess.run(cmd, cwd=self.root_path, capture_output=False)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Security tests failed: {e}")
            return False
    
    def run_all_tests(self, verbose: bool = False) -> bool:
        """Run all tests"""
        print("🚀 Running all tests...")
        
        cmd = ["python", "-m", "pytest", "tests/"]
        if verbose:
            cmd.append("-v")
        cmd.extend(["--tb=short", "--disable-warnings", "--maxfail=5"])
        
        try:
            result = subprocess.run(cmd, cwd=self.root_path, capture_output=False)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ All tests failed: {e}")
            return False
    
    def run_quick_tests(self, verbose: bool = False) -> bool:
        """Run quick smoke tests"""
        print("💨 Running quick smoke tests...")
        
        cmd = ["python", "-m", "pytest", "tests/unit/", "-k", "not slow"]
        if verbose:
            cmd.append("-v")
        cmd.extend(["--tb=short", "--disable-warnings", "--maxfail=3"])
        
        try:
            result = subprocess.run(cmd, cwd=self.root_path, capture_output=False)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Quick tests failed: {e}")
            return False
    
    def check_test_structure(self) -> bool:
        """Check if test structure is properly organized"""
        print("📁 Checking test structure...")
        
        required_dirs = [
            "tests/unit/",
            "tests/integration/", 
            "tests/e2e/",
            "tests/performance/",
            "tests/security/"
        ]
        
        missing_dirs = []
        for test_dir in required_dirs:
            dir_path = self.root_path / test_dir
            if not dir_path.exists():
                missing_dirs.append(test_dir)
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"📁 Created missing directory: {test_dir}")
        
        if missing_dirs:
            print(f"⚠️ Created {len(missing_dirs)} missing test directories")
        else:
            print("✅ Test structure is properly organized")
        
        return True

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Career Copilot Test Runner")
    parser.add_argument("test_type", nargs="?", default="all", 
                       choices=["unit", "integration", "e2e", "performance", "security", "all", "quick", "check"],
                       help="Type of tests to run")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    root_path = Path(__file__).parent.parent
    runner = TestRunner(str(root_path))
    
    # Check test structure first
    if args.test_type == "check":
        success = runner.check_test_structure()
        sys.exit(0 if success else 1)
    
    runner.check_test_structure()
    
    # Run the specified tests
    if args.test_type == "unit":
        success = runner.run_unit_tests(args.verbose)
    elif args.test_type == "integration":
        success = runner.run_integration_tests(args.verbose)
    elif args.test_type == "e2e":
        success = runner.run_e2e_tests(args.verbose)
    elif args.test_type == "performance":
        success = runner.run_performance_tests(args.verbose)
    elif args.test_type == "security":
        success = runner.run_security_tests(args.verbose)
    elif args.test_type == "quick":
        success = runner.run_quick_tests(args.verbose)
    else:  # all
        success = runner.run_all_tests(args.verbose)
    
    if success:
        print("✅ Tests completed successfully!")
    else:
        print("❌ Some tests failed!")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()