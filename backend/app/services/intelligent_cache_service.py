"""
Intelligent Cache Service with Advanced Caching Strategies.

Consolidates intelligent caching, cache invalidation, and cache monitoring:
- Multi-level caching (L1: Memory, L2: Redis, L3: Database)
- Adaptive TTL based on access patterns
- Cache warming and preloading
- Intelligent cache invalidation with rules and strategies
- Performance monitoring and optimization recommendations
- Cache health monitoring and alerting
"""

import asyncio
import hashlib
import json
import time
import fnmatch
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import pickle
import zlib

from .cache_service import get_cache_service
from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class CacheLevel(Enum):
    """Cache levels."""
    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"
    L3_DATABASE = "l3_database"


class CacheStrategy(Enum):
    """Cache strategies."""
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"
    WRITE_AROUND = "write_around"
    READ_THROUGH = "read_through"
    CACHE_ASIDE = "cache_aside"


class InvalidationStrategy(Enum):
    """Cache invalidation strategies."""
    IMMEDIATE = "immediate"  # Invalidate immediately
    DELAYED = "delayed"      # Invalidate after a delay
    SCHEDULED = "scheduled"  # Invalidate at scheduled times
    CONDITIONAL = "conditional"  # Invalidate based on conditions
    CASCADE = "cascade"      # Invalidate related cache entries


class InvalidationTrigger(Enum):
    """Cache invalidation triggers."""
    DATA_UPDATE = "data_update"
    USER_ACTION = "user_action"
    TIME_BASED = "time_based"
    DEPENDENCY_CHANGE = "dependency_change"
    MANUAL = "manual"
    SYSTEM_EVENT = "system_event"


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl: int
    size_bytes: int
    compressed: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CacheStats:
    """Cache statistics."""
    total_requests: int
    hits: int
    misses: int
    hit_rate: float
    l1_hits: int
    l2_hits: int
    l3_hits: int
    evictions: int
    memory_usage: int
    compression_ratio: float
    avg_response_time: float


@dataclass
class InvalidationRule:
    """Cache invalidation rule."""
    rule_id: str
    name: str
    description: str
    strategy: InvalidationStrategy
    trigger: InvalidationTrigger
    cache_patterns: List[str]
    conditions: Dict[str, Any]
    delay_seconds: int = 0
    enabled: bool = True
    created_at: datetime = None
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


@dataclass
class InvalidationEvent:
    """Cache invalidation event."""
    event_id: str
    rule_id: str
    trigger: InvalidationTrigger
    cache_patterns: List[str]
    metadata: Dict[str, Any]
    timestamp: datetime
    processed: bool = False
    processed_at: Optional[datetime] = None
    invalidated_keys: List[str] = None
    error: Optional[str] = None


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    timestamp: datetime
    hit_rate: float
    miss_rate: float
    total_requests: int
    redis_hits: int
    memory_hits: int
    errors: int
    avg_response_time: float
    memory_usage_mb: float
    redis_connected: bool
    evictions: int
    expirations: int


@dataclass
class CacheAlert:
    """Cache performance alert."""
    alert_id: str
    alert_type: str
    severity: str  # low, medium, high, critical
    message: str
    timestamp: datetime
    metrics: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class OptimizationRecommendation:
    """Cache optimization recommendation."""
    recommendation_id: str
    category: str  # ttl, memory, patterns, configuration
    priority: str  # low, medium, high
    title: str
    description: str
    impact: str
    implementation: str
    estimated_improvement: Dict[str, float]


class IntelligentCacheService:
    """Advanced caching service with intelligent strategies, invalidation, and monitoring."""
    
    def __init__(self):
        self.cache_service = get_cache_service()
        
        # Multi-level cache
        self.l1_cache = {}  # Memory cache
        self.l2_cache = None  # Redis cache (from cache_service)
        self.l3_cache = {}  # Database cache simulation
        
        # Cache configuration
        self.l1_max_size = 1000
        self.l1_max_memory = 100 * 1024 * 1024  # 100MB
        self.compression_threshold = 1024  # Compress entries > 1KB
        self.adaptive_ttl_enabled = True
        
        # Access pattern tracking
        self.access_patterns = {}
        self.hot_keys = set()
        self.cold_keys = set()
        
        # Performance tracking
        self.stats = CacheStats(
            total_requests=0, hits=0, misses=0, hit_rate=0.0,
            l1_hits=0, l2_hits=0, l3_hits=0, evictions=0,
            memory_usage=0, compression_ratio=1.0, avg_response_time=0.0
        )
        
        # Cache warming
        self.warming_enabled = True
        self.preload_patterns = []
        
        # Invalidation functionality
        self.invalidation_rules: Dict[str, InvalidationRule] = {}
        self.pending_events: List[InvalidationEvent] = []
        self.processed_events: List[InvalidationEvent] = []
        self.dependency_graph: Dict[str, Set[str]] = {}
        
        # Event handlers
        self.event_handlers: Dict[InvalidationTrigger, List[Callable]] = {
            trigger: [] for trigger in InvalidationTrigger
        }
        
        # Monitoring functionality
        self.metrics_history: List[CacheMetrics] = []
        self.active_alerts: List[CacheAlert] = []
        self.recommendations: List[OptimizationRecommendation] = []
        
        # Alert thresholds
        self.hit_rate_threshold = 0.8  # Alert if hit rate < 80%
        self.error_rate_threshold = 0.05  # Alert if error rate > 5%
        self.response_time_threshold = 0.1  # Alert if avg response time > 100ms
        self.memory_usage_threshold = 0.9  # Alert if memory usage > 90%
        
        # Monitoring configuration
        self.monitoring_interval = 60  # seconds
        self.metrics_retention_hours = 24
        self.max_metrics_history = 1440  # 24 hours of minute-by-minute data
        
    async def initialize(self):
        """Initialize intelligent cache service."""
        try:
            self.l2_cache = self.cache_service
            
            # Initialize default invalidation rules
            self._initialize_default_invalidation_rules()
            
            # Start background tasks
            asyncio.create_task(self._cache_maintenance_loop())
            asyncio.create_task(self._access_pattern_analysis_loop())
            asyncio.create_task(self._cache_warming_loop())
            asyncio.create_task(self._monitoring_loop())
            
            logger.info("Intelligent cache service initialized with invalidation and monitoring")
        except Exception as e:
            logger.error(f"Failed to initialize intelligent cache service: {e}")
            raise
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from multi-level cache with intelligent routing."""
        start_time = time.time()
        self.stats.total_requests += 1
        
        try:
            # Update access pattern
            self._update_access_pattern(key)
            
            # L1 Cache (Memory) - fastest
            if key in self.l1_cache:
                entry = self.l1_cache[key]
                if not self._is_expired(entry):
                    entry.last_accessed = datetime.utcnow()
                    entry.access_count += 1
                    self.stats.hits += 1
                    self.stats.l1_hits += 1
                    self._record_response_time(start_time)
                    return self._decompress_value(entry.value, entry.compressed)
                else:
                    # Remove expired entry
                    del self.l1_cache[key]
            
            # L2 Cache (Redis) - medium speed
            l2_value = await self.l2_cache.aget(key)
            if l2_value is not None:
                # Promote to L1 if it's a hot key
                if self._is_hot_key(key):
                    await self._promote_to_l1(key, l2_value)
                
                self.stats.hits += 1
                self.stats.l2_hits += 1
                self._record_response_time(start_time)
                return l2_value
            
            # L3 Cache (Database/Persistent) - slowest
            l3_value = await self._get_from_l3(key)
            if l3_value is not None:
                # Promote to higher levels based on access pattern
                if self._is_hot_key(key):
                    await self._promote_to_l1(key, l3_value)
                    await self.l2_cache.aset(key, l3_value, self._calculate_adaptive_ttl(key))
                elif self._should_cache_in_l2(key):
                    await self.l2_cache.aset(key, l3_value, self._calculate_adaptive_ttl(key))
                
                self.stats.hits += 1
                self.stats.l3_hits += 1
                self._record_response_time(start_time)
                return l3_value
            
            # Cache miss
            self.stats.misses += 1
            self._record_response_time(start_time)
            return default
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self.stats.misses += 1
            self._record_response_time(start_time)
            return default
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        strategy: CacheStrategy = CacheStrategy.WRITE_THROUGH
    ) -> bool:
        """Set value in multi-level cache with intelligent strategy."""
        try:
            # Calculate adaptive TTL
            effective_ttl = ttl or self._calculate_adaptive_ttl(key)
            
            # Compress large values
            compressed_value, is_compressed = self._compress_value(value)
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=compressed_value,
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow(),
                access_count=1,
                ttl=effective_ttl,
                size_bytes=len(str(compressed_value)),
                compressed=is_compressed
            )
            
            # Apply caching strategy
            if strategy == CacheStrategy.WRITE_THROUGH:
                # Write to all levels
                success = await self._write_through(key, entry, effective_ttl)
            elif strategy == CacheStrategy.WRITE_BACK:
                # Write to L1, defer L2/L3 writes
                success = await self._write_back(key, entry, effective_ttl)
            elif strategy == CacheStrategy.WRITE_AROUND:
                # Write to L2/L3, skip L1
                success = await self._write_around(key, entry, effective_ttl)
            else:
                # Default to write-through
                success = await self._write_through(key, entry, effective_ttl)
            
            # Update access pattern
            self._update_access_pattern(key)
            
            return success
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete from all cache levels with dependency invalidation."""
        try:
            success = True
            
            # Remove from L1
            if key in self.l1_cache:
                del self.l1_cache[key]
            
            # Remove from L2
            success &= await self.l2_cache.adelete(key)
            
            # Remove from L3
            success &= await self._delete_from_l3(key)
            
            # Handle dependent keys
            await self._invalidate_dependencies(key)
            
            # Update access patterns
            if key in self.access_patterns:
                del self.access_patterns[key]
            
            self.hot_keys.discard(key)
            self.cold_keys.discard(key)
            
            return success
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern."""
        try:
            invalidated_count = 0
            
            # Invalidate L1 entries
            keys_to_delete = []
            for key in self.l1_cache.keys():
                if self._matches_pattern(key, pattern):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self.l1_cache[key]
                invalidated_count += 1
            
            # Invalidate L2 entries
            l2_count = await self.l2_cache.adelete_pattern(pattern)
            invalidated_count += l2_count
            
            # Invalidate L3 entries
            l3_count = await self._invalidate_l3_pattern(pattern)
            invalidated_count += l3_count
            
            logger.info(f"Invalidated {invalidated_count} cache entries matching pattern: {pattern}")
            return invalidated_count
            
        except Exception as e:
            logger.error(f"Pattern invalidation error: {e}")
            return 0
    
    async def warm_cache(self, keys: List[str], preload_func: Optional[Callable] = None) -> int:
        """Warm cache with specified keys."""
        try:
            warmed_count = 0
            
            for key in keys:
                # Check if already cached
                cached_value = await self.get(key)
                if cached_value is not None:
                    continue
                
                # Preload data
                if preload_func:
                    try:
                        value = await preload_func(key)
                        if value is not None:
                            await self.set(key, value)
                            warmed_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to preload key {key}: {e}")
            
            logger.info(f"Cache warming completed: {warmed_count} keys loaded")
            return warmed_count
            
        except Exception as e:
            logger.error(f"Cache warming error: {e}")
            return 0
    
    async def optimize_cache(self) -> Dict[str, Any]:
        """Optimize cache performance and memory usage."""
        try:
            optimization_results = {
                "l1_optimizations": 0,
                "l2_optimizations": 0,
                "memory_freed": 0,
                "hot_keys_promoted": 0,
                "cold_keys_demoted": 0
            }
            
            # Optimize L1 cache
            l1_results = await self._optimize_l1_cache()
            optimization_results.update(l1_results)
            
            # Optimize L2 cache
            # The new cache_service does not have optimize_cache method.
            # l2_results = self.l2_cache.optimize_cache()
            # optimization_results["l2_optimizations"] = l2_results.get("memory_cleanup", 0)
            
            # Promote/demote keys based on access patterns
            promotion_results = await self._optimize_key_placement()
            optimization_results.update(promotion_results)
            
            # Update statistics
            self._update_cache_stats()
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"Cache optimization error: {e}")
            return {}
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        # Update current stats
        self._update_cache_stats()
        
        return {
            "performance": {
                "total_requests": self.stats.total_requests,
                "hits": self.stats.hits,
                "misses": self.stats.misses,
                "hit_rate": self.stats.hit_rate,
                "avg_response_time": self.stats.avg_response_time
            },
            "level_distribution": {
                "l1_hits": self.stats.l1_hits,
                "l2_hits": self.stats.l2_hits,
                "l3_hits": self.stats.l3_hits,
                "l1_hit_rate": (self.stats.l1_hits / max(self.stats.total_requests, 1)) * 100,
                "l2_hit_rate": (self.stats.l2_hits / max(self.stats.total_requests, 1)) * 100,
                "l3_hit_rate": (self.stats.l3_hits / max(self.stats.total_requests, 1)) * 100
            },
            "memory_usage": {
                "l1_entries": len(self.l1_cache),
                "l1_memory_bytes": self.stats.memory_usage,
                "l1_max_entries": self.l1_max_size,
                "l1_max_memory": self.l1_max_memory,
                "compression_ratio": self.stats.compression_ratio
            },
            "access_patterns": {
                "hot_keys": len(self.hot_keys),
                "cold_keys": len(self.cold_keys),
                "tracked_patterns": len(self.access_patterns)
            },
            "configuration": {
                "adaptive_ttl_enabled": self.adaptive_ttl_enabled,
                "warming_enabled": self.warming_enabled,
                "compression_threshold": self.compression_threshold
            }
        }
    
    def add_invalidation_rule(self, pattern: str, dependencies: List[str]):
        """Add cache invalidation rule."""
        self.invalidation_rules[pattern] = dependencies
        
        # Update dependency graph
        for dep in dependencies:
            if dep not in self.dependency_graph:
                self.dependency_graph[dep] = set()
            self.dependency_graph[dep].add(pattern)
    
    def add_preload_pattern(self, pattern: str, preload_func: Callable):
        """Add cache preload pattern."""
        self.preload_patterns.append({
            "pattern": pattern,
            "preload_func": preload_func
        })
    
    # Invalidation methods
    def _initialize_default_invalidation_rules(self):
        """Initialize default invalidation rules."""
        # User data update rule
        self.add_invalidation_rule(InvalidationRule(
            rule_id="user_data_update",
            name="User Data Update",
            description="Invalidate user-related caches when user data is updated",
            strategy=InvalidationStrategy.IMMEDIATE,
            trigger=InvalidationTrigger.DATA_UPDATE,
            cache_patterns=["session:*", "user_settings:*", "user_sessions:*"],
            conditions={"entity_type": "user"}
        ))
        
        # Job data update rule
        self.add_invalidation_rule(InvalidationRule(
            rule_id="job_data_update",
            name="Job Data Update",
            description="Invalidate job-related caches when job data is updated",
            strategy=InvalidationStrategy.CASCADE,
            trigger=InvalidationTrigger.DATA_UPDATE,
            cache_patterns=["recommendations:*", "job_search:*", "analytics:*"],
            conditions={"entity_type": "job"}
        ))
        
        # AI model change rule
        self.add_invalidation_rule(InvalidationRule(
            rule_id="ai_model_change",
            name="AI Model Change",
            description="Invalidate AI response caches when model configuration changes",
            strategy=InvalidationStrategy.IMMEDIATE,
            trigger=InvalidationTrigger.SYSTEM_EVENT,
            cache_patterns=["llm_response:*"],
            conditions={"event_type": "ai_model_change"}
        ))
        
        # Scheduled cleanup rule
        self.add_invalidation_rule(InvalidationRule(
            rule_id="scheduled_cleanup",
            name="Scheduled Cleanup",
            description="Periodic cleanup of expired cache entries",
            strategy=InvalidationStrategy.SCHEDULED,
            trigger=InvalidationTrigger.TIME_BASED,
            cache_patterns=["*"],
            conditions={"schedule": "0 2 * * *"},  # Daily at 2 AM
            delay_seconds=0
        ))
    
    def add_invalidation_rule(self, rule: InvalidationRule) -> bool:
        """Add a cache invalidation rule."""
        try:
            if rule.created_at is None:
                rule.created_at = datetime.utcnow()
            
            self.invalidation_rules[rule.rule_id] = rule
            logger.info(f"Added invalidation rule: {rule.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding invalidation rule: {e}")
            return False
    
    def remove_invalidation_rule(self, rule_id: str) -> bool:
        """Remove a cache invalidation rule."""
        if rule_id in self.invalidation_rules:
            del self.invalidation_rules[rule_id]
            logger.info(f"Removed invalidation rule: {rule_id}")
            return True
        return False
    
    async def trigger_invalidation(
        self,
        trigger: InvalidationTrigger,
        metadata: Dict[str, Any],
        force: bool = False
    ) -> List[str]:
        """Trigger cache invalidation based on an event."""
        event_ids = []
        
        # Find matching rules
        matching_rules = self._find_matching_invalidation_rules(trigger, metadata, force)
        
        for rule in matching_rules:
            # Create invalidation event
            event = InvalidationEvent(
                event_id=f"{rule.rule_id}_{int(time.time())}_{len(self.pending_events)}",
                rule_id=rule.rule_id,
                trigger=trigger,
                cache_patterns=rule.cache_patterns.copy(),
                metadata=metadata.copy(),
                timestamp=datetime.utcnow()
            )
            
            # Process based on strategy
            if rule.strategy == InvalidationStrategy.IMMEDIATE:
                await self._process_immediate_invalidation(event, rule)
            elif rule.strategy == InvalidationStrategy.DELAYED:
                await self._schedule_delayed_invalidation(event, rule)
            elif rule.strategy == InvalidationStrategy.CASCADE:
                await self._process_cascade_invalidation(event, rule)
            else:
                # Add to pending events for later processing
                self.pending_events.append(event)
            
            event_ids.append(event.event_id)
            
            # Update rule statistics
            rule.last_triggered = datetime.utcnow()
            rule.trigger_count += 1
        
        return event_ids
    
    def _find_matching_invalidation_rules(
        self,
        trigger: InvalidationTrigger,
        metadata: Dict[str, Any],
        force: bool = False
    ) -> List[InvalidationRule]:
        """Find invalidation rules that match the trigger and conditions."""
        matching_rules = []
        
        for rule in self.invalidation_rules.values():
            if not rule.enabled and not force:
                continue
            
            if rule.trigger != trigger:
                continue
            
            # Check conditions
            if not force and not self._check_invalidation_conditions(rule.conditions, metadata):
                continue
            
            matching_rules.append(rule)
        
        return matching_rules
    
    def _check_invalidation_conditions(self, conditions: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        """Check if metadata matches rule conditions."""
        for key, expected_value in conditions.items():
            if key not in metadata:
                return False
            
            actual_value = metadata[key]
            
            # Handle different condition types
            if isinstance(expected_value, list):
                if actual_value not in expected_value:
                    return False
            elif isinstance(expected_value, dict):
                # Handle complex conditions (e.g., ranges, patterns)
                if "pattern" in expected_value:
                    if not fnmatch.fnmatch(str(actual_value), expected_value["pattern"]):
                        return False
                elif "range" in expected_value:
                    range_val = expected_value["range"]
                    if not (range_val.get("min", float('-inf')) <= actual_value <= range_val.get("max", float('inf'))):
                        return False
            else:
                if actual_value != expected_value:
                    return False
        
        return True
    
    async def _process_immediate_invalidation(self, event: InvalidationEvent, rule: InvalidationRule):
        """Process immediate cache invalidation."""
        try:
            invalidated_keys = []
            
            for pattern in event.cache_patterns:
                if "*" in pattern:
                    # Pattern-based invalidation
                    count = await self.invalidate_pattern(pattern)
                    invalidated_keys.append(f"{pattern} ({count} keys)")
                else:
                    # Direct key invalidation
                    success = await self.delete(pattern)
                    if success:
                        invalidated_keys.append(pattern)
            
            event.processed = True
            event.processed_at = datetime.utcnow()
            event.invalidated_keys = invalidated_keys
            
            self.processed_events.append(event)
            logger.info(f"Immediate invalidation completed for rule {rule.rule_id}: {len(invalidated_keys)} patterns")
            
        except Exception as e:
            event.error = str(e)
            logger.error(f"Error in immediate invalidation: {e}")
    
    async def _schedule_delayed_invalidation(self, event: InvalidationEvent, rule: InvalidationRule):
        """Schedule delayed cache invalidation."""
        async def delayed_invalidation():
            await asyncio.sleep(rule.delay_seconds)
            await self._process_immediate_invalidation(event, rule)
        
        # Schedule the invalidation
        asyncio.create_task(delayed_invalidation())
        logger.info(f"Scheduled delayed invalidation for rule {rule.rule_id} in {rule.delay_seconds} seconds")
    
    async def _process_cascade_invalidation(self, event: InvalidationEvent, rule: InvalidationRule):
        """Process cascade cache invalidation with dependency resolution."""
        try:
            invalidated_keys = []
            
            # First, invalidate direct patterns
            for pattern in event.cache_patterns:
                if "*" in pattern:
                    count = await self.invalidate_pattern(pattern)
                    invalidated_keys.append(f"{pattern} ({count} keys)")
                else:
                    success = await self.delete(pattern)
                    if success:
                        invalidated_keys.append(pattern)
            
            # Then, invalidate dependent caches
            dependent_patterns = self._get_dependent_patterns(event.cache_patterns)
            for pattern in dependent_patterns:
                if "*" in pattern:
                    count = await self.invalidate_pattern(pattern)
                    invalidated_keys.append(f"dependent:{pattern} ({count} keys)")
                else:
                    success = await self.delete(pattern)
                    if success:
                        invalidated_keys.append(f"dependent:{pattern}")
            
            event.processed = True
            event.processed_at = datetime.utcnow()
            event.invalidated_keys = invalidated_keys
            
            self.processed_events.append(event)
            logger.info(f"Cascade invalidation completed for rule {rule.rule_id}: {len(invalidated_keys)} patterns")
            
        except Exception as e:
            event.error = str(e)
            logger.error(f"Error in cascade invalidation: {e}")
    
    def _get_dependent_patterns(self, patterns: List[str]) -> List[str]:
        """Get cache patterns that depend on the given patterns."""
        dependent_patterns = set()
        
        for pattern in patterns:
            if pattern in self.dependency_graph:
                dependent_patterns.update(self.dependency_graph[pattern])
        
        return list(dependent_patterns)
    
    def add_cache_dependency(self, source_pattern: str, dependent_pattern: str):
        """Add a cache dependency relationship."""
        if source_pattern not in self.dependency_graph:
            self.dependency_graph[source_pattern] = set()
        
        self.dependency_graph[source_pattern].add(dependent_pattern)
        logger.debug(f"Added cache dependency: {source_pattern} -> {dependent_pattern}")
    
    async def invalidate_user_caches(self, user_id: str) -> int:
        """Invalidate all caches related to a specific user."""
        patterns = [
            f"session:*{user_id}*",
            f"user_settings:{user_id}",
            f"user_sessions:{user_id}",
            f"recommendations:{user_id}:*",
            f"analytics:{user_id}:*"
        ]
        
        total_invalidated = 0
        for pattern in patterns:
            count = await self.invalidate_pattern(pattern)
            total_invalidated += count
        
        logger.info(f"Invalidated {total_invalidated} cache entries for user {user_id}")
        return total_invalidated
    
    # Monitoring methods
    async def collect_metrics(self) -> CacheMetrics:
        """Collect current cache metrics."""
        try:
            # Get cache statistics from cache service
            cache_stats = self.cache_service.get_cache_stats()
            
            # Calculate derived metrics
            total_requests = self.stats.total_requests
            hit_rate = self.stats.hit_rate / 100.0 if self.stats.hit_rate > 1 else self.stats.hit_rate
            miss_rate = 1.0 - hit_rate if total_requests > 0 else 0.0
            
            # Estimate memory usage
            memory_usage_mb = self.stats.memory_usage / (1024 * 1024)  # Convert to MB
            
            metrics = CacheMetrics(
                timestamp=datetime.utcnow(),
                hit_rate=hit_rate,
                miss_rate=miss_rate,
                total_requests=total_requests,
                redis_hits=self.stats.l2_hits,
                memory_hits=self.stats.l1_hits,
                errors=0,  # Would need to track errors separately
                avg_response_time=self.stats.avg_response_time,
                memory_usage_mb=memory_usage_mb,
                redis_connected=cache_stats.get("enabled", False),
                evictions=self.stats.evictions,
                expirations=0  # Would need to track expirations separately
            )
            
            # Add to history
            self.metrics_history.append(metrics)
            
            # Trim history to max size
            if len(self.metrics_history) > self.max_metrics_history:
                self.metrics_history = self.metrics_history[-self.max_metrics_history:]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting cache metrics: {e}")
            raise
    
    async def check_alerts(self):
        """Check for cache performance alerts."""
        if not self.metrics_history:
            return
        
        current_metrics = self.metrics_history[-1]
        
        # Check hit rate alert
        if current_metrics.hit_rate < self.hit_rate_threshold:
            await self._create_alert(
                alert_type="low_hit_rate",
                severity="medium",
                message=f"Cache hit rate is {current_metrics.hit_rate:.2%}, below threshold of {self.hit_rate_threshold:.2%}",
                metrics={"hit_rate": current_metrics.hit_rate, "threshold": self.hit_rate_threshold}
            )
        
        # Check response time alert
        if current_metrics.avg_response_time > self.response_time_threshold:
            await self._create_alert(
                alert_type="slow_response_time",
                severity="medium",
                message=f"Average cache response time is {current_metrics.avg_response_time:.3f}s, above threshold of {self.response_time_threshold:.3f}s",
                metrics={"response_time": current_metrics.avg_response_time, "threshold": self.response_time_threshold}
            )
        
        # Check Redis connection
        if not current_metrics.redis_connected:
            await self._create_alert(
                alert_type="redis_disconnected",
                severity="high",
                message="Redis connection is down, falling back to memory cache",
                metrics={"redis_connected": False}
            )
    
    async def _create_alert(self, alert_type: str, severity: str, message: str, metrics: Dict[str, Any]):
        """Create a new alert if not already active."""
        # Check if similar alert is already active
        for alert in self.active_alerts:
            if alert.alert_type == alert_type and not alert.resolved:
                return  # Alert already exists
        
        alert = CacheAlert(
            alert_id=f"{alert_type}_{int(time.time())}",
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.utcnow(),
            metrics=metrics
        )
        
        self.active_alerts.append(alert)
        logger.warning(f"Cache alert created: {message}")
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert."""
        for alert in self.active_alerts:
            if alert.alert_id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
                logger.info(f"Cache alert resolved: {alert_id}")
                return True
        return False
    
    async def generate_recommendations(self):
        """Generate cache optimization recommendations."""
        if len(self.metrics_history) < 10:  # Need some history
            return
        
        # Clear old recommendations
        self.recommendations.clear()
        
        # Analyze recent metrics
        recent_metrics = self.metrics_history[-10:]  # Last 10 data points
        
        # Hit rate analysis
        avg_hit_rate = sum(m.hit_rate for m in recent_metrics) / len(recent_metrics)
        if avg_hit_rate < 0.7:
            self.recommendations.append(OptimizationRecommendation(
                recommendation_id="improve_hit_rate",
                category="patterns",
                priority="high",
                title="Improve Cache Hit Rate",
                description=f"Current hit rate is {avg_hit_rate:.2%}. Consider increasing TTL for frequently accessed data or reviewing cache key patterns.",
                impact="Improved performance and reduced backend load",
                implementation="Review cache TTL settings and access patterns",
                estimated_improvement={"hit_rate": 0.15, "response_time": -0.02}
            ))
        
        # Memory usage analysis
        avg_memory_usage = sum(m.memory_usage_mb for m in recent_metrics) / len(recent_metrics)
        if avg_memory_usage > 100:  # Arbitrary threshold
            self.recommendations.append(OptimizationRecommendation(
                recommendation_id="optimize_memory",
                category="memory",
                priority="medium",
                title="Optimize Memory Usage",
                description=f"Memory cache is using {avg_memory_usage:.1f}MB. Consider implementing more aggressive eviction policies.",
                impact="Reduced memory footprint and better resource utilization",
                implementation="Adjust cache size limits and eviction policies",
                estimated_improvement={"memory_usage": -0.3}
            ))
        
        # Response time analysis
        avg_response_time = sum(m.avg_response_time for m in recent_metrics) / len(recent_metrics)
        if avg_response_time > 0.05:  # 50ms threshold
            self.recommendations.append(OptimizationRecommendation(
                recommendation_id="improve_response_time",
                category="configuration",
                priority="medium",
                title="Improve Response Time",
                description=f"Average response time is {avg_response_time:.3f}s. Consider optimizing serialization or Redis configuration.",
                impact="Faster cache operations and improved user experience",
                implementation="Review serialization methods and Redis connection settings",
                estimated_improvement={"response_time": -0.02}
            ))
    
    def get_current_metrics(self) -> Optional[CacheMetrics]:
        """Get the most recent cache metrics."""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_history(self, hours: int = 1) -> List[CacheMetrics]:
        """Get cache metrics history for the specified number of hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]
    
    def get_active_alerts(self) -> List[CacheAlert]:
        """Get all active (unresolved) alerts."""
        return [alert for alert in self.active_alerts if not alert.resolved]
    
    def get_optimization_recommendations(self) -> List[OptimizationRecommendation]:
        """Get current optimization recommendations."""
        return self.recommendations.copy()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get cache performance summary."""
        if not self.metrics_history:
            return {"status": "no_data"}
        
        current = self.metrics_history[-1]
        recent_metrics = self.metrics_history[-60:] if len(self.metrics_history) >= 60 else self.metrics_history
        
        # Calculate trends
        if len(recent_metrics) > 1:
            hit_rate_trend = recent_metrics[-1].hit_rate - recent_metrics[0].hit_rate
            response_time_trend = recent_metrics[-1].avg_response_time - recent_metrics[0].avg_response_time
        else:
            hit_rate_trend = 0.0
            response_time_trend = 0.0
        
        return {
            "status": "healthy" if current.hit_rate > 0.8 and current.avg_response_time < 0.1 else "degraded",
            "current_hit_rate": current.hit_rate,
            "current_response_time": current.avg_response_time,
            "redis_connected": current.redis_connected,
            "memory_usage_mb": current.memory_usage_mb,
            "total_requests": current.total_requests,
            "active_alerts": len(self.get_active_alerts()),
            "recommendations": len(self.recommendations),
            "trends": {
                "hit_rate": hit_rate_trend,
                "response_time": response_time_trend
            },
            "last_updated": current.timestamp.isoformat()
        }
    
    def get_invalidation_stats(self) -> Dict[str, Any]:
        """Get cache invalidation statistics."""
        total_rules = len(self.invalidation_rules)
        enabled_rules = sum(1 for rule in self.invalidation_rules.values() if rule.enabled)
        pending_events = len(self.pending_events)
        processed_events = len(self.processed_events)
        
        # Calculate trigger statistics
        trigger_stats = {}
        for rule in self.invalidation_rules.values():
            trigger_type = rule.trigger.value
            if trigger_type not in trigger_stats:
                trigger_stats[trigger_type] = {"count": 0, "total_triggers": 0}
            trigger_stats[trigger_type]["count"] += 1
            trigger_stats[trigger_type]["total_triggers"] += rule.trigger_count
        
        return {
            "total_rules": total_rules,
            "enabled_rules": enabled_rules,
            "pending_events": pending_events,
            "processed_events": processed_events,
            "trigger_statistics": trigger_stats,
            "dependency_relationships": len(self.dependency_graph)
        }
    
    # Private methods
    def _update_access_pattern(self, key: str):
        """Update access pattern for key."""
        current_time = time.time()
        
        if key not in self.access_patterns:
            self.access_patterns[key] = {
                "count": 0,
                "last_access": current_time,
                "first_access": current_time,
                "frequency": 0.0
            }
        
        pattern = self.access_patterns[key]
        pattern["count"] += 1
        pattern["last_access"] = current_time
        
        # Calculate access frequency (accesses per hour)
        time_span = current_time - pattern["first_access"]
        if time_span > 0:
            pattern["frequency"] = pattern["count"] / (time_span / 3600)
        
        # Classify as hot or cold
        if pattern["frequency"] > 10:  # More than 10 accesses per hour
            self.hot_keys.add(key)
            self.cold_keys.discard(key)
        elif pattern["frequency"] < 1:  # Less than 1 access per hour
            self.cold_keys.add(key)
            self.hot_keys.discard(key)
    
    def _is_hot_key(self, key: str) -> bool:
        """Check if key is frequently accessed."""
        return key in self.hot_keys
    
    def _should_cache_in_l2(self, key: str) -> bool:
        """Determine if key should be cached in L2."""
        if key in self.access_patterns:
            pattern = self.access_patterns[key]
            return pattern["frequency"] > 0.5  # More than 0.5 accesses per hour
        return True  # Default to caching
    
    def _calculate_adaptive_ttl(self, key: str) -> int:
        """Calculate adaptive TTL based on access patterns."""
        if not self.adaptive_ttl_enabled:
            return 3600  # Default 1 hour
        
        if key in self.access_patterns:
            pattern = self.access_patterns[key]
            frequency = pattern["frequency"]
            
            # Higher frequency = longer TTL
            if frequency > 10:
                return 7200  # 2 hours for hot keys
            elif frequency > 1:
                return 3600  # 1 hour for warm keys
            else:
                return 1800  # 30 minutes for cold keys
        
        return 3600  # Default
    
    def _compress_value(self, value: Any) -> Tuple[Any, bool]:
        """Compress value if it exceeds threshold."""
        try:
            serialized = pickle.dumps(value)
            if len(serialized) > self.compression_threshold:
                compressed = zlib.compress(serialized)
                if len(compressed) < len(serialized):
                    return compressed, True
            return value, False
        except Exception:
            return value, False
    
    def _decompress_value(self, value: Any, is_compressed: bool) -> Any:
        """Decompress value if needed."""
        try:
            if is_compressed:
                decompressed = zlib.decompress(value)
                return pickle.loads(decompressed)
            return value
        except Exception:
            return value
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired."""
        age = (datetime.utcnow() - entry.created_at).total_seconds()
        return age > entry.ttl
    
    async def _promote_to_l1(self, key: str, value: Any):
        """Promote key to L1 cache."""
        try:
            # Check L1 capacity
            if len(self.l1_cache) >= self.l1_max_size:
                await self._evict_l1_entry()
            
            # Create L1 entry
            compressed_value, is_compressed = self._compress_value(value)
            entry = CacheEntry(
                key=key,
                value=compressed_value,
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow(),
                access_count=1,
                ttl=self._calculate_adaptive_ttl(key),
                size_bytes=len(str(compressed_value)),
                compressed=is_compressed
            )
            
            self.l1_cache[key] = entry
            
        except Exception as e:
            logger.error(f"Failed to promote key {key} to L1: {e}")
    
    async def _evict_l1_entry(self):
        """Evict least recently used entry from L1."""
        if not self.l1_cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self.l1_cache.keys(),
            key=lambda k: self.l1_cache[k].last_accessed
        )
        
        # Move to L2 if it's still valuable
        entry = self.l1_cache[lru_key]
        if entry.access_count > 1:
            await self.l2_cache.aset(
                lru_key, 
                self._decompress_value(entry.value, entry.compressed),
                entry.ttl
            )
        
        del self.l1_cache[lru_key]
        self.stats.evictions += 1
    
    async def _write_through(self, key: str, entry: CacheEntry, ttl: int) -> bool:
        """Write-through caching strategy."""
        success = True
        
        # Write to L1
        if len(self.l1_cache) >= self.l1_max_size:
            await self._evict_l1_entry()
        self.l1_cache[key] = entry
        
        # Write to L2
        value = self._decompress_value(entry.value, entry.compressed)
        success &= await self.l2_cache.aset(key, value, ttl)
        
        # Write to L3
        success &= await self._set_in_l3(key, value, ttl)
        
        return success
    
    async def _write_back(self, key: str, entry: CacheEntry, ttl: int) -> bool:
        """Write-back caching strategy."""
        # Write to L1 immediately
        if len(self.l1_cache) >= self.l1_max_size:
            await self._evict_l1_entry()
        self.l1_cache[key] = entry
        
        # Mark for later write to L2/L3
        entry.metadata = entry.metadata or {}
        entry.metadata["dirty"] = True
        
        return True
    
    async def _write_around(self, key: str, entry: CacheEntry, ttl: int) -> bool:
        """Write-around caching strategy."""
        success = True
        
        # Skip L1, write to L2 and L3
        value = self._decompress_value(entry.value, entry.compressed)
        success &= await self.l2_cache.aset(key, value, ttl)
        success &= await self._set_in_l3(key, value, ttl)
        
        return success
    
    async def _get_from_l3(self, key: str) -> Any:
        """Get value from L3 cache (database simulation)."""
        # This is a simulation - in real implementation, this would query database
        return self.l3_cache.get(key)
    
    async def _set_in_l3(self, key: str, value: Any, ttl: int) -> bool:
        """Set value in L3 cache (database simulation)."""
        try:
            self.l3_cache[key] = {
                "value": value,
                "expires_at": time.time() + ttl
            }
            return True
        except Exception:
            return False
    
    async def _delete_from_l3(self, key: str) -> bool:
        """Delete from L3 cache."""
        try:
            if key in self.l3_cache:
                del self.l3_cache[key]
            return True
        except Exception:
            return False
    
    async def _invalidate_l3_pattern(self, pattern: str) -> int:
        """Invalidate L3 entries matching pattern."""
        count = 0
        keys_to_delete = []
        
        for key in self.l3_cache.keys():
            if self._matches_pattern(key, pattern):
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self.l3_cache[key]
            count += 1
        
        return count
    
    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if key matches pattern."""
        import fnmatch
        return fnmatch.fnmatch(key, pattern)
    
    async def _invalidate_dependencies(self, key: str):
        """Invalidate dependent cache entries."""
        if key in self.dependency_graph:
            for dependent_pattern in self.dependency_graph[key]:
                await self.invalidate_pattern(dependent_pattern)
    
    async def _optimize_l1_cache(self) -> Dict[str, Any]:
        """Optimize L1 cache."""
        results = {"l1_optimizations": 0, "memory_freed": 0}
        
        # Remove expired entries
        current_time = datetime.utcnow()
        expired_keys = []
        
        for key, entry in self.l1_cache.items():
            if self._is_expired(entry):
                expired_keys.append(key)
        
        memory_freed = 0
        for key in expired_keys:
            entry = self.l1_cache[key]
            memory_freed += entry.size_bytes
            del self.l1_cache[key]
            results["l1_optimizations"] += 1
        
        results["memory_freed"] = memory_freed
        return results
    
    async def _optimize_key_placement(self) -> Dict[str, Any]:
        """Optimize key placement across cache levels."""
        results = {"hot_keys_promoted": 0, "cold_keys_demoted": 0}
        
        # Promote hot keys to L1
        for key in list(self.hot_keys):
            if key not in self.l1_cache:
                # Try to get from L2 and promote
                value = await self.l2_cache.aget(key)
                if value is not None:
                    await self._promote_to_l1(key, value)
                    results["hot_keys_promoted"] += 1
        
        # Demote cold keys from L1
        for key in list(self.cold_keys):
            if key in self.l1_cache:
                entry = self.l1_cache[key]
                # Move to L2
                value = self._decompress_value(entry.value, entry.compressed)
                await self.l2_cache.aset(key, value, entry.ttl)
                del self.l1_cache[key]
                results["cold_keys_demoted"] += 1
        
        return results
    
    def _update_cache_stats(self):
        """Update cache statistics."""
        if self.stats.total_requests > 0:
            self.stats.hit_rate = (self.stats.hits / self.stats.total_requests) * 100
        
        # Calculate memory usage
        memory_usage = sum(entry.size_bytes for entry in self.l1_cache.values())
        self.stats.memory_usage = memory_usage
        
        # Calculate compression ratio
        if self.l1_cache:
            compressed_entries = [e for e in self.l1_cache.values() if e.compressed]
            if compressed_entries:
                # This is a simplified calculation
                self.stats.compression_ratio = 0.7  # Assume 30% compression
    
    def _record_response_time(self, start_time: float):
        """Record response time for statistics."""
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Update running average
        if self.stats.total_requests > 1:
            self.stats.avg_response_time = (
                (self.stats.avg_response_time * (self.stats.total_requests - 1) + response_time) /
                self.stats.total_requests
            )
        else:
            self.stats.avg_response_time = response_time
    
    async def _cache_maintenance_loop(self):
        """Background cache maintenance."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self.optimize_cache()
            except Exception as e:
                logger.error(f"Cache maintenance error: {e}")
    
    async def _access_pattern_analysis_loop(self):
        """Background access pattern analysis."""
        while True:
            try:
                await asyncio.sleep(600)  # Run every 10 minutes
                await self._analyze_access_patterns()
            except Exception as e:
                logger.error(f"Access pattern analysis error: {e}")
    
    async def _cache_warming_loop(self):
        """Background cache warming."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                if self.warming_enabled:
                    await self._perform_cache_warming()
            except Exception as e:
                logger.error(f"Cache warming error: {e}")
    
    async def _monitoring_loop(self):
        """Background cache monitoring."""
        while True:
            try:
                await asyncio.sleep(self.monitoring_interval)
                await self.collect_metrics()
                await self.check_alerts()
                await self.generate_recommendations()
            except Exception as e:
                logger.error(f"Cache monitoring error: {e}")
    
    async def _analyze_access_patterns(self):
        """Analyze access patterns and update classifications."""
        current_time = time.time()
        
        # Update hot/cold classifications
        for key, pattern in self.access_patterns.items():
            time_since_last_access = current_time - pattern["last_access"]
            
            # If not accessed in last hour, consider for cold classification
            if time_since_last_access > 3600:
                self.hot_keys.discard(key)
                if pattern["frequency"] < 1:
                    self.cold_keys.add(key)
    
    async def _perform_cache_warming(self):
        """Perform cache warming based on patterns."""
        for pattern_config in self.preload_patterns:
            try:
                pattern = pattern_config["pattern"]
                preload_func = pattern_config["preload_func"]
                
                # Generate keys to warm (this is simplified)
                keys_to_warm = []  # Would be generated based on pattern
                
                if keys_to_warm:
                    await self.warm_cache(keys_to_warm, preload_func)
                    
            except Exception as e:
                logger.error(f"Cache warming failed for pattern {pattern}: {e}")


# Global intelligent cache service instance
_intelligent_cache_service = None


async def get_intelligent_cache_service() -> IntelligentCacheService:
    """Get the global intelligent cache service instance."""
    global _intelligent_cache_service
    if _intelligent_cache_service is None:
        _intelligent_cache_service = IntelligentCacheService()
        await _intelligent_cache_service.initialize()
    return _intelligent_cache_service


# Convenience functions for backward compatibility
def get_cache_invalidation_service() -> IntelligentCacheService:
    """Get cache invalidation service (now part of intelligent cache service)."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in an async context, we can't await here
            # Return a placeholder or raise an error
            logger.warning("get_cache_invalidation_service called from async context - use get_intelligent_cache_service instead")
            return None
        else:
            return loop.run_until_complete(get_intelligent_cache_service())
    except RuntimeError:
        # No event loop running
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(get_intelligent_cache_service())
        finally:
            loop.close()


def get_cache_monitoring_service() -> IntelligentCacheService:
    """Get cache monitoring service (now part of intelligent cache service)."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in an async context, we can't await here
            logger.warning("get_cache_monitoring_service called from async context - use get_intelligent_cache_service instead")
            return None
        else:
            return loop.run_until_complete(get_intelligent_cache_service())
    except RuntimeError:
        # No event loop running
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(get_intelligent_cache_service())
        finally:
            loop.close()
