"""Content Quality Service for scoring and improving content quality"""

import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QualityScore:
	"""Data class for content quality scores"""

	overall_score: float
	readability_score: float
	grammar_score: float
	structure_score: float
	keyword_relevance_score: float
	length_score: float
	tone_consistency_score: float
	suggestions: List[str]
	issues: List[Dict[str, Any]]


@dataclass
class GrammarIssue:
	"""Data class for grammar issues"""

	type: str
	message: str
	position: int
	length: int
	suggestions: List[str]
	severity: str  # low, medium, high


class ContentQualityService:
	"""Service for analyzing and improving content quality"""

	def __init__(self):
		# Common grammar patterns and issues
		self.grammar_patterns = {
			"double_space": r"\s{2,}",
			"missing_comma_before_and": r"\b\w+\s+\w+\s+and\s+\w+\b",
			"passive_voice": r"\b(is|are|was|were|being|been)\s+\w+ed\b",
			"weak_words": r"\b(very|really|quite|rather|somewhat|pretty|fairly)\s+",
			"redundant_phrases": r"\b(in order to|due to the fact that|at this point in time)\b",
			"sentence_fragments": r"^[A-Z][^.!?]*[^.!?]$",
		}

		# Readability metrics
		self.readability_weights = {"avg_sentence_length": 0.3, "avg_word_length": 0.2, "complex_words_ratio": 0.3, "paragraph_structure": 0.2}

		# Tone indicators
		self.tone_indicators = {
			"professional": ["sincerely", "respectfully", "professional", "experience", "qualifications"],
			"casual": ["hi", "hey", "thanks", "awesome", "cool"],
			"enthusiastic": ["excited", "thrilled", "passionate", "love", "amazing"],
			"confident": ["confident", "proven", "successful", "accomplished", "expertise"],
		}

	def analyze_content_quality(
		self, content: str, content_type: str = "cover_letter", target_tone: str = "professional", job_keywords: Optional[List[str]] = None
	) -> QualityScore:
		"""
		Analyze content quality and provide comprehensive scoring

		Args:
		    content: The content to analyze
		    content_type: Type of content (cover_letter, resume_tailoring, email_template)
		    target_tone: Expected tone (professional, casual, enthusiastic, confident)
		    job_keywords: Relevant keywords for the job

		Returns:
		    QualityScore object with detailed analysis
		"""
		try:
			# Initialize scores
			readability_score = self._calculate_readability_score(content)
			grammar_score = self._calculate_grammar_score(content)
			structure_score = self._calculate_structure_score(content, content_type)
			keyword_relevance_score = self._calculate_keyword_relevance(content, job_keywords or [])
			length_score = self._calculate_length_score(content, content_type)
			tone_consistency_score = self._calculate_tone_consistency(content, target_tone)

			# Calculate overall score (weighted average)
			overall_score = (
				readability_score * 0.2
				+ grammar_score * 0.25
				+ structure_score * 0.2
				+ keyword_relevance_score * 0.15
				+ length_score * 0.1
				+ tone_consistency_score * 0.1
			)

			# Generate suggestions and identify issues
			suggestions = self._generate_suggestions(
				content, readability_score, grammar_score, structure_score, keyword_relevance_score, length_score, tone_consistency_score
			)

			issues = self._identify_issues(content)

			return QualityScore(
				overall_score=round(overall_score, 2),
				readability_score=round(readability_score, 2),
				grammar_score=round(grammar_score, 2),
				structure_score=round(structure_score, 2),
				keyword_relevance_score=round(keyword_relevance_score, 2),
				length_score=round(length_score, 2),
				tone_consistency_score=round(tone_consistency_score, 2),
				suggestions=suggestions,
				issues=issues,
			)

		except Exception as e:
			logger.error(f"Error analyzing content quality: {e!s}")
			# Return default scores in case of error
			return QualityScore(
				overall_score=50.0,
				readability_score=50.0,
				grammar_score=50.0,
				structure_score=50.0,
				keyword_relevance_score=50.0,
				length_score=50.0,
				tone_consistency_score=50.0,
				suggestions=["Unable to analyze content quality"],
				issues=[],
			)

	def _calculate_readability_score(self, content: str) -> float:
		"""Calculate readability score based on sentence and word complexity"""

		sentences = re.split(r"[.!?]+", content)
		sentences = [s.strip() for s in sentences if s.strip()]

		if not sentences:
			return 0.0

		words = content.split()
		if not words:
			return 0.0

		# Average sentence length
		avg_sentence_length = len(words) / len(sentences)
		sentence_length_score = max(0, 100 - (avg_sentence_length - 15) * 2)  # Optimal: 15 words

		# Average word length
		avg_word_length = sum(len(word.strip(".,!?;:")) for word in words) / len(words)
		word_length_score = max(0, 100 - (avg_word_length - 5) * 10)  # Optimal: 5 characters

		# Complex words ratio (words with 3+ syllables)
		complex_words = sum(1 for word in words if self._count_syllables(word) >= 3)
		complex_ratio = complex_words / len(words)
		complex_score = max(0, 100 - complex_ratio * 200)  # Penalize high complexity

		# Paragraph structure
		paragraphs = content.split("\n\n")
		paragraph_score = 100 if 2 <= len(paragraphs) <= 5 else max(0, 100 - abs(len(paragraphs) - 3) * 20)

		# Weighted average
		readability_score = (
			sentence_length_score * self.readability_weights["avg_sentence_length"]
			+ word_length_score * self.readability_weights["avg_word_length"]
			+ complex_score * self.readability_weights["complex_words_ratio"]
			+ paragraph_score * self.readability_weights["paragraph_structure"]
		)

		return min(100, max(0, readability_score))

	def _calculate_grammar_score(self, content: str) -> float:
		"""Calculate grammar score by detecting common issues"""

		issues_found = 0
		total_checks = len(self.grammar_patterns)

		for pattern_name, pattern in self.grammar_patterns.items():
			matches = re.findall(pattern, content, re.IGNORECASE)
			if matches:
				issues_found += min(len(matches), 3)  # Cap at 3 per pattern type

		# Basic punctuation checks
		if not content.strip().endswith((".", "!", "?")):
			issues_found += 1

		# Check for proper capitalization
		sentences = re.split(r"[.!?]+", content)
		for sentence in sentences:
			sentence = sentence.strip()
			if sentence and not sentence[0].isupper():
				issues_found += 1

		# Calculate score (fewer issues = higher score)
		max_possible_issues = total_checks * 3 + 10  # Conservative estimate
		grammar_score = max(0, 100 - (issues_found / max_possible_issues) * 100)

		return grammar_score

	def _calculate_structure_score(self, content: str, content_type: str) -> float:
		"""Calculate structure score based on content type expectations"""

		score = 100

		if content_type == "cover_letter":
			# Check for proper cover letter structure
			has_greeting = bool(re.search(r"^(Dear|Hello|Hi)", content, re.IGNORECASE | re.MULTILINE))
			has_closing = bool(re.search(r"(Sincerely|Best regards|Thank you)", content, re.IGNORECASE))
			has_body_paragraphs = len(content.split("\n\n")) >= 3

			if not has_greeting:
				score -= 20
			if not has_closing:
				score -= 20
			if not has_body_paragraphs:
				score -= 15

		elif content_type == "email_template":
			# Check for email structure
			has_subject_indication = "subject:" in content.lower()
			has_greeting = bool(re.search(r"^(Dear|Hello|Hi)", content, re.IGNORECASE | re.MULTILINE))
			has_closing = bool(re.search(r"(Best|Thanks|Regards)", content, re.IGNORECASE))

			if not has_subject_indication:
				score -= 25
			if not has_greeting:
				score -= 15
			if not has_closing:
				score -= 15

		return max(0, score)

	def _calculate_keyword_relevance(self, content: str, job_keywords: List[str]) -> float:
		"""Calculate how well content incorporates relevant keywords"""

		if not job_keywords:
			return 75  # Neutral score when no keywords provided

		content_lower = content.lower()
		keywords_found = sum(1 for keyword in job_keywords if keyword.lower() in content_lower)

		if len(job_keywords) == 0:
			return 75

		relevance_ratio = keywords_found / len(job_keywords)
		return min(100, relevance_ratio * 100 + 25)  # Boost base score

	def _calculate_length_score(self, content: str, content_type: str) -> float:
		"""Calculate score based on appropriate content length"""

		word_count = len(content.split())

		# Optimal word count ranges by content type
		optimal_ranges = {"cover_letter": (200, 400), "email_template": (50, 150), "resume_tailoring": (100, 300)}

		min_words, max_words = optimal_ranges.get(content_type, (100, 300))

		if min_words <= word_count <= max_words:
			return 100
		elif word_count < min_words:
			return max(0, 100 - (min_words - word_count) * 2)
		else:
			return max(0, 100 - (word_count - max_words) * 1)

	def _calculate_tone_consistency(self, content: str, target_tone: str) -> float:
		"""Calculate how consistent the content is with the target tone"""

		content_lower = content.lower()

		# Count indicators for each tone
		tone_scores = {}
		for tone, indicators in self.tone_indicators.items():
			score = sum(1 for indicator in indicators if indicator in content_lower)
			tone_scores[tone] = score

		# Get target tone score
		target_score = tone_scores.get(target_tone, 0)
		total_indicators = sum(tone_scores.values())

		if total_indicators == 0:
			return 50  # Neutral if no tone indicators found

		consistency_ratio = target_score / total_indicators
		return min(100, consistency_ratio * 100 + 25)

	def _generate_suggestions(
		self,
		content: str,
		readability_score: float,
		grammar_score: float,
		structure_score: float,
		keyword_relevance_score: float,
		length_score: float,
		tone_consistency_score: float,
	) -> List[str]:
		"""Generate improvement suggestions based on scores"""

		suggestions = []

		if readability_score < 70:
			suggestions.append("Consider using shorter sentences and simpler words for better readability")

		if grammar_score < 80:
			suggestions.append("Review for grammar and punctuation errors")

		if structure_score < 70:
			suggestions.append("Improve document structure with proper greeting, body, and closing")

		if keyword_relevance_score < 60:
			suggestions.append("Include more relevant keywords from the job description")

		if length_score < 70:
			word_count = len(content.split())
			if word_count < 100:
				suggestions.append("Consider expanding the content with more details")
			else:
				suggestions.append("Consider condensing the content for better impact")

		if tone_consistency_score < 60:
			suggestions.append("Ensure the tone is consistent throughout the document")

		return suggestions

	def _identify_issues(self, content: str) -> List[Dict[str, Any]]:
		"""Identify specific issues in the content"""

		issues = []

		# Check for grammar patterns
		for pattern_name, pattern in self.grammar_patterns.items():
			matches = list(re.finditer(pattern, content, re.IGNORECASE))
			for match in matches:
				issue_type = pattern_name.replace("_", " ").title()
				issues.append(
					{
						"type": "grammar",
						"issue": issue_type,
						"position": match.start(),
						"length": match.end() - match.start(),
						"text": match.group(),
						"severity": "medium",
						"suggestion": self._get_grammar_suggestion(pattern_name, match.group()),
					}
				)

		# Check for formatting issues
		if content.count("\n\n") == 0:
			issues.append(
				{
					"type": "formatting",
					"issue": "No paragraph breaks",
					"position": 0,
					"length": 0,
					"text": "",
					"severity": "low",
					"suggestion": "Add paragraph breaks to improve readability",
				}
			)

		return issues

	def _get_grammar_suggestion(self, pattern_name: str, matched_text: str) -> str:
		"""Get specific suggestions for grammar issues"""

		suggestions = {
			"double_space": "Replace multiple spaces with single space",
			"passive_voice": "Consider using active voice for stronger impact",
			"weak_words": "Remove or replace weak modifier words",
			"redundant_phrases": "Use more concise phrasing",
			"sentence_fragments": "Complete the sentence with proper punctuation",
		}

		return suggestions.get(pattern_name, "Review this section for improvement")

	def _count_syllables(self, word: str) -> int:
		"""Estimate syllable count for readability calculation"""

		word = word.lower().strip(".,!?;:")
		if not word:
			return 0

		# Simple syllable counting heuristic
		vowels = "aeiouy"
		syllable_count = 0
		prev_was_vowel = False

		for char in word:
			is_vowel = char in vowels
			if is_vowel and not prev_was_vowel:
				syllable_count += 1
			prev_was_vowel = is_vowel

		# Handle silent 'e'
		if word.endswith("e") and syllable_count > 1:
			syllable_count -= 1

		return max(1, syllable_count)

	def check_spelling_and_grammar(self, content: str) -> Dict[str, Any]:
		"""
		Basic spelling and grammar check
		Note: In a production environment, this would integrate with services like Grammarly API
		"""

		issues = []
		suggestions = []

		# Basic checks that can be done without external services
		words = re.findall(r"\b\w+\b", content.lower())

		# Check for common misspellings
		common_misspellings = {
			"recieve": "receive",
			"seperate": "separate",
			"definately": "definitely",
			"occured": "occurred",
			"begining": "beginning",
		}

		for wrong, correct in common_misspellings.items():
			if wrong in words:
				issues.append(
					{
						"type": "spelling",
						"issue": f'Possible misspelling: "{wrong}"',
						"suggestion": f'Did you mean "{correct}"?',
						"severity": "medium",
					}
				)

		# Check for repeated words
		for i in range(len(words) - 1):
			if words[i] == words[i + 1]:
				issues.append({"type": "grammar", "issue": f'Repeated word: "{words[i]}"', "suggestion": "Remove duplicate word", "severity": "low"})

		return {"issues": issues, "suggestions": suggestions, "total_issues": len(issues)}

	def export_content(self, content: str, format_type: str = "txt") -> str:
		"""
		Export content in different formats

		Args:
		    content: Content to export
		    format_type: Export format (txt, html, markdown)

		Returns:
		    Formatted content string
		"""

		if format_type == "html":
			# Convert to basic HTML
			paragraphs = content.split("\n\n")
			html_content = "<html><body>\n"
			for paragraph in paragraphs:
				if paragraph.strip():
					html_content += f"<p>{paragraph.strip()}</p>\n"
			html_content += "</body></html>"
			return html_content

		elif format_type == "markdown":
			# Convert to markdown (basic formatting)
			lines = content.split("\n")
			markdown_content = ""
			for line in lines:
				line = line.strip()
				if line:
					# Simple heuristic for headers
					if line.isupper() and len(line) < 50:
						markdown_content += f"# {line}\n\n"
					else:
						markdown_content += f"{line}\n\n"
			return markdown_content

		else:  # txt format
			return content
