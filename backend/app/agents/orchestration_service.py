"""
Optimized AI Agent Orchestration Service

This module provides the streamlined orchestration service that manages the execution
of multiple AI agents in a coordinated workflow for job application tracking with enhanced
error handling, health monitoring, and performance optimization.
"""

import asyncio
import logging
import uuid
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Set
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque

from crewai import Crew, Process, Task
from pydantic import BaseModel, Field

from ..core.config import get_settings
from ..core.exceptions import ErrorCategory, ErrorSeverity, WorkflowExecutionError
from ..core.langsmith_integration import trace_ai_operation
from ..monitoring.metrics_collector import get_metrics_collector
from .base_agent import AgentCommunicationProtocol
from ..models.agent_models import (
    AgentState,
    WorkflowState,
    WorkflowProgress,
    get_workflow_progress_manager
)
# Lazy imports to avoid circular dependencies
# from .communication_agent import CommunicationAgent
# from .contract_analyzer_agent import ContractAnalyzerAgent
# from .legal_precedent_agent import LegalPrecedentAgent
# from .negotiation_agent import NegotiationAgent
# from .risk_assessment_agent import RiskAssessmentAgent

logger = logging.getLogger(__name__)
metrics_collector = get_metrics_collector()


class AgentStatus(str, Enum):
    """Agent status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


class WorkflowMode(str, Enum):
    """Workflow execution modes."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"


@dataclass
class AgentHealthMetrics:
    """Health metrics for individual agents."""
    agent_name: str
    status: AgentStatus = AgentStatus.HEALTHY
    last_health_check: Optional[datetime] = None
    success_rate: float = 1.0
    avg_response_time: float = 0.0
    error_count: int = 0
    consecutive_failures: int = 0
    last_error: Optional[str] = None
    recovery_attempts: int = 0
    
    def update_success(self, response_time: float):
        """Update metrics after successful execution."""
        self.consecutive_failures = 0
        self.avg_response_time = (self.avg_response_time + response_time) / 2
        self.last_health_check = datetime.utcnow()
        
        # Update status based on performance
        if response_time > 30.0:  # Slow response
            self.status = AgentStatus.DEGRADED
        else:
            self.status = AgentStatus.HEALTHY
    
    def update_failure(self, error: str):
        """Update metrics after failed execution."""
        self.consecutive_failures += 1
        self.error_count += 1
        self.last_error = error
        self.last_health_check = datetime.utcnow()
        
        # Update status based on failure pattern
        if self.consecutive_failures >= 3:
            self.status = AgentStatus.UNHEALTHY
        elif self.consecutive_failures >= 1:
            self.status = AgentStatus.DEGRADED


@dataclass
class AgentDependency:
    """Represents a dependency between agents."""
    agent_name: str
    depends_on: List[str] = field(default_factory=list)
    can_run_parallel_with: List[str] = field(default_factory=list)
    priority: int = 0  # Higher number = higher priority
    resource_requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceLimits:
    """Resource limits for agent execution."""
    max_concurrent_agents: int = 3
    max_memory_mb: int = 2048
    max_cpu_percent: float = 80.0
    max_tokens_per_minute: int = 10000
    max_cost_per_minute: float = 1.0


@dataclass
class WorkflowOptimization:
    """Workflow optimization settings."""
    enable_parallel_execution: bool = True
    max_concurrent_agents: int = 3
    timeout_per_agent: int = 60
    enable_fallback_agents: bool = True
    enable_result_caching: bool = True
    cache_ttl_minutes: int = 30
    enable_adaptive_routing: bool = True
    health_check_interval: int = 300  # 5 minutes
    enable_dependency_resolution: bool = True
    enable_resource_management: bool = True
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)


class OptimizedWorkflowConfig(BaseModel):
    """Optimized configuration for agent workflow execution"""
    
    max_execution_time: int = Field(default=180, description="Maximum execution time in seconds")
    execution_mode: WorkflowMode = Field(default=WorkflowMode.ADAPTIVE, description="Workflow execution mode")
    retry_failed_tasks: bool = Field(default=True, description="Retry failed tasks")
    max_retries: int = Field(default=2, description="Maximum number of retries")
    enable_health_monitoring: bool = Field(default=True, description="Enable agent health monitoring")
    enable_performance_optimization: bool = Field(default=True, description="Enable performance optimizations")
    fallback_timeout: int = Field(default=30, description="Fallback timeout in seconds")
    circuit_breaker_threshold: int = Field(default=3, description="Circuit breaker failure threshold")


class DependencyResolver:
    """Resolves agent dependencies and determines execution order."""
    
    def __init__(self, dependencies: Dict[str, AgentDependency]):
        self.dependencies = dependencies
        self.execution_graph = self._build_execution_graph()
    
    def _build_execution_graph(self) -> Dict[str, Set[str]]:
        """Build a directed graph of agent dependencies."""
        graph = defaultdict(set)
        
        for agent_name, dependency in self.dependencies.items():
            for dep in dependency.depends_on:
                graph[dep].add(agent_name)
        
        return dict(graph)
    
    def get_execution_order(self) -> List[List[str]]:
        """Get agents grouped by execution stages (topological sort)."""
        # Kahn's algorithm for topological sorting
        in_degree = defaultdict(int)
        
        # Calculate in-degrees
        for agent_name in self.dependencies:
            in_degree[agent_name] = len(self.dependencies[agent_name].depends_on)
        
        # Find agents with no dependencies (can start immediately)
        queue = deque([agent for agent, degree in in_degree.items() if degree == 0])
        execution_stages = []
        
        while queue:
            # Current stage - agents that can run in parallel
            current_stage = []
            stage_size = len(queue)
            
            for _ in range(stage_size):
                agent = queue.popleft()
                current_stage.append(agent)
                
                # Reduce in-degree for dependent agents
                for dependent in self.execution_graph.get(agent, []):
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
            
            if current_stage:
                # Sort by priority within the stage
                current_stage.sort(key=lambda x: self.dependencies[x].priority, reverse=True)
                execution_stages.append(current_stage)
        
        return execution_stages
    
    def can_run_parallel(self, agent1: str, agent2: str) -> bool:
        """Check if two agents can run in parallel."""
        dep1 = self.dependencies.get(agent1)
        dep2 = self.dependencies.get(agent2)
        
        if not dep1 or not dep2:
            return False
        
        # Check if they're explicitly marked as parallel-compatible
        if agent2 in dep1.can_run_parallel_with or agent1 in dep2.can_run_parallel_with:
            return True
        
        # Check if neither depends on the other
        return (agent2 not in dep1.depends_on and 
                agent1 not in dep2.depends_on and
                agent1 != agent2)
    
    def get_parallel_groups(self, stage_agents: List[str], max_parallel: int) -> List[List[str]]:
        """Group agents in a stage into parallel execution groups."""
        if len(stage_agents) <= max_parallel:
            return [stage_agents]
        
        groups = []
        remaining = stage_agents.copy()
        
        while remaining:
            current_group = [remaining.pop(0)]
            
            # Add compatible agents to current group
            i = 0
            while i < len(remaining) and len(current_group) < max_parallel:
                agent = remaining[i]
                
                # Check if agent can run parallel with all agents in current group
                can_add = all(self.can_run_parallel(agent, group_agent) 
                             for group_agent in current_group)
                
                if can_add:
                    current_group.append(remaining.pop(i))
                else:
                    i += 1
            
            groups.append(current_group)
        
        return groups


class ResourceManager:
    """Manages resource allocation and limits for agent execution."""
    
    def __init__(self, limits: ResourceLimits):
        self.limits = limits
        self.current_usage = {
            "concurrent_agents": 0,
            "memory_mb": 0,
            "cpu_percent": 0.0,
            "tokens_per_minute": 0,
            "cost_per_minute": 0.0
        }
        self.agent_resources = {}
        self.usage_history = []
    
    def can_allocate_resources(self, agent_name: str, requirements: Dict[str, Any]) -> bool:
        """Check if resources can be allocated for an agent."""
        # Check concurrent agent limit
        if self.current_usage["concurrent_agents"] >= self.limits.max_concurrent_agents:
            return False
        
        # Check memory limit
        required_memory = requirements.get("memory_mb", 256)  # Default 256MB
        if self.current_usage["memory_mb"] + required_memory > self.limits.max_memory_mb:
            return False
        
        # Check CPU limit
        required_cpu = requirements.get("cpu_percent", 10.0)  # Default 10%
        if self.current_usage["cpu_percent"] + required_cpu > self.limits.max_cpu_percent:
            return False
        
        # Check token rate limit
        required_tokens = requirements.get("tokens_per_minute", 1000)  # Default 1000
        if self.current_usage["tokens_per_minute"] + required_tokens > self.limits.max_tokens_per_minute:
            return False
        
        # Check cost limit
        required_cost = requirements.get("cost_per_minute", 0.1)  # Default $0.10
        if self.current_usage["cost_per_minute"] + required_cost > self.limits.max_cost_per_minute:
            return False
        
        return True
    
    def allocate_resources(self, agent_name: str, requirements: Dict[str, Any]) -> bool:
        """Allocate resources for an agent."""
        if not self.can_allocate_resources(agent_name, requirements):
            return False
        
        # Allocate resources
        self.current_usage["concurrent_agents"] += 1
        self.current_usage["memory_mb"] += requirements.get("memory_mb", 256)
        self.current_usage["cpu_percent"] += requirements.get("cpu_percent", 10.0)
        self.current_usage["tokens_per_minute"] += requirements.get("tokens_per_minute", 1000)
        self.current_usage["cost_per_minute"] += requirements.get("cost_per_minute", 0.1)
        
        # Track agent resources
        self.agent_resources[agent_name] = {
            "allocated_at": datetime.utcnow(),
            "requirements": requirements.copy()
        }
        
        return True
    
    def release_resources(self, agent_name: str):
        """Release resources allocated to an agent."""
        if agent_name not in self.agent_resources:
            return
        
        requirements = self.agent_resources[agent_name]["requirements"]
        
        # Release resources
        self.current_usage["concurrent_agents"] = max(0, self.current_usage["concurrent_agents"] - 1)
        self.current_usage["memory_mb"] = max(0, self.current_usage["memory_mb"] - requirements.get("memory_mb", 256))
        self.current_usage["cpu_percent"] = max(0.0, self.current_usage["cpu_percent"] - requirements.get("cpu_percent", 10.0))
        self.current_usage["tokens_per_minute"] = max(0, self.current_usage["tokens_per_minute"] - requirements.get("tokens_per_minute", 1000))
        self.current_usage["cost_per_minute"] = max(0.0, self.current_usage["cost_per_minute"] - requirements.get("cost_per_minute", 0.1))
        
        # Record usage history
        allocation_time = self.agent_resources[agent_name]["allocated_at"]
        execution_time = (datetime.utcnow() - allocation_time).total_seconds()
        
        self.usage_history.append({
            "agent_name": agent_name,
            "execution_time": execution_time,
            "resources_used": requirements.copy(),
            "completed_at": datetime.utcnow()
        })
        
        # Remove from active tracking
        del self.agent_resources[agent_name]
    
    def get_resource_utilization(self) -> Dict[str, float]:
        """Get current resource utilization as percentages."""
        return {
            "concurrent_agents": (self.current_usage["concurrent_agents"] / self.limits.max_concurrent_agents) * 100,
            "memory": (self.current_usage["memory_mb"] / self.limits.max_memory_mb) * 100,
            "cpu": (self.current_usage["cpu_percent"] / self.limits.max_cpu_percent) * 100,
            "tokens": (self.current_usage["tokens_per_minute"] / self.limits.max_tokens_per_minute) * 100,
            "cost": (self.current_usage["cost_per_minute"] / self.limits.max_cost_per_minute) * 100
        }
    
    def cleanup_expired_allocations(self, max_age_minutes: int = 60):
        """Clean up resource allocations that have been active too long."""
        current_time = datetime.utcnow()
        expired_agents = []
        
        for agent_name, allocation in self.agent_resources.items():
            age_minutes = (current_time - allocation["allocated_at"]).total_seconds() / 60
            if age_minutes > max_age_minutes:
                expired_agents.append(agent_name)
        
        for agent_name in expired_agents:
            logger.warning(f"Releasing expired resource allocation for agent {agent_name}")
            self.release_resources(agent_name)
        
        return len(expired_agents)


class OptimizedWorkflowStatus(BaseModel):
    """Enhanced status tracking for workflow execution"""
    
    workflow_id: str
    status: str  # "initialized", "running", "completed", "failed", "degraded"
    execution_mode: WorkflowMode
    start_time: datetime
    end_time: Optional[datetime] = None
    current_stage: str = "initialization"
    completed_agents: List[str] = Field(default_factory=list)
    failed_agents: List[str] = Field(default_factory=list)
    degraded_agents: List[str] = Field(default_factory=list)
    running_agents: List[str] = Field(default_factory=list)
    pending_agents: List[str] = Field(default_factory=list)
    total_execution_time: Optional[float] = None
    error_message: Optional[str] = None
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    recovery_actions: List[str] = Field(default_factory=list)
    execution_stages: List[List[str]] = Field(default_factory=list)
    current_stage_index: int = 0
    parallel_groups: List[List[str]] = Field(default_factory=list)
    resource_utilization: Dict[str, float] = Field(default_factory=dict)


class OptimizedAgentOrchestrationService:
    """
    Optimized service for orchestrating multiple AI agents in a job application tracking workflow.
    
    Enhanced features:
    - Streamlined agent initialization and management
    - Advanced health monitoring and recovery
    - Performance optimization and adaptive routing
    - Robust error handling with circuit breakers
    - Intelligent fallback mechanisms
    - Real-time performance metrics
    """
    
    def __init__(self, config: Optional[OptimizedWorkflowConfig] = None):
        """
        Initialize the optimized orchestration service.
        
        Args:
            config: Optional workflow configuration
        """
        self.config = config or OptimizedWorkflowConfig()
        self.settings = get_settings()
        self.optimization = WorkflowOptimization()
        
        # Initialize communication protocol
        self.communication_protocol = AgentCommunicationProtocol()
        
        # Initialize agent management
        self.agents = {}
        self.agent_health = {}
        self.workflow_status = {}
        self.result_cache = {}
        
        # Initialize dependency resolution and resource management
        self.agent_dependencies = self._initialize_agent_dependencies()
        self.dependency_resolver = DependencyResolver(self.agent_dependencies)
        self.resource_manager = ResourceManager(self.optimization.resource_limits)
        
        # Performance tracking
        self.performance_stats = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "avg_execution_time": 0.0,
            "agent_utilization": {},
            "parallel_execution_stats": {
                "total_parallel_stages": 0,
                "avg_parallel_agents": 0.0,
                "resource_wait_time": 0.0
            }
        }
        
        # Circuit breaker states
        self.circuit_breakers = {}
        
        # Initialize agents with health monitoring
        self._initialize_optimized_agents()
        
        # Start health monitoring if enabled (defer to avoid event loop issues)
        self._health_monitoring_enabled = self.config.enable_health_monitoring
        
        logger.info("Optimized agent orchestration service initialized with enhanced monitoring, dependency resolution, and resource management")
    
    async def _broadcast_progress_update(self, workflow_id: str):
        """Broadcast progress update to connected clients."""
        try:
            # Import here to avoid circular imports
            from ..api.v1.analysis_status import broadcast_analysis_update
            
            workflow_manager = get_workflow_progress_manager()
            workflow = workflow_manager.get_workflow(workflow_id)
            
            if workflow:
                progress_data = workflow.get_progress_summary()
                await broadcast_analysis_update(workflow_id, progress_data)
        except Exception as e:
            logger.warning(f"Failed to broadcast progress update for {workflow_id}: {e}")
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a workflow and notify connected clients."""
        try:
            workflow_manager = get_workflow_progress_manager()
            success = workflow_manager.cancel_workflow(workflow_id)
            
            if success:
                # Broadcast cancellation
                await self._broadcast_progress_update(workflow_id)
                logger.info(f"Workflow {workflow_id} cancelled successfully")
            
            return success
        except Exception as e:
            logger.error(f"Error cancelling workflow {workflow_id}: {e}")
            return False
    
    async def update_agent_progress(self, workflow_id: str, agent_name: str, percentage: float, operation: str = None):
        """Update agent progress and broadcast to connected clients."""
        try:
            workflow_manager = get_workflow_progress_manager()
            success = workflow_manager.update_agent_progress(workflow_id, agent_name, percentage, operation)
            
            if success:
                await self._broadcast_progress_update(workflow_id)
            
            return success
        except Exception as e:
            logger.error(f"Error updating agent progress for {workflow_id}/{agent_name}: {e}")
            return False
    
    def _initialize_agent_dependencies(self) -> Dict[str, AgentDependency]:
        """Initialize agent dependencies and execution requirements."""
        return {
            "analyzer": AgentDependency(
                agent_name="analyzer",
                depends_on=[],  # No dependencies - can start immediately
                can_run_parallel_with=[],  # Analyzer should run first
                priority=10,  # Highest priority
                resource_requirements={
                    "memory_mb": 512,
                    "cpu_percent": 20.0,
                    "tokens_per_minute": 2000,
                    "cost_per_minute": 0.2
                }
            ),
            "risk_assessor": AgentDependency(
                agent_name="risk_assessor",
                depends_on=["analyzer"],  # Needs analysis results
                can_run_parallel_with=["precedent_researcher"],  # Can run with precedent research
                priority=8,
                resource_requirements={
                    "memory_mb": 384,
                    "cpu_percent": 15.0,
                    "tokens_per_minute": 1500,
                    "cost_per_minute": 0.15
                }
            ),
            "precedent_researcher": AgentDependency(
                agent_name="precedent_researcher",
                depends_on=["analyzer"],  # Needs analysis results
                can_run_parallel_with=["risk_assessor"],  # Can run with risk assessment
                priority=7,
                resource_requirements={
                    "memory_mb": 640,  # Higher memory for vector search
                    "cpu_percent": 25.0,
                    "tokens_per_minute": 1800,
                    "cost_per_minute": 0.18
                }
            ),
            "negotiator": AgentDependency(
                agent_name="negotiator",
                depends_on=["risk_assessor", "precedent_researcher"],  # Needs both risk and precedent results
                can_run_parallel_with=[],  # Should run after risk and precedent analysis
                priority=6,
                resource_requirements={
                    "memory_mb": 448,
                    "cpu_percent": 18.0,
                    "tokens_per_minute": 1600,
                    "cost_per_minute": 0.16
                }
            ),
            "communicator": AgentDependency(
                agent_name="communicator",
                depends_on=["negotiator"],  # Needs negotiation results
                can_run_parallel_with=[],  # Should run last
                priority=5,
                resource_requirements={
                    "memory_mb": 320,
                    "cpu_percent": 12.0,
                    "tokens_per_minute": 1200,
                    "cost_per_minute": 0.12
                }
            )
        }
    
    def _initialize_optimized_agents(self) -> None:
        """Initialize all specialized agents with health monitoring"""
        try:
            agent_config = self.config.dict()
            agent_config.update({
                "enable_monitoring": True,
                "timeout": self.optimization.timeout_per_agent,
                "enable_caching": self.optimization.enable_result_caching
            })
            
            # Lazy import agents to avoid circular dependencies
            from .contract_analyzer_agent import ContractAnalyzerAgent
            from .risk_assessment_agent import RiskAssessmentAgent
            from .legal_precedent_agent import LegalPrecedentAgent
            from .negotiation_agent import NegotiationAgent
            from .communication_agent import CommunicationAgent
            
            # Initialize agents with error handling
            agents_to_initialize = [
                ("analyzer", ContractAnalyzerAgent, "Contract Analysis Agent"),
                ("risk_assessor", RiskAssessmentAgent, "Risk Assessment Agent"),
                ("precedent_researcher", LegalPrecedentAgent, "Legal Precedent Agent"),
                ("negotiator", NegotiationAgent, "Negotiation Agent"),
                ("communicator", CommunicationAgent, "Communication Agent")
            ]
            
            for agent_key, agent_class, agent_description in agents_to_initialize:
                try:
                    # Initialize agent
                    self.agents[agent_key] = agent_class(
                        communication_protocol=self.communication_protocol,
                        config=agent_config
                    )
                    
                    # Initialize health metrics
                    self.agent_health[agent_key] = AgentHealthMetrics(agent_name=agent_key)
                    
                    # Initialize circuit breaker
                    self.circuit_breakers[agent_key] = {
                        "failure_count": 0,
                        "last_failure": None,
                        "state": "closed"  # closed, open, half-open
                    }
                    
                    logger.info(f"Initialized {agent_description} ({agent_key})")
                    
                except Exception as e:
                    logger.error(f"Failed to initialize {agent_description}: {e}")
                    # Mark agent as unhealthy but continue with others
                    self.agent_health[agent_key] = AgentHealthMetrics(
                        agent_name=agent_key,
                        status=AgentStatus.OFFLINE,
                        last_error=str(e)
                    )
            
            healthy_agents = len([h for h in self.agent_health.values() if h.status != AgentStatus.OFFLINE])
            logger.info(f"Initialized {healthy_agents}/{len(agents_to_initialize)} agents successfully")
            
            if healthy_agents == 0:
                raise WorkflowExecutionError(
                    "No agents could be initialized",
                    category=ErrorCategory.CONFIGURATION,
                    severity=ErrorSeverity.CRITICAL
                )
            
        except Exception as e:
            logger.error(f"Critical failure in agent initialization: {e}")
            raise WorkflowExecutionError(
                f"Failed to initialize agent orchestration: {e}",
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.CRITICAL
            )
    
    async def start_health_monitoring_if_enabled(self):
        """Start health monitoring if enabled and event loop is available"""
        if hasattr(self, '_health_monitoring_enabled') and self._health_monitoring_enabled:
            try:
                asyncio.create_task(self._start_health_monitoring())
                logger.info("Agent health monitoring started")
            except Exception as e:
                logger.warning(f"Failed to start health monitoring: {e}")
    
    async def _start_health_monitoring(self):
        """Start continuous health monitoring for all agents"""
        logger.info("Starting agent health monitoring")
        
        while True:
            try:
                await asyncio.sleep(self.optimization.health_check_interval)
                await self._perform_health_checks()
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _perform_health_checks(self):
        """Perform health checks on all agents"""
        logger.debug("Performing agent health checks")
        
        for agent_key, agent in self.agents.items():
            try:
                start_time = time.time()
                
                # Simple health check - try to get agent state
                if hasattr(agent, 'get_agent_state'):
                    state = agent.get_agent_state()
                    response_time = time.time() - start_time
                    
                    # Update health metrics
                    health = self.agent_health[agent_key]
                    health.update_success(response_time)
                    
                    # Reset circuit breaker on successful health check
                    if self.circuit_breakers[agent_key]["state"] == "half-open":
                        self.circuit_breakers[agent_key]["state"] = "closed"
                        self.circuit_breakers[agent_key]["failure_count"] = 0
                        logger.info(f"Agent {agent_key} recovered - circuit breaker closed")
                
            except Exception as e:
                # Update health metrics for failure
                health = self.agent_health[agent_key]
                health.update_failure(str(e))
                
                # Update circuit breaker
                self._update_circuit_breaker(agent_key, str(e))
                
                logger.warning(f"Health check failed for agent {agent_key}: {e}")
        
        # Log overall health status
        healthy_count = len([h for h in self.agent_health.values() if h.status == AgentStatus.HEALTHY])
        total_count = len(self.agent_health)
        logger.debug(f"Agent health status: {healthy_count}/{total_count} healthy")
    
    def _update_circuit_breaker(self, agent_key: str, error: str):
        """Update circuit breaker state for an agent"""
        breaker = self.circuit_breakers[agent_key]
        breaker["failure_count"] += 1
        breaker["last_failure"] = datetime.utcnow()
        
        if breaker["failure_count"] >= self.config.circuit_breaker_threshold:
            if breaker["state"] == "closed":
                breaker["state"] = "open"
                logger.warning(f"Circuit breaker opened for agent {agent_key} after {breaker['failure_count']} failures")
        
        # Auto-recovery attempt after timeout
        if breaker["state"] == "open":
            time_since_failure = datetime.utcnow() - breaker["last_failure"]
            if time_since_failure > timedelta(seconds=self.config.fallback_timeout):
                breaker["state"] = "half-open"
                logger.info(f"Circuit breaker for agent {agent_key} moved to half-open state")
    
    def _is_agent_available(self, agent_key: str) -> bool:
        """Check if an agent is available for execution"""
        if agent_key not in self.agents:
            return False
        
        health = self.agent_health.get(agent_key)
        if not health or health.status == AgentStatus.OFFLINE:
            return False
        
        breaker = self.circuit_breakers.get(agent_key, {})
        if breaker.get("state") == "open":
            return False
        
        return True
    
    @trace_ai_operation("optimized_workflow_execution", "orchestration")
    async def execute_optimized_contract_analysis_workflow(
        self,
        contract_text: str,
        contract_filename: str,
        workflow_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the optimized job application tracking workflow with enhanced error handling and performance monitoring.
        
        Args:
            contract_text: The contract text to analyze
            contract_filename: Name of the contract file
            workflow_config: Optional workflow-specific configuration
            
        Returns:
            Dict[str, Any]: Complete workflow results with performance metrics
        """
        workflow_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        # Update performance stats
        self.performance_stats["total_workflows"] += 1
        
        # Create workflow progress tracking
        workflow_progress_manager = get_workflow_progress_manager()
        agent_names = ["analyzer", "risk_assessor", "precedent_researcher", "negotiator", "communicator"]
        workflow_progress = workflow_progress_manager.create_workflow(
            workflow_id=workflow_id,
            agent_names=agent_names,
            contract_id=workflow_config.get("contract_id") if workflow_config else None
        )
        
        # Check cache first if enabled
        cache_key = None
        if self.optimization.enable_result_caching:
            cache_key = self._generate_cache_key(contract_text, workflow_config)
            cached_result = self.result_cache.get(cache_key)
            if cached_result and self._is_cache_valid(cached_result):
                logger.info(f"Returning cached result for workflow {workflow_id}")
                return cached_result["result"]
        
        # Initialize optimized workflow status
        status = OptimizedWorkflowStatus(
            workflow_id=workflow_id,
            status="initialized",
            execution_mode=self.config.execution_mode,
            start_time=start_time
        )
        self.workflow_status[workflow_id] = status
        
        # Initialize workflow progress tracking
        agent_names = ["analyzer", "risk_assessor", "precedent_researcher", "negotiator", "communicator"]
        workflow_progress_manager = get_workflow_progress_manager()
        workflow_progress = workflow_progress_manager.create_workflow(
            workflow_id=workflow_id,
            agent_names=agent_names,
            contract_id=None  # Could be set if we have a contract ID
        )
        workflow_progress.current_stage = "initialization"
        
        # Set workflow ID for all agents
        for agent_key, agent in self.agents.items():
            if hasattr(agent, 'set_workflow_id'):
                agent.set_workflow_id(workflow_id)
        
        try:
            logger.info(f"Starting optimized workflow {workflow_id} for {contract_filename} in {self.config.execution_mode.value} mode")
            
            # Record workflow start metrics
            metrics_collector.increment_active_analyses()
            
            # Update status
            status.status = "running"
            
            # Execute workflow based on mode
            if self.config.execution_mode == WorkflowMode.PARALLEL:
                final_results = await self._execute_parallel_workflow(
                    contract_text, contract_filename, workflow_id, status
                )
            elif self.config.execution_mode == WorkflowMode.ADAPTIVE:
                final_results = await self._execute_adaptive_workflow(
                    contract_text, contract_filename, workflow_id, status
                )
            else:  # Sequential mode
                final_results = await self._execute_sequential_workflow(
                    contract_text, contract_filename, workflow_id, status
                )
            
            # Update final status
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            status.status = "completed"
            status.end_time = end_time
            status.total_execution_time = execution_time
            status.current_stage = "completed"
            
            # Update workflow progress to completed
            workflow_progress.current_stage = "completed"
            workflow_progress.workflow_state = WorkflowState.COMPLETED
            workflow_progress.end_time = end_time
            workflow_progress.total_execution_time = execution_time
            
            # Update performance metrics
            self.performance_stats["successful_workflows"] += 1
            self.performance_stats["avg_execution_time"] = (
                (self.performance_stats["avg_execution_time"] * (self.performance_stats["successful_workflows"] - 1) + 
                 execution_time) / self.performance_stats["successful_workflows"]
            )
            
            # Cache result if enabled
            if self.optimization.enable_result_caching and cache_key:
                self.result_cache[cache_key] = {
                    "result": final_results,
                    "timestamp": datetime.utcnow(),
                    "ttl_minutes": self.optimization.cache_ttl_minutes
                }
            
            # Record success metrics
            metrics_collector.record_contract_analysis(
                status="completed",
                model_used="multi_agent_workflow",
                duration=execution_time,
                risk_score=final_results.get("overall_risk_score", 0.0),
                contract_type=final_results.get("contract_structure", {}).get("contract_type", "unknown")
            )
            
            logger.info(f"Optimized workflow {workflow_id} completed successfully in {execution_time:.2f}s")
            
            return final_results
            
        except Exception as e:
            # Handle workflow failure with enhanced error recovery
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            error_msg = f"Optimized workflow {workflow_id} failed: {e}"
            
            status.status = "failed"
            status.end_time = end_time
            status.total_execution_time = execution_time
            status.error_message = str(e)
            
            # Update workflow progress to failed
            workflow_progress.workflow_state = WorkflowState.FAILED
            workflow_progress.end_time = end_time
            workflow_progress.total_execution_time = execution_time
            workflow_progress.error_message = str(e)
            
            # Update failure stats
            self.performance_stats["failed_workflows"] += 1
            
            # Record failure metrics
            metrics_collector.record_contract_analysis(
                status="failed",
                model_used="multi_agent_workflow",
                duration=execution_time,
                contract_type="unknown"
            )
            
            logger.error(error_msg, exc_info=True)
            
            # Attempt graceful degradation
            degraded_result = await self._attempt_graceful_degradation(
                contract_text, contract_filename, workflow_id, status
            )
            
            if degraded_result:
                logger.info(f"Workflow {workflow_id} completed with degraded functionality")
                return degraded_result
            
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": error_msg,
                "execution_time": execution_time,
                "completed_agents": status.completed_agents,
                "failed_agents": status.failed_agents,
                "degraded_agents": status.degraded_agents,
                "recovery_attempted": True
            }
        
        finally:
            # Always decrement active analyses
            metrics_collector.decrement_active_analyses()
    
    async def _execute_parallel_workflow(
        self, contract_text: str, contract_filename: str, workflow_id: str, status: OptimizedWorkflowStatus
    ) -> Dict[str, Any]:
        """Execute workflow with enhanced parallel agent execution using dependency resolution"""
        logger.info(f"Executing enhanced parallel workflow for {workflow_id}")
        
        if not self.optimization.enable_dependency_resolution:
            # Fall back to legacy parallel execution
            return await self._execute_legacy_parallel_workflow(contract_text, contract_filename, workflow_id, status)
        
        # Get execution stages from dependency resolver
        execution_stages = self.dependency_resolver.get_execution_order()
        status.execution_stages = execution_stages
        
        logger.info(f"Workflow {workflow_id} execution plan: {len(execution_stages)} stages")
        for i, stage in enumerate(execution_stages):
            logger.info(f"  Stage {i+1}: {stage}")
        
        # Execute stages sequentially, with parallel execution within each stage
        stage_results = {}
        
        for stage_index, stage_agents in enumerate(execution_stages):
            status.current_stage_index = stage_index
            status.current_stage = f"stage_{stage_index + 1}"
            
            logger.info(f"Executing stage {stage_index + 1}/{len(execution_stages)}: {stage_agents}")
            
            # Get parallel groups for this stage based on resource limits
            if self.optimization.enable_resource_management:
                parallel_groups = self.dependency_resolver.get_parallel_groups(
                    stage_agents, 
                    self.optimization.max_concurrent_agents
                )
            else:
                # Simple grouping by max concurrent limit
                parallel_groups = [stage_agents[i:i + self.optimization.max_concurrent_agents] 
                                 for i in range(0, len(stage_agents), self.optimization.max_concurrent_agents)]
            
            status.parallel_groups = parallel_groups
            
            # Execute each parallel group
            for group_index, agent_group in enumerate(parallel_groups):
                logger.info(f"Executing parallel group {group_index + 1}/{len(parallel_groups)}: {agent_group}")
                
                # Wait for resource availability if resource management is enabled
                if self.optimization.enable_resource_management:
                    await self._wait_for_resources(agent_group, workflow_id)
                
                # Execute agents in parallel within the group
                group_results = await self._execute_agent_group_parallel(
                    agent_group, stage_results, contract_text, contract_filename, workflow_id, status
                )
                
                # Update stage results
                stage_results.update(group_results)
                
                # Update status
                for agent_name in agent_group:
                    if agent_name in status.running_agents:
                        status.running_agents.remove(agent_name)
                    
                    if group_results.get(agent_name, {}).get("success", False):
                        if agent_name not in status.completed_agents:
                            status.completed_agents.append(agent_name)
                    else:
                        if agent_name not in status.failed_agents:
                            status.failed_agents.append(agent_name)
        
        # Update resource utilization in status
        if self.optimization.enable_resource_management:
            status.resource_utilization = self.resource_manager.get_resource_utilization()
        
        # Compile final results
        return self._compile_optimized_results(
            stage_results.get("analyzer", {}),
            stage_results.get("risk_assessor", {}),
            stage_results.get("precedent_researcher", {}),
            stage_results.get("negotiator", {}),
            stage_results.get("communicator", {}),
            workflow_id, status
        )
    
    async def _wait_for_resources(self, agent_group: List[str], workflow_id: str):
        """Wait for sufficient resources to become available for agent group."""
        max_wait_time = 300  # 5 minutes maximum wait
        wait_start = time.time()
        
        while time.time() - wait_start < max_wait_time:
            # Check if all agents in group can get resources
            can_allocate_all = True
            
            for agent_name in agent_group:
                dependency = self.agent_dependencies.get(agent_name)
                if dependency and not self.resource_manager.can_allocate_resources(
                    agent_name, dependency.resource_requirements
                ):
                    can_allocate_all = False
                    break
            
            if can_allocate_all:
                return
            
            # Clean up any expired allocations
            self.resource_manager.cleanup_expired_allocations()
            
            # Wait a bit before checking again
            await asyncio.sleep(5)
        
        logger.warning(f"Resource wait timeout for workflow {workflow_id}, proceeding with available resources")
    
    async def _execute_agent_group_parallel(
        self, 
        agent_group: List[str], 
        previous_results: Dict[str, Any],
        contract_text: str,
        contract_filename: str,
        workflow_id: str,
        status: OptimizedWorkflowStatus
    ) -> Dict[str, Any]:
        """Execute a group of agents in parallel with resource management."""
        
        # Prepare tasks for parallel execution
        tasks = []
        allocated_agents = []
        
        for agent_name in agent_group:
            # Allocate resources if resource management is enabled
            if self.optimization.enable_resource_management:
                dependency = self.agent_dependencies.get(agent_name)
                if dependency:
                    if self.resource_manager.allocate_resources(agent_name, dependency.resource_requirements):
                        allocated_agents.append(agent_name)
                    else:
                        logger.warning(f"Could not allocate resources for agent {agent_name}, skipping")
                        continue
                else:
                    allocated_agents.append(agent_name)
            else:
                allocated_agents.append(agent_name)
            
            # Prepare task input based on dependencies
            task_input = self._prepare_agent_input(agent_name, previous_results, contract_text, contract_filename, workflow_id)
            
            # Create task
            task = self._execute_agent_with_resource_management(agent_name, task_input, workflow_id, status)
            tasks.append((agent_name, task))
            
            # Update status
            if agent_name not in status.running_agents:
                status.running_agents.append(agent_name)
        
        # Execute tasks in parallel
        results = {}
        
        if tasks:
            try:
                # Execute with timeout
                task_results = await asyncio.wait_for(
                    asyncio.gather(*[task for _, task in tasks], return_exceptions=True),
                    timeout=self.optimization.timeout_per_agent * 2
                )
                
                # Process results
                for i, (agent_name, _) in enumerate(tasks):
                    if isinstance(task_results[i], Exception):
                        logger.error(f"Agent {agent_name} failed: {task_results[i]}")
                        results[agent_name] = {"success": False, "error": str(task_results[i])}
                    else:
                        results[agent_name] = task_results[i]
                
            except asyncio.TimeoutError:
                logger.error(f"Parallel group execution timed out for agents: {[name for name, _ in tasks]}")
                for agent_name, _ in tasks:
                    results[agent_name] = {"success": False, "error": "Execution timed out"}
            
            finally:
                # Release resources for all allocated agents
                if self.optimization.enable_resource_management:
                    for agent_name in allocated_agents:
                        self.resource_manager.release_resources(agent_name)
        
        # Update performance stats
        if len(allocated_agents) > 1:
            self.performance_stats["parallel_execution_stats"]["total_parallel_stages"] += 1
            current_avg = self.performance_stats["parallel_execution_stats"]["avg_parallel_agents"]
            total_stages = self.performance_stats["parallel_execution_stats"]["total_parallel_stages"]
            self.performance_stats["parallel_execution_stats"]["avg_parallel_agents"] = \
                ((current_avg * (total_stages - 1)) + len(allocated_agents)) / total_stages
        
        return results
    
    def _prepare_agent_input(
        self, 
        agent_name: str, 
        previous_results: Dict[str, Any],
        contract_text: str,
        contract_filename: str,
        workflow_id: str
    ) -> Dict[str, Any]:
        """Prepare input for an agent based on its dependencies."""
        
        base_input = {"workflow_id": workflow_id}
        
        if agent_name == "analyzer":
            base_input.update({
                "contract_text": contract_text,
                "contract_filename": contract_filename
            })
        elif agent_name == "risk_assessor":
            base_input["analysis_results"] = previous_results.get("analyzer", {})
        elif agent_name == "precedent_researcher":
            base_input.update({
                "analysis_results": previous_results.get("analyzer", {}),
                "risk_results": previous_results.get("risk_assessor", {})
            })
        elif agent_name == "negotiator":
            base_input.update({
                "analysis_results": previous_results.get("analyzer", {}),
                "risk_results": previous_results.get("risk_assessor", {}),
                "precedent_results": previous_results.get("precedent_researcher", {})
            })
        elif agent_name == "communicator":
            base_input.update({
                "analysis_results": previous_results.get("analyzer", {}),
                "risk_results": previous_results.get("risk_assessor", {}),
                "negotiation_results": previous_results.get("negotiator", {})
            })
        
        return base_input
    
    async def _execute_agent_with_resource_management(
        self, agent_name: str, task_input: Dict[str, Any], workflow_id: str, status: OptimizedWorkflowStatus
    ) -> Dict[str, Any]:
        """Execute an agent with resource management and enhanced monitoring."""
        
        start_time = time.time()
        
        # Update workflow progress - agent starting
        workflow_manager = get_workflow_progress_manager()
        workflow_manager.start_agent(workflow_id, agent_name)
        await self._broadcast_progress_update(workflow_id)
        
        try:
            # Execute the agent
            result = await self._execute_agent_with_fallback(agent_name, task_input, workflow_id, status)
            
            execution_time = time.time() - start_time
            
            # Update workflow progress based on result
            if result.get("success", False):
                workflow_manager.complete_agent(workflow_id, agent_name)
            else:
                error_message = result.get("error", "Agent execution failed")
                workflow_manager.fail_agent(workflow_id, agent_name, error_message)
            
            # Broadcast progress update
            await self._broadcast_progress_update(workflow_id)
            
            # Update performance stats
            if agent_name not in self.performance_stats["agent_utilization"]:
                self.performance_stats["agent_utilization"][agent_name] = {
                    "total_executions": 0,
                    "total_time": 0.0,
                    "avg_time": 0.0,
                    "success_rate": 0.0,
                    "total_successes": 0
                }
            
            stats = self.performance_stats["agent_utilization"][agent_name]
            stats["total_executions"] += 1
            stats["total_time"] += execution_time
            stats["avg_time"] = stats["total_time"] / stats["total_executions"]
            
            if result.get("success", False):
                stats["total_successes"] += 1
            
            stats["success_rate"] = stats["total_successes"] / stats["total_executions"]
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Agent {agent_name} execution failed after {execution_time:.2f}s: {e}")
            
            # Update workflow progress - agent failed
            workflow_manager.fail_agent(workflow_id, agent_name, str(e))
            await self._broadcast_progress_update(workflow_id)
            
            return {"success": False, "error": str(e), "execution_time": execution_time}
    
    async def _execute_legacy_parallel_workflow(
        self, contract_text: str, contract_filename: str, workflow_id: str, status: OptimizedWorkflowStatus
    ) -> Dict[str, Any]:
        """Legacy parallel execution method for backward compatibility"""
        logger.info(f"Executing legacy parallel workflow for {workflow_id}")
        
        # Stage 1: Contract Analysis (must be first)
        status.current_stage = "contract_analysis"
        analysis_results = await self._execute_agent_with_fallback(
            "analyzer", {
                "contract_text": contract_text,
                "contract_filename": contract_filename,
                "workflow_id": workflow_id
            }, workflow_id, status
        )
        
        if not analysis_results.get("success", False):
            raise WorkflowExecutionError("Contract analysis stage failed - cannot proceed")
        
        # Stage 2: Parallel execution of risk assessment and precedent research
        status.current_stage = "parallel_analysis"
        
        # Create tasks for parallel execution
        risk_task = self._execute_agent_with_fallback(
            "risk_assessor", {
                "analysis_results": analysis_results,
                "workflow_id": workflow_id
            }, workflow_id, status
        )
        
        precedent_task = self._execute_agent_with_fallback(
            "precedent_researcher", {
                "analysis_results": analysis_results,
                "risk_results": {"risky_clauses": analysis_results.get("identified_clauses", [])},
                "workflow_id": workflow_id
            }, workflow_id, status
        )
        
        # Execute in parallel with timeout
        try:
            risk_results, precedent_results = await asyncio.wait_for(
                asyncio.gather(risk_task, precedent_task, return_exceptions=True),
                timeout=self.optimization.timeout_per_agent * 2
            )
            
            # Handle exceptions from parallel execution
            if isinstance(risk_results, Exception):
                logger.error(f"Risk assessment failed: {risk_results}")
                risk_results = {"success": False, "error": str(risk_results)}
            
            if isinstance(precedent_results, Exception):
                logger.error(f"Precedent research failed: {precedent_results}")
                precedent_results = {"success": False, "error": str(precedent_results)}
                
        except asyncio.TimeoutError:
            logger.error("Parallel execution timed out")
            raise WorkflowExecutionError("Parallel agent execution timed out")
        
        # Stage 3: Negotiation (depends on both risk and precedent results)
        status.current_stage = "negotiation"
        negotiation_results = await self._execute_agent_with_fallback(
            "negotiator", {
                "analysis_results": analysis_results,
                "risk_results": risk_results,
                "precedent_results": precedent_results,
                "workflow_id": workflow_id
            }, workflow_id, status
        )
        
        # Stage 4: Communication (final stage)
        status.current_stage = "communication"
        communication_results = await self._execute_agent_with_fallback(
            "communicator", {
                "analysis_results": analysis_results,
                "risk_results": risk_results,
                "negotiation_results": negotiation_results,
                "workflow_id": workflow_id
            }, workflow_id, status
        )
        
        return self._compile_optimized_results(
            analysis_results, risk_results, precedent_results, 
            negotiation_results, communication_results, workflow_id, status
        )
    
    async def _execute_adaptive_workflow(
        self, contract_text: str, contract_filename: str, workflow_id: str, status: OptimizedWorkflowStatus
    ) -> Dict[str, Any]:
        """Execute workflow with adaptive routing based on agent health and performance"""
        logger.info(f"Executing adaptive workflow for {workflow_id}")
        
        # Assess agent health and choose optimal execution path
        healthy_agents = [k for k, v in self.agent_health.items() if v.status == AgentStatus.HEALTHY]
        degraded_agents = [k for k, v in self.agent_health.items() if v.status == AgentStatus.DEGRADED]
        
        logger.info(f"Agent health status - Healthy: {healthy_agents}, Degraded: {degraded_agents}")
        
        # Adaptive execution based on agent health
        if len(healthy_agents) >= 4:  # Most agents healthy - use parallel execution
            return await self._execute_parallel_workflow(contract_text, contract_filename, workflow_id, status)
        elif len(healthy_agents) >= 2:  # Some agents healthy - use selective parallel execution
            return await self._execute_selective_parallel_workflow(contract_text, contract_filename, workflow_id, status)
        else:  # Few healthy agents - use sequential with extensive fallbacks
            return await self._execute_sequential_workflow(contract_text, contract_filename, workflow_id, status)
    
    async def _execute_sequential_workflow(
        self, contract_text: str, contract_filename: str, workflow_id: str, status: OptimizedWorkflowStatus
    ) -> Dict[str, Any]:
        """Execute workflow sequentially with enhanced error handling"""
        logger.info(f"Executing sequential workflow for {workflow_id}")
        
        # Stage 1: Contract Analysis
        status.current_stage = "contract_analysis"
        analysis_results = await self._execute_agent_with_fallback(
            "analyzer", {
                "contract_text": contract_text,
                "contract_filename": contract_filename,
                "workflow_id": workflow_id
            }, workflow_id, status
        )
        
        # Stage 2: Risk Assessment
        status.current_stage = "risk_assessment"
        risk_results = await self._execute_agent_with_fallback(
            "risk_assessor", {
                "analysis_results": analysis_results,
                "workflow_id": workflow_id
            }, workflow_id, status
        )
        
        # Stage 3: Precedent Research
        status.current_stage = "precedent_research"
        precedent_results = await self._execute_agent_with_fallback(
            "precedent_researcher", {
                "analysis_results": analysis_results,
                "risk_results": risk_results,
                "workflow_id": workflow_id
            }, workflow_id, status
        )
        
        # Stage 4: Negotiation
        status.current_stage = "negotiation"
        negotiation_results = await self._execute_agent_with_fallback(
            "negotiator", {
                "analysis_results": analysis_results,
                "risk_results": risk_results,
                "precedent_results": precedent_results,
                "workflow_id": workflow_id
            }, workflow_id, status
        )
        
        # Stage 5: Communication
        status.current_stage = "communication"
        communication_results = await self._execute_agent_with_fallback(
            "communicator", {
                "analysis_results": analysis_results,
                "risk_results": risk_results,
                "negotiation_results": negotiation_results,
                "workflow_id": workflow_id
            }, workflow_id, status
        )
        
        return self._compile_optimized_results(
            analysis_results, risk_results, precedent_results, 
            negotiation_results, communication_results, workflow_id, status
        )
    
    async def _execute_agent_with_fallback(
        self, agent_key: str, task_input: Dict[str, Any], workflow_id: str, status: OptimizedWorkflowStatus
    ) -> Dict[str, Any]:
        """Execute an agent with comprehensive fallback mechanisms"""
        
        # Check if agent is available
        if not self._is_agent_available(agent_key):
            logger.warning(f"Agent {agent_key} is not available, attempting fallback")
            return await self._execute_fallback_for_agent(agent_key, task_input, workflow_id, status)
        
        agent = self.agents[agent_key]
        start_time = time.time()
        
        try:
            # Execute with caching and timeout (if agent supports it)
            if hasattr(agent, 'execute_with_caching_and_timeout'):
                result = await agent.execute_with_caching_and_timeout(task_input)
            else:
                # Fallback to regular execution with timeout
                result = await asyncio.wait_for(
                    agent.execute_with_monitoring(task_input),
                    timeout=self.optimization.timeout_per_agent
                )
            
            execution_time = time.time() - start_time
            
            # Update health metrics on success
            self.agent_health[agent_key].update_success(execution_time)
            
            # Update status
            if result.get("success", False):
                status.completed_agents.append(agent_key)
                logger.info(f"Agent {agent_key} completed successfully in {execution_time:.2f}s")
            else:
                status.degraded_agents.append(agent_key)
                logger.warning(f"Agent {agent_key} completed with issues: {result.get('error', 'Unknown error')}")
            
            return result
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            error_msg = f"Agent {agent_key} timed out after {execution_time:.2f}s"
            logger.error(error_msg)
            
            # Update health and circuit breaker
            self.agent_health[agent_key].update_failure(error_msg)
            self._update_circuit_breaker(agent_key, error_msg)
            
            status.failed_agents.append(agent_key)
            
            # Attempt fallback
            return await self._execute_fallback_for_agent(agent_key, task_input, workflow_id, status)
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Agent {agent_key} failed: {e}"
            logger.error(error_msg, exc_info=True)
            
            # Update health and circuit breaker
            self.agent_health[agent_key].update_failure(error_msg)
            self._update_circuit_breaker(agent_key, error_msg)
            
            status.failed_agents.append(agent_key)
            
            # Attempt fallback
            return await self._execute_fallback_for_agent(agent_key, task_input, workflow_id, status)
    
    async def _execute_fallback_for_agent(
        self, agent_key: str, task_input: Dict[str, Any], workflow_id: str, status: OptimizedWorkflowStatus
    ) -> Dict[str, Any]:
        """Execute fallback logic for a failed agent"""
        
        if not self.optimization.enable_fallback_agents:
            return {"success": False, "error": f"Agent {agent_key} failed and fallback disabled"}
        
        logger.info(f"Executing fallback for agent {agent_key}")
        status.recovery_actions.append(f"fallback_executed_for_{agent_key}")
        
        # Agent-specific fallback logic
        if agent_key == "analyzer":
            return await self._fallback_contract_analysis(task_input, workflow_id)
        elif agent_key == "risk_assessor":
            return await self._fallback_risk_assessment(task_input, workflow_id)
        elif agent_key == "precedent_researcher":
            return await self._fallback_precedent_research(task_input, workflow_id)
        elif agent_key == "negotiator":
            return await self._fallback_negotiation(task_input, workflow_id)
        elif agent_key == "communicator":
            return await self._fallback_communication(task_input, workflow_id)
        else:
            return {"success": False, "error": f"No fallback available for agent {agent_key}"}
    
    async def _fallback_contract_analysis(self, task_input: Dict[str, Any], workflow_id: str) -> Dict[str, Any]:
        """Fallback job application tracking using simplified logic"""
        logger.info(f"Executing fallback job application tracking for workflow {workflow_id}")
        
        contract_text = task_input.get("contract_text", "")
        contract_filename = task_input.get("contract_filename", "unknown")
        
        # Simple text-based analysis
        clauses = []
        text_lines = contract_text.split('\n')
        
        # Basic clause identification
        for i, line in enumerate(text_lines):
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in ['liability', 'termination', 'payment', 'confidentiality']):
                clauses.append({
                    "clause_index": i,
                    "clause_text": line.strip(),
                    "clause_type": self._identify_clause_type(line_lower),
                    "confidence": 0.6,
                    "fallback_generated": True
                })
        
        return {
            "success": True,
            "contract_structure": {
                "contract_type": "General Agreement",
                "main_sections": ["Terms", "Conditions"],
                "parties": ["Party A", "Party B"],
                "confidence_score": 0.5,
                "fallback_analysis": True
            },
            "identified_clauses": clauses[:10],  # Limit to 10 clauses
            "fallback_used": True,
            "workflow_id": workflow_id
        }
    
    async def _fallback_risk_assessment(self, task_input: Dict[str, Any], workflow_id: str) -> Dict[str, Any]:
        """Fallback risk assessment using rule-based logic"""
        logger.info(f"Executing fallback risk assessment for workflow {workflow_id}")
        
        analysis_results = task_input.get("analysis_results", {})
        identified_clauses = analysis_results.get("identified_clauses", [])
        
        risky_clauses = []
        total_risk_score = 0.0
        
        # Simple risk scoring based on keywords
        risk_keywords = {
            'liability': 8.0,
            'unlimited': 9.0,
            'termination': 6.0,
            'penalty': 7.0,
            'indemnification': 8.5,
            'damages': 7.5
        }
        
        for clause in identified_clauses:
            clause_text = clause.get("clause_text", "").lower()
            risk_score = 0.0
            
            for keyword, score in risk_keywords.items():
                if keyword in clause_text:
                    risk_score = max(risk_score, score)
            
            if risk_score >= 5.0:
                risky_clauses.append({
                    **clause,
                    "overall_risk_score": risk_score,
                    "risk_level": "High" if risk_score >= 8.0 else "Medium",
                    "risk_explanation": f"Contains high-risk keyword patterns",
                    "fallback_generated": True
                })
                total_risk_score += risk_score
        
        overall_risk = min(10.0, total_risk_score / max(len(risky_clauses), 1))
        
        return {
            "success": True,
            "risky_clauses": risky_clauses,
            "overall_risk_score": overall_risk,
            "risk_summary": f"Identified {len(risky_clauses)} potentially risky clauses using fallback analysis",
            "fallback_used": True,
            "workflow_id": workflow_id
        }
    
    def _identify_clause_type(self, text: str) -> str:
        """Simple clause type identification"""
        if 'liability' in text:
            return 'liability'
        elif 'termination' in text:
            return 'termination'
        elif 'payment' in text:
            return 'payment_terms'
        elif 'confidential' in text:
            return 'confidentiality'
        else:
            return 'general'
    
    async def _fallback_precedent_research(self, task_input: Dict[str, Any], workflow_id: str) -> Dict[str, Any]:
        """Fallback precedent research using basic templates"""
        logger.info(f"Executing fallback precedent research for workflow {workflow_id}")
        
        # Basic precedent templates
        precedent_matches = [
            {
                "precedent_id": "fallback_001",
                "clause_text": "Standard liability limitation clause",
                "category": "liability",
                "risk_level": "Medium",
                "effectiveness_score": 0.7,
                "source_document": "Standard Commercial Agreement Template",
                "fallback_generated": True
            },
            {
                "precedent_id": "fallback_002", 
                "clause_text": "Standard termination notice clause",
                "category": "termination",
                "risk_level": "Low",
                "effectiveness_score": 0.8,
                "source_document": "Standard Commercial Agreement Template",
                "fallback_generated": True
            }
        ]
        
        return {
            "success": True,
            "precedent_matches": precedent_matches,
            "precedent_context": ["Basic precedent templates used due to service unavailability"],
            "fallback_used": True,
            "workflow_id": workflow_id
        }
    
    async def _fallback_negotiation(self, task_input: Dict[str, Any], workflow_id: str) -> Dict[str, Any]:
        """Fallback negotiation using basic recommendations"""
        logger.info(f"Executing fallback negotiation for workflow {workflow_id}")
        
        risk_results = task_input.get("risk_results", {})
        risky_clauses = risk_results.get("risky_clauses", [])
        
        suggested_redlines = []
        for clause in risky_clauses[:5]:  # Limit to top 5
            suggested_redlines.append({
                "clause_index": clause.get("clause_index", 0),
                "original_text": clause.get("clause_text", ""),
                "suggested_change": "Consider adding limitation or clarification language",
                "priority": "medium",
                "rationale": "Risk mitigation through standard protective language",
                "fallback_generated": True
            })
        
        return {
            "success": True,
            "suggested_redlines": suggested_redlines,
            "negotiation_strategy": "Focus on risk mitigation through standard protective language",
            "alternative_clauses": [],
            "fallback_used": True,
            "workflow_id": workflow_id
        }
    
    async def _fallback_communication(self, task_input: Dict[str, Any], workflow_id: str) -> Dict[str, Any]:
        """Fallback communication using basic templates"""
        logger.info(f"Executing fallback communication for workflow {workflow_id}")
        
        return {
            "success": True,
            "email_draft": "Contract analysis completed. Please review the attached results and recommendations.",
            "communication_templates": {
                "executive_summary": "Contract analysis has been completed with basic risk assessment.",
                "next_steps": ["Review analysis results", "Consider recommended changes", "Proceed with legal review"]
            },
            "next_steps": ["Review analysis results", "Consider recommended changes"],
            "fallback_used": True,
            "workflow_id": workflow_id
        }
    
    async def _attempt_graceful_degradation(
        self, contract_text: str, contract_filename: str, workflow_id: str, status: OptimizedWorkflowStatus
    ) -> Optional[Dict[str, Any]]:
        """Attempt to provide partial results when workflow fails"""
        logger.info(f"Attempting graceful degradation for workflow {workflow_id}")
        
        try:
            # Try to provide at least basic analysis
            basic_analysis = await self._fallback_contract_analysis({
                "contract_text": contract_text,
                "contract_filename": contract_filename,
                "workflow_id": workflow_id
            }, workflow_id)
            
            if basic_analysis.get("success"):
                basic_risk = await self._fallback_risk_assessment({
                    "analysis_results": basic_analysis,
                    "workflow_id": workflow_id
                }, workflow_id)
                
                status.status = "degraded"
                status.recovery_actions.append("graceful_degradation_successful")
                
                return {
                    "success": True,
                    "degraded_mode": True,
                    "contract_structure": basic_analysis.get("contract_structure", {}),
                    "identified_clauses": basic_analysis.get("identified_clauses", []),
                    "risky_clauses": basic_risk.get("risky_clauses", []),
                    "overall_risk_score": basic_risk.get("overall_risk_score", 0.0),
                    "risk_summary": "Basic analysis completed in degraded mode",
                    "workflow_id": workflow_id,
                    "completed_agents": status.completed_agents,
                    "degraded_agents": status.degraded_agents,
                    "warning": "Analysis completed with limited functionality due to service issues"
                }
        
        except Exception as e:
            logger.error(f"Graceful degradation failed: {e}")
            status.recovery_actions.append("graceful_degradation_failed")
        
        return None
    
    def _generate_cache_key(self, contract_text: str, workflow_config: Optional[Dict[str, Any]]) -> str:
        """Generate cache key for workflow results"""
        import hashlib
        
        content = contract_text + str(workflow_config or {})
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_cache_valid(self, cached_result: Dict[str, Any]) -> bool:
        """Check if cached result is still valid"""
        timestamp = cached_result.get("timestamp")
        ttl_minutes = cached_result.get("ttl_minutes", self.optimization.cache_ttl_minutes)
        
        if not timestamp:
            return False
        
        age = datetime.utcnow() - timestamp
        return age.total_seconds() < (ttl_minutes * 60)
    
    async def _execute_negotiation_stage(
        self,
        analysis_results: Dict[str, Any],
        risk_results: Dict[str, Any],
        precedent_results: Dict[str, Any],
        workflow_id: str
    ) -> Dict[str, Any]:
        """Execute the negotiation stage"""
        try:
            negotiator = self.agents["negotiator"]
            
            task_input = {
                "analysis_results": analysis_results,
                "risk_results": risk_results,
                "precedent_results": precedent_results,
                "workflow_id": workflow_id
            }
            
            result = await negotiator.execute_with_monitoring(task_input)
            
            logger.info(f"Negotiation stage completed for workflow {workflow_id}")
            return result
            
        except Exception as e:
            logger.error(f"Negotiation stage failed for workflow {workflow_id}: {e}")
            self.workflow_status[workflow_id].failed_agents.append("negotiator")
            return {"success": False, "error": str(e)}
    
    async def _execute_communication_stage(
        self,
        analysis_results: Dict[str, Any],
        risk_results: Dict[str, Any],
        negotiation_results: Dict[str, Any],
        workflow_id: str
    ) -> Dict[str, Any]:
        """Execute the communication stage"""
        try:
            communicator = self.agents["communicator"]
            
            task_input = {
                "analysis_results": analysis_results,
                "risk_results": risk_results,
                "negotiation_results": negotiation_results,
                "workflow_id": workflow_id
            }
            
            result = await communicator.execute_with_monitoring(task_input)
            
            logger.info(f"Communication stage completed for workflow {workflow_id}")
            return result
            
        except Exception as e:
            logger.error(f"Communication stage failed for workflow {workflow_id}: {e}")
            self.workflow_status[workflow_id].failed_agents.append("communicator")
            return {"success": False, "error": str(e)}
    
    def _compile_optimized_results(
        self,
        analysis_results: Dict[str, Any],
        risk_results: Dict[str, Any],
        precedent_results: Dict[str, Any],
        negotiation_results: Dict[str, Any],
        communication_results: Dict[str, Any],
        workflow_id: str,
        status: OptimizedWorkflowStatus
    ) -> Dict[str, Any]:
        """Compile all stage results into optimized final workflow output"""
        
        # Calculate quality metrics
        quality_score = self._calculate_result_quality(
            analysis_results, risk_results, precedent_results, negotiation_results, communication_results
        )
        
        # Determine if any fallbacks were used
        fallback_used = any([
            analysis_results.get("fallback_used", False),
            risk_results.get("fallback_used", False),
            precedent_results.get("fallback_used", False),
            negotiation_results.get("fallback_used", False),
            communication_results.get("fallback_used", False)
        ])
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "execution_mode": status.execution_mode.value,
            "execution_time": status.total_execution_time,
            "quality_score": quality_score,
            "fallback_used": fallback_used,
            
            # Agent execution status
            "completed_agents": status.completed_agents,
            "failed_agents": status.failed_agents,
            "degraded_agents": status.degraded_agents,
            "recovery_actions": status.recovery_actions,
            
            # Contract analysis results
            "contract_structure": analysis_results.get("contract_structure", {}),
            "identified_clauses": analysis_results.get("identified_clauses", []),
            
            # Risk assessment results
            "risky_clauses": risk_results.get("risky_clauses", []),
            "overall_risk_score": risk_results.get("overall_risk_score", 0.0),
            "risk_summary": risk_results.get("risk_summary", ""),
            
            # Precedent research results
            "precedent_matches": precedent_results.get("precedent_matches", []),
            "precedent_context": precedent_results.get("precedent_context", []),
            
            # Negotiation results
            "suggested_redlines": negotiation_results.get("suggested_redlines", []),
            "negotiation_strategy": negotiation_results.get("negotiation_strategy", ""),
            "alternative_clauses": negotiation_results.get("alternative_clauses", []),
            
            # Communication results
            "email_draft": communication_results.get("email_draft", ""),
            "communication_templates": communication_results.get("communication_templates", {}),
            "next_steps": communication_results.get("next_steps", []),
            
            # Enhanced metadata
            "workflow_metadata": {
                "start_time": status.start_time,
                "end_time": status.end_time,
                "total_execution_time": status.total_execution_time,
                "execution_mode": status.execution_mode.value,
                "agents_used": status.completed_agents,
                "workflow_version": "2.0.0",
                "optimization_enabled": True,
                "health_monitoring_enabled": self.config.enable_health_monitoring,
                "performance_optimization_enabled": self.config.enable_performance_optimization
            },
            
            # Performance metrics
            "performance_metrics": {
                "agent_health_scores": {k: v.success_rate for k, v in self.agent_health.items()},
                "avg_agent_response_time": {k: v.avg_response_time for k, v in self.agent_health.items()},
                "circuit_breaker_states": {k: v["state"] for k, v in self.circuit_breakers.items()},
                "cache_hit": not fallback_used and self.optimization.enable_result_caching
            }
        }
    
    def _calculate_result_quality(self, *results) -> float:
        """Calculate overall quality score for workflow results"""
        quality_factors = []
        
        for result in results:
            if not result or not result.get("success", False):
                quality_factors.append(0.0)
                continue
            
            # Base quality score
            base_score = 0.8
            
            # Reduce quality if fallback was used
            if result.get("fallback_used", False):
                base_score *= 0.6
            
            # Increase quality based on result completeness
            if result.get("confidence_score"):
                base_score *= result["confidence_score"]
            
            quality_factors.append(base_score)
        
        return sum(quality_factors) / len(quality_factors) if quality_factors else 0.0
    
    async def _execute_selective_parallel_workflow(
        self, contract_text: str, contract_filename: str, workflow_id: str, status: OptimizedWorkflowStatus
    ) -> Dict[str, Any]:
        """Execute workflow with selective parallelization based on agent health"""
        logger.info(f"Executing selective parallel workflow for {workflow_id}")
        
        # Stage 1: Contract Analysis (always first)
        status.current_stage = "contract_analysis"
        analysis_results = await self._execute_agent_with_fallback(
            "analyzer", {
                "contract_text": contract_text,
                "contract_filename": contract_filename,
                "workflow_id": workflow_id
            }, workflow_id, status
        )
        
        # Stage 2: Selective parallel execution based on agent health
        status.current_stage = "selective_parallel"
        
        # Only run healthy agents in parallel
        healthy_agents = [k for k, v in self.agent_health.items() if v.status == AgentStatus.HEALTHY]
        
        parallel_tasks = []
        if "risk_assessor" in healthy_agents:
            parallel_tasks.append(("risk_assessor", {
                "analysis_results": analysis_results,
                "workflow_id": workflow_id
            }))
        
        if "precedent_researcher" in healthy_agents and len(parallel_tasks) < 2:
            parallel_tasks.append(("precedent_researcher", {
                "analysis_results": analysis_results,
                "risk_results": {"risky_clauses": analysis_results.get("identified_clauses", [])},
                "workflow_id": workflow_id
            }))
        
        # Execute parallel tasks
        parallel_results = {}
        if parallel_tasks:
            tasks = [
                self._execute_agent_with_fallback(agent_key, task_input, workflow_id, status)
                for agent_key, task_input in parallel_tasks
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, (agent_key, _) in enumerate(parallel_tasks):
                if isinstance(results[i], Exception):
                    parallel_results[agent_key] = {"success": False, "error": str(results[i])}
                else:
                    parallel_results[agent_key] = results[i]
        
        # Execute remaining agents sequentially
        risk_results = parallel_results.get("risk_assessor")
        if not risk_results:
            risk_results = await self._execute_agent_with_fallback(
                "risk_assessor", {
                    "analysis_results": analysis_results,
                    "workflow_id": workflow_id
                }, workflow_id, status
            )
        
        precedent_results = parallel_results.get("precedent_researcher")
        if not precedent_results:
            precedent_results = await self._execute_agent_with_fallback(
                "precedent_researcher", {
                    "analysis_results": analysis_results,
                    "risk_results": risk_results,
                    "workflow_id": workflow_id
                }, workflow_id, status
            )
        
        # Continue with remaining stages sequentially
        negotiation_results = await self._execute_agent_with_fallback(
            "negotiator", {
                "analysis_results": analysis_results,
                "risk_results": risk_results,
                "precedent_results": precedent_results,
                "workflow_id": workflow_id
            }, workflow_id, status
        )
        
        communication_results = await self._execute_agent_with_fallback(
            "communicator", {
                "analysis_results": analysis_results,
                "risk_results": risk_results,
                "negotiation_results": negotiation_results,
                "workflow_id": workflow_id
            }, workflow_id, status
        )
        
        return self._compile_optimized_results(
            analysis_results, risk_results, precedent_results, 
            negotiation_results, communication_results, workflow_id, status
        )
    
    def get_workflow_status(self, workflow_id: str) -> Optional[OptimizedWorkflowStatus]:
        """Get the status of a specific workflow"""
        return self.workflow_status.get(workflow_id)
    
    def get_all_workflow_statuses(self) -> Dict[str, OptimizedWorkflowStatus]:
        """Get all workflow statuses"""
        return self.workflow_status.copy()
    
    def get_agent_health_status(self) -> Dict[str, Dict[str, Any]]:
        """Get comprehensive health status for all agents"""
        return {
            agent_key: {
                "status": health.status.value,
                "success_rate": health.success_rate,
                "avg_response_time": health.avg_response_time,
                "error_count": health.error_count,
                "consecutive_failures": health.consecutive_failures,
                "last_health_check": health.last_health_check.isoformat() if health.last_health_check else None,
                "last_error": health.last_error,
                "recovery_attempts": health.recovery_attempts,
                "circuit_breaker_state": self.circuit_breakers.get(agent_key, {}).get("state", "unknown")
            }
            for agent_key, health in self.agent_health.items()
        }
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        base_stats = {
            **self.performance_stats,
            "agent_health_summary": {
                "healthy": len([h for h in self.agent_health.values() if h.status == AgentStatus.HEALTHY]),
                "degraded": len([h for h in self.agent_health.values() if h.status == AgentStatus.DEGRADED]),
                "unhealthy": len([h for h in self.agent_health.values() if h.status == AgentStatus.UNHEALTHY]),
                "offline": len([h for h in self.agent_health.values() if h.status == AgentStatus.OFFLINE])
            },
            "circuit_breaker_summary": {
                "closed": len([cb for cb in self.circuit_breakers.values() if cb["state"] == "closed"]),
                "open": len([cb for cb in self.circuit_breakers.values() if cb["state"] == "open"]),
                "half_open": len([cb for cb in self.circuit_breakers.values() if cb["state"] == "half-open"])
            },
            "cache_statistics": {
                "cache_size": len(self.result_cache),
                "cache_enabled": self.optimization.enable_result_caching
            },
            "dependency_resolution": {
                "enabled": self.optimization.enable_dependency_resolution,
                "total_agents": len(self.agent_dependencies),
                "execution_stages": len(self.dependency_resolver.get_execution_order()) if self.optimization.enable_dependency_resolution else 0
            }
        }
        
        # Add resource management statistics if enabled
        if self.optimization.enable_resource_management:
            base_stats["resource_management"] = {
                "enabled": True,
                "current_utilization": self.resource_manager.get_resource_utilization(),
                "active_allocations": len(self.resource_manager.agent_resources),
                "total_usage_history": len(self.resource_manager.usage_history)
            }
        else:
            base_stats["resource_management"] = {"enabled": False}
        
        return base_stats
    
    async def force_agent_recovery(self, agent_key: str) -> bool:
        """Force recovery attempt for a specific agent"""
        if agent_key not in self.agents:
            return False
        
        try:
            logger.info(f"Forcing recovery for agent {agent_key}")
            
            # Reset circuit breaker
            self.circuit_breakers[agent_key] = {
                "failure_count": 0,
                "last_failure": None,
                "state": "closed"
            }
            
            # Reset health metrics
            self.agent_health[agent_key].consecutive_failures = 0
            self.agent_health[agent_key].recovery_attempts += 1
            self.agent_health[agent_key].status = AgentStatus.HEALTHY
            
            # Perform health check
            await self._perform_health_checks()
            
            logger.info(f"Recovery attempt completed for agent {agent_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to recover agent {agent_key}: {e}")
            return False
    
    def clear_result_cache(self):
        """Clear the result cache"""
        self.result_cache.clear()
        logger.info("Result cache cleared")
    
    def update_optimization_settings(self, new_settings: Dict[str, Any]):
        """Update optimization settings at runtime"""
        for key, value in new_settings.items():
            if hasattr(self.optimization, key):
                setattr(self.optimization, key, value)
                logger.info(f"Updated optimization setting {key} to {value}")
    
    def get_dependency_graph(self) -> Dict[str, Any]:
        """Get the current agent dependency graph for visualization."""
        execution_stages = self.dependency_resolver.get_execution_order()
        
        return {
            "dependencies": {
                name: {
                    "depends_on": dep.depends_on,
                    "can_run_parallel_with": dep.can_run_parallel_with,
                    "priority": dep.priority,
                    "resource_requirements": dep.resource_requirements
                }
                for name, dep in self.agent_dependencies.items()
            },
            "execution_stages": execution_stages,
            "parallel_capabilities": {
                stage_idx: self.dependency_resolver.get_parallel_groups(
                    stage, self.optimization.max_concurrent_agents
                )
                for stage_idx, stage in enumerate(execution_stages)
            }
        }
    
    def get_resource_status(self) -> Dict[str, Any]:
        """Get current resource utilization and limits."""
        if not self.optimization.enable_resource_management:
            return {"resource_management_enabled": False}
        
        return {
            "resource_management_enabled": True,
            "current_usage": self.resource_manager.current_usage,
            "resource_limits": {
                "max_concurrent_agents": self.resource_manager.limits.max_concurrent_agents,
                "max_memory_mb": self.resource_manager.limits.max_memory_mb,
                "max_cpu_percent": self.resource_manager.limits.max_cpu_percent,
                "max_tokens_per_minute": self.resource_manager.limits.max_tokens_per_minute,
                "max_cost_per_minute": self.resource_manager.limits.max_cost_per_minute
            },
            "utilization_percentages": self.resource_manager.get_resource_utilization(),
            "active_allocations": {
                agent: {
                    "allocated_at": alloc["allocated_at"].isoformat(),
                    "requirements": alloc["requirements"]
                }
                for agent, alloc in self.resource_manager.agent_resources.items()
            },
            "usage_history_count": len(self.resource_manager.usage_history)
        }
    
    def update_resource_limits(self, new_limits: Dict[str, Any]):
        """Update resource limits at runtime."""
        if not self.optimization.enable_resource_management:
            logger.warning("Resource management is disabled, cannot update limits")
            return False
        
        for key, value in new_limits.items():
            if hasattr(self.resource_manager.limits, key):
                setattr(self.resource_manager.limits, key, value)
                logger.info(f"Updated resource limit {key} to {value}")
        
        return True
    
    def force_resource_cleanup(self) -> int:
        """Force cleanup of all resource allocations."""
        if not self.optimization.enable_resource_management:
            return 0
        
        cleanup_count = 0
        agents_to_cleanup = list(self.resource_manager.agent_resources.keys())
        
        for agent_name in agents_to_cleanup:
            self.resource_manager.release_resources(agent_name)
            cleanup_count += 1
        
        logger.info(f"Force cleaned up {cleanup_count} resource allocations")
        return cleanup_count
    
    # Legacy method for backward compatibility
    def get_agent_states(self) -> Dict[str, Dict[str, Any]]:
        """Get the current state of all agents (legacy method)"""
        return {
            name: agent.get_agent_state() if hasattr(agent, 'get_agent_state') else {"status": "unknown"}
            for name, agent in self.agents.items()
        }
    
    # Legacy method for backward compatibility  
    async def execute_contract_analysis_workflow(
        self,
        contract_text: str,
        contract_filename: str,
        workflow_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Legacy method - redirects to optimized workflow"""
        return await self.execute_optimized_contract_analysis_workflow(
            contract_text, contract_filename, workflow_config
        )
    
    async def create_crew_for_workflow(
        self, workflow_type: str = "contract_analysis"
    ) -> Crew:
        """
        Create a CrewAI crew for a specific workflow type (legacy method).
        
        Args:
            workflow_type: Type of workflow to create crew for
            
        Returns:
            Crew: Configured CrewAI crew
        """
        try:
            if workflow_type == "contract_analysis":
                return await self._create_contract_analysis_crew()
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")
                
        except Exception as e:
            logger.error(f"Failed to create crew for workflow {workflow_type}: {e}")
            raise WorkflowExecutionError(
                f"Failed to create crew for workflow {workflow_type}: {e}",
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.HIGH
            )
    
    async def _create_contract_analysis_crew(self) -> Crew:
        """Create a crew specifically for job application tracking (legacy method)"""
        
        # Get available agent instances
        available_agents = []
        available_tasks = []
        
        if "analyzer" in self.agents and self._is_agent_available("analyzer"):
            analyzer = self.agents["analyzer"].crew_agent
            available_agents.append(analyzer)
            available_tasks.append(Task(
                description="Analyze the contract structure and identify key clauses",
                agent=analyzer,
                expected_output="Structured analysis of contract clauses and sections"
            ))
        
        if "risk_assessor" in self.agents and self._is_agent_available("risk_assessor"):
            risk_assessor = self.agents["risk_assessor"].crew_agent
            available_agents.append(risk_assessor)
            available_tasks.append(Task(
                description="Assess risks in identified contract clauses",
                agent=risk_assessor,
                expected_output="Risk assessment with scores and explanations"
            ))
        
        if "precedent_researcher" in self.agents and self._is_agent_available("precedent_researcher"):
            precedent_researcher = self.agents["precedent_researcher"].crew_agent
            available_agents.append(precedent_researcher)
            available_tasks.append(Task(
                description="Research legal precedents for identified risky clauses",
                agent=precedent_researcher,
                expected_output="Relevant legal precedents and case references"
            ))
        
        if "negotiator" in self.agents and self._is_agent_available("negotiator"):
            negotiator = self.agents["negotiator"].crew_agent
            available_agents.append(negotiator)
            available_tasks.append(Task(
                description="Generate redline suggestions and negotiation strategies",
                agent=negotiator,
                expected_output="Redline suggestions and alternative clause language"
            ))
        
        if "communicator" in self.agents and self._is_agent_available("communicator"):
            communicator = self.agents["communicator"].crew_agent
            available_agents.append(communicator)
            available_tasks.append(Task(
                description="Prepare communication materials for contract discussions",
                agent=communicator,
                expected_output="Email drafts and communication templates"
            ))
        
        if not available_agents:
            raise WorkflowExecutionError(
                "No healthy agents available for crew creation",
                category=ErrorCategory.RESOURCE,
                severity=ErrorSeverity.HIGH
            )
        
        # Create and return crew with available agents
        crew = Crew(
            agents=available_agents,
            tasks=available_tasks,
            process=Process.sequential,
            verbose=self.config.enable_health_monitoring
        )
        
        logger.info(f"Created crew with {len(available_agents)} available agents")
        return crew
    
    async def create_crew_for_workflow(
        self, workflow_type: str = "contract_analysis"
    ) -> Crew:
        """
        Create a CrewAI crew for a specific workflow type.
        
        Args:
            workflow_type: Type of workflow to create crew for
            
        Returns:
            Crew: Configured CrewAI crew
        """
        try:
            if workflow_type == "contract_analysis":
                return await self._create_contract_analysis_crew()
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")
                
        except Exception as e:
            logger.error(f"Failed to create crew for workflow {workflow_type}: {e}")
            raise WorkflowExecutionError(
                f"Failed to create crew for workflow {workflow_type}: {e}",
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.HIGH
            )
    
    async def _create_contract_analysis_crew(self) -> Crew:
        """Create a crew specifically for job application tracking"""
        
        # Get agent instances (with error handling for missing agents)
        try:
            analyzer = self.agents["analyzer"].crew_agent
            risk_assessor = self.agents["risk_assessor"].crew_agent
            precedent_researcher = self.agents["precedent_researcher"].crew_agent
            negotiator = self.agents["negotiator"].crew_agent
            communicator = self.agents["communicator"].crew_agent
        except (KeyError, AttributeError) as e:
            logger.error(f"Failed to get crew agents: {e}")
            raise WorkflowExecutionError(
                f"Agent not available for crew creation: {e}",
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.HIGH
            )
        
        # Define tasks
        analysis_task = Task(
            description="Analyze the contract structure and identify key clauses",
            agent=analyzer,
            expected_output="Structured analysis of contract clauses and sections"
        )
        
        risk_task = Task(
            description="Assess risks in identified contract clauses",
            agent=risk_assessor,
            expected_output="Risk assessment with scores and explanations"
        )
        
        precedent_task = Task(
            description="Research legal precedents for identified risky clauses",
            agent=precedent_researcher,
            expected_output="Relevant legal precedents and case references"
        )
        
        negotiation_task = Task(
            description="Generate redline suggestions and negotiation strategies",
            agent=negotiator,
            expected_output="Redline suggestions and alternative clause language"
        )
        
        communication_task = Task(
            description="Prepare communication materials for contract discussions",
            agent=communicator,
            expected_output="Email drafts and communication templates"
        )
        
        # Create and return crew
        crew = Crew(
            agents=[analyzer, risk_assessor, precedent_researcher, negotiator, communicator],
            tasks=[analysis_task, risk_task, precedent_task, negotiation_task, communication_task],
            process=Process.sequential,
            verbose=self.config.verbose_logging
        )
        
        return crew


# Global orchestration service instance
_orchestration_service: Optional[OptimizedAgentOrchestrationService] = None


def get_orchestration_service(config: Optional[OptimizedWorkflowConfig] = None) -> OptimizedAgentOrchestrationService:
    """Get or create the global optimized orchestration service instance"""
    global _orchestration_service
    
    if _orchestration_service is None:
        _orchestration_service = OptimizedAgentOrchestrationService(config)
    
    return _orchestration_service


def get_optimized_orchestration_service(config: Optional[OptimizedWorkflowConfig] = None) -> OptimizedAgentOrchestrationService:
    """Get or create the optimized orchestration service instance"""
    return get_orchestration_service(config)


# Legacy alias for backward compatibility
AgentOrchestrationService = OptimizedAgentOrchestrationService
WorkflowConfig = OptimizedWorkflowConfig
WorkflowStatus = OptimizedWorkflowStatus