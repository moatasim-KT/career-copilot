#!/usr/bin/env python3
"""
Setup PostgreSQL test database for Career Copilot tests
Uses psycopg2 to connect and create the test database
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
	import psycopg2
	from psycopg2 import sql
	from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
	print("❌ Error: psycopg2 not installed")
	print("Install with: pip install psycopg2-binary")
	sys.exit(1)


def setup_test_database():
	"""Create and configure the test database."""

	# Database configuration
	DB_NAME = "career_copilot_test"
	# Try common PostgreSQL users
	DB_USER = "moatasimfarooque"  # Current system user (common for local PostgreSQL)
	DB_PASSWORD = ""  # Local PostgreSQL often uses peer authentication
	DB_HOST = "localhost"
	DB_PORT = "5432"

	print("🔧 Setting up PostgreSQL test database...")

	# Connect to default postgres database (or user's default database)
	conn = None
	for dbname in ["postgres", DB_USER, "template1"]:
		try:
			print(f"🔌 Attempting connection to database '{dbname}' as user '{DB_USER}'...")
			conn = psycopg2.connect(dbname=dbname, user=DB_USER, password=DB_PASSWORD if DB_PASSWORD else None, host=DB_HOST, port=DB_PORT)
			conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
			cur = conn.cursor()

			print("✅ Connected to PostgreSQL server")
			break
		except psycopg2.OperationalError:
			continue

	if conn is None:
		print("❌ Could not connect to PostgreSQL with any default database")
		print(f"   Tried databases: postgres, {DB_USER}, template1")
		print(f"   User: {DB_USER}")
		print()
		print("Please ensure PostgreSQL is running and accessible")
		return 1

	try:
		# Check if test database exists
		cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
		exists = cur.fetchone()

		if exists:
			print(f"🗑️  Dropping existing test database: {DB_NAME}")
			# Terminate existing connections
			cur.execute(
				sql.SQL("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = %s
                AND pid <> pg_backend_pid()
            """),
				[DB_NAME],
			)

			# Drop database
			cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(DB_NAME)))

		# Create test database
		print(f"📦 Creating test database: {DB_NAME}")
		cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))

		# Grant privileges
		print("🔐 Granting privileges...")
		cur.execute(sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(sql.Identifier(DB_NAME), sql.Identifier(DB_USER)))

		cur.close()
		conn.close()

		print("✅ Test database setup complete!")
		print()
		print("You can now run tests with:")
		print("  pytest tests/ -v")
		print("  pytest tests/ --cov=app --cov-report=html")
		print()
		print("Database connection string:")
		conn_str = f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
		print(f"  {conn_str}")
		print()
		print("Add to your .env file:")
		print(f"  TEST_DATABASE_URL={conn_str}")

		return 0

	except Exception as e:
		print(f"❌ Error: {e}")
		if conn:
			conn.close()
		return 1


if __name__ == "__main__":
	sys.exit(setup_test_database())
