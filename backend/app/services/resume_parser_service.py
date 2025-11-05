"""Resume parsing service backed by Docling.

Converts resume documents into Markdown and extracts structured metadata.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, ClassVar, Dict, Iterable, List, Optional, Tuple

from app.core.logging import get_logger

_logger = get_logger(__name__)


class ResumeParserService:
	"""Convert resumes to structured data using Docling."""

	__version__ = "1.0.0"
	_supported_extensions: ClassVar[set[str]] = {".pdf", ".docx", ".doc", ".md", ".txt"}
	_converter_instance: ClassVar[Optional[Any]] = None

	def __init__(self) -> None:
		self._converter = self._ensure_converter()

	@classmethod
	def _ensure_converter(cls):
		if cls._converter_instance is not None:
			return cls._converter_instance
		try:
			from docling.document_converter import DocumentConverter  # type: ignore
		except ImportError as exc:  # pragma: no cover
			raise RuntimeError("Docling is required for resume parsing. Install it with `pip install docling`.") from exc
		cls._converter_instance = DocumentConverter()
		return cls._converter_instance

	def validate_resume_file(self, file_path: str) -> Tuple[bool, str | None]:
		"""Validate that the resume exists, is not empty, and is supported."""
		path = Path(file_path)
		if not path.exists():
			return False, "File not found"
		if not path.is_file():
			return False, "Provided path is not a file"
		if path.stat().st_size == 0:
			return False, "File is empty"
		if path.suffix.lower() not in self._supported_extensions:
			return False, f"Unsupported file type '{path.suffix}'. Supported types: {sorted(self._supported_extensions)}"
		return True, None

	def parse_resume_sync(self, file_path: str, filename: str, user_id: int) -> Dict[str, Any]:
		"""Parse a resume file into structured metadata."""
		markdown, metadata = self._convert_to_markdown(file_path, filename)
		sections = self._split_sections(markdown)
		contact = self._extract_contact_details(markdown)
		summary = self._extract_summary(sections)
		skills = self._extract_list_section(sections, {"skills", "technical skills", "core competencies", "technologies"})
		experience_entries, experience_text = self._extract_experience(sections)
		education = self._extract_list_section(sections, {"education", "academics", "academic background"})
		certifications = self._extract_list_section(sections, {"certifications", "licenses", "certification"})
		experience_level = self._estimate_experience_level(experience_text)

		return {
			"filename": filename,
			"user_id": user_id,
			"contact": contact,
			"summary": summary,
			"skills": skills,
			"experience": experience_entries,
			"experience_level": experience_level,
			"education": education,
			"certifications": certifications,
			"content_markdown": markdown,
			"sections": sections,
			"metadata": metadata,
		}

	def export_parsed_data(self, parsed_resume: Dict[str, Any], output_path: Path) -> None:
		"""Persist parsed resume data to JSON for downstream jobs."""
		output_path.parent.mkdir(parents=True, exist_ok=True)
		with output_path.open("w", encoding="utf-8") as handle:
			json.dump(parsed_resume, handle, ensure_ascii=False, indent=2)

	def _convert_to_markdown(self, file_path: str, filename: str) -> Tuple[str, Dict[str, Any]]:
		try:
			result = self._converter.convert(file_path)
		except Exception as exc:
			_logger.error("Docling conversion failed for %s: %s", filename, exc)
			raise RuntimeError(f"Docling failed to convert '{filename}': {exc!s}") from exc

		document = getattr(result, "document", None)
		if document is None:
			raise RuntimeError(f"Docling returned no document for '{filename}'")

		try:
			markdown = document.export_to_markdown()
		except Exception as exc:  # pragma: no cover
			_logger.error("Markdown export failed for %s: %s", filename, exc)
			raise RuntimeError(f"Unable to export markdown for '{filename}': {exc!s}") from exc

		metadata = {
			"docling_version": getattr(result, "docling_version", None),
			"warnings": [str(warning) for warning in getattr(result, "warnings", [])],
			"num_pages": getattr(result, "num_pages", None),
		}

		return markdown, metadata

	def _split_sections(self, markdown: str) -> Dict[str, str]:
		sections: Dict[str, str] = {}
		current_key = "document"
		buffer: List[str] = []
		heading_pattern = re.compile(r"^#{1,6}\s+(?P<title>.+?)\s*$")

		for raw_line in markdown.splitlines():
			line = raw_line.rstrip()
			heading = heading_pattern.match(line)
			if heading:
				if buffer:
					sections[current_key] = "\n".join(buffer).strip()
					buffer = []
				current_key = heading.group("title").strip().lower()
				continue
			buffer.append(line)

		if buffer:
			sections[current_key] = "\n".join(buffer).strip()

		return sections

	def _extract_contact_details(self, markdown: str) -> Dict[str, Optional[str]]:
		email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", markdown)
		phone_match = re.search(r"(\+?\d{1,3}[\s-]?)?(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})", markdown)
		linkedin_match = re.search(r"https?://(?:www\.)?linkedin\.com/[A-Za-z0-9_./-]+", markdown, flags=re.IGNORECASE)
		github_match = re.search(r"https?://(?:www\.)?github\.com/[A-Za-z0-9_.-]+", markdown, flags=re.IGNORECASE)

		name_line = None
		for candidate in markdown.splitlines():
			candidate = candidate.strip("# ")
			if not candidate:
				continue
			if email_match and email_match.group(0) in candidate:
				continue
			if linkedin_match and linkedin_match.group(0) in candidate:
				continue
			if github_match and github_match.group(0) in candidate:
				continue
			name_line = candidate
			break

		return {
			"full_name": name_line,
			"email": email_match.group(0) if email_match else None,
			"phone": phone_match.group(0) if phone_match else None,
			"linkedin": linkedin_match.group(0) if linkedin_match else None,
			"github": github_match.group(0) if github_match else None,
		}

	def _extract_summary(self, sections: Dict[str, str]) -> Optional[str]:
		for key in ("summary", "professional summary", "profile", "about", "objective"):
			section = self._match_section(sections, key)
			if section:
				paragraphs = [p.strip() for p in section.split("\n\n") if p.strip()]
				if paragraphs:
					return paragraphs[0]
		document_body = sections.get("document")
		if document_body:
			paragraphs = [p.strip() for p in document_body.split("\n\n") if p.strip()]
			if paragraphs:
				return paragraphs[0]
		return None

	def _extract_list_section(self, sections: Dict[str, str], candidate_keys: Iterable[str]) -> List[str]:
		section_text = None
		for key in candidate_keys:
			section_text = self._match_section(sections, key)
			if section_text:
				break
		if not section_text:
			return []

		items: List[str] = []
		for line in section_text.splitlines():
			clean = line.strip()
			if not clean:
				continue
			clean = re.sub(r"^[\-*•\d.\s]+", "", clean)
			if not clean:
				continue
			parts = [part.strip() for part in re.split(r",|\s{2,}", clean) if part.strip()]
			if len(parts) == 1:
				items.append(parts[0])
			else:
				items.extend(parts)

		seen = set()
		unique_items = []
		for item in items:
			lower = item.lower()
			if lower in seen:
				continue
			seen.add(lower)
			unique_items.append(item)

		return unique_items

	def _extract_experience(self, sections: Dict[str, str]) -> Tuple[List[Dict[str, Any]], str]:
		section_text = self._match_section(
			sections,
			{"experience", "professional experience", "work experience", "employment", "career history"},
		)
		if not section_text:
			return [], ""

		entries: List[Dict[str, Any]] = []
		blocks = [block.strip() for block in re.split(r"\n\s*\n", section_text) if block.strip()]
		for block in blocks:
			lines = [re.sub(r"^[\-*•\d.\s]+", "", line).strip() for line in block.splitlines() if line.strip()]
			if not lines:
				continue
			header = lines[0]
			dates = self._extract_dates(header)
			role, company = self._split_role_company(header)
			description = lines[1:]
			entries.append(
				{
					"role": role,
					"company": company,
					"dates": dates,
					"highlights": description,
				}
			)

		return entries, section_text

	def _match_section(self, sections: Dict[str, str], keys: Iterable[str]) -> Optional[str]:
		if isinstance(keys, str):
			keys = [keys]
		for section_key, section_value in sections.items():
			for key in keys:
				needle = key.lower()
				if needle == section_key:
					return section_value
				if needle in section_key:
					return section_value
		return None

	def _extract_dates(self, text: str) -> Optional[str]:
		pattern = re.compile(
			r"((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})\s*(?:\s*(?:-|to|\u2013)\s*(Present|Current|\d{4}))?",
			re.IGNORECASE,
		)
		match = pattern.search(text)
		return match.group(0) if match else None

	def _split_role_company(self, header: str) -> Tuple[Optional[str], Optional[str]]:
		parts = re.split(r"\s+[-\u2013|@]\s+", header)
		if len(parts) >= 2:
			return parts[0].strip(), parts[1].strip()
		return header.strip() if header else None, None

	def _estimate_experience_level(self, experience_text: str) -> Optional[str]:
		if not experience_text:
			return None
		year_matches = [int(match) for match in re.findall(r"(\d{1,2})\+?\s+years?", experience_text, flags=re.IGNORECASE)]
		if year_matches:
			max_years = max(year_matches)
			if max_years >= 8:
				return "senior"
			if max_years >= 4:
				return "mid"
			return "junior"

		role_mentions = len(re.findall(r"\b(manager|lead|director|head)\b", experience_text, flags=re.IGNORECASE))
		if role_mentions >= 2:
			return "senior"
		if role_mentions == 1:
			return "mid"
		return "junior"
