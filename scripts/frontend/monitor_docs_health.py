#!/usr/bin/env python3
"""
Documentation health monitoring system.
Monitors documentation quality, completeness, and maintenance status.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple


@dataclass
class DocumentationHealthMetrics:
	"""Health metrics for documentation"""

	total_files: int
	outdated_files: int
	broken_links: int
	missing_sections: int
	code_examples_valid: int
	diagrams_valid: int
	last_updated: str


@dataclass
class FileHealthStatus:
	"""Health status for individual documentation file"""

	file_path: str
	is_outdated: bool
	days_since_update: int
	broken_links: List[str]
	missing_sections: List[str]
	code_examples_valid: bool
	diagrams_valid: bool


class DocumentationHealthMonitor:
	"""Monitors and reports on documentation health"""

	def __init__(self):
		self.docs_path = Path("docs")
		self.backend_path = Path("backend")
		self.frontend_path = Path("frontend")
		self.max_age_days = 30  # Consider files outdated after 30 days

	def run_full_health_check(self) -> Tuple[DocumentationHealthMetrics, List[FileHealthStatus]]:
		"""Run comprehensive health check on all documentation"""
		print("🏥 Running documentation health check...")

		# Get all documentation files
		doc_files = self.get_all_doc_files()

		# Analyze each file
		file_statuses = []
		for doc_file in doc_files:
			status = self.analyze_file_health(doc_file)
			file_statuses.append(status)

		# Calculate overall metrics
		metrics = self.calculate_metrics(file_statuses)

		return metrics, file_statuses

	def get_all_doc_files(self) -> List[Path]:
		"""Get all documentation files"""
		doc_files = []

		if self.docs_path.exists():
			# Get all .md files in docs directory
			for md_file in self.docs_path.rglob("*.md"):
				doc_files.append(md_file)

		return doc_files

	def analyze_file_health(self, file_path: Path) -> FileHealthStatus:
		"""Analyze health of a single documentation file"""
		try:
			content = file_path.read_text()
			stat = file_path.stat()

			# Calculate days since last update
			last_modified = datetime.fromtimestamp(stat.st_mtime)
			days_since_update = (datetime.now() - last_modified).days

			# Check if outdated
			is_outdated = days_since_update > self.max_age_days

			# Check for broken links
			broken_links = self.check_broken_links(content, file_path)

			# Check for missing sections
			missing_sections = self.check_missing_sections(content, file_path)

			# Validate code examples
			code_examples_valid = self.validate_code_examples(content)

			# Validate diagrams
			diagrams_valid = self.validate_diagrams(content)

			return FileHealthStatus(
				file_path=str(file_path),
				is_outdated=is_outdated,
				days_since_update=days_since_update,
				broken_links=broken_links,
				missing_sections=missing_sections,
				code_examples_valid=code_examples_valid,
				diagrams_valid=diagrams_valid,
			)

		except Exception as e:
			print(f"Error analyzing {file_path}: {e}")
			return FileHealthStatus(
				file_path=str(file_path),
				is_outdated=True,
				days_since_update=999,
				broken_links=[],
				missing_sections=["Analysis failed"],
				code_examples_valid=False,
				diagrams_valid=False,
			)

	def check_broken_links(self, content: str, file_path: Path) -> List[str]:
		"""Check for broken links in documentation"""
		broken_links = []

		# Check WikiLinks
		wikilink_pattern = r"\[\[([^\]]+)\]\]"
		wikilinks = re.findall(wikilink_pattern, content)

		for link in wikilinks:
			# Check if linked file exists
			link_path = self.docs_path / f"{link}.md"
			if not link_path.exists():
				# Check in subdirectories
				found = False
				for subdir in ["architecture", "development", "api", "database"]:
					subdir_path = self.docs_path / subdir / f"{link}.md"
					if subdir_path.exists():
						found = True
						break

				if not found:
					broken_links.append(f"[[{link}]]")

		# Check regular markdown links
		link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
		links = re.findall(link_pattern, content)

		for text, url in links:
			if url.startswith("http"):
				# External links - could check with requests, but skip for now
				continue
			elif url.startswith("./") or url.startswith("../"):
				# Relative links
				resolved_path = (file_path.parent / url).resolve()
				if not resolved_path.exists():
					broken_links.append(url)
			elif not url.startswith("#"):
				# Local file references
				if not (self.docs_path / url).exists():
					broken_links.append(url)

		return broken_links

	def check_missing_sections(self, content: str, file_path: Path) -> List[str]:
		"""Check for missing required sections"""
		missing_sections = []

		# Define required sections based on file type
		filename = file_path.name.lower()

		if "architecture" in str(file_path):
			required_sections = ["Overview", "Components", "Data Flow", "Security Considerations"]
		elif "api" in str(file_path):
			required_sections = ["Endpoints", "Authentication", "Error Handling", "Examples"]
		elif "development" in str(file_path):
			required_sections = ["Setup", "Usage", "Configuration", "Testing"]
		elif "deployment" in str(file_path):
			required_sections = ["Prerequisites", "Configuration", "Deployment", "Monitoring"]
		else:
			required_sections = ["Overview", "Usage"]

		# Check if sections exist (case-insensitive)
		content_lower = content.lower()
		for section in required_sections:
			if f"## {section.lower()}" not in content_lower:
				missing_sections.append(section)

		return missing_sections

	def validate_code_examples(self, content: str) -> bool:
		"""Validate code examples in documentation"""
		# Extract code blocks
		code_blocks = re.findall(r"```(\w+)?\s*\n(.*?)\n```", content, re.DOTALL)

		if not code_blocks:
			return True  # No code blocks to validate

		# Basic validation - check for common syntax errors
		for lang, code in code_blocks:
			if lang in ["python", "py"]:
				if self.has_python_syntax_errors(code):
					return False
			elif lang in ["typescript", "ts", "javascript", "js"]:
				if self.has_javascript_syntax_errors(code):
					return False
			elif lang == "sql":
				if self.has_sql_syntax_errors(code):
					return False

		return True

	def validate_diagrams(self, content: str) -> bool:
		"""Validate Mermaid diagrams in documentation"""
		# Extract Mermaid blocks
		mermaid_blocks = re.findall(r"```mermaid\s*\n(.*?)\n```", content, re.DOTALL)

		for block in mermaid_blocks:
			# Basic validation
			lines = block.strip().split("\n")
			if not lines:
				return False

			# Check for valid diagram type
			first_line = lines[0].strip()
			if not first_line.startswith(("graph", "flowchart", "sequenceDiagram", "classDiagram")):
				return False

		return True

	def has_python_syntax_errors(self, code: str) -> bool:
		"""Check for Python syntax errors"""
		try:
			compile(code, "<string>", "exec")
			return False
		except SyntaxError:
			return True

	def has_javascript_syntax_errors(self, code: str) -> bool:
		"""Check for JavaScript/TypeScript syntax errors (basic check)"""
		# Basic checks for common syntax errors
		bracket_count = code.count("{") - code.count("}")
		paren_count = code.count("(") - code.count(")")
		square_count = code.count("[") - code.count("]")

		return bracket_count != 0 or paren_count != 0 or square_count != 0

	def has_sql_syntax_errors(self, code: str) -> bool:
		"""Check for basic SQL syntax errors"""
		# Basic check for SELECT statements
		if code.strip().upper().startswith("SELECT"):
			if "FROM" not in code.upper():
				return True
		return False

	def calculate_metrics(self, file_statuses: List[FileHealthStatus]) -> DocumentationHealthMetrics:
		"""Calculate overall health metrics"""
		total_files = len(file_statuses)
		outdated_files = len([s for s in file_statuses if s.is_outdated])
		broken_links = sum(len(s.broken_links) for s in file_statuses)
		missing_sections = sum(len(s.missing_sections) for s in file_statuses)
		code_examples_valid = len([s for s in file_statuses if s.code_examples_valid])
		diagrams_valid = len([s for s in file_statuses if s.diagrams_valid])

		return DocumentationHealthMetrics(
			total_files=total_files,
			outdated_files=outdated_files,
			broken_links=broken_links,
			missing_sections=missing_sections,
			code_examples_valid=code_examples_valid,
			diagrams_valid=diagrams_valid,
			last_updated=datetime.now().isoformat(),
		)

	def generate_health_report(self, metrics: DocumentationHealthMetrics, file_statuses: List[FileHealthStatus]) -> str:
		"""Generate comprehensive health report"""
		report = "# Documentation Health Report\n\n"
		report += f"Generated: {metrics.last_updated}\n\n"

		# Overall health score
		health_score = self.calculate_health_score(metrics)
		report += f"## Overall Health Score: {health_score:.1f}/100\n\n"

		# Metrics summary
		report += "## Health Metrics\n\n"
		report += f"- **Total Files:** {metrics.total_files}\n"
		report += f"- **Outdated Files:** {metrics.outdated_files} ({metrics.outdated_files / metrics.total_files * 100:.1f}%)\n"
		report += f"- **Broken Links:** {metrics.broken_links}\n"
		report += f"- **Missing Sections:** {metrics.missing_sections}\n"
		report += f"- **Valid Code Examples:** {metrics.code_examples_valid}/{metrics.total_files}\n"
		report += f"- **Valid Diagrams:** {metrics.diagrams_valid}/{metrics.total_files}\n\n"

		# Detailed issues
		if metrics.outdated_files > 0 or metrics.broken_links > 0 or metrics.missing_sections > 0:
			report += "## Issues Found\n\n"

			for status in file_statuses:
				has_issues = (
					status.is_outdated
					or status.broken_links
					or status.missing_sections
					or not status.code_examples_valid
					or not status.diagrams_valid
				)

				if has_issues:
					report += f"### {Path(status.file_path).name}\n\n"

					if status.is_outdated:
						report += f"- **Outdated:** {status.days_since_update} days since last update\n"

					if status.broken_links:
						report += "- **Broken Links:**\n"
						for link in status.broken_links:
							report += f"  - {link}\n"

					if status.missing_sections:
						report += "- **Missing Sections:**\n"
						for section in status.missing_sections:
							report += f"  - {section}\n"

					if not status.code_examples_valid:
						report += "- **Invalid Code Examples:** Syntax errors detected\n"

					if not status.diagrams_valid:
						report += "- **Invalid Diagrams:** Syntax errors detected\n"

					report += "\n"

		# Recommendations
		report += "## Recommendations\n\n"
		if health_score < 80:
			report += "1. Update outdated documentation files\n"
			report += "2. Fix broken links and WikiLinks\n"
			report += "3. Add missing required sections\n"
			report += "4. Validate and fix code examples\n"
			report += "5. Check and repair diagram syntax\n"
			report += "6. Consider setting up automated documentation updates\n"

		return report

	def calculate_health_score(self, metrics: DocumentationHealthMetrics) -> float:
		"""Calculate overall health score (0-100)"""
		if metrics.total_files == 0:
			return 100.0

		# Weights for different factors
		weights = {"outdated": 0.2, "broken_links": 0.2, "missing_sections": 0.2, "code_examples": 0.2, "diagrams": 0.2}

		# Calculate individual scores
		outdated_score = max(0, 100 - (metrics.outdated_files / metrics.total_files) * 100)
		broken_links_score = max(0, 100 - (metrics.broken_links / metrics.total_files) * 10)
		missing_sections_score = max(0, 100 - (metrics.missing_sections / metrics.total_files) * 20)
		code_examples_score = (metrics.code_examples_valid / metrics.total_files) * 100
		diagrams_score = (metrics.diagrams_valid / metrics.total_files) * 100

		# Weighted average
		total_score = (
			outdated_score * weights["outdated"]
			+ broken_links_score * weights["broken_links"]
			+ missing_sections_score * weights["missing_sections"]
			+ code_examples_score * weights["code_examples"]
			+ diagrams_score * weights["diagrams"]
		)

		return round(total_score, 1)


def main():
	"""Main health monitoring process"""
	monitor = DocumentationHealthMonitor()

	try:
		# Run health check
		metrics, file_statuses = monitor.run_full_health_check()

		# Generate report
		report = monitor.generate_health_report(metrics, file_statuses)

		# Save report
		report_path = Path("docs/health-report.md")
		report_path.parent.mkdir(parents=True, exist_ok=True)
		report_path.write_text(report)

		# Save detailed results
		results_data = {
			"generated_at": metrics.last_updated,
			"metrics": {
				"total_files": metrics.total_files,
				"outdated_files": metrics.outdated_files,
				"broken_links": metrics.broken_links,
				"missing_sections": metrics.missing_sections,
				"code_examples_valid": metrics.code_examples_valid,
				"diagrams_valid": metrics.diagrams_valid,
			},
			"file_statuses": [
				{
					"file_path": s.file_path,
					"is_outdated": s.is_outdated,
					"days_since_update": s.days_since_update,
					"broken_links": s.broken_links,
					"missing_sections": s.missing_sections,
					"code_examples_valid": s.code_examples_valid,
					"diagrams_valid": s.diagrams_valid,
				}
				for s in file_statuses
			],
		}

		results_path = Path("docs/health-results.json")
		with open(results_path, "w") as f:
			json.dump(results_data, f, indent=2)

		# Print summary
		health_score = monitor.calculate_health_score(metrics)
		print(f"🏥 Documentation Health Score: {health_score:.1f}/100")
		print(f"📊 Analyzed {metrics.total_files} files")
		print(f"📝 Generated health report")

		# Exit with error code if health is poor
		if health_score < 70:
			print("⚠️  Documentation health is poor. Check health-report.md")
			sys.exit(1)

	except Exception as e:
		print(f"❌ Health check failed: {e}")
		sys.exit(1)


if __name__ == "__main__":
	main()
