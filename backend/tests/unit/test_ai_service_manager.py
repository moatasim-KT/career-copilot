
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

@pytest.fixture
def ai_service_manager():
    with patch('app.core.config.get_settings') as mock_get_settings, \
         patch('app.core.caching.get_cache_manager') as mock_get_cache_manager:
        
        mock_settings = MagicMock()
        mock_settings.openai_api_key = MagicMock(get_secret_value=lambda: "test_openai_key")
        mock_settings.anthropic_api_key = MagicMock(return_value="test_anthropic_key") # Anthropic API key is not a SecretStr
        mock_settings.groq_api_key = MagicMock(return_value="test_groq_key")
        mock_settings.enable_redis_caching = True
        mock_settings.redis_host = "localhost"
        mock_settings.redis_port = 6379
        mock_settings.redis_password = None
        mock_get_settings.return_value = mock_settings
        
        mock_cache_instance = MagicMock()
        mock_cache_instance.async_get = AsyncMock(return_value=None) # Configure async_get to be an AsyncMock
        mock_get_cache_manager.return_value = mock_cache_instance
        
        # Import AIServiceManager and ModelType after patches are in place
        from app.services.ai_service_manager import AIServiceManager, ModelType
        
        manager = AIServiceManager()
        
        # Patch _create_llm_instance to return a mock LLM client
        mock_llm_client = MagicMock()
        mock_llm_client.ainvoke = AsyncMock()
        manager._create_llm_instance = AsyncMock(return_value=mock_llm_client)
        
        # Patch _call_model_with_performance_tracking to be an AsyncMock
        manager._call_model_with_performance_tracking = AsyncMock()
        
        manager.openai_client = mock_llm_client # Assign the mock client to openai_client for assertions
        manager.anthropic_client = mock_llm_client # Assign the mock client to anthropic_client for assertions
        manager.ModelType = ModelType # Assign ModelType to the manager instance for easier access in tests
        return manager

@pytest.mark.asyncio
async def test_analyze_with_fallback_success(ai_service_manager):
    # Mock the return value of _call_model_with_performance_tracking
    ai_service_manager._call_model_with_performance_tracking.return_value = MagicMock(
        content="OpenAI response",
        model_used="gpt-4",
        provider=ai_service_manager.ModelType.GENERAL,
        confidence_score=0.9,
        processing_time=0.1,
        token_usage={"total_tokens": 30},
        cost=0.01,
        complexity_used=MagicMock(),
        cost_category=MagicMock(),
        budget_impact=MagicMock(),
        metadata=MagicMock()
    )
    
    result = await ai_service_manager.analyze_with_fallback(
        model_type=ai_service_manager.ModelType.GENERAL,
        prompt="test prompt",
        user_id=1
    )
    
    assert result.content == "OpenAI response"
    ai_service_manager._call_model_with_performance_tracking.assert_called_once()

@pytest.mark.asyncio
async def test_analyze_with_fallback_fallback_triggered(ai_service_manager):
    # Simulate OpenAI failure, then Anthropic success
    ai_service_manager._call_model_with_performance_tracking.side_effect = [
        Exception("OpenAI error"), # First call (OpenAI) fails
        MagicMock(
            content="Anthropic response",
            model_used="claude-3",
            provider=ai_service_manager.ModelType.GENERAL,
            confidence_score=0.8,
            processing_time=0.2,
            token_usage={"total_tokens": 40},
            cost=0.02,
            complexity_used=MagicMock(),
            cost_category=MagicMock(),
            budget_impact=MagicMock(),
            metadata=MagicMock()
        ) # Second call (Anthropic) succeeds
    ]
    
    result = await ai_service_manager.analyze_with_fallback(
        model_type=ai_service_manager.ModelType.GENERAL,
        prompt="test prompt",
        user_id=1
    )
    
    assert result.content == "Anthropic response"
    assert ai_service_manager._call_model_with_performance_tracking.call_count == 2

@pytest.mark.asyncio
async def test_analyze_with_fallback_all_fail(ai_service_manager):
    ai_service_manager._call_model_with_performance_tracking.side_effect = Exception("All models fail")
    
    with pytest.raises(Exception, match="All AI models failed"):
        await ai_service_manager.analyze_with_fallback(
        model_type=ai_service_manager.ModelType.GENERAL,
        prompt="test prompt",
        user_id=1
        )
    
    # Assert that _call_model_with_performance_tracking was called multiple times
    assert ai_service_manager._call_model_with_performance_tracking.call_count > 0
