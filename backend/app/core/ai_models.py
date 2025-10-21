"""
Multi-model AI support with confidence scoring and model selection.
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import openai
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from .config import get_settings
from .logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ModelProvider(str, Enum):
	"""AI model providers."""

	OPENAI = "openai"
	ANTHROPIC = "anthropic"
	GOOGLE = "google"
	LOCAL = "local"


class ModelCapability(str, Enum):
	"""Model capabilities."""

	TEXT_GENERATION = "text_generation"
	ANALYSIS = "analysis"
	CLASSIFICATION = "classification"
	SUMMARIZATION = "summarization"


@dataclass
class ModelResponse:
	"""Standardized model response."""

	content: str
	confidence: float
	model_name: str
	provider: str
	tokens_used: int
	cost_estimate: float
	processing_time: float
	metadata: Dict[str, Any]


@dataclass
class ModelConfig:
	"""Model configuration."""

	name: str
	provider: ModelProvider
	capabilities: List[ModelCapability]
	max_tokens: int
	temperature: float
	cost_per_token: float
	priority: int  # Lower number = higher priority


class BaseAIModel(ABC):
	"""Base class for AI models."""

	def __init__(self, config: ModelConfig):
		self.config = config
		self.client = None
		self._initialize_client()

	@abstractmethod
	def _initialize_client(self):
		"""Initialize the model client."""
		pass

	@abstractmethod
	async def generate_response(self, messages: List[BaseMessage], **kwargs) -> ModelResponse:
		"""Generate response from the model."""
		pass

	@abstractmethod
	async def calculate_confidence(self, response: str, context: str) -> float:
		"""Calculate confidence score for the response."""
		pass


class OpenAIModel(BaseAIModel):
	"""OpenAI model implementation."""

	def _initialize_client(self):
		"""Initialize OpenAI client."""
		self.client = ChatOpenAI(
			model=self.config.name,
			temperature=self.config.temperature,
			max_tokens=self.config.max_tokens,
			api_key=settings.openai_api_key.get_secret_value(),
		)

	async def generate_response(self, messages: List[BaseMessage], **kwargs) -> ModelResponse:
		"""Generate response using OpenAI."""
		start_time = time.time()

		try:
			# Generate response
			response = await self.client.ainvoke(messages)
			content = response.content

			# Calculate confidence
			confidence = await self.calculate_confidence(content, messages[0].content)

			# Estimate tokens and cost
			tokens_used = self._estimate_tokens(messages, content)
			cost_estimate = tokens_used * self.config.cost_per_token

			processing_time = time.time() - start_time

			return ModelResponse(
				content=content,
				confidence=confidence,
				model_name=self.config.name,
				provider=ModelProvider.OPENAI,
				tokens_used=tokens_used,
				cost_estimate=cost_estimate,
				processing_time=processing_time,
				metadata={"finish_reason": getattr(response, "finish_reason", None), "model_version": self.config.name},
			)

		except Exception as e:
			logger.error(f"OpenAI model error: {e}")
			raise

	async def calculate_confidence(self, response: str, context: str) -> float:
		"""Calculate confidence score using OpenAI."""
		try:
			# Use a separate call to evaluate confidence
			confidence_prompt = f"""
            Rate the confidence of this response on a scale of 0.0 to 1.0:
            
            Context: {context[:500]}...
            Response: {response}
            
            Consider:
            - Completeness of the response
            - Relevance to the context
            - Clarity and specificity
            - Factual accuracy (if applicable)
            
            Return only a number between 0.0 and 1.0:
            """

			confidence_messages = [
				SystemMessage(content="You are a confidence evaluator. Return only a number between 0.0 and 1.0."),
				HumanMessage(content=confidence_prompt),
			]

			confidence_response = await self.client.ainvoke(confidence_messages)
			confidence_text = confidence_response.content.strip()

			# Extract number from response
			try:
				confidence = float(confidence_text)
				return max(0.0, min(1.0, confidence))  # Clamp between 0 and 1
			except ValueError:
				# Fallback confidence calculation
				return self._fallback_confidence(response, context)

		except Exception as e:
			logger.warning(f"Confidence calculation failed: {e}")
			return self._fallback_confidence(response, context)

	def _fallback_confidence(self, response: str, context: str) -> float:
		"""Fallback confidence calculation based on response characteristics."""
		# Simple heuristics for confidence
		confidence = 0.5  # Base confidence

		# Length factor
		if len(response) > 100:
			confidence += 0.1
		if len(response) > 500:
			confidence += 0.1

		# Specificity factor
		if any(word in response.lower() for word in ["specific", "detailed", "precise"]):
			confidence += 0.1

		# Completeness factor
		if response.endswith(".") and len(response.split(".")) > 2:
			confidence += 0.1

		return min(1.0, confidence)

	def _estimate_tokens(self, messages: List[BaseMessage], response: str) -> int:
		"""Estimate token usage."""
		# Rough estimation: 1 token ≈ 4 characters
		total_chars = sum(len(msg.content) for msg in messages) + len(response)
		return int(total_chars / 4)


class AnthropicModel(BaseAIModel):
	"""Anthropic Claude model implementation (placeholder)."""

	def _initialize_client(self):
		"""Initialize Anthropic client (placeholder)."""
		# TODO: Implement Anthropic client when API key is available
		self.client = None
		logger.warning("Anthropic model not implemented - requires API key")

	async def generate_response(self, messages: List[BaseMessage], **kwargs) -> ModelResponse:
		"""Generate response using Anthropic (placeholder)."""
		raise NotImplementedError("Anthropic model not implemented")

	async def calculate_confidence(self, response: str, context: str) -> float:
		"""Calculate confidence score (placeholder)."""
		return 0.5


class ModelManager:
	"""Manages multiple AI models and model selection."""

	def __init__(self):
		self.models: Dict[str, BaseAIModel] = {}
		self.model_configs = self._get_default_configs()
		self._initialize_models()

	def _get_default_configs(self) -> Dict[str, ModelConfig]:
		"""Get default model configurations."""
		return {
			"gpt-4": ModelConfig(
				name="gpt-4",
				provider=ModelProvider.OPENAI,
				capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.ANALYSIS],
				max_tokens=4000,
				temperature=0.1,
				cost_per_token=0.00003,
				priority=1,
			),
			"gpt-3.5-turbo": ModelConfig(
				name="gpt-3.5-turbo",
				provider=ModelProvider.OPENAI,
				capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.ANALYSIS],
				max_tokens=4000,
				temperature=0.1,
				cost_per_token=0.000002,
				priority=2,
			),
			"claude-3": ModelConfig(
				name="claude-3",
				provider=ModelProvider.ANTHROPIC,
				capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.ANALYSIS],
				max_tokens=4000,
				temperature=0.1,
				cost_per_token=0.000015,
				priority=1,
			),
		}

	def _initialize_models(self):
		"""Initialize available models."""
		for model_name, config in self.model_configs.items():
			try:
				if config.provider == ModelProvider.OPENAI:
					self.models[model_name] = OpenAIModel(config)
				elif config.provider == ModelProvider.ANTHROPIC:
					self.models[model_name] = AnthropicModel(config)
				# Add other providers as needed

				logger.info(f"Initialized model: {model_name}")
			except Exception as e:
				logger.warning(f"Failed to initialize model {model_name}: {e}")

	def get_available_models(self) -> List[str]:
		"""Get list of available models."""
		return list(self.models.keys())

	def get_model_by_capability(self, capability: ModelCapability, preferred_model: Optional[str] = None) -> Optional[BaseAIModel]:
		"""Get model by capability with optional preference."""
		if preferred_model and preferred_model in self.models:
			model = self.models[preferred_model]
			if capability in model.config.capabilities:
				return model

		# Find best model by priority
		available_models = [(name, model) for name, model in self.models.items() if capability in model.config.capabilities]

		if not available_models:
			return None

		# Sort by priority (lower number = higher priority)
		available_models.sort(key=lambda x: x[1].config.priority)
		return available_models[0][1]

	async def generate_with_fallback(
		self,
		messages: List[BaseMessage],
		capability: ModelCapability,
		preferred_model: Optional[str] = None,
		min_confidence: float = 0.7,
		max_attempts: int = 3,
	) -> ModelResponse:
		"""Generate response with fallback models."""
		attempts = 0
		last_error = None

		# Get primary model
		model = self.get_model_by_capability(capability, preferred_model)
		if not model:
			raise ValueError(f"No model available for capability: {capability}")

		models_to_try = [model]

		# Add fallback models
		for model_name, fallback_model in self.models.items():
			if fallback_model != model and capability in fallback_model.config.capabilities:
				models_to_try.append(fallback_model)

		for attempt in range(max_attempts):
			if attempt >= len(models_to_try):
				break

			current_model = models_to_try[attempt]

			try:
				response = await current_model.generate_response(messages)

				# Check confidence threshold
				if response.confidence >= min_confidence:
					logger.info(f"Generated response with {current_model.config.name} (confidence: {response.confidence:.2f})")
					return response
				else:
					logger.warning(f"Low confidence response from {current_model.config.name}: {response.confidence:.2f}")
					if attempt < max_attempts - 1:
						continue
					else:
						# Return low confidence response if it's the last attempt
						return response

			except Exception as e:
				last_error = e
				logger.warning(f"Model {current_model.config.name} failed: {e}")
				continue

		# If all models failed
		if last_error:
			raise last_error
		else:
			raise RuntimeError("All models failed to generate response")

	async def compare_models(
		self, messages: List[BaseMessage], capability: ModelCapability, models_to_compare: Optional[List[str]] = None
	) -> Dict[str, ModelResponse]:
		"""Compare responses from multiple models."""
		if models_to_compare is None:
			models_to_compare = [name for name, model in self.models.items() if capability in model.config.capabilities]

		results = {}
		tasks = []

		for model_name in models_to_compare:
			if model_name in self.models:
				task = self.models[model_name].generate_response(messages)
				tasks.append((model_name, task))

		# Run all models in parallel
		for model_name, task in tasks:
			try:
				response = await task
				results[model_name] = response
			except Exception as e:
				logger.error(f"Model {model_name} comparison failed: {e}")
				results[model_name] = None

		return results


# Global model manager instance
model_manager = ModelManager()


async def get_model_manager() -> ModelManager:
	"""Get the global model manager instance."""
	return model_manager
