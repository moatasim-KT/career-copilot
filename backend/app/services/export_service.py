"""
Data export service for backup and migration
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from io import StringIO
from sqlalchemy.orm import Session
import logging

from app.models.user import User
from app.models.job import Job
from app.models.application import JobApplication
from app.models.document import Document
from app.models.analytics import Analytics

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting user data"""
    
    def export_user_data(self, db: Session, user_id: int, format: str = 'json') -> Dict:
        """Export all user data in specified format"""
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        # Gather all user data
        data = {
            "user": self._export_user_profile(user),
            "jobs": self._export_jobs(db, user_id),
            "applications": self._export_applications(db, user_id),
            "documents": self._export_documents(db, user_id),
            "analytics": self._export_analytics(db, user_id),
            "export_metadata": {
                "exported_at": datetime.now().isoformat(),
                "format": format,
                "version": "1.0"
            }
        }
        
        if format == 'json':
            return self._format_json(data)
        elif format == 'csv':
            return self._format_csv(data)
        else:
            return {"error": f"Unsupported format: {format}"}
    
    def _export_user_profile(self, user: User) -> Dict:
        """Export user profile data"""
        return {
            "id": user.id,
            "email": user.email,
            "profile": user.profile,
            "settings": user.settings,
            "created_at": user.created_at.isoformat(),
            "last_active": user.last_active.isoformat()
        }
    
    def _export_jobs(self, db: Session, user_id: int) -> List[Dict]:
        """Export user's jobs"""
        jobs = db.query(Job).filter(Job.user_id == user_id).all()
        
        return [
            {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "requirements": job.requirements,
                "description": job.description,
                "status": job.status,
                "source": job.source,
                "date_posted": job.date_posted.isoformat() if job.date_posted else None,
                "created_at": job.created_at.isoformat()
            }
            for job in jobs
        ]
    
    def _export_applications(self, db: Session, user_id: int) -> List[Dict]:
        """Export user's applications"""
        applications = db.query(JobApplication).filter(
            JobApplication.user_id == user_id
        ).all()
        
        return [
            {
                "id": app.id,
                "job_id": app.job_id,
                "status": app.status,
                "applied_date": app.applied_date.isoformat() if app.applied_date else None,
                "notes": app.notes,
                "documents": app.documents,
                "created_at": app.created_at.isoformat()
            }
            for app in applications
        ]
    
    def _export_documents(self, db: Session, user_id: int) -> List[Dict]:
        """Export user's documents metadata"""
        documents = db.query(Document).filter(Document.user_id == user_id).all()
        
        return [
            {
                "id": doc.id,
                "filename": doc.original_filename,
                "document_type": doc.document_type,
                "version": doc.version,
                "usage_count": doc.usage_count,
                "tags": doc.tags,
                "created_at": doc.created_at.isoformat()
            }
            for doc in documents
        ]
    
    def _export_analytics(self, db: Session, user_id: int) -> List[Dict]:
        """Export user's analytics data"""
        analytics = db.query(Analytics).filter(
            Analytics.user_id == user_id
        ).order_by(Analytics.generated_at.desc()).limit(100).all()
        
        return [
            {
                "type": a.type,
                "data": a.data,
                "generated_at": a.generated_at.isoformat()
            }
            for a in analytics
        ]
    
    def _format_json(self, data: Dict) -> Dict:
        """Format data as JSON"""
        return {
            "success": True,
            "format": "json",
            "data": data,
            "size_estimate_kb": len(json.dumps(data)) / 1024
        }
    
    def _format_csv(self, data: Dict) -> Dict:
        """Format data as CSV files"""
        csv_files = {}
        
        # Jobs CSV
        if data.get('jobs'):
            jobs_csv = StringIO()
            writer = csv.DictWriter(jobs_csv, fieldnames=data['jobs'][0].keys())
            writer.writeheader()
            writer.writerows(data['jobs'])
            csv_files['jobs.csv'] = jobs_csv.getvalue()
        
        # Applications CSV
        if data.get('applications'):
            apps_csv = StringIO()
            writer = csv.DictWriter(apps_csv, fieldnames=data['applications'][0].keys())
            writer.writeheader()
            writer.writerows(data['applications'])
            csv_files['applications.csv'] = apps_csv.getvalue()
        
        return {
            "success": True,
            "format": "csv",
            "files": csv_files,
            "file_count": len(csv_files)
        }
    
    def export_jobs_to_csv(self, db: Session, user_id: int) -> str:
        """Export jobs to CSV string"""
        jobs = db.query(Job).filter(Job.user_id == user_id).all()
        
        if not jobs:
            return ""
        
        output = StringIO()
        fieldnames = ['title', 'company', 'location', 'salary_min', 'salary_max', 
                     'status', 'source', 'date_posted', 'created_at']
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for job in jobs:
            writer.writerow({
                'title': job.title,
                'company': job.company,
                'location': job.location or '',
                'salary_min': job.salary_min or '',
                'salary_max': job.salary_max or '',
                'status': job.status,
                'source': job.source,
                'date_posted': job.date_posted.isoformat() if job.date_posted else '',
                'created_at': job.created_at.isoformat()
            })
        
        return output.getvalue()
    
    def import_user_data(self, db: Session, user_id: int, data: Dict) -> Dict:
        """Import user data from export"""
        try:
            imported_counts = {
                "jobs": 0,
                "applications": 0,
                "documents": 0
            }
            
            # Import jobs
            if 'jobs' in data:
                for job_data in data['jobs']:
                    # Check if job already exists
                    existing = db.query(Job).filter(
                        Job.user_id == user_id,
                        Job.title == job_data['title'],
                        Job.company == job_data['company']
                    ).first()
                    
                    if not existing:
                        job = Job(
                            user_id=user_id,
                            title=job_data['title'],
                            company=job_data['company'],
                            location=job_data.get('location'),
                            salary_min=job_data.get('salary_min'),
                            salary_max=job_data.get('salary_max'),
                            requirements=job_data.get('requirements', {}),
                            description=job_data.get('description'),
                            status=job_data.get('status', 'not_applied'),
                            source=job_data.get('source', 'import')
                        )
                        db.add(job)
                        imported_counts['jobs'] += 1
            
            db.commit()
            
            return {
                "success": True,
                "imported": imported_counts
            }
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_backup_archive(self, db: Session, user_id: int) -> Dict:
        """Create a complete backup archive with all user data and files"""
        try:
            from zipfile import ZipFile
            from tempfile import NamedTemporaryFile
            import os
            
            # Get all user data
            export_data = self.export_user_data(db, user_id, 'json')
            if 'error' in export_data:
                return export_data
            
            # Create temporary zip file
            with NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
                with ZipFile(temp_file.name, 'w') as zip_file:
                    # Add JSON data
                    zip_file.writestr('user_data.json', 
                                    json.dumps(export_data['data'], indent=2))
                    
                    # Add CSV exports
                    csv_data = self.export_user_data(db, user_id, 'csv')
                    if 'files' in csv_data:
                        for filename, content in csv_data['files'].items():
                            zip_file.writestr(f'csv/{filename}', content)
                    
                    # Add document files if they exist
                    documents = db.query(Document).filter(Document.user_id == user_id).all()
                    for doc in documents:
                        file_path = Path(f"uploads/{doc.filename}")
                        if file_path.exists():
                            zip_file.write(file_path, f'documents/{doc.original_filename}')
                
                return {
                    "success": True,
                    "backup_file": temp_file.name,
                    "size_bytes": os.path.getsize(temp_file.name)
                }
                
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def export_for_migration(self, db: Session, user_id: int) -> Dict:
        """Export data in format suitable for migration to other systems"""
        try:
            # Get all user data
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found"}
            
            # Create migration-friendly format
            migration_data = {
                "format_version": "1.0",
                "export_type": "migration",
                "exported_at": datetime.now().isoformat(),
                "user": {
                    "email": user.email,
                    "profile": user.profile,
                    "settings": user.settings
                },
                "jobs": [],
                "applications": [],
                "analytics_summary": {},
                "offline_capabilities": {
                    "service_worker_enabled": True,
                    "indexeddb_storage": True,
                    "background_sync": True,
                    "cache_strategies": ["network-first", "cache-first", "stale-while-revalidate"]
                }
            }
            
            # Export jobs with full details
            jobs = db.query(Job).filter(Job.user_id == user_id).all()
            for job in jobs:
                job_data = {
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "salary_range": {
                        "min": job.salary_min,
                        "max": job.salary_max,
                        "currency": getattr(job, 'currency', 'USD')
                    },
                    "requirements": job.requirements,
                    "description": job.description,
                    "status": job.status,
                    "source": job.source,
                    "dates": {
                        "posted": job.date_posted.isoformat() if job.date_posted else None,
                        "added": job.created_at.isoformat(),
                        "applied": job.date_applied.isoformat() if job.date_applied else None
                    },
                    "recommendation_score": float(job.recommendation_score) if job.recommendation_score else None,
                    "tags": job.tags or []
                }
                migration_data["jobs"].append(job_data)
            
            # Export applications
            applications = db.query(JobApplication).filter(JobApplication.user_id == user_id).all()
            for app in applications:
                app_data = {
                    "job_reference": {
                        "title": app.job.title if app.job else "Unknown",
                        "company": app.job.company if app.job else "Unknown"
                    },
                    "status": app.status,
                    "applied_date": app.applied_date.isoformat() if app.applied_date else None,
                    "response_date": app.response_date.isoformat() if app.response_date else None,
                    "notes": app.notes,
                    "documents_used": app.documents or []
                }
                migration_data["applications"].append(app_data)
            
            # Add analytics summary
            analytics = db.query(Analytics).filter(
                Analytics.user_id == user_id
            ).order_by(Analytics.generated_at.desc()).limit(10).all()
            
            migration_data["analytics_summary"] = {
                "total_jobs": len(migration_data["jobs"]),
                "total_applications": len(migration_data["applications"]),
                "application_rate": len(migration_data["applications"]) / max(len(migration_data["jobs"]), 1),
                "recent_analytics": [
                    {
                        "type": a.type,
                        "generated_at": a.generated_at.isoformat(),
                        "summary": a.data.get("summary", {}) if isinstance(a.data, dict) else {}
                    }
                    for a in analytics
                ]
            }
            
            return {
                "success": True,
                "migration_data": migration_data,
                "compatibility": {
                    "career_copilot": "1.0",
                    "generic_json": True,
                    "csv_compatible": True
                }
            }
            
        except Exception as e:
            logger.error(f"Migration export failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


    def prepare_offline_export(self, db: Session, user_id: int) -> Dict:
        """Prepare comprehensive offline data package"""
        try:
            # Get all user data
            user_data = self.export_user_data(db, user_id, 'json')
            if 'error' in user_data:
                return user_data
            
            # Add offline-specific metadata
            offline_package = {
                "offline_version": "1.0",
                "prepared_at": datetime.now().isoformat(),
                "user_data": user_data['data'],
                "offline_manifest": {
                    "cached_endpoints": [
                        "/api/v1/jobs",
                        "/api/v1/profile", 
                        "/api/v1/analytics",
                        "/api/v1/recommendations",
                        "/api/v1/applications"
                    ],
                    "cache_duration_hours": 24,
                    "sync_strategies": {
                        "jobs": "background-sync",
                        "profile": "immediate-sync",
                        "applications": "background-sync"
                    },
                    "fallback_data": {
                        "recommendations": "local-algorithm",
                        "skill_analysis": "regex-based",
                        "market_trends": "historical-data"
                    }
                },
                "storage_estimate": {
                    "jobs_count": len(user_data['data'].get('jobs', [])),
                    "applications_count": len(user_data['data'].get('applications', [])),
                    "documents_count": len(user_data['data'].get('documents', [])),
                    "estimated_size_mb": len(json.dumps(user_data['data'])) / (1024 * 1024)
                }
            }
            
            return {
                "success": True,
                "offline_package": offline_package,
                "ready_for_offline": True
            }
            
        except Exception as e:
            logger.error(f"Offline export preparation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def export_with_offline_support(self, db: Session, user_id: int, include_offline_data: bool = True) -> Dict:
        """Export data with offline functionality support"""
        try:
            # Get standard export
            standard_export = self.export_user_data(db, user_id, 'json')
            if 'error' in standard_export:
                return standard_export
            
            export_data = standard_export['data']
            
            if include_offline_data:
                # Add offline support data
                export_data['offline_support'] = {
                    "service_worker_config": {
                        "cache_name": "career-copilot-v1",
                        "static_cache": "career-copilot-static-v1", 
                        "api_cache": "career-copilot-api-v1",
                        "cache_strategies": {
                            "static_assets": "cache-first",
                            "api_endpoints": "network-first",
                            "user_data": "stale-while-revalidate"
                        }
                    },
                    "indexeddb_schema": {
                        "version": 1,
                        "stores": [
                            {
                                "name": "pendingActions",
                                "keyPath": "id",
                                "indexes": ["type", "timestamp"]
                            },
                            {
                                "name": "cachedData", 
                                "keyPath": "key",
                                "indexes": ["timestamp"]
                            },
                            {
                                "name": "offlineJobs",
                                "keyPath": "id",
                                "indexes": ["status", "company"]
                            },
                            {
                                "name": "userProfile",
                                "keyPath": "id"
                            }
                        ]
                    },
                    "sync_configuration": {
                        "background_sync_tags": [
                            "job-application-sync",
                            "profile-update-sync",
                            "document-upload-sync"
                        ],
                        "retry_intervals": [1000, 5000, 15000, 30000],
                        "max_retries": 3
                    }
                }
            
            return {
                "success": True,
                "format": "json",
                "data": export_data,
                "offline_ready": include_offline_data,
                "export_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Export with offline support failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


export_service = ExportService()