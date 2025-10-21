#!/usr/bin/env python3
"""
Configuration setup script for Career Copilot.
Helps users initialize and configure the application.
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import secrets
import string
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigurationSetup:
    """Handles initial configuration setup."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"
        self.env_file = self.project_root / ".env"
        
    def setup_initial_config(self, environment: str = "development", interactive: bool = True):
        """Set up initial configuration for the application."""
        print("🚀 Setting up Career Copilot configuration...")
        print(f"Environment: {environment}")
        print()
        
        # Create necessary directories
        self._create_directories()
        
        # Copy environment template if .env doesn't exist
        if not self.env_file.exists():
            self._create_env_file(environment, interactive)
        else:
            print("✅ .env file already exists")
            
        # Generate secrets if needed
        self._generate_secrets(interactive)
        
        # Validate configuration
        self._validate_setup()
        
        print("\n🎉 Configuration setup completed!")
        print("\nNext steps:")
        print("1. Edit .env file with your API keys and credentials")
        print("2. Run: python config/validate_config.py")
        print("3. Start the application: python start_production.py")
        
    def _create_directories(self):
        """Create necessary directories."""
        directories = [
            "data",
            "data/chroma",
            "data/storage",
            "data/backups",
            "logs",
            "logs/audit",
            "secrets"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Set restrictive permissions for sensitive directories
            if directory in ["secrets", "logs/audit"]:
                os.chmod(dir_path, 0o700)
                
        print("✅ Created necessary directories")
        
    def _create_env_file(self, environment: str, interactive: bool):
        """Create .env file from template."""
        template_file = self.config_dir / "templates" / "env.template"
        
        if not template_file.exists():
            logger.error("Environment template file not found")
            return
            
        # Copy template to .env
        shutil.copy(template_file, self.env_file)
        
        # Update environment-specific settings
        self._update_env_file(environment, interactive)
        
        print("✅ Created .env file from template")
        
    def _update_env_file(self, environment: str, interactive: bool):
        """Update .env file with environment-specific settings."""
        with open(self.env_file, 'r') as f:
            content = f.read()
            
        # Update environment
        content = content.replace("ENVIRONMENT=development", f"ENVIRONMENT={environment}")
        
        if environment == "production":
            content = content.replace("DEVELOPMENT_MODE=true", "DEVELOPMENT_MODE=false")
            content = content.replace("PRODUCTION_MODE=false", "PRODUCTION_MODE=true")
            content = content.replace("API_DEBUG=false", "API_DEBUG=false")
            
        # Generate secure secrets
        jwt_secret = self._generate_secure_key(64)
        master_api_key = self._generate_secure_key(32)
        
        content = content.replace("JWT_SECRET_KEY=your_jwt_secret_key_here_change_in_production", 
                                f"JWT_SECRET_KEY={jwt_secret}")
        content = content.replace("MASTER_API_KEY=your_master_api_key_here", 
                                f"MASTER_API_KEY={master_api_key}")
        
        # Interactive configuration
        if interactive:
            content = self._interactive_config_update(content)
            
        with open(self.env_file, 'w') as f:
            f.write(content)
            
    def _interactive_config_update(self, content: str) -> str:
        """Interactively update configuration values."""
        print("\n📝 Interactive Configuration Setup")
        print("Press Enter to skip optional configurations")
        print()
        
        # OpenAI API Key (required)
        openai_key = input("Enter your OpenAI API Key (required): ").strip()
        if openai_key:
            content = content.replace("OPENAI_API_KEY=your_openai_api_key_here", 
                                    f"OPENAI_API_KEY={openai_key}")
            
        # Groq API Key (optional)
        groq_key = input("Enter your Groq API Key (optional, for fast inference): ").strip()
        if groq_key:
            content = content.replace("GROQ_API_KEY=your_groq_api_key_here", 
                                    f"GROQ_API_KEY={groq_key}")
            content = content.replace("GROQ_ENABLED=true", "GROQ_ENABLED=true")
            
        # LangSmith API Key (optional)
        langsmith_key = input("Enter your LangSmith API Key (optional, for AI tracing): ").strip()
        if langsmith_key:
            content = content.replace("LANGSMITH_API_KEY=your_langsmith_api_key_here", 
                                    f"LANGSMITH_API_KEY={langsmith_key}")
            content = content.replace("LANGSMITH_TRACING=false", "LANGSMITH_TRACING=true")
            
        return content
        
    def _generate_secrets(self, interactive: bool):
        """Generate and save secret keys."""
        secrets_dir = self.project_root / "secrets"
        
        # Generate JWT secret if not exists
        jwt_file = secrets_dir / "jwt_secret.txt"
        if not jwt_file.exists():
            jwt_secret = self._generate_secure_key(64)
            with open(jwt_file, 'w') as f:
                f.write(jwt_secret)
            os.chmod(jwt_file, 0o600)
            
        # Generate API key if not exists
        api_key_file = secrets_dir / "master_api_key.txt"
        if not api_key_file.exists():
            api_key = self._generate_secure_key(32)
            with open(api_key_file, 'w') as f:
                f.write(api_key)
            os.chmod(api_key_file, 0o600)
            
        print("✅ Generated security secrets")
        
    def _generate_secure_key(self, length: int = 32) -> str:
        """Generate a secure random key."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
        
    def _validate_setup(self):
        """Validate the setup configuration."""
        try:
            # Check if .env file exists and is readable
            if not self.env_file.exists():
                logger.error(".env file not found")
                return False
                
            # Check if required directories exist
            required_dirs = ["data", "logs", "secrets"]
            for directory in required_dirs:
                if not (self.project_root / directory).exists():
                    logger.error(f"Required directory not found: {directory}")
                    return False
                    
            print("✅ Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
            
    def create_docker_compose(self, environment: str = "development"):
        """Create docker-compose.yml from template."""
        template_file = self.config_dir / "templates" / "docker-compose.template.yaml"
        output_file = self.project_root / "docker-compose.yml"
        
        if not template_file.exists():
            logger.error("Docker compose template not found")
            return
            
        # Copy template
        shutil.copy(template_file, output_file)
        
        print("✅ Created docker-compose.yml from template")
        
    def setup_monitoring(self):
        """Set up monitoring configuration."""
        monitoring_dir = self.project_root / "monitoring"
        
        # Create monitoring directories
        for subdir in ["prometheus", "grafana/dashboards", "grafana/datasources"]:
            (monitoring_dir / subdir).mkdir(parents=True, exist_ok=True)
            
        print("✅ Set up monitoring directories")
        
    def create_systemd_service(self, service_name: str = "career-copilot"):
        """Create systemd service file for production deployment."""
        service_content = f"""[Unit]
Description=Career Copilot Application
After=network.target

[Service]
Type=simple
User=career-copilot
WorkingDirectory={self.project_root}
Environment=ENVIRONMENT=production
ExecStart={sys.executable} start_production.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        service_file = self.project_root / f"{service_name}.service"
        with open(service_file, 'w') as f:
            f.write(service_content)
            
        print(f"✅ Created systemd service file: {service_file}")
        print(f"To install: sudo cp {service_file} /etc/systemd/system/")
        print(f"To enable: sudo systemctl enable {service_name}")
        
    def show_configuration_summary(self):
        """Show current configuration summary."""
        print("\n📊 Configuration Summary")
        print("=" * 50)
        
        # Check .env file
        if self.env_file.exists():
            print("✅ .env file: Present")
        else:
            print("❌ .env file: Missing")
            
        # Check directories
        directories = ["data", "logs", "secrets", "config"]
        for directory in directories:
            if (self.project_root / directory).exists():
                print(f"✅ {directory}/ directory: Present")
            else:
                print(f"❌ {directory}/ directory: Missing")
                
        # Check configuration files
        config_files = [
            "config/base.yaml",
            "config/monitoring.yaml",
            "config/feature_flags.json"
        ]
        
        for config_file in config_files:
            if (self.project_root / config_file).exists():
                print(f"✅ {config_file}: Present")
            else:
                print(f"❌ {config_file}: Missing")
                
        print("=" * 50)


def main():
    """Main setup function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Career Copilot Configuration Setup")
    parser.add_argument("--environment", "-e", default="development", 
                       choices=["development", "production", "staging", "testing"],
                       help="Target environment")
    parser.add_argument("--non-interactive", "-n", action="store_true",
                       help="Run in non-interactive mode")
    parser.add_argument("--docker", "-d", action="store_true",
                       help="Create Docker configuration")
    parser.add_argument("--monitoring", "-m", action="store_true",
                       help="Set up monitoring")
    parser.add_argument("--systemd", "-s", action="store_true",
                       help="Create systemd service file")
    parser.add_argument("--summary", action="store_true",
                       help="Show configuration summary")
    
    args = parser.parse_args()
    
    setup = ConfigurationSetup()
    
    if args.summary:
        setup.show_configuration_summary()
        return
        
    # Run main setup
    setup.setup_initial_config(
        environment=args.environment,
        interactive=not args.non_interactive
    )
    
    # Optional components
    if args.docker:
        setup.create_docker_compose(args.environment)
        
    if args.monitoring:
        setup.setup_monitoring()
        
    if args.systemd:
        setup.create_systemd_service()
        
    # Show summary
    setup.show_configuration_summary()


if __name__ == "__main__":
    main()