#!/usr/bin/env python3
"""
WikiLink validation and maintenance system.
Validates WikiLinks across the documentation and suggests fixes.
"""

import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class WikiLinkValidationResult:
	"""Result of WikiLink validation"""

	source_file: str
	link_text: str
	target_exists: bool
	suggested_fix: str
	line_number: int


@dataclass
class WikiLinkNetwork:
	"""Network analysis of WikiLinks"""

	incoming_links: Dict[str, List[str]]  # target -> [source files]
	outgoing_links: Dict[str, List[str]]  # source -> [target files]
	orphaned_files: List[str]  # Files with no incoming links
	broken_links: List[WikiLinkValidationResult]


class WikiLinkValidator:
	"""Validates and maintains WikiLinks in documentation"""

	def __init__(self):
		self.docs_path = Path("docs")
		self.root_path = Path(".")
		# Updated pattern to capture link target and optional alias
		self.wikilink_pattern = r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]"

		# Directories that should be treated as valid link targets
		self.valid_directories = {
			"backend/app/services",
			"backend/app/api/v1",
			"backend/app/models",
			"backend/app/core",
			"frontend/src/app",
			"frontend/src/components",
			"frontend/src/lib",
			"scripts",
		}

		# Auto-generated files to exclude from broken link analysis
		self.auto_generated_files = {
			"wikilink-report.md",
			"wikilink-network.md",
			"wikilink-results.json",
		}

		# Files that are intentionally orphaned (entry points, meta-docs)
		self.intentional_orphans = {
			"README.md",  # Root entry point
			"wikilink-report.md",  # Auto-generated report
			"wikilink-network.md",  # Auto-generated network
		}

	def validate_all_wikilinks(self) -> WikiLinkNetwork:
		"""Validate all WikiLinks and build network analysis"""
		print("🔗 Analyzing WikiLink network...")

		# Get all documentation files
		doc_files = self.get_all_doc_files()

		# Build link network
		incoming_links = defaultdict(list)
		outgoing_links = defaultdict(list)
		broken_links = []

		for doc_file in doc_files:
			# Skip auto-generated files in broken link analysis
			if doc_file.name in self.auto_generated_files:
				continue

			file_links = self.extract_wikilinks(doc_file)

			# Record outgoing links
			outgoing_links[str(doc_file)] = file_links

			# Record incoming links
			for link in file_links:
				# Skip certain link patterns that are not file references
				if self.should_skip_link(link):
					continue

				target_file = self.resolve_wikilink(link, doc_file)
				if target_file:
					incoming_links[str(target_file)].append(str(doc_file))
				else:
					# Broken link
					line_num = self.find_link_line_number(doc_file, link)
					broken_links.append(
						WikiLinkValidationResult(
							source_file=str(doc_file), link_text=link, target_exists=False, suggested_fix=self.suggest_fix(link), line_number=line_num
						)
					)

		# Find orphaned files
		all_files = {str(f) for f in doc_files}
		linked_files = set(incoming_links.keys())
		orphaned_files = list(all_files - linked_files)

		# Remove index files and intentional orphans
		orphaned_files = [f for f in orphaned_files if not Path(f).name.startswith("index") and Path(f).name not in self.intentional_orphans]

		return WikiLinkNetwork(
			incoming_links=dict(incoming_links), outgoing_links=dict(outgoing_links), orphaned_files=orphaned_files, broken_links=broken_links
		)

	def should_skip_link(self, link_text: str) -> bool:
		"""Determine if a link should be skipped in validation"""
		link_text = link_text.strip()

		# Skip section anchors (internal page links)
		if link_text.startswith("#"):
			return True

		# Skip numeric patterns like [1, 2, 3]
		if re.match(r"^[\d,\s]+$", link_text):
			return True

		# Skip source code file wikilinks (these should be inline code, not wikilinks)
		# Examples: [[backend/app/main.py]], [[frontend/src/lib/api.ts]]
		source_code_extensions = (".py", ".ts", ".tsx", ".js", ".jsx", ".vue", ".go", ".rs", ".java", ".cpp", ".c", ".h")
		if any(link_text.endswith(ext) for ext in source_code_extensions):
			return True

		# Skip if it looks like code/data (contains special chars)
		if any(char in link_text for char in ["{", "}", "[", "]", "<", ">"]):
			return True

		return False

	def get_all_doc_files(self) -> List[Path]:
		"""Get all documentation files"""
		doc_files = []

		if self.docs_path.exists():
			for md_file in self.docs_path.rglob("*.md"):
				doc_files.append(md_file)

		return doc_files

	def extract_wikilinks(self, file_path: Path) -> List[str]:
		"""Extract all WikiLinks from a file"""
		try:
			content = file_path.read_text()
			# Extract both link and alias, but we only need the link target
			matches = re.findall(self.wikilink_pattern, content)
			# Return just the link targets (first group)
			return [match[0] if isinstance(match, tuple) else match for match in matches]
		except Exception:
			return []

	def resolve_wikilink(self, link_text: str, source_file: Optional[Path] = None) -> Optional[Path]:
		"""Resolve a WikiLink to an actual file path"""
		original_link = link_text

	def resolve_wikilink(self, link_text: str, source_file: Optional[Path] = None) -> Optional[Path]:
		"""Resolve a WikiLink to an actual file path"""
		original_link = link_text

		# Strip whitespace
		link_text = link_text.strip()

		# Skip section anchors - they're internal links
		if link_text.startswith("#"):
			return None

		# Handle directory references (ending with /)
		if link_text.endswith("/"):
			# Check if it's a valid directory
			dir_path = self.root_path / link_text.rstrip("/")
			if dir_path.is_dir() and str(link_text.rstrip("/")) in self.valid_directories:
				return dir_path
			# Check for README.md in that directory
			readme_path = dir_path / "README.md"
			if readme_path.exists():
				return readme_path

		# Handle .md extensions
		if link_text.endswith(".md"):
			link_text = link_text[:-3]

		# Handle path-based disambiguation (e.g., "career-copilot/README")
		if "/" in link_text:
			# Try without first component (e.g., "career-copilot/README" -> "README")
			parts = link_text.split("/")
			if len(parts) > 1:
				simple_name = parts[-1]
				# Try in root
				root_target = self.root_path / f"{simple_name}.md"
				if root_target.exists():
					return root_target
				# Try in docs
				docs_target = self.docs_path / f"{simple_name}.md"
				if docs_target.exists():
					return docs_target

		# Handle relative paths from source file
		if source_file:
			source_dir = source_file.parent

			if link_text.startswith("../"):
				# Go up directories
				parts = link_text.split("/")
				up_count = 0
				while parts and parts[0] == "..":
					up_count += 1
					parts.pop(0)

				target_dir = source_dir
				for _ in range(up_count):
					target_dir = target_dir.parent

				if parts:
					target_path = target_dir / "/".join(parts)
					# Check as file
					if target_path.suffix == "":
						target_path = Path(str(target_path) + ".md")
					if target_path.exists():
						return target_path
					# Check as directory
					if (target_dir / "/".join(parts)).is_dir():
						return target_dir / "/".join(parts)

			elif link_text.startswith("./"):
				# Relative to source directory
				relative_path = link_text[2:]
				target_path = source_dir / relative_path
				if target_path.suffix == "":
					target_path = Path(str(target_path) + ".md")
				if target_path.exists():
					return target_path

		# Try direct match in docs directory
		target_path = self.docs_path / f"{link_text}.md"
		if target_path.exists():
			return target_path

		# Try in subdirectories
		for subdir in ["architecture", "development", "api", "database", "deployment", "troubleshooting", "components", "setup"]:
			subdir_path = self.docs_path / subdir / f"{link_text}.md"
			if subdir_path.exists():
				return subdir_path

		# Try case-insensitive match
		link_lower = link_text.lower()
		for md_file in self.docs_path.rglob("*.md"):
			if md_file.stem.lower() == link_lower:
				return md_file

		# Try in root directory for files like README.md
		root_target = self.root_path / f"{link_text}.md"
		if root_target.exists():
			return root_target

		# Try as code file (Python, TypeScript, etc.)
		for ext in [".py", ".ts", ".tsx", ".js", ".jsx"]:
			code_file = self.root_path / f"{link_text}{ext}"
			if code_file.exists():
				return code_file

		# Check if it's a valid directory reference
		dir_path = self.root_path / link_text
		if dir_path.is_dir():
			return dir_path

		return None

	def find_link_line_number(self, file_path: Path, link_text: str) -> int:
		"""Find the line number of a WikiLink"""
		try:
			content = file_path.read_text()
			lines = content.split("\n")

			for i, line in enumerate(lines, 1):
				if f"[[{link_text}]]" in line:
					return i

		except Exception:
			pass

		return 0

	def suggest_fix(self, broken_link: str) -> str:
		"""Suggest a fix for a broken WikiLink"""
		# Find similar existing files
		existing_files = []
		for md_file in self.docs_path.rglob("*.md"):
			existing_files.append(md_file.stem)

		# Find closest matches
		broken_lower = broken_link.lower()
		suggestions = []

		for existing in existing_files:
			if broken_lower in existing.lower() or existing.lower() in broken_lower:
				suggestions.append(existing)

		if suggestions:
			return f"Try: {suggestions[0]}"
		else:
			return "No similar files found. Consider creating the linked document."

	def generate_validation_report(self, network: WikiLinkNetwork) -> str:
		"""Generate comprehensive WikiLink validation report"""
		report = "# WikiLink Validation Report\n\n"
		report += f"Generated: {self.get_current_timestamp()}\n\n"

		# Summary statistics
		total_files = len(network.incoming_links) + len(network.orphaned_files)
		total_links = sum(len(links) for links in network.outgoing_links.values())
		broken_count = len(network.broken_links)

		# Separate user-facing vs auto-generated broken links
		user_facing_broken = [b for b in network.broken_links if Path(b.source_file).name not in self.auto_generated_files]
		auto_gen_broken = [b for b in network.broken_links if Path(b.source_file).name in self.auto_generated_files]

		report += "## Summary\n\n"
		report += f"- **Total Documentation Files:** {total_files}\n"
		report += f"- **Total WikiLinks:** {total_links}\n"
		report += f"- **Broken Links (User-Facing):** {len(user_facing_broken)}\n"
		report += f"- **Broken Links (Auto-Generated):** {len(auto_gen_broken)}\n"
		report += f"- **Total Broken Links:** {broken_count}\n"
		report += f"- **Orphaned Files:** {len(network.orphaned_files)}\n\n"

		# Network health score
		health_score = self.calculate_network_health(network)
		report += f"## Network Health Score: {health_score:.1f}/100\n\n"

		if health_score >= 80:
			report += "✅ **Excellent** - Documentation is well-connected and maintained\n\n"
		elif health_score >= 60:
			report += "✓ **Good** - Documentation is in good shape with minor issues\n\n"
		elif health_score >= 40:
			report += "⚠️  **Fair** - Documentation needs attention\n\n"
		else:
			report += "❌ **Poor** - Significant documentation issues\n\n"

		# User-facing broken links section (priority)
		if user_facing_broken:
			report += "## ⚠️  User-Facing Broken Links (Priority Fixes)\n\n"
			report += "These broken links appear in documentation that users actually read:\n\n"

			# Group by source file
			by_file = defaultdict(list)
			for broken in user_facing_broken:
				by_file[broken.source_file].append(broken)

			for source_file, links in sorted(by_file.items()):
				report += f"### {Path(source_file).name}\n\n"
				for broken in links[:10]:  # Limit to first 10 per file
					report += f"- **Link:** `[[{broken.link_text}]]` (Line {broken.line_number})\n"
					report += f"  - **Suggestion:** {broken.suggested_fix}\n"
				if len(links) > 10:
					report += f"\n  ... and {len(links) - 10} more broken links\n"
				report += "\n"

		# Auto-generated broken links (for reference only)
		if auto_gen_broken:
			report += "## Auto-Generated File Issues (Reference Only)\n\n"
			report += f"Found {len(auto_gen_broken)} broken links in auto-generated files. "
			report += "These can be safely ignored as they will be regenerated.\n\n"

		# Orphaned files section
		if network.orphaned_files:
			report += "## Orphaned Files\n\n"
			report += "These files are not linked from any other document:\n\n"
			for orphaned in sorted(network.orphaned_files):
				report += f"- `{Path(orphaned).name}`\n"
			report += "\n**Note:** Some files (like README.md, index files) are intentionally entry points and don't need incoming links.\n\n"

		# Network analysis
		report += "## Network Analysis\n\n"

		# Most connected files
		if network.incoming_links:
			most_connected = sorted(network.incoming_links.items(), key=lambda x: len(x[1]), reverse=True)[:5]

			report += "### Most Connected Files\n\n"
			for file_path, links in most_connected:
				report += f"- `{Path(file_path).name}` ({len(links)} incoming links)\n"
			report += "\n"

		# Files with most outgoing links
		if network.outgoing_links:
			most_outgoing = sorted(network.outgoing_links.items(), key=lambda x: len(x[1]), reverse=True)[:5]

			report += "### Most Outgoing Links\n\n"
			for file_path, links in most_outgoing:
				report += f"- `{Path(file_path).name}` ({len(links)} outgoing links)\n"
			report += "\n"

		# Recommendations
		report += "## Recommendations\n\n"
		if broken_count > 0:
			report += "1. Fix broken WikiLinks using the suggested alternatives\n"
			report += "2. Create missing documentation files if needed\n"

		if network.orphaned_files:
			report += "3. Add WikiLinks to orphaned files from relevant documents\n"
			report += "4. Consider if orphaned files should be integrated into the main documentation flow\n"

		if health_score < 80:
			report += "5. Review the overall documentation structure\n"
			report += "6. Consider creating index files to improve navigation\n"

		return report

	def calculate_network_health(self, network: WikiLinkNetwork) -> float:
		"""Calculate network health score based on user-facing documentation only"""
		total_files = len(network.incoming_links) + len(network.orphaned_files)
		if total_files == 0:
			return 100.0

		# Only count user-facing broken links for health score
		user_facing_broken = [b for b in network.broken_links if Path(b.source_file).name not in self.auto_generated_files]

		# Calculate metrics
		total_links = sum(len(links) for links in network.outgoing_links.values())
		broken_count = len(user_facing_broken)
		orphaned_count = len(network.orphaned_files)

		# Factors affecting health
		broken_ratio = (broken_count / total_links) if total_links > 0 else 0
		orphaned_ratio = (orphaned_count / total_files) if total_files > 0 else 0

		# Penalties (scaled to be reasonable)
		broken_links_penalty = min(broken_ratio * 40, 40)  # Max 40 points for broken links
		orphaned_penalty = min(orphaned_ratio * 20, 20)  # Max 20 points for orphaned files

		# Connectivity bonus
		avg_links = total_links / len(network.outgoing_links) if network.outgoing_links else 0
		connectivity_bonus = min(avg_links * 2, 20)  # Up to 20 points for good connectivity

		# Calculate score
		base_score = 60  # Start with 60, allow room for bonuses
		score = base_score - broken_links_penalty - orphaned_penalty + connectivity_bonus

		return max(0.0, min(100.0, score))

	def get_current_timestamp(self) -> str:
		"""Get current timestamp"""
		from datetime import datetime

		return datetime.now().isoformat()

	def generate_network_graph(self, network: WikiLinkNetwork) -> str:
		"""Generate a Mermaid graph of the WikiLink network"""
		graph = "graph TD\n"

		# Add nodes
		all_files = set(network.incoming_links.keys()) | set(network.outgoing_links.keys())

		for file_path in all_files:
			file_name = Path(file_path).stem
			node_id = file_name.replace("-", "_").replace(" ", "_")
			graph += f'    {node_id}["{file_name}"]\n'

		# Add edges
		for source, targets in network.outgoing_links.items():
			source_name = Path(source).stem
			source_id = source_name.replace("-", "_").replace(" ", "_")

			for target in targets:
				target_file = self.resolve_wikilink(target, Path(source))
				if target_file:
					target_name = target_file.stem
					target_id = target_name.replace("-", "_").replace(" ", "_")
					graph += f"    {source_id} --> {target_id}\n"

		return graph


def main():
	"""Main WikiLink validation process"""
	validator = WikiLinkValidator()

	try:
		# Validate all WikiLinks
		network = validator.validate_all_wikilinks()

		# Generate report
		report = validator.generate_validation_report(network)

		# Save report
		report_path = Path("docs/wikilink-report.md")
		report_path.parent.mkdir(parents=True, exist_ok=True)
		report_path.write_text(report)

		# Generate network graph
		graph = validator.generate_network_graph(network)
		graph_path = Path("docs/wikilink-network.md")
		graph_content = "# WikiLink Network Graph\n\n```mermaid\n" + graph + "\n```\n"
		graph_path.write_text(graph_content)

		# Save detailed results
		results_data = {
			"generated_at": validator.get_current_timestamp(),
			"network": {
				"incoming_links": network.incoming_links,
				"outgoing_links": network.outgoing_links,
				"orphaned_files": network.orphaned_files,
				"broken_links": [
					{
						"source_file": b.source_file,
						"link_text": b.link_text,
						"target_exists": b.target_exists,
						"suggested_fix": b.suggested_fix,
						"line_number": b.line_number,
					}
					for b in network.broken_links
				],
			},
		}

		results_path = Path("docs/wikilink-results.json")
		with open(results_path, "w") as f:
			json.dump(results_data, f, indent=2)

		# Print summary
		health_score = validator.calculate_network_health(network)
		total_broken = len(network.broken_links)
		user_facing_broken = len([b for b in network.broken_links if Path(b.source_file).name not in validator.auto_generated_files])
		orphaned_count = len(network.orphaned_files)

		print(f"🔗 WikiLink Network Health: {health_score:.1f}/100")
		print(f"📊 Broken Links (User-Facing): {user_facing_broken}")
		print(f"📊 Broken Links (Auto-Generated): {total_broken - user_facing_broken}")
		print(f"📄 Orphaned Files: {orphaned_count}")
		print(f"📝 Generated validation report and network graph")

		# Exit with error code only if there are user-facing issues
		if user_facing_broken > 10 or orphaned_count > 5:
			print("⚠️  WikiLink issues found in user-facing documentation. Check wikilink-report.md")
			sys.exit(1)
		elif user_facing_broken > 0:
			print("✓ Minor issues found. Check wikilink-report.md for details")
		else:
			print("✅ All user-facing documentation links are valid!")

	except Exception as e:
		print(f"❌ WikiLink validation failed: {e}")
		import traceback

		traceback.print_exc()
		sys.exit(1)


if __name__ == "__main__":
	main()
