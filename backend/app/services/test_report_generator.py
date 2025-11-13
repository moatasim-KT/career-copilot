"""Simple test report generator

This module reads the existing `reports/api_test_results.txt` (if present)
and produces a small JSON summary and an HTML report. It also supports
exporting CSV and JSON versions.

This is intentionally lightweight and defensive — it will return an
empty summary if no test artifacts are available.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

REPORT_FILE = Path(__file__).parents[2] / "reports" / "api_test_results.txt"


@dataclass
class TestResultLine:
	raw: str
	status: str | None = None
	method: str | None = None
	path: str | None = None
	message: str | None = None


def _parse_line(line: str) -> TestResultLine:
	# Very small heuristic parser for lines like:
	# ✓ PASS  GET     /api/v1/jobs                              [200] - OK
	# ✗ FAIL  GET     /api/v1/admin/cache/stats                  [404] - Cache stats (no auth)
	s = line.strip()
	if not s:
		return TestResultLine(raw=line)

	status = None
	if s.startswith("✓") or "PASS" in s:
		status = "pass"
	elif s.startswith("✗") or "FAIL" in s:
		status = "fail"

	# Attempt to extract method and path
	parts = s.split()
	method = None
	path = None
	message = None
	for i, p in enumerate(parts):
		if p in ("GET", "POST", "PUT", "DELETE", "PATCH"):
			method = p
			# next token usually the path
			if i + 1 < len(parts):
				path = parts[i + 1]
			break

	if "-" in s:
		# everything after the dash is message
		try:
			msg = s.split("-", 1)[1].strip()
			message = msg
		except Exception:
			message = None

	return TestResultLine(raw=line, status=status, method=method, path=path, message=message)


def read_test_artifact() -> List[TestResultLine]:
	if not REPORT_FILE.exists():
		return []

	lines: List[TestResultLine] = []
	try:
		with REPORT_FILE.open("r", encoding="utf-8") as f:
			for ln in f:
				lines.append(_parse_line(ln))
	except Exception:
		return []

	return lines


def generate_summary(lines: List[TestResultLine]) -> Dict[str, Any]:
	total = len(lines)
	passed = sum(1 for l in lines if l.status == "pass")
	failed = sum(1 for l in lines if l.status == "fail")

	by_endpoint: Dict[str, Dict[str, Any]] = {}
	for l in lines:
		key = l.path or l.raw
		if key not in by_endpoint:
			by_endpoint[key] = {"calls": 0, "last_status": None, "messages": []}
		by_endpoint[key]["calls"] += 1
		if l.status:
			by_endpoint[key]["last_status"] = l.status
		if l.message:
			by_endpoint[key]["messages"].append(l.message)

	return {
		"total_lines": total,
		"passed": passed,
		"failed": failed,
		"by_endpoint": by_endpoint,
	}


def generate_html_report(summary: Dict[str, Any]) -> str:
	html = [
		"<html><head><meta charset='utf-8'><title>API Test Report</title>",
		"<style>body{font-family:Arial,Helvetica,sans-serif}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:8px}</style>",
		"</head><body>",
	]
	html.append(f"<h1>API Test Report</h1>")
	html.append(f"<p>Total lines: {summary.get('total_lines', 0)} - Passed: {summary.get('passed', 0)} - Failed: {summary.get('failed', 0)}</p>")

	html.append("<h2>Endpoint Summary</h2>")
	html.append("<table><thead><tr><th>Endpoint</th><th>Calls</th><th>Last Status</th><th>Messages</th></tr></thead><tbody>")
	for endpoint, data in summary.get("by_endpoint", {}).items():
		msgs = "<br>".join(data.get("messages", []))
		html.append(f"<tr><td>{endpoint}</td><td>{data.get('calls')}</td><td>{data.get('last_status')}</td><td>{msgs}</td></tr>")
	html.append("</tbody></table>")

	html.append("</body></html>")
	return "\n".join(html)


def export_json(summary: Dict[str, Any], out: Path) -> bool:
	try:
		out.parent.mkdir(parents=True, exist_ok=True)
		with out.open("w", encoding="utf-8") as f:
			json.dump(summary, f, indent=2, default=str)
		return True
	except Exception:
		return False


def export_csv(summary: Dict[str, Any], out: Path) -> bool:
	try:
		out.parent.mkdir(parents=True, exist_ok=True)
		rows = []
		for endpoint, data in summary.get("by_endpoint", {}).items():
			rows.append(
				{
					"endpoint": endpoint,
					"calls": data.get("calls"),
					"last_status": data.get("last_status"),
					"messages": " | ".join(data.get("messages", [])),
				}
			)

		with out.open("w", newline="", encoding="utf-8") as f:
			writer = csv.DictWriter(f, fieldnames=["endpoint", "calls", "last_status", "messages"])
			writer.writeheader()
			for r in rows:
				writer.writerow(r)

		return True
	except Exception:
		return False


def build_report() -> Dict[str, Any]:
	lines = read_test_artifact()
	summary = generate_summary(lines)
	html = generate_html_report(summary)

	out_dir = Path(__file__).parents[2] / "reports" / "generated"
	out_dir.mkdir(parents=True, exist_ok=True)

	html_path = out_dir / "api_test_report.html"
	json_path = out_dir / "api_test_report.json"
	csv_path = out_dir / "api_test_report.csv"

	html_path.write_text(html, encoding="utf-8")
	export_json(summary, json_path)
	export_csv(summary, csv_path)

	return {
		"summary": summary,
		"html_path": str(html_path),
		"json_path": str(json_path),
		"csv_path": str(csv_path),
	}
