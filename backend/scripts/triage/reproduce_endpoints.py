#!/usr/bin/env python3
"""
Reproduce specific failing endpoints to capture full stack traces.

Usage: run from repository root with PYTHONPATH set so imports resolve, e.g.

PYTHONPATH="." python backend/scripts/triage/reproduce_endpoints.py

This script targets a small set of endpoints known to fail in the last test run
and prints full exception tracebacks to help root-cause debugging.
"""

import sys
import time
import traceback
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[3]

DEFAULT_ENDPOINTS = [
	("GET", "/api/v1/users/me"),  # mapper duplication error (InterviewQuestion)
	("GET", "/api/v1/job-sources"),  # async loop / Future attached to different loop
]


def load_app():
	# Ensure the backend package directory is on sys.path and import the
	# application package by its canonical name ("app") so SQLAlchemy model
	# classes are registered under a single module path. This avoids the
	# "Multiple classes found for path ..." mapper duplication caused when
	# modules are imported under both 'backend.app' and 'app'.
	backend_dir = Path(__file__).resolve().parents[3] / "backend"
	if str(backend_dir) not in sys.path:
		sys.path.insert(0, str(backend_dir))

	# import here to avoid side effects during static analysis
	from app.main import create_app

	return create_app()


def call_endpoint(client: TestClient, method: str, path: str):
	method = method.upper()
	start = time.time()
	try:
		if method == "GET":
			r = client.get(path, headers={"accept": "application/json"})
		elif method == "POST":
			r = client.post(path, json={}, headers={"accept": "application/json"})
		else:
			print(f"Skipping unsupported method: {method} {path}")
			return

		elapsed = time.time() - start
		print(f"{method} {path} -> status={r.status_code} time={elapsed:.4f}s")
		print("Response body:")
		print(r.text[:2000])
	except Exception:
		elapsed = time.time() - start
		print(f"{method} {path} -> EXCEPTION after {elapsed:.4f}s")
		traceback.print_exc()


def main(endpoints=None):
	if endpoints is None:
		endpoints = DEFAULT_ENDPOINTS

	app = load_app()
	# Ensure the synchronous DB engine and schema exist before spinning up
	# TestClient. This avoids creating loop-bound async engines during
	# TestClient/anyio lifespan setup which can cause cross-event-loop
	# errors with asyncpg. init_db() will initialize the sync engine and
	# create tables (async engine is left to be created lazily on the
	# active request loop).
	try:
		from app.core.database import get_db_manager, init_db

		print("Calling init_db() to initialize sync engine and schema...")
		init_db()

		# Do NOT eagerly initialize the async engine here. Creating a
		# long-lived async engine before TestClient starts can bind the
		# engine's resources (asyncpg connection pool) to a different
		# event loop than the one TestClient uses, producing
		# "Future attached to a different loop" errors. The async engine
		# should be created lazily on the active request loop or via an
		# application lifespan handler when running the real server.
	except Exception as e:
		print("init_db() failed:", e)

	client = TestClient(app)

	print("Starting repro run for endpoints:")
	for m, p in endpoints:
		print(f"- {m} {p}")

	print("\nRunning...\n")
	for method, path in endpoints:
		call_endpoint(client, method, path)


if __name__ == "__main__":
	main()
