"""
Integration tests for GROQ Phase 2: Optimizer, Router, and Monitor
"""

import pytest
import asyncio
from datetime import datetime

from backend.app.services.groq_service import GROQService, GROQModel, GROQTaskType
from backend.app.services.groq_optimizer import GROQOptimizer, GROQOptimizationConfig, OptimizationStrategy
from backend.app.services.groq_router import GROQModelRouter, RoutingStrategy
from backend.app.services.groq_monitor import GROQMonitor, MonitoringConfig


@pytest.fixture
async def groq_service():
    """Create GROQ service instance."""
    service = GROQService()
    yield service
    await service.close()


@pytest.fixture
def groq_optimizer():
    """Create GROQ optimizer instance."""
    config = GROQOptimizationConfig(
        strategy=OptimizationStrategy.BALANCED,
        enable_caching=True,
        enable_batching=False,  # Disable for testing
        enable_adaptive_routing=True
    )
    return GROQOptimizer(config)


@pytest.fixture
def groq_router(groq_service):
    """Create GROQ router instance."""
    return GROQModelRouter(groq_service)


@pytest.fixture
def groq_monitor(groq_service):
    """Create GROQ monitor instance."""
    config = MonitoringConfig(
        max_response_time=10.0,
        min_success_rate=0.95,
        max_cost_per_request=0.01
    )
    return GROQMonitor(groq_service, config)


class TestGROQOptimizer:
    """Test GROQ optimizer functionality."""
    
    @pytest.mark.asyncio
    async def test_optimizer_initialization(self, groq_optimizer):
        """Test optimizer initializes correctly."""
        assert groq_optimizer is not None
        assert groq_optimizer.config is not None
        assert groq_optimizer.groq_service is not None
        assert groq_optimizer.request_optimizer is not None
    
    @pytest.mark.asyncio
    async def test_message_optimization(self, groq_optimizer):
        """Test message optimization."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Analyze this contract clause: The contractor shall..."}
        ]
        
        optimized = groq_optimizer.request_optimizer.optimize_messages(messages)
        
        assert len(optimized) == len(messages)
        assert all("content" in msg for msg in optimized)
        assert all("role" in msg for msg in optimized)
    
    @pytest.mark.asyncio
    async def test_parameter_optimization(self, groq_optimizer):
        """Test parameter optimization."""
        base_params = {"temperature": 0.1, "max_tokens": 4000}
        
        optimized = groq_optimizer.request_optimizer.optimize_parameters(
            GROQModel.LLAMA3_1_8B,
            GROQTaskType.FAST_ANALYSIS,
            base_params
        )
        
        assert "temperature" in optimized
        assert "max_tokens" in optimized
    
    @pytest.mark.asyncio
    async def test_optimization_report(self, groq_optimizer):
        """Test optimization report generation."""
        report = await groq_optimizer.get_optimization_report()
        
        assert "config" in report
        assert "metrics" in report
        assert "performance" in report
        assert "groq_service_metrics" in report


class TestGROQRouter:
    """Test GROQ router functionality."""
    
    @pytest.mark.asyncio
    async def test_router_initialization(self, groq_router):
        """Test router initializes correctly."""
        assert groq_router is not None
        assert groq_router.groq_service is not None
        assert len(groq_router.routing_rules) > 0
        assert len(groq_router.performance_metrics) > 0
    
    @pytest.mark.asyncio
    async def test_model_selection_performance(self, groq_router):
        """Test performance-based model selection."""
        decision = await groq_router.select_model(
            GROQTaskType.FAST_ANALYSIS,
            RoutingStrategy.PERFORMANCE_BASED
        )
        
        assert decision is not None
        assert decision.selected_model is not None
        assert decision.confidence > 0
        assert decision.routing_strategy == RoutingStrategy.PERFORMANCE_BASED
    
    @pytest.mark.asyncio
    async def test_model_selection_cost(self, groq_router):
        """Test cost-optimized model selection."""
        decision = await groq_router.select_model(
            GROQTaskType.CONVERSATION,
            RoutingStrategy.COST_OPTIMIZED
        )
        
        assert decision is not None
        assert decision.selected_model is not None
        assert decision.estimated_cost >= 0
    
    @pytest.mark.asyncio
    async def test_model_selection_quality(self, groq_router):
        """Test quality-focused model selection."""
        decision = await groq_router.select_model(
            GROQTaskType.REASONING,
            RoutingStrategy.QUALITY_FOCUSED
        )
        
        assert decision is not None
        assert decision.selected_model is not None
        assert decision.confidence > 0
    
    @pytest.mark.asyncio
    async def test_adaptive_routing(self, groq_router):
        """Test adaptive routing with context."""
        context = {
            "urgency": "high",
            "budget_constraint": "normal",
            "quality_requirement": "high"
        }
        
        decision = await groq_router.select_model(
            GROQTaskType.CODE_GENERATION,
            RoutingStrategy.ADAPTIVE,
            context=context
        )
        
        assert decision is not None
        assert decision.selected_model is not None
        assert "context" in decision.metadata
    
    @pytest.mark.asyncio
    async def test_performance_tracking(self, groq_router):
        """Test performance tracking."""
        groq_router.record_request_result(
            GROQModel.LLAMA3_1_8B,
            GROQTaskType.FAST_ANALYSIS,
            response_time=1.5,
            quality_score=0.85,
            cost=0.0001,
            success=True
        )
        
        stats = groq_router.get_routing_statistics()
        
        assert "total_models" in stats
        assert "performance_metrics" in stats
        assert "circuit_breaker_states" in stats
    
    @pytest.mark.asyncio
    async def test_circuit_breaker(self, groq_router):
        """Test circuit breaker functionality."""
        model = GROQModel.LLAMA3_1_8B
        
        # Record multiple failures
        for _ in range(6):
            groq_router.record_request_result(
                model,
                GROQTaskType.FAST_ANALYSIS,
                response_time=0.0,
                quality_score=0.0,
                cost=0.0,
                success=False
            )
        
        # Circuit breaker should be open
        circuit_breaker = groq_router.circuit_breakers.get(model)
        assert circuit_breaker is not None
        assert circuit_breaker["state"] == "open"


class TestGROQMonitor:
    """Test GROQ monitor functionality."""
    
    @pytest.mark.asyncio
    async def test_monitor_initialization(self, groq_monitor):
        """Test monitor initializes correctly."""
        assert groq_monitor is not None
        assert groq_monitor.groq_service is not None
        assert groq_monitor.config is not None
    
    @pytest.mark.asyncio
    async def test_request_recording(self, groq_monitor):
        """Test request recording."""
        groq_monitor.record_request(
            GROQModel.LLAMA3_1_8B,
            GROQTaskType.FAST_ANALYSIS,
            response_time=1.5,
            token_count=500,
            cost=0.000025,
            quality_score=0.85,
            success=True
        )
        
        assert len(groq_monitor.performance_metrics) == 1
        assert len(groq_monitor.cost_breakdown) > 0
    
    @pytest.mark.asyncio
    async def test_dashboard_data(self, groq_monitor):
        """Test dashboard data generation."""
        # Record some test data
        for i in range(5):
            groq_monitor.record_request(
                GROQModel.LLAMA3_1_8B,
                GROQTaskType.FAST_ANALYSIS,
                response_time=1.0 + i * 0.1,
                token_count=500,
                cost=0.000025,
                quality_score=0.85,
                success=True
            )
        
        dashboard = groq_monitor.get_dashboard_data("24h")
        
        assert "summary" in dashboard
        assert "model_usage" in dashboard
        assert "task_usage" in dashboard
        assert "cost_breakdown" in dashboard
        assert dashboard["summary"]["total_requests"] == 5
    
    @pytest.mark.asyncio
    async def test_cost_report(self, groq_monitor):
        """Test cost report generation."""
        # Record some test data
        groq_monitor.record_request(
            GROQModel.LLAMA3_1_8B,
            GROQTaskType.FAST_ANALYSIS,
            response_time=1.5,
            token_count=500,
            cost=0.000025,
            quality_score=0.85,
            success=True
        )
        
        report = groq_monitor.get_cost_report("daily")
        
        assert "cost_timeline" in report
        assert "cost_breakdown" in report
        assert "total_cost" in report
    
    @pytest.mark.asyncio
    async def test_alert_generation(self, groq_monitor):
        """Test alert generation."""
        # Record a request that exceeds thresholds
        groq_monitor.record_request(
            GROQModel.LLAMA3_1_8B,
            GROQTaskType.FAST_ANALYSIS,
            response_time=15.0,  # Exceeds max_response_time
            token_count=500,
            cost=0.000025,
            quality_score=0.85,
            success=True
        )
        
        # Wait for alert processing
        await asyncio.sleep(0.1)
        
        # Check if alert was created
        assert len(groq_monitor.alerts) > 0
    
    @pytest.mark.asyncio
    async def test_metrics_export(self, groq_monitor):
        """Test metrics export."""
        # Record some test data
        groq_monitor.record_request(
            GROQModel.LLAMA3_1_8B,
            GROQTaskType.FAST_ANALYSIS,
            response_time=1.5,
            token_count=500,
            cost=0.000025,
            quality_score=0.85,
            success=True
        )
        
        export_data = await groq_monitor.export_metrics("json")
        
        assert export_data is not None
        assert isinstance(export_data, str)
        assert "performance_metrics" in export_data


class TestIntegration:
    """Test integration between optimizer, router, and monitor."""
    
    @pytest.mark.asyncio
    async def test_full_pipeline(self, groq_optimizer, groq_router, groq_monitor):
        """Test complete pipeline: route -> optimize -> monitor."""
        # Step 1: Route to optimal model
        routing_decision = await groq_router.select_model(
            GROQTaskType.FAST_ANALYSIS,
            RoutingStrategy.ADAPTIVE
        )
        
        assert routing_decision.selected_model is not None
        
        # Step 2: Prepare optimized request
        messages = [
            {"role": "user", "content": "Analyze this contract clause"}
        ]
        
        optimized_messages = groq_optimizer.request_optimizer.optimize_messages(messages)
        
        assert len(optimized_messages) > 0
        
        # Step 3: Record monitoring data
        groq_monitor.record_request(
            routing_decision.selected_model,
            GROQTaskType.FAST_ANALYSIS,
            response_time=routing_decision.estimated_time,
            token_count=500,
            cost=routing_decision.estimated_cost,
            quality_score=0.85,
            success=True
        )
        
        # Verify monitoring data
        dashboard = groq_monitor.get_dashboard_data("1h")
        assert dashboard["summary"]["total_requests"] > 0
    
    @pytest.mark.asyncio
    async def test_optimization_with_routing(self, groq_optimizer, groq_router):
        """Test optimizer using router for model selection."""
        messages = [
            {"role": "user", "content": "Generate code for a sorting algorithm"}
        ]
        
        # Router selects optimal model
        routing_decision = await groq_router.select_model(
            GROQTaskType.CODE_GENERATION,
            RoutingStrategy.QUALITY_FOCUSED
        )
        
        # Optimizer prepares request
        optimized_params = groq_optimizer.request_optimizer.optimize_parameters(
            routing_decision.selected_model,
            GROQTaskType.CODE_GENERATION,
            {"temperature": 0.2, "max_tokens": 2000}
        )
        
        assert optimized_params is not None
        assert "temperature" in optimized_params
    
    @pytest.mark.asyncio
    async def test_monitoring_with_alerts(self, groq_monitor):
        """Test monitoring with alert generation."""
        # Start monitoring
        await groq_monitor.start_monitoring()
        
        # Record some requests
        for i in range(3):
            groq_monitor.record_request(
                GROQModel.LLAMA3_1_8B,
                GROQTaskType.FAST_ANALYSIS,
                response_time=1.0,
                token_count=500,
                cost=0.000025,
                quality_score=0.85,
                success=True
            )
        
        # Wait for monitoring tasks
        await asyncio.sleep(0.5)
        
        # Stop monitoring
        await groq_monitor.stop_monitoring()
        
        # Verify monitoring ran
        assert groq_monitor.is_monitoring == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
