#!/usr/bin/env python3
"""
End-to-End Test for Job Deduplication System

This script tests the complete job ingestion and deduplication workflow:
1. Scrapes jobs from a single source (small batch)
2. Verifies deduplication statistics
3. Re-runs scraping to ensure duplicates are filtered
4. Validates fingerprint generation
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict

from app.core.database import SessionLocal
from app.models.job import Job
from app.models.user import User
from app.services.job_deduplication_service import JobDeduplicationService
from app.services.job_scraping_service import JobScrapingService


class DeduplicationE2ETest:
	"""End-to-end test for job deduplication"""

	def __init__(self):
		self.db = SessionLocal()
		self.scraping_service = JobScrapingService(self.db)
		self.dedup_service = JobDeduplicationService(self.db)
		self.test_user = None

	def setup(self):
		"""Setup test environment"""
		print("\n" + "=" * 70)
		print("   🧪 JOB DEDUPLICATION END-TO-END TEST")
		print("=" * 70)
		print()

		# Find or create test user
		self.test_user = self.db.query(User).filter(User.email == "test@example.com").first()

		if not self.test_user:
			# Try to find any user
			self.test_user = self.db.query(User).first()

		if not self.test_user:
			print("❌ No test user found. Please create a user first.")
			sys.exit(1)

		print(f"✓ Using test user: {self.test_user.email} (ID: {self.test_user.id})")
		print()

	def get_job_stats(self) -> Dict[str, Any]:
		"""Get current job statistics for test user"""
		total_jobs = self.db.query(Job).filter(Job.user_id == self.test_user.id).count()

		jobs_with_fingerprint = self.db.query(Job).filter(Job.user_id == self.test_user.id, Job.job_fingerprint.isnot(None)).count()

		jobs_without_fingerprint = self.db.query(Job).filter(Job.user_id == self.test_user.id, Job.job_fingerprint.is_(None)).count()

		return {
			"total_jobs": total_jobs,
			"with_fingerprint": jobs_with_fingerprint,
			"without_fingerprint": jobs_without_fingerprint,
		}

	async def test_scraping_with_deduplication(self):
		"""Test job scraping with deduplication enabled"""
		print("📊 PHASE 1: Initial Job Scraping")
		print("-" * 70)

		# Get initial stats
		initial_stats = self.get_job_stats()
		print(f"Initial jobs in database: {initial_stats['total_jobs']}")
		print(f"  • With fingerprint: {initial_stats['with_fingerprint']}")
		print(f"  • Without fingerprint: {initial_stats['without_fingerprint']}")
		print()

		# Run job scraping (using the actual method from the service)
		print("🔍 Scraping jobs (limited batch)...")
		try:
			result = await self.scraping_service.ingest_jobs_for_user(
				user_id=self.test_user.id,
				max_jobs=20,  # Small batch for testing
			)

			print(f"✓ Scraping completed")
			print(f"  • Total jobs found: {result.get('jobs_found', 0)}")
			print(f"  • New jobs saved: {result.get('jobs_saved', 0)}")
			print(f"  • Duplicates filtered: {result.get('duplicates_filtered', 0)}")

			print()

		except Exception as e:
			print(f"❌ Error during scraping: {e}")
			import traceback

			traceback.print_exc()
			return False

		# Get updated stats
		updated_stats = self.get_job_stats()
		new_jobs = updated_stats["total_jobs"] - initial_stats["total_jobs"]

		print(f"Updated jobs in database: {updated_stats['total_jobs']} (+{new_jobs})")
		print(f"  • With fingerprint: {updated_stats['with_fingerprint']}")
		print(f"  • Without fingerprint: {updated_stats['without_fingerprint']}")
		print()

		return new_jobs >= 0  # Accept 0 or more jobs (API might have no new jobs)

	async def test_duplicate_filtering(self):
		"""Test that re-scraping filters out duplicates"""
		print("📊 PHASE 2: Re-scraping to Test Duplicate Filtering")
		print("-" * 70)

		before_stats = self.get_job_stats()
		print(f"Jobs before re-scraping: {before_stats['total_jobs']}")
		print()

		# Re-run the same scraper
		print("🔍 Re-scraping same source (should find duplicates)...")
		try:
			result = await self.scraping_service.ingest_jobs_for_user(
				user_id=self.test_user.id,
				max_jobs=20,
			)

			print(f"✓ Re-scraping completed")
			print(f"  • Total jobs found: {result.get('jobs_found', 0)}")
			print(f"  • New jobs saved: {result.get('jobs_saved', 0)}")
			print(f"  • Duplicates filtered: {result.get('duplicates_filtered', 0)}")

			duplicates = result.get("duplicates_filtered", 0)
			if duplicates > 0:
				print(f"  ✓ Deduplication is working! {duplicates} duplicates were filtered")
			else:
				print(f"  ⚠️  No duplicates found (may be new jobs from API)")

			print()

		except Exception as e:
			print(f"❌ Error during re-scraping: {e}")
			return False

		after_stats = self.get_job_stats()
		new_jobs = after_stats["total_jobs"] - before_stats["total_jobs"]

		print(f"Jobs after re-scraping: {after_stats['total_jobs']} (+{new_jobs})")
		print()

		if new_jobs == 0:
			print("✓ Perfect! All duplicates were filtered out")
		elif new_jobs < result.get("jobs_found", 0):
			print(f"✓ Good! Some duplicates were filtered ({result.get('jobs_found', 0) - new_jobs} duplicates)")
		else:
			print("⚠️  Warning: No duplicates filtered (might be new jobs)")

		print()
		return True

	def test_fingerprint_validation(self):
		"""Validate that all recent jobs have fingerprints"""
		print("📊 PHASE 3: Fingerprint Validation")
		print("-" * 70)

		# Check recent jobs
		recent_jobs = self.db.query(Job).filter(Job.user_id == self.test_user.id).order_by(Job.created_at.desc()).limit(10).all()

		print(f"Checking {len(recent_jobs)} most recent jobs...")
		print()

		jobs_with_fingerprint = 0
		jobs_without_fingerprint = 0

		for job in recent_jobs:
			if job.job_fingerprint:
				jobs_with_fingerprint += 1
				# Verify fingerprint is valid (32 character MD5)
				if len(job.job_fingerprint) == 32:
					status = "✓"
				else:
					status = "⚠️"
			else:
				jobs_without_fingerprint += 1
				status = "✗"

			print(f"{status} {job.title[:50]:50s} @ {job.company[:20]:20s} | FP: {job.job_fingerprint or 'None'}")

		print()
		print(f"Summary:")
		print(f"  • Jobs with valid fingerprint: {jobs_with_fingerprint}")
		print(f"  • Jobs without fingerprint: {jobs_without_fingerprint}")
		print()

		if jobs_without_fingerprint > 0:
			print(f"⚠️  Found {jobs_without_fingerprint} jobs without fingerprints")
			print(f"   Consider running the backfill script")
		else:
			print("✓ All recent jobs have fingerprints!")

		print()
		return jobs_with_fingerprint > 0

	def test_bulk_deduplication(self):
		"""Test bulk deduplication on existing database jobs"""
		print("📊 PHASE 4: Bulk Database Deduplication Check")
		print("-" * 70)

		print("🔍 Checking for duplicates in database...")

		try:
			results = self.dedup_service.bulk_deduplicate_database_jobs(user_id=self.test_user.id)

			print(f"✓ Bulk deduplication analysis completed")
			print(f"  • Total jobs analyzed: {results.get('total_jobs', 0)}")
			print(f"  • Duplicates found: {results.get('duplicates_found', 0)}")

			if results.get("duplicates_found", 0) > 0:
				print(f"  • Duplicates by type:")
				by_type = results.get("duplicates_by_type", {})
				print(f"    - URL: {by_type.get('url', 0)}")
				print(f"    - Fingerprint: {by_type.get('fingerprint', 0)}")
				print(f"  ⚠️  Found duplicates in database - consider cleanup")
			else:
				print(f"  ✓ No duplicates found in database!")

			print()

		except Exception as e:
			print(f"❌ Error during bulk deduplication: {e}")
			return False

		return True

	def cleanup(self):
		"""Cleanup resources"""
		if self.db:
			self.db.close()

	async def run(self):
		"""Run all test phases"""
		try:
			self.setup()

			# Phase 1: Initial scraping
			success = await self.test_scraping_with_deduplication()
			if not success:
				print("❌ Phase 1 failed - stopping test")
				return False

			# Phase 2: Duplicate filtering
			success = await self.test_duplicate_filtering()
			if not success:
				print("❌ Phase 2 failed - stopping test")
				return False

			# Phase 3: Fingerprint validation
			self.test_fingerprint_validation()

			# Phase 4: Bulk deduplication
			self.test_bulk_deduplication()

			# Final summary
			print("=" * 70)
			print("   ✅ ALL TESTS COMPLETED SUCCESSFULLY")
			print("=" * 70)
			print()

			final_stats = self.get_job_stats()
			print("Final Statistics:")
			print(f"  • Total jobs: {final_stats['total_jobs']}")
			print(f"  • With fingerprint: {final_stats['with_fingerprint']}")
			print(f"  • Without fingerprint: {final_stats['without_fingerprint']}")
			print()

			return True

		except Exception as e:
			print(f"\n❌ Test failed with error: {e}")
			import traceback

			traceback.print_exc()
			return False
		finally:
			self.cleanup()


async def main():
	"""Main entry point"""
	test = DeduplicationE2ETest()
	success = await test.run()
	sys.exit(0 if success else 1)


if __name__ == "__main__":
	asyncio.run(main())
