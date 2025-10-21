"""
Enhanced Base Agent Class for CrewAI Contract Analysis

This module provides the enhanced base class for all specialized job application tracking agents,
implementing comprehensive error handling, retry mechanisms, fallback providers, and
detailed logging with correlation IDs.
"""

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from crewai import Agent
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from ..core.config import get_settings
from ..core.exceptions import (
    ErrorCategory, 
    ErrorSeverity, 
    WorkflowExecutionError,
    ExternalServiceError,
    ContractAnalysisError
)
from ..core.langsmith_integration import trace_ai_operation
from ..core.retry_handler import (
    get_retry_handler,
    RetryConfig,
    CircuitBreakerConfig,
    with_retry,
    with_circuit_breaker
)
from ..core.fallback_manager import get_fallback_manager, FallbackConfig
from ..core.correlation_manager import (
    get_correlation_manager,
    correlation_context,
    log_with_correlation,
    get_correlation_id
)
from ..core.agent_cache_manager import get_agent_cache_manager, AgentType
from ..utils.cache_utilities import (
    cached_agent_execution,
    timeout_handler,
    cache_context,
    cache_invalidation_manager,
    cache_metrics_collector
)
from ..models.agent_models import (
    AgentState,
    AgentProgressMetrics,
    WorkflowProgress,
    get_workflow_progress_manager
)

logger = logging.getLogger(__name__)


class AgentMemory(BaseModel):
    """Shared memory structure for agent communication"""
    
    agent_id: str = Field(description="Unique identifier for the agent")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict, description="Agent-specific data")
    context: Dict[str, Any] = Field(default_factory=dict, description="Shared context data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")


class AgentCommunicationProtocol:
    """Protocol for agent-to-agent communication"""
    
    def __init__(self):
        self.shared_memory: Dict[str, AgentMemory] = {}
        self.message_queue: List[Dict[str, Any]] = []
    
    def store_memory(self, agent_id: str, data: Dict[str, Any], context: Dict[str, Any] = None) -> None:
        """Store data in shared memory for other agents to access"""
        memory = AgentMemory(
            agent_id=agent_id,
            data=data,
            context=context or {},
            metadata={"stored_at": datetime.utcnow()}
        )
        self.shared_memory[agent_id] = memory
        logger.debug(f"Agent {agent_id} stored memory with keys: {list(data.keys())}")
    
    def retrieve_memory(self, agent_id: str) -> Optional[AgentMemory]:
        """Retrieve memory from a specific agent"""
        return self.shared_memory.get(agent_id)
    
    def get_all_memories(self) -> Dict[str, AgentMemory]:
        """Get all stored memories"""
        return self.shared_memory.copy()
    
    def send_message(self, from_agent: str, to_agent: str, message: Dict[str, Any]) -> None:
        """Send a message between agents"""
        message_data = {
            "id": str(uuid.uuid4()),
            "from_agent": from_agent,
            "to_agent": to_agent,
            "message": message,
            "timestamp": datetime.utcnow()
        }
        self.message_queue.append(message_data)
        logger.debug(f"Message sent from {from_agent} to {to_agent}")
    
    def get_messages_for_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a specific agent"""
        return [msg for msg in self.message_queue if msg["to_agent"] == agent_id]
    
    def clear_messages_for_agent(self, agent_id: str) -> None:
        """Clear processed messages for an agent"""
        self.message_queue = [msg for msg in self.message_queue if msg["to_agent"] != agent_id]


class BaseContractAgent(ABC):
    """
    Enhanced base class for all job application tracking agents.
    
    Provides comprehensive functionality including:
    - Agent initialization and configuration
    - Shared memory management
    - Communication protocols
    - Enhanced error handling with retry mechanisms
    - Fallback provider switching (OpenAI → Groq → Gemini)
    - Circuit breaker pattern for preventing cascading failures
    - Detailed error logging with correlation IDs
    - Graceful failure handling with partial results
    - Performance monitoring and metrics
    """
    
    def __init__(
        self,
        agent_name: str,
        role: str,
        goal: str,
        backstory: str,
        communication_protocol: AgentCommunicationProtocol,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the enhanced base agent.
        
        Args:
            agent_name: Unique name for the agent
            role: Role description for the agent
            goal: Goal description for the agent
            backstory: Backstory for the agent
            communication_protocol: Shared communication protocol
            config: Optional configuration parameters
        """
        self.agent_name = agent_name
        self.agent_id = f"{agent_name}_{uuid.uuid4().hex[:8]}"
        self.communication_protocol = communication_protocol
        self.config = config or {}
        
        # Initialize enhanced services
        self.settings = get_settings()
        self.retry_handler = get_retry_handler()
        self.fallback_manager = get_fallback_manager()
        self.correlation_manager = get_correlation_manager()
        self.agent_cache_manager = get_agent_cache_manager()
        
        # Agent type for caching (should be overridden by subclasses)
        self.agent_type = getattr(self, 'agent_type', None)
        
        # Enhanced configuration
        self.retry_config = self._create_retry_config()
        self.circuit_breaker_config = self._create_circuit_breaker_config()
        self.fallback_config = self._create_fallback_config()
        
        # Initialize LLM with fallback support
        self.llm = self._initialize_llm()
        self._register_with_fallback_manager()
        
        # Create CrewAI agent
        self.crew_agent = self._create_crew_agent(role, goal, backstory)
        
        # Initialize enhanced agent state
        self.state = {
            "initialized_at": datetime.utcnow(),
            "execution_count": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "last_execution": None,
            "errors": [],
            "performance_metrics": {},
            "retry_statistics": {
                "total_retries": 0,
                "successful_retries": 0,
                "failed_retries": 0,
            },
            "fallback_statistics": {
                "fallback_used": 0,
                "providers_used": {},
            },
            "circuit_breaker_trips": 0,
        }
        
        # Initialize agent state tracking
        self.progress_metrics = AgentProgressMetrics(agent_name=self.agent_name)
        self.workflow_progress_manager = get_workflow_progress_manager()
        self.current_workflow_id: Optional[str] = None
        
        log_with_correlation(
            "INFO", 
            f"Initialized enhanced {self.agent_name} agent with ID: {self.agent_id}",
            component="base_agent",
            operation="agent_initialization"
        )
    
    def _create_retry_config(self) -> RetryConfig:
        """Create retry configuration for the agent."""
        return RetryConfig(
            max_attempts=self.config.get("max_retry_attempts", 3),
            base_delay=self.config.get("retry_base_delay", 2.0),
            max_delay=self.config.get("retry_max_delay", 60.0),
            exponential_base=self.config.get("retry_exponential_base", 2.0),
            jitter=self.config.get("retry_jitter", True),
        )
    
    def _create_circuit_breaker_config(self) -> CircuitBreakerConfig:
        """Create circuit breaker configuration for the agent."""
        return CircuitBreakerConfig(
            failure_threshold=self.config.get("circuit_breaker_failure_threshold", 5),
            recovery_timeout=self.config.get("circuit_breaker_recovery_timeout", 60),
            success_threshold=self.config.get("circuit_breaker_success_threshold", 3),
        )
    
    def _create_fallback_config(self) -> FallbackConfig:
        """Create fallback configuration for the agent."""
        return FallbackConfig(
            strategy=self.config.get("fallback_strategy", "sequential"),
            timeout_per_provider=self.config.get("provider_timeout", 30.0),
        )
    
    def _initialize_llm(self) -> ChatOpenAI:
        """Initialize the language model for the agent with enhanced error handling."""
        try:
            # Primary LLM (OpenAI)
            llm = ChatOpenAI(
                model=self.settings.openai_model,
                temperature=self.config.get("temperature", self.settings.openai_temperature),
                api_key=self.settings.openai_api_key.get_secret_value(),
                max_tokens=self.config.get("max_tokens", 2000),
                timeout=self.config.get("timeout", 60)
            )
            
            log_with_correlation(
                "INFO",
                f"Successfully initialized primary LLM for {self.agent_name}",
                component="base_agent",
                operation="llm_initialization"
            )
            
            return llm
            
        except Exception as e:
            log_with_correlation(
                "ERROR",
                f"Failed to initialize LLM for {self.agent_name}: {e}",
                component="base_agent",
                operation="llm_initialization",
                error=e
            )
            
            raise WorkflowExecutionError(
                f"Failed to initialize LLM for {self.agent_name}: {e}",
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.HIGH
            )
    
    def _register_with_fallback_manager(self):
        """Register this agent's LLM providers with the fallback manager."""
        try:
            # Register primary OpenAI provider
            if hasattr(self, 'llm') and self.llm:
                self.fallback_manager.register_provider("openai", self.llm)
            
            # Register additional providers if available
            if hasattr(self.settings, 'groq_api_key') and self.settings.groq_api_key:
                # GROQ provider would be registered here
                pass
            
            # Set fallback chain for this agent type
            task_type = getattr(self, 'task_type', 'general')
            self.fallback_manager.set_fallback_chain(
                task_type, 
                self.config.get("fallback_chain", ["openai", "groq", "gemini"])
            )
            
        except Exception as e:
            log_with_correlation(
                "WARNING",
                f"Failed to register with fallback manager: {e}",
                component="base_agent",
                operation="fallback_registration",
                error=e
            )
    
    def _create_crew_agent(self, role: str, goal: str, backstory: str) -> Agent:
        """Create the CrewAI agent instance"""
        try:
            return Agent(
                role=role,
                goal=goal,
                backstory=backstory,
                llm=self.llm,
                verbose=self.config.get("verbose", True),
                allow_delegation=self.config.get("allow_delegation", False),
                max_iter=self.config.get("max_iterations", 5),
                memory=True
            )
        except Exception as e:
            logger.error(f"Failed to create CrewAI agent for {self.agent_name}: {e}")
            raise WorkflowExecutionError(
                f"Failed to create CrewAI agent for {self.agent_name}: {e}",
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.HIGH
            )
    
    @abstractmethod
    async def execute_task(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main task.
        
        Args:
            task_input: Input data for the task
            
        Returns:
            Dict[str, Any]: Task execution results
        """
        pass
    
    async def execute_with_caching_and_timeout(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent task with caching and timeout handling.
        
        Args:
            task_input: Input data for the task
            
        Returns:
            Dict[str, Any]: Task execution results with caching metadata
        """
        if not self.agent_type:
            # Fallback to regular execution if agent type not set
            return await self.execute_with_monitoring(task_input)
        
        start_time = time.time()
        
        async with cache_context(self.agent_type) as ctx:
            try:
                # Try to get cached result first
                cached_result = await self.agent_cache_manager.get_cached_result(
                    self.agent_type, task_input
                )
                
                if cached_result is not None:
                    ctx.cache_hit = True
                    cache_metrics_collector.record_cache_operation(True, time.time() - start_time)
                    
                    log_with_correlation(
                        "INFO",
                        f"Using cached result for agent {self.agent_name}",
                        component="base_agent",
                        operation="cached_execution"
                    )
                    
                    return cached_result
                
                # No cache hit, execute with timeout
                retry_count = task_input.get("retry_count", 0)
                
                result = await self.agent_cache_manager.execute_with_timeout(
                    agent_type=self.agent_type,
                    coro=self.execute_with_monitoring(task_input),
                    retry_count=retry_count
                )
                
                execution_time = time.time() - start_time
                cache_metrics_collector.record_cache_operation(False, execution_time)
                
                # Cache successful results
                if result.get("success", True) and "error" not in result:
                    metadata = {
                        "agent_name": self.agent_name,
                        "execution_timestamp": datetime.utcnow().isoformat(),
                        "workflow_id": task_input.get("workflow_id")
                    }
                    
                    await self.agent_cache_manager.cache_result(
                        agent_type=self.agent_type,
                        task_input=task_input,
                        result=result,
                        execution_time=execution_time,
                        metadata=metadata
                    )
                    
                    # Trigger cache invalidation for dependent agents
                    await cache_invalidation_manager.invalidate_dependent_caches(
                        self.agent_type, result
                    )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                cache_metrics_collector.record_cache_operation(False, execution_time)
                
                log_with_correlation(
                    "ERROR",
                    f"Error in cached execution for agent {self.agent_name}: {e}",
                    component="base_agent",
                    operation="cached_execution",
                    error=e
                )
                
                # Return error result
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "agent_name": self.agent_name,
                    "execution_time": execution_time
                }

    @trace_ai_operation("enhanced_agent_execution", "agent")
    async def execute_with_monitoring(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent task with enhanced monitoring, retry, and fallback handling.
        
        Args:
            task_input: Input data for the task
            
        Returns:
            Dict[str, Any]: Task execution results with comprehensive metadata
        """
        execution_id = str(uuid.uuid4())
        correlation_id = get_correlation_id() or self.correlation_manager.generate_correlation_id()
        
        async with correlation_context(
            correlation_id=correlation_id,
            operation=f"{self.agent_name}_execution",
            agent_id=self.agent_id,
            execution_id=execution_id
        ):
            start_time = datetime.utcnow()
            
            try:
                log_with_correlation(
                    "INFO",
                    f"Starting enhanced execution for agent {self.agent_name}",
                    component="base_agent",
                    operation="agent_execution"
                )
                
                # Extract workflow ID from task input if available
                self.current_workflow_id = task_input.get("workflow_id")
                
                # Update agent state tracking
                self.progress_metrics.start_execution()
                
                # Update workflow progress if workflow ID is available
                if self.current_workflow_id:
                    self.workflow_progress_manager.start_agent(self.current_workflow_id, self.agent_name)
                
                # Update state
                self.state["execution_count"] += 1
                self.state["last_execution"] = {
                    "execution_id": execution_id,
                    "correlation_id": correlation_id,
                    "start_time": start_time,
                    "status": "running"
                }
                
                # Execute with retry and fallback
                result = await self._execute_with_retry_and_fallback(task_input, execution_id)
                
                # Calculate execution time
                end_time = datetime.utcnow()
                execution_time = (end_time - start_time).total_seconds()
                
                # Update agent state tracking with success
                self.progress_metrics.complete_execution()
                
                # Update workflow progress if workflow ID is available
                if self.current_workflow_id:
                    self.workflow_progress_manager.complete_agent(self.current_workflow_id, self.agent_name)
                
                # Update state with success
                self.state["successful_executions"] += 1
                self.state["last_execution"].update({
                    "end_time": end_time,
                    "execution_time": execution_time,
                    "status": "completed",
                    "result_keys": list(result.keys()) if isinstance(result, dict) else []
                })
                
                # Store results in shared memory
                self.store_results(result)
                
                # Add comprehensive execution metadata
                result["_metadata"] = {
                    "agent_id": self.agent_id,
                    "agent_name": self.agent_name,
                    "execution_id": execution_id,
                    "correlation_id": correlation_id,
                    "execution_time": execution_time,
                    "timestamp": end_time,
                    "retry_attempts": result.get("_retry_attempts", 0),
                    "fallback_used": result.get("_fallback_used", False),
                    "provider_used": result.get("_provider_used", "openai"),
                    "circuit_breaker_state": self._get_circuit_breaker_state(),
                }
                
                log_with_correlation(
                    "INFO",
                    f"Successfully completed execution for agent {self.agent_name} in {execution_time:.2f}s",
                    component="base_agent",
                    operation="agent_execution",
                    execution_time=execution_time
                )
                
                return result
                
            except Exception as e:
                # Handle execution errors with enhanced logging
                end_time = datetime.utcnow()
                execution_time = (end_time - start_time).total_seconds()
                
                # Update agent state tracking with failure
                self.progress_metrics.fail_execution(str(e))
                
                # Update workflow progress if workflow ID is available
                if self.current_workflow_id:
                    self.workflow_progress_manager.fail_agent(self.current_workflow_id, self.agent_name, str(e))
                
                # Update state with error
                self.state["failed_executions"] += 1
                self.state["errors"].append({
                    "execution_id": execution_id,
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "timestamp": end_time
                })
                
                self.state["last_execution"].update({
                    "end_time": end_time,
                    "execution_time": execution_time,
                    "status": "failed",
                    "error": str(e)
                })
                
                log_with_correlation(
                    "ERROR",
                    f"Agent {self.agent_name} execution failed after {execution_time:.2f}s",
                    component="base_agent",
                    operation="agent_execution",
                    error=e,
                    execution_time=execution_time
                )
                
                # Try to return partial results if available
                partial_result = self._get_partial_results(e, task_input)
                
                # Create comprehensive error result
                error_result = {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "agent_id": self.agent_id,
                    "agent_name": self.agent_name,
                    "partial_results": partial_result,
                    "_metadata": {
                        "agent_id": self.agent_id,
                        "agent_name": self.agent_name,
                        "execution_id": execution_id,
                        "correlation_id": correlation_id,
                        "execution_time": execution_time,
                        "timestamp": end_time,
                        "error": True,
                        "has_partial_results": partial_result is not None,
                        "circuit_breaker_state": self._get_circuit_breaker_state(),
                    }
                }
                
                return error_result
    
    async def _execute_with_retry_and_fallback(
        self, 
        task_input: Dict[str, Any], 
        execution_id: str
    ) -> Dict[str, Any]:
        """Execute task with retry logic and fallback provider switching."""
        
        # Execute with retry handler
        retry_result = await self.retry_handler.execute_with_retry(
            self._execute_with_fallback,
            task_input,
            execution_id,
            retry_config=self.retry_config,
            circuit_breaker_name=f"{self.agent_name}_circuit_breaker",
            circuit_breaker_config=self.circuit_breaker_config,
            correlation_id=get_correlation_id()
        )
        
        # Update retry statistics
        self.state["retry_statistics"]["total_retries"] += len(retry_result.attempts) - 1
        if retry_result.success:
            self.state["retry_statistics"]["successful_retries"] += len(retry_result.attempts) - 1
        else:
            self.state["retry_statistics"]["failed_retries"] += len(retry_result.attempts) - 1
        
        if retry_result.success:
            # Add retry metadata to result
            result = retry_result.result
            result["_retry_attempts"] = len(retry_result.attempts)
            result["_total_retry_time"] = retry_result.total_time
            return result
        else:
            # All retries failed
            raise retry_result.final_exception
    
    async def _execute_with_fallback(
        self, 
        task_input: Dict[str, Any], 
        execution_id: str
    ) -> Dict[str, Any]:
        """Execute task with fallback provider logic."""
        
        try:
            # Try to execute with fallback manager
            task_type = getattr(self, 'task_type', 'general')
            
            result, provider_used, execution_metadata = await self.fallback_manager.execute_with_fallback(
                task_type=task_type,
                func_name="execute_task",
                task_input=task_input,
                required_capabilities=getattr(self, 'required_capabilities', None),
                preferred_provider=self.config.get('preferred_provider')
            )
            
            # Update fallback statistics
            self.state["fallback_statistics"]["fallback_used"] += 1
            provider_stats = self.state["fallback_statistics"]["providers_used"]
            provider_stats[provider_used] = provider_stats.get(provider_used, 0) + 1
            
            # Add fallback metadata to result
            if isinstance(result, dict):
                result["_fallback_used"] = len(execution_metadata.get("attempts", [])) > 1
                result["_provider_used"] = provider_used
                result["_execution_metadata"] = execution_metadata
            
            return result
            
        except Exception as e:
            # Fallback failed, try direct execution
            log_with_correlation(
                "WARNING",
                f"Fallback execution failed for {self.agent_name}, trying direct execution",
                component="base_agent",
                operation="fallback_execution",
                error=e
            )
            
            # Direct execution as last resort
            result = await self.execute_task(task_input)
            
            if isinstance(result, dict):
                result["_fallback_used"] = False
                result["_provider_used"] = "direct"
            
            return result
    
    def _get_partial_results(
        self, 
        error: Exception, 
        task_input: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Attempt to return partial results on graceful failure.
        
        Args:
            error: The exception that caused the failure
            task_input: Original task input
            
        Returns:
            Optional partial results that might be useful
        """
        try:
            # Check if we have any cached or intermediate results
            shared_context = self.get_shared_context()
            
            partial_results = {
                "error_occurred": True,
                "error_message": str(error),
                "input_received": bool(task_input),
                "shared_context_available": bool(shared_context),
            }
            
            # Add any available shared context
            if shared_context:
                partial_results["available_context"] = list(shared_context.keys())
            
            # Add agent state information
            partial_results["agent_state"] = {
                "execution_count": self.state.get("execution_count", 0),
                "last_successful_execution": self.state.get("last_successful_execution"),
                "recent_errors": self.state.get("errors", [])[-3:],  # Last 3 errors
            }
            
            return partial_results
            
        except Exception as e:
            log_with_correlation(
                "WARNING",
                f"Failed to generate partial results: {e}",
                component="base_agent",
                operation="partial_results_generation",
                error=e
            )
            return None
    
    def _get_circuit_breaker_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        try:
            circuit_breaker_name = f"{self.agent_name}_circuit_breaker"
            metrics = self.retry_handler.get_circuit_breaker_metrics()
            return metrics.get(circuit_breaker_name, {"state": "unknown"})
        except Exception:
            return {"state": "unknown"}
    
    def store_results(self, results: Dict[str, Any]) -> None:
        """Store agent results in shared memory"""
        try:
            context = {
                "agent_name": self.agent_name,
                "execution_time": datetime.utcnow(),
                "result_type": type(results).__name__
            }
            
            self.communication_protocol.store_memory(
                agent_id=self.agent_id,
                data=results,
                context=context
            )
            
        except Exception as e:
            logger.warning(f"Failed to store results for agent {self.agent_name}: {e}")
    
    def get_shared_context(self) -> Dict[str, Any]:
        """Get shared context from all agents"""
        try:
            all_memories = self.communication_protocol.get_all_memories()
            shared_context = {}
            
            for agent_id, memory in all_memories.items():
                if agent_id != self.agent_id:  # Exclude own memory
                    shared_context[memory.agent_id] = {
                        "data": memory.data,
                        "context": memory.context,
                        "timestamp": memory.timestamp
                    }
            
            return shared_context
            
        except Exception as e:
            logger.warning(f"Failed to get shared context for agent {self.agent_name}: {e}")
            return {}
    
    def send_message_to_agent(self, target_agent_id: str, message: Dict[str, Any]) -> None:
        """Send a message to another agent"""
        try:
            self.communication_protocol.send_message(
                from_agent=self.agent_id,
                to_agent=target_agent_id,
                message=message
            )
        except Exception as e:
            logger.warning(f"Failed to send message from {self.agent_name} to {target_agent_id}: {e}")
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get messages sent to this agent"""
        try:
            return self.communication_protocol.get_messages_for_agent(self.agent_id)
        except Exception as e:
            logger.warning(f"Failed to get messages for agent {self.agent_name}: {e}")
            return []
    
    def clear_processed_messages(self) -> None:
        """Clear processed messages"""
        try:
            self.communication_protocol.clear_messages_for_agent(self.agent_id)
        except Exception as e:
            logger.warning(f"Failed to clear messages for agent {self.agent_name}: {e}")
    
    async def invalidate_cache(self) -> int:
        """Invalidate cache for this agent type."""
        if self.agent_type:
            return await self.agent_cache_manager.invalidate_cache(self.agent_type)
        return 0
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics for this agent type."""
        if self.agent_type:
            stats = self.agent_cache_manager.get_cache_statistics()
            return stats.get("agent_stats", {}).get(self.agent_type.value, {})
        return {}
    
    def get_timeout_config(self) -> Dict[str, Any]:
        """Get timeout configuration for this agent type."""
        if self.agent_type:
            return self.agent_cache_manager.timeout_configs[self.agent_type].__dict__
        return {}
    
    def update_cache_config(self, config_updates: Dict[str, Any]) -> bool:
        """Update cache configuration for this agent type."""
        if self.agent_type:
            return self.agent_cache_manager.update_cache_config(self.agent_type, config_updates)
        return False
    
    def update_timeout_config(self, config_updates: Dict[str, Any]) -> bool:
        """Update timeout configuration for this agent type."""
        if self.agent_type:
            return self.agent_cache_manager.update_timeout_config(self.agent_type, config_updates)
        return False

    def get_agent_state(self) -> Dict[str, Any]:
        """Get comprehensive current agent state with enhanced metrics."""
        base_state = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "state": self.state.copy(),
            "config": self.config.copy(),
            "health_metrics": self._calculate_health_metrics(),
            "circuit_breaker_state": self._get_circuit_breaker_state(),
            "fallback_manager_status": self._get_fallback_manager_status(),
            "correlation_summary": self._get_correlation_summary(),
        }
        
        # Add cache information if agent type is set
        if self.agent_type:
            base_state["cache_statistics"] = self.get_cache_statistics()
            base_state["timeout_config"] = self.get_timeout_config()
        
        return base_state
    
    def _calculate_health_metrics(self) -> Dict[str, Any]:
        """Calculate agent health metrics."""
        total_executions = self.state.get("execution_count", 0)
        successful_executions = self.state.get("successful_executions", 0)
        failed_executions = self.state.get("failed_executions", 0)
        
        success_rate = (successful_executions / max(total_executions, 1)) * 100
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate_percentage": round(success_rate, 2),
            "health_status": self._determine_health_status(success_rate),
            "recent_error_count": len([
                error for error in self.state.get("errors", [])
                if (datetime.utcnow() - datetime.fromisoformat(error.get("timestamp", "1970-01-01"))).total_seconds() < 3600
            ]),
            "retry_statistics": self.state.get("retry_statistics", {}),
            "fallback_statistics": self.state.get("fallback_statistics", {}),
        }
    
    def _determine_health_status(self, success_rate: float) -> str:
        """Determine agent health status based on success rate."""
        if success_rate >= 95:
            return "excellent"
        elif success_rate >= 85:
            return "good"
        elif success_rate >= 70:
            return "fair"
        elif success_rate >= 50:
            return "poor"
        else:
            return "critical"
    
    def _get_fallback_manager_status(self) -> Dict[str, Any]:
        """Get fallback manager status for this agent."""
        try:
            return {
                "provider_health": self.fallback_manager.get_provider_health_status(),
                "fallback_chains": self.fallback_manager.get_fallback_chains(),
                "registered_providers": list(self.fallback_manager.providers.keys()),
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_correlation_summary(self) -> Dict[str, Any]:
        """Get correlation tracking summary."""
        try:
            current_correlation_id = get_correlation_id()
            if current_correlation_id:
                return self.correlation_manager.get_correlation_summary(current_correlation_id)
            return {"status": "no_active_correlation"}
        except Exception as e:
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of the agent."""
        health_check_id = str(uuid.uuid4())
        
        async with correlation_context(
            operation=f"{self.agent_name}_health_check",
            health_check_id=health_check_id
        ):
            start_time = datetime.utcnow()
            
            try:
                log_with_correlation(
                    "INFO",
                    f"Starting health check for agent {self.agent_name}",
                    component="base_agent",
                    operation="health_check"
                )
                
                health_status = {
                    "agent_id": self.agent_id,
                    "agent_name": self.agent_name,
                    "health_check_id": health_check_id,
                    "timestamp": start_time.isoformat(),
                    "status": "healthy",
                    "checks": {}
                }
                
                # Check LLM connectivity
                try:
                    # Simple test to verify LLM is responsive
                    test_messages = [{"role": "user", "content": "Hello"}]
                    if hasattr(self.llm, 'ainvoke'):
                        from langchain.schema import HumanMessage
                        await self.llm.ainvoke([HumanMessage(content="Hello")])
                    health_status["checks"]["llm_connectivity"] = {"status": "pass", "message": "LLM is responsive"}
                except Exception as e:
                    health_status["checks"]["llm_connectivity"] = {"status": "fail", "error": str(e)}
                    health_status["status"] = "degraded"
                
                # Check circuit breaker state
                cb_state = self._get_circuit_breaker_state()
                if cb_state.get("state") == "open":
                    health_status["checks"]["circuit_breaker"] = {"status": "fail", "message": "Circuit breaker is open"}
                    health_status["status"] = "degraded"
                else:
                    health_status["checks"]["circuit_breaker"] = {"status": "pass", "state": cb_state.get("state", "unknown")}
                
                # Check recent error rate
                health_metrics = self._calculate_health_metrics()
                if health_metrics["success_rate_percentage"] < 70:
                    health_status["checks"]["error_rate"] = {
                        "status": "warn", 
                        "success_rate": health_metrics["success_rate_percentage"]
                    }
                    if health_status["status"] == "healthy":
                        health_status["status"] = "degraded"
                else:
                    health_status["checks"]["error_rate"] = {
                        "status": "pass", 
                        "success_rate": health_metrics["success_rate_percentage"]
                    }
                
                # Check fallback provider health
                try:
                    provider_health = self.fallback_manager.get_provider_health_status()
                    healthy_providers = [
                        name for name, status in provider_health.items() 
                        if status.get("status") in ["healthy", "degraded"]
                    ]
                    
                    if len(healthy_providers) == 0:
                        health_status["checks"]["fallback_providers"] = {"status": "fail", "message": "No healthy providers"}
                        health_status["status"] = "unhealthy"
                    elif len(healthy_providers) == 1:
                        health_status["checks"]["fallback_providers"] = {"status": "warn", "healthy_providers": healthy_providers}
                        if health_status["status"] == "healthy":
                            health_status["status"] = "degraded"
                    else:
                        health_status["checks"]["fallback_providers"] = {"status": "pass", "healthy_providers": healthy_providers}
                
                except Exception as e:
                    health_status["checks"]["fallback_providers"] = {"status": "error", "error": str(e)}
                
                # Add performance metrics
                health_status["performance_metrics"] = health_metrics
                
                # Calculate overall health check duration
                end_time = datetime.utcnow()
                health_status["check_duration_seconds"] = (end_time - start_time).total_seconds()
                
                log_with_correlation(
                    "INFO",
                    f"Health check completed for agent {self.agent_name}: {health_status['status']}",
                    component="base_agent",
                    operation="health_check",
                    health_status=health_status["status"]
                )
                
                return health_status
                
            except Exception as e:
                log_with_correlation(
                    "ERROR",
                    f"Health check failed for agent {self.agent_name}",
                    component="base_agent",
                    operation="health_check",
                    error=e
                )
                
                return {
                    "agent_id": self.agent_id,
                    "agent_name": self.agent_name,
                    "health_check_id": health_check_id,
                    "timestamp": start_time.isoformat(),
                    "status": "unhealthy",
                    "error": str(e),
                    "check_duration_seconds": (datetime.utcnow() - start_time).total_seconds()
                }
    
    def validate_input(self, task_input: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """
        Validate task input against required fields.
        
        Args:
            task_input: Input data to validate
            required_fields: List of required field names
            
        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors = []
        
        if not isinstance(task_input, dict):
            errors.append("Task input must be a dictionary")
            return errors
        
        for field in required_fields:
            if field not in task_input:
                errors.append(f"Required field '{field}' is missing")
            elif task_input[field] is None:
                errors.append(f"Required field '{field}' cannot be None")
            elif isinstance(task_input[field], str) and not task_input[field].strip():
                errors.append(f"Required field '{field}' cannot be empty")
        
        return errors
    
    def update_progress(self, percentage: float, operation: str = None):
        """
        Update agent progress percentage and current operation.
        
        Args:
            percentage: Progress percentage (0-100)
            operation: Current operation description
        """
        self.progress_metrics.update_progress(percentage, operation)
        
        # Update workflow progress if workflow ID is available
        if self.current_workflow_id:
            self.workflow_progress_manager.update_agent_progress(
                self.current_workflow_id, 
                self.agent_name, 
                percentage, 
                operation
            )
        
        log_with_correlation(
            "DEBUG",
            f"Agent {self.agent_name} progress updated: {percentage:.1f}% - {operation or 'No operation specified'}",
            component="base_agent",
            operation="progress_update",
            progress_percentage=percentage,
            current_operation=operation
        )
    
    def get_progress_metrics(self) -> AgentProgressMetrics:
        """
        Get current agent progress metrics.
        
        Returns:
            AgentProgressMetrics: Current progress metrics
        """
        return self.progress_metrics
    
    def get_current_state(self) -> AgentState:
        """
        Get current agent execution state.
        
        Returns:
            AgentState: Current agent state
        """
        return self.progress_metrics.state
    
    def set_workflow_id(self, workflow_id: str):
        """
        Set the current workflow ID for progress tracking.
        
        Args:
            workflow_id: Workflow identifier
        """
        self.current_workflow_id = workflow_id
        log_with_correlation(
            "DEBUG",
            f"Agent {self.agent_name} associated with workflow {workflow_id}",
            component="base_agent",
            operation="workflow_association",
            workflow_id=workflow_id
        )
    
    def reset_progress(self):
        """Reset agent progress metrics for a new execution."""
        self.progress_metrics = AgentProgressMetrics(agent_name=self.agent_name)
        log_with_correlation(
            "DEBUG",
            f"Agent {self.agent_name} progress metrics reset",
            component="base_agent",
            operation="progress_reset"
        )
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """
        Get a summary of agent progress for frontend display.
        
        Returns:
            Dict[str, Any]: Progress summary
        """
        return {
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
            "state": self.progress_metrics.state.value,
            "progress_percentage": round(self.progress_metrics.progress_percentage, 2),
            "current_operation": self.progress_metrics.current_operation,
            "start_time": self.progress_metrics.start_time.isoformat() if self.progress_metrics.start_time else None,
            "end_time": self.progress_metrics.end_time.isoformat() if self.progress_metrics.end_time else None,
            "execution_time": self.progress_metrics.execution_time,
            "error_message": self.progress_metrics.error_message,
            "retry_count": self.progress_metrics.retry_count,
            "estimated_completion_time": self.progress_metrics.estimated_completion_time.isoformat() if self.progress_metrics.estimated_completion_time else None,
            "workflow_id": self.current_workflow_id
        }