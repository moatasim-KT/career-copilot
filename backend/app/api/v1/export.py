"""
Data export API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
import json

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.export_service import export_service

router = APIRouter()


@router.get("/user-data")
async def export_user_data(
    format: str = Query('json', regex='^(json|csv)$'),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export all user data in specified format"""
    result = export_service.export_user_data(db, current_user.id, format)
    
    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result


@router.get("/jobs/csv")
async def export_jobs_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export jobs as CSV file"""
    csv_content = export_service.export_jobs_to_csv(db, current_user.id)
    
    if not csv_content:
        raise HTTPException(status_code=404, detail="No jobs found to export")
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=jobs_export.csv"
        }
    )


@router.post("/import")
async def import_user_data(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import user data from export"""
    result = export_service.import_user_data(db, current_user.id, data)
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error', 'Import failed'))
    
    return result


@router.get("/backup")
async def create_backup_archive(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create complete backup archive"""
    result = export_service.create_backup_archive(db, current_user.id)
    
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Backup creation failed'))
    
    return result


@router.get("/migration")
async def export_for_migration(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export data in migration-friendly format"""
    result = export_service.export_for_migration(db, current_user.id)
    
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Migration export failed'))
    
    return result


@router.get("/offline-package")
async def prepare_offline_package(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Prepare comprehensive offline data package"""
    result = export_service.prepare_offline_export(db, current_user.id)
    
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Offline package preparation failed'))
    
    return result


@router.get("/with-offline-support")
async def export_with_offline_support(
    include_offline_data: bool = Query(True, description="Include offline functionality data"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export data with offline functionality support"""
    result = export_service.export_with_offline_support(db, current_user.id, include_offline_data)
    
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Export with offline support failed'))
    
    return result