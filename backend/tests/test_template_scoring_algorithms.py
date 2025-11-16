"""
Tests for Template Service Resume Scoring Algorithms
Tests the ATS compatibility, readability scoring, and keyword extraction.
"""

import pytest
from sqlalchemy.orm import Session

from app.models.template import DocumentTemplate
from app.models.user import User
from app.services.template_service import TemplateService


@pytest.fixture
def sample_user(db: Session):
	"""Get the test user created by conftest (id=1)."""
	user = db.query(User).filter(User.id == 1).first()
	return user


@pytest.fixture
def template_service(db: Session):
	"""Create template service instance."""
	return TemplateService(db)


@pytest.fixture
def complete_template(db: Session, sample_user):
	"""Create a complete, well-structured resume template."""
	template = DocumentTemplate(
		user_id=sample_user.id,
		name="Professional Resume",
		description="Complete ATS-friendly template",
		template_content="# Professional Resume\n\n## Header\n{full_name}\n\n## Professional Summary\n{summary_text}\n\n## Work Experience\n{title}\n\n## Skills\n{skills_list}\n\n## Education\n{degree}",
		template_structure={
			"sections": [
				{"id": "header", "title": "Header", "fields": [{"name": "full_name", "type": "text"}]},
				{"id": "summary", "title": "Professional Summary", "fields": [{"name": "summary_text", "type": "textarea"}]},
				{"id": "experience", "title": "Work Experience", "fields": [{"name": "title", "type": "text"}]},
				{"id": "skills", "title": "Skills", "fields": [{"name": "skills_list", "type": "text"}]},
				{"id": "education", "title": "Education", "fields": [{"name": "degree", "type": "text"}]},
			]
		},
	)
	db.add(template)
	db.commit()
	db.refresh(template)
	return template


@pytest.fixture
def incomplete_template(db: Session, sample_user):
	"""Create an incomplete template missing key sections."""
	template = DocumentTemplate(
		user_id=sample_user.id,
		name="Basic Resume",
		description="Missing key sections",
		template_content="# Basic Resume\n\n## Header\n{full_name}\n\n## Other Info\n{info}",
		template_structure={
			"sections": [
				{"id": "header", "title": "Header", "fields": [{"name": "full_name", "type": "text"}]},
				{"id": "custom_section", "title": "Other Info", "fields": [{"name": "info", "type": "text"}]},
			]
		},
	)
	db.add(template)
	db.commit()
	db.refresh(template)
	return template


@pytest.fixture
def complex_formatted_template(db: Session, sample_user):
	"""Create a template with complex formatting (bad for ATS)."""
	template = DocumentTemplate(
		user_id=sample_user.id,
		name="Fancy Resume",
		description="Complex formatting with tables and images",
		template_content="# Fancy Resume\n\n<table><tr><td>{full_name}</td></tr></table>\n\n![Logo](logo.png)\n\n{title}\n\n<div style='column-count: 2'>{skills_list}</div>",
		template_structure={
			"sections": [
				{"id": "header", "title": "Header", "fields": [{"name": "full_name", "type": "text"}], "layout": "table"},
				{"id": "experience", "title": "Experience", "fields": [{"name": "title", "type": "text"}], "image": "logo.png"},
				{"id": "skills", "title": "Skills", "fields": [{"name": "skills_list", "type": "text"}], "column": "two-column"},
			]
		},
	)
	db.add(template)
	db.commit()
	db.refresh(template)
	return template


class TestATSCompatibilityScoring:
	"""Test ATS compatibility scoring algorithm."""

	def test_complete_template_high_score(self, template_service, complete_template):
		"""Test that complete template with all required sections scores high."""
		score = template_service._calculate_ats_score(complete_template)

		assert score >= 90, f"Expected score >= 90, got {score}"
		assert score <= 100, f"Score should not exceed 100, got {score}"

	def test_incomplete_template_penalized(self, template_service, incomplete_template):
		"""Test that template missing required sections is penalized."""
		score = template_service._calculate_ats_score(incomplete_template)

		# Missing experience and skills (2 required sections * 15 points each = -30)
		assert score < 80, f"Incomplete template should score < 80, got {score}"
		assert score >= 0, f"Score should not be negative, got {score}"

	def test_complex_formatting_penalized(self, template_service, complex_formatted_template):
		"""Test that complex formatting (tables, images) is penalized."""
		score = template_service._calculate_ats_score(complex_formatted_template)

		# Should have penalties for table and image
		assert score < 90, f"Complex formatting should score < 90, got {score}"

	def test_score_range(self, template_service, complete_template, incomplete_template):
		"""Test that scores are within valid range (0-100)."""
		complete_score = template_service._calculate_ats_score(complete_template)
		incomplete_score = template_service._calculate_ats_score(incomplete_template)

		assert 0 <= complete_score <= 100
		assert 0 <= incomplete_score <= 100
		assert complete_score > incomplete_score, "Complete template should score higher"


class TestReadabilityScoring:
	"""Test readability scoring algorithm."""

	def test_optimal_section_count_scores_high(self, template_service, complete_template):
		"""Test that templates with 3-8 sections score well."""
		score = template_service._calculate_readability_score(complete_template)

		# 5 sections is optimal
		assert score >= 90, f"Expected score >= 90 for 5 sections, got {score}"

	def test_too_many_sections_penalized(self, db: Session, sample_user, template_service):
		"""Test that templates with too many sections are penalized."""
		# Create template with 12 sections (excessive)
		sections = [{"id": f"section_{i}", "title": f"Section {i}", "fields": []} for i in range(12)]
		template = DocumentTemplate(
			user_id=sample_user.id,
			name="Over-complicated Resume",
			description="Too many sections",
			template_content="# Over-complicated Resume\n\n" + "\n\n".join([f"## Section {i}" for i in range(12)]),
			template_structure={"sections": sections},
		)
		db.add(template)
		db.commit()

		score = template_service._calculate_readability_score(template)

		# Should be penalized: (12 - 8) * 5 = -20 points
		assert score < 90, f"Too many sections should score < 90, got {score}"

	def test_missing_section_headers_penalized(self, db: Session, sample_user, template_service):
		"""Test that sections without headers are penalized."""
		template = DocumentTemplate(
			user_id=sample_user.id,
			name="Headerless Resume",
			description="Missing section titles",
			template_content="# Headerless Resume\n\nSection content without headers",
			template_structure={
				"sections": [
					{"id": "section1", "fields": []},  # No title
					{"id": "section2", "fields": []},  # No title
					{"id": "section3", "title": "Good Section", "fields": []},
				]
			},
		)
		db.add(template)
		db.commit()

		score = template_service._calculate_readability_score(template)

		# Should be penalized: 2 sections * 10 points = -20
		assert score < 90, f"Missing headers should score < 90, got {score}"

	def test_consistent_structure_bonus(self, template_service, complete_template):
		"""Test that consistent structure (all sections have fields) gets bonus."""
		score = template_service._calculate_readability_score(complete_template)

		# Should get +10 bonus for consistency
		assert score >= 100, f"Consistent structure should score high, got {score}"


class TestKeywordDensityExtraction:
	"""Test keyword density extraction."""

	def test_extracts_common_keywords(self, template_service, complete_template):
		"""Test that common keywords are extracted from template."""
		keyword_density = template_service._extract_keyword_density(complete_template)

		assert isinstance(keyword_density, dict)
		# Should find "experience", "skills", "education" in the template
		assert "experience" in keyword_density
		assert "skills" in keyword_density
		assert "education" in keyword_density

	def test_calculates_density_percentage(self, template_service, complete_template):
		"""Test that keyword density is calculated as percentage."""
		keyword_density = template_service._extract_keyword_density(complete_template)

		# All densities should be floats representing percentages
		for keyword, density in keyword_density.items():
			assert isinstance(density, float)
			assert density > 0, f"Density for '{keyword}' should be positive"
			assert density < 100, f"Density for '{keyword}' should be < 100%"

	def test_empty_for_minimal_content(self, template_service, incomplete_template):
		"""Test that minimal content yields few or no keywords."""
		keyword_density = template_service._extract_keyword_density(incomplete_template)

		# Should have few keywords since template is minimal
		assert len(keyword_density) <= 2, f"Minimal template should have <= 2 keywords, got {len(keyword_density)}"


class TestSuggestionGeneration:
	"""Test context-aware suggestion generation."""

	def test_suggestions_for_low_ats_score(self, template_service, incomplete_template):
		"""Test that low ATS score generates relevant suggestions."""
		ats_score = template_service._calculate_ats_score(incomplete_template)
		readability = template_service._calculate_readability_score(incomplete_template)

		suggestions = template_service._generate_suggestions(incomplete_template, ats_score, readability)

		assert len(suggestions) > 0
		assert len(suggestions) <= 5, "Should return max 5 suggestions"

		# Should suggest improving ATS compatibility
		suggestion_text = " ".join(suggestions).lower()
		assert "ats" in suggestion_text or "section" in suggestion_text

	def test_suggests_missing_sections(self, template_service, incomplete_template):
		"""Test that missing required sections generate specific suggestions."""
		ats_score = template_service._calculate_ats_score(incomplete_template)
		readability = template_service._calculate_readability_score(incomplete_template)

		suggestions = template_service._generate_suggestions(incomplete_template, ats_score, readability)

		suggestion_text = " ".join(suggestions).lower()
		# Should suggest adding experience and skills
		assert "experience" in suggestion_text or "skills" in suggestion_text

	def test_limits_to_top_5_suggestions(self, template_service, incomplete_template):
		"""Test that suggestions are limited to top 5."""
		ats_score = 50  # Low score will generate many suggestions
		readability = 50

		suggestions = template_service._generate_suggestions(incomplete_template, ats_score, readability)

		assert len(suggestions) <= 5, f"Should return max 5 suggestions, got {len(suggestions)}"

	def test_all_suggestions_are_strings(self, template_service, complete_template):
		"""Test that all suggestions are valid strings."""
		ats_score = template_service._calculate_ats_score(complete_template)
		readability = template_service._calculate_readability_score(complete_template)

		suggestions = template_service._generate_suggestions(complete_template, ats_score, readability)

		for suggestion in suggestions:
			assert isinstance(suggestion, str)
			assert len(suggestion) > 0, "Suggestion should not be empty"


class TestTemplateAnalysisIntegration:
	"""Test the complete analyze_template method integration."""

	def test_complete_analysis_structure(self, template_service, complete_template):
		"""Test that analyze_template returns complete analysis."""
		analysis = template_service.analyze_template(complete_template.id, complete_template.user_id)

		assert hasattr(analysis, "ats_compatibility")
		assert hasattr(analysis, "readability_score")
		assert hasattr(analysis, "keyword_density")
		assert hasattr(analysis, "suggestions")
		assert hasattr(analysis, "missing_sections")

	def test_analysis_with_complete_template(self, template_service, complete_template):
		"""Test analysis of complete, well-structured template."""
		analysis = template_service.analyze_template(complete_template.id, complete_template.user_id)

		assert analysis.ats_compatibility >= 90
		assert analysis.readability_score >= 90
		assert len(analysis.missing_sections) == 0, "Complete template should have no missing sections"
		assert isinstance(analysis.keyword_density, dict)
		assert len(analysis.suggestions) > 0, "Should always provide some suggestions"

	def test_analysis_with_incomplete_template(self, template_service, incomplete_template):
		"""Test analysis identifies issues in incomplete template."""
		analysis = template_service.analyze_template(incomplete_template.id, incomplete_template.user_id)

		assert analysis.ats_compatibility < 90, "Incomplete template should score lower"
		assert len(analysis.missing_sections) > 0, "Should identify missing sections"

		# Should identify experience and skills as missing
		missing = analysis.missing_sections
		assert "experience" in missing or "skills" in missing

	def test_analysis_provides_actionable_suggestions(self, template_service, incomplete_template):
		"""Test that suggestions are specific and actionable."""
		analysis = template_service.analyze_template(incomplete_template.id, incomplete_template.user_id)

		# Should have multiple actionable suggestions
		assert len(analysis.suggestions) >= 3

		for suggestion in analysis.suggestions:
			# Suggestions should be specific actions
			assert len(suggestion) > 20, f"Suggestion too short: '{suggestion}'"
			assert any(word in suggestion.lower() for word in ["add", "include", "consider", "ensure", "use"]), (
				f"Suggestion should contain action word: '{suggestion}'"
			)
