"""
LLM Request/Response Caching Manager
Provides intelligent caching for LLM requests with semantic similarity detection and cache optimization.
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.caching import get_cache_manager

logger = get_logger(__name__)
settings = get_settings()
cache_manager = get_cache_manager()


class CacheEntry:
    """Represents a cached LLM response."""
    
    def __init__(self, request_hash: str, response: Dict[str, Any], metadata: Dict[str, Any] = None):
        self.request_hash = request_hash
        self.response = response
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.access_count = 1
        self.cache_id = str(uuid4())
    
    def update_access(self):
        """Update access statistics."""
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "request_hash": self.request_hash,
            "response": self.response,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "cache_id": self.cache_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create from dictionary."""
        entry = cls(
            request_hash=data["request_hash"],
            response=data["response"],
            metadata=data.get("metadata", {})
        )
        entry.created_at = datetime.fromisoformat(data["created_at"])
        entry.last_accessed = datetime.fromisoformat(data["last_accessed"])
        entry.access_count = data["access_count"]
        entry.cache_id = data["cache_id"]
        return entry


class SemanticSimilarityMatcher:
    """Matches semantically similar requests for cache hits."""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        self.request_vectors = {}
        self.request_texts = {}
        self.fitted = False
    
    def _extract_request_text(self, messages: List[Dict[str, str]]) -> str:
        """Extract text content from messages for similarity comparison."""
        text_parts = []
        for msg in messages:
            if isinstance(msg, dict) and "content" in msg:
                text_parts.append(msg["content"])
            elif isinstance(msg, str):
                text_parts.append(msg)
        
        return " ".join(text_parts)
    
    def add_request(self, request_hash: str, messages: List[Dict[str, str]]):
        """Add a request to the similarity matcher."""
        request_text = self._extract_request_text(messages)
        self.request_texts[request_hash] = request_text
        
        # Refit vectorizer if we have enough samples
        if len(self.request_texts) >= 2:
            self._refit_vectorizer()
    
    def _refit_vectorizer(self):
        """Refit the vectorizer with current request texts."""
        try:
            texts = list(self.request_texts.values())
            if len(texts) < 2:
                return
            
            # Fit vectorizer
            vectors = self.vectorizer.fit_transform(texts)
            
            # Store vectors for each request
            for i, (request_hash, text) in enumerate(self.request_texts.items()):
                self.request_vectors[request_hash] = vectors[i]
            
            self.fitted = True
            
        except Exception as e:
            logger.warning(f"Failed to refit similarity vectorizer: {e}")
            self.fitted = False
    
    def find_similar_request(self, messages: List[Dict[str, str]]) -> Optional[Tuple[str, float]]:
        """Find a similar cached request."""
        if not self.fitted or len(self.request_vectors) == 0:
            return None
        
        try:
            request_text = self._extract_request_text(messages)
            
            # Transform new request
            new_vector = self.vectorizer.transform([request_text])
            
            best_match = None
            best_similarity = 0.0
            
            # Compare with all cached requests
            for request_hash, cached_vector in self.request_vectors.items():
                similarity = cosine_similarity(new_vector, cached_vector)[0][0]
                
                if similarity > best_similarity and similarity >= self.similarity_threshold:
                    best_similarity = similarity
                    best_match = request_hash
            
            if best_match:
                logger.debug(f"Found similar request with similarity {best_similarity:.3f}")
                return best_match, best_similarity
            
            return None
            
        except Exception as e:
            logger.warning(f"Error in similarity matching: {e}")
            return None
    
    def remove_request(self, request_hash: str):
        """Remove a request from the matcher."""
        if request_hash in self.request_texts:
            del self.request_texts[request_hash]
        
        if request_hash in self.request_vectors:
            del self.request_vectors[request_hash]
        
        # Refit if we still have requests
        if len(self.request_texts) >= 2:
            self._refit_vectorizer()
        else:
            self.fitted = False


class CacheOptimizer:
    """Optimizes cache performance and manages cache lifecycle."""
    
    def __init__(self):
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "semantic_hits": 0,
            "evictions": 0,
            "total_requests": 0
        }
        self.optimization_history = []
    
    def should_cache_response(self, response: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        """Determine if a response should be cached."""
        # Don't cache error responses
        if "error" in response or response.get("success", True) is False:
            return False
        
        # Don't cache very short responses (likely not useful)
        content = response.get("content", "")
        if len(content) < 50:
            return False
        
        # Don't cache responses with very high temperature (too random)
        temperature = metadata.get("temperature", 0.1)
        if temperature > 0.8:
            return False
        
        # Don't cache streaming responses
        if metadata.get("stream", False):
            return False
        
        return True
    
    def calculate_cache_ttl(self, response: Dict[str, Any], metadata: Dict[str, Any]) -> int:
        """Calculate appropriate TTL for a cache entry."""
        base_ttl = 3600  # 1 hour
        
        # Longer TTL for analysis tasks (more stable)
        task_type = metadata.get("task_type", "")
        if "analysis" in task_type.lower():
            base_ttl *= 4  # 4 hours
        
        # Longer TTL for lower temperature (more deterministic)
        temperature = metadata.get("temperature", 0.1)
        if temperature <= 0.1:
            base_ttl *= 2
        elif temperature >= 0.5:
            base_ttl = int(base_ttl * 0.5)
        
        # Longer TTL for expensive models
        model = metadata.get("model", "")
        if "gpt-4" in model.lower():
            base_ttl *= 3
        
        # Shorter TTL for time-sensitive content
        content = response.get("content", "").lower()
        time_sensitive_keywords = ["today", "now", "current", "latest", "recent"]
        if any(keyword in content for keyword in time_sensitive_keywords):
            base_ttl = int(base_ttl * 0.3)
        
        return max(300, min(base_ttl, 24 * 3600))  # Between 5 minutes and 24 hours
    
    def should_evict_entry(self, entry: CacheEntry) -> bool:
        """Determine if a cache entry should be evicted."""
        now = datetime.now()
        
        # Evict very old entries
        if now - entry.created_at > timedelta(days=7):
            return True
        
        # Evict entries that haven't been accessed recently and have low access count
        if (now - entry.last_accessed > timedelta(hours=24) and 
            entry.access_count < 3):
            return True
        
        return False
    
    def optimize_cache(self, cache_entries: Dict[str, CacheEntry]) -> Dict[str, Any]:
        """Optimize cache by removing stale entries and updating statistics."""
        optimization_start = time.time()
        
        initial_count = len(cache_entries)
        evicted_entries = []
        
        # Find entries to evict
        for request_hash, entry in list(cache_entries.items()):
            if self.should_evict_entry(entry):
                evicted_entries.append(request_hash)
        
        # Remove evicted entries
        for request_hash in evicted_entries:
            del cache_entries[request_hash]
        
        evicted_count = len(evicted_entries)
        self.cache_stats["evictions"] += evicted_count
        
        optimization_time = time.time() - optimization_start
        
        optimization_result = {
            "initial_entries": initial_count,
            "evicted_entries": evicted_count,
            "remaining_entries": len(cache_entries),
            "optimization_time": optimization_time,
            "timestamp": datetime.now().isoformat()
        }
        
        self.optimization_history.append(optimization_result)
        
        # Keep only last 100 optimization records
        if len(self.optimization_history) > 100:
            self.optimization_history = self.optimization_history[-100:]
        
        logger.info(f"Cache optimization completed: evicted {evicted_count} entries in {optimization_time:.3f}s")
        
        return optimization_result
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        semantic_hit_rate = (self.cache_stats["semantic_hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_requests": total_requests,
            "cache_hits": self.cache_stats["hits"],
            "cache_misses": self.cache_stats["misses"],
            "semantic_hits": self.cache_stats["semantic_hits"],
            "hit_rate": hit_rate,
            "semantic_hit_rate": semantic_hit_rate,
            "evictions": self.cache_stats["evictions"],
            "recent_optimizations": len(self.optimization_history)
        }


class LLMCacheManager:
    """Comprehensive LLM request/response cache manager."""
    
    def __init__(self):
        self.cache_entries = {}
        self.similarity_matcher = SemanticSimilarityMatcher()
        self.optimizer = CacheOptimizer()
        
        # Configuration
        self.enable_semantic_matching = True
        self.max_cache_entries = 10000
        self.optimization_interval = 3600  # 1 hour
        self.last_optimization = time.time()
        
        # Metrics
        self.request_count = 0
        self.cache_size_history = []
        
        logger.info("LLM Cache Manager initialized")
    
    def _generate_request_hash(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        """Generate a hash for the request."""
        # Create a normalized representation of the request
        request_data = {
            "messages": messages,
            "model": model,
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "top_p": kwargs.get("top_p", 1.0)
        }
        
        # Sort keys for consistent hashing
        request_str = json.dumps(request_data, sort_keys=True)
        return hashlib.sha256(request_str.encode()).hexdigest()
    
    async def get_cached_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Get cached response for a request."""
        self.request_count += 1
        self.optimizer.cache_stats["total_requests"] += 1
        
        # Generate request hash
        request_hash = self._generate_request_hash(messages, model, **kwargs)
        
        # Check for exact match first
        if request_hash in self.cache_entries:
            entry = self.cache_entries[request_hash]
            entry.update_access()
            
            self.optimizer.cache_stats["hits"] += 1
            
            logger.debug(f"Cache hit for request {request_hash[:8]}")
            
            return {
                **entry.response,
                "cached": True,
                "cache_type": "exact",
                "cache_id": entry.cache_id,
                "access_count": entry.access_count
            }
        
        # Check for semantic similarity if enabled
        if self.enable_semantic_matching:
            similar_match = self.similarity_matcher.find_similar_request(messages)
            
            if similar_match:
                similar_hash, similarity_score = similar_match
                
                if similar_hash in self.cache_entries:
                    entry = self.cache_entries[similar_hash]
                    entry.update_access()
                    
                    self.optimizer.cache_stats["semantic_hits"] += 1
                    
                    logger.debug(f"Semantic cache hit for request {request_hash[:8]} "
                               f"(similarity: {similarity_score:.3f})")
                    
                    return {
                        **entry.response,
                        "cached": True,
                        "cache_type": "semantic",
                        "similarity_score": similarity_score,
                        "cache_id": entry.cache_id,
                        "access_count": entry.access_count
                    }
        
        # No cache hit
        self.optimizer.cache_stats["misses"] += 1
        return None
    
    async def cache_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
        response: Dict[str, Any],
        **kwargs
    ) -> bool:
        """Cache a response."""
        try:
            # Check if response should be cached
            metadata = {
                "model": model,
                "temperature": kwargs.get("temperature", 0.1),
                "max_tokens": kwargs.get("max_tokens", 1000),
                "task_type": kwargs.get("task_type", ""),
                "stream": kwargs.get("stream", False)
            }
            
            if not self.optimizer.should_cache_response(response, metadata):
                return False
            
            # Generate request hash
            request_hash = self._generate_request_hash(messages, model, **kwargs)
            
            # Create cache entry
            cache_entry = CacheEntry(request_hash, response, metadata)
            
            # Add to cache
            self.cache_entries[request_hash] = cache_entry
            
            # Add to similarity matcher
            if self.enable_semantic_matching:
                self.similarity_matcher.add_request(request_hash, messages)
            
            # Check if we need to evict entries
            if len(self.cache_entries) > self.max_cache_entries:
                await self._evict_entries()
            
            # Periodic optimization
            if time.time() - self.last_optimization > self.optimization_interval:
                await self._optimize_cache()
            
            # Calculate TTL and store in persistent cache
            ttl = self.optimizer.calculate_cache_ttl(response, metadata)
            cache_key = f"llm_cache:{request_hash}"
            
            await cache_manager.async_set(cache_key, cache_entry.to_dict(), ttl)
            
            logger.debug(f"Cached response for request {request_hash[:8]} (TTL: {ttl}s)")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache response: {e}")
            return False
    
    async def _evict_entries(self):
        """Evict least recently used entries."""
        if len(self.cache_entries) <= self.max_cache_entries:
            return
        
        # Sort by last accessed time
        sorted_entries = sorted(
            self.cache_entries.items(),
            key=lambda x: x[1].last_accessed
        )
        
        # Evict oldest entries
        entries_to_evict = len(self.cache_entries) - self.max_cache_entries
        
        for i in range(entries_to_evict):
            request_hash, entry = sorted_entries[i]
            
            # Remove from cache
            del self.cache_entries[request_hash]
            
            # Remove from similarity matcher
            if self.enable_semantic_matching:
                self.similarity_matcher.remove_request(request_hash)
            
            # Remove from persistent cache
            cache_key = f"llm_cache:{request_hash}"
            cache_manager.delete(cache_key)
        
        self.optimizer.cache_stats["evictions"] += entries_to_evict
        
        logger.info(f"Evicted {entries_to_evict} cache entries")
    
    async def _optimize_cache(self):
        """Perform cache optimization."""
        self.last_optimization = time.time()
        
        # Run optimizer
        optimization_result = self.optimizer.optimize_cache(self.cache_entries)
        
        # Update cache size history
        self.cache_size_history.append({
            "timestamp": datetime.now().isoformat(),
            "size": len(self.cache_entries)
        })
        
        # Keep only last 100 size records
        if len(self.cache_size_history) > 100:
            self.cache_size_history = self.cache_size_history[-100:]
        
        return optimization_result
    
    async def invalidate_cache(self, pattern: Optional[str] = None) -> int:
        """Invalidate cache entries matching a pattern."""
        if pattern is None:
            # Clear all entries
            count = len(self.cache_entries)
            self.cache_entries.clear()
            
            # Clear similarity matcher
            self.similarity_matcher.request_texts.clear()
            self.similarity_matcher.request_vectors.clear()
            self.similarity_matcher.fitted = False
            
            # Clear persistent cache
            cache_manager.invalidate_pattern("llm_cache:*")
            
            logger.info(f"Invalidated all {count} cache entries")
            return count
        
        else:
            # Pattern-based invalidation
            import fnmatch
            
            matching_hashes = [
                request_hash for request_hash in self.cache_entries.keys()
                if fnmatch.fnmatch(request_hash, pattern)
            ]
            
            for request_hash in matching_hashes:
                # Remove from cache
                del self.cache_entries[request_hash]
                
                # Remove from similarity matcher
                if self.enable_semantic_matching:
                    self.similarity_matcher.remove_request(request_hash)
                
                # Remove from persistent cache
                cache_key = f"llm_cache:{request_hash}"
                cache_manager.delete(cache_key)
            
            logger.info(f"Invalidated {len(matching_hashes)} cache entries matching pattern: {pattern}")
            return len(matching_hashes)
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        base_stats = self.optimizer.get_cache_statistics()
        
        return {
            **base_stats,
            "cache_entries": len(self.cache_entries),
            "max_cache_entries": self.max_cache_entries,
            "semantic_matching_enabled": self.enable_semantic_matching,
            "similarity_threshold": self.similarity_matcher.similarity_threshold,
            "request_count": self.request_count,
            "cache_size_history": self.cache_size_history[-10:],  # Last 10 records
            "last_optimization": datetime.fromtimestamp(self.last_optimization).isoformat()
        }
    
    def get_cache_entries_info(self) -> List[Dict[str, Any]]:
        """Get information about cached entries."""
        entries_info = []
        
        for request_hash, entry in self.cache_entries.items():
            entries_info.append({
                "request_hash": request_hash[:8],
                "cache_id": entry.cache_id,
                "created_at": entry.created_at.isoformat(),
                "last_accessed": entry.last_accessed.isoformat(),
                "access_count": entry.access_count,
                "model": entry.metadata.get("model", "unknown"),
                "response_length": len(entry.response.get("content", "")),
                "metadata": entry.metadata
            })
        
        # Sort by last accessed (most recent first)
        entries_info.sort(key=lambda x: x["last_accessed"], reverse=True)
        
        return entries_info
    
    async def preload_cache_from_persistent(self):
        """Preload cache entries from persistent storage."""
        try:
            # This would require scanning Redis keys, which is expensive
            # For now, we'll load cache entries on-demand
            logger.info("Cache preloading from persistent storage not implemented")
            
        except Exception as e:
            logger.error(f"Failed to preload cache: {e}")


# Global cache manager instance
_llm_cache_manager = None


def get_llm_cache_manager() -> LLMCacheManager:
    """Get the global LLM cache manager instance."""
    global _llm_cache_manager
    
    if _llm_cache_manager is None:
        _llm_cache_manager = LLMCacheManager()
    
    return _llm_cache_manager