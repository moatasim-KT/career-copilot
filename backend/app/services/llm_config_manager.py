"""
LLM Configuration Manager
Manages configuration for multiple LLM providers and routing strategies.
"""

import json
import os
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..core.config import get_settings
from ..core.logging import get_logger
from .enhanced_llm_manager import ProviderConfig, LLMProvider, TaskType, RoutingCriteria

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class LLMManagerConfig:
    """Configuration for the LLM Manager."""
    providers: Dict[str, ProviderConfig]
    task_routing: Dict[TaskType, List[str]]
    default_routing_criteria: RoutingCriteria
    cache_ttl: int
    max_retries: int
    fallback_enabled: bool
    circuit_breaker_threshold: int
    circuit_breaker_timeout: int


class LLMConfigManager:
    """Manages LLM configuration with persistence and validation."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager."""
        self.config_path = config_path or self._get_default_config_path()
        self.config: Optional[LLMManagerConfig] = None
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / "llm_config.json")
    
    def _load_config(self):
        """Load configuration from file or create default."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                self.config = self._parse_config_data(config_data)
                logger.info(f"Loaded LLM configuration from {self.config_path}")
            else:
                self.config = self._create_default_config()
                self._save_config()
                logger.info("Created default LLM configuration")
        except Exception as e:
            logger.error(f"Failed to load LLM configuration: {e}")
            self.config = self._create_default_config()
    
    def _parse_config_data(self, config_data: Dict[str, Any]) -> LLMManagerConfig:
        """Parse configuration data from JSON."""
        # Parse providers
        providers = {}
        for provider_id, provider_data in config_data.get("providers", {}).items():
            providers[provider_id] = ProviderConfig(
                provider=LLMProvider(provider_data["provider"]),
                model_name=provider_data["model_name"],
                api_key=provider_data.get("api_key"),
                base_url=provider_data.get("base_url"),
                temperature=provider_data.get("temperature", 0.1),
                max_tokens=provider_data.get("max_tokens", 4000),
                cost_per_token=provider_data.get("cost_per_token", 0.0),
                rate_limit_rpm=provider_data.get("rate_limit_rpm", 60),
                rate_limit_tpm=provider_data.get("rate_limit_tpm", 40000),
                timeout=provider_data.get("timeout", 60),
                priority=provider_data.get("priority", 1),
                capabilities=provider_data.get("capabilities", []),
                enabled=provider_data.get("enabled", True),
                metadata=provider_data.get("metadata", {})
            )
        
        # Parse task routing
        task_routing = {}
        for task_type_str, provider_list in config_data.get("task_routing", {}).items():
            task_routing[TaskType(task_type_str)] = provider_list
        
        return LLMManagerConfig(
            providers=providers,
            task_routing=task_routing,
            default_routing_criteria=RoutingCriteria(
                config_data.get("default_routing_criteria", "cost")
            ),
            cache_ttl=config_data.get("cache_ttl", 3600),
            max_retries=config_data.get("max_retries", 3),
            fallback_enabled=config_data.get("fallback_enabled", True),
            circuit_breaker_threshold=config_data.get("circuit_breaker_threshold", 5),
            circuit_breaker_timeout=config_data.get("circuit_breaker_timeout", 60)
        )
    
    def _create_default_config(self) -> LLMManagerConfig:
        """Create default configuration."""
        providers = {}
        
        # OpenAI providers
        if hasattr(settings, 'openai_api_key') and settings.openai_api_key:
            providers["openai-gpt4"] = ProviderConfig(
                provider=LLMProvider.OPENAI,
                model_name="gpt-4",
                temperature=0.1,
                max_tokens=4000,
                cost_per_token=0.00003,
                rate_limit_rpm=60,
                rate_limit_tpm=40000,
                priority=1,
                capabilities=["analysis", "reasoning", "complex_tasks"],
                metadata={"quality": "high", "speed": "medium"}
            )
            
            providers["openai-gpt35"] = ProviderConfig(
                provider=LLMProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                temperature=0.1,
                max_tokens=4000,
                cost_per_token=0.000002,
                rate_limit_rpm=3500,
                rate_limit_tpm=90000,
                priority=2,
                capabilities=["generation", "communication", "simple_analysis"],
                metadata={"quality": "medium", "speed": "fast"}
            )
        
        # GROQ providers
        if hasattr(settings, 'groq_api_key') and settings.groq_api_key:
            providers["groq-mixtral"] = ProviderConfig(
                provider=LLMProvider.GROQ,
                model_name="llama3-8b-8192",
                api_key=settings.groq_api_key.get_secret_value() if hasattr(settings.groq_api_key, 'get_secret_value') else settings.groq_api_key,
                temperature=0.1,
                max_tokens=4000,
                cost_per_token=0.00000027,
                rate_limit_rpm=30,
                rate_limit_tpm=6000,
                priority=1,
                capabilities=["fast_analysis", "reasoning", "generation"],
                metadata={"quality": "high", "speed": "very_fast"}
            )
            
            providers["groq-llama2"] = ProviderConfig(
                provider=LLMProvider.GROQ,
                model_name="llama2-70b-4096",
                api_key=settings.groq_api_key.get_secret_value() if hasattr(settings.groq_api_key, 'get_secret_value') else settings.groq_api_key,
                temperature=0.1,
                max_tokens=4000,
                cost_per_token=0.00000070,
                rate_limit_rpm=30,
                rate_limit_tpm=6000,
                priority=2,
                capabilities=["generation", "communication", "simple_analysis"],
                metadata={"quality": "medium", "speed": "fast"}
            )
        
        # Ollama providers
        if getattr(settings, 'ollama_enabled', False):
            providers["ollama-local"] = ProviderConfig(
                provider=LLMProvider.OLLAMA,
                model_name=getattr(settings, 'ollama_model', 'llama2'),
                base_url=getattr(settings, 'ollama_base_url', 'http://localhost:11434'),
                temperature=0.1,
                max_tokens=4000,
                cost_per_token=0.0,
                rate_limit_rpm=60,
                rate_limit_tpm=10000,
                priority=3,
                capabilities=["local_processing", "privacy", "generation"],
                metadata={"quality": "medium", "speed": "medium", "cost": "free"}
            )
        
        # Default task routing
        task_routing = {
            TaskType.CONTRACT_ANALYSIS: [
                "openai-gpt4", "groq-mixtral", "openai-gpt35", "ollama-local"
            ],
            TaskType.RISK_ASSESSMENT: [
                "openai-gpt4", "groq-mixtral", "openai-gpt35", "ollama-local"
            ],
            TaskType.LEGAL_PRECEDENT: [
                "openai-gpt4", "groq-mixtral", "openai-gpt35", "ollama-local"
            ],
            TaskType.NEGOTIATION: [
                "openai-gpt35", "groq-llama2", "openai-gpt4", "ollama-local"
            ],
            TaskType.COMMUNICATION: [
                "openai-gpt35", "groq-llama2", "ollama-local", "openai-gpt4"
            ],
            TaskType.GENERAL: [
                "openai-gpt35", "groq-llama2", "ollama-local", "openai-gpt4"
            ]
        }
        
        return LLMManagerConfig(
            providers=providers,
            task_routing=task_routing,
            default_routing_criteria=RoutingCriteria.COST,
            cache_ttl=3600,
            max_retries=3,
            fallback_enabled=True,
            circuit_breaker_threshold=5,
            circuit_breaker_timeout=60
        )
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            config_data = self._config_to_dict()
            
            # Ensure config directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Saved LLM configuration to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save LLM configuration: {e}")
    
    def _config_to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for JSON serialization."""
        if not self.config:
            return {}
        
        # Convert providers
        providers_dict = {}
        for provider_id, provider_config in self.config.providers.items():
            provider_dict = asdict(provider_config)
            provider_dict["provider"] = provider_config.provider.value
            # Don't save sensitive API keys in config file
            if "api_key" in provider_dict:
                provider_dict["api_key"] = None
            providers_dict[provider_id] = provider_dict
        
        # Convert task routing
        task_routing_dict = {}
        for task_type, provider_list in self.config.task_routing.items():
            task_routing_dict[task_type.value] = provider_list
        
        return {
            "providers": providers_dict,
            "task_routing": task_routing_dict,
            "default_routing_criteria": self.config.default_routing_criteria.value,
            "cache_ttl": self.config.cache_ttl,
            "max_retries": self.config.max_retries,
            "fallback_enabled": self.config.fallback_enabled,
            "circuit_breaker_threshold": self.config.circuit_breaker_threshold,
            "circuit_breaker_timeout": self.config.circuit_breaker_timeout
        }
    
    def get_config_value(self) -> LLMManagerConfig:
        """Get current configuration."""
        if not self.config:
            self.config = self._create_default_config()
        return self.config
    
    def update_provider_config(
        self, 
        provider_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update configuration for a specific provider."""
        try:
            if not self.config or provider_id not in self.config.providers:
                logger.error(f"Provider {provider_id} not found in configuration")
                return False
            
            provider_config = self.config.providers[provider_id]
            
            # Update allowed fields
            allowed_fields = [
                "enabled", "temperature", "max_tokens", "priority", 
                "rate_limit_rpm", "rate_limit_tpm", "timeout", "capabilities"
            ]
            
            for field, value in updates.items():
                if field in allowed_fields and hasattr(provider_config, field):
                    setattr(provider_config, field, value)
                    logger.info(f"Updated {provider_id}.{field} = {value}")
            
            self._save_config()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update provider config: {e}")
            return False
    
    def add_provider(
        self, 
        provider_id: str, 
        provider_config: ProviderConfig
    ) -> bool:
        """Add a new provider configuration."""
        try:
            if not self.config:
                self.config = self._create_default_config()
            
            self.config.providers[provider_id] = provider_config
            
            # Add to default task routing
            for task_type in TaskType:
                if task_type not in self.config.task_routing:
                    self.config.task_routing[task_type] = []
                if provider_id not in self.config.task_routing[task_type]:
                    self.config.task_routing[task_type].append(provider_id)
            
            self._save_config()
            logger.info(f"Added provider {provider_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add provider: {e}")
            return False
    
    def remove_provider(self, provider_id: str) -> bool:
        """Remove a provider configuration."""
        try:
            if not self.config or provider_id not in self.config.providers:
                logger.error(f"Provider {provider_id} not found")
                return False
            
            # Remove from providers
            del self.config.providers[provider_id]
            
            # Remove from task routing
            for task_type, provider_list in self.config.task_routing.items():
                if provider_id in provider_list:
                    provider_list.remove(provider_id)
            
            self._save_config()
            logger.info(f"Removed provider {provider_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove provider: {e}")
            return False
    
    def update_task_routing(
        self, 
        task_type: TaskType, 
        provider_order: List[str]
    ) -> bool:
        """Update provider order for a specific task type."""
        try:
            if not self.config:
                self.config = self._create_default_config()
            
            # Validate that all providers exist
            for provider_id in provider_order:
                if provider_id not in self.config.providers:
                    logger.error(f"Provider {provider_id} not found in configuration")
                    return False
            
            self.config.task_routing[task_type] = provider_order
            self._save_config()
            logger.info(f"Updated task routing for {task_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update task routing: {e}")
            return False
    
    def get_provider_configs(self) -> Dict[str, ProviderConfig]:
        """Get all provider configurations with API keys from environment."""
        if not self.config:
            return {}
        
        # Inject API keys from environment
        providers = {}
        for provider_id, provider_config in self.config.providers.items():
            # Create a copy to avoid modifying the original
            config_dict = asdict(provider_config)
            
            # Inject API keys from settings
            if provider_config.provider == LLMProvider.OPENAI:
                if hasattr(settings, 'openai_api_key') and settings.openai_api_key:
                    config_dict["api_key"] = settings.openai_api_key.get_secret_value()
            elif provider_config.provider == LLMProvider.GROQ:
                if hasattr(settings, 'groq_api_key') and settings.groq_api_key:
                    api_key = settings.groq_api_key
                    if hasattr(api_key, 'get_secret_value'):
                        config_dict["api_key"] = api_key.get_secret_value()
                    else:
                        config_dict["api_key"] = str(api_key)
            
            providers[provider_id] = ProviderConfig(**config_dict)
        
        return providers
    
    def validate_config(self) -> List[str]:
        """Validate current configuration and return list of issues."""
        issues = []
        
        if not self.config:
            issues.append("No configuration loaded")
            return issues
        
        # Validate providers
        if not self.config.providers:
            issues.append("No providers configured")
        
        for provider_id, provider_config in self.config.providers.items():
            # Check required fields
            if not provider_config.model_name:
                issues.append(f"Provider {provider_id} missing model_name")
            
            if provider_config.cost_per_token < 0:
                issues.append(f"Provider {provider_id} has negative cost_per_token")
            
            if provider_config.priority < 1:
                issues.append(f"Provider {provider_id} has invalid priority")
        
        # Validate task routing
        for task_type, provider_list in self.config.task_routing.items():
            for provider_id in provider_list:
                if provider_id not in self.config.providers:
                    issues.append(f"Task routing for {task_type.value} references unknown provider {provider_id}")
        
        return issues
    
    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        self.config = self._create_default_config()
        self._save_config()
        logger.info("Reset LLM configuration to defaults")


# Global instance
_llm_config_manager = None


def get_llm_config_manager() -> LLMConfigManager:
    """Get global LLM configuration manager instance."""
    global _llm_config_manager
    if _llm_config_manager is None:
        _llm_config_manager = LLMConfigManager()
    return _llm_config_manager