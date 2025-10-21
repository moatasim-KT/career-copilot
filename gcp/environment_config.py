"""
Environment-specific configuration management for Career Copilot deployment
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class EnvironmentConfig:
    """Manages environment-specific configuration for Google Cloud deployment"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = Path(__file__).parent / config_file
        self.config = self._load_config()
        self.environment = os.getenv('ENVIRONMENT', 'production')
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
    
    def get_environment_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration for specific environment"""
        env = environment or self.environment
        
        if env not in self.config.get('environments', {}):
            raise ValueError(f"Environment '{env}' not found in configuration")
        
        # Merge common config with environment-specific config
        common_config = self.config.get('common', {})
        env_config = self.config['environments'][env]
        
        # Deep merge configurations
        merged_config = self._deep_merge(common_config.copy(), env_config)
        merged_config['environment'] = env
        
        return merged_config
    
    def get_function_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Get Cloud Functions configuration"""
        config = self.get_environment_config(environment)
        return config.get('functions', {})
    
    def get_scheduler_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Get Cloud Scheduler configuration"""
        config = self.get_environment_config(environment)
        return config.get('scheduler', {})
    
    def get_monitoring_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Get monitoring configuration"""
        config = self.get_environment_config(environment)
        return config.get('monitoring', {})
    
    def get_firestore_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Get Firestore configuration"""
        config = self.get_environment_config(environment)
        return config.get('firestore', {})
    
    def get_iam_roles(self) -> list:
        """Get required IAM roles"""
        return self.config.get('common', {}).get('iam_roles', [])
    
    def get_required_apis(self) -> list:
        """Get required Google Cloud APIs"""
        return self.config.get('common', {}).get('required_apis', [])
    
    def get_environment_variables(self, environment: Optional[str] = None) -> Dict[str, str]:
        """Get environment variables for deployment"""
        config = self.get_environment_config(environment)
        
        # Base environment variables
        env_vars = {
            'ENVIRONMENT': config['environment'],
            'PROJECT_ID': config.get('project_id', os.getenv('PROJECT_ID', 'career-copilot')),
            'REGION': config.get('region', 'us-central1'),
            'LOG_LEVEL': config.get('monitoring', {}).get('log_level', 'INFO'),
            'FIRESTORE_DATABASE': config.get('firestore', {}).get('database_id', '(default)'),
        }
        
        # Add monitoring configuration
        monitoring = config.get('monitoring', {})
        if monitoring.get('enable_tracing'):
            env_vars['ENABLE_TRACING'] = 'true'
        
        # Add custom environment variables from config
        custom_env_vars = config.get('environment_variables', {})
        for key, value in custom_env_vars.items():
            # Replace placeholders
            if isinstance(value, str):
                value = value.replace('${PROJECT_ID}', env_vars['PROJECT_ID'])
                value = value.replace('${LOG_LEVEL}', env_vars['LOG_LEVEL'])
                value = value.replace('${ENABLE_TRACING}', env_vars.get('ENABLE_TRACING', 'false'))
            env_vars[key] = str(value)
        
        return env_vars
    
    def validate_environment(self, environment: str) -> bool:
        """Validate that environment configuration is complete"""
        try:
            config = self.get_environment_config(environment)
            
            # Required fields
            required_fields = [
                'project_id',
                'region',
                'functions',
                'scheduler',
                'monitoring'
            ]
            
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate function configuration
            functions = config['functions']
            required_function_fields = ['memory', 'timeout', 'max_instances']
            for field in required_function_fields:
                if field not in functions:
                    raise ValueError(f"Missing required function field: {field}")
            
            # Validate scheduler configuration
            scheduler = config['scheduler']
            required_scheduler_fields = ['job_ingestion', 'morning_briefing', 'evening_update']
            for field in required_scheduler_fields:
                if field not in scheduler:
                    raise ValueError(f"Missing required scheduler field: {field}")
            
            return True
            
        except Exception as e:
            print(f"Environment validation failed: {e}")
            return False
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base
    
    def generate_deployment_script(self, environment: str, output_file: str = None) -> str:
        """Generate environment-specific deployment script"""
        config = self.get_environment_config(environment)
        
        script_template = """#!/bin/bash
# Auto-generated deployment script for {environment} environment
set -e

PROJECT_ID="{project_id}"
REGION="{region}"
ENV="{environment}"

# Function configuration
MEMORY="{memory}"
TIMEOUT="{timeout}"
MAX_INSTANCES="{max_instances}"

# Scheduler configuration
JOB_INGESTION_SCHEDULE="{job_ingestion_schedule}"
MORNING_BRIEFING_SCHEDULE="{morning_briefing_schedule}"
EVENING_UPDATE_SCHEDULE="{evening_update_schedule}"

# Environment variables
ENV_VARS="{env_vars}"

echo "🚀 Deploying Career Copilot to Google Cloud ({environment})..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Run the main deployment script with environment-specific variables
export PROJECT_ID REGION ENV MEMORY TIMEOUT MAX_INSTANCES
export JOB_INGESTION_SCHEDULE MORNING_BRIEFING_SCHEDULE EVENING_UPDATE_SCHEDULE
export ENV_VARS

./deploy.sh
"""
        
        functions = config['functions']
        scheduler = config['scheduler']
        env_vars = self.get_environment_variables(environment)
        env_vars_str = ','.join([f"{k}={v}" for k, v in env_vars.items()])
        
        script_content = script_template.format(
            environment=environment,
            project_id=config['project_id'],
            region=config['region'],
            memory=functions['memory'],
            timeout=functions['timeout'],
            max_instances=functions['max_instances'],
            job_ingestion_schedule=scheduler['job_ingestion'],
            morning_briefing_schedule=scheduler['morning_briefing'],
            evening_update_schedule=scheduler['evening_update'],
            env_vars=env_vars_str
        )
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(script_content)
            os.chmod(output_file, 0o755)  # Make executable
        
        return script_content


# Global configuration instance
config_manager = EnvironmentConfig()


def get_config(environment: str = None) -> Dict[str, Any]:
    """Get configuration for specified environment"""
    return config_manager.get_environment_config(environment)


def get_env_vars(environment: str = None) -> Dict[str, str]:
    """Get environment variables for specified environment"""
    return config_manager.get_environment_variables(environment)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        env = sys.argv[1]
        if config_manager.validate_environment(env):
            print(f"✅ Environment '{env}' configuration is valid")
            config = get_config(env)
            print(f"📋 Configuration: {yaml.dump(config, default_flow_style=False)}")
        else:
            print(f"❌ Environment '{env}' configuration is invalid")
            sys.exit(1)
    else:
        print("Available environments:")
        for env in config_manager.config.get('environments', {}):
            print(f"  - {env}")