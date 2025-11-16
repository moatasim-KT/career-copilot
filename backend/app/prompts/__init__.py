"""
Prompt Registry and Template Management System

This module provides centralized prompt template management with version control,
A/B testing support, and metadata tracking for all LLM prompts.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, Template

from ..core.logging import get_logger

logger = get_logger(__name__)


class PromptCategory(Enum):
	"""Categories of prompts for organization."""

	COVER_LETTER = "cover_letters"
	EMAIL = "emails"
	RESUME = "resumes"
	IMPROVEMENT = "improvement"
	ANALYSIS = "analysis"
	NEGOTIATION = "negotiation"
	INTERVIEW = "interview"
	GENERAL = "general"


class PromptTone(Enum):
	"""Tone options for prompts."""

	PROFESSIONAL = "professional"
	CASUAL = "casual"
	ENTHUSIASTIC = "enthusiastic"
	CONFIDENT = "confident"
	CREATIVE = "creative"


@dataclass
class PromptMetadata:
	"""Metadata for a prompt template."""

	name: str
	category: PromptCategory
	version: str
	description: str
	author: str = "system"
	created_at: datetime = field(default_factory=datetime.utcnow)
	updated_at: datetime = field(default_factory=datetime.utcnow)

	# Template properties
	input_variables: List[str] = field(default_factory=list)
	output_format: str = "text"  # "text", "json", "markdown"
	estimated_tokens: int = 500

	# Usage tracking
	usage_count: int = 0
	success_rate: float = 0.0
	average_tokens: int = 0

	# A/B testing
	is_active: bool = True
	ab_test_group: Optional[str] = None
	performance_score: float = 0.0

	# Tags and metadata
	tags: List[str] = field(default_factory=list)
	model_recommendations: List[str] = field(default_factory=list)
	custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptTemplate:
	"""A versioned prompt template with metadata."""

	id: str
	content: str
	metadata: PromptMetadata
	template_obj: Optional[Template] = None

	def __post_init__(self):
		"""Initialize Jinja2 template."""
		if not self.template_obj:
			self.template_obj = Template(self.content)

	def render(self, **kwargs) -> str:
		"""Render the template with provided variables.

		Args:
			**kwargs: Template variables

		Returns:
			Rendered prompt string
		"""
		return self.template_obj.render(**kwargs)

	def validate_inputs(self, **kwargs) -> bool:
		"""Validate that all required input variables are provided.

		Args:
			**kwargs: Input variables to validate

		Returns:
			True if all required variables present, False otherwise
		"""
		missing = set(self.metadata.input_variables) - set(kwargs.keys())
		if missing:
			logger.warning(f"Missing required variables: {missing}")
			return False
		return True

	def to_dict(self) -> Dict[str, Any]:
		"""Convert to dictionary for serialization."""
		return {
			"id": self.id,
			"content": self.content,
			"metadata": {
				"name": self.metadata.name,
				"category": self.metadata.category.value,
				"version": self.metadata.version,
				"description": self.metadata.description,
				"author": self.metadata.author,
				"created_at": self.metadata.created_at.isoformat(),
				"updated_at": self.metadata.updated_at.isoformat(),
				"input_variables": self.metadata.input_variables,
				"output_format": self.metadata.output_format,
				"estimated_tokens": self.metadata.estimated_tokens,
				"usage_count": self.metadata.usage_count,
				"success_rate": self.metadata.success_rate,
				"average_tokens": self.metadata.average_tokens,
				"is_active": self.metadata.is_active,
				"ab_test_group": self.metadata.ab_test_group,
				"performance_score": self.metadata.performance_score,
				"tags": self.metadata.tags,
				"model_recommendations": self.metadata.model_recommendations,
				"custom_metadata": self.metadata.custom_metadata,
			},
		}


class PromptRegistry:
	"""Central registry for managing prompt templates with versioning."""

	def __init__(self, prompts_dir: Optional[Path] = None):
		"""Initialize the prompt registry.

		Args:
			prompts_dir: Directory containing prompt templates
		"""
		self.prompts_dir = prompts_dir or Path(__file__).parent
		self.templates: Dict[str, Dict[str, PromptTemplate]] = {}  # {name: {version: template}}
		self.jinja_env = Environment(loader=FileSystemLoader(str(self.prompts_dir)), autoescape=False)  # nosec B701

		self._load_templates()

	def _load_templates(self) -> None:
		"""Load all templates from the prompts directory."""
		logger.info(f"Loading prompt templates from {self.prompts_dir}")

		for category in PromptCategory:
			category_dir = self.prompts_dir / category.value
			if category_dir.exists():
				self._load_category_templates(category, category_dir)

	def _load_category_templates(self, category: PromptCategory, category_dir: Path) -> None:
		"""Load templates for a specific category.

		Args:
			category: Prompt category
			category_dir: Directory containing category templates
		"""
		for template_file in category_dir.glob("*.j2"):
			try:
				# Load template content
				content = template_file.read_text()

				# Load metadata from companion JSON file
				metadata_file = template_file.with_suffix(".json")
				if metadata_file.exists():
					metadata_dict = json.loads(metadata_file.read_text())
					metadata = self._parse_metadata(category, metadata_dict)
				else:
					# Create default metadata
					metadata = PromptMetadata(
						name=template_file.stem, category=category, version="1.0.0", description=f"Template for {template_file.stem}"
					)

				# Generate template ID
				template_id = self._generate_template_id(metadata.name, metadata.version)

				# Create template
				template = PromptTemplate(id=template_id, content=content, metadata=metadata)

				# Register template
				if metadata.name not in self.templates:
					self.templates[metadata.name] = {}
				self.templates[metadata.name][metadata.version] = template

				logger.debug(f"Loaded template: {metadata.name} v{metadata.version}")

			except Exception as e:
				logger.error(f"Failed to load template {template_file}: {e}")

	def _parse_metadata(self, category: PromptCategory, metadata_dict: Dict) -> PromptMetadata:
		"""Parse metadata dictionary into PromptMetadata object.

		Args:
			category: Prompt category
			metadata_dict: Metadata dictionary from JSON

		Returns:
			PromptMetadata object
		"""
		return PromptMetadata(
			name=metadata_dict["name"],
			category=category,
			version=metadata_dict.get("version", "1.0.0"),
			description=metadata_dict.get("description", ""),
			author=metadata_dict.get("author", "system"),
			input_variables=metadata_dict.get("input_variables", []),
			output_format=metadata_dict.get("output_format", "text"),
			estimated_tokens=metadata_dict.get("estimated_tokens", 500),
			tags=metadata_dict.get("tags", []),
			model_recommendations=metadata_dict.get("model_recommendations", []),
			custom_metadata=metadata_dict.get("custom_metadata", {}),
		)

	def _generate_template_id(self, name: str, version: str) -> str:
		"""Generate unique template ID.

		Args:
			name: Template name
			version: Version string

		Returns:
			Unique template ID
		"""
		content = f"{name}:{version}"
		return hashlib.sha256(content.encode()).hexdigest()[:16]

	def register_template(self, name: str, content: str, metadata: PromptMetadata) -> PromptTemplate:
		"""Register a new prompt template.

		Args:
			name: Template name
			content: Template content (Jinja2 format)
			metadata: Template metadata

		Returns:
			Registered PromptTemplate
		"""
		template_id = self._generate_template_id(name, metadata.version)

		template = PromptTemplate(id=template_id, content=content, metadata=metadata)

		if name not in self.templates:
			self.templates[name] = {}

		self.templates[name][metadata.version] = template
		logger.info(f"Registered template: {name} v{metadata.version}")

		return template

	def get_template(self, name: str, version: str = "latest") -> Optional[PromptTemplate]:
		"""Get a specific prompt template.

		Args:
			name: Template name
			version: Version string or "latest"

		Returns:
			PromptTemplate if found, None otherwise
		"""
		if name not in self.templates:
			logger.warning(f"Template not found: {name}")
			return None

		if version == "latest":
			# Get highest version number
			versions = sorted(self.templates[name].keys(), reverse=True)
			version = versions[0] if versions else None

		if version and version in self.templates[name]:
			return self.templates[name][version]

		logger.warning(f"Template version not found: {name} v{version}")
		return None

	def list_templates(self, category: Optional[PromptCategory] = None, tags: Optional[List[str]] = None) -> List[PromptTemplate]:
		"""List all registered templates with optional filtering.

		Args:
			category: Filter by category
			tags: Filter by tags (any match)

		Returns:
			List of matching templates
		"""
		results = []

		for name, versions in self.templates.items():
			for version, template in versions.items():
				# Apply category filter
				if category and template.metadata.category != category:
					continue

				# Apply tags filter
				if tags and not any(tag in template.metadata.tags for tag in tags):
					continue

				results.append(template)

		return results

	def get_versions(self, name: str) -> List[str]:
		"""Get all versions of a template.

		Args:
			name: Template name

		Returns:
			List of version strings
		"""
		if name not in self.templates:
			return []
		return sorted(self.templates[name].keys(), reverse=True)

	def update_usage_stats(self, name: str, version: str, success: bool, tokens_used: int) -> None:
		"""Update usage statistics for a template.

		Args:
			name: Template name
			version: Version string
			success: Whether the prompt execution was successful
			tokens_used: Number of tokens used
		"""
		template = self.get_template(name, version)
		if not template:
			return

		metadata = template.metadata
		metadata.usage_count += 1

		# Update success rate (exponential moving average)
		alpha = 0.1  # Weight for new observation
		if success:
			metadata.success_rate = metadata.success_rate * (1 - alpha) + alpha
		else:
			metadata.success_rate = metadata.success_rate * (1 - alpha)

		# Update average tokens (exponential moving average)
		metadata.average_tokens = int(metadata.average_tokens * (1 - alpha) + tokens_used * alpha)

		metadata.updated_at = datetime.utcnow()

	def export_registry(self, output_path: Path) -> None:
		"""Export registry to JSON file.

		Args:
			output_path: Path to save registry JSON
		"""
		registry_data = {
			"templates": {name: {version: template.to_dict() for version, template in versions.items()} for name, versions in self.templates.items()},
			"export_time": datetime.utcnow().isoformat(),
		}

		output_path.write_text(json.dumps(registry_data, indent=2))
		logger.info(f"Exported registry to {output_path}")


# Global registry instance
_prompt_registry: Optional[PromptRegistry] = None


def get_prompt_registry() -> PromptRegistry:
	"""Get the global prompt registry instance.

	Returns:
		Global PromptRegistry instance
	"""
	global _prompt_registry
	if _prompt_registry is None:
		_prompt_registry = PromptRegistry()
	return _prompt_registry
