"""
Integration tests for the consolidated LLM service.
Tests AI operations, configuration integration, and end-to-end functionality.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import tempfile
import os

from app.services.llm_service import LLMService, ModelType, ModelProvider, get_llm_service
from app.services.llm_config_manager import LLMOperationsManager, get_llm_operations_manager
from app.core.task_complexity import TaskComplexity
from app.core.cost_tracker import CostCategory


@pytest.fixture
def mock_external_dependencies():
    """Mock all external dependencies for integration testing."""
    with patch('app.services.llm_service.get_settings') as mock_settings, \
         patch('app.services.llm_service.get_cache_service') as mock_cache, \
         patch('app.services.llm_service.get_complexity_analyzer') as mock_complexity, \
         patch('app.services.llm_service.get_cost_tracker') as mock_cost, \
         patch('app.services.llm_service.get_metrics_collector') as mock_metrics, \
         patch('app.services.llm_service.get_performance_metrics_collector') as mock_perf, \
         patch('app.services.llm_service.get_streaming_manager') as mock_stream, \
         patch('app.services.llm_service.get_token_optimizer') as mock_token, \
         patch('app.services.llm_config_manager.get_settings') as mock_config_settings, \
         patch('app.services.llm_config_manager.get_cache_service') as mock_config_cache:
        
        # Configure LLM service settings
        settings = MagicMock()
        settings.openai_api_key = MagicMock()
        settings.openai_api_key.get_secret_value.return_value = "test_openai_key"
        settings.anthropic_api_key = "test_anthropic_key"
        settings.groq_api_key = MagicMock()
        settings.groq_api_key.get_secret_value.return_value = "test_groq_key"
        mock_settings.return_value = settings
        mock_config_settings.return_value = settings
        
        # Configure cache service
        cache_service = MagicMock()
        cache_service.aget = AsyncMock(return_value=None)
        cache_service.aset = AsyncMock(return_value=True)
        mock_cache.return_value = cache_service
        mock_config_cache.return_value = cache_service
        
        # Configure complexity analyzer
        complexity_analyzer = MagicMock()
        complexity_analyzer.analyze_task_complexity.return_value = TaskComplexity.SIMPLE
        mock_complexity.return_value = complexity_analyzer
        
        # Configure other services
        mock_cost.return_value = MagicMock()
        mock_metrics.return_value = MagicMock()
        mock_perf.return_value = MagicMock()
        mock_stream.return_value = MagicMock()
        mock_token.return_value = MagicMock()
        
        yield {
            'settings': settings,
            'cache': cache_service,
            'complexity': complexity_analyzer
        }


@pytest.fixture
def integrated_llm_service(mock_external_dependencies):
    """Create integrated LLM service with mocked external calls."""
    service = LLMService()
    
    # Mock the actual LLM calls
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Integration test response"
    mock_response.response_metadata = {
        'token_usage': {
            'prompt_tokens': 15,
            'completion_tokens': 25,
            'total_tokens': 40
        }
    }
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)
    service._create_llm_instance = AsyncMock(return_value=mock_llm)
    
    return service


@pytest.fixture
def temp_config_for_integration():
    """Create temporary config file for integration testing."""
    config_data = {
        "providers": {
            "test-openai-gpt4": {
                "provider": "openai",
                "model_name": "gpt-4",
                "temperature": 0.1,
                "max_tokens": 2000,
                "cost_per_token": 0.01,
                "priority": 1,
                "capabilities": ["analysis", "reasoning"],
                "enabled": True
            },
            "test-openai-gpt35": {
                "provider": "openai",
                "model_name": "gpt-3.5-turbo",
                "temperature": 0.2,
                "max_tokens": 1000,
                "cost_per_token": 0.001,
                "priority": 2,
                "capabilities": ["generation"],
                "enabled": True
            }
        },
        "task_routing": {
            "contract_analysis": ["test-openai-gpt4", "test-openai-gpt35"],
            "general": ["test-openai-gpt35", "test-openai-gpt4"]
        },
        "default_routing_criteria": "cost",
        "cache_ttl": 1800,
        "max_retries": 2,
        "fallback_enabled": True,
        "circuit_breaker_threshold": 3,
        "circuit_breaker_timeout": 30
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def integrated_operations_manager(temp_config_for_integration, mock_external_dependencies):
    """Create integrated operations manager."""
    return LLMOperationsManager(config_path=temp_config_for_integration)


class TestLLMServiceIntegration:
    """Integration tests for LLM service functionality."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_analysis_workflow(self, integrated_llm_service):
        """Test complete analysis workflow from request to response."""
        # Test contract analysis workflow
        result = await integrated_llm_service.analyze_with_fallback(
            model_type=ModelType.CONTRACT_ANALYSIS,
            prompt="Analyze the risks in this employment contract clause: 'Employee agrees to work exclusively for the company.'",
            context="You are a legal expert specializing in employment law.",
            user_id="test_user_123"
        )
        
        # Verify response structure
        assert result is not None
        assert hasattr(result, 'content')
        assert hasattr(result, 'model_used')
        assert hasattr(result, 'provider')
        assert hasattr(result, 'token_usage')
        assert hasattr(result, 'cost')
        assert hasattr(result, 'processing_time')
        
        # Verify response content
        assert result.content == "Integration test response"
        assert result.token_usage['total_tokens'] == 40
        assert result.processing_time >= 0
        assert result.cost >= 0
    
    @pytest.mark.asyncio
    async def test_multiple_model_types_integration(self, integrated_llm_service):
        """Test integration across different model types."""
        test_cases = [
            (ModelType.CONTRACT_ANALYSIS, "Analyze this contract clause"),
            (ModelType.GENERAL, "What is the weather like?"),
            (ModelType.COMMUNICATION, "Write a professional email"),
            (ModelType.NEGOTIATION, "Suggest negotiation strategies")
        ]
        
        results = []
        for model_type, prompt in test_cases:
            result = await integrated_llm_service.analyze_with_fallback(
                model_type=model_type,
                prompt=prompt
            )
            results.append((model_type, result))
        
        # Verify all requests completed successfully
        assert len(results) == 4
        for model_type, result in results:
            assert result is not None
            assert result.content == "Integration test response"
            assert result.complexity_used is not None
    
    @pytest.mark.asyncio
    async def test_error_handling_and_fallback_integration(self, integrated_llm_service):
        """Test error handling and fallback mechanisms."""
        # Mock first provider to fail, second to succeed
        call_count = 0
        
        async def mock_failing_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First provider failed")
            else:
                mock_response = MagicMock()
                mock_response.content = "Fallback response"
                mock_response.response_metadata = {
                    'token_usage': {'prompt_tokens': 10, 'completion_tokens': 20, 'total_tokens': 30}
                }
                return mock_response
        
        # Replace the mock with failing behavior
        integrated_llm_service._create_llm_instance = AsyncMock(side_effect=lambda config: MagicMock(ainvoke=mock_failing_call))
        
        result = await integrated_llm_service.analyze_with_fallback(
            model_type=ModelType.GENERAL,
            prompt="Test fallback mechanism"
        )
        
        # Verify fallback worked
        assert result is not None
        assert call_count >= 2  # At least one failure and one success
    
    @pytest.mark.asyncio
    async def test_caching_integration(self, integrated_llm_service, mock_external_dependencies):
        """Test caching integration across service calls."""
        prompt = "What are the key elements of a valid contract?"
        
        # First call - should not be cached
        result1 = await integrated_llm_service.analyze_with_fallback(
            model_type=ModelType.CONTRACT_ANALYSIS,
            prompt=prompt
        )
        
        # Verify cache was called for storage
        mock_external_dependencies['cache'].aset.assert_called()
        
        # Mock cache to return cached response for second call
        cached_response = result1
        mock_external_dependencies['cache'].aget.return_value = cached_response
        
        # Second call - should use cache
        result2 = await integrated_llm_service.analyze_with_fallback(
            model_type=ModelType.CONTRACT_ANALYSIS,
            prompt=prompt
        )
        
        # Verify cache was checked
        mock_external_dependencies['cache'].aget.assert_called()
        assert result2 == cached_response
    
    @pytest.mark.asyncio
    async def test_legacy_compatibility_integration(self, integrated_llm_service):
        """Test legacy generate_response method integration."""
        result = await integrated_llm_service.generate_response(
            "Generate a summary of contract terms",
            model_type=ModelType.CONTRACT_ANALYSIS,
            context="You are a legal assistant"
        )
        
        assert isinstance(result, str)
        assert result == "Integration test response"
    
    def test_service_health_integration(self, integrated_llm_service):
        """Test service health monitoring integration."""
        health = integrated_llm_service.get_service_health()
        
        assert isinstance(health, dict)
        assert len(health) > 0
        
        # Verify all providers have health status
        for provider_name, status in health.items():
            assert 'state' in status
            assert 'failure_count' in status
            assert 'available' in status
            assert status['state'] in ['closed', 'open', 'half-open']


class TestLLMOperationsManagerIntegration:
    """Integration tests for LLM operations manager."""
    
    def test_config_and_cache_integration(self, integrated_operations_manager):
        """Test configuration and cache system integration."""
        # Verify config loaded correctly
        config = integrated_operations_manager.get_config()
        assert config is not None
        assert len(config.providers) == 2
        assert "test-openai-gpt4" in config.providers
        assert "test-openai-gpt35" in config.providers
        
        # Verify cache system initialized
        assert integrated_operations_manager.cache_entries is not None
        assert integrated_operations_manager.similarity_matcher is not None
        assert integrated_operations_manager.cache_optimizer is not None
    
    @pytest.mark.asyncio
    async def test_cache_operations_integration(self, integrated_operations_manager):
        """Test cache operations integration."""
        messages = [{"role": "user", "content": "Test integration message"}]
        model = "gpt-3.5-turbo"
        response = {
            "content": "This is a comprehensive response for integration testing",
            "success": True
        }
        
        # Test caching
        cache_result = await integrated_operations_manager.cache_response(
            messages=messages,
            model=model,
            response=response,
            temperature=0.1,
            task_type="contract_analysis"
        )
        
        assert cache_result is True
        assert len(integrated_operations_manager.cache_entries) == 1
        
        # Test retrieval
        cached_response = await integrated_operations_manager.get_cached_response(
            messages=messages,
            model=model,
            temperature=0.1
        )
        
        assert cached_response is not None
        assert cached_response["content"] == response["content"]
        assert cached_response["cached"] is True
    
    @pytest.mark.asyncio
    async def test_benchmark_integration(self, integrated_operations_manager):
        """Test benchmark system integration."""
        # Mock provider function for testing
        async def mock_provider_func(messages, **kwargs):
            return {
                "content": "Benchmark test response with analysis and important findings",
                "success": True,
                "model": "test-model",
                "tokens_used": 50,
                "response_time": 0.5
            }
        
        # Get contract analysis tests
        contract_tests = integrated_operations_manager.benchmark_test_suite.get_test_suite("contract_analysis")
        assert len(contract_tests) > 0
        
        # Run benchmark on subset of tests for integration testing
        test_subset = contract_tests[:2]  # Use first 2 tests for faster integration testing
        
        benchmark_result = await integrated_operations_manager.run_benchmark(
            provider_func=mock_provider_func,
            provider_name="test-provider",
            model="test-model",
            tests=test_subset
        )
        
        # Verify benchmark results
        assert benchmark_result is not None
        assert benchmark_result.provider == "test-provider"
        assert benchmark_result.model == "test-model"
        assert benchmark_result.total_tests == len(test_subset)
        assert benchmark_result.successful_tests >= 0
        assert benchmark_result.overall_score >= 0.0
        assert len(benchmark_result.test_results) == len(test_subset)
    
    def test_quality_evaluation_integration(self, integrated_operations_manager):
        """Test quality evaluation integration."""
        evaluator = integrated_operations_manager.quality_evaluator
        
        # Create test benchmark
        from app.services.llm_config_manager import BenchmarkTest
        test = BenchmarkTest(
            test_id="integration_test",
            name="Integration Test",
            description="Test quality evaluation",
            messages=[{"role": "user", "content": "Analyze contract risks"}],
            expected_keywords=["risk", "analysis", "contract", "liability"]
        )
        
        # Test response with good quality
        good_response = """
        This comprehensive analysis shows several important risk factors in the contract.
        The liability clauses present significant risks to the contracting party.
        Key areas of concern include indemnification requirements and limitation of liability.
        The contract analysis reveals potential exposure in multiple areas.
        """
        
        quality_score = evaluator.evaluate_response(good_response, test)
        
        assert 0.0 <= quality_score <= 1.0
        assert quality_score > 0.6  # Should be a good score due to keyword matches and structure


class TestServiceInteroperability:
    """Test interoperability between LLM service and operations manager."""
    
    @pytest.mark.asyncio
    async def test_service_and_manager_integration(self, integrated_llm_service, integrated_operations_manager):
        """Test integration between LLM service and operations manager."""
        # Test that both services can work together
        
        # Get configuration from operations manager
        config = integrated_operations_manager.get_config()
        assert config is not None
        
        # Use LLM service for analysis
        result = await integrated_llm_service.analyze_with_fallback(
            model_type=ModelType.CONTRACT_ANALYSIS,
            prompt="Test interoperability between services"
        )
        
        assert result is not None
        assert result.content == "Integration test response"
        
        # Test that operations manager can cache the result
        messages = [{"role": "user", "content": "Test interoperability between services"}]
        cache_result = await integrated_operations_manager.cache_response(
            messages=messages,
            model=result.model_used,
            response={"content": result.content, "success": True}
        )
        
        assert cache_result is True
    
    def test_singleton_integration(self):
        """Test that singleton instances work correctly in integration."""
        with patch('app.services.llm_service.get_settings'), \
             patch('app.services.llm_service.get_cache_service'), \
             patch('app.services.llm_service.get_complexity_analyzer'), \
             patch('app.services.llm_service.get_cost_tracker'), \
             patch('app.services.llm_service.get_metrics_collector'), \
             patch('app.services.llm_service.get_performance_metrics_collector'), \
             patch('app.services.llm_service.get_streaming_manager'), \
             patch('app.services.llm_service.get_token_optimizer'), \
             patch('app.services.llm_config_manager.get_settings'), \
             patch('app.services.llm_config_manager.get_cache_service'):
            
            # Test LLM service singleton
            service1 = get_llm_service()
            service2 = get_llm_service()
            assert service1 is service2
            
            # Test operations manager singleton
            manager1 = get_llm_operations_manager()
            manager2 = get_llm_operations_manager()
            assert manager1 is manager2
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, integrated_llm_service):
        """Test service performance under concurrent load."""
        # Create multiple concurrent requests
        tasks = []
        for i in range(5):  # Reduced from 10 for faster testing
            task = integrated_llm_service.analyze_with_fallback(
                model_type=ModelType.GENERAL,
                prompt=f"Test concurrent request {i}",
                user_id=f"user_{i}"
            )
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all requests completed successfully
        assert len(results) == 5
        for i, result in enumerate(results):
            assert not isinstance(result, Exception), f"Request {i} failed: {result}"
            assert result.content == "Integration test response"
    
    @pytest.mark.asyncio
    async def test_error_recovery_integration(self, integrated_llm_service):
        """Test error recovery and circuit breaker integration."""
        # Test circuit breaker functionality
        provider = "openai"
        circuit_breaker = integrated_llm_service.circuit_breakers[provider]
        
        # Verify initial state
        assert circuit_breaker.state == "closed"
        assert circuit_breaker.can_attempt() is True
        
        # Simulate failures
        for _ in range(5):  # Default threshold
            circuit_breaker.record_failure()
        
        # Verify circuit opened
        assert circuit_breaker.state == "open"
        assert circuit_breaker.can_attempt() is False
        
        # Test recovery
        circuit_breaker.record_success()
        assert circuit_breaker.state == "closed"
        assert circuit_breaker.can_attempt() is True