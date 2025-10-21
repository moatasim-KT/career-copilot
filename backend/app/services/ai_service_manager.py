"""
AI Service Manager for handling multiple AI providers with intelligent model selection.
Enhanced with performance metrics, streaming support, and token optimization.
"""

import asyncio
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union, AsyncGenerator

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, SystemMessage

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.caching import get_cache_manager, cache_result
from ..core.task_complexity import TaskComplexity, get_complexity_analyzer
from ..core.cost_tracker import CostCategory, get_cost_tracker
from ..monitoring.metrics_collector import get_metrics_collector
from ..core.performance_metrics import get_performance_metrics_collector, TimeWindow
from ..core.streaming_manager import get_streaming_manager, StreamingMode, StreamingChunk
from ..core.token_optimizer import get_token_optimizer, TokenBudget, OptimizationStrategy

logger = get_logger(__name__)
settings = get_settings()
metrics_collector = get_metrics_collector()
cache_manager = get_cache_manager()
complexity_analyzer = get_complexity_analyzer()
cost_tracker = get_cost_tracker()
performance_collector = get_performance_metrics_collector()
streaming_manager = get_streaming_manager()
token_optimizer = get_token_optimizer()


class ModelType(Enum):
    """Types of AI models for different use cases."""
    CONTRACT_ANALYSIS = "contract_analysis"
    NEGOTIATION = "negotiation"
    COMMUNICATION = "communication"
    GENERAL = "general"


class ModelProvider(Enum):
    """AI model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


@dataclass
class ModelConfig:
    """Configuration for an AI model."""
    provider: ModelProvider
    model_name: str
    temperature: float
    max_tokens: int
    cost_per_token: float
    capabilities: List[str]
    priority: int  # Lower number = higher priority
    complexity_level: TaskComplexity  # Recommended complexity level
    tokens_per_minute: int = 10000  # Rate limit
    requests_per_minute: int = 60  # Rate limit


@dataclass
class AIResponse:
    """Response from AI model."""
    content: str
    model_used: str
    provider: ModelProvider
    confidence_score: float
    processing_time: float
    token_usage: Dict[str, int]
    cost: float
    complexity_used: TaskComplexity
    cost_category: CostCategory
    budget_impact: Dict[str, Any]
    metadata: Dict[str, Any]
    # Performance metrics
    performance_metrics: Optional[Dict[str, Any]] = None
    # Streaming information
    is_streaming: bool = False
    streaming_session_id: Optional[str] = None
    # Token optimization
    token_optimization: Optional[Dict[str, Any]] = None


class CircuitBreaker:
    """Circuit breaker for AI service failures."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def call_allowed(self) -> bool:
        """Check if calls are allowed."""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
                return True
            return False
        else:  # half-open
            return True
    
    def record_success(self):
        """Record successful call."""
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self):
        """Record failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"


class AIServiceManager:
    """Manager for multiple AI providers with intelligent selection and fallback."""
    
    def __init__(self):
        """Initialize AI service manager."""
        self.models = self._initialize_models()
        self.circuit_breakers = {
            provider: CircuitBreaker() for provider in ModelProvider
        }
        # Use centralized cache manager instead of local cache
        self.cache_ttl = 3600  # 1 hour
        
    def _initialize_models(self) -> Dict[ModelType, List[ModelConfig]]:
        """Initialize available models for each use case."""
        models = {
            ModelType.CONTRACT_ANALYSIS: [],
            ModelType.NEGOTIATION: [],
            ModelType.COMMUNICATION: [],
            ModelType.GENERAL: []
        }
        
        # OpenAI models
        if hasattr(settings, 'openai_api_key') and settings.openai_api_key:
            # GPT-4 for complex analysis
            models[ModelType.CONTRACT_ANALYSIS].append(ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4",
                temperature=0.1,
                max_tokens=4000,
                cost_per_token=0.00003,
                capabilities=["analysis", "reasoning", "json"],
                priority=1,
                complexity_level=TaskComplexity.COMPLEX,
                tokens_per_minute=10000,
                requests_per_minute=20
            ))
            
            # GPT-4 Turbo for very complex analysis
            models[ModelType.CONTRACT_ANALYSIS].append(ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4-turbo-preview",
                temperature=0.1,
                max_tokens=4000,
                cost_per_token=0.00001,
                capabilities=["analysis", "reasoning", "json", "long_context"],
                priority=1,
                complexity_level=TaskComplexity.COMPLEX,
                tokens_per_minute=15000,
                requests_per_minute=30
            ))
            
            # GPT-3.5 for medium complexity tasks
            models[ModelType.NEGOTIATION].append(ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                temperature=0.3,
                max_tokens=2000,
                cost_per_token=0.000002,
                capabilities=["generation", "reasoning"],
                priority=2,
                complexity_level=TaskComplexity.MEDIUM,
                tokens_per_minute=40000,
                requests_per_minute=60
            ))
            
            models[ModelType.COMMUNICATION].append(ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                temperature=0.5,
                max_tokens=1500,
                cost_per_token=0.000002,
                capabilities=["generation", "communication"],
                priority=2,
                complexity_level=TaskComplexity.SIMPLE,
                tokens_per_minute=40000,
                requests_per_minute=60
            ))
            
            # Add general purpose models for different complexity levels
            models[ModelType.GENERAL].append(ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                temperature=0.2,
                max_tokens=2000,
                cost_per_token=0.000002,
                capabilities=["generation", "reasoning"],
                priority=3,
                complexity_level=TaskComplexity.SIMPLE,
                tokens_per_minute=40000,
                requests_per_minute=60
            ))
        
        # Anthropic models
        if hasattr(settings, 'anthropic_api_key') and settings.anthropic_api_key:
            models[ModelType.CONTRACT_ANALYSIS].append(ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model_name="claude-3-opus-20240229",
                temperature=0.1,
                max_tokens=4000,
                cost_per_token=0.000075,
                capabilities=["analysis", "reasoning", "long_context"],
                priority=1,
                complexity_level=TaskComplexity.COMPLEX,
                tokens_per_minute=8000,
                requests_per_minute=15
            ))
            
            models[ModelType.CONTRACT_ANALYSIS].append(ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model_name="claude-3-sonnet-20240229",
                temperature=0.1,
                max_tokens=4000,
                cost_per_token=0.000015,
                capabilities=["analysis", "reasoning", "long_context"],
                priority=2,
                complexity_level=TaskComplexity.MEDIUM,
                tokens_per_minute=20000,
                requests_per_minute=40
            ))
            
            models[ModelType.NEGOTIATION].append(ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model_name="claude-3-haiku-20240307",
                temperature=0.3,
                max_tokens=2000,
                cost_per_token=0.00000025,
                capabilities=["generation", "reasoning", "speed"],
                priority=3,
                complexity_level=TaskComplexity.SIMPLE,
                tokens_per_minute=50000,
                requests_per_minute=100
            ))
        
        # Add Groq models if available (fast and cost-effective)
        if hasattr(settings, 'groq_api_key') and settings.groq_api_key:
            models[ModelType.COMMUNICATION].append(ModelConfig(
                provider=ModelProvider.OPENAI,  # Groq uses OpenAI-compatible API
                model_name="mixtral-8x7b-32768",
                temperature=0.3,
                max_tokens=2000,
                cost_per_token=0.0000002,  # Very low cost
                capabilities=["generation", "speed"],
                priority=4,
                complexity_level=TaskComplexity.SIMPLE,
                tokens_per_minute=100000,
                requests_per_minute=200
            ))
        
        return models
    
    async def analyze_with_fallback(
        self, 
        model_type: ModelType, 
        prompt: str,
        criteria: str = "cost",
        max_retries: int = 3,
        context: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        budget_limit: Optional[float] = None,
        enable_streaming: bool = False,
        streaming_mode: StreamingMode = StreamingMode.BUFFERED,
        token_budget: Optional[TokenBudget] = None,
        optimization_strategy: OptimizationStrategy = OptimizationStrategy.BALANCED
    ) -> Union[AIResponse, AsyncGenerator[StreamingChunk, None]]:
        """
        Analyze with intelligent model selection and fallback.
        
        Args:
            model_type: Type of model needed
            prompt: Input prompt
            criteria: Selection criteria ("cost", "quality", "speed", "confidence", "complexity")
            max_retries: Maximum retry attempts
            context: Additional context for complexity analysis
            user_id: User ID for budget tracking
            session_id: Session ID for tracking
            budget_limit: Optional budget limit for this request
            enable_streaming: Enable streaming response
            streaming_mode: Streaming mode configuration
            token_budget: Token budget for optimization
            optimization_strategy: Token optimization strategy
            
        Returns:
            AIResponse with analysis results or AsyncGenerator for streaming
        """
        # Analyze task complexity
        task_complexity = complexity_analyzer.analyze_task_complexity(
            prompt=prompt,
            context=context,
            task_type=model_type.value
        )
        
        # Determine cost category
        cost_category = self._map_model_type_to_cost_category(model_type)
        
        # Prepare messages for processing
        messages = [HumanMessage(content=prompt)]
        if context:
            messages.insert(0, SystemMessage(content=context))
        
        # Apply token optimization if budget is specified
        optimization_result = None
        if token_budget:
            messages, optimization_result = token_optimizer.optimize_for_budget(
                messages, token_budget, task_complexity
            )
            logger.info(f"Token optimization: {optimization_result.reduction_percentage:.1f}% reduction")
        
        # Check cache first (skip for streaming requests)
        cache_key = f"ai_response:{model_type.value}:{task_complexity.value}:{hash(prompt)}"
        if not enable_streaming:
            cached_response = await cache_manager.async_get(cache_key)
            if cached_response is not None:
                logger.info("Returning cached AI response")
                return cached_response
        
        # Get available models for this type
        available_models = self.models.get(model_type, [])
        if not available_models:
            raise ValueError(f"No models available for {model_type.value}")
        
        # Filter models by complexity and sort by criteria
        suitable_models = self._filter_models_by_complexity(available_models, task_complexity)
        sorted_models = self._sort_models_by_criteria(suitable_models, criteria, task_complexity)
        
        # Handle streaming requests
        if enable_streaming:
            return await self._handle_streaming_request(
                sorted_models, messages, model_type, task_complexity, cost_category,
                streaming_mode, user_id, session_id, budget_limit, optimization_result
            )
        
        # Handle regular requests with performance tracking
        return await self._handle_regular_request(
            sorted_models, messages, model_type, task_complexity, cost_category,
            max_retries, user_id, session_id, budget_limit, optimization_result, cache_key
        )
    
    def _map_model_type_to_cost_category(self, model_type: ModelType) -> CostCategory:
        """Map model type to cost category."""
        mapping = {
            ModelType.CONTRACT_ANALYSIS: CostCategory.CONTRACT_ANALYSIS,
            ModelType.NEGOTIATION: CostCategory.NEGOTIATION,
            ModelType.COMMUNICATION: CostCategory.COMMUNICATION,
            ModelType.GENERAL: CostCategory.GENERAL
        }
        return mapping.get(model_type, CostCategory.GENERAL)
    
    def _filter_models_by_complexity(self, models: List[ModelConfig], task_complexity: TaskComplexity) -> List[ModelConfig]:
        """Filter models suitable for the given task complexity."""
        suitable_models = []
        
        for model in models:
            # Allow models at the same complexity level or higher capability
            if task_complexity == TaskComplexity.SIMPLE:
                # Simple tasks can use any model
                suitable_models.append(model)
            elif task_complexity == TaskComplexity.MEDIUM:
                # Medium tasks need medium or complex models
                if model.complexity_level in [TaskComplexity.MEDIUM, TaskComplexity.COMPLEX]:
                    suitable_models.append(model)
            else:  # COMPLEX
                # Complex tasks need complex models
                if model.complexity_level == TaskComplexity.COMPLEX:
                    suitable_models.append(model)
        
        # If no suitable models found, fall back to all models
        if not suitable_models:
            logger.warning(f"No models found for complexity {task_complexity.value}, using all available")
            suitable_models = models
        
        return suitable_models
    
    def _sort_models_by_criteria(self, models: List[ModelConfig], criteria: str, task_complexity: TaskComplexity) -> List[ModelConfig]:
        """Sort models by selection criteria with complexity awareness."""
        if criteria == "cost":
            return sorted(models, key=lambda m: m.cost_per_token)
        elif criteria == "quality":
            return sorted(models, key=lambda m: m.priority)
        elif criteria == "speed":
            # Prefer models with higher throughput
            return sorted(models, key=lambda m: (-m.tokens_per_minute, m.priority))
        elif criteria == "confidence":
            # Prefer higher-capability models
            return sorted(models, key=lambda m: (len(m.capabilities), m.priority), reverse=True)
        elif criteria == "complexity":
            # Sort by complexity match first, then by cost
            def complexity_sort_key(model):
                complexity_match = 1 if model.complexity_level == task_complexity else 0
                return (-complexity_match, model.cost_per_token)
            return sorted(models, key=complexity_sort_key)
        else:
            return sorted(models, key=lambda m: m.priority)
    
    async def _call_model(
        self, 
        model_config: ModelConfig, 
        prompt: str, 
        task_complexity: TaskComplexity,
        cost_category: CostCategory,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> AIResponse:
        """Call a specific AI model."""
        start_time = time.time()
        
        try:
            if model_config.provider == ModelProvider.OPENAI:
                response = await self._call_openai(model_config, prompt)
            elif model_config.provider == ModelProvider.ANTHROPIC:
                response = await self._call_anthropic(model_config, prompt)
            else:
                raise ValueError(f"Unsupported provider: {model_config.provider}")
            
            processing_time = time.time() - start_time
            
            # Calculate confidence score (simplified)
            confidence_score = self._calculate_confidence(response, model_config)
            
            # Calculate cost
            token_usage = self._extract_token_usage(response)
            cost = token_usage.get("total_tokens", 0) * model_config.cost_per_token
            
            # Record cost in cost tracker
            cost_entry = await cost_tracker.record_cost(
                provider=model_config.provider.value,
                model=model_config.model_name,
                category=cost_category,
                prompt_tokens=token_usage.get("prompt_tokens", 0),
                completion_tokens=token_usage.get("completion_tokens", 0),
                cost=cost,
                user_id=user_id,
                session_id=session_id,
                metadata={
                    "task_complexity": task_complexity.value,
                    "temperature": model_config.temperature,
                    "max_tokens": model_config.max_tokens
                }
            )
            
            # Get budget impact
            budget_statuses = await cost_tracker.check_budget_limits(
                category=cost_category,
                estimated_cost=0,  # Already spent
                user_id=user_id
            )
            
            budget_impact = {
                "cost_recorded": str(cost_entry.cost),
                "affected_budgets": [status.to_dict() for status in budget_statuses]
            }
            
            ai_response = AIResponse(
                content=response.content,
                model_used=model_config.model_name,
                provider=model_config.provider,
                confidence_score=confidence_score,
                processing_time=processing_time,
                token_usage=token_usage,
                cost=cost,
                complexity_used=task_complexity,
                cost_category=cost_category,
                budget_impact=budget_impact,
                metadata={
                    "temperature": model_config.temperature,
                    "max_tokens": model_config.max_tokens,
                    "complexity_level": model_config.complexity_level.value
                }
            )
            
            # Record AI request metrics
            metrics_collector.record_ai_request(
                provider=model_config.provider.value,
                model=model_config.model_name,
                status="success",
                duration=processing_time,
                token_usage=token_usage,
                cost=cost
            )
            
            return ai_response
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Record failed AI request metrics
            metrics_collector.record_ai_request(
                provider=model_config.provider.value,
                model=model_config.model_name,
                status="failed",
                duration=processing_time,
                token_usage={},
                cost=0.0
            )
            
            logger.error(f"Error calling {model_config.model_name}: {e}")
            raise
    
    async def _call_openai(self, model_config: ModelConfig, prompt: str):
        """Call OpenAI model."""
        llm = ChatOpenAI(
            model=model_config.model_name,
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens,
            api_key=settings.openai_api_key.get_secret_value()
        )
        
        messages = [HumanMessage(content=prompt)]
        response = await llm.ainvoke(messages)
        return response
    
    async def _call_anthropic(self, model_config: ModelConfig, prompt: str):
        """Call Anthropic model."""
        llm = ChatAnthropic(
            model=model_config.model_name,
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens,
            api_key=settings.anthropic_api_key
        )
        
        messages = [HumanMessage(content=prompt)]
        response = await llm.ainvoke(messages)
        return response
    
    def _calculate_confidence(self, response, model_config: ModelConfig) -> float:
        """Calculate confidence score for response."""
        # Simplified confidence calculation
        base_confidence = 0.7
        
        # Higher confidence for better models
        if "gpt-4" in model_config.model_name:
            base_confidence = 0.9
        elif "claude-3" in model_config.model_name:
            base_confidence = 0.85
        
        # Adjust based on response length (longer responses might be more detailed)
        if len(response.content) > 1000:
            base_confidence += 0.05
        
        return min(base_confidence, 1.0)
    
    def _extract_token_usage(self, response) -> Dict[str, int]:
        """Extract token usage from response."""
        # Try to extract token usage from response metadata
        if hasattr(response, 'response_metadata'):
            usage = response.response_metadata.get('token_usage', {})
            return {
                "prompt_tokens": usage.get('prompt_tokens', 0),
                "completion_tokens": usage.get('completion_tokens', 0),
                "total_tokens": usage.get('total_tokens', 0)
            }
        
        # Fallback: estimate based on content length
        estimated_tokens = len(response.content.split()) * 1.3  # Rough estimate
        return {
            "prompt_tokens": 0,
            "completion_tokens": int(estimated_tokens),
            "total_tokens": int(estimated_tokens)
        }
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get list of available models by type."""
        result = {}
        for model_type, configs in self.models.items():
            result[model_type.value] = [
                f"{config.provider.value}:{config.model_name}" 
                for config in configs
            ]
        return result
    
    def get_service_health(self) -> Dict[str, Any]:
        """Get health status of AI services."""
        health = {}
        for provider, circuit_breaker in self.circuit_breakers.items():
            health[provider.value] = {
                "state": circuit_breaker.state,
                "failure_count": circuit_breaker.failure_count,
                "last_failure": circuit_breaker.last_failure_time
            }
        return health
    
    def clear_cache(self):
        """Clear AI response cache."""
        cache_manager.invalidate_pattern("ai_response:*")
        logger.info("AI response cache cleared")
    
    async def get_cost_estimate(
        self, 
        model_type: ModelType, 
        prompt: str, 
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get cost estimate for a request without executing it."""
        # Analyze task complexity
        task_complexity = complexity_analyzer.analyze_task_complexity(
            prompt=prompt,
            context=context,
            task_type=model_type.value
        )
        
        # Get available models
        available_models = self.models.get(model_type, [])
        suitable_models = self._filter_models_by_complexity(available_models, task_complexity)
        
        # Estimate tokens
        estimated_tokens = len(prompt.split()) * 1.5
        if context:
            estimated_tokens += len(context.split()) * 1.3
        
        # Calculate estimates for each suitable model
        estimates = []
        for model in suitable_models:
            cost_estimate = estimated_tokens * model.cost_per_token
            estimates.append({
                "provider": model.provider.value,
                "model": model.model_name,
                "complexity_level": model.complexity_level.value,
                "estimated_tokens": int(estimated_tokens),
                "estimated_cost": cost_estimate,
                "cost_per_token": model.cost_per_token,
                "priority": model.priority
            })
        
        # Sort by cost
        estimates.sort(key=lambda x: x["estimated_cost"])
        
        return {
            "task_complexity": task_complexity.value,
            "total_models_available": len(available_models),
            "suitable_models": len(suitable_models),
            "cost_estimates": estimates,
            "recommended_model": estimates[0] if estimates else None
        }
    
    async def get_complexity_analysis(self, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed complexity analysis for a prompt."""
        # Analyze complexity for different task types
        analyses = {}
        
        for model_type in ModelType:
            complexity = complexity_analyzer.analyze_task_complexity(
                prompt=prompt,
                context=context,
                task_type=model_type.value
            )
            
            recommended_providers = complexity_analyzer.get_recommended_providers(complexity)
            cost_multiplier = complexity_analyzer.estimate_cost_multiplier(complexity)
            
            analyses[model_type.value] = {
                "complexity": complexity.value,
                "recommended_providers": recommended_providers,
                "cost_multiplier": cost_multiplier
            }
        
        return {
            "prompt_length": len(prompt),
            "context_length": len(context) if context else 0,
            "analyses_by_task_type": analyses
        }
    
    async def get_budget_status(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get current budget status."""
        budget_statuses = await cost_tracker.get_all_budget_statuses(user_id)
        
        return {
            "user_id": user_id,
            "budget_count": len(budget_statuses),
            "budgets": [status.to_dict() for status in budget_statuses],
            "alerts": [
                status.to_dict() for status in budget_statuses 
                if status.alert_triggered
            ],
            "exceeded": [
                status.to_dict() for status in budget_statuses 
                if status.limit_exceeded
            ]
        }
    
    async def optimize_model_selection(
        self,
        model_type: ModelType,
        prompt: str,
        context: Optional[str] = None,
        budget_constraint: Optional[float] = None,
        quality_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Optimize model selection based on constraints."""
        # Analyze task complexity
        task_complexity = complexity_analyzer.analyze_task_complexity(
            prompt=prompt,
            context=context,
            task_type=model_type.value
        )
        
        # Get suitable models
        available_models = self.models.get(model_type, [])
        suitable_models = self._filter_models_by_complexity(available_models, task_complexity)
        
        # Estimate costs
        estimated_tokens = len(prompt.split()) * 1.5
        if context:
            estimated_tokens += len(context.split()) * 1.3
        
        # Filter by budget constraint
        if budget_constraint:
            suitable_models = [
                model for model in suitable_models
                if estimated_tokens * model.cost_per_token <= budget_constraint
            ]
        
        # Filter by quality threshold (based on priority - lower is better)
        if quality_threshold:
            suitable_models = [
                model for model in suitable_models
                if model.priority <= quality_threshold
            ]
        
        if not suitable_models:
            return {
                "error": "No models meet the specified constraints",
                "task_complexity": task_complexity.value,
                "budget_constraint": budget_constraint,
                "quality_threshold": quality_threshold
            }
        
        # Sort by cost-effectiveness (cost per capability)
        def cost_effectiveness_score(model):
            cost = estimated_tokens * model.cost_per_token
            capability_score = len(model.capabilities) / model.priority
            return cost / capability_score if capability_score > 0 else float('inf')
        
        suitable_models.sort(key=cost_effectiveness_score)
        
        recommended_model = suitable_models[0]
        
        return {
            "task_complexity": task_complexity.value,
            "recommended_model": {
                "provider": recommended_model.provider.value,
                "model": recommended_model.model_name,
                "complexity_level": recommended_model.complexity_level.value,
                "estimated_cost": estimated_tokens * recommended_model.cost_per_token,
                "priority": recommended_model.priority,
                "capabilities": recommended_model.capabilities
            },
            "alternatives": [
                {
                    "provider": model.provider.value,
                    "model": model.model_name,
                    "estimated_cost": estimated_tokens * model.cost_per_token,
                    "priority": model.priority
                }
                for model in suitable_models[1:5]  # Top 5 alternatives
            ],
            "constraints_applied": {
                "budget_constraint": budget_constraint,
                "quality_threshold": quality_threshold
            }
        }
    
    async def _handle_streaming_request(
        self, 
        sorted_models: List[ModelConfig],
        messages: List[BaseMessage],
        model_type: ModelType,
        task_complexity: TaskComplexity,
        cost_category: CostCategory,
        streaming_mode: StreamingMode,
        user_id: Optional[str],
        session_id: Optional[str],
        budget_limit: Optional[float],
        optimization_result: Optional[Any]
    ) -> AsyncGenerator[StreamingChunk, None]:
        """Handle streaming AI requests with performance tracking."""
        
        for model_config in sorted_models:
            # Check circuit breaker
            if not self.circuit_breakers[model_config.provider].call_allowed():
                logger.warning(f"Circuit breaker open for {model_config.provider.value}")
                continue
            
            # Budget checks
            estimated_tokens = sum(len(msg.content.split()) for msg in messages) * 1.5
            estimated_cost = estimated_tokens * model_config.cost_per_token
            
            if budget_limit and estimated_cost > budget_limit:
                logger.warning(f"Budget limit exceeded for streaming request")
                continue
            
            try:
                # Create streaming session
                streaming_session = streaming_manager.create_streaming_session(
                    provider=model_config.provider.value,
                    model=model_config.model_name,
                    operation=model_type.value,
                    mode=streaming_mode
                )
                
                # Create LLM instance
                llm = await self._create_llm_instance(model_config)
                
                # Stream response
                async for chunk in streaming_manager.stream_llm_response(llm, messages, streaming_session):
                    yield chunk
                
                # Record success
                self.circuit_breakers[model_config.provider].record_success()
                return
                
            except Exception as e:
                logger.error(f"Streaming failed for {model_config.model_name}: {e}")
                self.circuit_breakers[model_config.provider].record_failure()
                continue
        
        raise Exception("All models failed for streaming request")
    
    async def _handle_regular_request(
        self,
        sorted_models: List[ModelConfig],
        messages: List[BaseMessage],
        model_type: ModelType,
        task_complexity: TaskComplexity,
        cost_category: CostCategory,
        max_retries: int,
        user_id: Optional[str],
        session_id: Optional[str],
        budget_limit: Optional[float],
        optimization_result: Optional[Any],
        cache_key: str
    ) -> AIResponse:
        """Handle regular AI requests with performance tracking."""
        
        last_error = None
        
        for attempt in range(max_retries):
            for model_config in sorted_models:
                # Check circuit breaker
                if not self.circuit_breakers[model_config.provider].call_allowed():
                    logger.warning(f"Circuit breaker open for {model_config.provider.value}")
                    continue
                
                # Budget checks
                estimated_tokens = sum(len(msg.content.split()) for msg in messages) * 1.5
                estimated_cost = estimated_tokens * model_config.cost_per_token
                
                if budget_limit and estimated_cost > budget_limit:
                    logger.warning(f"Budget limit exceeded: ${estimated_cost:.4f} > ${budget_limit:.4f}")
                    continue
                
                try:
                    # Start performance tracking
                    request_id = str(uuid.uuid4())
                    request_context = performance_collector.record_request_start(
                        request_id=request_id,
                        provider=model_config.provider.value,
                        model=model_config.model_name,
                        operation=model_type.value,
                        is_streaming=False
                    )
                    
                    # Call model with performance tracking
                    response = await self._call_model_with_performance_tracking(
                        model_config, messages, task_complexity, cost_category,
                        user_id, session_id, request_context, optimization_result
                    )
                    
                    # Record success
                    self.circuit_breakers[model_config.provider].record_success()
                    
                    # Cache response
                    await cache_manager.async_set(cache_key, response, self.cache_ttl)
                    
                    return response
                    
                except Exception as e:
                    last_error = e
                    logger.warning(f"Model {model_config.model_name} failed: {e}")
                    self.circuit_breakers[model_config.provider].record_failure()
                    continue
            
            # Wait before retry
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        
        raise Exception(f"All AI models failed. Last error: {last_error}")
    
    async def _create_llm_instance(self, model_config: ModelConfig):
        """Create LLM instance for the given model configuration."""
        if model_config.provider == ModelProvider.OPENAI:
            return ChatOpenAI(
                model=model_config.model_name,
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens,
                api_key=settings.openai_api_key.get_secret_value()
            )
        elif model_config.provider == ModelProvider.ANTHROPIC:
            return ChatAnthropic(
                model=model_config.model_name,
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens,
                api_key=settings.anthropic_api_key
            )
        else:
            raise ValueError(f"Unsupported provider: {model_config.provider}")
    
    async def _call_model_with_performance_tracking(
        self,
        model_config: ModelConfig,
        messages: List[BaseMessage],
        task_complexity: TaskComplexity,
        cost_category: CostCategory,
        user_id: Optional[str],
        session_id: Optional[str],
        request_context: Dict[str, Any],
        optimization_result: Optional[Any]
    ) -> AIResponse:
        """Call model with comprehensive performance tracking."""
        
        try:
            # Create LLM instance
            llm = await self._create_llm_instance(model_config)
            
            # Execute request
            response = await llm.ainvoke(messages)
            
            # Extract token usage and calculate cost
            token_usage = self._extract_token_usage(response)
            cost = token_usage.get("total_tokens", 0) * model_config.cost_per_token
            
            # Record performance metrics
            performance_collector.record_request_completion(
                request_context=request_context,
                success=True,
                token_usage=token_usage,
                cost=cost
            )
            
            # Get performance metrics for this model
            performance_metrics = performance_collector.get_aggregated_metrics(
                provider=model_config.provider.value,
                model=model_config.model_name,
                operation=request_context["operation"],
                time_window=TimeWindow.HOUR
            )
            
            # Record cost in cost tracker
            cost_entry = await cost_tracker.record_cost(
                provider=model_config.provider.value,
                model=model_config.model_name,
                category=cost_category,
                prompt_tokens=token_usage.get("prompt_tokens", 0),
                completion_tokens=token_usage.get("completion_tokens", 0),
                cost=cost,
                user_id=user_id,
                session_id=session_id,
                metadata={
                    "task_complexity": task_complexity.value,
                    "temperature": model_config.temperature,
                    "max_tokens": model_config.max_tokens,
                    "optimization_applied": optimization_result is not None
                }
            )
            
            # Get budget impact
            budget_statuses = await cost_tracker.check_budget_limits(
                category=cost_category,
                estimated_cost=0,  # Already spent
                user_id=user_id
            )
            
            budget_impact = {
                "cost_recorded": str(cost_entry.cost),
                "affected_budgets": [status.to_dict() for status in budget_statuses]
            }
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence(response, model_config)
            
            # Create AI response with performance data
            ai_response = AIResponse(
                content=response.content,
                model_used=model_config.model_name,
                provider=model_config.provider,
                confidence_score=confidence_score,
                processing_time=request_context.get("processing_time", 0),
                token_usage=token_usage,
                cost=cost,
                complexity_used=task_complexity,
                cost_category=cost_category,
                budget_impact=budget_impact,
                metadata={
                    "temperature": model_config.temperature,
                    "max_tokens": model_config.max_tokens,
                    "complexity_level": model_config.complexity_level.value,
                    "request_id": request_context["request_id"]
                },
                performance_metrics={
                    "latency": performance_metrics.latency.__dict__ if performance_metrics and performance_metrics.latency else None,
                    "success_rate": performance_metrics.success_rate.__dict__ if performance_metrics and performance_metrics.success_rate else None,
                    "token_usage_stats": performance_metrics.token_usage.__dict__ if performance_metrics and performance_metrics.token_usage else None
                },
                is_streaming=False,
                streaming_session_id=None,
                token_optimization={
                    "applied": optimization_result is not None,
                    "reduction_percentage": optimization_result.reduction_percentage if optimization_result else 0,
                    "techniques_used": [t.value for t in optimization_result.techniques_used] if optimization_result else [],
                    "quality_score": optimization_result.quality_score if optimization_result else 1.0
                }
            )
            
            # Record AI request metrics in monitoring system
            metrics_collector.record_ai_request(
                provider=model_config.provider.value,
                model=model_config.model_name,
                status="success",
                duration=ai_response.processing_time,
                token_usage=token_usage,
                cost=cost
            )
            
            return ai_response
            
        except Exception as e:
            # Record failed request
            performance_collector.record_request_completion(
                request_context=request_context,
                success=False,
                token_usage={},
                cost=0.0,
                error_type=type(e).__name__
            )
            
            # Record failed AI request metrics
            metrics_collector.record_ai_request(
                provider=model_config.provider.value,
                model=model_config.model_name,
                status="failed",
                duration=time.time() - request_context["start_time"],
                token_usage={},
                cost=0.0,
                error_type=type(e).__name__
            )
            
            raise
    
    async def analyze_with_streaming(
        self,
        model_type: ModelType,
        prompt: str,
        streaming_mode: StreamingMode = StreamingMode.BUFFERED,
        context: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        optimization_config: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[StreamingChunk, None]:
        """Analyze with streaming response and advanced optimizations."""
        
        # Use the main method with streaming enabled
        async for chunk in await self.analyze_with_fallback(
            model_type=model_type,
            prompt=prompt,
            context=context,
            user_id=user_id,
            session_id=session_id,
            enable_streaming=True,
            streaming_mode=streaming_mode
        ):
            yield chunk
    
    def get_performance_summary(self, time_window: TimeWindow = TimeWindow.HOUR) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        return performance_collector.get_performance_summary(time_window)
    
    def get_streaming_performance(self) -> Dict[str, Any]:
        """Get streaming performance summary."""
        return streaming_manager.get_streaming_performance_summary()
    
    def get_token_optimization_stats(self) -> Dict[str, Any]:
        """Get token optimization statistics."""
        return token_optimizer.get_optimization_stats()


# Global instance
_ai_service_manager = None


def get_ai_service_manager() -> AIServiceManager:
    """Get global AI service manager instance."""
    global _ai_service_manager
    if _ai_service_manager is None:
        _ai_service_manager = AIServiceManager()
    return _ai_service_manager