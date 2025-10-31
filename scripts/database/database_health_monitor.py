#!/usr/bin/env python3
"""
Database Health Monitoring Script.

This script provides comprehensive database health monitoring including
connection status, performance metrics, backup status, and migration status.
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import get_database_manager
from app.core.database_backup import get_backup_manager
from app.core.database_migrations import get_migration_manager
from app.core.database_performance import get_db_performance_optimizer
from app.core.logging import get_logger

logger = get_logger(__name__)


class DatabaseHealthMonitor:
	"""Comprehensive database health monitoring."""

	def __init__(self) -> None:
		self.health_checks = {
			"connectivity": self._check_connectivity,
			"performance": self._check_performance,
			"backups": self._check_backups,
			"migrations": self._check_migrations,
			"disk_space": self._check_disk_space,
			"connection_pools": self._check_connection_pools,
			"slow_queries": self._check_slow_queries,
		}

	async def run_health_check(self, checks: Optional[List[str]] = None) -> Dict[str, Any]:
		"""
		Run comprehensive health check.

		Args:
		    checks: List of specific checks to run (all if None)

		Returns:
		    Health check results
		"""
		if checks is None:
			checks = list(self.health_checks.keys())

		results = {
			"timestamp": datetime.now().isoformat(),
			"overall_status": "healthy",
			"checks": {},
			"summary": {"total_checks": len(checks), "passed_checks": 0, "failed_checks": 0, "warning_checks": 0},
		}

		for check_name in checks:
			if check_name not in self.health_checks:
				logger.warning(f"Unknown health check: {check_name}")
				continue

			try:
				logger.info(f"Running health check: {check_name}")
				check_result = await self.health_checks[check_name]()
				results["checks"][check_name] = check_result

				# Update summary
				if check_result["status"] == "healthy":
					results["summary"]["passed_checks"] += 1
				elif check_result["status"] == "warning":
					results["summary"]["warning_checks"] += 1
				else:
					results["summary"]["failed_checks"] += 1
					results["overall_status"] = "unhealthy"

			except Exception as e:
				logger.error(f"Health check {check_name} failed: {e}")
				results["checks"][check_name] = {"status": "error", "message": f"Check failed: {e!s}", "timestamp": datetime.now().isoformat()}
				results["summary"]["failed_checks"] += 1
				results["overall_status"] = "unhealthy"

		# Set overall status based on failed checks
		if results["summary"]["failed_checks"] > 0:
			results["overall_status"] = "unhealthy"
		elif results["summary"]["warning_checks"] > 0:
			results["overall_status"] = "warning"

		return results

	async def _check_connectivity(self) -> Dict[str, Any]:
		"""Check database connectivity."""
		try:
			db_manager = await get_database_manager()
			health_status = await db_manager.health_check()

			if all(health_status.values()):
				return {
					"status": "healthy",
					"message": "All database connections are healthy",
					"details": health_status,
					"timestamp": datetime.now().isoformat(),
				}
			else:
				failed_connections = [k for k, v in health_status.items() if not v]
				return {
					"status": "unhealthy",
					"message": f"Failed connections: {', '.join(failed_connections)}",
					"details": health_status,
					"timestamp": datetime.now().isoformat(),
				}

		except Exception as e:
			return {"status": "error", "message": f"Connectivity check failed: {e!s}", "timestamp": datetime.now().isoformat()}

	async def _check_performance(self) -> Dict[str, Any]:
		"""Check database performance metrics."""
		try:
			db_optimizer = await get_db_performance_optimizer()
			metrics = await db_optimizer.get_performance_metrics(hours=1)

			# Define performance thresholds
			thresholds = {
				"avg_execution_time": 1.0,  # seconds
				"slow_queries": 10,  # count
				"success_rate": 95.0,  # percentage
			}

			issues = []
			warnings = []

			if "query_performance" in metrics:
				perf = metrics["query_performance"]

				if perf.get("avg_execution_time", 0) > thresholds["avg_execution_time"]:
					issues.append(f"High average query time: {perf['avg_execution_time']:.2f}s")

				if perf.get("slow_queries", 0) > thresholds["slow_queries"]:
					warnings.append(f"High slow query count: {perf['slow_queries']}")

				if perf.get("success_rate", 100) < thresholds["success_rate"]:
					issues.append(f"Low success rate: {perf['success_rate']:.1f}%")

			if issues:
				status = "unhealthy"
				message = f"Performance issues detected: {'; '.join(issues)}"
			elif warnings:
				status = "warning"
				message = f"Performance warnings: {'; '.join(warnings)}"
			else:
				status = "healthy"
				message = "Database performance is good"

			return {"status": status, "message": message, "details": metrics, "thresholds": thresholds, "timestamp": datetime.now().isoformat()}

		except Exception as e:
			return {"status": "error", "message": f"Performance check failed: {e!s}", "timestamp": datetime.now().isoformat()}

	async def _check_backups(self) -> Dict[str, Any]:
		"""Check backup system status."""
		try:
			backup_manager = await get_backup_manager()
			backup_health = await backup_manager.health_check()

			# Check recent backups
			recent_backups = backup_manager.list_backups()
			recent_cutoff = datetime.now() - timedelta(days=7)
			recent_successful = [b for b in recent_backups if b.created_at >= recent_cutoff and b.status.value == "completed"]

			issues = []
			warnings = []

			if backup_health["status"] != "healthy":
				issues.append("Backup system is unhealthy")

			if backup_health["failed_backups"] > 0:
				warnings.append(f"{backup_health['failed_backups']} failed backups")

			if len(recent_successful) == 0:
				issues.append("No successful backups in the last 7 days")
			elif len(recent_successful) < 3:
				warnings.append(f"Only {len(recent_successful)} successful backups in last 7 days")

			if not backup_health["backup_directory_writable"]:
				issues.append("Backup directory is not writable")

			if issues:
				status = "unhealthy"
				message = f"Backup issues: {'; '.join(issues)}"
			elif warnings:
				status = "warning"
				message = f"Backup warnings: {'; '.join(warnings)}"
			else:
				status = "healthy"
				message = "Backup system is healthy"

			return {
				"status": status,
				"message": message,
				"details": {
					"backup_health": backup_health,
					"recent_successful_backups": len(recent_successful),
					"total_backups": len(recent_backups),
				},
				"timestamp": datetime.now().isoformat(),
			}

		except Exception as e:
			return {"status": "error", "message": f"Backup check failed: {e!s}", "timestamp": datetime.now().isoformat()}

	async def _check_migrations(self) -> Dict[str, Any]:
		"""Check migration system status."""
		try:
			migration_manager = await get_migration_manager()
			migration_status = await migration_manager.get_migration_status()
			validation_results = await migration_manager.validate_migrations()

			issues = []
			warnings = []

			if not validation_results["valid"]:
				issues.extend(validation_results["errors"])

			if validation_results["warnings"]:
				warnings.extend(validation_results["warnings"])

			if migration_status["has_missing_migrations"]:
				issues.append("Missing migration files detected")

			if len(migration_status["pending_migrations"]) > 0:
				warnings.append(f"{len(migration_status['pending_migrations'])} pending migrations")

			if issues:
				status = "unhealthy"
				message = f"Migration issues: {'; '.join(issues)}"
			elif warnings:
				status = "warning"
				message = f"Migration warnings: {'; '.join(warnings)}"
			else:
				status = "healthy"
				message = "Migration system is healthy"

			return {
				"status": status,
				"message": message,
				"details": {"migration_status": migration_status, "validation_results": validation_results},
				"timestamp": datetime.now().isoformat(),
			}

		except Exception as e:
			return {"status": "error", "message": f"Migration check failed: {e!s}", "timestamp": datetime.now().isoformat()}

	async def _check_disk_space(self) -> Dict[str, Any]:
		"""Check disk space usage."""
		try:
			import shutil

			# Check disk space for key directories
			directories = [("Database", "."), ("Backups", "backups"), ("Logs", "logs")]

			disk_info = {}
			warnings = []
			issues = []

			for name, path in directories:
				try:
					if Path(path).exists():
						total, used, free = shutil.disk_usage(path)
						usage_percent = (used / total) * 100

						disk_info[name.lower()] = {
							"total_gb": round(total / (1024**3), 2),
							"used_gb": round(used / (1024**3), 2),
							"free_gb": round(free / (1024**3), 2),
							"usage_percent": round(usage_percent, 1),
						}

						if usage_percent > 90:
							issues.append(f"{name} disk usage critical: {usage_percent:.1f}%")
						elif usage_percent > 80:
							warnings.append(f"{name} disk usage high: {usage_percent:.1f}%")

				except Exception as e:
					warnings.append(f"Could not check {name} disk space: {e!s}")

			if issues:
				status = "unhealthy"
				message = f"Disk space critical: {'; '.join(issues)}"
			elif warnings:
				status = "warning"
				message = f"Disk space warnings: {'; '.join(warnings)}"
			else:
				status = "healthy"
				message = "Disk space usage is normal"

			return {"status": status, "message": message, "details": disk_info, "timestamp": datetime.now().isoformat()}

		except Exception as e:
			return {"status": "error", "message": f"Disk space check failed: {e!s}", "timestamp": datetime.now().isoformat()}

	async def _check_connection_pools(self) -> Dict[str, Any]:
		"""Check database connection pool status."""
		try:
			db_optimizer = await get_db_performance_optimizer()
			health_status = await db_optimizer.health_check()

			pool_issues = []
			pool_warnings = []

			# Check connection pool metrics if available
			if "connection_pools" in health_status:
				pools = health_status["connection_pools"]

				for pool_name, pool_info in pools.items():
					if isinstance(pool_info, dict):
						utilization = pool_info.get("utilization_percent", 0)

						if utilization > 90:
							pool_issues.append(f"{pool_name} pool utilization critical: {utilization:.1f}%")
						elif utilization > 75:
							pool_warnings.append(f"{pool_name} pool utilization high: {utilization:.1f}%")

			if pool_issues:
				status = "unhealthy"
				message = f"Connection pool issues: {'; '.join(pool_issues)}"
			elif pool_warnings:
				status = "warning"
				message = f"Connection pool warnings: {'; '.join(pool_warnings)}"
			else:
				status = "healthy"
				message = "Connection pools are healthy"

			return {
				"status": status,
				"message": message,
				"details": health_status.get("connection_pools", {}),
				"timestamp": datetime.now().isoformat(),
			}

		except Exception as e:
			return {"status": "error", "message": f"Connection pool check failed: {e!s}", "timestamp": datetime.now().isoformat()}

	async def _check_slow_queries(self) -> Dict[str, Any]:
		"""Check for slow queries and performance issues."""
		try:
			db_optimizer = await get_db_performance_optimizer()
			slow_queries = await db_optimizer.analyze_slow_queries(hours=24, min_occurrences=1)

			critical_queries = []
			warning_queries = []

			for query_analysis in slow_queries:
				if query_analysis.avg_execution_time > 5.0:  # 5 seconds
					critical_queries.append(
						{
							"pattern": query_analysis.query_pattern[:100] + "...",
							"avg_time": query_analysis.avg_execution_time,
							"count": query_analysis.execution_count,
						}
					)
				elif query_analysis.avg_execution_time > 2.0:  # 2 seconds
					warning_queries.append(
						{
							"pattern": query_analysis.query_pattern[:100] + "...",
							"avg_time": query_analysis.avg_execution_time,
							"count": query_analysis.execution_count,
						}
					)

			if critical_queries:
				status = "unhealthy"
				message = f"{len(critical_queries)} critical slow queries detected"
			elif warning_queries:
				status = "warning"
				message = f"{len(warning_queries)} slow queries detected"
			else:
				status = "healthy"
				message = "No significant slow queries detected"

			return {
				"status": status,
				"message": message,
				"details": {"critical_queries": critical_queries, "warning_queries": warning_queries, "total_analyzed": len(slow_queries)},
				"timestamp": datetime.now().isoformat(),
			}

		except Exception as e:
			return {"status": "error", "message": f"Slow query check failed: {e!s}", "timestamp": datetime.now().isoformat()}

	def generate_report(self, results: Dict[str, Any], format: str = "text") -> str:
		"""Generate health check report in specified format."""
		if format == "json":
			return json.dumps(results, indent=2)

		# Text format
		report_lines = [
			"DATABASE HEALTH CHECK REPORT",
			"=" * 50,
			f"Timestamp: {results['timestamp']}",
			f"Overall Status: {results['overall_status'].upper()}",
			"",
			"SUMMARY:",
			f"  Total Checks: {results['summary']['total_checks']}",
			f"  Passed: {results['summary']['passed_checks']}",
			f"  Warnings: {results['summary']['warning_checks']}",
			f"  Failed: {results['summary']['failed_checks']}",
			"",
			"DETAILED RESULTS:",
			"-" * 30,
		]

		for check_name, check_result in results["checks"].items():
			status_icon = {"healthy": "✓", "warning": "⚠", "unhealthy": "✗", "error": "✗"}.get(check_result["status"], "?")

			report_lines.extend(
				[f"{status_icon} {check_name.upper()}: {check_result['status'].upper()}", f"  Message: {check_result['message']}", ""]
			)

		return "\n".join(report_lines)


def _resolve_output_path(raw_path: str) -> Path:
	"""Resolve and validate the output path to prevent path traversal."""
	base_dir = Path.cwd().resolve()
	candidate = Path(raw_path).expanduser()
	if not candidate.is_absolute():
		candidate = (base_dir / candidate).resolve()
	else:
		candidate = candidate.resolve()

	try:
		candidate.relative_to(base_dir)
	except ValueError as exc:
		raise ValueError("Output path must be within the current working directory") from exc

	candidate.parent.mkdir(parents=True, exist_ok=True)
	return candidate


async def main() -> int:
	"""Main function for command-line usage."""
	parser = argparse.ArgumentParser(description="Database Health Monitor")
	parser.add_argument(
		"--checks",
		nargs="*",
		choices=["connectivity", "performance", "backups", "migrations", "disk_space", "connection_pools", "slow_queries"],
		help="Specific checks to run (default: all)",
	)
	parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
	parser.add_argument("--output", help="Output file path (default: stdout)")
	parser.add_argument("--continuous", action="store_true", help="Run continuously with specified interval")
	parser.add_argument("--interval", type=int, default=300, help="Interval in seconds for continuous monitoring (default: 300)")

	args = parser.parse_args()

	monitor: DatabaseHealthMonitor = DatabaseHealthMonitor()

	output_path: Optional[Path] = None
	if args.output:
		try:
			output_path = _resolve_output_path(args.output)
		except ValueError as exc:
			print(f"Invalid output path: {exc}", file=sys.stderr)
			return 1

	if args.continuous:
		print(f"Starting continuous monitoring (interval: {args.interval}s)")
		print("Press Ctrl+C to stop...")

		try:
			while True:
				results = await monitor.run_health_check(args.checks)
				report = monitor.generate_report(results, args.format)

				if output_path:
					with output_path.open("w", encoding="utf-8") as file_handle:
						file_handle.write(report)
					print(f"Report written to {output_path}")
				else:
					print(report)
					print("\n" + "=" * 50 + "\n")

				await asyncio.sleep(args.interval)

		except KeyboardInterrupt:
			print("\nMonitoring stopped")
			return 0
	else:
		# Single run
		results = await monitor.run_health_check(args.checks)
		report = monitor.generate_report(results, args.format)

		if output_path:
			with output_path.open("w", encoding="utf-8") as file_handle:
				file_handle.write(report)
			print(f"Report written to {output_path}")
		else:
			print(report)

		# Return appropriate exit code
		return 0 if results["overall_status"] in ["healthy", "warning"] else 1


if __name__ == "__main__":
	sys.exit(asyncio.run(main()))
