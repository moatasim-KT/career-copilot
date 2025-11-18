"""
Multi-language text processing service for Phase 3.3.
Handles language detection, normalization, and translation support.
"""

import re
from typing import ClassVar, Dict, List, Optional

from langdetect import LangDetectException, detect


class LanguageProcessor:
	"""Process and normalize multilingual job content."""

	# Supported languages
	SUPPORTED_LANGUAGES: ClassVar[set[str]] = {"en", "de", "fr", "it", "es"}

	# Language level normalization
	LEVEL_MAPPING: ClassVar[Dict[str, str]] = {
		# English
		"native": "Native",
		"fluent": "Fluent",
		"working": "Working",
		"basic": "Basic",
		# German
		"muttersprache": "Native",
		"fliessend": "Fluent",
		"verhandlungssicher": "Fluent",
		"gut": "Working",
		"grundkenntnisse": "Basic",
		# French
		"langue maternelle": "Native",
		"courant": "Fluent",
		"professionnel": "Working",
		"notions": "Basic",
	}

	def __init__(self):
		"""Initialize language processor."""
		pass

	def detect_language(self, text: str) -> str:
		"""
		Detect language of text.

		Args:
		    text: Text to analyze

		Returns:
		    ISO 639-1 language code (en, de, fr, it, es)
		"""
		if not text or len(text.strip()) < 10:
			return "en"  # Default to English

		try:
			lang = detect(text)
			if lang in self.SUPPORTED_LANGUAGES:
				return lang
			return "en"
		except LangDetectException:
			return "en"

	def normalize_language_requirements(self, languages: List[str]) -> List[str]:
		"""
		Normalize language requirement strings.

		Args:
		    languages: Raw language requirements

		Returns:
		    Normalized list like ["German (Fluent)", "English (Working)"]
		"""
		if not languages:
			return []

		normalized = []
		for lang in languages:
			# Extract language and level
			# Examples: "German (fluent)", "Deutsch (fliessend)", "French"
			match = re.search(r"([A-Za-zäöüß]+)\s*\(?([A-Za-zäöüß\s]*)\)?", lang)
			if match:
				language_name = match.group(1).strip()
				level = match.group(2).strip().lower() if match.group(2) else "working"

				# Normalize language name
				language_name = self._normalize_language_name(language_name)

				# Normalize level
				level_normalized = self.LEVEL_MAPPING.get(level.lower(), level.title())

				if level_normalized:
					normalized.append(f"{language_name} ({level_normalized})")
				else:
					normalized.append(language_name)

		return normalized

	def _normalize_language_name(self, name: str) -> str:
		"""Normalize language names to English."""
		name_map = {
			"deutsch": "German",
			"englisch": "English",
			"französisch": "French",
			"francais": "French",
			"italiano": "Italian",
			"espanol": "Spanish",
			"español": "Spanish",
		}
		return name_map.get(name.lower(), name.title())

	def normalize_company_name(self, name: str, source: Optional[str] = None) -> str:
		"""
		Normalize company names by removing legal suffixes.

		Args:
		    name: Company name
		    source: Source board (for country-specific normalization)

		Returns:
		    Normalized company name
		"""
		if not name:
			return name

		# German suffixes (XING, JobScout24)
		german_suffixes = [
			r"\s+GmbH\s*$",
			r"\s+AG\s*$",
			r"\s+KG\s*$",
			r"\s+GmbH\s*&\s*Co\.\s*KG\s*$",
			r"\s+mbH\s*$",
		]

		# French suffixes (Welcome to the Jungle)
		french_suffixes = [
			r"\s+SAS\s*$",
			r"\s+SARL\s*$",
			r"\s+SA\s*$",
		]

		# Swiss suffixes (JobScout24)
		swiss_suffixes = german_suffixes  # Same as German

		# English suffixes (AngelList)
		english_suffixes = [
			r"\s+Inc\.\s*$",
			r"\s+LLC\s*$",
			r"\s+Ltd\.\s*$",
			r"\s+Corp\.\s*$",
		]

		all_suffixes = german_suffixes + french_suffixes + english_suffixes

		normalized = name
		for suffix_pattern in all_suffixes:
			normalized = re.sub(suffix_pattern, "", normalized, flags=re.IGNORECASE)

		return normalized.strip()

	def parse_swiss_number(self, text: str) -> Optional[int]:
		"""
		Parse Swiss number format (uses apostrophes).

		Args:
		    text: Text like "100'000" or "CHF 100'000"

		Returns:
		    Integer value or None
		"""
		if not text:
			return None

		# Remove CHF prefix
		text = re.sub(r"CHF\s*", "", text, flags=re.IGNORECASE)

		# Remove apostrophes and commas
		number_str = text.replace("'", "").replace(",", "").strip()

		try:
			return int(number_str)
		except ValueError:
			return None

	def normalize_tech_stack(self, technologies: List[str]) -> List[str]:
		"""
		Normalize technology names.

		Args:
		    technologies: Raw tech stack list

		Returns:
		    Normalized unique list
		"""
		if not technologies:
			return []

		tech_map = {
			"react.js": "React",
			"reactjs": "React",
			"react native": "React Native",
			"node.js": "Node.js",
			"nodejs": "Node.js",
			"aws": "AWS",
			"amazon web services": "AWS",
			"postgres": "PostgreSQL",
			"postgresql": "PostgreSQL",
			"k8s": "Kubernetes",
			"docker": "Docker",
			"python": "Python",
			"javascript": "JavaScript",
			"typescript": "TypeScript",
			"java": "Java",
			"golang": "Go",
			"ruby on rails": "Ruby on Rails",
			"rails": "Ruby on Rails",
		}

		normalized = []
		seen = set()

		for tech in technologies:
			if not tech:
				continue

			tech_lower = tech.lower().strip()
			normalized_tech = tech_map.get(tech_lower, tech.strip())

			# Avoid duplicates
			if normalized_tech.lower() not in seen:
				normalized.append(normalized_tech)
				seen.add(normalized_tech.lower())

		return normalized

	def format_equity_range(self, equity: Dict) -> Optional[str]:
		"""
		Format equity range from AngelList data.

		Args:
		    equity: Dict with min, max, type

		Returns:
		    Formatted string like "0.1%-0.5%" or "1,000-5,000 shares"
		"""
		if not equity:
			return None

		equity_type = equity.get("type", "percentage")
		min_equity = equity.get("min", 0)
		max_equity = equity.get("max", 0)

		if min_equity == 0 and max_equity == 0:
			return None

		if equity_type == "percentage":
			return f"{min_equity}%-{max_equity}%"
		else:
			return f"{min_equity:,}-{max_equity:,} shares"

	def map_experience_level(self, level: str, source: str) -> str:
		"""
		Map experience level to standard values.

		Args:
		    level: Raw experience level
		    source: Source board name

		Returns:
		    Normalized level
		"""
		if not level:
			return "Mid-Level"

		level_lower = level.lower().strip()

		# XING mapping (German)
		if source == "XING":
			xing_map = {
				"berufseinsteiger": "Entry Level",
				"mit_berufserfahrung": "Mid-Level",
				"mit berufserfahrung": "Mid-Level",
				"fuehrungskraft": "Manager",
				"führungskraft": "Manager",
			}
			return xing_map.get(level_lower, "Mid-Level")

		# AngelList mapping
		if source == "AngelList":
			angellist_map = {
				"intern": "Internship",
				"junior": "Junior",
				"mid": "Mid-Level",
				"senior": "Senior",
				"lead": "Lead",
				"staff": "Staff",
				"principal": "Principal",
			}
			return angellist_map.get(level_lower, level.replace("_", "-").title())

		# Generic mapping
		generic_map = {
			"entry": "Entry Level",
			"junior": "Junior",
			"mid": "Mid-Level",
			"senior": "Senior",
			"lead": "Lead",
			"staff": "Staff",
			"manager": "Manager",
			"director": "Director",
		}

		return generic_map.get(level_lower, "Mid-Level")

	def map_funding_stage(self, stage: str) -> str:
		"""
		Map funding stage to standard format.

		Args:
		    stage: Raw funding stage from AngelList

		Returns:
		    Normalized stage
		"""
		if not stage:
			return None

		stage_map = {
			"bootstrapped": "Bootstrapped",
			"pre_seed": "Pre-Seed",
			"seed": "Seed",
			"series_a": "Series A",
			"series_b": "Series B",
			"series_c": "Series C",
			"series_d": "Series D+",
			"series_d_+": "Series D+",
			"acquired": "Acquired",
			"public": "Public",
		}

		return stage_map.get(stage.lower(), stage.replace("_", " ").title())


# Singleton instance
_language_processor = None


def get_language_processor() -> LanguageProcessor:
	"""Get singleton language processor instance."""
	global _language_processor
	if _language_processor is None:
		_language_processor = LanguageProcessor()
	return _language_processor
