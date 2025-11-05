"""
Docstring Enhancement Utility Module.

This module provides utilities for generating Google-style docstrings and basic
type-hint analysis. It is intentionally lightweight and safe to import.
"""

import ast
import inspect
import sys
from dataclasses import fields, is_dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, get_type_hints

# Handle different Python versions for GenericAlias checks
if sys.version_info >= (3, 9):
	from types import GenericAlias

	def is_generic_alias(obj: Any) -> bool:
		return isinstance(obj, (GenericAlias, type(List[int])))
else:

	def is_generic_alias(obj: Any) -> bool:  # type: ignore[no-redef]
		return hasattr(obj, "__origin__")


class TypeAnalyzer:
	"""Utility class for analyzing and formatting type hints."""

	@staticmethod
	def infer_type(value: Any) -> Type:
		if value is None:
			return type(None)
		if isinstance(value, (int, float, str, bool)):
			return type(value)
		if isinstance(value, list):
			elem_types = {TypeAnalyzer.infer_type(x) for x in value[:5]}  # sample
			if len(elem_types) == 1:
				return List[next(iter(elem_types))]  # type: ignore[index]
			return List[Any]
		if isinstance(value, dict):
			if not value:
				return Dict[Any, Any]
			key_type = TypeAnalyzer.infer_type(next(iter(value.keys())))
			val_type = TypeAnalyzer.infer_type(next(iter(value.values())))
			return Dict[key_type, val_type]  # type: ignore[index]
		if isinstance(value, tuple):
			return Tuple[tuple(TypeAnalyzer.infer_type(x) for x in value)]  # type: ignore[index]
		return type(value)

	@staticmethod
	def get_callable_types(func: Callable) -> Dict[str, Type]:
		try:
			hints = get_type_hints(func)
			if not hints:
				sig = inspect.signature(func)
				hints = {}
				for name, param in sig.parameters.items():
					if param.annotation != inspect.Parameter.empty:
						hints[name] = param.annotation
					elif param.default != inspect.Parameter.empty:
						hints[name] = TypeAnalyzer.infer_type(param.default)
			return hints
		except Exception:
			return {}

	@staticmethod
	def format_type(type_hint: Type) -> str:
		if type_hint == Any:
			return "Any"
		try:
			if is_generic_alias(type_hint):
				origin = getattr(type_hint, "__origin__", None)
				args = getattr(type_hint, "__args__", ())
				if origin is Union:
					return " | ".join(TypeAnalyzer.format_type(t) for t in args)
				if origin in (list, List):
					return f"List[{TypeAnalyzer.format_type(args[0])}]" if args else "List[Any]"
				if origin in (dict, Dict):
					kt = TypeAnalyzer.format_type(args[0]) if args else "Any"
					vt = TypeAnalyzer.format_type(args[1]) if len(args) > 1 else "Any"
					return f"Dict[{kt}, {vt}]"
		except Exception:
			pass
		return getattr(type_hint, "__name__", str(type_hint))


class DocstringTemplate:
	"""Generator for Google-style docstrings."""

	@staticmethod
	def function_docstring(
		description: str,
		args: Optional[List[Tuple[str, str, str]]] = None,
		returns: Optional[Tuple[str, str]] = None,
		raises: Optional[List[Tuple[str, str]]] = None,
		examples: Optional[List[str]] = None,
		note: Optional[str] = None,
		warning: Optional[str] = None,
	) -> str:
		lines: List[str] = ['"""', description, ""]

		if args:
			lines.append("Args:")
			for name, arg_type, desc in args:
				lines.append(f"    {name} ({arg_type}): {desc}")
			lines.append("")

		if returns:
			ret_type, ret_desc = returns
			lines.append("Returns:")
			lines.append(f"    {ret_type}: {ret_desc}")
			lines.append("")

		if raises:
			lines.append("Raises:")
			for exc_type, exc_desc in raises:
				lines.append(f"    {exc_type}: {exc_desc}")
			lines.append("")

		if examples:
			lines.append("Examples:")
			for example in examples:
				for line in example.split("\n"):
					lines.append(f"    {line}")
			lines.append("")

		if note:
			lines.append("Note:")
			lines.append(f"    {note}")
			lines.append("")

		if warning:
			lines.append("Warning:")
			lines.append(f"    {warning}")
			lines.append("")

		if lines and lines[-1] == "":
			lines.pop()
		lines.append('"""')
		return "\n".join(lines)

	@staticmethod
	def class_docstring(
		description: str,
		attributes: Optional[List[Tuple[str, str, str]]] = None,
		examples: Optional[List[str]] = None,
		note: Optional[str] = None,
	) -> str:
		lines: List[str] = ['"""', description, ""]
		if attributes:
			lines.append("Attributes:")
			for name, attr_type, desc in attributes:
				lines.append(f"    {name} ({attr_type}): {desc}")
			lines.append("")
		if examples:
			lines.append("Examples:")
			for example in examples:
				for line in example.split("\n"):
					lines.append(f"    {line}")
			lines.append("")
		if note:
			lines.append("Note:")
			lines.append(f"    {note}")
			lines.append("")
		if lines and lines[-1] == "":
			lines.pop()
		lines.append('"""')
		return "\n".join(lines)


class DocstringTransformer(ast.NodeTransformer):
	"""AST transformer that adds basic docstrings when missing."""

	def __init__(self, enhancer: "DocstringEnhancer"):
		self.enhancer = enhancer

	def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:  # type: ignore[override]
		self.generic_visit(node)
		if not ast.get_docstring(node):
			# Basic placeholder using function name
			doc = self.enhancer.template.function_docstring(description=f"{node.name.replace('_', ' ').title()} function.")
			node.body.insert(0, ast.Expr(value=ast.Constant(value=doc)))
		return node

	def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:  # type: ignore[override]
		self.generic_visit(node)
		if not ast.get_docstring(node):
			doc = self.enhancer.template.class_docstring(description=f"{node.name} class.")
			node.body.insert(0, ast.Expr(value=ast.Constant(value=doc)))
		return node


class DocstringEnhancer:
	"""Utility for enhancing docstrings and type hints in Python code."""

	def __init__(self) -> None:
		self.type_analyzer = TypeAnalyzer()
		self.template = DocstringTemplate()

	def enhance_module(self, module_path: str) -> str:
		with open(module_path, "r", encoding="utf-8") as f:
			code = f.read()
		tree = ast.parse(code)
		transformer = DocstringTransformer(self)
		enhanced_tree = transformer.visit(tree)
		return ast.unparse(enhanced_tree)

	def generate_function_docstring_from_callable(self, func: Callable) -> str:
		sig = inspect.signature(func)
		desc = func.__doc__ or f"Implementation of {func.__name__}."
		hints = self.type_analyzer.get_callable_types(func)
		args: List[Tuple[str, str, str]] = []
		for name, param in sig.parameters.items():
			if name in ("self", "cls"):
				continue
			param_type = hints.get(name, Any)
			args.append((name, self.type_analyzer.format_type(param_type), f"The {name} parameter"))
		returns: Optional[Tuple[str, str]] = None
		if "return" in hints:
			returns = (self.type_analyzer.format_type(hints["return"]), "The function's return value")
		return self.template.function_docstring(description=desc, args=args or None, returns=returns)

	def enhance_class_docstring_from_type(self, cls: Type) -> str:
		desc = cls.__doc__ or f"Implementation of {cls.__name__}."
		attributes: List[Tuple[str, str, str]] = []
		if is_dataclass(cls):
			for f in fields(cls):  # type: ignore[assignment]
				attributes.append((f.name, self.type_analyzer.format_type(f.type), f"The {f.name} field"))
		return self.template.class_docstring(description=desc, attributes=attributes or None)


def get_docstring_pattern(pattern_name: str) -> Dict[str, Any]:
	"""Return predefined docstring pattern configuration."""
	COMMON_DOCSTRING_PATTERNS: Dict[str, Dict[str, Any]] = {
		"api_endpoint": {"description": "Template for FastAPI endpoint functions"},
		"service_method": {
			"description": "Business logic method in a service class",
			"raises": [("ValidationError", "When input validation fails"), ("ServiceError", "When service operation fails")],
		},
		"repository_method": {
			"description": "Data access method in a repository class",
			"raises": [("DatabaseError", "When database operation fails"), ("NotFoundError", "When requested resource is not found")],
		},
		"utility_function": {"description": "Utility function for common operations"},
	}
	if pattern_name not in COMMON_DOCSTRING_PATTERNS:
		raise KeyError(f"Unknown docstring pattern: {pattern_name}")
	return COMMON_DOCSTRING_PATTERNS[pattern_name]
