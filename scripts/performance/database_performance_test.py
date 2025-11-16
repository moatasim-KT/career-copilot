#!/usr/bin/env python3
"""
Direct Database Performance Testing
Focuses on database query performance, index analysis, and optimization recommendations
"""

import json
import logging
import os
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


def get_db_connection():
	"""Get database connection with proper environment setup"""
	try:
		# Load environment variables
		from dotenv import load_dotenv

		backend_dir = Path(__file__).parent.parent.parent / "backend"
		env_file = backend_dir / ".env"

		if env_file.exists():
			load_dotenv(env_file)
			logger.info(f"✅ Loaded environment from {env_file}")
		else:
			logger.warning(f"⚠️  No .env file found at {env_file}")

		# Add backend to path
		sys.path.insert(0, str(backend_dir))

		# Import after path is set
		from sqlalchemy import create_engine, inspect, text
		from sqlalchemy.orm import sessionmaker

		# Get database URL from environment
		database_url = os.getenv("DATABASE_URL")
		if not database_url:
			logger.error("❌ DATABASE_URL not found in environment")
			return None, None

		logger.info(f"📊 Connecting to database...")
		engine = create_engine(database_url, pool_pre_ping=True, echo=False)

		# Test connection
		with engine.connect() as conn:
			conn.execute(text("SELECT 1"))

		Session = sessionmaker(bind=engine)
		logger.info("✅ Database connection established")
		return engine, Session

	except Exception as e:
		logger.error(f"❌ Database connection failed: {e}")
		return None, None


def analyze_table_indexes(engine) -> Dict[str, Any]:
	"""Analyze database indexes and their usage"""
	from sqlalchemy import inspect, text

	results = {"tables_analyzed": 0, "total_indexes": 0, "indexes_by_table": {}, "missing_indexes_recommendations": [], "unused_indexes": []}

	try:
		inspector = inspect(engine)
		tables = inspector.get_table_names()

		logger.info(f"📊 Analyzing indexes for {len(tables)} tables...")

		for table in tables:
			indexes = inspector.get_indexes(table)
			results["tables_analyzed"] += 1
			results["total_indexes"] += len(indexes)
			results["indexes_by_table"][table] = {
				"count": len(indexes),
				"indexes": [{"name": idx["name"], "columns": idx["column_names"], "unique": idx.get("unique", False)} for idx in indexes],
			}

		# Check for common missing indexes
		critical_tables = ["jobs", "applications", "users"]
		for table in critical_tables:
			if table in tables:
				indexes = inspector.get_indexes(table)
				index_columns = set()
				for idx in indexes:
					index_columns.update(idx["column_names"])

				# Recommend indexes for common query patterns
				if table == "jobs":
					recommended = ["title", "company", "location", "created_at", "user_id"]
					for col in recommended:
						if col not in index_columns:
							results["missing_indexes_recommendations"].append(
								{"table": table, "column": col, "reason": f"Frequently queried column for filtering/sorting"}
							)

				elif table == "applications":
					recommended = ["job_id", "status", "created_at", "user_id"]
					for col in recommended:
						if col not in index_columns:
							results["missing_indexes_recommendations"].append(
								{"table": table, "column": col, "reason": f"Common in WHERE clauses and JOINs"}
							)

		logger.info(f"✅ Analyzed {results['tables_analyzed']} tables with {results['total_indexes']} indexes")
		if results["missing_indexes_recommendations"]:
			logger.warning(f"⚠️  Found {len(results['missing_indexes_recommendations'])} missing index recommendations")

		return results

	except Exception as e:
		logger.error(f"❌ Index analysis failed: {e}")
		return results


def test_query_performance(engine, Session) -> Dict[str, Any]:
	"""Test performance of common queries"""
	from sqlalchemy import text

	results = {"queries_tested": 0, "total_duration": 0, "queries": []}

	test_queries = [
		{"name": "Count Jobs", "query": "SELECT COUNT(*) FROM jobs", "expected_ms": 100},
		{"name": "Count Applications", "query": "SELECT COUNT(*) FROM applications", "expected_ms": 100},
		{"name": "Count Users", "query": "SELECT COUNT(*) FROM users", "expected_ms": 50},
		{"name": "Recent Jobs", "query": "SELECT * FROM jobs ORDER BY created_at DESC LIMIT 10", "expected_ms": 200},
		{
			"name": "Jobs with Applications Join",
			"query": """
                SELECT j.id, j.title, COUNT(a.id) as app_count 
                FROM jobs j 
                LEFT JOIN applications a ON j.id = a.job_id 
                GROUP BY j.id, j.title 
                LIMIT 10
            """,
			"expected_ms": 500,
		},
	]

	logger.info(f"📊 Testing {len(test_queries)} common queries...")

	with engine.connect() as conn:
		for test in test_queries:
			try:
				start = time.time()
				result = conn.execute(text(test["query"]))
				rows = result.fetchall()
				duration_ms = (time.time() - start) * 1000

				query_result = {
					"name": test["name"],
					"duration_ms": round(duration_ms, 2),
					"expected_ms": test["expected_ms"],
					"status": "✅ PASS" if duration_ms <= test["expected_ms"] else "⚠️  SLOW",
					"row_count": len(rows),
				}

				results["queries"].append(query_result)
				results["queries_tested"] += 1
				results["total_duration"] += duration_ms

				status_icon = "✅" if duration_ms <= test["expected_ms"] else "⚠️"
				logger.info(f"  {status_icon} {test['name']}: {duration_ms:.2f}ms (expected <{test['expected_ms']}ms)")

			except Exception as e:
				logger.warning(f"  ❌ {test['name']}: {e}")
				results["queries"].append({"name": test["name"], "error": str(e), "status": "❌ ERROR"})

	avg_duration = results["total_duration"] / results["queries_tested"] if results["queries_tested"] > 0 else 0
	results["avg_duration_ms"] = round(avg_duration, 2)

	logger.info(f"✅ Completed {results['queries_tested']} queries in {results['total_duration']:.2f}ms (avg: {avg_duration:.2f}ms)")

	return results


def test_concurrent_reads(engine) -> Dict[str, Any]:
	"""Test database performance under concurrent read load"""
	import concurrent.futures

	from sqlalchemy import text

	results = {
		"concurrent_users": 10,
		"requests_per_user": 5,
		"total_requests": 0,
		"successful_requests": 0,
		"failed_requests": 0,
		"durations": [],
		"avg_duration_ms": 0,
		"median_duration_ms": 0,
		"p95_duration_ms": 0,
		"p99_duration_ms": 0,
	}

	def execute_query(user_id: int):
		"""Execute a test query"""
		durations = []
		for i in range(results["requests_per_user"]):
			try:
				start = time.time()
				with engine.connect() as conn:
					conn.execute(text("SELECT * FROM jobs LIMIT 10"))
				duration_ms = (time.time() - start) * 1000
				durations.append(duration_ms)
				results["successful_requests"] += 1
			except Exception as e:
				logger.warning(f"Query failed for user {user_id}: {e}")
				results["failed_requests"] += 1
		return durations

	logger.info(f"📊 Testing concurrent load: {results['concurrent_users']} users x {results['requests_per_user']} requests...")

	start_time = time.time()

	with concurrent.futures.ThreadPoolExecutor(max_workers=results["concurrent_users"]) as executor:
		futures = [executor.submit(execute_query, i) for i in range(results["concurrent_users"])]
		for future in concurrent.futures.as_completed(futures):
			durations = future.result()
			results["durations"].extend(durations)

	total_time = time.time() - start_time
	results["total_requests"] = results["successful_requests"] + results["failed_requests"]

	if results["durations"]:
		sorted_durations = sorted(results["durations"])
		results["avg_duration_ms"] = round(statistics.mean(sorted_durations), 2)
		results["median_duration_ms"] = round(statistics.median(sorted_durations), 2)
		results["p95_duration_ms"] = round(sorted_durations[int(len(sorted_durations) * 0.95)], 2)
		results["p99_duration_ms"] = round(sorted_durations[int(len(sorted_durations) * 0.99)], 2)
		results["throughput_rps"] = round(results["total_requests"] / total_time, 2)

	logger.info(f"✅ Completed {results['total_requests']} requests in {total_time:.2f}s")
	logger.info(f"   Throughput: {results['throughput_rps']:.2f} requests/sec")
	logger.info(f"   Avg: {results['avg_duration_ms']}ms | P95: {results['p95_duration_ms']}ms | P99: {results['p99_duration_ms']}ms")

	return results


def generate_recommendations(index_analysis: Dict, query_performance: Dict, concurrent_test: Dict) -> List[Dict[str, Any]]:
	"""Generate optimization recommendations based on test results"""
	recommendations = []

	# Check for missing indexes
	if index_analysis.get("missing_indexes_recommendations"):
		for rec in index_analysis["missing_indexes_recommendations"]:
			recommendations.append(
				{
					"priority": "HIGH",
					"category": "Database Indexing",
					"issue": f"Missing index on {rec['table']}.{rec['column']}",
					"recommendation": f"CREATE INDEX idx_{rec['table']}_{rec['column']} ON {rec['table']}({rec['column']})",
					"impact": "Improved query performance for filtering and sorting",
					"reason": rec["reason"],
				}
			)

	# Check for slow queries
	slow_queries = [q for q in query_performance.get("queries", []) if q.get("duration_ms", 0) > q.get("expected_ms", 999999)]
	if slow_queries:
		for query in slow_queries:
			recommendations.append(
				{
					"priority": "MEDIUM",
					"category": "Query Optimization",
					"issue": f"Slow query: {query['name']} ({query['duration_ms']}ms > {query['expected_ms']}ms expected)",
					"recommendation": "Review query execution plan and add appropriate indexes",
					"impact": "Faster response times for common operations",
					"command": "EXPLAIN ANALYZE <query>",
				}
			)

	# Check concurrent performance
	if concurrent_test.get("p95_duration_ms", 0) > 500:
		recommendations.append(
			{
				"priority": "HIGH",
				"category": "Database Performance",
				"issue": f"High P95 latency under concurrent load: {concurrent_test['p95_duration_ms']}ms",
				"recommendation": "Consider increasing database connection pool size or optimizing queries",
				"impact": "Better performance under load",
				"current_p95": concurrent_test["p95_duration_ms"],
				"target_p95": 500,
			}
		)

	if concurrent_test.get("failed_requests", 0) > 0:
		recommendations.append(
			{
				"priority": "CRITICAL",
				"category": "Database Reliability",
				"issue": f"{concurrent_test['failed_requests']} failed requests under concurrent load",
				"recommendation": "Investigate connection pool exhaustion or timeout issues",
				"impact": "Improved reliability under load",
			}
		)

	# Add general best practices
	recommendations.append(
		{
			"priority": "LOW",
			"category": "Monitoring",
			"issue": "Performance monitoring",
			"recommendation": "Set up continuous performance monitoring with tools like pg_stat_statements",
			"impact": "Proactive identification of performance regressions",
		}
	)

	return recommendations


def main():
	"""Main execution function"""
	logger.info("=" * 70)
	logger.info("DATABASE PERFORMANCE TESTING SUITE")
	logger.info("=" * 70)

	# Get database connection
	engine, Session = get_db_connection()

	if not engine:
		logger.error("❌ Cannot proceed without database connection")
		sys.exit(1)

	results = {"timestamp": datetime.now().isoformat(), "test_suite": "Database Performance", "status": "completed"}

	# Run tests
	logger.info("\n" + "=" * 70)
	logger.info("1. ANALYZING DATABASE INDEXES")
	logger.info("=" * 70)
	results["index_analysis"] = analyze_table_indexes(engine)

	logger.info("\n" + "=" * 70)
	logger.info("2. TESTING QUERY PERFORMANCE")
	logger.info("=" * 70)
	results["query_performance"] = test_query_performance(engine, Session)

	logger.info("\n" + "=" * 70)
	logger.info("3. TESTING CONCURRENT READ LOAD")
	logger.info("=" * 70)
	results["concurrent_test"] = test_concurrent_reads(engine)

	logger.info("\n" + "=" * 70)
	logger.info("4. GENERATING RECOMMENDATIONS")
	logger.info("=" * 70)
	recommendations = generate_recommendations(results["index_analysis"], results["query_performance"], results["concurrent_test"])
	results["recommendations"] = recommendations
	results["recommendation_count"] = len(recommendations)

	# Print recommendations
	for i, rec in enumerate(recommendations, 1):
		priority_icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(rec["priority"], "⚪")
		logger.info(f"\n{i}. {priority_icon} [{rec['priority']}] {rec['category']}")
		logger.info(f"   Issue: {rec['issue']}")
		logger.info(f"   Recommendation: {rec['recommendation']}")
		logger.info(f"   Impact: {rec['impact']}")

	# Save results
	output_file = Path(__file__).parent.parent.parent / f"database_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
	with open(output_file, "w") as f:
		json.dump(results, f, indent=2)

	logger.info("\n" + "=" * 70)
	logger.info("SUMMARY")
	logger.info("=" * 70)
	logger.info(f"✅ Tables analyzed: {results['index_analysis']['tables_analyzed']}")
	logger.info(f"✅ Queries tested: {results['query_performance']['queries_tested']}")
	logger.info(f"✅ Concurrent requests: {results['concurrent_test']['total_requests']}")
	logger.info(f"⚠️  Recommendations: {results['recommendation_count']}")
	logger.info(f"📄 Report saved: {output_file}")
	logger.info("=" * 70)

	# Calculate performance score
	score = 100
	if results["index_analysis"]["missing_indexes_recommendations"]:
		score -= len(results["index_analysis"]["missing_indexes_recommendations"]) * 5
	slow_query_count = len([q for q in results["query_performance"]["queries"] if q.get("duration_ms", 0) > q.get("expected_ms", 999999)])
	if slow_query_count:
		score -= slow_query_count * 10
	if results["concurrent_test"]["p95_duration_ms"] > 500:
		score -= 15
	if results["concurrent_test"]["failed_requests"] > 0:
		score -= 20

	score = max(0, score)
	logger.info(f"\n🎯 PERFORMANCE SCORE: {score}/100")

	if score >= 90:
		logger.info("✅ Excellent database performance!")
	elif score >= 70:
		logger.info("⚠️  Good performance with room for improvement")
	elif score >= 50:
		logger.info("⚠️  Moderate performance - optimization recommended")
	else:
		logger.info("❌ Poor performance - immediate optimization required")

	return score


if __name__ == "__main__":
	try:
		score = main()
		sys.exit(0 if score >= 70 else 1)
	except KeyboardInterrupt:
		logger.info("\n⚠️  Test interrupted by user")
		sys.exit(130)
	except Exception as e:
		logger.error(f"\n❌ Test failed with error: {e}", exc_info=True)
		sys.exit(1)
