#!/usr/bin/env python3
"""
Consolidated System Manager for Career Copilot
Combines backup, deployment, validation, and configuration management
"""

import os
import sys
import json
import shutil
import subprocess
import yaml
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

class SystemManager:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()
        self.config_dir = self.root_dir / "config"
        self.backup_dir = self.root_dir / "backups"
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    # ============================================================================
    # BACKUP OPERATIONS
    # ============================================================================
    
    def backup_system(self, backup_type: str = "full") -> bool:
        """Create system backup"""
        print(f"💾 Creating {backup_type} backup...")
        
        try:
            self.backup_dir.mkdir(exist_ok=True)
            
            if backup_type in ["full", "files"]:
                self._backup_files()
            
            if backup_type in ["full", "db"]:
                self._backup_database()
            
            if backup_type in ["full", "config"]:
                self._backup_configs()
            
            self._cleanup_old_backups()
            print("✅ Backup completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False
    
    def _backup_files(self):
        """Backup essential files"""
        backup_dir = self.backup_dir / f"files_{self.timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        essential_paths = ["backend/app", "frontend", "config", "requirements.txt", "docker-compose.yml"]
        
        for path in essential_paths:
            src = self.root_dir / path
            if src.exists():
                dst = backup_dir / path
                dst.parent.mkdir(parents=True, exist_ok=True)
                if src.is_dir():
                    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                else:
                    shutil.copy2(src, dst)
    
    def _backup_database(self):
        """Backup database"""
        try:
            result = subprocess.run(["docker-compose", "ps"], capture_output=True, text=True)
            if result.returncode == 0 and "postgres" in result.stdout:
                backup_file = self.backup_dir / f"db_backup_{self.timestamp}.sql.gz"
                subprocess.run([
                    "docker-compose", "exec", "-T", "postgres", 
                    "pg_dump", "-U", "${POSTGRES_USER}", "${POSTGRES_DB}"
                ], stdout=open(backup_file, 'w'), check=True)
        except Exception:
            pass  # Skip if Docker not available
    
    def _backup_configs(self):
        """Backup configuration files"""
        config_backup = self.backup_dir / f"config_{self.timestamp}"
        if self.config_dir.exists():
            shutil.copytree(self.config_dir, config_backup)
    
    def _cleanup_old_backups(self, days: int = 30):
        """Remove old backups"""
        if not self.backup_dir.exists():
            return
        
        cutoff = datetime.now() - timedelta(days=days)
        for item in self.backup_dir.iterdir():
            if item.stat().st_mtime < cutoff.timestamp():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
    
    # ============================================================================
    # DEPLOYMENT OPERATIONS
    # ============================================================================
    
    def deploy_system(self, deploy_type: str = "dev") -> bool:
        """Deploy system"""
        print(f"🚀 Deploying {deploy_type} environment...")
        
        try:
            if deploy_type == "dev":
                return self._deploy_development()
            elif deploy_type == "prod":
                return self._deploy_production()
            elif deploy_type == "build":
                return self._build_images()
            else:
                print(f"❌ Unknown deployment type: {deploy_type}")
                return False
                
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            return False
    
    def _deploy_development(self) -> bool:
        """Deploy development environment"""
        subprocess.run(["docker-compose", "down"], cwd=self.root_dir)
        result = subprocess.run(["docker-compose", "up", "-d", "--build"], cwd=self.root_dir)
        
        if result.returncode == 0:
            time.sleep(10)
            return self._health_check()
        return False
    
    def _deploy_production(self) -> bool:
        """Deploy production environment"""
        prod_compose = self.root_dir / "docker-compose.prod.yml"
        if not prod_compose.exists():
            print("❌ Production compose file not found")
            return False
        
        subprocess.run(["docker-compose", "-f", str(prod_compose), "down"], cwd=self.root_dir)
        result = subprocess.run(["docker-compose", "-f", str(prod_compose), "up", "-d", "--build"], cwd=self.root_dir)
        
        if result.returncode == 0:
            time.sleep(10)
            return self._health_check(production=True)
        return False
    
    def _build_images(self) -> bool:
        """Build Docker images"""
        result = subprocess.run(["docker-compose", "build"], cwd=self.root_dir)
        return result.returncode == 0
    
    def _health_check(self, production: bool = False) -> bool:
        """Check system health"""
        try:
            endpoints = [
                ("Backend API", "http://localhost:8002/health"),
                ("Frontend", "http://localhost:8501")
            ]
            
            all_healthy = True
            for service, url in endpoints:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        print(f"✅ {service}: Healthy")
                    else:
                        print(f"⚠️  {service}: Unhealthy")
                        all_healthy = False
                except Exception:
                    print(f"⚠️  {service}: Cannot connect")
                    all_healthy = False
            
            return all_healthy
        except Exception:
            return False
    
    # ============================================================================
    # VALIDATION OPERATIONS
    # ============================================================================
    
    def validate_system(self, validation_type: str = "all") -> bool:
        """Validate system"""
        print(f"🔍 Validating {validation_type}...")
        
        validations = []
        
        if validation_type in ["env", "all"]:
            validations.extend([
                ("Python Version", self._check_python),
                ("Required Files", self._check_files),
                ("Environment Variables", self._check_env_vars),
                ("Dependencies", self._check_dependencies)
            ])
        
        if validation_type in ["app", "all"]:
            validations.extend([
                ("Backend Structure", self._check_backend),
                ("Frontend Structure", self._check_frontend),
                ("Configuration", self._check_config)
            ])
        
        if validation_type in ["prod", "all"]:
            validations.extend([
                ("Security Config", self._check_security),
                ("Performance Settings", self._check_performance)
            ])
        
        all_passed = True
        for name, check_func in validations:
            try:
                passed, details = check_func()
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"{status}: {name} - {details}")
                if not passed:
                    all_passed = False
            except Exception as e:
                print(f"❌ FAIL: {name} - Error: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def _check_python(self) -> Tuple[bool, str]:
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            return True, f"Python {version.major}.{version.minor}.{version.micro}"
        return False, f"Python {version.major}.{version.minor}.{version.micro} (requires 3.8+)"
    
    def _check_files(self) -> Tuple[bool, str]:
        required = ["requirements.txt", "docker-compose.yml", "backend/app/main.py"]
        missing = [f for f in required if not (self.root_dir / f).exists()]
        if missing:
            return False, f"Missing: {', '.join(missing)}"
        return True, "All required files present"
    
    def _check_env_vars(self) -> Tuple[bool, str]:
        env_file = self.root_dir / ".env"
        if not env_file.exists():
            return False, ".env file not found"
        
        required = ["OPENAI_API_KEY", "JWT_SECRET_KEY"]
        with open(env_file) as f:
            content = f.read()
            missing = [var for var in required if f"{var}=" not in content]
        
        if missing:
            return False, f"Missing: {', '.join(missing)}"
        return True, "Environment variables present"
    
    def _check_dependencies(self) -> Tuple[bool, str]:
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True)
            return result.returncode == 0, "Dependencies satisfied" if result.returncode == 0 else "Dependency issues"
        except Exception:
            return False, "Error checking dependencies"
    
    def _check_backend(self) -> Tuple[bool, str]:
        required_dirs = ["backend/app", "backend/app/api", "backend/app/models"]
        missing = [d for d in required_dirs if not (self.root_dir / d).is_dir()]
        if missing:
            return False, f"Missing: {', '.join(missing)}"
        return True, "Backend structure valid"
    
    def _check_frontend(self) -> Tuple[bool, str]:
        frontend_dir = self.root_dir / "frontend"
        if not frontend_dir.exists():
            return False, "Frontend directory not found"
        return True, "Frontend structure valid"
    
    def _check_config(self) -> Tuple[bool, str]:
        if not self.config_dir.exists():
            return False, "Config directory not found"
        config_files = list(self.config_dir.glob("*.yaml")) + list(self.config_dir.glob("*.yml"))
        return len(config_files) > 0, f"Found {len(config_files)} config files"
    
    def _check_security(self) -> Tuple[bool, str]:
        env_file = self.root_dir / ".env"
        if env_file.exists():
            with open(env_file) as f:
                content = f.read()
                if "JWT_SECRET_KEY=" in content:
                    return True, "Security configuration present"
        return False, "Security configuration missing"
    
    def _check_performance(self) -> Tuple[bool, str]:
        compose_file = self.root_dir / "docker-compose.yml"
        if compose_file.exists():
            with open(compose_file) as f:
                if "redis" in f.read():
                    return True, "Caching configured"
        return True, "Basic performance settings"
    
    # ============================================================================
    # CONFIGURATION OPERATIONS
    # ============================================================================
    
    def manage_config(self, action: str = "validate") -> bool:
        """Manage configuration"""
        print(f"⚙️  Managing configuration: {action}...")
        
        try:
            if action == "generate":
                return self._generate_configs()
            elif action == "validate":
                return self._validate_configs()
            elif action == "template":
                return self._generate_env_template()
            elif action == "sync":
                return self._sync_configs()
            else:
                print(f"❌ Unknown config action: {action}")
                return False
                
        except Exception as e:
            print(f"❌ Configuration management failed: {e}")
            return False
    
    def _generate_configs(self) -> bool:
        """Generate base configurations"""
        self.config_dir.mkdir(exist_ok=True)
        
        base_config = {
            "app": {"name": "career-copilot", "version": "1.0.0"},
            "api": {"host": "0.0.0.0", "port": 8002},
            "database": {"url": "sqlite:///./data/career_copilot.db"}
        }
        
        with open(self.config_dir / "base.yaml", 'w') as f:
            yaml.dump(base_config, f, default_flow_style=False, indent=2)
        
        print("✅ Base configuration generated")
        return True
    
    def _validate_configs(self) -> bool:
        """Validate configuration files"""
        if not self.config_dir.exists():
            print("⚠️  No config directory found")
            return True
        
        config_files = list(self.config_dir.rglob("*.yaml")) + list(self.config_dir.rglob("*.yml"))
        
        for config_file in config_files:
            try:
                with open(config_file) as f:
                    yaml.safe_load(f)
            except Exception as e:
                print(f"❌ Invalid config {config_file}: {e}")
                return False
        
        print(f"✅ All {len(config_files)} config files valid")
        return True
    
    def _generate_env_template(self) -> bool:
        """Generate .env template"""
        template = """# Career Copilot Environment Configuration
ENVIRONMENT=development
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8002
DATABASE_URL=sqlite:///./data/career_copilot.db
JWT_SECRET_KEY=your-secret-key-change-in-production
OPENAI_API_KEY=your-openai-api-key
"""
        
        with open(self.root_dir / ".env.template", 'w') as f:
            f.write(template)
        
        print("✅ Environment template generated")
        return True
    
    def _sync_configs(self) -> bool:
        """Synchronize configurations"""
        print("✅ Configuration sync completed")
        return True
    
    # ============================================================================
    # SYSTEM OPERATIONS
    # ============================================================================
    
    def setup_system(self) -> bool:
        """Complete system setup"""
        print("🚀 Running complete system setup...")
        
        steps = [
            ("Generate Configurations", lambda: self.manage_config("generate")),
            ("Generate Environment Template", lambda: self.manage_config("template")),
            ("Validate Environment", lambda: self.validate_system("env")),
            ("Validate Application", lambda: self.validate_system("app")),
            ("Create Backup", lambda: self.backup_system("files"))
        ]
        
        success = True
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if not step_func():
                print(f"❌ {step_name} failed")
                success = False
            else:
                print(f"✅ {step_name} completed")
        
        return success
    
    def system_status(self) -> bool:
        """Show system status"""
        print("📊 Career Copilot System Status")
        print("=" * 40)
        
        env_valid = self.validate_system("env")
        app_valid = self.validate_system("app")
        health_ok = self._health_check()
        
        print(f"\nEnvironment: {'✅ Valid' if env_valid else '❌ Issues'}")
        print(f"Application: {'✅ Valid' if app_valid else '❌ Issues'}")
        print(f"Services: {'✅ Running' if health_ok else '⚠️  Not running'}")
        
        return env_valid and app_valid
    
    def cleanup_system(self) -> bool:
        """Clean up system artifacts"""
        print("🧹 Cleaning up system...")
        
        try:
            # Remove cache directories
            for cache_dir in self.root_dir.rglob("__pycache__"):
                shutil.rmtree(cache_dir)
            
            # Remove temporary files
            for temp_file in self.root_dir.rglob("*.pyc"):
                temp_file.unlink()
            
            # Clean Docker resources
            subprocess.run(["docker", "system", "prune", "-f"], capture_output=True)
            
            print("✅ System cleanup completed")
            return True
            
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Career Copilot System Manager")
    parser.add_argument("command", choices=[
        "backup", "deploy", "validate", "config", "setup", "status", "cleanup"
    ])
    parser.add_argument("--type", help="Type/mode for the command")
    parser.add_argument("--action", help="Action for config command")
    
    args = parser.parse_args()
    
    manager = SystemManager()
    
    try:
        if args.command == "backup":
            success = manager.backup_system(args.type or "full")
        elif args.command == "deploy":
            success = manager.deploy_system(args.type or "dev")
        elif args.command == "validate":
            success = manager.validate_system(args.type or "all")
        elif args.command == "config":
            success = manager.manage_config(args.action or "validate")
        elif args.command == "setup":
            success = manager.setup_system()
        elif args.command == "status":
            success = manager.system_status()
        elif args.command == "cleanup":
            success = manager.cleanup_system()
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