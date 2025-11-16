"""
Comprehensive data import service for Career Copilot
Supports CSV import for jobs and applications
"""

import csv
import io
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.application import Application
from app.models.job import Job
from app.schemas.import_schemas import (
	ApplicationImportRow,
	ImportResult,
	ImportValidationError,
	JobImportRow,
)
from app.utils.datetime import utc_now

logger = get_logger(__name__)


class ImportService:
	"""Service for importing data from CSV files"""

	async def import_jobs_csv(
		self,
		db: AsyncSession,
		user_id: int,
		csv_content: str,
	) -> ImportResult:
		"""
		Import jobs from CSV content

		Args:
		    db: Database session
		    user_id: User ID for the imported jobs
		    csv_content: CSV file content as string

		Returns:
		    ImportResult with success/failure counts and errors
		"""
		try:
			# Parse CSV
			csv_file = io.StringIO(csv_content)
			reader = csv.DictReader(csv_file)

			total_records = 0
			successful = 0
			failed = 0
			errors: List[ImportValidationError] = []
			created_ids: List[int] = []
			skipped_rows: List[int] = []

			# Process each row
			for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
				total_records += 1

				try:
					# Skip empty rows
					if not any(row.values()):
						skipped_rows.append(row_num)
						continue

					# Validate and parse row
					job_data = self._validate_job_row(row, row_num)

					if job_data is None:
						# Validation failed, error already added
						failed += 1
						errors.append(ImportValidationError(row_number=row_num, error="Row validation failed"))
						continue

					# Parse tech_stack from comma-separated string
					tech_stack = []
					if job_data.get("tech_stack"):
						tech_stack_str = job_data["tech_stack"]
						if isinstance(tech_stack_str, str):
							tech_stack = [t.strip() for t in tech_stack_str.split(",") if t.strip()]

					# Parse date_applied
					date_applied = None
					if job_data.get("date_applied"):
						try:
							date_applied = datetime.fromisoformat(job_data["date_applied"].replace("Z", "+00:00"))
						except (ValueError, AttributeError):
							# Invalid date format, skip it
							pass

					# Create job object
					job = Job(
						user_id=user_id,
						company=job_data["company"],
						title=job_data["title"],
						location=job_data.get("location"),
						description=job_data.get("description"),
						requirements=job_data.get("requirements"),
						responsibilities=job_data.get("responsibilities"),
						salary_min=job_data.get("salary_min"),
						salary_max=job_data.get("salary_max"),
						job_type=job_data.get("job_type"),
						remote_option=job_data.get("remote_option"),
						tech_stack=tech_stack if tech_stack else None,
						application_url=job_data.get("application_url"),
						source=job_data.get("source", "manual"),
						status=job_data.get("status", "not_applied"),
						date_applied=date_applied,
						notes=job_data.get("notes"),
						currency=job_data.get("currency"),
					)

					db.add(job)
					await db.flush()  # Flush to get the ID

					created_ids.append(job.id)
					successful += 1

				except Exception as e:
					failed += 1
					errors.append(ImportValidationError(row_number=row_num, error=str(e)))
					logger.error(f"Error importing job row {row_num}: {e}", exc_info=True)

			# Commit all changes
			await db.commit()

			return ImportResult(
				success=True,
				total_records=total_records,
				successful=successful,
				failed=failed,
				errors=errors,
				created_ids=created_ids,
				skipped_rows=skipped_rows,
				import_metadata={
					"imported_at": utc_now().isoformat(),
					"user_id": user_id,
					"import_type": "jobs",
				},
			)

		except Exception as e:
			await db.rollback()
			logger.error(f"Error importing jobs from CSV: {e}", exc_info=True)
			return ImportResult(
				success=False, total_records=0, successful=0, failed=0, errors=[ImportValidationError(row_number=0, error=f"Import failed: {e!r}")]
			)

	async def import_applications_csv(
		self,
		db: AsyncSession,
		user_id: int,
		csv_content: str,
	) -> ImportResult:
		"""
		Import applications from CSV content

		Args:
		    db: Database session
		    user_id: User ID for the imported applications
		    csv_content: CSV file content as string

		Returns:
		    ImportResult with success/failure counts and errors
		"""
		try:
			# Parse CSV
			csv_file = io.StringIO(csv_content)
			reader = csv.DictReader(csv_file)

			total_records = 0
			successful = 0
			failed = 0
			errors: List[ImportValidationError] = []
			created_ids: List[int] = []
			skipped_rows: List[int] = []

			# Process each row
			for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
				total_records += 1

				try:
					# Skip empty rows
					if not any(row.values()):
						skipped_rows.append(row_num)
						continue

					# Validate and parse row
					app_data = self._validate_application_row(row, row_num)

					if app_data is None:
						# Validation failed
						failed += 1
						errors.append(ImportValidationError(row_number=row_num, error="Row validation failed"))
						continue

					# Verify job exists and belongs to user
					job_id = app_data["job_id"]
					job_result = await db.execute(select(Job).where(Job.id == job_id, Job.user_id == user_id))
					job = job_result.scalar_one_or_none()

					if not job:
						failed += 1
						errors.append(
							ImportValidationError(
								row_number=row_num, field="job_id", error=f"Job with ID {job_id} not found or does not belong to user", value=job_id
							)
						)
						continue

					# Parse dates
					applied_date = self._parse_date(app_data.get("applied_date"))
					response_date = self._parse_date(app_data.get("response_date"))
					interview_date = self._parse_datetime(app_data.get("interview_date"))
					offer_date = self._parse_date(app_data.get("offer_date"))
					follow_up_date = self._parse_date(app_data.get("follow_up_date"))

					# Parse interview_feedback JSON
					interview_feedback = None
					if app_data.get("interview_feedback"):
						try:
							interview_feedback = json.loads(app_data["interview_feedback"])
						except json.JSONDecodeError:
							# Invalid JSON, skip it
							pass

					# Create application object
					application = Application(
						user_id=user_id,
						job_id=job_id,
						status=app_data.get("status", "interested"),
						applied_date=applied_date,
						response_date=response_date,
						interview_date=interview_date,
						offer_date=offer_date,
						follow_up_date=follow_up_date,
						notes=app_data.get("notes"),
						interview_feedback=interview_feedback,
					)

					db.add(application)
					await db.flush()  # Flush to get the ID

					created_ids.append(application.id)
					successful += 1

				except Exception as e:
					failed += 1
					errors.append(ImportValidationError(row_number=row_num, error=str(e)))
					logger.error(f"Error importing application row {row_num}: {e}", exc_info=True)

			# Commit all changes
			await db.commit()

			return ImportResult(
				success=True,
				total_records=total_records,
				successful=successful,
				failed=failed,
				errors=errors,
				created_ids=created_ids,
				skipped_rows=skipped_rows,
				import_metadata={
					"imported_at": utc_now().isoformat(),
					"user_id": user_id,
					"import_type": "applications",
				},
			)

		except Exception as e:
			await db.rollback()
			logger.error(f"Error importing applications from CSV: {e}", exc_info=True)
			return ImportResult(
				success=False, total_records=0, successful=0, failed=0, errors=[ImportValidationError(row_number=0, error=f"Import failed: {e!r}")]
			)

	def _validate_job_row(self, row: Dict[str, Any], row_num: int) -> Optional[Dict[str, Any]]:
		"""
		Validate a job row from CSV

		Args:
		    row: Dictionary of row data
		    row_num: Row number for error reporting

		Returns:
		    Validated data dictionary or None if validation fails
		"""
		try:
			# Required fields
			if not row.get("company") or not row.get("title"):
				return None

			# Create validated data dict
			validated_data = {
				"company": row["company"].strip(),
				"title": row["title"].strip(),
				"location": row.get("location", "").strip() or None,
				"description": row.get("description", "").strip() or None,
				"requirements": row.get("requirements", "").strip() or None,
				"responsibilities": row.get("responsibilities", "").strip() or None,
				"job_type": row.get("job_type", "").strip() or None,
				"remote_option": row.get("remote_option", "").strip() or None,
				"tech_stack": row.get("tech_stack", "").strip() or None,
				"application_url": row.get("application_url", "").strip() or None,
				"source": row.get("source", "manual").strip() or "manual",
				"status": row.get("status", "not_applied").strip() or "not_applied",
				"date_applied": row.get("date_applied", "").strip() or None,
				"notes": row.get("notes", "").strip() or None,
				"currency": row.get("currency", "").strip() or None,
			}

			# Parse salary fields
			if row.get("salary_min"):
				try:
					validated_data["salary_min"] = int(float(row["salary_min"]))
				except (ValueError, TypeError):
					validated_data["salary_min"] = None
			else:
				validated_data["salary_min"] = None

			if row.get("salary_max"):
				try:
					validated_data["salary_max"] = int(float(row["salary_max"]))
				except (ValueError, TypeError):
					validated_data["salary_max"] = None
			else:
				validated_data["salary_max"] = None

			return validated_data

		except Exception as e:
			logger.error(f"Error validating job row {row_num}: {e}", exc_info=True)
			return None

	def _validate_application_row(self, row: Dict[str, Any], row_num: int) -> Optional[Dict[str, Any]]:
		"""
		Validate an application row from CSV

		Args:
		    row: Dictionary of row data
		    row_num: Row number for error reporting

		Returns:
		    Validated data dictionary or None if validation fails
		"""
		try:
			# Required fields
			if not row.get("job_id"):
				return None

			# Parse job_id
			try:
				job_id = int(row["job_id"])
			except (ValueError, TypeError):
				return None

			# Validate status
			status = row.get("status", "interested").strip() or "interested"
			allowed_statuses = ["interested", "applied", "interview", "offer", "rejected", "accepted", "declined"]
			if status not in allowed_statuses:
				status = "interested"

			# Create validated data dict
			validated_data = {
				"job_id": job_id,
				"status": status,
				"applied_date": row.get("applied_date", "").strip() or None,
				"response_date": row.get("response_date", "").strip() or None,
				"interview_date": row.get("interview_date", "").strip() or None,
				"offer_date": row.get("offer_date", "").strip() or None,
				"follow_up_date": row.get("follow_up_date", "").strip() or None,
				"notes": row.get("notes", "").strip() or None,
				"interview_feedback": row.get("interview_feedback", "").strip() or None,
			}

			return validated_data

		except Exception as e:
			logger.error(f"Error validating application row {row_num}: {e}", exc_info=True)
			return None

	def _parse_date(self, date_str: Optional[str]):
		"""Parse date string to date object"""
		if not date_str:
			return None
		try:
			dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
			return dt.date()
		except (ValueError, AttributeError):
			return None

	def _parse_datetime(self, datetime_str: Optional[str]):
		"""Parse datetime string to datetime object"""
		if not datetime_str:
			return None
		try:
			return datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
		except (ValueError, AttributeError):
			return None


# Create singleton instance
import_service = ImportService()
