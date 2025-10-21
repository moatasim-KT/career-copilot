"""
Cache Monitoring Service for tracking cache performance and optimization.
Provides detailed metrics, alerts, and optimization recommendations.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from ..core.caching import get_cache_manager
from ..core.config import get_settings
from ..core.logging import get_logger
from ..monitoring.metrics_collector import get_metrics_collector

logger = get_logger(__name__)
settings = get_settings()
cache_manager = get_cache_manager()
metrics_collector = get_metrics_collector()


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


class CacheMonitoringService:
    """Service for monitoring cache performance and providing optimization insights."""
    
    def __init__(self):
        """Initialize cache monitoring service."""
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
        
        logger.info("Cache monitoring service initialized")
    
    async def start_monitoring(self):
        """Start continuous cache monitoring."""
        logger.info("Starting cache monitoring")
        
        while True:
            try:
                await self.collect_metrics()
                await self.check_alerts()
                await self.generate_recommendations()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in cache monitoring: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def collect_metrics(self) -> CacheMetrics:
        """Collect current cache metrics."""
        try:
            # Get cache statistics
            cache_stats = cache_manager.get_stats()
            
            # Calculate derived metrics
            total_requests = cache_stats.get("total_hits", 0) + cache_stats.get("total_misses", 0)
            hit_rate = cache_stats.get("hit_rate", 0) / 100.0  # Convert percentage to decimal
            miss_rate = 1.0 - hit_rate if total_requests > 0 else 0.0
            
            # Estimate memory usage (simplified)
            memory_usage_mb = cache_stats.get("memory_cache_size", 0) * 0.001  # Rough estimate
            
            metrics = CacheMetrics(
                timestamp=datetime.utcnow(),
                hit_rate=hit_rate,
                miss_rate=miss_rate,
                total_requests=total_requests,
                redis_hits=cache_stats.get("redis_hits", 0),
                memory_hits=cache_stats.get("memory_hits", 0),
                errors=cache_stats.get("errors", 0),
                avg_response_time=cache_stats.get("avg_response_time", 0.0),
                memory_usage_mb=memory_usage_mb,
                redis_connected=cache_stats.get("redis_connected", False),
                evictions=cache_stats.get("evictions", 0),
                expirations=cache_stats.get("expirations", 0)
            )
            
            # Add to history
            self.metrics_history.append(metrics)
            
            # Trim history to max size
            if len(self.metrics_history) > self.max_metrics_history:
                self.metrics_history = self.metrics_history[-self.max_metrics_history:]
            
            # Record metrics for Prometheus
            metrics_collector.record_cache_metrics(
                hit_rate=hit_rate,
                miss_rate=miss_rate,
                response_time=metrics.avg_response_time,
                memory_usage=memory_usage_mb,
                redis_connected=metrics.redis_connected
            )
            
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
        
        # Check error rate alert
        if current_metrics.total_requests > 0:
            error_rate = current_metrics.errors / current_metrics.total_requests
            if error_rate > self.error_rate_threshold:
                await self._create_alert(
                    alert_type="high_error_rate",
                    severity="high",
                    message=f"Cache error rate is {error_rate:.2%}, above threshold of {self.error_rate_threshold:.2%}",
                    metrics={"error_rate": error_rate, "threshold": self.error_rate_threshold}
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
        
        # Send alert to monitoring system
        metrics_collector.record_cache_alert(
            alert_type=alert_type,
            severity=severity,
            message=message
        )
    
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
        
        # Redis connection analysis
        redis_connected_count = sum(1 for m in recent_metrics if m.redis_connected)
        if redis_connected_count < len(recent_metrics):
            self.recommendations.append(OptimizationRecommendation(
                recommendation_id="improve_redis_reliability",
                category="configuration",
                priority="high",
                title="Improve Redis Reliability",
                description="Redis connection has been unstable. Consider reviewing connection settings and implementing connection pooling.",
                impact="More reliable caching and reduced fallback to memory cache",
                implementation="Review Redis configuration, connection pooling, and network settings",
                estimated_improvement={"reliability": 0.2}
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
    
    def get_recommendations(self) -> List[OptimizationRecommendation]:
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
    
    async def optimize_cache(self) -> Dict[str, Any]:
        """Perform cache optimization based on current recommendations."""
        optimization_results = {
            "actions_taken": [],
            "improvements": {},
            "errors": []
        }
        
        try:
            # Perform cache manager optimization
            cache_optimization = cache_manager.optimize_cache()
            optimization_results["actions_taken"].append("cache_manager_optimization")
            optimization_results["improvements"].update(cache_optimization)
            
            # Clear expired entries
            if hasattr(cache_manager, '_cleanup_memory_cache'):
                cache_manager._cleanup_memory_cache()
                optimization_results["actions_taken"].append("memory_cleanup")
            
            # Apply recommendations
            for recommendation in self.recommendations:
                if recommendation.priority == "high":
                    # Implement high-priority recommendations automatically
                    if recommendation.category == "ttl":
                        # Adjust TTL settings (simplified)
                        optimization_results["actions_taken"].append(f"ttl_optimization_{recommendation.recommendation_id}")
                    elif recommendation.category == "memory":
                        # Trigger memory optimization
                        optimization_results["actions_taken"].append(f"memory_optimization_{recommendation.recommendation_id}")
            
            logger.info(f"Cache optimization completed: {optimization_results}")
            return optimization_results
            
        except Exception as e:
            logger.error(f"Error during cache optimization: {e}")
            optimization_results["errors"].append(str(e))
            return optimization_results


# Global instance
_cache_monitoring_service = None


def get_cache_monitoring_service() -> CacheMonitoringService:
    """Get global cache monitoring service instance."""
    global _cache_monitoring_service
    if _cache_monitoring_service is None:
        _cache_monitoring_service = CacheMonitoringService()
    return _cache_monitoring_service