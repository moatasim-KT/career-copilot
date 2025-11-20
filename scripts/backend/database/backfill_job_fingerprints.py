#!/usr/bin/env python3
"""
Backfill Job Fingerprints

This script generates fingerprints for existing jobs that don't have them.
Useful for migrating existing data to use the new deduplication system.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.models.job import Job
from app.services.job_deduplication_service import JobDeduplicationService
from sqlalchemy import func


def backfill_fingerprints(batch_size: int = 1000, dry_run: bool = False):
	"""
	Backfill fingerprints for jobs that don't have them

	Args:
		batch_size: Number of jobs to process per batch
		dry_run: If True, only report what would be done without making changes
	"""
	db = SessionLocal()
	dedup_service = JobDeduplicationService(db)

	try:
		print("\n" + "=" * 70)
		print("   🔄 JOB FINGERPRINT BACKFILL")
		print("=" * 70)
		print()

		if dry_run:
			print("🔍 DRY RUN MODE - No changes will be made")
			print()

		# Count jobs without fingerprints
		total_without_fp = db.query(func.count(Job.id)).filter(Job.job_fingerprint.is_(None)).scalar()

		total_with_fp = db.query(func.count(Job.id)).filter(Job.job_fingerprint.isnot(None)).scalar()

		total_jobs = total_without_fp + total_with_fp

		print(f"📊 Current Status:")
		print(f"  • Total jobs: {total_jobs:,}")
		print(f"  • With fingerprint: {total_with_fp:,} ({total_with_fp / total_jobs * 100:.1f}%)")
		print(f"  • Without fingerprint: {total_without_fp:,} ({total_without_fp / total_jobs * 100:.1f}%)")
		print()

		if total_without_fp == 0:
			print("✓ All jobs already have fingerprints!")
			return

		if dry_run:
			print(f"Would generate fingerprints for {total_without_fp:,} jobs")
			print()

			# Show sample of jobs that would be updated
			sample_jobs = db.query(Job).filter(Job.job_fingerprint.is_(None)).limit(5).all()

			print("Sample jobs that would be updated:")
			for job in sample_jobs:
				fp = dedup_service.create_job_fingerprint(job.title, job.company, job.location)
				print(f"  • {job.title[:40]:40s} @ {job.company[:20]:20s} → {fp}")

			print()
			print("Run without --dry-run to apply changes")
			return

		# Process in batches
		print(f"🔄 Processing {total_without_fp:,} jobs in batches of {batch_size:,}...")
		print()

		processed = 0
		updated = 0
		errors = 0
		offset = 0

		while offset < total_without_fp:
			# Get batch
			batch = db.query(Job).filter(Job.job_fingerprint.is_(None)).limit(batch_size).offset(offset).all()

			if not batch:
				break

			batch_updated = 0

			for job in batch:
				try:
					# Generate fingerprint
					fingerprint = dedup_service.create_job_fingerprint(job.title, job.company, job.location)

					job.job_fingerprint = fingerprint
					batch_updated += 1

				except Exception as e:
					errors += 1
					print(f"⚠️  Error processing job {job.id}: {e}")

			# Commit batch
			try:
				db.commit()
				updated += batch_updated
				processed += len(batch)

				# Progress update
				progress = (processed / total_without_fp) * 100
				print(f"  Progress: {processed:,}/{total_without_fp:,} ({progress:.1f}%) - Updated: {updated:,}, Errors: {errors}")

			except Exception as e:
				db.rollback()
				print(f"❌ Error committing batch: {e}")
				errors += len(batch)

			offset += batch_size

		print()
		print("=" * 70)
		print("   ✅ BACKFILL COMPLETED")
		print("=" * 70)
		print()
		print(f"Results:")
		print(f"  • Processed: {processed:,} jobs")
		print(f"  • Updated: {updated:,} jobs")
		print(f"  • Errors: {errors}")
		print()

		# Verify
		remaining = db.query(func.count(Job.id)).filter(Job.job_fingerprint.is_(None)).scalar()

		if remaining == 0:
			print("✓ All jobs now have fingerprints!")
		else:
			print(f"⚠️  {remaining:,} jobs still without fingerprints")

	except Exception as e:
		print(f"\n❌ Backfill failed: {e}")
		import traceback

		traceback.print_exc()
		db.rollback()
		sys.exit(1)

	finally:
		db.close()


def main():
	"""Main entry point"""
	import argparse

	parser = argparse.ArgumentParser(description="Backfill fingerprints for jobs without them")
	parser.add_argument(
		"--batch-size",
		type=int,
		default=1000,
		help="Number of jobs to process per batch (default: 1000)",
	)
	parser.add_argument(
		"--dry-run",
		action="store_true",
		help="Show what would be done without making changes",
	)

	args = parser.parse_args()

	backfill_fingerprints(batch_size=args.batch_size, dry_run=args.dry_run)


if __name__ == "__main__":
	main()
	main()
