"""
Feature Flags Management System for Career Copilot.

This module provides a comprehensive feature flags system that allows for:
- Gradual rollouts of new features
- A/B testing capabilities
- Environment-specific feature control
- Runtime feature toggling
- User-based feature targeting
"""

import json
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

try:
    from .logging import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)


class FeatureState(str, Enum):
    """Feature flag states."""
    DISABLED = "disabled"
    ENABLED = "enabled"
    ROLLOUT = "rollout"
    TESTING = "testing"
    DEPRECATED = "deprecated"


class RolloutStrategy(str, Enum):
    """Feature rollout strategies."""
    PERCENTAGE = "percentage"
    USER_LIST = "user_list"
    USER_ATTRIBUTE = "user_attribute"
    TIME_BASED = "time_based"
    ENVIRONMENT = "environment"


@dataclass
class RolloutConfig:
    """Configuration for feature rollout."""
    strategy: RolloutStrategy
    percentage: Optional[float] = None
    user_list: Optional[List[str]] = None
    user_attribute: Optional[str] = None
    attribute_values: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    environments: Optional[List[str]] = None


@dataclass
class FeatureFlag:
    """Feature flag definition."""
    name: str
    description: str
    state: FeatureState
    default_value: bool = False
    rollout_config: Optional[RolloutConfig] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserContext:
    """User context for feature flag evaluation."""
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    environment: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None


class FeatureFlagProvider(ABC):
    """Abstract base class for feature flag providers."""
    
    @abstractmethod
    async def get_flag(self, flag_name: str) -> Optional[FeatureFlag]:
        """Get a feature flag by name."""
        pass
    
    @abstractmethod
    async def get_all_flags(self) -> Dict[str, FeatureFlag]:
        """Get all feature flags."""
        pass
    
    @abstractmethod
    async def set_flag(self, flag: FeatureFlag) -> None:
        """Set or update a feature flag."""
        pass
    
    @abstractmethod
    async def delete_flag(self, flag_name: str) -> None:
        """Delete a feature flag."""
        pass


class FileBasedProvider(FeatureFlagProvider):
    """File-based feature flag provider."""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.flags: Dict[str, FeatureFlag] = {}
        self.last_modified = 0
        self.lock = threading.RLock()
        self._load_flags()
    
    def _load_flags(self):
        """Load feature flags from file."""
        try:
            if not self.config_path.exists():
                logger.warning(f"Feature flags file not found: {self.config_path}")
                return
            
            stat = self.config_path.stat()
            if stat.st_mtime <= self.last_modified:
                return
            
            with open(self.config_path, 'r') as f:
                data = json.load(f)
            
            with self.lock:
                self.flags = {}
                for flag_name, flag_data in data.get('flags', {}).items():
                    rollout_config = None
                    if 'rollout_config' in flag_data:
                        rc_data = flag_data['rollout_config']
                        rollout_config = RolloutConfig(
                            strategy=RolloutStrategy(rc_data['strategy']),
                            percentage=rc_data.get('percentage'),
                            user_list=rc_data.get('user_list'),
                            user_attribute=rc_data.get('user_attribute'),
                            attribute_values=rc_data.get('attribute_values'),
                            start_time=datetime.fromisoformat(rc_data['start_time']) if rc_data.get('start_time') else None,
                            end_time=datetime.fromisoformat(rc_data['end_time']) if rc_data.get('end_time') else None,
                            environments=rc_data.get('environments')
                        )
                    
                    flag = FeatureFlag(
                        name=flag_name,
                        description=flag_data.get('description', ''),
                        state=FeatureState(flag_data.get('state', 'disabled')),
                        default_value=flag_data.get('default_value', False),
                        rollout_config=rollout_config,
                        dependencies=flag_data.get('dependencies', []),
                        tags=flag_data.get('tags', []),
                        created_at=datetime.fromisoformat(flag_data['created_at']) if flag_data.get('created_at') else datetime.utcnow(),
                        updated_at=datetime.fromisoformat(flag_data['updated_at']) if flag_data.get('updated_at') else datetime.utcnow(),
                        created_by=flag_data.get('created_by'),
                        metadata=flag_data.get('metadata', {})
                    )
                    self.flags[flag_name] = flag
                
                self.last_modified = stat.st_mtime
                logger.info(f"Loaded {len(self.flags)} feature flags from {self.config_path}")
        
        except Exception as e:
            logger.error(f"Failed to load feature flags from {self.config_path}: {e}")
    
    async def get_flag(self, flag_name: str) -> Optional[FeatureFlag]:
        """Get a feature flag by name."""
        self._load_flags()  # Check for updates
        with self.lock:
            return self.flags.get(flag_name)
    
    async def get_all_flags(self) -> Dict[str, FeatureFlag]:
        """Get all feature flags."""
        self._load_flags()  # Check for updates
        with self.lock:
            return self.flags.copy()
    
    async def set_flag(self, flag: FeatureFlag) -> None:
        """Set or update a feature flag."""
        with self.lock:
            self.flags[flag.name] = flag
            flag.updated_at = datetime.utcnow()
            await self._save_flags()
    
    async def delete_flag(self, flag_name: str) -> None:
        """Delete a feature flag."""
        with self.lock:
            if flag_name in self.flags:
                del self.flags[flag_name]
                await self._save_flags()
    
    async def _save_flags(self):
        """Save feature flags to file."""
        try:
            data = {'flags': {}}
            for flag_name, flag in self.flags.items():
                flag_data = {
                    'description': flag.description,
                    'state': flag.state.value,
                    'default_value': flag.default_value,
                    'dependencies': flag.dependencies,
                    'tags': flag.tags,
                    'created_at': flag.created_at.isoformat(),
                    'updated_at': flag.updated_at.isoformat(),
                    'created_by': flag.created_by,
                    'metadata': flag.metadata
                }
                
                if flag.rollout_config:
                    rc = flag.rollout_config
                    flag_data['rollout_config'] = {
                        'strategy': rc.strategy.value,
                        'percentage': rc.percentage,
                        'user_list': rc.user_list,
                        'user_attribute': rc.user_attribute,
                        'attribute_values': rc.attribute_values,
                        'start_time': rc.start_time.isoformat() if rc.start_time else None,
                        'end_time': rc.end_time.isoformat() if rc.end_time else None,
                        'environments': rc.environments
                    }
                
                data['flags'][flag_name] = flag_data
            
            # Create backup
            if self.config_path.exists():
                backup_path = self.config_path.with_suffix('.bak')
                self.config_path.rename(backup_path)
            
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {len(self.flags)} feature flags to {self.config_path}")
        
        except Exception as e:
            logger.error(f"Failed to save feature flags to {self.config_path}: {e}")
            raise


class FeatureFlagManager:
    """Main feature flag manager."""
    
    def __init__(self, provider: FeatureFlagProvider, environment: str = "development"):
        self.provider = provider
        self.environment = environment
        self.cache: Dict[str, bool] = {}
        self.cache_ttl = 300  # 5 minutes
        self.cache_timestamps: Dict[str, float] = {}
        self.lock = threading.RLock()
    
    async def is_enabled(self, flag_name: str, user_context: Optional[UserContext] = None, default: bool = False) -> bool:
        """Check if a feature flag is enabled for the given context."""
        try:
            # Check cache first
            cache_key = self._get_cache_key(flag_name, user_context)
            if self._is_cache_valid(cache_key):
                with self.lock:
                    return self.cache.get(cache_key, default)
            
            # Get flag from provider
            flag = await self.provider.get_flag(flag_name)
            if not flag:
                logger.warning(f"Feature flag '{flag_name}' not found, using default: {default}")
                return default
            
            # Evaluate flag
            result = await self._evaluate_flag(flag, user_context)
            
            # Cache result
            with self.lock:
                self.cache[cache_key] = result
                self.cache_timestamps[cache_key] = time.time()
            
            return result
        
        except Exception as e:
            logger.error(f"Error evaluating feature flag '{flag_name}': {e}")
            return default
    
    async def _evaluate_flag(self, flag: FeatureFlag, user_context: Optional[UserContext] = None) -> bool:
        """Evaluate a feature flag based on its configuration."""
        # Check dependencies first
        if flag.dependencies:
            for dep_flag in flag.dependencies:
                if not await self.is_enabled(dep_flag, user_context):
                    logger.debug(f"Feature flag '{flag.name}' disabled due to dependency '{dep_flag}'")
                    return False
        
        # Check flag state
        if flag.state == FeatureState.DISABLED:
            return False
        elif flag.state == FeatureState.ENABLED:
            return True
        elif flag.state == FeatureState.DEPRECATED:
            logger.warning(f"Feature flag '{flag.name}' is deprecated")
            return flag.default_value
        elif flag.state in [FeatureState.ROLLOUT, FeatureState.TESTING]:
            return await self._evaluate_rollout(flag, user_context)
        
        return flag.default_value
    
    async def _evaluate_rollout(self, flag: FeatureFlag, user_context: Optional[UserContext] = None) -> bool:
        """Evaluate rollout configuration."""
        if not flag.rollout_config:
            return flag.default_value
        
        rollout = flag.rollout_config
        
        # Time-based rollout
        if rollout.strategy == RolloutStrategy.TIME_BASED:
            now = datetime.utcnow()
            if rollout.start_time and now < rollout.start_time:
                return False
            if rollout.end_time and now > rollout.end_time:
                return False
            return True
        
        # Environment-based rollout
        if rollout.strategy == RolloutStrategy.ENVIRONMENT:
            if rollout.environments and self.environment in rollout.environments:
                return True
            return False
        
        # User context required for other strategies
        if not user_context:
            return flag.default_value
        
        # User list rollout
        if rollout.strategy == RolloutStrategy.USER_LIST:
            if rollout.user_list and user_context.user_id in rollout.user_list:
                return True
            return False
        
        # User attribute rollout
        if rollout.strategy == RolloutStrategy.USER_ATTRIBUTE:
            if (rollout.user_attribute and 
                rollout.attribute_values and 
                user_context.attributes.get(rollout.user_attribute) in rollout.attribute_values):
                return True
            return False
        
        # Percentage rollout
        if rollout.strategy == RolloutStrategy.PERCENTAGE:
            if rollout.percentage is not None:
                # Use consistent hash for user to ensure stable rollout
                user_hash = hash(f"{flag.name}:{user_context.user_id or user_context.session_id or 'anonymous'}")
                percentage = (user_hash % 100) / 100.0
                return percentage < (rollout.percentage / 100.0)
            return False
        
        return flag.default_value
    
    def _get_cache_key(self, flag_name: str, user_context: Optional[UserContext] = None) -> str:
        """Generate cache key for flag evaluation."""
        if not user_context:
            return f"{flag_name}:anonymous"
        
        context_parts = [
            user_context.user_id or "anonymous",
            user_context.role or "default",
            user_context.environment or self.environment
        ]
        return f"{flag_name}:{':'.join(context_parts)}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid."""
        with self.lock:
            if cache_key not in self.cache_timestamps:
                return False
            return time.time() - self.cache_timestamps[cache_key] < self.cache_ttl
    
    async def get_flag_info(self, flag_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a feature flag."""
        flag = await self.provider.get_flag(flag_name)
        if not flag:
            return None
        
        return {
            'name': flag.name,
            'description': flag.description,
            'state': flag.state.value,
            'default_value': flag.default_value,
            'dependencies': flag.dependencies,
            'tags': flag.tags,
            'created_at': flag.created_at.isoformat(),
            'updated_at': flag.updated_at.isoformat(),
            'created_by': flag.created_by,
            'metadata': flag.metadata,
            'rollout_config': flag.rollout_config.__dict__ if flag.rollout_config else None
        }
    
    async def list_flags(self, tags: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """List all feature flags, optionally filtered by tags."""
        all_flags = await self.provider.get_all_flags()
        result = {}
        
        for flag_name, flag in all_flags.items():
            if tags and not any(tag in flag.tags for tag in tags):
                continue
            
            result[flag_name] = {
                'description': flag.description,
                'state': flag.state.value,
                'default_value': flag.default_value,
                'tags': flag.tags,
                'updated_at': flag.updated_at.isoformat()
            }
        
        return result
    
    async def create_flag(self, name: str, description: str, state: FeatureState = FeatureState.DISABLED, 
                         default_value: bool = False, tags: Optional[List[str]] = None,
                         created_by: Optional[str] = None) -> FeatureFlag:
        """Create a new feature flag."""
        flag = FeatureFlag(
            name=name,
            description=description,
            state=state,
            default_value=default_value,
            tags=tags or [],
            created_by=created_by
        )
        
        await self.provider.set_flag(flag)
        logger.info(f"Created feature flag '{name}' with state '{state.value}'")
        return flag
    
    async def update_flag_state(self, flag_name: str, state: FeatureState) -> bool:
        """Update the state of a feature flag."""
        flag = await self.provider.get_flag(flag_name)
        if not flag:
            return False
        
        flag.state = state
        flag.updated_at = datetime.utcnow()
        await self.provider.set_flag(flag)
        
        # Clear cache for this flag
        with self.lock:
            keys_to_remove = [key for key in self.cache.keys() if key.startswith(f"{flag_name}:")]
            for key in keys_to_remove:
                del self.cache[key]
                del self.cache_timestamps[key]
        
        logger.info(f"Updated feature flag '{flag_name}' state to '{state.value}'")
        return True
    
    async def set_rollout_percentage(self, flag_name: str, percentage: float) -> bool:
        """Set percentage rollout for a feature flag."""
        flag = await self.provider.get_flag(flag_name)
        if not flag:
            return False
        
        if not flag.rollout_config:
            flag.rollout_config = RolloutConfig(strategy=RolloutStrategy.PERCENTAGE)
        
        flag.rollout_config.strategy = RolloutStrategy.PERCENTAGE
        flag.rollout_config.percentage = percentage
        flag.state = FeatureState.ROLLOUT
        flag.updated_at = datetime.utcnow()
        
        await self.provider.set_flag(flag)
        
        # Clear cache
        with self.lock:
            keys_to_remove = [key for key in self.cache.keys() if key.startswith(f"{flag_name}:")]
            for key in keys_to_remove:
                del self.cache[key]
                del self.cache_timestamps[key]
        
        logger.info(f"Set rollout percentage for '{flag_name}' to {percentage}%")
        return True
    
    def clear_cache(self):
        """Clear the feature flag cache."""
        with self.lock:
            self.cache.clear()
            self.cache_timestamps.clear()
        logger.info("Feature flag cache cleared")


# Global feature flag manager instance
_feature_flag_manager: Optional[FeatureFlagManager] = None
_manager_lock = threading.Lock()


def get_feature_flag_manager(environment: str = "development") -> FeatureFlagManager:
    """Get the global feature flag manager instance."""
    global _feature_flag_manager
    
    with _manager_lock:
        if _feature_flag_manager is None:
            # Find config directory
            current_path = Path(__file__).resolve()
            project_root = None
            
            # Start from current working directory and work up
            search_paths = [Path.cwd()]
            
            # Add parent directories of the current file
            for parent in current_path.parents:
                search_paths.append(parent)
            
            # Look for config directory
            for path in search_paths:
                if (path / "config").exists():
                    project_root = path
                    break
            
            if project_root is None:
                project_root = Path.cwd()
            
            config_path = project_root / "config" / "feature_flags.json"
            provider = FileBasedProvider(config_path)
            _feature_flag_manager = FeatureFlagManager(provider, environment)
            
            logger.info(f"Created feature flag manager for {environment} environment")
        
        return _feature_flag_manager


async def is_feature_enabled(flag_name: str, user_context: Optional[UserContext] = None, 
                           default: bool = False) -> bool:
    """Check if a feature flag is enabled."""
    manager = get_feature_flag_manager()
    return await manager.is_enabled(flag_name, user_context, default)


async def get_user_context(user_id: Optional[str] = None, email: Optional[str] = None,
                          role: Optional[str] = None, **attributes) -> UserContext:
    """Create a user context for feature flag evaluation."""
    return UserContext(
        user_id=user_id,
        email=email,
        role=role,
        attributes=attributes
    )