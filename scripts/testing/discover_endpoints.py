#!/usr/bin/env python3
"""
Lightweight endpoint discovery tool.

Scans the `backend/app` directory for FastAPI APIRouter instances and
route decorators like `@router.get`, `@router.post`, etc., and emits a
JSON endpoint map to `reports/endpoint_map.json`.

This is a best-effort static analysis (regex-based) and doesn't require
running the application. It complements runtime OpenAPI generation.
"""

import ast
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_APP = ROOT / "backend" / "app"
OUTPUT = ROOT / "reports" / "endpoint_map.json"


def find_python_files(base: Path):
	for p in base.rglob("*.py"):
		yield p


ROUTE_DECORATOR_RE = re.compile(r"@(?P<router>\w+)\.(?P<method>get|post|put|delete|patch|options|head)\((?P<args>.*)\)")
PREFIX_RE = re.compile(r"router\s*=\s*APIRouter\((?P<args>.*)\)")
PREFIX_ARG_RE = re.compile(r"prefix\s*=\s*['\"](?P<prefix>[^'\"]+)['\"]")
TAGS_ARG_RE = re.compile(r"tags\s*=\s*\[(?P<tags>[^\]]*)\]")


def extract_routes_from_file(path: Path):
	text = path.read_text(encoding="utf-8")
	routes = []

	# try to find local variable name for router and its prefix/tags
	router_prefixes = {}

	for m in re.finditer(r"(\w+)\s*=\s*APIRouter\((.*?)\)", text, flags=re.S):
		name = m.group(1)
		args = m.group(2)
		prefix_m = PREFIX_ARG_RE.search(args)
		tags_m = TAGS_ARG_RE.search(args)
		prefix = prefix_m.group("prefix") if prefix_m else ""
		tags_raw = tags_m.group("tags") if tags_m else ""
		# parse tags into list
		tags = [t.strip().strip("\"'") for t in tags_raw.split(",") if t.strip()] if tags_raw else []
		router_prefixes[name] = {"prefix": prefix, "tags": tags}

	# find route decorators
	for m in ROUTE_DECORATOR_RE.finditer(text):
		router_var = m.group("router")
		method = m.group("method").upper()
		args = m.group("args")

		# Extract path argument if present
		path_m = re.search(r"['\"](?P<path>[^'\"]+)['\"]", args)
		route_path = path_m.group("path") if path_m else ""

		prefix = router_prefixes.get(router_var, {}).get("prefix", "")
		tags = router_prefixes.get(router_var, {}).get("tags", [])

		full_path = (prefix + route_path).replace("//", "/") if prefix or route_path else None

		# try to find function name and docstring
		# naive: find next def after decorator
		post = text[m.end() :]
		def_m = re.search(r"def\s+(?P<name>\w+)\s*\((?P<args>[^)]*)\):", post)
		func_name = def_m.group("name") if def_m else None
		doc = None
		if def_m:
			# attempt to extract simple docstring
			func_block = post[def_m.end() : def_m.end() + 400]
			ds = re.search(r"\"\"\"(?P<doc>.*?)\"\"\"", func_block, flags=re.S)
			if ds:
				doc = ds.group("doc").strip()

		routes.append(
			{
				"file": str(path.relative_to(ROOT)),
				"router_var": router_var,
				"method": method,
				"path": full_path,
				"function": func_name,
				"tags": tags,
				"doc": doc,
			}
		)

	return routes


def categorize(route):
	tags = route.get("tags") or []
	if any(t.lower().startswith("auth") or "auth" in t.lower() for t in tags):
		return "authentication"
	if any(t.lower() in ("jobs", "applications", "jobs-api", "jobs") for t in tags):
		return "jobs"
	if any("analytics" in t.lower() for t in tags):
		return "analytics"
	if any("admin" in t.lower() for t in tags):
		return "admin"
	if any("health" in t.lower() for t in tags):
		return "health"
	return "other"


def main():
	all_routes = []
	backend_dir = BACKEND_APP
	if not backend_dir.exists():
		print(f"Backend app directory not found: {backend_dir}")
		return 1

	for py in find_python_files(backend_dir):
		try:
			routes = extract_routes_from_file(py)
			all_routes.extend(routes)
		except Exception as e:
			print(f"Warning: failed to parse {py}: {e}")

	# normalize and filter
	cleaned = []
	for r in all_routes:
		if not r["path"]:
			# try to infer from function or skip
			continue
		r["category"] = categorize(r)
		cleaned.append(r)

	OUTPUT.parent.mkdir(parents=True, exist_ok=True)
	with open(OUTPUT, "w", encoding="utf-8") as f:
		json.dump(cleaned, f, indent=2)

	print(f"Discovered {len(cleaned)} routes. Map written to: {OUTPUT}")
	# print a short summary
	from collections import Counter

	cats = Counter(r["category"] for r in cleaned)
	print("Categories:")
	for k, v in cats.items():
		print(f"  {k}: {v}")

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
