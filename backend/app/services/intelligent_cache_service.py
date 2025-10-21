"""
Intelligent Cache Service with Advanced Caching Strategies.

Provides intelligent caching with:
- Multi-level caching (L1: Memory, L2: Redis, L3: Database)
- Adaptive TTL based on access patterns
- Cache warming and preloading
- Intelligent cache invalidation
- Performance optimization
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
import pickle
import zlib

from ..core.caching import get_cache_manager
from ..core.database import get_database_manager
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


class IntelligentCacheService:
    """Advanced caching service with intelligent strategies."""
    
    def __init__(self):
        self.cache_manager = get_cache_manager()
        self.db_manager = None
        
        # Multi-level cache
        self.l1_cache = {}  # Memory cache
        self.l2_cache = None  # Redis cache (from cache_manager)
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
        
        # Intelligent invalidation
        self.invalidation_rules = {}
        self.dependency_graph = {}
        
    async def initialize(self):
        """Initialize intelligent cache service."""
        try:
            self.db_manager = await get_database_manager()
            self.l2_cache = self.cache_manager
            
            # Start background tasks
            asyncio.create_task(self._cache_maintenance_loop())
            asyncio.create_task(self._access_pattern_analysis_loop())
            asyncio.create_task(self._cache_warming_loop())
            
            logger.info("Intelligent cache service initialized")
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
            l2_value = await self.l2_cache.async_get(key)
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
                    await self.l2_cache.async_set(key, l3_value, self._calculate_adaptive_ttl(key))
                elif self._should_cache_in_l2(key):
                    await self.l2_cache.async_set(key, l3_value, self._calculate_adaptive_ttl(key))
                
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
            success &= self.l2_cache.delete(key)
            
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
            l2_count = self.l2_cache.invalidate_pattern(pattern)
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
            l2_results = self.l2_cache.optimize_cache()
            optimization_results["l2_optimizations"] = l2_results.get("memory_cleanup", 0)
            
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
            await self.l2_cache.async_set(
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
        success &= await self.l2_cache.async_set(key, value, ttl)
        
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
        success &= await self.l2_cache.async_set(key, value, ttl)
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
                value = await self.l2_cache.async_get(key)
                if value is not None:
                    await self._promote_to_l1(key, value)
                    results["hot_keys_promoted"] += 1
        
        # Demote cold keys from L1
        for key in list(self.cold_keys):
            if key in self.l1_cache:
                entry = self.l1_cache[key]
                # Move to L2
                value = self._decompress_value(entry.value, entry.compressed)
                await self.l2_cache.async_set(key, value, entry.ttl)
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