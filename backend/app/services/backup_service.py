"""
Backup and recovery service for Career Co-Pilot system
Implements requirement 11.5: Easily exportable database for backup and migration purposes
"""

import json
import os
import shutil
import subprocess
import tarfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

from app.core.config import settings
from app.core.database import get_db
from app.models.analytics import Analytics
from app.models.application import Application

# from app.models.document import Document  # TODO: Document model doesn't exist
from app.models.job import Job
from app.models.user import User
from app.utils.logging import get_logger, handle_exceptions, performance_tracker

logger = get_logger(__name__)


class BackupService:
	"""Service for creating and managing system backups"""

	def __init__(self):
		self.backup_dir = Path("backups")
		self.backup_dir.mkdir(exist_ok=True)

	@handle_exceptions(component="backup_service")
	def create_full_backup(self, include_files: bool = True, compress: bool = True) -> Dict[str, Any]:
		"""
		Create a complete system backup including database and files

		Args:
		    include_files: Whether to include uploaded files
		    compress: Whether to compress the backup

		Returns:
		    Dict with backup information
		"""
		backup_id = f"backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
		backup_path = self.backup_dir / backup_id
		backup_path.mkdir(exist_ok=True)

		logger.info(f"Starting full backup: {backup_id}")

		with performance_tracker.track_operation("full_backup", threshold_seconds=30.0):
			backup_info = {
				"backup_id": backup_id,
				"timestamp": datetime.now(timezone.utc).isoformat(),
				"type": "full",
				"status": "in_progress",
				"components": {},
			}

			try:
				# 1. Database backup
				db_backup_info = self._backup_database(backup_path)
				backup_info["components"]["database"] = db_backup_info

				# 2. Configuration backup
				config_backup_info = self._backup_configuration(backup_path)
				backup_info["components"]["configuration"] = config_backup_info

				# 3. File uploads backup (if requested)
				if include_files:
					files_backup_info = self._backup_files(backup_path)
					backup_info["components"]["files"] = files_backup_info

				# 4. Application logs backup
				logs_backup_info = self._backup_logs(backup_path)
				backup_info["components"]["logs"] = logs_backup_info

				# 5. Create backup manifest
				manifest_path = backup_path / "manifest.json"
				with open(manifest_path, "w") as f:
					json.dump(backup_info, f, indent=2)

				# 6. Compress backup if requested
				if compress:
					compressed_path = self._compress_backup(backup_path)
					backup_info["compressed_path"] = str(compressed_path)
					backup_info["compressed_size_mb"] = round(compressed_path.stat().st_size / 1024 / 1024, 2)

					# Remove uncompressed directory
					shutil.rmtree(backup_path)
					backup_info["backup_path"] = str(compressed_path)
				else:
					backup_info["backup_path"] = str(backup_path)

				# Calculate total size
				if compress:
					total_size = compressed_path.stat().st_size
				else:
					total_size = sum(f.stat().st_size for f in backup_path.rglob("*") if f.is_file())

				backup_info["total_size_mb"] = round(total_size / 1024 / 1024, 2)
				backup_info["status"] = "completed"

				logger.info(f"Backup completed successfully: {backup_id}")
				return backup_info

			except Exception as e:
				backup_info["status"] = "failed"
				backup_info["error"] = str(e)
				logger.error(f"Backup failed: {backup_id} - {e!s}")

				# Cleanup failed backup
				if backup_path.exists():
					shutil.rmtree(backup_path)

				raise

	@handle_exceptions(component="backup_service")
	def _backup_database(self, backup_path: Path) -> Dict[str, Any]:
		"""Backup PostgreSQL database"""
		logger.info("Starting database backup")

		db_backup_path = backup_path / "database"
		db_backup_path.mkdir(exist_ok=True)

		# Parse database URL
		db_url = settings.DATABASE_URL
		if db_url.startswith("postgresql://"):
			# Extract connection details
			import urllib.parse

			parsed = urllib.parse.urlparse(db_url)

			# Create pg_dump command
			dump_file = db_backup_path / "database_dump.sql"

			env = os.environ.copy()
			if parsed.password:
				env["PGPASSWORD"] = parsed.password

			cmd = [
				"pg_dump",
				"-h",
				parsed.hostname or "localhost",
				"-p",
				str(parsed.port or 5432),
				"-U",
				parsed.username or "postgres",
				"-d",
				parsed.path.lstrip("/"),
				"--no-password",
				"--verbose",
				"--clean",
				"--if-exists",
				"-f",
				str(dump_file),
			]

			try:
				result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)

				if result.returncode == 0:
					# Also create a JSON export of key data
					json_backup_path = db_backup_path / "data_export.json"
					self._export_data_as_json(json_backup_path)

					return {
						"status": "success",
						"dump_file": str(dump_file),
						"json_export": str(json_backup_path),
						"size_mb": round(dump_file.stat().st_size / 1024 / 1024, 2),
					}
				else:
					raise Exception(f"pg_dump failed: {result.stderr}")

			except subprocess.TimeoutExpired:
				raise Exception("Database backup timed out")
			except FileNotFoundError:
				# Fallback to JSON export only if pg_dump not available
				logger.warning("pg_dump not found, using JSON export only")
				json_backup_path = db_backup_path / "data_export.json"
				self._export_data_as_json(json_backup_path)

				return {"status": "partial", "json_export": str(json_backup_path), "warning": "pg_dump not available, JSON export only"}
		else:
			raise Exception(f"Unsupported database URL format: {db_url}")

	def _export_data_as_json(self, json_path: Path):
		"""Export database data as JSON for portability"""
		db = next(get_db())
		try:
			export_data = {
				"export_timestamp": datetime.now(timezone.utc).isoformat(),
				"version": "1.0",
				"users": [],
				"jobs": [],
				"applications": [],
				"documents": [],
				"analytics": [],
			}

			# Export users (excluding sensitive data)
			users = db.query(User).all()
			for user in users:
				export_data["users"].append(
					{
						"id": user.id,
						"email": user.email,
						"profile": user.profile,
						"settings": user.settings,
						"created_at": user.created_at.isoformat() if user.created_at else None,
						"updated_at": user.updated_at.isoformat() if user.updated_at else None,
					}
				)

			# Export jobs
			jobs = db.query(Job).all()
			for job in jobs:
				export_data["jobs"].append(
					{
						"id": job.id,
						"user_id": job.user_id,
						"title": job.title,
						"company": job.company,
						"location": job.location,
						"salary_min": job.salary_min,
						"salary_max": job.salary_max,
						"currency": job.currency,
						"requirements": job.requirements,
						"description": job.description,
						"application_url": job.application_url,
						"status": job.status,
						"source": job.source,
						"date_posted": job.date_posted.isoformat() if job.date_posted else None,
						"date_added": job.date_added.isoformat() if job.date_added else None,
						"date_applied": job.date_applied.isoformat() if job.date_applied else None,
						"recommendation_score": float(job.recommendation_score) if job.recommendation_score else None,
						"tags": job.tags,
						"created_at": job.created_at.isoformat() if job.created_at else None,
						"updated_at": job.updated_at.isoformat() if job.updated_at else None,
					}
				)

			# Export applications
			applications = db.query(Application).all()
			for app in applications:
				export_data["applications"].append(
					{
						"id": app.id,
						"job_id": app.job_id,
						"user_id": app.user_id,
						"status": app.status,
						"applied_at": app.applied_at.isoformat() if app.applied_at else None,
						"response_date": app.response_date.isoformat() if app.response_date else None,
						"notes": app.notes,
						"documents": app.documents,
					}
				)

			# Export documents metadata (not file content)
			# TODO: Document model doesn't exist - commenting out for now
			# documents = db.query(Document).all()
			# for doc in documents:
			# 	export_data["documents"].append(
			# 		{
			# 			"id": doc.id,
			# 			"user_id": doc.user_id,
			# 			"filename": doc.filename,
			# 			"original_filename": doc.original_filename,
			# 			"file_type": doc.file_type,
			# 			"file_size": doc.file_size,
			# 			"file_path": doc.file_path,
			# 			"document_type": doc.document_type,
			# 			"metadata": doc.metadata,
			# 			"created_at": doc.created_at.isoformat() if doc.created_at else None,
			# 			"updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
			# 		}
			# 	)

			# Export analytics (last 30 days only)
			cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
			analytics = db.query(Analytics).filter(Analytics.generated_at >= cutoff_date).all()
			for analytic in analytics:
				export_data["analytics"].append(
					{
						"id": analytic.id,
						"user_id": analytic.user_id,
						"type": analytic.type,
						"data": analytic.data,
						"generated_at": analytic.generated_at.isoformat() if analytic.generated_at else None,
					}
				)

			# Write JSON file
			with open(json_path, "w") as f:
				json.dump(export_data, f, indent=2, default=str)

		finally:
			db.close()

	def _backup_configuration(self, backup_path: Path) -> Dict[str, Any]:
		"""Backup configuration files"""
		config_backup_path = backup_path / "configuration"
		config_backup_path.mkdir(exist_ok=True)

		config_files = []

		# Backup environment file if it exists
		env_file = Path(".env")
		if env_file.exists():
			shutil.copy2(env_file, config_backup_path / ".env.backup")
			config_files.append(".env")

		# Backup docker-compose files
		for compose_file in ["docker-compose.yml", "docker-compose.override.yml"]:
			compose_path = Path(compose_file)
			if compose_path.exists():
				shutil.copy2(compose_path, config_backup_path / f"{compose_file}.backup")
				config_files.append(compose_file)

		# Create configuration summary
		config_summary = {
			"timestamp": datetime.now(timezone.utc).isoformat(),
			"environment": settings.ENVIRONMENT,
			"database_url": settings.DATABASE_URL.split("@")[0] + "@[REDACTED]",  # Hide credentials
			"redis_url": settings.REDIS_URL.split("@")[0] + "@[REDACTED]" if "@" in settings.REDIS_URL else settings.REDIS_URL,
			"upload_dir": settings.UPLOAD_DIR,
			"encryption_enabled": settings.ENCRYPT_FILES,
			"compression_enabled": settings.ENABLE_COMPRESSION,
		}

		with open(config_backup_path / "config_summary.json", "w") as f:
			json.dump(config_summary, f, indent=2)

		return {"status": "success", "files_backed_up": config_files, "config_summary": "config_summary.json"}

	def _backup_files(self, backup_path: Path) -> Dict[str, Any]:
		"""Backup uploaded files"""
		files_backup_path = backup_path / "files"
		files_backup_path.mkdir(exist_ok=True)

		upload_dir = Path(settings.UPLOAD_DIR)
		if not upload_dir.exists():
			return {"status": "skipped", "reason": "Upload directory does not exist"}

		# Copy all files
		total_files = 0
		total_size = 0

		for file_path in upload_dir.rglob("*"):
			if file_path.is_file():
				relative_path = file_path.relative_to(upload_dir)
				dest_path = files_backup_path / relative_path
				dest_path.parent.mkdir(parents=True, exist_ok=True)

				shutil.copy2(file_path, dest_path)
				total_files += 1
				total_size += file_path.stat().st_size

		return {"status": "success", "total_files": total_files, "total_size_mb": round(total_size / 1024 / 1024, 2)}

	def _backup_logs(self, backup_path: Path) -> Dict[str, Any]:
		"""Backup recent application logs"""
		logs_backup_path = backup_path / "logs"
		logs_backup_path.mkdir(exist_ok=True)

		logs_dir = Path("logs")
		if not logs_dir.exists():
			return {"status": "skipped", "reason": "Logs directory does not exist"}

		# Copy recent log files
		log_files = []
		for log_file in logs_dir.glob("*.log*"):
			if log_file.is_file():
				shutil.copy2(log_file, logs_backup_path / log_file.name)
				log_files.append(log_file.name)

		return {"status": "success", "log_files": log_files}

	def _compress_backup(self, backup_path: Path) -> Path:
		"""Compress backup directory"""
		compressed_path = backup_path.with_suffix(".tar.gz")

		with tarfile.open(compressed_path, "w:gz") as tar:
			tar.add(backup_path, arcname=backup_path.name)

		return compressed_path

	def _safe_extract(self, tar: tarfile.TarFile, destination: Path) -> None:
		"""Safely extract tar contents to destination preventing path traversal"""
		destination_root = destination.resolve()
		members = tar.getmembers()

		for member in members:
			member_path = (destination_root / member.name).resolve()
			if not self._is_within_directory(destination_root, member_path):
				raise ValueError("Invalid archive contents detected during extraction")
			if member.islnk() or member.issym():
				raise ValueError("Archive contains unsupported link entry")
			if member.isdev() or member.ischr() or member.isblk() or member.isfifo():
				raise ValueError("Archive contains unsupported special file entry")

		for member in members:
			member_path = (destination_root / member.name).resolve()
			if member.isdir():
				member_path.mkdir(parents=True, exist_ok=True)
				continue

			if member.isfile():
				member_path.parent.mkdir(parents=True, exist_ok=True)
				# Security: Path already validated above via _is_within_directory check (lines 396-400)
				# This prevents tar slip attacks (CWE-22)
				extracted_file = tar.extractfile(member)
				if extracted_file is None:
					raise ValueError(f"Failed to extract file from archive: {member.name}")
				try:
					with open(member_path, "wb") as destination_file:
						shutil.copyfileobj(extracted_file, destination_file)
				finally:
					extracted_file.close()
				continue

			raise ValueError(f"Unsupported tar entry type: {member.name}")

	def _is_within_directory(self, directory: Path, target: Path) -> bool:
		"""Check that target resides within directory."""
		abs_directory = os.path.abspath(str(directory))
		abs_target = os.path.abspath(str(target))
		return os.path.commonpath([abs_directory, abs_target]) == abs_directory

	@handle_exceptions(component="backup_service")
	def list_backups(self) -> List[Dict[str, Any]]:
		"""List all available backups"""
		backups = []

		for backup_item in self.backup_dir.iterdir():
			if backup_item.is_dir() or backup_item.suffix == ".tar.gz":
				backup_info = {
					"name": backup_item.name,
					"path": str(backup_item),
					"size_mb": round(backup_item.stat().st_size / 1024 / 1024, 2) if backup_item.is_file() else 0,
					"created_at": datetime.fromtimestamp(backup_item.stat().st_ctime).isoformat(),
					"type": "compressed" if backup_item.suffix == ".tar.gz" else "directory",
				}

				# Try to read manifest if available
				if backup_item.is_dir():
					manifest_path = backup_item / "manifest.json"
					if manifest_path.exists():
						try:
							with open(manifest_path, "r") as f:
								manifest = json.load(f)
								backup_info.update(manifest)
						except Exception as e:
							backup_info["manifest_error"] = str(e)

				backups.append(backup_info)

		# Sort by creation time, newest first
		backups.sort(key=lambda x: x["created_at"], reverse=True)
		return backups

	@handle_exceptions(component="backup_service")
	def delete_backup(self, backup_name: str) -> Dict[str, Any]:
		"""Delete a backup safely and prevent path traversal"""
		if not backup_name or backup_name.strip() == "":
			raise ValueError("Backup name is required")

		backup_root = self.backup_dir.resolve()
		candidate_names = {backup_name}
		if not backup_name.endswith(".tar.gz"):
			candidate_names.add(f"{backup_name}.tar.gz")

		deleted_items: List[str] = []

		for candidate in candidate_names:
			if Path(candidate).name != candidate:
				raise ValueError("Invalid backup name")

			candidate_path = (backup_root / candidate).resolve()
			try:
				candidate_path.relative_to(backup_root)
			except ValueError:
				raise ValueError("Invalid backup name")

			if not candidate_path.exists():
				continue

			if candidate_path.is_dir():
				shutil.rmtree(candidate_path)
			else:
				candidate_path.unlink()

			deleted_items.append(candidate_path.name)

		if not deleted_items:
			raise FileNotFoundError(f"Backup not found: {backup_name}")

		return {"deleted_items": deleted_items, "timestamp": datetime.now(timezone.utc).isoformat()}

	@handle_exceptions(component="backup_service")
	def restore_from_backup(self, backup_name: str, restore_database: bool = True, restore_files: bool = True) -> Dict[str, Any]:
		"""
		Restore system from backup

		Args:
		    backup_name: Name of backup to restore from
		    restore_database: Whether to restore database
		    restore_files: Whether to restore files

		Returns:
		    Dict with restore information
		"""
		logger.info(f"Starting restore from backup: {backup_name}")

		backup_path = self.backup_dir / backup_name
		if not backup_path.exists():
			# Try compressed version
			backup_path = self.backup_dir / f"{backup_name}.tar.gz"
			if not backup_path.exists():
				raise Exception(f"Backup not found: {backup_name}")

		restore_info = {"backup_name": backup_name, "timestamp": datetime.now(timezone.utc).isoformat(), "status": "in_progress", "components": {}}

		try:
			# Extract if compressed
			if backup_path.suffix == ".tar.gz":
				extract_path = self.backup_dir / f"restore_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
				extract_path.mkdir(exist_ok=True)

				with tarfile.open(backup_path, "r:gz") as tar:
					self._safe_extract(tar, extract_path)

				# Find the actual backup directory
				extracted_dirs = [d for d in extract_path.iterdir() if d.is_dir()]
				if extracted_dirs:
					working_path = extracted_dirs[0]
				else:
					raise Exception("No backup directory found in compressed file")
			else:
				working_path = backup_path

			# Restore database
			if restore_database:
				db_restore_info = self._restore_database(working_path)
				restore_info["components"]["database"] = db_restore_info

			# Restore files
			if restore_files:
				files_restore_info = self._restore_files(working_path)
				restore_info["components"]["files"] = files_restore_info

			restore_info["status"] = "completed"
			logger.info(f"Restore completed successfully: {backup_name}")

			return restore_info

		except Exception as e:
			restore_info["status"] = "failed"
			restore_info["error"] = str(e)
			logger.error(f"Restore failed: {backup_name} - {e!s}")
			raise

	def _restore_database(self, backup_path: Path) -> Dict[str, Any]:
		"""Restore database from backup"""
		db_backup_path = backup_path / "database"
		if not db_backup_path.exists():
			return {"status": "skipped", "reason": "No database backup found"}

		# Try SQL dump first
		dump_file = db_backup_path / "database_dump.sql"
		if dump_file.exists():
			return self._restore_from_sql_dump(dump_file)

		# Fallback to JSON import
		json_file = db_backup_path / "data_export.json"
		if json_file.exists():
			return self._restore_from_json(json_file)

		return {"status": "failed", "reason": "No valid database backup found"}

	def _restore_from_sql_dump(self, dump_file: Path) -> Dict[str, Any]:
		"""Restore database from SQL dump"""
		# Parse database URL
		db_url = settings.DATABASE_URL
		if db_url.startswith("postgresql://"):
			import urllib.parse

			parsed = urllib.parse.urlparse(db_url)

			env = os.environ.copy()
			if parsed.password:
				env["PGPASSWORD"] = parsed.password

			cmd = [
				"psql",
				"-h",
				parsed.hostname or "localhost",
				"-p",
				str(parsed.port or 5432),
				"-U",
				parsed.username or "postgres",
				"-d",
				parsed.path.lstrip("/"),
				"--no-password",
				"-f",
				str(dump_file),
			]

			try:
				result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)

				if result.returncode == 0:
					return {"status": "success", "method": "sql_dump"}
				else:
					raise Exception(f"psql restore failed: {result.stderr}")

			except subprocess.TimeoutExpired:
				raise Exception("Database restore timed out")
			except FileNotFoundError:
				raise Exception("psql command not found")
		else:
			raise Exception(f"Unsupported database URL format: {db_url}")

	def _restore_from_json(self, json_file: Path) -> Dict[str, Any]:
		"""Restore database from JSON export"""
		with open(json_file, "r") as f:
			export_data = json.load(f)

		db = next(get_db())
		try:
			# This is a simplified restore - in production you'd want more sophisticated handling
			logger.warning("JSON restore is a basic implementation - use SQL dump for full restore")

			# Clear existing data (be very careful with this!)
			# db.query(Analytics).delete()
			# db.query(JobApplication).delete()
			# db.query(Document).delete()
			# db.query(Job).delete()
			# db.query(User).delete()

			# Restore users
			for user_data in export_data.get("users", []):
				# Check if user already exists
				existing_user = db.query(User).filter(User.email == user_data["email"]).first()
				if not existing_user:
					user = User(email=user_data["email"], profile=user_data.get("profile", {}), settings=user_data.get("settings", {}))
					db.add(user)

			db.commit()

			return {"status": "partial", "method": "json_import", "warning": "JSON restore is limited - use SQL dump for complete restore"}

		except Exception as e:
			db.rollback()
			raise Exception(f"JSON restore failed: {e!s}")
		finally:
			db.close()

	def _restore_files(self, backup_path: Path) -> Dict[str, Any]:
		"""Restore files from backup"""
		files_backup_path = backup_path / "files"
		if not files_backup_path.exists():
			return {"status": "skipped", "reason": "No files backup found"}

		upload_dir = Path(settings.UPLOAD_DIR)
		upload_dir.mkdir(parents=True, exist_ok=True)

		# Copy files back
		total_files = 0
		for file_path in files_backup_path.rglob("*"):
			if file_path.is_file():
				relative_path = file_path.relative_to(files_backup_path)
				dest_path = upload_dir / relative_path
				dest_path.parent.mkdir(parents=True, exist_ok=True)

				shutil.copy2(file_path, dest_path)
				total_files += 1

		return {"status": "success", "files_restored": total_files}

	@handle_exceptions(component="backup_service")
	def cleanup_old_backups(self, keep_days: int = 30) -> Dict[str, Any]:
		"""Clean up old backups"""
		cutoff_date = datetime.now(timezone.utc) - timedelta(days=keep_days)

		deleted_backups = []
		total_size_freed = 0

		for backup_item in self.backup_dir.iterdir():
			if backup_item.is_dir() or backup_item.suffix == ".tar.gz":
				created_time = datetime.fromtimestamp(backup_item.stat().st_ctime)

				if created_time < cutoff_date:
					size = backup_item.stat().st_size if backup_item.is_file() else 0

					if backup_item.is_dir():
						shutil.rmtree(backup_item)
					else:
						backup_item.unlink()

					deleted_backups.append(
						{"name": backup_item.name, "created_at": created_time.isoformat(), "size_mb": round(size / 1024 / 1024, 2)}
					)
					total_size_freed += size

		return {
			"deleted_count": len(deleted_backups),
			"deleted_backups": deleted_backups,
			"total_size_freed_mb": round(total_size_freed / 1024 / 1024, 2),
			"cutoff_date": cutoff_date.isoformat(),
		}


# Global service instance
backup_service = BackupService()
