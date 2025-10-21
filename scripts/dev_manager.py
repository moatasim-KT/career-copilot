#!/usr/bin/env python3
"""
Development Manager for Career Copilot
Handles development workflow, testing, and environment management
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional

class DevManager:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()
        
    def start_development(self, services: Optional[List[str]] = None) -> bool:
        """Start development environment"""
        print("🚀 Starting development environment...")
        
        try:
            # Validate environment first
            if not self._validate_dev_environment():
                return False
            
            # Start services
            if services:
                cmd = ["docker-compose", "up", "-d"] + services
            else:
                cmd = ["docker-compose", "up", "-d"]
            
            result = subprocess.run(cmd, cwd=self.root_dir)
            
            if result.returncode == 0:
                print("✅ Development environment started")
                return True
            else:
                print("❌ Failed to start development environment")
                return False
                
        except Exception as e:
            print(f"❌ Development startup failed: {e}")
            return False
    
    def run_tests(self, test_type: str = "all") -> bool:
        """Run tests"""
        print(f"🧪 Running {test_type} tests...")
        
        try:
            if test_type == "unit":
                cmd = ["python", "-m", "pytest", "tests/unit/", "-v"]
            elif test_type == "integration":
                cmd = ["python", "tests/integration/run_all_integration_tests.py"]
            elif test_type == "consolidated":
                test_files = [
                    "tests/unit/test_recommendation_system.py",
                    "tests/unit/test_skill_system.py",
                    "tests/unit/test_notification_system_consolidated.py",
                    "tests/unit/test_analytics_system.py"
                ]
                cmd = ["python", "-m", "pytest"] + test_files + ["-v"]
            else:  # all
                cmd = ["python", "-m", "pytest", "tests/", "-v"]
            
            result = subprocess.run(cmd, cwd=self.root_dir)
            
            if result.returncode == 0:
                print(f"✅ {test_type} tests passed")
                return True
            else:
                print(f"❌ {test_type} tests failed")
                return False
                
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return False
    
    def setup_environment(self) -> bool:
        """Setup development environment"""
        print("⚙️  Setting up development environment...")
        
        try:
            # Create virtual environment if needed
            venv_path = self.root_dir / "backend" / "venv"
            if not venv_path.exists():
                print("Creating virtual environment...")
                subprocess.run([
                    sys.executable, "-m", "venv", str(venv_path)
                ], check=True)
            
            # Install dependencies
            pip_path = venv_path / "bin" / "pip"
            if not pip_path.exists():
                pip_path = venv_path / "Scripts" / "pip.exe"  # Windows
            
            if pip_path.exists():
                print("Installing dependencies...")
                subprocess.run([
                    str(pip_path), "install", "-r", "requirements.txt"
                ], cwd=self.root_dir, check=True)
            
            # Setup .env if needed
            env_file = self.root_dir / ".env"
            if not env_file.exists():
                template_file = self.root_dir / ".env.example"
                if template_file.exists():
                    import shutil
                    shutil.copy2(template_file, env_file)
                    print("✅ Created .env from template")
            
            print("✅ Development environment setup completed")
            return True
            
        except Exception as e:
            print(f"❌ Environment setup failed: {e}")
            return False
    
    def code_quality_check(self) -> bool:
        """Run code quality checks"""
        print("🔍 Running code quality checks...")
        
        checks = [
            ("Python syntax", ["python", "-m", "py_compile"] + list(self.root_dir.rglob("*.py"))),
            ("Import check", ["python", "-m", "pip", "check"])
        ]
        
        all_passed = True
        for check_name, cmd in checks:
            try:
                # Limit file list for syntax check
                if "py_compile" in cmd:
                    py_files = list(self.root_dir.rglob("*.py"))[:50]  # Limit to first 50 files
                    cmd = cmd[:3] + [str(f) for f in py_files]
                
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.root_dir)
                
                if result.returncode == 0:
                    print(f"✅ {check_name}: Passed")
                else:
                    print(f"❌ {check_name}: Failed")
                    all_passed = False
                    
            except Exception as e:
                print(f"⚠️  {check_name}: Error - {str(e)}")
                all_passed = False
        
        return all_passed
    
    def generate_docs(self) -> bool:
        """Generate documentation"""
        print("📚 Generating documentation...")
        
        try:
            docs_dir = self.root_dir / "docs"
            docs_dir.mkdir(exist_ok=True)
            
            # Generate API documentation
            api_doc = docs_dir / "API.md"
            with open(api_doc, 'w') as f:
                f.write("# Career Copilot API Documentation\n\n")
                f.write("## Endpoints\n\n")
                f.write("- GET /health - Health check\n")
                f.write("- GET /api/v1/jobs - List jobs\n")
                f.write("- POST /api/v1/jobs - Create job\n")
                f.write("- GET /api/v1/recommendations - Get recommendations\n")
            
            # Generate development guide
            dev_guide = docs_dir / "DEVELOPMENT.md"
            with open(dev_guide, 'w') as f:
                f.write("# Development Guide\n\n")
                f.write("## Quick Start\n\n")
                f.write("```bash\n")
                f.write("python scripts/dev_manager.py setup\n")
                f.write("python scripts/dev_manager.py start\n")
                f.write("python scripts/dev_manager.py test\n")
                f.write("```\n")
            
            print("✅ Documentation generated")
            return True
            
        except Exception as e:
            print(f"❌ Documentation generation failed: {e}")
            return False
    
    def _validate_dev_environment(self) -> bool:
        """Validate development environment"""
        required_files = [
            "requirements.txt",
            "docker-compose.yml",
            "backend/app/main.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not (self.root_dir / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ Missing required files: {', '.join(missing_files)}")
            return False
        
        return True
    
    def stop_services(self) -> bool:
        """Stop development services"""
        print("🛑 Stopping development services...")
        
        try:
            result = subprocess.run(["docker-compose", "down"], cwd=self.root_dir)
            
            if result.returncode == 0:
                print("✅ Services stopped")
                return True
            else:
                print("❌ Failed to stop services")
                return False
                
        except Exception as e:
            print(f"❌ Service stop failed: {e}")
            return False
    
    def show_logs(self, service: Optional[str] = None) -> bool:
        """Show service logs"""
        try:
            cmd = ["docker-compose", "logs"]
            if service:
                cmd.append(service)
            
            subprocess.run(cmd, cwd=self.root_dir)
            return True
            
        except Exception as e:
            print(f"❌ Failed to show logs: {e}")
            return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Career Copilot Development Manager")
    parser.add_argument("command", choices=[
        "setup", "start", "stop", "test", "quality", "docs", "logs"
    ])
    parser.add_argument("--type", help="Type for test command")
    parser.add_argument("--service", help="Specific service")
    
    args = parser.parse_args()
    
    manager = DevManager()
    
    try:
        if args.command == "setup":
            success = manager.setup_environment()
        elif args.command == "start":
            success = manager.start_development()
        elif args.command == "stop":
            success = manager.stop_services()
        elif args.command == "test":
            success = manager.run_tests(args.type or "all")
        elif args.command == "quality":
            success = manager.code_quality_check()
        elif args.command == "docs":
            success = manager.generate_docs()
        elif args.command == "logs":
            success = manager.show_logs(args.service)
        else:
            success = False
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()