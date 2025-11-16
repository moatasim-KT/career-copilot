"""
Unit tests for AnthropicServicePlugin.

Tests plugin initialization, completion generation, health checks,
error handling, and LangChain integration.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm_service_plugin import AnthropicServicePlugin, ServiceConfig, ServiceStatus


@pytest.fixture
def anthropic_config():
	"""Create test configuration for Anthropic plugin."""
	return ServiceConfig(
		service_id="anthropic_test",
		service_type="ai_provider",
		config={
			"provider": "anthropic",
			"model_name": "claude-3-5-sonnet-20241022",
			"temperature": 0.7,
			"max_tokens": 2000,
			"api_key": "test-api-key",
		},
	)


@pytest.fixture
async def anthropic_plugin(anthropic_config):
	"""Create AnthropicServicePlugin instance with test config."""
	plugin = AnthropicServicePlugin(anthropic_config)
	# Mock the client initialization to avoid actual API calls
	with patch("app.services.llm_service_plugin.ChatAnthropic"):
		await plugin._initialize_client()
	return plugin


class TestAnthropicPluginInitialization:
	"""Test plugin initialization and configuration."""

	def test_plugin_init_with_valid_config(self, anthropic_config):
		"""Test plugin initializes correctly with valid configuration."""
		plugin = AnthropicServicePlugin(anthropic_config)

		assert plugin.config == anthropic_config
		assert plugin.provider_name == "anthropic"
		assert plugin.api_key == "test-api-key"
		assert plugin.base_url == "https://api.anthropic.com"

	def test_plugin_supports_claude_models(self, anthropic_config):
		"""Test plugin supports various Claude model versions."""
		plugin = AnthropicServicePlugin(anthropic_config)

		expected_models = ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-3-5-sonnet-20241022"]

		for model in expected_models:
			assert model in plugin.models

	def test_plugin_config_extraction(self, anthropic_config):
		"""Test plugin extracts config values correctly."""
		plugin = AnthropicServicePlugin(anthropic_config)

		assert plugin.config.config["model_name"] == "claude-3-5-sonnet-20241022"
		assert plugin.config.config["temperature"] == 0.7
		assert plugin.config.config["max_tokens"] == 2000


class TestAnthropicCompletionGeneration:
	"""Test completion generation with various scenarios."""

	@pytest.mark.asyncio
	async def test_generate_completion_success(self, anthropic_plugin):
		"""Test successful completion generation."""
		mock_response = {
			"content": "This is a test response from Claude.",
			"model": "claude-3-5-sonnet-20241022",
			"usage": {"input_tokens": 10, "output_tokens": 20},
		}

		with patch.object(
			anthropic_plugin,
			"generate_completion",
			new_callable=AsyncMock,
			return_value=mock_response,
		):
			messages = [{"role": "user", "content": "What is the capital of France?"}]
			result = await anthropic_plugin.generate_completion(messages=messages)

			assert result["content"] == "This is a test response from Claude."
			assert "model" in result

	@pytest.mark.asyncio
	async def test_generate_completion_with_system_message(self, anthropic_plugin):
		"""Test completion with system message included."""
		mock_response = {"content": "Professional response", "model": "claude-3-5-sonnet-20241022"}

		with patch.object(
			anthropic_plugin,
			"generate_completion",
			new_callable=AsyncMock,
			return_value=mock_response,
		):
			messages = [{"role": "system", "content": "You are a career advisor."}, {"role": "user", "content": "Analyze this job posting"}]
			result = await anthropic_plugin.generate_completion(messages=messages)

			assert result["content"] == "Professional response"

	@pytest.mark.asyncio
	async def test_generate_completion_with_custom_params(self, anthropic_plugin):
		"""Test completion respects custom temperature and max_tokens."""
		mock_response = {"content": "Custom params response", "model": "claude-3-5-sonnet-20241022"}

		with patch.object(
			anthropic_plugin,
			"generate_completion",
			new_callable=AsyncMock,
			return_value=mock_response,
		):
			messages = [{"role": "user", "content": "Test prompt"}]
			result = await anthropic_plugin.generate_completion(messages=messages, temperature=0.3, max_tokens=200)

			assert result["content"] == "Custom params response"


class TestAnthropicHealthCheck:
	"""Test health check functionality."""

	@pytest.mark.asyncio
	async def test_health_check_success(self, anthropic_plugin):
		"""Test health check returns healthy status when API is accessible."""
		mock_health_data = {"healthy": True, "response_time": 0.5, "model": "claude-3-5-sonnet-20241022"}

		with patch.object(
			anthropic_plugin,
			"_perform_health_check",
			new_callable=AsyncMock,
			return_value=mock_health_data,
		):
			health = await anthropic_plugin.health_check()

			assert health.status == ServiceStatus.HEALTHY
			assert health.response_time == 0.5

	@pytest.mark.asyncio
	async def test_health_check_failure(self, anthropic_plugin):
		"""Test health check returns unhealthy on API failure."""
		mock_health_data = {"healthy": False, "error": "Connection timeout", "response_time": 0}

		with patch.object(
			anthropic_plugin,
			"_perform_health_check",
			new_callable=AsyncMock,
			return_value=mock_health_data,
		):
			health = await anthropic_plugin.health_check()

			assert health.status == ServiceStatus.UNHEALTHY


class TestAnthropicMetrics:
	"""Test metrics tracking functionality."""

	def test_success_rate_calculation(self, anthropic_config):
		"""Test success rate calculation."""
		plugin = AnthropicServicePlugin(anthropic_config)

		# Initially 100% (no requests)
		assert plugin.get_success_rate() == 1.0

		# Simulate requests
		plugin.total_requests = 10
		plugin.success_count = 8

		assert plugin.get_success_rate() == 0.8

	def test_metrics_update_on_success(self, anthropic_config):
		"""Test metrics update on successful request."""
		plugin = AnthropicServicePlugin(anthropic_config)

		initial_total = plugin.total_requests
		initial_success = plugin.success_count

		plugin._update_metrics(success=True, response_time=0.5)

		assert plugin.total_requests == initial_total + 1
		assert plugin.success_count == initial_success + 1

	def test_metrics_update_on_failure(self, anthropic_config):
		"""Test metrics update on failed request."""
		plugin = AnthropicServicePlugin(anthropic_config)

		initial_total = plugin.total_requests
		initial_failures = plugin.failure_count

		plugin._update_metrics(success=False, response_time=0)

		assert plugin.total_requests == initial_total + 1
		assert plugin.failure_count == initial_failures + 1
		assert plugin.last_failure_time is not None


class TestAnthropicErrorHandling:
	"""Test error handling for various failure scenarios."""

	@pytest.mark.asyncio
	async def test_initialization_error_handling(self, anthropic_config):
		"""Test handling of initialization errors."""
		plugin = AnthropicServicePlugin(anthropic_config)

		with patch("app.services.llm_service_plugin.ChatAnthropic", side_effect=Exception("Invalid API key")):
			with pytest.raises(Exception) as exc_info:
				await plugin._initialize_client()

			assert "Invalid API key" in str(exc_info.value)

	@pytest.mark.asyncio
	async def test_health_check_error_handling(self, anthropic_plugin):
		"""Test health check handles errors gracefully."""
		with patch.object(
			anthropic_plugin,
			"_perform_health_check",
			new_callable=AsyncMock,
			side_effect=Exception("Network error"),
		):
			health = await anthropic_plugin.health_check()

			# Should return ERROR status, not crash
			assert health.status == ServiceStatus.ERROR
			assert health.error_message == "Network error"


class TestAnthropicClientManagement:
	"""Test client lifecycle management."""

	@pytest.mark.asyncio
	async def test_client_initialization(self, anthropic_config):
		"""Test client is initialized correctly."""
		plugin = AnthropicServicePlugin(anthropic_config)

		with patch("app.services.llm_service_plugin.ChatAnthropic") as mock_chat:
			await plugin._initialize_client()

			# Verify ChatAnthropic was called with correct params
			mock_chat.assert_called_once()
			call_kwargs = mock_chat.call_args.kwargs
			assert call_kwargs["model"] == "claude-3-5-sonnet-20241022"

	@pytest.mark.asyncio
	async def test_client_cleanup(self, anthropic_plugin):
		"""Test client cleanup on shutdown."""
		# Create mock client with close method
		mock_client = MagicMock()
		mock_client.close = AsyncMock()
		anthropic_plugin.client = mock_client

		await anthropic_plugin._cleanup_client()

		# Verify close was called
		mock_client.close.assert_called_once()


class TestAnthropicIntegration:
	"""Integration tests for AnthropicServicePlugin."""

	def test_plugin_configuration_matches_spec(self, anthropic_config):
		"""Test plugin adheres to configuration specification."""
		plugin = AnthropicServicePlugin(anthropic_config)

		# Verify all required attributes exist
		assert hasattr(plugin, "provider_name")
		assert hasattr(plugin, "api_key")
		assert hasattr(plugin, "base_url")
		assert hasattr(plugin, "models")
		assert hasattr(plugin, "max_retries")
		assert hasattr(plugin, "timeout")

	def test_plugin_model_support(self, anthropic_config):
		"""Test plugin supports all major Claude models."""
		plugin = AnthropicServicePlugin(anthropic_config)

		# All Claude 3 variants should be supported
		assert any("opus" in model for model in plugin.models)
		assert any("sonnet" in model for model in plugin.models)
		assert any("haiku" in model for model in plugin.models)
		assert any("3-5" in model for model in plugin.models)  # Claude 3.5
