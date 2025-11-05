#!/usr/bin/env python3
"""
Monitor Deduplication Metrics

This script provides insights into job deduplication performance and statistics.
Useful for tracking deduplication effectiveness over time.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from app.core.database import SessionLocal
from app.models.job import Job
from app.services.job_deduplication_service import JobDeduplicationService
from sqlalchemy import and_, func


class DeduplicationMonitor:
	"""Monitor and report on deduplication metrics"""

	def __init__(self, db_session):
		self.db = db_session
		self.dedup_service = JobDeduplicationService(db_session)

	def get_overall_stats(self):
		"""Get overall deduplication statistics"""
		print("\n" + "=" * 70)
		print("   📊 JOB DEDUPLICATION METRICS")
		print("=" * 70)
		print()

		# Total jobs
		total_jobs = self.db.query(func.count(Job.id)).scalar()

		# Jobs with fingerprints
		with_fingerprint = self.db.query(func.count(Job.id)).filter(Job.job_fingerprint.isnot(None)).scalar()

		# Jobs without fingerprints
		without_fingerprint = total_jobs - with_fingerprint

		# Unique fingerprints
		unique_fingerprints = self.db.query(func.count(func.distinct(Job.job_fingerprint))).filter(Job.job_fingerprint.isnot(None)).scalar()

		# Potential duplicates (same fingerprint)
		potential_duplicates = with_fingerprint - unique_fingerprints

		print("📈 Overall Statistics:")
		print(f"  • Total jobs: {total_jobs:,}")
		print(f"  • With fingerprint: {with_fingerprint:,} ({with_fingerprint / total_jobs * 100:.1f}%)")
		print(f"  • Without fingerprint: {without_fingerprint:,} ({without_fingerprint / total_jobs * 100:.1f}%)")
		print(f"  • Unique fingerprints: {unique_fingerprints:,}")
		print(f"  • Potential duplicates: {potential_duplicates:,}")
		print()

		if potential_duplicates > 0:
			print(f"⚠️  Found {potential_duplicates:,} potential duplicate jobs in database")
			print(f"   Consider running bulk deduplication cleanup")
		else:
			print("✓ No duplicate fingerprints found!")

		print()

	def get_recent_activity(self, days: int = 7):
		"""Get deduplication activity for recent jobs"""
		print(f"📅 Recent Activity (Last {days} Days):")
		print("-" * 70)

		cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

		# Jobs created in period
		recent_jobs = self.db.query(func.count(Job.id)).filter(Job.created_at >= cutoff_date).scalar()

		# Recent jobs with fingerprints
		recent_with_fp = self.db.query(func.count(Job.id)).filter(and_(Job.created_at >= cutoff_date, Job.job_fingerprint.isnot(None))).scalar()

		# Daily breakdown
		daily_stats = defaultdict(lambda: {"total": 0, "with_fp": 0})

		jobs = self.db.query(Job.created_at, Job.job_fingerprint).filter(Job.created_at >= cutoff_date).all()

		for job in jobs:
			date_key = job.created_at.date()
			daily_stats[date_key]["total"] += 1
			if job.job_fingerprint:
				daily_stats[date_key]["with_fp"] += 1

		print(f"  • Jobs created: {recent_jobs:,}")
		print(f"  • With fingerprint: {recent_with_fp:,} ({recent_with_fp / recent_jobs * 100 if recent_jobs > 0 else 0:.1f}%)")
		print()

		if daily_stats:
			print("  Daily Breakdown:")
			for date in sorted(daily_stats.keys(), reverse=True):
				stats = daily_stats[date]
				fp_pct = stats["with_fp"] / stats["total"] * 100 if stats["total"] > 0 else 0
				print(f"    {date}: {stats['total']:3d} jobs ({stats['with_fp']:3d} with FP, {fp_pct:.0f}%)")

		print()

	def get_duplicate_patterns(self):
		"""Analyze patterns in duplicate jobs"""
		print("🔍 Duplicate Patterns Analysis:")
		print("-" * 70)

		# Find fingerprints that appear multiple times
		duplicate_fps = (
			self.db.query(Job.job_fingerprint, func.count(Job.id).label("count"))
			.filter(Job.job_fingerprint.isnot(None))
			.group_by(Job.job_fingerprint)
			.having(func.count(Job.id) > 1)
			.order_by(func.count(Job.id).desc())
			.limit(10)
			.all()
		)

		if not duplicate_fps:
			print("  ✓ No duplicate fingerprints found!")
			print()
			return

		print(f"  Top {len(duplicate_fps)} most duplicated jobs:")
		print()

		for fp, count in duplicate_fps:
			# Get one example of this job
			example = self.db.query(Job).filter(Job.job_fingerprint == fp).first()

			if example:
				print(f"  • {count}x: {example.title[:40]:40s} @ {example.company[:20]:20s}")
				print(f"         Fingerprint: {fp}")

		print()

	def get_url_based_duplicates(self):
		"""Find jobs with duplicate URLs"""
		print("🔗 URL-Based Duplicate Analysis:")
		print("-" * 70)

		# Find URLs that appear multiple times
		duplicate_urls = (
			self.db.query(Job.application_url, func.count(Job.id).label("count"))
			.filter(Job.application_url.isnot(None))
			.group_by(Job.application_url)
			.having(func.count(Job.id) > 1)
			.order_by(func.count(Job.id).desc())
			.limit(5)
			.all()
		)

		if not duplicate_urls:
			print("  ✓ No duplicate URLs found!")
			print()
			return

		print(f"  Found {len(duplicate_urls)} URLs with multiple jobs:")
		print()

		for url, count in duplicate_urls:
			print(f"  • {count}x: {url[:60]:60s}")

			# Show the jobs
			jobs = self.db.query(Job).filter(Job.application_url == url).limit(3).all()

			for job in jobs:
				print(f"         - {job.title[:50]} @ {job.company} (ID: {job.id})")

		print()

	def get_fingerprint_coverage_by_user(self):
		"""Get fingerprint coverage statistics per user"""
		print("👥 Fingerprint Coverage by User:")
		print("-" * 70)

		# Get stats per user
		from sqlalchemy import case

		user_stats = (
			self.db.query(
				Job.user_id, func.count(Job.id).label("total"), func.sum(case((Job.job_fingerprint.isnot(None), 1), else_=0)).label("with_fp")
			)
			.group_by(Job.user_id)
			.order_by(func.count(Job.id).desc())
			.limit(10)
			.all()
		)

		if not user_stats:
			print("  No jobs found")
			print()
			return

		print(f"  Top {len(user_stats)} users by job count:")
		print()

		for user_id, total, with_fp in user_stats:
			with_fp = int(with_fp) if with_fp else 0
			coverage = with_fp / total * 100 if total > 0 else 0
			bar_length = int(coverage / 2)  # Scale to 50 chars max
			bar = "█" * bar_length + "░" * (50 - bar_length)

			print(f"  User {user_id:3d}: {total:5,d} jobs | {bar} {coverage:5.1f}%")

		print()

	def run_full_report(self, days: int = 7):
		"""Run complete monitoring report"""
		try:
			self.get_overall_stats()
			self.get_recent_activity(days)
			self.get_duplicate_patterns()
			self.get_url_based_duplicates()
			self.get_fingerprint_coverage_by_user()

			print("=" * 70)
			print("   ✅ MONITORING REPORT COMPLETE")
			print("=" * 70)
			print()

			# Recommendations
			print("💡 Recommendations:")

			# Check if backfill is needed
			total_jobs = self.db.query(func.count(Job.id)).scalar()
			without_fp = self.db.query(func.count(Job.id)).filter(Job.job_fingerprint.is_(None)).scalar()

			if without_fp > 0:
				print(f"  • Run backfill script: {without_fp:,} jobs missing fingerprints")
				print(f"    Command: python scripts/backfill_job_fingerprints.py")

			# Check for duplicates
			duplicate_fps = self.db.query(func.count(func.distinct(Job.job_fingerprint))).filter(Job.job_fingerprint.isnot(None)).scalar()

			with_fp = self.db.query(func.count(Job.id)).filter(Job.job_fingerprint.isnot(None)).scalar()

			if with_fp - duplicate_fps > 0:
				print(f"  • Run cleanup: {with_fp - duplicate_fps:,} potential duplicates found")
				print(f"    (Review before deletion)")

			if without_fp == 0 and (with_fp - duplicate_fps) == 0:
				print("  ✓ System is healthy - no action needed!")

			print()

		except Exception as e:
			print(f"❌ Error generating report: {e}")
			import traceback

			traceback.print_exc()


def main():
	"""Main entry point"""
	import argparse

	parser = argparse.ArgumentParser(description="Monitor job deduplication metrics")
	parser.add_argument(
		"--days",
		type=int,
		default=7,
		help="Number of days to include in recent activity (default: 7)",
	)

	args = parser.parse_args()

	db = SessionLocal()

	try:
		monitor = DeduplicationMonitor(db)
		monitor.run_full_report(days=args.days)
	finally:
		db.close()


if __name__ == "__main__":
	main()
	main()
