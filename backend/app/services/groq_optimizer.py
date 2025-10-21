"""
GROQ Optimization Service
Provides GROQ-specific optimizations, intelligent routing, and performance tuning.
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from .groq_service import GROQService, GROQModel, GROQTaskType
from ..core.logging import get_logger
from ..core.caching import get_cache_manager

logger = get_logger(__name__)
cache_manager = get_cache_manager()


class OptimizationStrategy(str, Enum):
    """GROQ optimization strategies."""
    SPEED_FIRST = "speed_first"
    QUALITY_FIRST = "quality_first"
    COST_EFFICIENT = "cost_efficient"
    BALANCED = "balanced"
    ADAPTIVE = "adaptive"


@dataclass
class GROQOptimizationConfig:
    """Configuration for GROQ optimizations."""
    strategy: OptimizationStrategy = OptimizationStrategy.BALANCED
    enable_caching: bool = True
    cache_ttl: int = 3600
    enable_batching: bool = True
    batch_size: int = 5
    batch_timeout: float = 2.0
    enable_adaptive_routing: bool = True
    performance_window: int = 100
    quality_threshold: float = 0.8
    speed_threshold: float = 2.0
    cost_threshold: float = 0.001
    enable_request_optimization: bool = True
    enable_response_caching: bool = True
    enable_model_switching: bool = True
    fallback_models: List[str] = field(default_factory=lambda: ["llama3-8b-8192", "llama3-70b-8192"])


@dataclass
class OptimizationMetrics:
    """Metrics for optimization performance."""
    cache_hits: int = 0
    cache_misses: int = 0
    batched_requests: int = 0
    model_switches: int = 0
    optimization_savings: float = 0.0
    performance_improvements: Dict[str, float] = field(default_factory=dict)
    cost_savings: float = 0.0
    quality_improvements: Dict[str, float] = field(default_factory=dict)


class GROQRequestOptimizer:
    """Optimizes GROQ requests for better performance."""
    
    def __init__(self, config: GROQOptimizationConfig):
        self.config = config
        self.metrics = OptimizationMetrics()
    
    def optimize_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Optimize message structure for GROQ."""
        optimized_messages = []
        
        for message in messages:
            optimized_msg = message.copy()
            content = message.get("content", "")
            
            # Remove excessive whitespace
            content = " ".join(content.split())
            
            # Optimize for GROQ's context window
            if len(content) > 8000:  # Conservative limit
                content = self._truncate_intelligently(content, 8000)
            
            # Add GROQ-specific formatting hints
            if message.get("role") == "system":
                content = self._optimize_system_prompt(content)
            elif message.get("role") == "user":
                content = self._optimize_user_prompt(content)
            
            optimized_msg["content"] = content
            optimized_messages.append(optimized_msg)
        
        return optimized_messages
    
    def _truncate_intelligently(self, content: str, max_length: int) -> str:
        """Intelligently truncate content while preserving meaning."""
        if len(content) <= max_length:
            return content
        
        # Try to truncate at sentence boundaries
        sentences = content.split('. ')
        truncated = ""
        
        for sentence in sentences:
            if len(truncated + sentence + '. ') <= max_length - 50:  # Leave buffer
                truncated += sentence + '. '
            else:
                break
        
        if not truncated:
            # Fallback to character truncation
            truncated = content[:max_length - 50] + "..."
        
        return truncated.strip()
    
    def _optimize_system_prompt(self, content: str) -> str:
        """Optimize system prompts for GROQ."""
        # Add GROQ-specific instructions
        optimizations = [
            "Be concise and direct in your response.",
            "Focus on the key points and avoid unnecessary elaboration.",
            "Structure your response clearly with appropriate formatting."
        ]
        
        # Check if optimizations are already present
        if not any(opt.lower() in content.lower() for opt in optimizations):
            content += "\n\nAdditional instructions: " + " ".join(optimizations)
        
        return content
    
    def _optimize_user_prompt(self, content: str) -> str:
        """Optimize user prompts for GROQ."""
        # Add context markers for better understanding
        if "analyze" in content.lower() and "contract" in content.lower():
            content = f"[CONTRACT ANALYSIS TASK] {content}"
        elif "risk" in content.lower():
            content = f"[RISK ASSESSMENT TASK] {content}"
        elif "legal" in content.lower() and "precedent" in content.lower():
            content = f"[LEGAL RESEARCH TASK] {content}"
        
        return content
    
    def optimize_parameters(
        self, 
        model: GROQModel, 
        task_type: GROQTaskType,
        base_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize parameters for specific model and task."""
        optimized_params = base_params.copy()
        
        # Model-specific optimizations
        if model == GROQModel.LLAMA3_8B:
            # Mixtral works well with slightly higher temperature for creativity
            if task_type in [GROQTaskType.CODE_GENERATION, GROQTaskType.REASONING]:
                optimized_params["temperature"] = min(optimized_params.get("temperature", 0.1) + 0.05, 0.3)
        
        elif model == GROQModel.LLAMA3_70B:
            # Llama3-70B benefits from lower temperature for accuracy
            if task_type in [GROQTaskType.FAST_ANALYSIS, GROQTaskType.CLASSIFICATION]:
                optimized_params["temperature"] = max(optimized_params.get("temperature", 0.1) - 0.02, 0.0)
        
        elif model == GROQModel.LLAMA3_8B:
            # Llama3-8B is fast, optimize for throughput
            optimized_params["max_tokens"] = min(optimized_params.get("max_tokens", 4000), 2000)
        
        # Task-specific optimizations
        if task_type == GROQTaskType.SUMMARIZATION:
            optimized_params["temperature"] = 0.1
            optimized_params["top_p"] = 0.9
        
        elif task_type == GROQTaskType.CODE_GENERATION:
            optimized_params["temperature"] = 0.2
            optimized_params["top_p"] = 0.95
        
        elif task_type == GROQTaskType.CLASSIFICATION:
            optimized_params["temperature"] = 0.0
            optimized_params["max_tokens"] = 100
        
        return optimized_params


class GROQBatchProcessor:
    """Handles batching of GROQ requests for efficiency."""
    
    def __init__(self, config: GROQOptimizationConfig, groq_service: GROQService):
        self.config = config
        self.groq_service = groq_service
        self.pending_requests: List[Tuple[Dict, asyncio.Future]] = []
        self.batch_timer: Optional[asyncio.Task] = None
    
    async def add_request(self, request_data: Dict) -> Dict[str, Any]:
        """Add request to batch processing queue."""
        if not self.config.enable_batching:
            # Process immediately if batching is disabled
            return await self.groq_service.generate_completion(**request_data)
        
        future = asyncio.Future()
        self.pending_requests.append((request_data, future))
        
        # Start batch timer if not already running
        if self.batch_timer is None or self.batch_timer.done():
            self.batch_timer = asyncio.create_task(self._batch_timer())
        
        # Process immediately if batch is full
        if len(self.pending_requests) >= self.config.batch_size:
            await self._process_batch()
        
        return await future
    
    async def _batch_timer(self):
        """Timer for batch processing."""
        await asyncio.sleep(self.config.batch_timeout)
        if self.pending_requests:
            await self._process_batch()
    
    async def _process_batch(self):
        """Process the current batch of requests."""
        if not self.pending_requests:
            return
        
        batch = self.pending_requests.copy()
        self.pending_requests.clear()
        
        # Process requests in parallel
        tasks = []
        for request_data, future in batch:
            task = asyncio.create_task(self._process_single_request(request_data, future))
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_single_request(self, request_data: Dict, future: asyncio.Future):
        """Process a single request from the batch."""
        try:
            result = await self.groq_service.generate_completion(**request_data)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)


class GROQAdaptiveRouter:
    """Adaptive routing based on real-time performance metrics."""
    
    def __init__(self, config: GROQOptimizationConfig, groq_service: GROQService):
        self.config = config
        self.groq_service = groq_service
        self.performance_history: Dict[str, List[float]] = {}
        self.quality_history: Dict[str, List[float]] = {}
        self.cost_history: Dict[str, List[float]] = {}
    
    async def select_optimal_model(
        self, 
        task_type: GROQTaskType,
        priority: str = "balanced"
    ) -> GROQModel:
        """Select optimal model based on adaptive routing."""
        if not self.config.enable_adaptive_routing:
            return await self.groq_service.get_optimal_model(task_type, priority)
        
        # Get performance data for all suitable models
        suitable_models = []
        for model in GROQModel:
            config = self.groq_service.model_configs.get(model)
            if config and config.enabled and task_type in config.optimal_tasks:
                suitable_models.append(model)
        
        if not suitable_models:
            return await self.groq_service.get_optimal_model(task_type, priority)
        
        # Calculate adaptive scores
        model_scores = {}
        for model in suitable_models:
            score = await self._calculate_adaptive_score(model, task_type, priority)
            model_scores[model] = score
        
        # Select best model
        best_model = max(model_scores.items(), key=lambda x: x[1])[0]
        return best_model
    
    async def _calculate_adaptive_score(
        self, 
        model: GROQModel, 
        task_type: GROQTaskType, 
        priority: str
    ) -> float:
        """Calculate adaptive score for model selection."""
        model_config = self.groq_service.model_configs[model]
        base_score = 0.0
        
        # Get recent performance data
        perf_key = f"{model.value}:{task_type.value}"
        recent_performance = self.performance_history.get(perf_key, [])
        recent_quality = self.quality_history.get(perf_key, [])
        recent_cost = self.cost_history.get(perf_key, [])
        
        # Calculate performance score
        if recent_performance:
            avg_performance = sum(recent_performance[-10:]) / len(recent_performance[-10:])
            performance_score = max(0, (5.0 - avg_performance) / 5.0)  # Normalize to 0-1
        else:
            performance_score = model_config.speed_score
        
        # Calculate quality score
        if recent_quality:
            avg_quality = sum(recent_quality[-10:]) / len(recent_quality[-10:])
            quality_score = avg_quality
        else:
            quality_score = model_config.quality_score
        
        # Calculate cost score (lower cost = higher score)
        if recent_cost:
            avg_cost = sum(recent_cost[-10:]) / len(recent_cost[-10:])
            cost_score = max(0, (0.001 - avg_cost) / 0.001)  # Normalize
        else:
            cost_score = max(0, (0.001 - model_config.cost_per_token) / 0.001)
        
        # Weight scores based on priority
        if priority == "speed":
            base_score = performance_score * 0.7 + quality_score * 0.2 + cost_score * 0.1
        elif priority == "quality":
            base_score = quality_score * 0.7 + performance_score * 0.2 + cost_score * 0.1
        elif priority == "cost":
            base_score = cost_score * 0.7 + performance_score * 0.2 + quality_score * 0.1
        else:  # balanced
            base_score = (performance_score + quality_score + cost_score) / 3
        
        return base_score
    
    def record_performance(
        self, 
        model: GROQModel, 
        task_type: GROQTaskType, 
        performance_time: float,
        quality_score: float,
        cost: float
    ):
        """Record performance metrics for adaptive routing."""
        key = f"{model.value}:{task_type.value}"
        
        # Record performance
        if key not in self.performance_history:
            self.performance_history[key] = []
        self.performance_history[key].append(performance_time)
        
        # Record quality
        if key not in self.quality_history:
            self.quality_history[key] = []
        self.quality_history[key].append(quality_score)
        
        # Record cost
        if key not in self.cost_history:
            self.cost_history[key] = []
        self.cost_history[key].append(cost)
        
        # Keep only recent history
        for history in [self.performance_history, self.quality_history, self.cost_history]:
            if len(history[key]) > self.config.performance_window:
                history[key] = history[key][-self.config.performance_window:]


class GROQOptimizer:
    """Main GROQ optimization service."""
    
    def __init__(self, config: Optional[GROQOptimizationConfig] = None):
        """Initialize GROQ optimizer."""
        self.config = config or GROQOptimizationConfig()
        self.groq_service = GROQService()
        self.request_optimizer = GROQRequestOptimizer(self.config)
        self.batch_processor = GROQBatchProcessor(self.config, self.groq_service)
        self.adaptive_router = GROQAdaptiveRouter(self.config, self.groq_service)
        self.metrics = OptimizationMetrics()
        
        logger.info("GROQ optimizer initialized")
    
    async def optimized_completion(
        self,
        messages: List[Dict[str, str]],
        task_type: GROQTaskType = GROQTaskType.CONVERSATION,
        priority: str = "balanced",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate optimized completion using GROQ."""
        start_time = datetime.now()
        
        # Check cache first
        if self.config.enable_response_caching:
            cache_key = self._generate_cache_key(messages, task_type, kwargs)
            cached_result = await cache_manager.async_get(cache_key)
            if cached_result:
                self.metrics.cache_hits += 1
                logger.info("Returning cached GROQ response")
                return cached_result
            self.metrics.cache_misses += 1
        
        # Optimize messages
        if self.config.enable_request_optimization:
            messages = self.request_optimizer.optimize_messages(messages)
        
        # Select optimal model
        model = await self.adaptive_router.select_optimal_model(task_type, priority)
        
        # Optimize parameters
        if self.config.enable_request_optimization:
            kwargs = self.request_optimizer.optimize_parameters(model, task_type, kwargs)
        
        # Prepare request
        request_data = {
            "messages": messages,
            "model": model,
            "task_type": task_type,
            "priority": priority,
            **kwargs
        }
        
        # Process request (with or without batching)
        try:
            if self.config.enable_batching:
                result = await self.batch_processor.add_request(request_data)
                self.metrics.batched_requests += 1
            else:
                result = await self.groq_service.generate_completion(**request_data)
            
            # Record performance for adaptive routing
            processing_time = (datetime.now() - start_time).total_seconds()
            self.adaptive_router.record_performance(
                model, task_type, processing_time,
                result.get("confidence_score", 0.8),
                result.get("cost", 0.0)
            )
            
            # Cache result
            if self.config.enable_response_caching:
                await cache_manager.async_set(cache_key, result, self.config.cache_ttl)
            
            # Update metrics
            self._update_optimization_metrics(result, processing_time)
            
            return result
            
        except Exception as e:
            logger.error(f"GROQ optimization failed: {e}")
            raise
    
    def _generate_cache_key(
        self, 
        messages: List[Dict[str, str]], 
        task_type: GROQTaskType, 
        kwargs: Dict[str, Any]
    ) -> str:
        """Generate cache key for request."""
        content_hash = hash(str(messages) + str(task_type) + str(sorted(kwargs.items())))
        return f"groq_optimized:{content_hash}"
    
    def _update_optimization_metrics(self, result: Dict[str, Any], processing_time: float):
        """Update optimization metrics."""
        # Calculate savings (simplified)
        base_cost = result.get("cost", 0.0) * 1.2  # Assume 20% savings
        self.metrics.cost_savings += base_cost - result.get("cost", 0.0)
        
        # Track performance improvements
        model = result.get("model", "unknown")
        if model not in self.metrics.performance_improvements:
            self.metrics.performance_improvements[model] = []
        
        self.metrics.performance_improvements[model].append(processing_time)
        
        # Keep only recent measurements
        if len(self.metrics.performance_improvements[model]) > 100:
            self.metrics.performance_improvements[model] = self.metrics.performance_improvements[model][-100:]
    
    async def get_optimization_report(self) -> Dict[str, Any]:
        """Get comprehensive optimization report."""
        return {
            "config": {
                "strategy": self.config.strategy.value,
                "caching_enabled": self.config.enable_caching,
                "batching_enabled": self.config.enable_batching,
                "adaptive_routing_enabled": self.config.enable_adaptive_routing
            },
            "metrics": {
                "cache_hit_rate": (
                    self.metrics.cache_hits / max(self.metrics.cache_hits + self.metrics.cache_misses, 1)
                ),
                "batched_requests": self.metrics.batched_requests,
                "model_switches": self.metrics.model_switches,
                "cost_savings": round(self.metrics.cost_savings, 6),
                "optimization_savings": round(self.metrics.optimization_savings, 6)
            },
            "performance": {
                model: {
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "sample_count": len(times)
                }
                for model, times in self.metrics.performance_improvements.items()
                if times
            },
            "groq_service_metrics": self.groq_service.get_metrics_summary()
        }
    
    async def reset_optimization_metrics(self):
        """Reset optimization metrics."""
        self.metrics = OptimizationMetrics()
        await self.groq_service.reset_metrics()
        logger.info("GROQ optimization metrics reset")


# Global instance
_groq_optimizer = None


def get_groq_optimizer() -> GROQOptimizer:
    """Get global GROQ optimizer instance."""
    global _groq_optimizer
    if _groq_optimizer is None:
        _groq_optimizer = GROQOptimizer()
    return _groq_optimizer