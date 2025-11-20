#!/usr/bin/env python3
"""
Automated architecture diagram validation and update system.
Validates Mermaid diagrams and updates them based on code analysis.
"""

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set

sys.path.insert(0, "backend")

from app.utils.datetime import utc_now


@dataclass
class DiagramValidationResult:
	"""Result of diagram validation"""

	file_path: str
	is_valid: bool
	errors: List[str]
	warnings: List[str]
	outdated_components: List[str]


@dataclass
class ComponentReference:
	"""Reference to a component in the codebase"""

	name: str
	type: str  # 'service', 'model', 'endpoint', 'component'
	file_path: str
	last_modified: str


class ArchitectureDiagramManager:
	"""Manages architecture diagram validation and updates"""

	def __init__(self):
		self.docs_path = Path("docs/architecture")
		self.backend_path = Path("backend")
		self.frontend_path = Path("frontend")

	def validate_all_diagrams(self) -> List[DiagramValidationResult]:
		"""Validate all architecture diagrams"""
		results = []

		if not self.docs_path.exists():
			return results

		for diagram_file in self.docs_path.glob("*.md"):
			if diagram_file.name.endswith(".md"):
				result = self.validate_diagram(diagram_file)
				results.append(result)

		return results

	def validate_diagram(self, diagram_file: Path) -> DiagramValidationResult:
		"""Validate a single diagram file"""
		errors = []
		warnings = []
		outdated_components = []

		try:
			content = diagram_file.read_text()

			# Extract Mermaid code blocks
			mermaid_blocks = re.findall(r"```mermaid\s*\n(.*?)\n```", content, re.DOTALL)

			for block in mermaid_blocks:
				# Validate Mermaid syntax
				syntax_errors = self.validate_mermaid_syntax(block)
				errors.extend(syntax_errors)

				# Check for outdated component references
				outdated = self.check_outdated_components(block)
				outdated_components.extend(outdated)

			# Check WikiLinks
			wikilink_warnings = self.validate_wikilinks(content)
			warnings.extend(wikilink_warnings)

		except Exception as e:
			errors.append(f"Failed to read diagram file: {e}")

		return DiagramValidationResult(
			file_path=str(diagram_file), is_valid=len(errors) == 0, errors=errors, warnings=warnings, outdated_components=outdated_components
		)

	def validate_mermaid_syntax(self, mermaid_code: str) -> List[str]:
		"""Validate Mermaid diagram syntax"""
		errors = []

		# Basic syntax checks
		lines = mermaid_code.strip().split("\n")

		if not lines[0].strip().startswith(("graph", "flowchart", "sequenceDiagram", "classDiagram")):
			errors.append("Invalid diagram type declaration")

		# Check for common syntax errors
		bracket_count = 0
		brace_count = 0

		for line in lines:
			bracket_count += line.count("[") - line.count("]")
			brace_count += line.count("{") - line.count("}")

		if bracket_count != 0:
			errors.append("Unmatched square brackets")

		if brace_count != 0:
			errors.append("Unmatched curly braces")

		# Check for invalid node definitions
		for line in lines:
			if "-->" in line or "->" in line:
				parts = line.split("-->") if "-->" in line else line.split("->")
				if len(parts) != 2:
					errors.append(f"Invalid connection syntax: {line.strip()}")

		return errors

	def check_outdated_components(self, mermaid_code: str) -> List[str]:
		"""Check for outdated component references in diagram"""
		outdated = []

		# Extract component names from diagram
		component_pattern = r"(\w+)\[([^\]]+)\]"
		matches = re.findall(component_pattern, mermaid_code)

		current_components = self.get_current_components()

		for node_id, label in matches:
			if node_id not in current_components:
				# Check if it's a known component with different name
				if not any(comp["name"].lower().replace(" ", "") == node_id.lower() for comp in current_components.values()):
					outdated.append(f"Unknown component: {node_id}")

		return outdated

	def validate_wikilinks(self, content: str) -> List[str]:
		"""Validate WikiLinks in the document"""
		warnings = []

		# Find all WikiLinks
		wikilink_pattern = r"\[\[([^\]]+)\]\]"
		matches = re.findall(wikilink_pattern, content)

		for link in matches:
			# Check if linked file exists
			link_path = self.docs_path / f"{link}.md"
			if not link_path.exists():
				# Also check in subdirectories
				found = False
				for subdir in ["architecture", "development", "api", "database"]:
					subdir_path = self.docs_path / subdir / f"{link}.md"
					if subdir_path.exists():
						found = True
						break

				if not found:
					warnings.append(f"Broken WikiLink: [[{link}]]")

		return warnings

	def get_current_components(self) -> Dict[str, Dict[str, Any]]:
		"""Get current components from codebase analysis"""
		components = {}

		# Analyze backend services
		if self.backend_path.exists():
			for service_file in (self.backend_path / "app" / "services").glob("*.py"):
				if service_file.name != "__init__.py":
					components[service_file.stem] = {
						"name": service_file.stem.replace("_", " ").title(),
						"type": "service",
						"file_path": str(service_file),
						"last_modified": self.get_file_modification_time(service_file),
					}

		# Analyze frontend components
		if self.frontend_path.exists():
			for component_file in (self.frontend_path / "src" / "components").rglob("*.tsx"):
				component_name = component_file.stem
				components[component_name.lower()] = {
					"name": component_name,
					"type": "component",
					"file_path": str(component_file),
					"last_modified": self.get_file_modification_time(component_file),
				}

		return components

	def get_file_modification_time(self, file_path: Path) -> str:
		"""Get file modification time"""
		try:
			stat = file_path.stat()
			return str(stat.st_mtime)
		except:
			return "unknown"

	def generate_validation_report(self, results: List[DiagramValidationResult]) -> str:
		"""Generate a validation report"""
		report = "# Architecture Diagram Validation Report\n\n"
		report += f"Generated: {self.get_current_timestamp()}\n\n"

		total_diagrams = len(results)
		valid_diagrams = len([r for r in results if r.is_valid])
		invalid_diagrams = total_diagrams - valid_diagrams

		report += "## Summary\n\n"
		report += f"- **Total Diagrams:** {total_diagrams}\n"
		report += f"- **Valid Diagrams:** {valid_diagrams}\n"
		report += f"- **Invalid Diagrams:** {invalid_diagrams}\n\n"

		if invalid_diagrams > 0:
			report += "## Issues Found\n\n"

			for result in results:
				if not result.is_valid or result.warnings or result.outdated_components:
					report += f"### {Path(result.file_path).name}\n\n"

					if result.errors:
						report += "**Errors:**\n"
						for error in result.errors:
							report += f"- {error}\n"
						report += "\n"

					if result.warnings:
						report += "**Warnings:**\n"
						for warning in result.warnings:
							report += f"- {warning}\n"
						report += "\n"

					if result.outdated_components:
						report += "**Outdated Components:**\n"
						for component in result.outdated_components:
							report += f"- {component}\n"
						report += "\n"

		report += "## Recommendations\n\n"
		if invalid_diagrams > 0:
			report += "1. Fix syntax errors in invalid diagrams\n"
			report += "2. Update component references to match current codebase\n"
			report += "3. Fix broken WikiLinks\n"
			report += "4. Regenerate diagrams from code analysis if needed\n"

		return report

	def get_current_timestamp(self) -> str:
		"""Get current timestamp"""
		return utc_now().isoformat()


def main():
	"""Main validation and update process"""
	manager = ArchitectureDiagramManager()

	print("🔍 Validating architecture diagrams...")

	# Validate all diagrams
	results = manager.validate_all_diagrams()

	# Generate report
	report = manager.generate_validation_report(results)

	# Save report
	report_path = Path("docs/architecture/validation-report.md")
	report_path.parent.mkdir(parents=True, exist_ok=True)
	report_path.write_text(report)

	# Print summary
	valid_count = len([r for r in results if r.is_valid])
	total_count = len(results)

	print(f"✅ Validated {total_count} diagrams")
	print(f"✅ Valid: {valid_count}, Invalid: {total_count - valid_count}")

	# Save detailed results
	results_data = {
		"generated_at": manager.get_current_timestamp(),
		"results": [
			{
				"file_path": r.file_path,
				"is_valid": r.is_valid,
				"errors": r.errors,
				"warnings": r.warnings,
				"outdated_components": r.outdated_components,
			}
			for r in results
		],
	}

	results_path = Path("docs/architecture/validation-results.json")
	with open(results_path, "w") as f:
		json.dump(results_data, f, indent=2)

	print("✅ Generated validation report")

	# Exit with error code if there are invalid diagrams
	if valid_count < total_count:
		print("❌ Some diagrams have issues. Check validation-report.md")
		sys.exit(1)


if __name__ == "__main__":
	main()
