#!/usr/bin/env python3
"""
Script to fix README formatting issues to enterprise-grade standards
"""

import re


def fix_readme_formatting(input_file, output_file):
	"""Fix common markdown formatting issues"""

	with open(input_file, "r", encoding="utf-8") as f:
		content = f.read()

	# Fix 1: Remove emoji from anchor links in TOC
	content = re.sub(r"\(#[🚀📋🎯📚⚙️📖💡🧪🔧🐛🚀⚡🔒🤝📝📞🔄📊]+-([-\w]+)\)", r"(#\1)", content)

	# Fix 2: Add blank lines before headings (h4)
	content = re.sub(r"([^\n])\n(####)", r"\1\n\n\2", content)

	# Fix 3: Add blank lines after headings (h4)
	content = re.sub(r"(####[^\n]+)\n([^-\n#])", r"\1\n\n\2", content)

	# Fix 4: Add blank lines before lists
	content = re.sub(r"([^\n:])\n(- \*\*)", r"\1\n\n\2", content)
	content = re.sub(r"([^\n:])\n(- \w)", r"\1\n\n\2", content)

	# Fix 5: Add blank lines after lists
	content = re.sub(
		r"(\n- [^\n]+)\n([^\n-])", lambda m: m.group(1) + "\n\n" + m.group(2) if not m.group(2).startswith("  ") else m.group(0), content
	)

	# Fix 6: Fix code blocks without language
	content = re.sub(r"\n```\n(Configuration|Checks)", r"\n```text\n\1", content)

	# Fix 7: Convert bold text section headers to proper h5 headings
	content = re.sub(r"\n\*\*Option ([A-Z]):", r"\n##### Option \1:", content)
	content = re.sub(r"\n\*\*Example:", r"\n##### Example:", content)
	content = re.sub(r"\n\*\*Frontend Tier\*\*:", r"\n**Frontend Tier**:", content)

	# Fix 8: Fix ordered list numbering issues
	def fix_ordered_list(match):
		lines = match.group(0).split("\n")
		fixed_lines = []
		counter = 1
		for line in lines:
			if re.match(r"^\d+\.", line):
				fixed_lines.append(re.sub(r"^\d+\.", f"{counter}.", line))
				counter += 1
			else:
				fixed_lines.append(line)
		return "\n".join(fixed_lines)

	# Fix ordered lists
	content = re.sub(r"(\n\d+\..*(?:\n(?:\d+\..*|  .*))*)", fix_ordered_list, content)

	# Fix 9: Remove trailing spaces
	content = re.sub(r" +\n", "\n", content)

	# Fix 10: Ensure proper spacing around horizontal rules
	content = re.sub(r"\n---\n", "\n\n---\n\n", content)
	content = re.sub(r"\n\n\n+", "\n\n", content)  # Remove excessive newlines

	with open(output_file, "w", encoding="utf-8") as f:
		f.write(content)

	print(f"✅ Fixed README formatting")
	print(f"   Input: {input_file}")
	print(f"   Output: {output_file}")


if __name__ == "__main__":
	fix_readme_formatting("README_NEW.md", "README_FIXED.md")
