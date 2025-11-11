"""
Data export API endpoints - Comprehensive export functionality
Supports JSON, CSV, and PDF formats for jobs and applications
"""

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.export import ExportFormat, ExportType
from app.services.export_service_v2 import export_service_v2

router = APIRouter(prefix="/api/v1/export", tags=["export"])


@router.get("/jobs")
async def export_jobs(
    format: ExportFormat = Query(ExportFormat.JSON, description="Export format (json, csv, pdf)"),
    status: Optional[str] = Query(None, description="Filter by job status"),
    company: Optional[str] = Query(None, description="Filter by company name"),
    location: Optional[str] = Query(None, description="Filter by location"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    remote_option: Optional[str] = Query(None, description="Filter by remote option"),
    date_from: Optional[datetime] = Query(None, description="Filter jobs created after this date"),
    date_to: Optional[datetime] = Query(None, description="Filter jobs created before this date"),
    page: int = Query(1, ge=1, description="Page number for pagination (JSON only)"),
    page_size: int = Query(100, ge=1, le=1000, description="Records per page (JSON only)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export jobs in specified format with optional filtering and pagination.
    
    Supports:
    - JSON: Paginated, structured data with metadata
    - CSV: Flat file format suitable for spreadsheets
    - PDF: Professional formatted report with charts
    """
    try:
        # Build filters
        filters = {}
        if status:
            filters["status"] = status
        if company:
            filters["company"] = company
        if location:
            filters["location"] = location
        if job_type:
            filters["job_type"] = job_type
        if remote_option:
            filters["remote_option"] = remote_option
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to

        if format == ExportFormat.JSON:
            result = await export_service_v2.export_jobs_json(
                db, current_user.id, filters, page=page, page_size=page_size
            )
            if not result.get("success"):
                raise HTTPException(status_code=500, detail=result.get("error"))
            return result

        elif format == ExportFormat.CSV:
            csv_content = await export_service_v2.export_jobs_csv(db, current_user.id, filters)
            filename = f"jobs_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

        elif format == ExportFormat.PDF:
            pdf_content = await export_service_v2.export_jobs_pdf(db, current_user.id, filters)
            filename = f"jobs_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/applications")
async def export_applications(
    format: ExportFormat = Query(ExportFormat.JSON, description="Export format (json, csv, pdf)"),
    status: Optional[str] = Query(None, description="Filter by application status"),
    date_from: Optional[datetime] = Query(None, description="Filter applications created after this date"),
    date_to: Optional[datetime] = Query(None, description="Filter applications created before this date"),
    page: int = Query(1, ge=1, description="Page number for pagination (JSON only)"),
    page_size: int = Query(100, ge=1, le=1000, description="Records per page (JSON only)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export applications in specified format with optional filtering and pagination.
    
    Supports:
    - JSON: Paginated, structured data with job details
    - CSV: Flat file format with interview feedback as JSON string
    - PDF: Professional formatted report with status summary
    """
    try:
        # Build filters
        filters = {}
        if status:
            filters["status"] = status
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to

        if format == ExportFormat.JSON:
            result = await export_service_v2.export_applications_json(
                db, current_user.id, filters, page=page, page_size=page_size
            )
            if not result.get("success"):
                raise HTTPException(status_code=500, detail=result.get("error"))
            return result

        elif format == ExportFormat.CSV:
            csv_content = await export_service_v2.export_applications_csv(db, current_user.id, filters)
            filename = f"applications_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

        elif format == ExportFormat.PDF:
            pdf_content = await export_service_v2.export_applications_pdf(db, current_user.id, filters)
            filename = f"applications_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/full-backup")
async def create_full_backup(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a complete backup archive containing all user data.
    
    The backup includes:
    - User profile and settings (JSON)
    - All jobs (JSON and CSV)
    - All applications (JSON and CSV)
    - Export metadata
    - README with instructions
    
    Returns a ZIP archive for download.
    """
    try:
        zip_content = await export_service_v2.create_full_backup(db, current_user.id)
        filename = f"career_copilot_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
        return Response(
            content=zip_content,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup creation failed: {str(e)}")
