"""
Startup validation checks for the Career Copilot application.

This module provides comprehensive startup checks to ensure all required
components are properly configured and initialized before the application starts.
"""

import os
from pathlib import Path
from typing import Dict, Any, Tuple

from .logging import get_logger
from .environment_config import get_environment_config_manager, setup_environment

logger = get_logger(__name__)


class StartupValidator:
	"""Validates application startup requirements."""

	def __init__(self):
		self.env_manager = get_environment_config_manager()
		self.validation_results = {}

	async def run_all_checks(self) -> Tuple[bool, Dict[str, Any]]:
		"""Run all startup validation checks."""
		logger.info("🔍 Running startup validation checks...")

		checks = [
			("Configuration", self.check_configuration),
			("Database", self.check_database),
			("Vector Store", self.check_vector_store),
			("AI Services", self.check_ai_services),
			("File System", self.check_file_system),
			("External Services", self.check_external_services),
		]

		all_passed = True
		results = {}

		for check_name, check_func in checks:
			try:
				logger.info(f"  🔍 Checking {check_name}...")
				passed, details = await check_func()
				results[check_name] = {"passed": passed, "details": details}

				if passed:
					logger.info(f"    ✅ {check_name} check passed")
				else:
					logger.error(f"    ❌ {check_name} check failed")
					all_passed = False

			except Exception as e:
				logger.error(f"    💥 {check_name} check crashed: {e}")
				results[check_name] = {"passed": False, "details": {"error": str(e)}}
				all_passed = False

		return all_passed, results

	async def check_configuration(self) -> Tuple[bool, Dict[str, Any]]:
		"""Check configuration validity with environment-specific validation."""
		details = {}

		try:
			# Get environment configuration
			env_config = self.env_manager.get_config_value()
			current_env = self.env_manager.get_environment()

			details["environment"] = current_env.value
			details["config"] = {
				"debug": env_config.debug,
				"monitoring_enabled": env_config.enable_monitoring,
				"security_enabled": env_config.enable_security,
				"auth_enabled": env_config.enable_auth,
			}

			# Environment-specific validation
			if self.env_manager.is_development():
				return await self._check_development_config(details)
			elif self.env_manager.is_production():
				return await self._check_production_config(details)
			else:
				return await self._check_basic_config(details)

		except Exception as e:
			return False, {"error": str(e)}

	async def _check_development_config(self, details: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
		"""Check development-specific configuration."""
		# Basic requirements for development
		required_env_vars = ["OPENAI_API_KEY"]
		missing_env_vars = []

		for var in required_env_vars:
			if not os.getenv(var):
				missing_env_vars.append(var)

		details["missing_env_vars"] = missing_env_vars
		details["validation_mode"] = "development"

		# Check environment consistency
		consistency_issues = self.env_manager.validate_environment_consistency()
		details["consistency_issues"] = consistency_issues

		passed = len(missing_env_vars) == 0
		return passed, details

	async def _check_production_config(self, details: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
		"""Check production-specific configuration."""
		# Production requirements
		required_env_vars = [
			"OPENAI_API_KEY",
			"JWT_SECRET_KEY",
		]

		missing_env_vars = []
		for var in required_env_vars:
			value = os.getenv(var)
			if not value or value == "your-secret-key-change-in-production":
				missing_env_vars.append(var)

		details["missing_env_vars"] = missing_env_vars
		details["validation_mode"] = "production"

		# Check production-specific settings
		production_warnings = []
		if os.getenv("DEBUG", "false").lower() == "true":
			production_warnings.append("DEBUG should be false in production")
		if os.getenv("API_DEBUG", "false").lower() == "true":
			production_warnings.append("API_DEBUG should be false in production")
		if os.getenv("DEVELOPMENT_MODE", "false").lower() == "true":
			production_warnings.append("DEVELOPMENT_MODE should be false in production")

		details["production_warnings"] = production_warnings

		# Check environment consistency
		consistency_issues = self.env_manager.validate_environment_consistency()
		details["consistency_issues"] = consistency_issues

		passed = len(missing_env_vars) == 0
		return passed, details

	async def _check_basic_config(self, details: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
		"""Check basic configuration for any environment."""
		required_env_vars = ["OPENAI_API_KEY"]
		missing_env_vars = []

		for var in required_env_vars:
			if not os.getenv(var):
				missing_env_vars.append(var)

		details["missing_env_vars"] = missing_env_vars
		details["validation_mode"] = "basic"

		passed = len(missing_env_vars) == 0
		return passed, details

	async def check_database(self) -> Tuple[bool, Dict[str, Any]]:
		"""Check database connectivity and schema."""
		details = {}

		try:
			from .database import get_database_manager
			from .migrations import get_database_migrator

			# Get database manager
			db_manager = await get_database_manager()

			# Check basic connectivity
			health_status = await db_manager.health_check()
			details["health_status"] = health_status

			# Check migration status
			migrator = await get_database_migrator()
			migration_health = await migrator.get_database_health()
			details["migration_status"] = migration_health

			# Check connection pool health
			pool_health = await db_manager.monitor_connection_health()
			details["connection_pool_health"] = pool_health

			# Check if tables exist
			async with db_manager.get_session() as session:
				from sqlalchemy import text

				# Test basic query
				await session.execute(text("SELECT 1"))
				details["basic_query"] = True

				# Check main tables
				tables = ["users", "contract_analyses", "audit_logs"]
				table_status = {}

				for table in tables:
					try:
						result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
						count = result.scalar()
						table_status[table] = {"exists": True, "count": count}
					except Exception as e:
						table_status[table] = {"exists": False, "error": str(e)}

				details["tables"] = table_status

			# Check if all required tables exist
			all_tables_exist = all(status["exists"] for status in table_status.values())

			# Check if migrations are up to date
			migrations_up_to_date = migration_health.get("migrations", {}).get("up_to_date", False)

			passed = (
				health_status.get("database", False)
				and details.get("basic_query", False)
				and all_tables_exist
				and migrations_up_to_date
				and pool_health.get("healthy", False)
			)

			return passed, details

		except Exception as e:
			return False, {"error": str(e)}

	async def check_vector_store(self) -> Tuple[bool, Dict[str, Any]]:
		"""Check vector store (ChromaDB) connectivity."""
		details = {}

		try:
			# Check if ChromaDB directory exists and is accessible
			chroma_dir = Path("data/chroma")
			details["chroma_dir_exists"] = chroma_dir.exists()

			if not chroma_dir.exists():
				chroma_dir.mkdir(parents=True, exist_ok=True)
				details["chroma_dir_created"] = True

			details["chroma_dir_writable"] = os.access(chroma_dir, os.W_OK)

			# Try to initialize ChromaDB
			try:
				import chromadb
				from chromadb.config import Settings

				# Create a simple test client
				client = chromadb.PersistentClient(path=str(chroma_dir), settings=Settings(anonymized_telemetry=False))

				# Test basic operations
				collections = client.list_collections()
				details["collections_count"] = len(collections)
				details["chroma_connected"] = True

				# Try to get or create a test collection
				try:
					collection = client.get_or_create_collection("test_collection")
					details["test_collection_accessible"] = True
					passed = True
				except Exception as e:
					details["collection_error"] = str(e)
					# Still pass if directory is writable
					passed = details["chroma_dir_writable"]

			except ImportError:
				details["chromadb_import_error"] = "ChromaDB not installed"
				passed = False
			except Exception as e:
				details["chroma_init_error"] = str(e)
				# Pass if directory is at least writable
				passed = details["chroma_dir_writable"]

			return passed, details

		except Exception as e:
			return False, {"error": str(e)}

	async def check_ai_services(self) -> Tuple[bool, Dict[str, Any]]:
		"""Check AI service configurations."""
		details = {}

		try:
			# Check OpenAI configuration
			openai_key = os.getenv("OPENAI_API_KEY")
			details["openai_configured"] = bool(openai_key)

			# Check other AI services
			groq_key = os.getenv("GROQ_API_KEY")
			details["groq_configured"] = bool(groq_key)

			ollama_enabled = os.getenv("OLLAMA_ENABLED", "false").lower() == "true"
			details["ollama_enabled"] = ollama_enabled

			# Test OpenAI connection if configured
			if openai_key:
				try:
					# Simple test to validate the key format
					if openai_key.startswith("sk-"):
						details["openai_key_format_valid"] = True
					else:
						details["openai_key_format_valid"] = False
						details["openai_warning"] = "API key doesn't start with 'sk-'"
				except Exception as e:
					details["openai_test_error"] = str(e)

			# At least OpenAI should be configured
			passed = details["openai_configured"]

			return passed, details

		except Exception as e:
			return False, {"error": str(e)}

	async def check_file_system(self) -> Tuple[bool, Dict[str, Any]]:
		"""Check file system permissions and directories."""
		details = {}

		try:
			# Check data directory
			data_dir = Path("./data")
			details["data_dir_exists"] = data_dir.exists()

			if not data_dir.exists():
				data_dir.mkdir(parents=True, exist_ok=True)
				details["data_dir_created"] = True

			details["data_dir_writable"] = os.access(data_dir, os.W_OK)

			# Check chroma directory
			chroma_dir = data_dir / "chroma"
			details["chroma_dir_exists"] = chroma_dir.exists()

			if not chroma_dir.exists():
				chroma_dir.mkdir(parents=True, exist_ok=True)
				details["chroma_dir_created"] = True

			# Check logs directory
			logs_dir = Path("./logs")
			details["logs_dir_exists"] = logs_dir.exists()

			if not logs_dir.exists():
				logs_dir.mkdir(parents=True, exist_ok=True)
				details["logs_dir_created"] = True

			details["logs_dir_writable"] = os.access(logs_dir, os.W_OK)

			passed = details["data_dir_writable"] and details["logs_dir_writable"]

			return passed, details

		except Exception as e:
			return False, {"error": str(e)}

	async def check_external_services(self) -> Tuple[bool, Dict[str, Any]]:
		"""Check external service configurations."""
		details = {}

		try:
			# Check email services
			smtp_enabled = os.getenv("SMTP_ENABLED", "false").lower() == "true"
			gmail_enabled = os.getenv("GMAIL_ENABLED", "false").lower() == "true"
			details["email_configured"] = smtp_enabled or gmail_enabled

			# Check Slack
			slack_enabled = os.getenv("SLACK_ENABLED", "false").lower() == "true"
			details["slack_configured"] = slack_enabled

			# Check DocuSign
			docusign_enabled = os.getenv("DOCUSIGN_ENABLED", "false").lower() == "true"
			docusign_sandbox_enabled = os.getenv("DOCUSIGN_SANDBOX_ENABLED", "false").lower() == "true"
			details["docusign_configured"] = docusign_enabled or docusign_sandbox_enabled

			# Check Google Drive
			google_drive_enabled = os.getenv("GOOGLE_DRIVE_ENABLED", "false").lower() == "true"
			details["google_drive_configured"] = google_drive_enabled

			# External services are optional, so always pass
			passed = True

			return passed, details

		except Exception as e:
			return False, {"error": str(e)}

	def print_validation_report(self, results: Dict[str, Any]) -> None:
		"""Print a detailed validation report."""
		logger.info("=" * 60)
		logger.info("🔍 STARTUP VALIDATION REPORT")
		logger.info("=" * 60)

		for check_name, result in results.items():
			status = "✅ PASS" if result["passed"] else "❌ FAIL"
			logger.info(f"{status} {check_name}")

			if not result["passed"]:
				details = result["details"]
				if "error" in details:
					logger.info(f"    Error: {details['error']}")
				else:
					for key, value in details.items():
						if isinstance(value, list) and value:
							logger.info(f"    {key}: {', '.join(map(str, value))}")
						elif isinstance(value, dict):
							for sub_key, sub_value in value.items():
								logger.info(f"    {key}.{sub_key}: {sub_value}")

		logger.info("=" * 60)


async def run_startup_checks() -> bool:
	"""Run all startup checks and return success status."""
	validator = StartupValidator()
	all_passed, results = await validator.run_all_checks()

	validator.print_validation_report(results)

	if all_passed:
		logger.info("🎉 All startup checks passed! Application is ready to start.")
	else:
		logger.error("❌ Some startup checks failed. Please fix the issues before starting the application.")

	return all_passed


async def ensure_database_initialized() -> bool:
	"""Ensure database is properly initialized with comprehensive checks."""
	try:
		from .database import get_database_manager

		logger.info("🔍 Performing comprehensive database initialization check...")

		# Check if database manager can be initialized
		db_manager = await get_database_manager()

		# Check database connectivity
		health_status = await db_manager.health_check()
		if not health_status.get("database", False):
			logger.error("❌ Database connectivity check failed")
			return False

		logger.info("✅ Database connectivity verified")

		# Check if tables exist
		async with db_manager.get_session() as session:
			from sqlalchemy import text

			# Check critical tables
			critical_tables = ["users", "contract_analyses", "audit_logs"]
			existing_tables = []
			missing_tables = []

			for table in critical_tables:
				try:
					result = await session.execute(text(f"SELECT COUNT(*) FROM {table} LIMIT 1"))
					count = result.scalar()
					existing_tables.append(table)
					logger.info(f"✅ Table '{table}' exists with {count} records")
				except Exception as e:
					missing_tables.append(table)
					logger.warning(f"⚠️  Table '{table}' missing or inaccessible: {e}")

			if missing_tables:
				logger.warning(f"⚠️  Missing tables: {', '.join(missing_tables)}")
				return False

			logger.info("✅ All critical database tables exist and are accessible")
			return True

	except Exception as e:
		logger.error(f"❌ Database initialization check failed: {e}")
		return False


async def auto_initialize_database() -> bool:
	"""Automatically initialize database if needed."""
	try:
		logger.info("🔧 Auto-initializing database...")

		# Import and run database initialization
		from ..scripts.initialize_database import initialize_database_complete

		success = await initialize_database_complete()

		if success:
			logger.info("✅ Database auto-initialization completed")
		else:
			logger.error("❌ Database auto-initialization failed")

		return success

	except Exception as e:
		logger.error(f"❌ Database auto-initialization error: {e}")
		return False


async def startup_check_and_init() -> bool:
	"""Enhanced startup check and auto-initialization with dependency validation."""
	try:
		logger.info("🚀 Starting comprehensive application startup validation...")

		# Phase 0: Environment setup
		logger.info("📋 Phase 0: Environment setup and validation")
		setup_environment()

		# Phase 1: Pre-initialization checks
		logger.info("📋 Phase 1: Pre-initialization validation")

		# Check environment and configuration
		validator = StartupValidator()
		config_ok, config_details = await validator.check_configuration()
		if not config_ok:
			logger.error("❌ Configuration validation failed")
			logger.error(f"   Missing keys: {config_details.get('missing_required_keys', [])}")
			logger.error(f"   Missing env vars: {config_details.get('missing_env_vars', [])}")
			return False

		logger.info("✅ Configuration validation passed")

		# Check file system permissions
		fs_ok, fs_details = await validator.check_file_system()
		if not fs_ok:
			logger.error("❌ File system validation failed")
			return False

		logger.info("✅ File system validation passed")

		# Phase 2: Database initialization and validation
		logger.info("📋 Phase 2: Database initialization and validation")

		db_initialized = await ensure_database_initialized()

		if not db_initialized:
			logger.info("🔧 Database not properly initialized, attempting auto-initialization...")

			# Try to auto-initialize
			init_success = await auto_initialize_database()

			if not init_success:
				logger.error("❌ Failed to auto-initialize database")
				logger.info("💡 Manual intervention required:")
				logger.info("   1. Run: python backend/backend/app/scripts/initialize_database.py")
				logger.info("   2. Check database permissions and connectivity")
				logger.info("   3. Verify environment variables are set correctly")
				return False

			# Re-verify database after initialization
			db_initialized = await ensure_database_initialized()
			if not db_initialized:
				logger.error("❌ Database initialization verification failed")
				return False

		logger.info("✅ Database initialization and validation completed")

		# Phase 3: Service dependency validation
		logger.info("📋 Phase 3: Service dependency validation")

		# Check AI services
		ai_ok, ai_details = await validator.check_ai_services()
		if not ai_ok:
			logger.warning("⚠️  AI services validation failed - some features may be limited")
			logger.warning(f"   Details: {ai_details}")
		else:
			logger.info("✅ AI services validation passed")

		# Check vector store
		vector_ok, vector_details = await validator.check_vector_store()
		if not vector_ok:
			logger.warning("⚠️  Vector store validation failed - search features may be limited")
			logger.warning(f"   Details: {vector_details}")
		else:
			logger.info("✅ Vector store validation passed")

		# Phase 4: External integrations (optional)
		logger.info("📋 Phase 4: External integrations validation")

		ext_ok, ext_details = await validator.check_external_services()
		if not ext_ok:
			logger.info("ℹ️  Some external services not configured - optional features will be disabled")
		else:
			logger.info("✅ External services validation passed")

		# Phase 5: Final comprehensive validation
		logger.info("📋 Phase 5: Final comprehensive validation")

		final_validation = await run_startup_checks()

		if final_validation:
			logger.info("🎉 All startup validation phases completed successfully!")
			logger.info("✅ Application is ready to serve requests")
			return True
		else:
			logger.error("❌ Final validation failed - application may not function correctly")
			return False

	except Exception as e:
		logger.error(f"❌ Startup check and initialization failed: {e}")
		import traceback

		logger.error(f"   Traceback: {traceback.format_exc()}")
		return False
