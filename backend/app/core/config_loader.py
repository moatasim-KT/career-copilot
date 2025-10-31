"""
Configuration loader for the unified configuration system.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

from .config import Settings

load_dotenv()

class ConfigLoader:
    """Configuration loader for the unified configuration system."""

    def __init__(self, environment: Optional[str] = None):
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self.config_path = Path("config")

    def load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Load a YAML configuration file."""
        if not file_path.exists():
            return {}
        with open(file_path, "r") as file:
            return yaml.safe_load(file) or {}

    def load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load a JSON configuration file."""
        if not file_path.exists():
            return {}
        with open(file_path, "r") as file:
            return json.load(file)

    def merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    def load_config(self) -> Settings:
        """Load and merge all configuration files and return a Pydantic Settings object."""
        # Start with the base settings from environment variables and .env file
        settings = Settings()

        # Load YAML and JSON configuration files
        application_config = self.load_yaml(self.config_path / "application.yaml")
        environment_config = self.load_yaml(self.config_path / "environments" / f"{self.environment}.yaml")
        feature_flags = self.load_json(self.config_path / "feature_flags.json")
        llm_config = self.load_json(self.config_path / "llm_config.json")

        # Merge configurations
        config_dict = settings.dict()
        config_dict = self.merge_configs(config_dict, application_config)
        config_dict = self.merge_configs(config_dict, environment_config)
        config_dict = self.merge_configs(config_dict, {"feature_flags": feature_flags})
        config_dict = self.merge_configs(config_dict, {"llm": llm_config})

        return Settings.parse_obj(config_dict)


_config_loader: Optional[ConfigLoader] = None

def get_config_loader(environment: Optional[str] = None) -> ConfigLoader:
    """Get the global configuration loader instance."""
    global _config_loader
    if _config_loader is None or (environment and _config_loader.environment != environment):
        _config_loader = ConfigLoader(environment)
    return _config_loader

def get_settings() -> Settings:
    """Get the application settings."""
    loader = get_config_loader()
    return loader.load_config()
