"""
Agent Result Caching and Timeout Management

This module provides specialized caching for agent execution results with TTL-based invalidation
and configurable timeout handling per agent type.
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid

from .caching import get_cache_manager
from .config import get_settings
from .logging import get_logger
from ..models.agent_models import AgentState

logger = get_logger(__name__)
settings = get_settings()
cache_manager = get_cache_manager()


class AgentType(str, Enum):
    """Agent type enumeration for configuration."""
    CONTRACT_ANALYZER = "contract_analyzer"
    RISK_ASSESSOR = "risk_assessor"
    LEGAL_PRECEDENT = "legal_precedent"
    NEGOTIATION = "negotiation"
    COMMUNICATION = "communication"


@dataclass
class AgentCacheConfig:
    """Configuration for agent caching and timeout behavior."""
    
    agent_type: AgentType
    cache_ttl_seconds: int = 3600  # 1 hour default
    timeout_seconds: int = 300  # 5 minutes default
    enable_caching: bool = True
    cache_key_prefix: str = ""
    max_cache_size: int = 1000
    
    # Cache invalidation settings
    invalidate_on_error: bool = True
    invalidate_on_timeout: bool = True
    
    # Performance settings
    enable_compression: bool = False
    enable_semantic_matching: bool = False
    
    def __post_init__(self):
        if not self.cache_key_prefix:
            self.cache_key_prefix = f"agent_result:{self.agent_type.value}"


@dataclass
class AgentCacheEntry:
    """Represents a cached agent execution result."""
    
    cache_key: str
    agent_type: AgentType
    input_hash: str
    result: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    last_accessed: datetime
    access_count: int = 1
    execution_time: float = 0.0
    cache_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def update_access(self):
        """Update access statistics."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1
    
    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if cache entry is expired."""
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > ttl_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "cache_key": self.cache_key,
            "agent_type": self.agent_type.value,
            "input_hash": self.input_hash,
            "result": self.result,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "execution_time": self.execution_time,
            "cache_id": self.cache_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentCacheEntry':
        """Create from dictionary."""
        entry = cls(
            cache_key=data["cache_key"],
            agent_type=AgentType(data["agent_type"]),
            input_hash=data["input_hash"],
            result=data["result"],
            metadata=data["metadata"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            access_count=data["access_count"],
            execution_time=data["execution_time"],
            cache_id=data["cache_id"]
        )
        return entry


@dataclass
class TimeoutConfig:
    """Timeout configuration for agent execution."""
    
    agent_type: AgentType
    default_timeout: int = 300  # 5 minutes
    max_timeout: int = 1800  # 30 minutes
    min_timeout: int = 30  # 30 seconds
    
    # Adaptive timeout settings
    enable_adaptive_timeout: bool = True
    timeout_multiplier_on_retry: float = 1.5
    max_retries_for_timeout: int = 3
    
    # Performance-based timeout adjustment
    adjust_based_on_history: bool = True
    history_window_size: int = 10
    timeout_percentile: float = 0.95  # Use 95th percentile of execution times
    
    def get_timeout_for_execution(
        self, 
        retry_count: int = 0, 
        execution_history: List[float] = None
    ) -> int:
        """Calculate timeout for current execution."""
        base_timeout = self.default_timeout
        
        # Adjust based on execution history
        if self.adjust_based_on_history and execution_history:
            if len(execution_history) >= 3:
                # Use percentile of historical execution times
                sorted_times = sorted(execution_history[-self.history_window_size:])
                percentile_index = int(len(sorted_times) * self.timeout_percentile)
                historical_timeout = int(sorted_times[percentile_index] * 2)  # 2x buffer
                base_timeout = max(base_timeout, historical_timeout)
        
        # Apply retry multiplier
        if self.enable_adaptive_timeout and retry_count > 0:
            base_timeout = int(base_timeout * (self.timeout_multiplier_on_retry ** retry_count))
        
        # Ensure within bounds
        return max(self.min_timeout, min(base_timeout, self.max_timeout))


class AgentCacheManager:
    """Comprehensive cache manager for agent execution results with timeout handling."""
    
    def __init__(self):
        """Initialize agent cache manager."""
        self.cache_configs = self._initialize_default_configs()
        self.timeout_configs = self._initialize_timeout_configs()
        self.cache_entries: Dict[str, AgentCacheEntry] = {}
        self.execution_history: Dict[AgentType, List[float]] = {}
        
        # Statistics
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "timeouts": 0,
            "evictions": 0,
            "total_requests": 0
        }
        
        # Cleanup settings
        self.cleanup_interval = 3600  # 1 hour
        self.last_cleanup = time.time()
        
        logger.info("Agent cache manager initialized")
    
    def _initialize_default_configs(self) -> Dict[AgentType, AgentCacheConfig]:
        """Initialize default cache configurations for each agent type."""
        return {
            AgentType.CONTRACT_ANALYZER: AgentCacheConfig(
                agent_type=AgentType.CONTRACT_ANALYZER,
                cache_ttl_seconds=7200,  # 2 hours - analysis results are stable
                timeout_seconds=600,  # 10 minutes - complex analysis
                enable_caching=True,
                max_cache_size=500
            ),
            AgentType.RISK_ASSESSOR: AgentCacheConfig(
                agent_type=AgentType.RISK_ASSESSOR,
                cache_ttl_seconds=3600,  # 1 hour - risk assessment can change
                timeout_seconds=300,  # 5 minutes - faster analysis
                enable_caching=True,
                max_cache_size=1000
            ),
            AgentType.LEGAL_PRECEDENT: AgentCacheConfig(
                agent_type=AgentType.LEGAL_PRECEDENT,
                cache_ttl_seconds=86400,  # 24 hours - precedents are stable
                timeout_seconds=900,  # 15 minutes - research takes time
                enable_caching=True,
                max_cache_size=200,
                enable_semantic_matching=True
            ),
            AgentType.NEGOTIATION: AgentCacheConfig(
                agent_type=AgentType.NEGOTIATION,
                cache_ttl_seconds=1800,  # 30 minutes - negotiation context changes
                timeout_seconds=450,  # 7.5 minutes - moderate complexity
                enable_caching=True,
                max_cache_size=300
            ),
            AgentType.COMMUNICATION: AgentCacheConfig(
                agent_type=AgentType.COMMUNICATION,
                cache_ttl_seconds=900,  # 15 minutes - communication is contextual
                timeout_seconds=180,  # 3 minutes - quick generation
                enable_caching=True,
                max_cache_size=500
            )
        }
    
    def _initialize_timeout_configs(self) -> Dict[AgentType, TimeoutConfig]:
        """Initialize timeout configurations for each agent type."""
        return {
            AgentType.CONTRACT_ANALYZER: TimeoutConfig(
                agent_type=AgentType.CONTRACT_ANALYZER,
                default_timeout=600,  # 10 minutes
                max_timeout=1800,  # 30 minutes
                enable_adaptive_timeout=True,
                timeout_multiplier_on_retry=1.5
            ),
            AgentType.RISK_ASSESSOR: TimeoutConfig(
                agent_type=AgentType.RISK_ASSESSOR,
                default_timeout=300,  # 5 minutes
                max_timeout=900,  # 15 minutes
                enable_adaptive_timeout=True,
                timeout_multiplier_on_retry=1.3
            ),
            AgentType.LEGAL_PRECEDENT: TimeoutConfig(
                agent_type=AgentType.LEGAL_PRECEDENT,
                default_timeout=900,  # 15 minutes
                max_timeout=2700,  # 45 minutes
                enable_adaptive_timeout=True,
                timeout_multiplier_on_retry=1.8
            ),
            AgentType.NEGOTIATION: TimeoutConfig(
                agent_type=AgentType.NEGOTIATION,
                default_timeout=450,  # 7.5 minutes
                max_timeout=1350,  # 22.5 minutes
                enable_adaptive_timeout=True,
                timeout_multiplier_on_retry=1.4
            ),
            AgentType.COMMUNICATION: TimeoutConfig(
                agent_type=AgentType.COMMUNICATION,
                default_timeout=180,  # 3 minutes
                max_timeout=540,  # 9 minutes
                enable_adaptive_timeout=True,
                timeout_multiplier_on_retry=1.2
            )
        }
    
    def _generate_input_hash(self, task_input: Dict[str, Any]) -> str:
        """Generate a hash for the task input."""
        # Create a normalized representation of the input
        # Remove volatile fields that shouldn't affect caching
        cache_input = {k: v for k, v in task_input.items() 
                      if k not in ['workflow_id', 'execution_id', 'timestamp']}
        
        # Sort keys for consistent hashing
        input_str = json.dumps(cache_input, sort_keys=True, default=str)
        return hashlib.sha256(input_str.encode()).hexdigest()
    
    def _generate_cache_key(self, agent_type: AgentType, input_hash: str) -> str:
        """Generate cache key for agent result."""
        config = self.cache_configs[agent_type]
        return f"{config.cache_key_prefix}:{input_hash}"
    
    async def get_cached_result(
        self, 
        agent_type: AgentType, 
        task_input: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get cached result for agent execution."""
        self.cache_stats["total_requests"] += 1
        
        config = self.cache_configs.get(agent_type)
        if not config or not config.enable_caching:
            self.cache_stats["misses"] += 1
            return None
        
        try:
            # Generate cache key
            input_hash = self._generate_input_hash(task_input)
            cache_key = self._generate_cache_key(agent_type, input_hash)
            
            # Check memory cache first
            if cache_key in self.cache_entries:
                entry = self.cache_entries[cache_key]
                
                # Check if expired
                if entry.is_expired(config.cache_ttl_seconds):
                    del self.cache_entries[cache_key]
                    await self._remove_from_persistent_cache(cache_key)
                    self.cache_stats["misses"] += 1
                    return None
                
                # Update access and return result
                entry.update_access()
                self.cache_stats["hits"] += 1
                
                logger.debug(f"Cache hit for {agent_type.value}: {cache_key[:8]}")
                
                # Add cache metadata to result
                result = entry.result.copy()
                result["_cache_metadata"] = {
                    "cached": True,
                    "cache_id": entry.cache_id,
                    "created_at": entry.created_at.isoformat(),
                    "access_count": entry.access_count,
                    "execution_time": entry.execution_time
                }
                
                return result
            
            # Check persistent cache
            cached_data = await cache_manager.async_get(cache_key)
            if cached_data:
                try:
                    entry = AgentCacheEntry.from_dict(cached_data)
                    
                    # Check if expired
                    if entry.is_expired(config.cache_ttl_seconds):
                        await cache_manager.delete(cache_key)
                        self.cache_stats["misses"] += 1
                        return None
                    
                    # Add to memory cache
                    entry.update_access()
                    self.cache_entries[cache_key] = entry
                    self.cache_stats["hits"] += 1
                    
                    logger.debug(f"Persistent cache hit for {agent_type.value}: {cache_key[:8]}")
                    
                    # Add cache metadata to result
                    result = entry.result.copy()
                    result["_cache_metadata"] = {
                        "cached": True,
                        "cache_id": entry.cache_id,
                        "created_at": entry.created_at.isoformat(),
                        "access_count": entry.access_count,
                        "execution_time": entry.execution_time
                    }
                    
                    return result
                    
                except Exception as e:
                    logger.warning(f"Failed to deserialize cached entry: {e}")
                    await cache_manager.delete(cache_key)
            
            # No cache hit
            self.cache_stats["misses"] += 1
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached result for {agent_type.value}: {e}")
            self.cache_stats["misses"] += 1
            return None
    
    async def cache_result(
        self,
        agent_type: AgentType,
        task_input: Dict[str, Any],
        result: Dict[str, Any],
        execution_time: float,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Cache agent execution result."""
        config = self.cache_configs.get(agent_type)
        if not config or not config.enable_caching:
            return False
        
        try:
            # Don't cache error results
            if not result.get("success", True) or "error" in result:
                return False
            
            # Generate cache key
            input_hash = self._generate_input_hash(task_input)
            cache_key = self._generate_cache_key(agent_type, input_hash)
            
            # Create cache entry
            cache_entry = AgentCacheEntry(
                cache_key=cache_key,
                agent_type=agent_type,
                input_hash=input_hash,
                result=result,
                metadata=metadata or {},
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow(),
                execution_time=execution_time
            )
            
            # Add to memory cache
            self.cache_entries[cache_key] = cache_entry
            
            # Store in persistent cache
            await cache_manager.async_set(
                cache_key, 
                cache_entry.to_dict(), 
                config.cache_ttl_seconds
            )
            
            # Update execution history for timeout calculation
            if agent_type not in self.execution_history:
                self.execution_history[agent_type] = []
            
            self.execution_history[agent_type].append(execution_time)
            
            # Keep only recent history
            timeout_config = self.timeout_configs[agent_type]
            max_history = timeout_config.history_window_size * 2
            if len(self.execution_history[agent_type]) > max_history:
                self.execution_history[agent_type] = self.execution_history[agent_type][-max_history:]
            
            # Check if we need to evict entries
            await self._check_and_evict_entries(agent_type)
            
            logger.debug(f"Cached result for {agent_type.value}: {cache_key[:8]} (TTL: {config.cache_ttl_seconds}s)")
            
            return True
            
        except Exception as e:
            logger.error(f"Error caching result for {agent_type.value}: {e}")
            return False
    
    async def _check_and_evict_entries(self, agent_type: AgentType):
        """Check and evict entries if cache is full."""
        config = self.cache_configs[agent_type]
        
        # Count entries for this agent type
        agent_entries = [
            (key, entry) for key, entry in self.cache_entries.items()
            if entry.agent_type == agent_type
        ]
        
        if len(agent_entries) > config.max_cache_size:
            # Sort by last accessed time (LRU)
            agent_entries.sort(key=lambda x: x[1].last_accessed)
            
            # Evict oldest entries
            entries_to_evict = len(agent_entries) - config.max_cache_size
            
            for i in range(entries_to_evict):
                key, entry = agent_entries[i]
                del self.cache_entries[key]
                await self._remove_from_persistent_cache(key)
                self.cache_stats["evictions"] += 1
            
            logger.info(f"Evicted {entries_to_evict} cache entries for {agent_type.value}")
    
    async def _remove_from_persistent_cache(self, cache_key: str):
        """Remove entry from persistent cache."""
        try:
            cache_manager.delete(cache_key)
        except Exception as e:
            logger.warning(f"Failed to remove from persistent cache: {e}")
    
    def get_timeout_for_agent(
        self, 
        agent_type: AgentType, 
        retry_count: int = 0
    ) -> int:
        """Get timeout for agent execution."""
        timeout_config = self.timeout_configs.get(agent_type)
        if not timeout_config:
            return 300  # Default 5 minutes
        
        execution_history = self.execution_history.get(agent_type, [])
        return timeout_config.get_timeout_for_execution(retry_count, execution_history)
    
    async def execute_with_timeout(
        self,
        agent_type: AgentType,
        coro,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Execute agent coroutine with timeout handling."""
        timeout_seconds = self.get_timeout_for_agent(agent_type, retry_count)
        
        try:
            result = await asyncio.wait_for(coro, timeout=timeout_seconds)
            return result
            
        except asyncio.TimeoutError:
            self.cache_stats["timeouts"] += 1
            
            logger.warning(f"Agent {agent_type.value} timed out after {timeout_seconds}s (retry: {retry_count})")
            
            # Return timeout error result
            return {
                "success": False,
                "error": "Agent execution timed out",
                "error_type": "timeout",
                "timeout_seconds": timeout_seconds,
                "retry_count": retry_count,
                "agent_type": agent_type.value
            }
    
    async def invalidate_cache(
        self, 
        agent_type: Optional[AgentType] = None, 
        pattern: Optional[str] = None
    ) -> int:
        """Invalidate cache entries."""
        invalidated_count = 0
        
        try:
            if agent_type:
                # Invalidate all entries for specific agent type
                keys_to_remove = [
                    key for key, entry in self.cache_entries.items()
                    if entry.agent_type == agent_type
                ]
                
                for key in keys_to_remove:
                    del self.cache_entries[key]
                    await self._remove_from_persistent_cache(key)
                    invalidated_count += 1
                
                # Clear execution history
                if agent_type in self.execution_history:
                    self.execution_history[agent_type].clear()
                
            elif pattern:
                # Pattern-based invalidation
                import fnmatch
                
                keys_to_remove = [
                    key for key in self.cache_entries.keys()
                    if fnmatch.fnmatch(key, pattern)
                ]
                
                for key in keys_to_remove:
                    del self.cache_entries[key]
                    await self._remove_from_persistent_cache(key)
                    invalidated_count += 1
                
                # Also invalidate from persistent cache
                cache_manager.invalidate_pattern(pattern)
                
            else:
                # Clear all caches
                invalidated_count = len(self.cache_entries)
                self.cache_entries.clear()
                self.execution_history.clear()
                
                # Clear persistent cache
                cache_manager.invalidate_pattern("agent_result:*")
            
            logger.info(f"Invalidated {invalidated_count} agent cache entries")
            return invalidated_count
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return 0
    
    async def cleanup_expired_entries(self) -> int:
        """Clean up expired cache entries."""
        if time.time() - self.last_cleanup < self.cleanup_interval:
            return 0
        
        self.last_cleanup = time.time()
        cleaned_count = 0
        
        try:
            expired_keys = []
            
            for key, entry in self.cache_entries.items():
                config = self.cache_configs[entry.agent_type]
                if entry.is_expired(config.cache_ttl_seconds):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache_entries[key]
                await self._remove_from_persistent_cache(key)
                cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} expired cache entries")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
            return 0
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        # Calculate statistics by agent type
        agent_stats = {}
        for agent_type in AgentType:
            agent_entries = [
                entry for entry in self.cache_entries.values()
                if entry.agent_type == agent_type
            ]
            
            agent_stats[agent_type.value] = {
                "cached_entries": len(agent_entries),
                "total_access_count": sum(entry.access_count for entry in agent_entries),
                "avg_execution_time": (
                    sum(entry.execution_time for entry in agent_entries) / len(agent_entries)
                    if agent_entries else 0.0
                ),
                "execution_history_size": len(self.execution_history.get(agent_type, [])),
                "cache_config": self.cache_configs[agent_type].__dict__,
                "timeout_config": self.timeout_configs[agent_type].__dict__
            }
        
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "overall_stats": {
                "total_entries": len(self.cache_entries),
                "hit_rate": hit_rate,
                "total_requests": total_requests,
                "cache_hits": self.cache_stats["hits"],
                "cache_misses": self.cache_stats["misses"],
                "timeouts": self.cache_stats["timeouts"],
                "evictions": self.cache_stats["evictions"]
            },
            "agent_stats": agent_stats,
            "last_cleanup": datetime.fromtimestamp(self.last_cleanup).isoformat()
        }
    
    def update_cache_config(
        self, 
        agent_type: AgentType, 
        config_updates: Dict[str, Any]
    ) -> bool:
        """Update cache configuration for an agent type."""
        try:
            config = self.cache_configs[agent_type]
            
            for key, value in config_updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            logger.info(f"Updated cache config for {agent_type.value}: {config_updates}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating cache config: {e}")
            return False
    
    def update_timeout_config(
        self, 
        agent_type: AgentType, 
        config_updates: Dict[str, Any]
    ) -> bool:
        """Update timeout configuration for an agent type."""
        try:
            config = self.timeout_configs[agent_type]
            
            for key, value in config_updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            logger.info(f"Updated timeout config for {agent_type.value}: {config_updates}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating timeout config: {e}")
            return False


# Global instance
_agent_cache_manager = None


def get_agent_cache_manager() -> AgentCacheManager:
    """Get the global agent cache manager instance."""
    global _agent_cache_manager
    if _agent_cache_manager is None:
        _agent_cache_manager = AgentCacheManager()
    return _agent_cache_manager