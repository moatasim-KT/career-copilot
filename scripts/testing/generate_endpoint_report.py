#!/usr/bin/env python3
"""
Generate a simple HTML report from reports/endpoint_map.json and (optionally)
reports/endpoint_test_results.json. This provides a comprehensive static
summary including categories, counts, and sample endpoints.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
ENDPOINT_MAP = REPORTS / "endpoint_map.json"
TEST_RESULTS = REPORTS / "endpoint_test_results.json"
OUTPUT = REPORTS / "endpoint_report.html"


def load_json(p: Path):
	if not p.exists():
		return None
	return json.loads(p.read_text(encoding="utf-8"))


def make_html(map_data, test_data):
	total = len(map_data) if map_data else 0

	by_cat = {}
	for e in map_data or []:
		c = e.get("category", "other")
		by_cat.setdefault(c, []).append(e)

	html = [
		"<!DOCTYPE html>",
		"<html>",
		"<head>",
		'<meta charset="utf-8">',
		"<title>Endpoint Discovery Report</title>",
		"<style>body{font-family:Arial,sans-serif;padding:20px} table{border-collapse:collapse;width:100%} th,td{border:1px solid #ddd;padding:8px} th{background:#f4f4f4}</style>",
		"</head>",
		"<body>",
	]

	html.append(f"<h1>Endpoint Discovery Report</h1>")
	html.append(f"<p>Total endpoints discovered: <strong>{total}</strong></p>")

	html.append("<h2>Categories</h2>")
	html.append("<ul>")
	for cat, items in sorted(by_cat.items(), key=lambda x: -len(x[1])):
		html.append(f"<li>{cat} — {len(items)} endpoints</li>")
	html.append("</ul>")

	html.append("<h2>Top 50 Endpoints (sample)</h2>")
	html.append("<table>")
	html.append("<tr><th>Method</th><th>Path</th><th>File</th><th>Category</th><th>Tags</th></tr>")
	for e in (map_data or [])[:50]:
		html.append("<tr>")
		html.append(f"<td>{e.get('method')}</td>")
		html.append(f"<td><code>{e.get('path')}</code></td>")
		html.append(f"<td>{e.get('file')}</td>")
		html.append(f"<td>{e.get('category')}</td>")
		html.append(f"<td>{', '.join(e.get('tags') or [])}</td>")
		html.append("</tr>")
	html.append("</table>")

	if test_data:
		results = test_data.get("results", [])
		total_tests = len(results)
		successes = sum(1 for r in results if r.get("status_code") and 200 <= r["status_code"] < 400)
		auth_failures = sum(1 for r in results if r.get("status_code") in (401, 403))
		server_errors = sum(1 for r in results if r.get("status_code") and r["status_code"] >= 500)

		html.append("<h2>Static Test Run Summary</h2>")
		html.append("<ul>")
		html.append(f"<li>Total endpoint checks: {total_tests}</li>")
		html.append(f"<li>Successful (2xx/3xx): {successes}</li>")
		html.append(f"<li>Auth failures (401/403): {auth_failures}</li>")
		html.append(f"<li>Server errors (5xx): {server_errors}</li>")
		html.append("</ul>")

		html.append("<h3>Slowest 10 endpoints</h3>")
		slow = sorted([r for r in results if r.get("response_time")], key=lambda x: -x.get("response_time", 0))[:10]
		html.append("<table>")
		html.append("<tr><th>Method</th><th>Path</th><th>Status</th><th>Status Code</th><th>Response time (s)</th></tr>")
		for r in slow:
			html.append("<tr>")
			html.append(f"<td>{r.get('method')}</td>")
			html.append(f"<td><code>{r.get('path')}</code></td>")
			html.append(f"<td>{r.get('status')}</td>")
			html.append(f"<td>{r.get('status_code')}</td>")
			html.append(f"<td>{r.get('response_time')}</td>")
			html.append("</tr>")
		html.append("</table>")

	html.append("<h2>Action Items</h2>")
	html.append("<ol>")
	html.append("<li>Run live integration tests against a running stack (docker-compose up) to validate auth and real responses.</li>")
	html.append("<li>Compare frontend-extracted API calls with this endpoint map and implement missing backend routes or adjust frontend calls.</li>")
	html.append("<li>For endpoints returning 5xx, inspect server logs and add unit/integration tests covering failure scenarios.</li>")
	html.append("</ol>")

	html.append("</body></html>")
	return "\n".join(html)


def main():
	map_data = load_json(ENDPOINT_MAP)
	test_data = load_json(TEST_RESULTS)

	html = make_html(map_data, test_data)

	REPORTS.mkdir(parents=True, exist_ok=True)
	with open(OUTPUT, "w", encoding="utf-8") as f:
		f.write(html)

	print(f"Report generated: {OUTPUT}")


if __name__ == "__main__":
	main()
