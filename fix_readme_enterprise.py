#!/usr/bin/env python3
"""
Comprehensive README formatting fix for enterprise-grade documentation
"""

import re


def fix_all_issues(content):
	"""Apply all formatting fixes"""

	# Fix 1: Fix TOC links - remove emoji from fragments
	toc_replacements = {
		"#-project-overview": "#project-overview",
		"#-visual-documentation": "#visual-documentation",
		"#-technical-architecture": "#technical-architecture",
		"#-project-structure": "#project-structure",
		"#-component-deep-dive": "#component-deep-dive",
		"#-prerequisites--dependencies": "#prerequisites--dependencies",
		"#-installation--setup": "#installation--setup",
		"#-external-apis--services": "#external-apis--services",
		"#-configuration": "#configuration",
		"#-usage--functionality": "#usage--functionality",
		"#-api-documentation": "#api-documentation",
		"#-code-examples--tutorials": "#code-examples--tutorials",
		"#-testing": "#testing",
		"#-development-workflow": "#development-workflow",
		"#-troubleshooting": "#troubleshooting",
		"#-deployment": "#deployment",
		"#-performance--optimization": "#performance--optimization",
		"#-security": "#security",
		"#-contributing": "#contributing",
		"#-technical-decisions--rationale": "#technical-decisions--rationale",
		"#-changelog--versioning": "#changelog--versioning",
		"#-resources": "#resources",
		"#-license": "#license",
		"#-support--contact": "#support--contact",
		"#-key-features": "#key-features",
	}

	for old, new in toc_replacements.items():
		content = content.replace(old, new)

	# Fix 2: Replace ASCII diagram code blocks with proper language
	content = re.sub(r"```\n┌", r"```text\n┌", content)
	content = re.sub(r"```\n\s*├", r"```text\n├", content)
	content = re.sub(r"```\n\s*└", r"```text\n└", content)
	content = re.sub(r"```\n\s*│", r"```text\n│", content)
	content = re.sub(r"```\n\s*▲", r"```text\n▲", content)
	content = re.sub(r"```\n\s*▼", r"```text\n▼", content)
	content = re.sub(r"```\n\[", r"```text\n[", content)

	# Fix 3: Fix code blocks that are validation output or configuration
	content = re.sub(r"```\n✅ Configuration", r"```text\n✅ Configuration", content)
	content = re.sub(r"```\n⚠️", r"```text\n⚠️", content)
	content = re.sub(r"```\nConfiguration", r"```text\nConfiguration", content)

	# Fix 4: Remove emoji from heading IDs (the actual headings should keep emoji)
	# We'll replace the TOC entries but keep the actual section headings with emoji

	# Fix 5: Rename duplicate headings to make them unique
	# Find and fix "Security Architecture" duplicates
	lines = content.split("\n")
	security_arch_count = 0
	for i, line in enumerate(lines):
		if line.strip() == "### Security Architecture":
			security_arch_count += 1
			if security_arch_count == 2:
				lines[i] = "### Security Implementation"

	# Find and fix "Rate Limiting" duplicates
	rate_limit_count = 0
	for i, line in enumerate(lines):
		if line.strip() == "### Rate Limiting":
			rate_limit_count += 1
			if rate_limit_count == 2:
				lines[i] = "### API Rate Limiting"

	content = "\n".join(lines)

	# Fix 6: Ensure quick start link is correct
	content = content.replace("#quick-start-5-minutes", "#-quick-start-5-minutes")

	return content


def main():
	"""Main function to fix README"""
	input_file = "README_NEW.md"
	output_file = "README_ENTERPRISE.md"

	print("🔧 Starting enterprise-grade README formatting...")

	with open(input_file, "r", encoding="utf-8") as f:
		content = f.read()

	print("📝 Applying formatting fixes...")
	content = fix_all_issues(content)

	with open(output_file, "w", encoding="utf-8") as f:
		f.write(content)

	print(f"✅ Enterprise-grade README created successfully!")
	print(f"   Input: {input_file}")
	print(f"   Output: {output_file}")
	print(f"\n📊 Fixes applied:")
	print(f"   • Fixed TOC link fragments")
	print(f"   • Added language specifiers to code blocks")
	print(f"   • Fixed duplicate heading names")
	print(f"   • Formatted ASCII diagrams properly")


if __name__ == "__main__":
	main()
