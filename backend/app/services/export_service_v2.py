"""
Comprehensive data export service for Career Copilot
Supports JSON, CSV, and PDF export formats
"""

import csv
import io
import json
import zipfile
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from app.schemas.export import (
    ApplicationExportData,
    ExportFormat,
    ExportMetadata,
    ExportType,
    JobExportData,
)

logger = get_logger(__name__)


class ExportServiceV2:
    """Enhanced export service with comprehensive format support"""

    async def export_jobs_json(
        self,
        db: AsyncSession,
        user_id: int,
        filters: Optional[Dict[str, Any]] = None,
        include_fields: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """Export jobs in JSON format with filtering and pagination"""
        try:
            # Build query
            query = select(Job).where(Job.user_id == user_id)

            # Apply filters
            if filters:
                if "status" in filters:
                    query = query.where(Job.status == filters["status"])
                if "company" in filters:
                    query = query.where(Job.company.ilike(f"%{filters['company']}%"))
                if "location" in filters:
                    query = query.where(Job.location.ilike(f"%{filters['location']}%"))
                if "job_type" in filters:
                    query = query.where(Job.job_type == filters["job_type"])
                if "remote_option" in filters:
                    query = query.where(Job.remote_option == filters["remote_option"])
                if "date_from" in filters:
                    query = query.where(Job.created_at >= filters["date_from"])
                if "date_to" in filters:
                    query = query.where(Job.created_at <= filters["date_to"])

            # Get total count
            count_result = await db.execute(select(Job.id).where(Job.user_id == user_id))
            total_count = len(count_result.all())

            # Apply pagination
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)

            # Execute query
            result = await db.execute(query)
            jobs = result.scalars().all()

            # Convert to export format
            jobs_data = []
            for job in jobs:
                job_dict = {
                    "id": job.id,
                    "company": job.company,
                    "title": job.title,
                    "location": job.location,
                    "description": job.description,
                    "requirements": job.requirements,
                    "responsibilities": job.responsibilities,
                    "salary_min": job.salary_min,
                    "salary_max": job.salary_max,
                    "job_type": job.job_type,
                    "remote_option": job.remote_option,
                    "tech_stack": job.tech_stack,
                    "application_url": job.application_url,
                    "source": job.source,
                    "status": job.status,
                    "date_applied": job.date_applied.isoformat() if job.date_applied else None,
                    "notes": job.notes,
                    "created_at": job.created_at.isoformat(),
                    "updated_at": job.updated_at.isoformat(),
                    "currency": job.currency,
                }

                # Filter fields if specified
                if include_fields:
                    job_dict = {k: v for k, v in job_dict.items() if k in include_fields}

                jobs_data.append(job_dict)

            return {
                "success": True,
                "data": jobs_data,
                "metadata": {
                    "total_records": total_count,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total_count + page_size - 1) // page_size,
                    "exported_at": datetime.utcnow().isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Error exporting jobs to JSON: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def export_applications_json(
        self,
        db: AsyncSession,
        user_id: int,
        filters: Optional[Dict[str, Any]] = None,
        include_fields: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """Export applications in JSON format with filtering and pagination"""
        try:
            # Build query with job relationship
            query = (
                select(Application)
                .options(selectinload(Application.job))
                .where(Application.user_id == user_id)
            )

            # Apply filters
            if filters:
                if "status" in filters:
                    query = query.where(Application.status == filters["status"])
                if "date_from" in filters:
                    query = query.where(Application.created_at >= filters["date_from"])
                if "date_to" in filters:
                    query = query.where(Application.created_at <= filters["date_to"])

            # Get total count
            count_result = await db.execute(
                select(Application.id).where(Application.user_id == user_id)
            )
            total_count = len(count_result.all())

            # Apply pagination
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)

            # Execute query
            result = await db.execute(query)
            applications = result.scalars().all()

            # Convert to export format
            apps_data = []
            for app in applications:
                app_dict = {
                    "id": app.id,
                    "job_id": app.job_id,
                    "job_title": app.job.title if app.job else None,
                    "job_company": app.job.company if app.job else None,
                    "status": app.status,
                    "applied_date": app.applied_date.isoformat() if app.applied_date else None,
                    "response_date": app.response_date.isoformat() if app.response_date else None,
                    "interview_date": app.interview_date.isoformat() if app.interview_date else None,
                    "offer_date": app.offer_date.isoformat() if app.offer_date else None,
                    "notes": app.notes,
                    "interview_feedback": app.interview_feedback,
                    "follow_up_date": app.follow_up_date.isoformat() if app.follow_up_date else None,
                    "created_at": app.created_at.isoformat(),
                    "updated_at": app.updated_at.isoformat(),
                }

                # Filter fields if specified
                if include_fields:
                    app_dict = {k: v for k, v in app_dict.items() if k in include_fields}

                apps_data.append(app_dict)

            return {
                "success": True,
                "data": apps_data,
                "metadata": {
                    "total_records": total_count,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total_count + page_size - 1) // page_size,
                    "exported_at": datetime.utcnow().isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Error exporting applications to JSON: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def export_jobs_csv(
        self,
        db: AsyncSession,
        user_id: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Export jobs to CSV format"""
        try:
            # Build query
            query = select(Job).where(Job.user_id == user_id)

            # Apply filters
            if filters:
                if "status" in filters:
                    query = query.where(Job.status == filters["status"])
                if "company" in filters:
                    query = query.where(Job.company.ilike(f"%{filters['company']}%"))
                if "date_from" in filters:
                    query = query.where(Job.created_at >= filters["date_from"])
                if "date_to" in filters:
                    query = query.where(Job.created_at <= filters["date_to"])

            # Execute query
            result = await db.execute(query)
            jobs = result.scalars().all()

            # Create CSV
            output = io.StringIO()
            fieldnames = [
                "id",
                "company",
                "title",
                "location",
                "job_type",
                "remote_option",
                "salary_min",
                "salary_max",
                "currency",
                "tech_stack",
                "status",
                "source",
                "application_url",
                "date_applied",
                "created_at",
                "notes",
            ]

            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()

            for job in jobs:
                # Handle tech_stack array
                tech_stack_str = ", ".join(job.tech_stack) if job.tech_stack else ""

                writer.writerow(
                    {
                        "id": job.id,
                        "company": job.company,
                        "title": job.title,
                        "location": job.location or "",
                        "job_type": job.job_type or "",
                        "remote_option": job.remote_option or "",
                        "salary_min": job.salary_min or "",
                        "salary_max": job.salary_max or "",
                        "currency": job.currency or "",
                        "tech_stack": tech_stack_str,
                        "status": job.status,
                        "source": job.source or "",
                        "application_url": job.application_url or "",
                        "date_applied": job.date_applied.isoformat() if job.date_applied else "",
                        "created_at": job.created_at.isoformat(),
                        "notes": (job.notes or "").replace("\n", " ").replace("\r", ""),
                    }
                )

            return output.getvalue()

        except Exception as e:
            logger.error(f"Error exporting jobs to CSV: {e}", exc_info=True)
            raise

    async def export_applications_csv(
        self,
        db: AsyncSession,
        user_id: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Export applications to CSV format"""
        try:
            # Build query with job relationship
            query = (
                select(Application)
                .options(selectinload(Application.job))
                .where(Application.user_id == user_id)
            )

            # Apply filters
            if filters:
                if "status" in filters:
                    query = query.where(Application.status == filters["status"])
                if "date_from" in filters:
                    query = query.where(Application.created_at >= filters["date_from"])
                if "date_to" in filters:
                    query = query.where(Application.created_at <= filters["date_to"])

            # Execute query
            result = await db.execute(query)
            applications = result.scalars().all()

            # Create CSV
            output = io.StringIO()
            fieldnames = [
                "id",
                "job_id",
                "job_title",
                "job_company",
                "status",
                "applied_date",
                "response_date",
                "interview_date",
                "offer_date",
                "follow_up_date",
                "interview_feedback",
                "notes",
                "created_at",
            ]

            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()

            for app in applications:
                # Handle interview_feedback JSON
                feedback_str = ""
                if app.interview_feedback:
                    feedback_str = json.dumps(app.interview_feedback).replace("\n", " ")

                writer.writerow(
                    {
                        "id": app.id,
                        "job_id": app.job_id,
                        "job_title": app.job.title if app.job else "",
                        "job_company": app.job.company if app.job else "",
                        "status": app.status,
                        "applied_date": app.applied_date.isoformat() if app.applied_date else "",
                        "response_date": app.response_date.isoformat() if app.response_date else "",
                        "interview_date": app.interview_date.isoformat() if app.interview_date else "",
                        "offer_date": app.offer_date.isoformat() if app.offer_date else "",
                        "follow_up_date": app.follow_up_date.isoformat() if app.follow_up_date else "",
                        "interview_feedback": feedback_str,
                        "notes": (app.notes or "").replace("\n", " ").replace("\r", ""),
                        "created_at": app.created_at.isoformat(),
                    }
                )

            return output.getvalue()

        except Exception as e:
            logger.error(f"Error exporting applications to CSV: {e}", exc_info=True)
            raise

    async def export_jobs_pdf(
        self,
        db: AsyncSession,
        user_id: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """Export jobs to PDF format"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import (
                SimpleDocTemplate,
                Table,
                TableStyle,
                Paragraph,
                Spacer,
                PageBreak,
            )

            # Build query
            query = select(Job).where(Job.user_id == user_id)

            # Apply filters
            if filters:
                if "status" in filters:
                    query = query.where(Job.status == filters["status"])
                if "company" in filters:
                    query = query.where(Job.company.ilike(f"%{filters['company']}%"))

            # Execute query
            result = await db.execute(query)
            jobs = result.scalars().all()

            # Create PDF
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#1a73e8"),
                spaceAfter=30,
            )
            heading_style = ParagraphStyle(
                "CustomHeading",
                parent=styles["Heading2"],
                fontSize=14,
                textColor=colors.HexColor("#333333"),
                spaceAfter=12,
            )

            # Title
            title = Paragraph("Job Export Report", title_style)
            elements.append(title)

            # Metadata
            metadata_text = f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}<br/>Total Jobs: {len(jobs)}"
            elements.append(Paragraph(metadata_text, styles["Normal"]))
            elements.append(Spacer(1, 0.3 * inch))

            # Jobs
            for i, job in enumerate(jobs):
                # Job header
                job_title = f"{job.title} at {job.company}"
                elements.append(Paragraph(job_title, heading_style))

                # Job details table
                data = [
                    ["Location:", job.location or "N/A"],
                    ["Job Type:", job.job_type or "N/A"],
                    ["Remote:", job.remote_option or "N/A"],
                    ["Status:", job.status],
                    [
                        "Salary:",
                        f"${job.salary_min:,} - ${job.salary_max:,} {job.currency or 'USD'}"
                        if job.salary_min and job.salary_max
                        else "Not specified",
                    ],
                    ["Source:", job.source or "N/A"],
                    ["Posted:", job.created_at.strftime("%Y-%m-%d")],
                ]

                if job.tech_stack:
                    tech_str = ", ".join(job.tech_stack[:10])  # Limit to 10 items
                    if len(job.tech_stack) > 10:
                        tech_str += f" (+{len(job.tech_stack) - 10} more)"
                    data.append(["Tech Stack:", tech_str])

                table = Table(data, colWidths=[1.5 * inch, 5 * inch])
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 10),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                            ("TOPPADDING", (0, 0), (-1, -1), 8),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ]
                    )
                )
                elements.append(table)

                # Description
                if job.description:
                    elements.append(Spacer(1, 0.1 * inch))
                    desc_text = job.description[:500]  # Limit length
                    if len(job.description) > 500:
                        desc_text += "..."
                    elements.append(Paragraph(f"<b>Description:</b> {desc_text}", styles["Normal"]))

                # Notes
                if job.notes:
                    elements.append(Spacer(1, 0.1 * inch))
                    notes_text = job.notes[:300]
                    if len(job.notes) > 300:
                        notes_text += "..."
                    elements.append(Paragraph(f"<b>Notes:</b> {notes_text}", styles["Normal"]))

                elements.append(Spacer(1, 0.3 * inch))

                # Page break every 3 jobs
                if (i + 1) % 3 == 0 and i < len(jobs) - 1:
                    elements.append(PageBreak())

            # Build PDF
            doc.build(elements)
            buffer.seek(0)
            return buffer.getvalue()

        except ImportError:
            logger.error("ReportLab not installed. Install with: pip install reportlab")
            raise Exception("PDF export requires reportlab library")
        except Exception as e:
            logger.error(f"Error exporting jobs to PDF: {e}", exc_info=True)
            raise

    async def export_applications_pdf(
        self,
        db: AsyncSession,
        user_id: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """Export applications to PDF format"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import (
                SimpleDocTemplate,
                Table,
                TableStyle,
                Paragraph,
                Spacer,
                PageBreak,
            )
            from reportlab.graphics.shapes import Drawing
            from reportlab.graphics.charts.piecharts import Pie

            # Build query with job relationship
            query = (
                select(Application)
                .options(selectinload(Application.job))
                .where(Application.user_id == user_id)
            )

            # Apply filters
            if filters:
                if "status" in filters:
                    query = query.where(Application.status == filters["status"])

            # Execute query
            result = await db.execute(query)
            applications = result.scalars().all()

            # Create PDF
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#1a73e8"),
                spaceAfter=30,
            )
            heading_style = ParagraphStyle(
                "CustomHeading",
                parent=styles["Heading2"],
                fontSize=14,
                textColor=colors.HexColor("#333333"),
                spaceAfter=12,
            )

            # Title
            title = Paragraph("Application Tracking Report", title_style)
            elements.append(title)

            # Metadata and statistics
            status_counts = {}
            for app in applications:
                status_counts[app.status] = status_counts.get(app.status, 0) + 1

            metadata_text = f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}<br/>Total Applications: {len(applications)}"
            elements.append(Paragraph(metadata_text, styles["Normal"]))
            elements.append(Spacer(1, 0.2 * inch))

            # Status summary
            if status_counts:
                summary_text = "<b>Status Summary:</b><br/>"
                for status, count in sorted(status_counts.items()):
                    summary_text += f"• {status.title()}: {count}<br/>"
                elements.append(Paragraph(summary_text, styles["Normal"]))
                elements.append(Spacer(1, 0.3 * inch))

            # Applications
            for i, app in enumerate(applications):
                # Application header
                app_title = f"{app.job.title if app.job else 'Unknown'} at {app.job.company if app.job else 'Unknown'}"
                elements.append(Paragraph(app_title, heading_style))

                # Application details table
                data = [
                    ["Status:", app.status.title()],
                    ["Applied:", app.applied_date.strftime("%Y-%m-%d") if app.applied_date else "N/A"],
                ]

                if app.response_date:
                    data.append(["Response:", app.response_date.strftime("%Y-%m-%d")])
                if app.interview_date:
                    data.append(["Interview:", app.interview_date.strftime("%Y-%m-%d %H:%M")])
                if app.offer_date:
                    data.append(["Offer:", app.offer_date.strftime("%Y-%m-%d")])
                if app.follow_up_date:
                    data.append(["Follow-up:", app.follow_up_date.strftime("%Y-%m-%d")])

                table = Table(data, colWidths=[1.5 * inch, 5 * inch])
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 10),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                            ("TOPPADDING", (0, 0), (-1, -1), 8),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ]
                    )
                )
                elements.append(table)

                # Interview feedback
                if app.interview_feedback:
                    elements.append(Spacer(1, 0.1 * inch))
                    feedback_text = json.dumps(app.interview_feedback, indent=2)[:300]
                    if len(json.dumps(app.interview_feedback)) > 300:
                        feedback_text += "..."
                    elements.append(Paragraph(f"<b>Interview Feedback:</b><br/><pre>{feedback_text}</pre>", styles["Normal"]))

                # Notes
                if app.notes:
                    elements.append(Spacer(1, 0.1 * inch))
                    notes_text = app.notes[:300]
                    if len(app.notes) > 300:
                        notes_text += "..."
                    elements.append(Paragraph(f"<b>Notes:</b> {notes_text}", styles["Normal"]))

                elements.append(Spacer(1, 0.3 * inch))

                # Page break every 4 applications
                if (i + 1) % 4 == 0 and i < len(applications) - 1:
                    elements.append(PageBreak())

            # Build PDF
            doc.build(elements)
            buffer.seek(0)
            return buffer.getvalue()

        except ImportError:
            logger.error("ReportLab not installed. Install with: pip install reportlab")
            raise Exception("PDF export requires reportlab library")
        except Exception as e:
            logger.error(f"Error exporting applications to PDF: {e}", exc_info=True)
            raise

    async def create_full_backup(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> bytes:
        """Create a complete backup archive with all user data"""
        try:
            # Get user profile
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()

            if not user:
                raise Exception("User not found")

            # Get all jobs
            jobs_result = await db.execute(select(Job).where(Job.user_id == user_id))
            jobs = jobs_result.scalars().all()

            # Get all applications
            apps_result = await db.execute(
                select(Application)
                .options(selectinload(Application.job))
                .where(Application.user_id == user_id)
            )
            applications = apps_result.scalars().all()

            # Create ZIP archive
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                # Add user profile JSON
                user_data = {
                    "id": user.id,
                    "email": user.email,
                    "profile": user.profile if hasattr(user, "profile") else {},
                    "settings": user.settings if hasattr(user, "settings") else {},
                    "created_at": user.created_at.isoformat() if hasattr(user, "created_at") else None,
                }
                zip_file.writestr("user_profile.json", json.dumps(user_data, indent=2))

                # Add jobs JSON
                jobs_data = []
                for job in jobs:
                    jobs_data.append(
                        {
                            "id": job.id,
                            "company": job.company,
                            "title": job.title,
                            "location": job.location,
                            "description": job.description,
                            "requirements": job.requirements,
                            "responsibilities": job.responsibilities,
                            "salary_min": job.salary_min,
                            "salary_max": job.salary_max,
                            "job_type": job.job_type,
                            "remote_option": job.remote_option,
                            "tech_stack": job.tech_stack,
                            "application_url": job.application_url,
                            "source": job.source,
                            "status": job.status,
                            "date_applied": job.date_applied.isoformat() if job.date_applied else None,
                            "notes": job.notes,
                            "created_at": job.created_at.isoformat(),
                            "updated_at": job.updated_at.isoformat(),
                            "currency": job.currency,
                        }
                    )
                zip_file.writestr("jobs.json", json.dumps(jobs_data, indent=2))

                # Add applications JSON
                apps_data = []
                for app in applications:
                    apps_data.append(
                        {
                            "id": app.id,
                            "job_id": app.job_id,
                            "job_title": app.job.title if app.job else None,
                            "job_company": app.job.company if app.job else None,
                            "status": app.status,
                            "applied_date": app.applied_date.isoformat() if app.applied_date else None,
                            "response_date": app.response_date.isoformat() if app.response_date else None,
                            "interview_date": app.interview_date.isoformat() if app.interview_date else None,
                            "offer_date": app.offer_date.isoformat() if app.offer_date else None,
                            "notes": app.notes,
                            "interview_feedback": app.interview_feedback,
                            "follow_up_date": app.follow_up_date.isoformat() if app.follow_up_date else None,
                            "created_at": app.created_at.isoformat(),
                            "updated_at": app.updated_at.isoformat(),
                        }
                    )
                zip_file.writestr("applications.json", json.dumps(apps_data, indent=2))

                # Add CSV exports
                jobs_csv = await self.export_jobs_csv(db, user_id)
                zip_file.writestr("jobs.csv", jobs_csv)

                apps_csv = await self.export_applications_csv(db, user_id)
                zip_file.writestr("applications.csv", apps_csv)

                # Add metadata
                metadata = {
                    "export_date": datetime.utcnow().isoformat(),
                    "export_version": "2.0",
                    "user_id": user_id,
                    "total_jobs": len(jobs),
                    "total_applications": len(applications),
                }
                zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))

                # Add README
                readme_content = """Career Copilot Data Export
================================

This archive contains a complete backup of your Career Copilot data.

Contents:
- user_profile.json: Your user profile and settings
- jobs.json: All your saved jobs in JSON format
- jobs.csv: All your saved jobs in CSV format
- applications.json: All your applications in JSON format
- applications.csv: All your applications in CSV format
- metadata.json: Export metadata and statistics

To restore this data, use the import functionality in Career Copilot.

Export Date: {export_date}
Total Jobs: {total_jobs}
Total Applications: {total_applications}
""".format(
                    export_date=metadata["export_date"],
                    total_jobs=metadata["total_jobs"],
                    total_applications=metadata["total_applications"],
                )
                zip_file.writestr("README.txt", readme_content)

            zip_buffer.seek(0)
            return zip_buffer.getvalue()

        except Exception as e:
            logger.error(f"Error creating full backup: {e}", exc_info=True)
            raise


# Create singleton instance
export_service_v2 = ExportServiceV2()
