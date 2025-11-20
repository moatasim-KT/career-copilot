#!/usr/bin/env python3
"""
Async reproducer that runs HTTPX AsyncClient against the ASGI app in the same
asyncio event loop. This avoids TestClient/anyio cross-event-loop issues by
keeping app and requests on a single loop.

Usage:
  PYTHONPATH="." python backend/scripts/triage/reproduce_endpoints_async.py
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
backend_dir = ROOT / "backend"
if str(backend_dir) not in sys.path:
	sys.path.insert(0, str(backend_dir))

import httpx
from httpx import ASGITransport

from app.core.database import init_db
from app.main import create_app

ENDPOINTS = [
	("GET", "/api/v1/users/me"),
	("GET", "/api/v1/job-sources"),
]


async def run():
	print("Calling init_db() to ensure sync engine/schema...")
	try:
		init_db()
	except Exception as e:
		print("init_db() failed:", e)

	app = create_app()

	transport = ASGITransport(app=app)
	async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
		for method, path in ENDPOINTS:
			try:
				if method == "GET":
					r = await client.get(path, headers={"accept": "application/json"})
				elif method == "POST":
					r = await client.post(path, json={}, headers={"accept": "application/json"})
				else:
					print("Skipping unsupported method", method, path)
					continue

				print(f"{method} {path} -> status={r.status_code} body={r.text[:1000]}")
			except Exception as exc:
				print(f"{method} {path} -> EXCEPTION:")
				import traceback

				traceback.print_exc()


if __name__ == "__main__":
	asyncio.run(run())
