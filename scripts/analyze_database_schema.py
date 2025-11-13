#!/usr/bin/env python3
"""
Automated database schema analysis and documentation generation.
Analyzes SQLAlchemy models and generates comprehensive schema documentation.
"""

import inspect
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

# Add backend to path
sys.path.insert(0, "backend")

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship


@dataclass
class TableInfo:
	"""Database table metadata"""

	name: str
	class_name: str
	file_path: str
	columns: List[Dict[str, Any]]
	relationships: List[Dict[str, Any]]
	indexes: List[Dict[str, Any]]
	description: str = ""


@dataclass
class SchemaInfo:
	"""Complete database schema information"""

	tables: List[TableInfo]
	generated_at: str


class SchemaAnalyzer:
	"""Analyzes SQLAlchemy models to extract schema information"""

	def __init__(self, models_path: str):
		self.models_path = Path(models_path)
		self.tables: List[TableInfo] = []

	def analyze_schema(self) -> SchemaInfo:
		"""Analyze all SQLAlchemy models"""
		self.tables = []

		# Find all model files
		model_files = self._find_model_files()

		for model_file in model_files:
			tables = self._analyze_model_file(model_file)
			self.tables.extend(tables)

		return SchemaInfo(tables=self.tables, generated_at=datetime.utcnow().isoformat())

	def _find_model_files(self) -> List[Path]:
		"""Find all model definition files"""
		model_files = []

		if self.models_path.exists():
			for file_path in self.models_path.rglob("*.py"):
				if file_path.name != "__init__.py":
					model_files.append(file_path)

		return model_files

	def _analyze_model_file(self, file_path: Path) -> List[TableInfo]:
		"""Analyze a single model file"""
		tables = []

		try:
			# Import the module
			module_name = self._get_module_name(file_path)
			spec = importlib.util.spec_from_file_location(module_name, file_path)
			module = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(module)

			# Find all SQLAlchemy model classes
			for name, obj in inspect.getmembers(module):
				if inspect.isclass(obj) and hasattr(obj, "__tablename__") and hasattr(obj, "__table__"):
					table_info = self._analyze_model_class(obj, file_path)
					if table_info:
						tables.append(table_info)

		except Exception as e:
			print(f"Error analyzing {file_path}: {e}")

		return tables

	def _analyze_model_class(self, model_class: Type, file_path: Path) -> Optional[TableInfo]:
		"""Analyze a single SQLAlchemy model class"""
		try:
			table_name = getattr(model_class, "__tablename__", None)
			if not table_name:
				return None

			# Extract columns
			columns = self._extract_columns(model_class)

			# Extract relationships
			relationships = self._extract_relationships(model_class)

			# Extract indexes
			indexes = self._extract_indexes(model_class)

			# Extract description from docstring
			description = getattr(model_class, "__doc__", "") or ""

			return TableInfo(
				name=table_name,
				class_name=model_class.__name__,
				file_path=str(file_path),
				columns=columns,
				relationships=relationships,
				indexes=indexes,
				description=description.strip(),
			)

		except Exception as e:
			print(f"Error analyzing model {model_class.__name__}: {e}")
			return None

	def _extract_columns(self, model_class: Type) -> List[Dict[str, Any]]:
		"""Extract column information from model"""
		columns = []

		# Get table columns
		table = getattr(model_class, "__table__", None)
		if table:
			for column in table.columns:
				column_info = {
					"name": column.name,
					"type": str(column.type),
					"nullable": column.nullable,
					"primary_key": column.primary_key,
					"unique": column.unique,
					"default": str(column.default) if column.default else None,
					"foreign_keys": [fk.target_fullname for fk in column.foreign_keys],
				}
				columns.append(column_info)

		return columns

	def _extract_relationships(self, model_class: Type) -> List[Dict[str, Any]]:
		"""Extract relationship information"""
		relationships = []

		# Check for relationship attributes
		for attr_name in dir(model_class):
			if not attr_name.startswith("_"):
				attr_value = getattr(model_class, attr_name)
				if hasattr(attr_value, "mapper") and hasattr(attr_value, "table"):
					# This is a relationship
					relationship_info = {
						"name": attr_name,
						"target_table": attr_value.table.name,
						"relationship_type": "one-to-many",  # Default assumption
						"backref": getattr(attr_value, "backref", None),
					}
					relationships.append(relationship_info)

		return relationships

	def _extract_indexes(self, model_class: Type) -> List[Dict[str, Any]]:
		"""Extract index information"""
		indexes = []

		table = getattr(model_class, "__table__", None)
		if table and hasattr(table, "indexes"):
			for index in table.indexes:
				index_info = {"name": index.name, "columns": [col.name for col in index.columns], "unique": index.unique}
				indexes.append(index_info)

		return indexes

	def _get_module_name(self, file_path: Path) -> str:
		"""Get module name from file path"""
		return str(file_path).replace("/", ".").replace(".py", "")


def generate_markdown_docs(schema: SchemaInfo):
	"""Generate Markdown documentation from schema"""
	docs_path = Path("docs/database")
	docs_path.mkdir(parents=True, exist_ok=True)

	# Generate index
	with open(docs_path / "README.md", "w") as f:
		f.write("# Database Schema Documentation\n\n")
		f.write("This documentation is automatically generated from SQLAlchemy models.\n\n")
		f.write("## Tables\n\n")

		for table in schema.tables:
			f.write(f"- [{table.name}]({table.name}.md) - {table.class_name}\n")

		f.write(f"\n## Summary\n\n")
		f.write(f"- **Total Tables:** {len(schema.tables)}\n")
		f.write(f"- **Generated:** {schema.generated_at}\n")

	# Generate table documentation
	for table in schema.tables:
		with open(docs_path / f"{table.name}.md", "w") as f:
			f.write(f"# {table.name}\n\n")
			f.write(f"**Model Class:** `{table.class_name}`\n\n")
			f.write(f"**File:** `{table.file_path}`\n\n")

			if table.description:
				f.write(f"## Description\n\n{table.description}\n\n")

			f.write("## Columns\n\n")
			f.write("| Column | Type | Nullable | Primary Key | Unique | Default | Foreign Keys |\n")
			f.write("|--------|------|----------|-------------|--------|---------|--------------|\n")

			for col in table.columns:
				fk_str = ", ".join(col["foreign_keys"]) if col["foreign_keys"] else "-"
				f.write(
					f"| {col['name']} | {col['type']} | {col['nullable']} | {col['primary_key']} | {col['unique']} | {col['default'] or '-'} | {fk_str} |\n"
				)

			f.write("\n")

			if table.relationships:
				f.write("## Relationships\n\n")
				for rel in table.relationships:
					f.write(f"- **{rel['name']}**: {rel['relationship_type']} relationship with `{rel['target_table']}`\n")
				f.write("\n")

			if table.indexes:
				f.write("## Indexes\n\n")
				for idx in table.indexes:
					unique_str = " (unique)" if idx["unique"] else ""
					f.write(f"- **{idx['name']}**: {', '.join(idx['columns'])}{unique_str}\n")
				f.write("\n")

			f.write("---\n\n")
			f.write("*Auto-generated from SQLAlchemy model*")


def main():
	"""Main entry point"""
	analyzer = SchemaAnalyzer("backend/app/models")

	print("🔍 Analyzing database schema...")
	schema = analyzer.analyze_schema()

	# Save JSON data
	output_path = Path("docs/database/schema.json")
	output_path.parent.mkdir(parents=True, exist_ok=True)

	with open(output_path, "w") as f:
		json.dump(asdict(schema), f, indent=2)

	print(f"✅ Analyzed {len(schema.tables)} database tables")

	# Generate Markdown documentation
	generate_markdown_docs(schema)

	print("✅ Generated database schema documentation")


if __name__ == "__main__":
	main()
