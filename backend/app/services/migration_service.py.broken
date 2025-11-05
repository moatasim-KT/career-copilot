"""
Data migration service for consolidating Job_Tracker_1 and Job_tracker_2 data
"""

import os
import sqlite3
import shutil
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from app.models.user import User
from app.models.job import Job
from app.models.application import Application
from app.models.document import Document
from app.core.database import get_db

logger = logging.getLogger(__name__)


class JobTracker1Extractor:
    """Extract and migrate data from Job_Tracker_1 (Flask/SQLite) system"""
    
    def __init__(self, db_path: str, uploads_path: str):
        """
        Initialize the Job_Tracker_1 extractor
        
        Args:
            db_path: Path to Job_Tracker_1 SQLite database
            uploads_path: Path to Job_Tracker_1 uploads directory
        """
        self.db_path = db_path
        self.uploads_path = uploads_path
        self.migration_stats = {
            'jobs_extracted': 0,
            'notes_extracted': 0,
            'contacts_extracted': 0,
            'files_migrated': 0,
            'errors': []
        }
    
    def extract_jobs(self) -> List[Dict]:
        """
        Extract job data from Job_Tracker_1 SQLite database
        
        Returns:
            List of job dictionaries with normalized data
        """
        jobs = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            
            # Extract jobs with all fields
            cursor.execute("""
                SELECT 
                    id, title, company, location, description, url, salary, 
                    job_type, date_posted, date_added, status, date_applied, 
                    parsed_data, company_data, company_reviews
                FROM job
                ORDER BY date_added DESC
            """)
            
            job_rows = cursor.fetchall()
            
            for row in job_rows:
                job_data = self._normalize_job_data(dict(row))
                
                # Extract associated notes
                cursor.execute("SELECT content, date_added FROM note WHERE job_id = ?", (row['id'],))
                notes = cursor.fetchall()
                job_data['notes'] = [{'content': note['content'], 'date_added': note['date_added']} for note in notes]
                
                # Extract associated contacts
                cursor.execute("""
                    SELECT name, title, email, phone, linkedin, notes 
                    FROM contact WHERE job_id = ?
                """, (row['id'],))
                contacts = cursor.fetchall()
                job_data['contacts'] = [dict(contact) for contact in contacts]
                
                jobs.append(job_data)
                self.migration_stats['jobs_extracted'] += 1
                self.migration_stats['notes_extracted'] += len(notes)
                self.migration_stats['contacts_extracted'] += len(contacts)
            
            conn.close()
            logger.info(f"Extracted {len(jobs)} jobs from Job_Tracker_1")
            
        except Exception as e:
            error_msg = f"Error extracting jobs from Job_Tracker_1: {str(e)}"
            logger.error(error_msg)
            self.migration_stats['errors'].append(error_msg)
            
        return jobs
    
    def _normalize_job_data(self, raw_job: Dict) -> Dict:
        """
        Normalize Job_Tracker_1 job data to unified schema format
        
        Args:
            raw_job: Raw job data from SQLite
            
        Returns:
            Normalized job data dictionary
        """
        # Parse salary information
        salary_min, salary_max = self._parse_salary(raw_job.get('salary'))
        
        # Parse job requirements from description and parsed_data
        requirements = self._extract_requirements(
            raw_job.get('description', ''),
            raw_job.get('parsed_data')
        )
        
        # Map Job_Tracker_1 status to unified status
        unified_status = self._map_job_status(raw_job.get('status', 'Saved'))
        
        # Parse dates
        date_posted = self._parse_date(raw_job.get('date_posted'))
        date_added = self._parse_date(raw_job.get('date_added'))
        date_applied = self._parse_date(raw_job.get('date_applied'))
        
        return {
            'original_id': raw_job['id'],
            'title': raw_job.get('title', '').strip(),
            'company': raw_job.get('company', '').strip(),
            'location': raw_job.get('location', '').strip() if raw_job.get('location') else None,
            'description': raw_job.get('description', '').strip() if raw_job.get('description') else None,
            'application_url': raw_job.get('url', '').strip() if raw_job.get('url') else None,
            'salary_min': salary_min,
            'salary_max': salary_max,
            'currency': 'USD',  # Default currency for Job_Tracker_1
            'requirements': requirements,
            'status': unified_status,
            'source': 'manual',  # Job_Tracker_1 jobs are manually added
            'date_posted': date_posted,
            'date_added': date_added,
            'date_applied': date_applied,
            'tags': self._extract_tags(raw_job),
            'job_type': raw_job.get('job_type'),
            'company_data': raw_job.get('company_data'),
            'company_reviews': raw_job.get('company_reviews'),
            'parsed_data': raw_job.get('parsed_data')
        }
    
    def _parse_salary(self, salary_str: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
        """
        Parse salary string to extract min and max values
        
        Args:
            salary_str: Salary string from Job_Tracker_1
            
        Returns:
            Tuple of (salary_min, salary_max)
        """
        if not salary_str:
            return None, None
            
        # Remove common currency symbols and text
        cleaned = salary_str.replace('$', '').replace(',', '').replace('USD', '').strip()
        
        # Try to extract salary range (e.g., "80000-120000", "80k-120k")
        if '-' in cleaned:
            parts = cleaned.split('-')
            if len(parts) == 2:
                try:
                    min_val = self._parse_salary_value(parts[0].strip())
                    max_val = self._parse_salary_value(parts[1].strip())
                    return min_val, max_val
                except ValueError:
                    pass
        
        # Try to extract single salary value
        try:
            single_val = self._parse_salary_value(cleaned)
            return single_val, single_val
        except ValueError:
            return None, None
    
    def _parse_salary_value(self, value_str: str) -> int:
        """Parse individual salary value, handling 'k' suffix"""
        value_str = value_str.lower().strip()
        
        if value_str.endswith('k'):
            return int(float(value_str[:-1]) * 1000)
        else:
            return int(float(value_str))
    
    def _extract_requirements(self, description: str, parsed_data_str: Optional[str]) -> Dict:
        """
        Extract job requirements from description and parsed data
        
        Args:
            description: Job description text
            parsed_data_str: JSON string of parsed job data
            
        Returns:
            Requirements dictionary
        """
        requirements = {
            'skills_required': [],
            'experience_level': 'mid',  # Default
            'employment_type': 'full_time',  # Default
            'remote_options': 'onsite'  # Default
        }
        
        # Parse structured data if available
        if parsed_data_str:
            try:
                parsed_data = json.loads(parsed_data_str)
                if isinstance(parsed_data, dict):
                    # Extract skills from parsed sections
                    skills = self._extract_skills_from_parsed_data(parsed_data)
                    requirements['skills_required'] = skills
                    
                    # Extract other requirements
                    requirements.update(self._extract_other_requirements(parsed_data))
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Fallback to description parsing if no structured data
        if not requirements['skills_required'] and description:
            requirements['skills_required'] = self._extract_skills_from_text(description)
        
        return requirements
    
    def _extract_skills_from_parsed_data(self, parsed_data: Dict) -> List[str]:
        """Extract skills from parsed job data structure"""
        skills = []
        
        # Look for skills in various sections
        if 'sections' in parsed_data:
            for section in parsed_data['sections']:
                if section.get('type') == 'list' and 'requirement' in section.get('title', '').lower():
                    content = section.get('content', [])
                    if isinstance(content, list):
                        skills.extend(self._extract_skills_from_list(content))
        
        return list(set(skills))  # Remove duplicates
    
    def _extract_skills_from_list(self, content_list: List[str]) -> List[str]:
        """Extract technical skills from a list of requirements"""
        skills = []
        
        # Common technical skills patterns
        skill_patterns = [
            'python', 'javascript', 'java', 'c++', 'c#', 'go', 'rust', 'php',
            'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask',
            'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
            'git', 'jenkins', 'ci/cd', 'agile', 'scrum'
        ]
        
        for item in content_list:
            if isinstance(item, str):
                item_lower = item.lower()
                for skill in skill_patterns:
                    if skill in item_lower:
                        skills.append(skill.title())
        
        return skills
    
    def _extract_skills_from_text(self, description: str) -> List[str]:
        """Extract skills from job description text using simple pattern matching"""
        skills = []
        
        # This is a simplified implementation
        # In production, you might want to use NLP libraries or ML models
        common_skills = [
            'Python', 'JavaScript', 'Java', 'C++', 'C#', 'Go', 'Rust', 'PHP',
            'React', 'Angular', 'Vue', 'Node.js', 'Express', 'Django', 'Flask',
            'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform',
            'Git', 'Jenkins', 'CI/CD', 'Agile', 'Scrum', 'Machine Learning',
            'Data Science', 'FastAPI', 'SQLAlchemy'
        ]
        
        description_lower = description.lower()
        for skill in common_skills:
            if skill.lower() in description_lower:
                skills.append(skill)
        
        return skills
    
    def _extract_other_requirements(self, parsed_data: Dict) -> Dict:
        """Extract other job requirements from parsed data"""
        requirements = {}
        
        # Try to determine experience level
        text_content = str(parsed_data).lower()
        if any(term in text_content for term in ['senior', 'lead', '5+ years', '7+ years']):
            requirements['experience_level'] = 'senior'
        elif any(term in text_content for term in ['junior', 'entry', '0-2 years', 'new grad']):
            requirements['experience_level'] = 'junior'
        else:
            requirements['experience_level'] = 'mid'
        
        # Try to determine remote options
        if any(term in text_content for term in ['remote', 'work from home', 'distributed']):
            requirements['remote_options'] = 'remote'
        elif any(term in text_content for term in ['hybrid', 'flexible']):
            requirements['remote_options'] = 'hybrid'
        else:
            requirements['remote_options'] = 'onsite'
        
        return requirements
    
    def _map_job_status(self, jt1_status: str) -> str:
        """
        Map Job_Tracker_1 status to unified status
        
        Args:
            jt1_status: Status from Job_Tracker_1
            
        Returns:
            Unified status string
        """
        status_mapping = {
            'Saved': 'not_applied',
            'Applied': 'applied',
            'Phone Interview': 'phone_screen',
            'Technical Interview': 'interview_scheduled',
            'Onsite Interview': 'interview_scheduled',
            'Offer': 'offer_received',
            'Rejected': 'rejected',
            'Withdrawn': 'withdrawn'
        }
        
        return status_mapping.get(jt1_status, 'not_applied')
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
            
        try:
            # Try different date formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S.%f']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None
    
    def _extract_tags(self, raw_job: Dict) -> List[str]:
        """Extract tags from job data"""
        tags = []
        
        # Add tags based on job type
        if job_type := raw_job.get('job_type'):
            tags.append(job_type.lower().replace(' ', '_'))
        
        # Add tags based on status
        if status := raw_job.get('status'):
            if status in ['Applied', 'Phone Interview', 'Technical Interview']:
                tags.append('active_application')
        
        # Add source tag
        tags.append('job_tracker_1')
        
        return tags
    
    def migrate_files(self, target_storage_path: str) -> List[Dict]:
        """
        Migrate file uploads from Job_Tracker_1 to unified storage
        
        Args:
            target_storage_path: Path to unified file storage directory
            
        Returns:
            List of migrated file information
        """
        migrated_files = []
        
        if not os.path.exists(self.uploads_path):
            logger.warning(f"Job_Tracker_1 uploads path not found: {self.uploads_path}")
            return migrated_files
        
        try:
            # Create target directories
            target_path = Path(target_storage_path)
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Migrate files from each subdirectory
            for subdir in ['cover_letters', 'other_docs']:
                source_dir = Path(self.uploads_path) / subdir
                if source_dir.exists():
                    target_subdir = target_path / 'job_tracker_1' / subdir
                    target_subdir.mkdir(parents=True, exist_ok=True)
                    
                    for file_path in source_dir.iterdir():
                        if file_path.is_file() and not file_path.name.startswith('.'):
                            try:
                                # Generate unique filename to avoid conflicts
                                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                new_filename = f"jt1_{timestamp}_{file_path.name}"
                                target_file = target_subdir / new_filename
                                
                                # Copy file
                                shutil.copy2(file_path, target_file)
                                
                                # Record migration info
                                file_info = {
                                    'original_path': str(file_path),
                                    'new_path': str(target_file.relative_to(target_path)),
                                    'filename': new_filename,
                                    'original_filename': file_path.name,
                                    'document_type': self._determine_document_type(file_path.name, subdir),
                                    'file_size': file_path.stat().st_size,
                                    'mime_type': self._get_mime_type(file_path.suffix),
                                    'source': 'job_tracker_1'
                                }
                                
                                migrated_files.append(file_info)
                                self.migration_stats['files_migrated'] += 1
                                
                                logger.info(f"Migrated file: {file_path.name} -> {new_filename}")
                                
                            except Exception as e:
                                error_msg = f"Error migrating file {file_path}: {str(e)}"
                                logger.error(error_msg)
                                self.migration_stats['errors'].append(error_msg)
        
        except Exception as e:
            error_msg = f"Error during file migration: {str(e)}"
            logger.error(error_msg)
            self.migration_stats['errors'].append(error_msg)
        
        return migrated_files
    
    def _determine_document_type(self, filename: str, subdir: str) -> str:
        """Determine document type based on filename and directory"""
        filename_lower = filename.lower()
        
        if subdir == 'cover_letters' or 'cover' in filename_lower:
            return 'cover_letter'
        elif 'resume' in filename_lower or 'cv' in filename_lower:
            return 'resume'
        elif 'portfolio' in filename_lower:
            return 'portfolio'
        else:
            return 'other'
    
    def _get_mime_type(self, file_extension: str) -> str:
        """Get MIME type based on file extension"""
        mime_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif'
        }
        
        return mime_types.get(file_extension.lower(), 'application/octet-stream')
    
    def get_migration_stats(self) -> Dict:
        """Get migration statistics"""
        return self.migration_stats.copy()


class JobTracker2Extractor:
    """Extract and migrate data from Job_tracker_2 (FastAPI/PostgreSQL) system"""
    
    def __init__(self, db_path: str, uploads_path: str):
        """
        Initialize the Job_tracker_2 extractor
        
        Args:
            db_path: Path to Job_tracker_2 SQLite database (contract_analyzer.db)
            uploads_path: Path to Job_tracker_2 uploads directory
        """
        self.db_path = db_path
        self.uploads_path = uploads_path
        self.migration_stats = {
            'users_extracted': 0,
            'contracts_extracted': 0,
            'analyses_extracted': 0,
            'files_migrated': 0,
            'errors': []
        }
    
    def extract_users(self) -> List[Dict]:
        """
        Extract user data from Job_tracker_2 database
        
        Returns:
            List of user dictionaries with normalized data
        """
        users = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Extract users with available fields (handle schema differences)
            cursor.execute("PRAGMA table_info(users)")
            columns_info = cursor.fetchall()
            available_columns = [col[1] for col in columns_info]
            
            # Build query with only available columns
            base_columns = ['id', 'username', 'email', 'hashed_password', 'is_active', 'created_at', 'updated_at']
            optional_columns = [
                'is_superuser', 'password_hash', 'roles', 'permissions', 'security_level',
                'mfa_enabled', 'mfa_secret', 'backup_codes', 'last_login', 'last_login_ip',
                'last_login_user_agent', 'failed_login_attempts', 'locked_until',
                'email_verified', 'email_verification_token', 'password_reset_token',
                'password_reset_expires', 'user_metadata', 'is_verified'
            ]
            
            # Select only columns that exist in the database
            select_columns = []
            for col in base_columns:
                if col in available_columns:
                    select_columns.append(col)
            
            for col in optional_columns:
                if col in available_columns:
                    select_columns.append(col)
            
            query = f"SELECT {', '.join(select_columns)} FROM users ORDER BY created_at DESC"
            cursor.execute(query)
            
            user_rows = cursor.fetchall()
            
            for row in user_rows:
                user_data = self._normalize_user_data(dict(row))
                
                # Extract user settings if table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
                if cursor.fetchone():
                    cursor.execute("PRAGMA table_info(user_settings)")
                    settings_columns = [col[1] for col in cursor.fetchall()]
                    
                    # Build settings query with available columns
                    available_settings_cols = [
                        'ai_model_preference', 'analysis_depth', 'email_notifications_enabled',
                        'slack_notifications_enabled', 'risk_threshold_low', 'risk_threshold_medium',
                        'risk_threshold_high', 'auto_generate_redlines', 'auto_generate_email_drafts',
                        'preferred_language', 'timezone', 'theme_preference', 'dashboard_layout',
                        'integration_settings'
                    ]
                    
                    existing_settings_cols = [col for col in available_settings_cols if col in settings_columns]
                    
                    if existing_settings_cols:
                        settings_query = f"SELECT {', '.join(existing_settings_cols)} FROM user_settings WHERE user_id = ?"
                        cursor.execute(settings_query, (row['id'],))
                
                settings_row = cursor.fetchone()
                if settings_row:
                    user_data['settings'] = dict(settings_row)
                
                users.append(user_data)
                self.migration_stats['users_extracted'] += 1
            
            conn.close()
            logger.info(f"Extracted {len(users)} users from Job_tracker_2")
            
        except Exception as e:
            error_msg = f"Error extracting users from Job_tracker_2: {str(e)}"
            logger.error(error_msg)
            self.migration_stats['errors'].append(error_msg)
            
        return users
    
    def extract_contract_analyses(self) -> List[Dict]:
        """
        Extract contract analysis data (treating as job applications) from Job_tracker_2
        
        Returns:
            List of contract analysis dictionaries normalized as job data
        """
        contracts = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Extract contract analyses with all fields
            cursor.execute("""
                SELECT 
                    id, user_id, filename, file_hash, file_size, contract_text,
                    analysis_status, risk_score, risky_clauses, suggested_redlines,
                    email_draft, processing_time_seconds, error_message,
                    workflow_state, ai_model_used, created_at, completed_at
                FROM contract_analyses
                ORDER BY created_at DESC
            """)
            
            contract_rows = cursor.fetchall()
            
            for row in contract_rows:
                contract_data = self._normalize_contract_as_job_data(dict(row))
                
                # Extract analysis history for this contract
                cursor.execute("""
                    SELECT analysis_type, status, risk_score, processing_time,
                           risk_level, risky_clauses_count, recommendations_count,
                           model_used, total_tokens, total_cost,
                           completed_agents, failed_agents, agent_count,
                           error_message, analysis_metadata,
                           created_at, completed_at
                    FROM analysis_history WHERE contract_id = ?
                    ORDER BY created_at DESC
                """, (row['id'],))
                
                analyses = cursor.fetchall()
                contract_data['analysis_history'] = [dict(analysis) for analysis in analyses]
                
                # Extract agent executions for detailed tracking
                cursor.execute("""
                    SELECT ae.agent_name, ae.agent_type, ae.status, ae.execution_time,
                           ae.token_usage, ae.cost, ae.llm_provider, ae.model_name,
                           ae.error_message, ae.error_type, ae.started_at, ae.completed_at
                    FROM agent_executions ae
                    JOIN analysis_history ah ON ae.analysis_id = ah.id
                    WHERE ah.contract_id = ?
                    ORDER BY ae.started_at DESC
                """, (row['id'],))
                
                executions = cursor.fetchall()
                contract_data['agent_executions'] = [dict(execution) for execution in executions]
                
                contracts.append(contract_data)
                self.migration_stats['contracts_extracted'] += 1
                self.migration_stats['analyses_extracted'] += len(analyses)
            
            conn.close()
            logger.info(f"Extracted {len(contracts)} contracts from Job_tracker_2")
            
        except Exception as e:
            error_msg = f"Error extracting contracts from Job_tracker_2: {str(e)}"
            logger.error(error_msg)
            self.migration_stats['errors'].append(error_msg)
            
        return contracts
    
    def _normalize_user_data(self, raw_user: Dict) -> Dict:
        """
        Normalize Job_tracker_2 user data to unified schema format
        
        Args:
            raw_user: Raw user data from Job_tracker_2 database
            
        Returns:
            Normalized user data dictionary
        """
        # Parse roles and permissions from JSON strings if they exist
        roles = self._parse_json_field(raw_user.get('roles', '[]'))
        permissions = self._parse_json_field(raw_user.get('permissions', '[]'))
        backup_codes = self._parse_json_field(raw_user.get('backup_codes', '[]'))
        
        # Handle user metadata if available
        user_metadata = self._parse_json_field(raw_user.get('user_metadata', '{}')) if raw_user.get('user_metadata') else {}
        
        # Create unified profile structure
        profile = {
            'skills': [],  # Will be populated from contract analysis data
            'experience_level': 'mid',  # Default, can be inferred from usage patterns
            'locations': [],  # Not available in Job_tracker_2, will be empty
            'preferences': {
                'salary_min': None,
                'company_size': [],
                'industries': ['legal', 'contract_analysis'],  # Inferred from usage
                'remote_preference': 'remote'  # Assume remote for contract analysis users
            },
            'career_goals': ['contract_analyst', 'legal_professional']  # Inferred
        }
        
        # Parse dates
        created_at = self._parse_date(raw_user.get('created_at'))
        updated_at = self._parse_date(raw_user.get('updated_at'))
        last_login = self._parse_date(raw_user.get('last_login'))
        
        return {
            'original_id': raw_user['id'],
            'email': raw_user.get('email', '').strip(),
            'username': raw_user.get('username', '').strip(),
            'password_hash': raw_user.get('password_hash') or raw_user.get('hashed_password'),
            'is_active': raw_user.get('is_active', True),
            'profile': profile,
            'settings': {},  # Will be populated separately if available
            'created_at': created_at,
            'updated_at': updated_at,
            'last_active': last_login or created_at,
            'migration_metadata': {
                'migrated_from': 'job_tracker_2',
                'original_roles': roles,
                'original_permissions': permissions,
                'security_level': raw_user.get('security_level'),
                'mfa_enabled': raw_user.get('mfa_enabled', False),
                'is_superuser': raw_user.get('is_superuser', False),
                'is_verified': raw_user.get('is_verified', False),
                'user_metadata': user_metadata
            }
        }
    
    def _normalize_contract_as_job_data(self, raw_contract: Dict) -> Dict:
        """
        Normalize Job_tracker_2 contract analysis data as job application data
        
        Args:
            raw_contract: Raw contract data from Job_tracker_2 database
            
        Returns:
            Normalized job data dictionary
        """
        # Extract company name from filename or contract text
        filename = raw_contract.get('filename', '')
        company_name = self._extract_company_from_filename(filename)
        
        # Parse risky clauses and suggestions
        risky_clauses = self._parse_json_field(raw_contract.get('risky_clauses', '[]'))
        suggested_redlines = self._parse_json_field(raw_contract.get('suggested_redlines', '[]'))
        workflow_state = self._parse_json_field(raw_contract.get('workflow_state', '{}'))
        
        # Map analysis status to job application status
        job_status = self._map_analysis_status_to_job_status(raw_contract.get('analysis_status', 'pending'))
        
        # Create job requirements based on contract analysis
        requirements = {
            'skills_required': ['contract_analysis', 'legal_review', 'risk_assessment'],
            'experience_level': self._infer_experience_level(raw_contract),
            'employment_type': 'contract',  # Assume contract work
            'remote_options': 'remote',  # Contract analysis is typically remote
            'contract_type': self._infer_contract_type(filename, risky_clauses)
        }
        
        # Parse dates
        created_at = self._parse_date(raw_contract.get('created_at'))
        completed_at = self._parse_date(raw_contract.get('completed_at'))
        
        # Create job description from contract analysis
        description = self._create_job_description_from_contract(
            raw_contract, risky_clauses, suggested_redlines
        )
        
        return {
            'original_id': raw_contract['id'],
            'user_id': raw_contract['user_id'],
            'title': f"Contract Analysis - {company_name}",
            'company': company_name,
            'location': 'Remote',  # Contract analysis is typically remote
            'description': description,
            'application_url': None,  # Not applicable for contract analysis
            'salary_min': None,  # Not applicable
            'salary_max': None,  # Not applicable
            'currency': 'USD',
            'requirements': requirements,
            'status': job_status,
            'source': 'contract_analysis',  # Custom source for Job_tracker_2 data
            'date_posted': created_at,
            'date_added': created_at,
            'date_applied': created_at,  # When analysis was started
            'tags': self._generate_contract_tags(raw_contract, risky_clauses),
            'contract_metadata': {
                'filename': filename,
                'file_hash': raw_contract.get('file_hash'),
                'file_size': raw_contract.get('file_size'),
                'risk_score': float(raw_contract.get('risk_score', 0)) if raw_contract.get('risk_score') else None,
                'risky_clauses': risky_clauses,
                'suggested_redlines': suggested_redlines,
                'email_draft': raw_contract.get('email_draft'),
                'processing_time_seconds': raw_contract.get('processing_time_seconds'),
                'ai_model_used': raw_contract.get('ai_model_used'),
                'workflow_state': workflow_state,
                'migrated_from': 'job_tracker_2'
            }
        }
    
    def _extract_company_from_filename(self, filename: str) -> str:
        """Extract company name from contract filename"""
        if not filename:
            return 'Unknown Company'
        
        # Remove file extension
        name_without_ext = filename.rsplit('.', 1)[0]
        
        # Common patterns in contract filenames
        # e.g., "acme_corp_contract.pdf", "Google_Employment_Agreement.pdf"
        name_parts = name_without_ext.replace('_', ' ').replace('-', ' ').split()
        
        # Look for company indicators
        company_indicators = ['corp', 'inc', 'llc', 'ltd', 'company', 'contract', 'agreement']
        
        # Filter out common contract terms
        contract_terms = ['contract', 'agreement', 'employment', 'service', 'nda', 'confidentiality']
        
        filtered_parts = []
        for part in name_parts:
            if part.lower() not in contract_terms:
                filtered_parts.append(part.title())
        
        if filtered_parts:
            # Take first 2-3 words as company name
            company_name = ' '.join(filtered_parts[:3])
        else:
            company_name = name_without_ext.replace('_', ' ').title()
        
        return company_name or 'Unknown Company'
    
    def _map_analysis_status_to_job_status(self, analysis_status: str) -> str:
        """Map Job_tracker_2 analysis status to unified job status"""
        status_mapping = {
            'pending': 'not_applied',
            'processing': 'applied',
            'completed': 'interviewed',  # Analysis completed = interview completed
            'failed': 'rejected',
            'error': 'rejected'
        }
        
        return status_mapping.get(analysis_status, 'not_applied')
    
    def _infer_experience_level(self, contract_data: Dict) -> str:
        """Infer experience level from contract complexity and processing time"""
        risk_score = contract_data.get('risk_score')
        processing_time = contract_data.get('processing_time_seconds')
        
        # Higher risk scores and longer processing times suggest more complex contracts
        # which might indicate senior-level work
        if risk_score and float(risk_score) > 0.7:
            return 'senior'
        elif processing_time and float(processing_time) > 300:  # 5 minutes
            return 'mid'
        else:
            return 'junior'
    
    def _infer_contract_type(self, filename: str, risky_clauses: List) -> str:
        """Infer contract type from filename and content"""
        filename_lower = filename.lower() if filename else ''
        
        if 'employment' in filename_lower or 'job' in filename_lower:
            return 'employment_agreement'
        elif 'nda' in filename_lower or 'confidentiality' in filename_lower:
            return 'nda'
        elif 'service' in filename_lower:
            return 'service_agreement'
        elif 'license' in filename_lower:
            return 'license_agreement'
        elif len(risky_clauses) > 5:  # Many risky clauses suggest complex contract
            return 'complex_commercial'
        else:
            return 'general_contract'
    
    def _create_job_description_from_contract(
        self, 
        contract_data: Dict, 
        risky_clauses: List, 
        suggested_redlines: List
    ) -> str:
        """Create a job description from contract analysis data"""
        filename = contract_data.get('filename', 'Unknown Contract')
        risk_score = contract_data.get('risk_score')
        ai_model = contract_data.get('ai_model_used', 'AI Analysis')
        
        description_parts = [
            f"Contract Analysis Project: {filename}",
            "",
            "Project Overview:",
            f"Analyzed legal contract using {ai_model} for risk assessment and compliance review.",
            ""
        ]
        
        if risk_score:
            risk_percentage = float(risk_score) * 100
            description_parts.extend([
                f"Risk Assessment: {risk_percentage:.1f}% risk score",
                ""
            ])
        
        if risky_clauses:
            description_parts.extend([
                "Key Risk Areas Identified:",
                *[f"• {clause.get('description', clause) if isinstance(clause, dict) else clause}" 
                  for clause in risky_clauses[:5]],  # Limit to top 5
                ""
            ])
        
        if suggested_redlines:
            description_parts.extend([
                "Recommendations Provided:",
                *[f"• {redline.get('suggestion', redline) if isinstance(redline, dict) else redline}" 
                  for redline in suggested_redlines[:3]],  # Limit to top 3
                ""
            ])
        
        description_parts.extend([
            "Skills Demonstrated:",
            "• Legal document analysis",
            "• Risk assessment and mitigation",
            "• Contract review and redlining",
            "• AI-assisted legal technology",
            "• Compliance evaluation"
        ])
        
        return "\n".join(description_parts)
    
    def _generate_contract_tags(self, contract_data: Dict, risky_clauses: List) -> List[str]:
        """Generate tags for contract analysis job"""
        tags = ['job_tracker_2', 'contract_analysis', 'legal_review']
        
        # Add risk level tag
        risk_score = contract_data.get('risk_score')
        if risk_score:
            risk_float = float(risk_score)
            if risk_float > 0.7:
                tags.append('high_risk')
            elif risk_float > 0.4:
                tags.append('medium_risk')
            else:
                tags.append('low_risk')
        
        # Add contract type tags
        filename = contract_data.get('filename', '').lower()
        if 'employment' in filename:
            tags.append('employment_contract')
        elif 'nda' in filename:
            tags.append('nda')
        elif 'service' in filename:
            tags.append('service_agreement')
        
        # Add AI model tag
        if ai_model := contract_data.get('ai_model_used'):
            tags.append(f"ai_{ai_model.lower().replace('-', '_')}")
        
        return tags
    
    def _parse_json_field(self, json_data) -> any:
        """Parse JSON field, handling both strings and objects"""
        if not json_data:
            return []
        
        # If it's already a dict or list, return as is
        if isinstance(json_data, (dict, list)):
            return json_data
        
        # If it's a string, try to parse it
        if isinstance(json_data, str):
            try:
                return json.loads(json_data)
            except (json.JSONDecodeError, TypeError):
                return []
        
        return []
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
            
        try:
            # Try different date formats
            for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None
    
    def migrate_files(self, target_storage_path: str) -> List[Dict]:
        """
        Migrate file uploads from Job_tracker_2 to unified storage
        
        Args:
            target_storage_path: Path to unified file storage directory
            
        Returns:
            List of migrated file information
        """
        migrated_files = []
        
        if not os.path.exists(self.uploads_path):
            logger.warning(f"Job_tracker_2 uploads path not found: {self.uploads_path}")
            return migrated_files
        
        try:
            # Create target directories
            target_path = Path(target_storage_path)
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Migrate files from uploads directory and subdirectories
            for root, dirs, files in os.walk(self.uploads_path):
                for file in files:
                    if file.startswith('.'):  # Skip hidden files
                        continue
                    
                    source_file = Path(root) / file
                    
                    try:
                        # Determine relative path from uploads root
                        rel_path = source_file.relative_to(Path(self.uploads_path))
                        
                        # Create target subdirectory structure
                        target_subdir = target_path / 'job_tracker_2' / rel_path.parent
                        target_subdir.mkdir(parents=True, exist_ok=True)
                        
                        # Generate unique filename to avoid conflicts
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        new_filename = f"jt2_{timestamp}_{file}"
                        target_file = target_subdir / new_filename
                        
                        # Copy file
                        shutil.copy2(source_file, target_file)
                        
                        # Record migration info
                        file_info = {
                            'original_path': str(source_file),
                            'new_path': str(target_file.relative_to(target_path)),
                            'filename': new_filename,
                            'original_filename': file,
                            'document_type': self._determine_document_type_jt2(file, str(rel_path)),
                            'file_size': source_file.stat().st_size,
                            'mime_type': self._get_mime_type(source_file.suffix),
                            'source': 'job_tracker_2',
                            'subdirectory': str(rel_path.parent) if rel_path.parent != Path('.') else ''
                        }
                        
                        migrated_files.append(file_info)
                        self.migration_stats['files_migrated'] += 1
                        
                        logger.info(f"Migrated file: {file} -> {new_filename}")
                        
                    except Exception as e:
                        error_msg = f"Error migrating file {source_file}: {str(e)}"
                        logger.error(error_msg)
                        self.migration_stats['errors'].append(error_msg)
        
        except Exception as e:
            error_msg = f"Error during Job_tracker_2 file migration: {str(e)}"
            logger.error(error_msg)
            self.migration_stats['errors'].append(error_msg)
        
        return migrated_files
    
    def _determine_document_type_jt2(self, filename: str, subdirectory: str) -> str:
        """Determine document type for Job_tracker_2 files"""
        filename_lower = filename.lower()
        subdir_lower = subdirectory.lower()
        
        # Job_tracker_2 is primarily for contract analysis
        if any(term in filename_lower for term in ['contract', 'agreement', 'legal']):
            return 'contract'
        elif any(term in filename_lower for term in ['analysis', 'report', 'review']):
            return 'analysis_report'
        elif 'email' in filename_lower or 'draft' in filename_lower:
            return 'email_draft'
        elif any(ext in filename_lower for ext in ['.pdf', '.doc', '.docx']):
            return 'legal_document'
        else:
            return 'other'
    
    def _get_mime_type(self, file_extension: str) -> str:
        """Get MIME type based on file extension"""
        mime_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif'
        }
        
        return mime_types.get(file_extension.lower(), 'application/octet-stream')
    
    def get_migration_stats(self) -> Dict:
        """Get migration statistics"""
        return self.migration_stats.copy()


class MigrationService:
    """Main migration service for consolidating job tracker data"""
    
    def __init__(self, db: Session):
        self.db = db
        self.migration_report = {
            'started_at': datetime.now(),
            'job_tracker_1': {
                'jobs_migrated': 0,
                'files_migrated': 0,
                'errors': []
            },
            'job_tracker_2': {
                'users_migrated': 0,
                'jobs_migrated': 0,
                'files_migrated': 0,
                'errors': []
            },
            'deduplication': {
                'duplicates_found': 0,
                'duplicates_merged': 0
            },
            'total_jobs': 0,
            'total_files': 0,
            'completed_at': None
        }
    
    def migrate_job_tracker_1(
        self, 
        db_path: str, 
        uploads_path: str, 
        target_storage_path: str,
        user_id: int = 1  # Default user for migration
    ) -> Dict:
        """
        Migrate data from Job_Tracker_1
        
        Args:
            db_path: Path to Job_Tracker_1 SQLite database
            uploads_path: Path to Job_Tracker_1 uploads directory
            target_storage_path: Path to unified file storage
            user_id: User ID to associate migrated data with
            
        Returns:
            Migration results dictionary
        """
        logger.info("Starting Job_Tracker_1 migration...")
        
        # Initialize extractor
        extractor = JobTracker1Extractor(db_path, uploads_path)
        
        # Extract jobs
        jobs_data = extractor.extract_jobs()
        
        # Migrate files
        migrated_files = extractor.migrate_files(target_storage_path)
        
        # Import jobs to unified database
        imported_jobs = self._import_jobs_to_unified_db(jobs_data, user_id)
        
        # Import documents to unified database
        imported_documents = self._import_documents_to_unified_db(migrated_files, user_id)
        
        # Update migration report
        stats = extractor.get_migration_stats()
        self.migration_report['job_tracker_1'].update({
            'jobs_migrated': len(imported_jobs),
            'files_migrated': len(imported_documents),
            'errors': stats['errors']
        })
        
        logger.info(f"Job_Tracker_1 migration completed: {len(imported_jobs)} jobs, {len(imported_documents)} files")
        
        return {
            'jobs': imported_jobs,
            'documents': imported_documents,
            'stats': stats
        }
    
    def _import_jobs_to_unified_db(self, jobs_data: List[Dict], user_id: int) -> List[Job]:
        """Import normalized job data to unified PostgreSQL database"""
        imported_jobs = []
        
        for job_data in jobs_data:
            try:
                # Create job record
                job = Job(
                    user_id=user_id,
                    title=job_data['title'],
                    company=job_data['company'],
                    location=job_data['location'],
                    description=job_data['description'],
                    application_url=job_data['application_url'],
                    salary_min=job_data['salary_min'],
                    salary_max=job_data['salary_max'],
                    currency=job_data['currency'],
                    requirements=job_data['requirements'],
                    status=job_data['status'],
                    source=job_data['source'],
                    date_posted=job_data['date_posted'],
                    date_added=job_data['date_added'],
                    date_applied=job_data['date_applied'],
                    tags=job_data['tags']
                )
                
                self.db.add(job)
                self.db.flush()  # Get the ID without committing
                
                # Create job application record if job was applied to
                if job_data['status'] != 'not_applied' and job_data['date_applied']:
    Application
                        job_id=job.id,
                        user_id=user_id,
                        status=job_data['status'],
                        applied_at=job_data['date_applied'],
                        notes=self._format_notes(job_data.get('notes', [])),
                        application_metadata={
                            'contacts': job_data.get('contacts', []),
                            'company_data': job_data.get('company_data'),
                            'company_reviews': job_data.get('company_reviews'),
                            'original_parsed_data': job_data.get('parsed_data'),
                            'migrated_from': 'job_tracker_1',
                            'original_id': job_data['original_id']
                        }
                    )
                    self.db.add(application)
                
                imported_jobs.append(job)
                
            except Exception as e:
                error_msg = f"Error importing job '{job_data.get('title', 'Unknown')}': {str(e)}"
                logger.error(error_msg)
                self.migration_report['job_tracker_1']['errors'].append(error_msg)
        
        try:
            self.db.commit()
            logger.info(f"Successfully imported {len(imported_jobs)} jobs from Job_Tracker_1")
        except Exception as e:
            self.db.rollback()
            error_msg = f"Error committing job imports: {str(e)}"
            logger.error(error_msg)
            self.migration_report['job_tracker_1']['errors'].append(error_msg)
            imported_jobs = []
        
        return imported_jobs
    
    def _import_documents_to_unified_db(self, files_data: List[Dict], user_id: int) -> List[Document]:
        """Import migrated files as document records"""
        imported_documents = []
        
        for file_data in files_data:
            try:
                document = Document(
                    user_id=user_id,
                    filename=file_data['filename'],
                    original_filename=file_data['original_filename'],
                    file_path=file_data['new_path'],
                    document_type=file_data['document_type'],
                    mime_type=file_data['mime_type'],
                    file_size=file_data['file_size'],
                    content_analysis={
                        'migrated_from': 'job_tracker_1',
                        'original_path': file_data['original_path']
                    },
                    tags=['job_tracker_1', file_data['document_type']],
                    description=f"Migrated from Job_Tracker_1: {file_data['original_filename']}"
                )
                
                self.db.add(document)
                imported_documents.append(document)
                
            except Exception as e:
                error_msg = f"Error importing document '{file_data.get('filename', 'Unknown')}': {str(e)}"
                logger.error(error_msg)
                self.migration_report['job_tracker_1']['errors'].append(error_msg)
        
        try:
            self.db.commit()
            logger.info(f"Successfully imported {len(imported_documents)} documents from Job_Tracker_1")
        except Exception as e:
            self.db.rollback()
            error_msg = f"Error committing document imports: {str(e)}"
            logger.error(error_msg)
            self.migration_report['job_tracker_1']['errors'].append(error_msg)
            imported_documents = []
        
        return imported_documents
    
    def _format_notes(self, notes_list: List[Dict]) -> str:
        """Format notes list into a single text field"""
        if not notes_list:
            return ""
        
        formatted_notes = []
        for note in notes_list:
            date_str = note.get('date_added', 'Unknown date')
            content = note.get('content', '')
            formatted_notes.append(f"[{date_str}] {content}")
        
        return "\n\n".join(formatted_notes)
    
    def migrate_job_tracker_2(
        self, 
        db_path: str, 
        uploads_path: str, 
        target_storage_path: str,
        create_default_user: bool = True
    ) -> Dict:
        """
        Migrate data from Job_tracker_2
        
        Args:
            db_path: Path to Job_tracker_2 SQLite database (contract_analyzer.db)
            uploads_path: Path to Job_tracker_2 uploads directory
            target_storage_path: Path to unified file storage
            create_default_user: Whether to create a default user if none exist
            
        Returns:
            Migration results dictionary
        """
        logger.info("Starting Job_tracker_2 migration...")
        
        # Initialize extractor
        extractor = JobTracker2Extractor(db_path, uploads_path)
        
        # Extract users first
        users_data = extractor.extract_users()
        
        # Extract contract analyses (as job data)
        contracts_data = extractor.extract_contract_analyses()
        
        # Migrate files
        migrated_files = extractor.migrate_files(target_storage_path)
        
        # Import users to unified database
        imported_users = self._import_users_to_unified_db(users_data, create_default_user)
        
        # Import contracts as jobs to unified database
        imported_jobs = self._import_contracts_as_jobs_to_unified_db(contracts_data, imported_users)
        
        # Import documents to unified database
        imported_documents = self._import_jt2_documents_to_unified_db(migrated_files, imported_users)
        
        # Update migration report
        stats = extractor.get_migration_stats()
        self.migration_report['job_tracker_2'].update({
            'users_migrated': len(imported_users),
            'jobs_migrated': len(imported_jobs),
            'files_migrated': len(imported_documents),
            'errors': stats['errors']
        })
        
        logger.info(f"Job_tracker_2 migration completed: {len(imported_users)} users, {len(imported_jobs)} jobs, {len(imported_documents)} files")
        
        return {
            'users': imported_users,
            'jobs': imported_jobs,
            'documents': imported_documents,
            'stats': stats
        }
    
    def _import_users_to_unified_db(self, users_data: List[Dict], create_default_user: bool) -> List[User]:
        """Import Job_tracker_2 users to unified PostgreSQL database"""
        imported_users = []
        
        # Create user ID mapping for later reference
        user_id_mapping = {}
        
        for user_data in users_data:
            try:
                # Check if user with same email already exists
                existing_user = self.db.query(User).filter(User.email == user_data['email']).first()
                
                if existing_user:
                    # Update existing user with Job_tracker_2 data
                    existing_user.profile.update(user_data['profile'])
                    existing_user.settings.update(user_data.get('settings', {}))
                    
                    # Add migration metadata
                    if 'migration_sources' not in existing_user.profile:
                        existing_user.profile['migration_sources'] = []
                    existing_user.profile['migration_sources'].append('job_tracker_2')
                    existing_user.profile['job_tracker_2_metadata'] = user_data['migration_metadata']
                    
                    user_id_mapping[user_data['original_id']] = existing_user.id
                    imported_users.append(existing_user)
                    
                    logger.info(f"Updated existing user: {user_data['email']}")
                    
                else:
                    # Create new user
                    user = User(
                        email=user_data['email'],
                        password_hash=user_data['password_hash'],
                        is_active=user_data['is_active'],
                        profile=user_data['profile'],
                        settings=user_data.get('settings', {}),
                        created_at=user_data['created_at'],
                        updated_at=user_data['updated_at'],
                        last_active=user_data['last_active']
                    )
                    
                    self.db.add(user)
                    self.db.flush()  # Get the ID without committing
                    
                    user_id_mapping[user_data['original_id']] = user.id
                    imported_users.append(user)
                    
                    logger.info(f"Created new user: {user_data['email']}")
                
            except Exception as e:
                error_msg = f"Error importing user '{user_data.get('email', 'Unknown')}': {str(e)}"
                logger.error(error_msg)
                self.migration_report['job_tracker_2']['errors'].append(error_msg)
        
        # Create default user if no users exist and requested
        if not imported_users and create_default_user:
            try:
                default_user = User(
                    email="admin@career-copilot.local",
                    password_hash="$2b$12$placeholder_hash_for_migration",  # Should be changed after migration
                    is_active=True,
                    profile={
                        'skills': ['contract_analysis', 'legal_review'],
                        'experience_level': 'mid',
                        'locations': ['Remote'],
                        'preferences': {
                            'industries': ['legal', 'contract_analysis'],
                            'remote_preference': 'remote'
                        }
                    },
                    settings={
                        'notifications': {
                            'morning_briefing': True,
                            'evening_summary': True
                        }
                    }
                )
                
                self.db.add(default_user)
                self.db.flush()
                
                # Map all Job_tracker_2 user IDs to this default user
                for user_data in users_data:
                    user_id_mapping[user_data['original_id']] = default_user.id
                
                imported_users.append(default_user)
                logger.info("Created default user for Job_tracker_2 migration")
                
            except Exception as e:
                error_msg = f"Error creating default user: {str(e)}"
                logger.error(error_msg)
                self.migration_report['job_tracker_2']['errors'].append(error_msg)
        
        # Store user ID mapping for use in job migration
        self._jt2_user_id_mapping = user_id_mapping
        
        try:
            self.db.commit()
            logger.info(f"Successfully imported {len(imported_users)} users from Job_tracker_2")
        except Exception as e:
            self.db.rollback()
            error_msg = f"Error committing user imports: {str(e)}"
            logger.error(error_msg)
            self.migration_report['job_tracker_2']['errors'].append(error_msg)
            imported_users = []
        
        return imported_users
    
    def _import_contracts_as_jobs_to_unified_db(self, contracts_data: List[Dict], imported_users: List[User]) -> List[Job]:
        """Import Job_tracker_2 contracts as jobs to unified PostgreSQL database"""
        imported_jobs = []
        
        for contract_data in contracts_data:
            try:
                # Map original user ID to new user ID
                original_user_id = contract_data['user_id']
                new_user_id = getattr(self, '_jt2_user_id_mapping', {}).get(original_user_id)
                
                if not new_user_id and imported_users:
                    # Fallback to first imported user
                    new_user_id = imported_users[0].id
                
                if not new_user_id:
                    logger.warning(f"No user mapping found for contract {contract_data['original_id']}, skipping")
                    continue
                
                # Create job record from contract data
                job = Job(
                    user_id=new_user_id,
                    title=contract_data['title'],
                    company=contract_data['company'],
                    location=contract_data['location'],
                    description=contract_data['description'],
                    application_url=contract_data['application_url'],
                    salary_min=contract_data['salary_min'],
                    salary_max=contract_data['salary_max'],
                    currency=contract_data['currency'],
                    requirements=contract_data['requirements'],
                    status=contract_data['status'],
                    source=contract_data['source'],
                    date_posted=contract_data['date_posted'],
                    date_added=contract_data['date_added'],
                    date_applied=contract_data['date_applied'],
                    tags=contract_data['tags']
                )
                
                self.db.add(job)
                self.db.flush()  # Get the ID without committing
                
                # Create job application record for contract analysis
                Application
                    job_id=job.id,
                    user_id=new_user_id,
                    status=contract_data['status'],
                    applied_at=contract_data['date_applied'],
                    notes=self._format_contract_analysis_notes(contract_data),
                    application_metadata={
                        'contract_analysis': contract_data['contract_metadata'],
                        'analysis_history': contract_data.get('analysis_history', []),
                        'agent_executions': contract_data.get('agent_executions', []),
                        'migrated_from': 'job_tracker_2',
                        'original_contract_id': contract_data['original_id']
                    }
                )
                self.db.add(application)
                
                imported_jobs.append(job)
                
            except Exception as e:
                error_msg = f"Error importing contract '{contract_data.get('title', 'Unknown')}': {str(e)}"
                logger.error(error_msg)
                self.migration_report['job_tracker_2']['errors'].append(error_msg)
        
        try:
            self.db.commit()
            logger.info(f"Successfully imported {len(imported_jobs)} contracts as jobs from Job_tracker_2")
        except Exception as e:
            self.db.rollback()
            error_msg = f"Error committing contract job imports: {str(e)}"
            logger.error(error_msg)
            self.migration_report['job_tracker_2']['errors'].append(error_msg)
            imported_jobs = []
        
        return imported_jobs
    
    def _import_jt2_documents_to_unified_db(self, files_data: List[Dict], imported_users: List[User]) -> List[Document]:
        """Import Job_tracker_2 migrated files as document records"""
        imported_documents = []
        
        # Use first imported user if available, otherwise skip
        if not imported_users:
            logger.warning("No users available for Job_tracker_2 document import")
            return imported_documents
        
        default_user_id = imported_users[0].id
        
        for file_data in files_data:
            try:
                document = Document(
                    user_id=default_user_id,
                    filename=file_data['filename'],
                    original_filename=file_data['original_filename'],
                    file_path=file_data['new_path'],
                    document_type=file_data['document_type'],
                    mime_type=file_data['mime_type'],
                    file_size=file_data['file_size'],
                    content_analysis={
                        'migrated_from': 'job_tracker_2',
                        'original_path': file_data['original_path'],
                        'subdirectory': file_data.get('subdirectory', ''),
                        'migration_notes': 'Migrated from Job_tracker_2 contract analysis system'
                    },
                    tags=['job_tracker_2', file_data['document_type'], 'contract_analysis'],
                    description=f"Migrated from Job_tracker_2: {file_data['original_filename']}"
                )
                
                self.db.add(document)
                imported_documents.append(document)
                
            except Exception as e:
                error_msg = f"Error importing document '{file_data.get('filename', 'Unknown')}': {str(e)}"
                logger.error(error_msg)
                self.migration_report['job_tracker_2']['errors'].append(error_msg)
        
        try:
            self.db.commit()
            logger.info(f"Successfully imported {len(imported_documents)} documents from Job_tracker_2")
        except Exception as e:
            self.db.rollback()
            error_msg = f"Error committing document imports: {str(e)}"
            logger.error(error_msg)
            self.migration_report['job_tracker_2']['errors'].append(error_msg)
            imported_documents = []
        
        return imported_documents
    
    def _format_contract_analysis_notes(self, contract_data: Dict) -> str:
        """Format contract analysis data into application notes"""
        notes_parts = []
        
        # Add basic contract info
        metadata = contract_data.get('contract_metadata', {})
        if filename := metadata.get('filename'):
            notes_parts.append(f"Contract File: {filename}")
        
        if risk_score := metadata.get('risk_score'):
            risk_percentage = risk_score * 100
            notes_parts.append(f"Risk Score: {risk_percentage:.1f}%")
        
        # Add risky clauses summary
        if risky_clauses := metadata.get('risky_clauses'):
            notes_parts.append(f"\nRisky Clauses Found: {len(risky_clauses)}")
            for i, clause in enumerate(risky_clauses[:3], 1):  # Top 3 clauses
                clause_text = clause.get('description', clause) if isinstance(clause, dict) else clause
                notes_parts.append(f"{i}. {clause_text}")
        
        # Add AI model info
        if ai_model := metadata.get('ai_model_used'):
            notes_parts.append(f"\nAnalysis Model: {ai_model}")
        
        # Add processing time
        if processing_time := metadata.get('processing_time_seconds'):
            notes_parts.append(f"Processing Time: {processing_time:.2f} seconds")
        
        # Add analysis history summary
        if analysis_history := contract_data.get('analysis_history'):
            notes_parts.append(f"\nAnalysis Runs: {len(analysis_history)}")
            for analysis in analysis_history[:2]:  # Latest 2 analyses
                status = analysis.get('status', 'unknown')
                created_at = analysis.get('created_at', 'unknown date')
                notes_parts.append(f"- {status} on {created_at}")
        
        return "\n".join(notes_parts) if notes_parts else "Contract analysis migrated from Job_tracker_2"

    def consolidate_and_deduplicate_jobs(self, user_id: Optional[int] = None) -> Dict:
        """
        Consolidate and deduplicate job data after migration
        
        Args:
            user_id: Optional user ID to limit deduplication scope
            
        Returns:
            Deduplication results dictionary
        """
        logger.info("Starting job consolidation and deduplication...")
        
        # Query jobs for deduplication
        query = self.db.query(Job)
        if user_id:
            query = query.filter(Job.user_id == user_id)
        
        all_jobs = query.order_by(Job.date_added.desc()).all()
        
        if len(all_jobs) < 2:
            logger.info("Less than 2 jobs found, no deduplication needed")
            return {
                'duplicates_found': 0,
                'duplicates_merged': 0,
                'conflicts_resolved': 0,
                'jobs_processed': len(all_jobs)
            }
        
        # Group jobs by potential duplicates
        duplicate_groups = self._identify_duplicate_jobs(all_jobs)
        
        # Resolve conflicts and merge duplicates
        merge_results = self._merge_duplicate_jobs(duplicate_groups)
        
        # Update migration report
        self.migration_report['deduplication'].update({
            'duplicates_found': merge_results['duplicates_found'],
            'duplicates_merged': merge_results['duplicates_merged']
        })
        
        logger.info(f"Deduplication completed: {merge_results['duplicates_found']} duplicates found, "
                   f"{merge_results['duplicates_merged']} merged")
        
        return merge_results
    
    def _identify_duplicate_jobs(self, jobs: List[Job]) -> List[List[Job]]:
        """
        Identify potential duplicate jobs based on company name and job title
        
        Args:
            jobs: List of Job objects to analyze
            
        Returns:
            List of duplicate groups, each group contains similar jobs
        """
        duplicate_groups = []
        processed_job_ids = set()
        
        for i, job in enumerate(jobs):
            if job.id in processed_job_ids:
                continue
            
            # Find similar jobs
            similar_jobs = [job]
            processed_job_ids.add(job.id)
            
            for j, other_job in enumerate(jobs[i+1:], i+1):
                if other_job.id in processed_job_ids:
                    continue
                
                if self._are_jobs_duplicates(job, other_job):
                    similar_jobs.append(other_job)
                    processed_job_ids.add(other_job.id)
            
            # Only add groups with more than one job
            if len(similar_jobs) > 1:
                duplicate_groups.append(similar_jobs)
        
        return duplicate_groups
    
    def _are_jobs_duplicates(self, job1: Job, job2: Job) -> bool:
        """
        Determine if two jobs are duplicates based on company name and job title
        
        Args:
            job1: First job to compare
            job2: Second job to compare
            
        Returns:
            True if jobs are considered duplicates
        """
        # Normalize company names for comparison
        company1 = self._normalize_company_name(job1.company)
        company2 = self._normalize_company_name(job2.company)
        
        # Normalize job titles for comparison
        title1 = self._normalize_job_title(job1.title)
        title2 = self._normalize_job_title(job2.title)
        
        # Check for exact matches
        if company1 == company2 and title1 == title2:
            return True
        
        # Check for fuzzy matches with high similarity
        company_similarity = self._calculate_string_similarity(company1, company2)
        title_similarity = self._calculate_string_similarity(title1, title2)
        
        # Consider duplicates if both company and title have high similarity
        return company_similarity >= 0.85 and title_similarity >= 0.80
    
    def _normalize_company_name(self, company_name: str) -> str:
        """
        Normalize company name for comparison
        
        Args:
            company_name: Raw company name
            
        Returns:
            Normalized company name
        """
        if not company_name:
            return ""
        
        # Convert to lowercase and strip whitespace
        normalized = company_name.lower().strip()
        
        # Remove common company suffixes
        suffixes = [
            'inc', 'inc.', 'incorporated', 'corp', 'corp.', 'corporation',
            'llc', 'l.l.c.', 'ltd', 'ltd.', 'limited', 'co', 'co.',
            'company', 'technologies', 'tech', 'systems', 'solutions'
        ]
        
        for suffix in suffixes:
            if normalized.endswith(f' {suffix}'):
                normalized = normalized[:-len(suffix)-1].strip()
        
        # Remove special characters and extra spaces
        import re
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _normalize_job_title(self, job_title: str) -> str:
        """
        Normalize job title for comparison
        
        Args:
            job_title: Raw job title
            
        Returns:
            Normalized job title
        """
        if not job_title:
            return ""
        
        # Convert to lowercase and strip whitespace
        normalized = job_title.lower().strip()
        
        # Remove common variations
        replacements = {
            'sr.': 'senior',
            'sr ': 'senior ',
            'jr.': 'junior',
            'jr ': 'junior ',
            'mgr': 'manager',
            'dev': 'developer',
            'eng': 'engineer',
            'sw': 'software',
            'swe': 'software engineer',
            'sde': 'software development engineer'
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        # Remove special characters and extra spaces
        import re
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings using Levenshtein distance
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not str1 or not str2:
            return 0.0
        
        if str1 == str2:
            return 1.0
        
        # Simple Levenshtein distance implementation
        def levenshtein_distance(s1: str, s2: str) -> int:
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            
            if len(s2) == 0:
                return len(s1)
            
            previous_row = list(range(len(s2) + 1))
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        max_len = max(len(str1), len(str2))
        distance = levenshtein_distance(str1, str2)
        similarity = 1.0 - (distance / max_len)
        
        return max(0.0, similarity)
    
    def _merge_duplicate_jobs(self, duplicate_groups: List[List[Job]]) -> Dict:
        """
        Merge duplicate jobs, resolving conflicts and preserving data
        
        Args:
            duplicate_groups: List of job groups to merge
            
        Returns:
            Merge results dictionary
        """
        duplicates_found = sum(len(group) - 1 for group in duplicate_groups)
        duplicates_merged = 0
        conflicts_resolved = 0
        
        for group in duplicate_groups:
            if len(group) < 2:
                continue
            
            try:
                # Select the primary job (most complete data)
                primary_job = self._select_primary_job(group)
                secondary_jobs = [job for job in group if job.id != primary_job.id]
                
                # Merge data from secondary jobs into primary
                merge_result = self._merge_job_data(primary_job, secondary_jobs)
                conflicts_resolved += merge_result['conflicts_resolved']
                
                # Update primary job in database
                self.db.merge(primary_job)
                
                # Handle applications and documents from secondary jobs
                self._merge_job_applications(primary_job, secondary_jobs)
                
                # Delete secondary jobs
                for secondary_job in secondary_jobs:
                    self.db.delete(secondary_job)
                    duplicates_merged += 1
                
                logger.info(f"Merged {len(secondary_jobs)} duplicate jobs into job ID {primary_job.id}")
                
            except Exception as e:
                error_msg = f"Error merging job group: {str(e)}"
                logger.error(error_msg)
                self.migration_report['deduplication'].setdefault('errors', []).append(error_msg)
        
        try:
            self.db.commit()
            logger.info(f"Successfully committed job deduplication changes")
        except Exception as e:
            self.db.rollback()
            error_msg = f"Error committing deduplication changes: {str(e)}"
            logger.error(error_msg)
            self.migration_report['deduplication'].setdefault('errors', []).append(error_msg)
            duplicates_merged = 0
        
        return {
            'duplicates_found': duplicates_found,
            'duplicates_merged': duplicates_merged,
            'conflicts_resolved': conflicts_resolved,
            'jobs_processed': sum(len(group) for group in duplicate_groups)
        }
    
    def _select_primary_job(self, jobs: List[Job]) -> Job:
        """
        Select the primary job from a group of duplicates
        
        Args:
            jobs: List of duplicate jobs
            
        Returns:
            The job selected as primary
        """
        # Score each job based on completeness and recency
        scored_jobs = []
        
        for job in jobs:
            score = 0
            
            # Prefer jobs with more complete data
            if job.description and len(job.description.strip()) > 100:
                score += 10
            if job.salary_min or job.salary_max:
                score += 5
            if job.application_url:
                score += 3
            if job.requirements and len(job.requirements) > 0:
                score += 5
            if job.tags and len(job.tags) > 0:
                score += 2
            
            # Prefer jobs that have been applied to
            if job.status != 'not_applied':
                score += 15
            
            # Prefer more recent jobs
            if job.date_added:
                days_old = (datetime.now() - job.date_added.replace(tzinfo=None)).days
                score += max(0, 30 - days_old)  # Bonus for recent jobs
            
            # Prefer manually added jobs over scraped ones
            if job.source == 'manual':
                score += 8
            elif job.source in ['scraped', 'api']:
                score += 3
            
            scored_jobs.append((job, score))
        
        # Return job with highest score
        scored_jobs.sort(key=lambda x: x[1], reverse=True)
        return scored_jobs[0][0]
    
    def _merge_job_data(self, primary_job: Job, secondary_jobs: List[Job]) -> Dict:
        """
        Merge data from secondary jobs into primary job
        
        Args:
            primary_job: The job to merge data into
            secondary_jobs: Jobs to merge data from
            
        Returns:
            Merge results with conflict information
        """
        conflicts_resolved = 0
        
        for secondary_job in secondary_jobs:
            # Merge description (take longer one)
            if secondary_job.description and len(secondary_job.description.strip()) > len(primary_job.description or ""):
                primary_job.description = secondary_job.description
                conflicts_resolved += 1
            
            # Merge salary information (take higher values)
            if secondary_job.salary_min and (not primary_job.salary_min or secondary_job.salary_min > primary_job.salary_min):
                primary_job.salary_min = secondary_job.salary_min
                conflicts_resolved += 1
            
            if secondary_job.salary_max and (not primary_job.salary_max or secondary_job.salary_max > primary_job.salary_max):
                primary_job.salary_max = secondary_job.salary_max
                conflicts_resolved += 1
            
            # Merge application URL (prefer non-empty)
            if secondary_job.application_url and not primary_job.application_url:
                primary_job.application_url = secondary_job.application_url
            
            # Merge requirements (combine unique skills)
            if secondary_job.requirements:
                primary_requirements = primary_job.requirements or {}
                secondary_requirements = secondary_job.requirements
                
                # Merge skills_required lists
                primary_skills = set(primary_requirements.get('skills_required', []))
                secondary_skills = set(secondary_requirements.get('skills_required', []))
                combined_skills = list(primary_skills.union(secondary_skills))
                
                if combined_skills != list(primary_skills):
                    primary_requirements['skills_required'] = combined_skills
                    conflicts_resolved += 1
                
                # Merge other requirement fields (prefer more specific values)
                for key, value in secondary_requirements.items():
                    if key != 'skills_required' and value and not primary_requirements.get(key):
                        primary_requirements[key] = value
                
                primary_job.requirements = primary_requirements
            
            # Merge tags (combine unique tags)
            if secondary_job.tags:
                primary_tags = set(primary_job.tags or [])
                secondary_tags = set(secondary_job.tags)
                combined_tags = list(primary_tags.union(secondary_tags))
                
                if combined_tags != list(primary_tags):
                    primary_job.tags = combined_tags
                    conflicts_resolved += 1
            
            # Update status to most advanced status
            status_priority = {
                'not_applied': 0,
                'applied': 1,
                'phone_screen': 2,
                'interview_scheduled': 3,
                'interviewed': 4,
                'offer_received': 5,
                'rejected': 6,
                'withdrawn': 7,
                'archived': 8
            }
            
            primary_priority = status_priority.get(primary_job.status, 0)
            secondary_priority = status_priority.get(secondary_job.status, 0)
            
            if secondary_priority > primary_priority:
                primary_job.status = secondary_job.status
                if secondary_job.date_applied:
                    primary_job.date_applied = secondary_job.date_applied
                conflicts_resolved += 1
            
            # Update dates (prefer earlier posted date, later applied date)
            if secondary_job.date_posted and (not primary_job.date_posted or secondary_job.date_posted < primary_job.date_posted):
                primary_job.date_posted = secondary_job.date_posted
            
            if secondary_job.date_applied and (not primary_job.date_applied or secondary_job.date_applied > primary_job.date_applied):
                primary_job.date_applied = secondary_job.date_applied
        
        return {'conflicts_resolved': conflicts_resolved}
    
    def _merge_job_applications(self, primary_job: Job, secondary_jobs: List[Job]):
        """
        Merge job applications from secondary jobs to primary job
        
        Args:
            primary_job: The job to merge applications into
            secondary_jobs: Jobs to merge applications from
        """
        for secondary_job in secondary_jobs:
            # Update applications to point to primary job
            applications = self.db.query(JobApplication).filter(JobApplication.job_id == secondary_job.id).all()
            
            for application in applications:
                # Check if primary job already has an application for this user
                existing_application = self.db.query(JobApplication).filter(
                    JobApplication.job_id == primary_job.id,
                    JobApplication.user_id == application.user_id
                ).first()
                
                if existing_application:
                    # Merge application data
                    if application.notes and not existing_application.notes:
                        existing_application.notes = application.notes
                    elif application.notes and existing_application.notes:
                        existing_application.notes += f"\n\n--- Merged from duplicate job ---\n{application.notes}"
                    
                    # Merge documents
                    existing_docs = existing_application.documents or []
                    new_docs = application.documents or []
                    combined_docs = existing_docs + new_docs
                    existing_application.documents = combined_docs
                    
                    # Merge metadata
                    existing_metadata = existing_application.application_metadata or {}
                    new_metadata = application.application_metadata or {}
                    existing_metadata.update(new_metadata)
                    existing_application.application_metadata = existing_metadata
                    
                    # Delete the duplicate application
                    self.db.delete(application)
                else:
                    # Move application to primary job
                    application.job_id = primary_job.id
    
    def generate_migration_validation_report(self) -> Dict:
        """
        Generate comprehensive migration validation report with statistics
        
        Returns:
            Detailed migration report with validation statistics
        """
        logger.info("Generating migration validation report...")
        
        # Basic migration statistics
        report = self.migration_report.copy()
        
        # Add validation statistics
        validation_stats = {
            'total_users': self.db.query(User).count(),
            'total_jobs': self.db.query(Job).count(),
            'total_applications': self.db.query(JobApplication).count(),
            'total_documents': self.db.query(Document).count(),
            
            'jobs_by_source': {},
            'jobs_by_status': {},
            'applications_by_status': {},
            'documents_by_type': {},
            
            'data_quality': {
                'jobs_with_description': 0,
                'jobs_with_salary': 0,
                'jobs_with_requirements': 0,
                'jobs_with_application_url': 0,
                'applications_with_notes': 0,
                'documents_with_analysis': 0
            }
        }
        
        # Analyze job sources
        from sqlalchemy import func
        job_sources = self.db.query(Job.source, func.count(Job.id)).group_by(Job.source).all()
        validation_stats['jobs_by_source'] = {source: count for source, count in job_sources}
        
        # Analyze job statuses
        job_statuses = self.db.query(Job.status, func.count(Job.id)).group_by(Job.status).all()
        validation_stats['jobs_by_status'] = {status: count for status, count in job_statuses}
        
        # Analyze application statuses
        app_statuses = self.db.query(JobApplication.status, func.count(JobApplication.id)).group_by(JobApplication.status).all()
        validation_stats['applications_by_status'] = {status: count for status, count in app_statuses}
        
        # Analyze document types
        doc_types = self.db.query(Document.document_type, func.count(Document.id)).group_by(Document.document_type).all()
        validation_stats['documents_by_type'] = {doc_type: count for doc_type, count in doc_types}
        
        # Analyze data quality
        validation_stats['data_quality']['jobs_with_description'] = self.db.query(Job).filter(Job.description.isnot(None), Job.description != '').count()
        validation_stats['data_quality']['jobs_with_salary'] = self.db.query(Job).filter(
            (Job.salary_min.isnot(None)) | (Job.salary_max.isnot(None))
        ).count()
        validation_stats['data_quality']['jobs_with_requirements'] = self.db.query(Job).filter(Job.requirements.isnot(None)).count()
        validation_stats['data_quality']['jobs_with_application_url'] = self.db.query(Job).filter(Job.application_url.isnot(None), Job.application_url != '').count()
        validation_stats['data_quality']['applications_with_notes'] = self.db.query(JobApplication).filter(JobApplication.notes.isnot(None), JobApplication.notes != '').count()
        validation_stats['data_quality']['documents_with_analysis'] = self.db.query(Document).filter(Document.content_analysis.isnot(None)).count()
        
        # Add validation stats to report
        report['validation_statistics'] = validation_stats
        
        # Calculate data quality percentages
        total_jobs = validation_stats['total_jobs']
        total_applications = validation_stats['total_applications']
        total_documents = validation_stats['total_documents']
        
        if total_jobs > 0:
            report['data_quality_percentages'] = {
                'jobs_with_description': round((validation_stats['data_quality']['jobs_with_description'] / total_jobs) * 100, 1),
                'jobs_with_salary': round((validation_stats['data_quality']['jobs_with_salary'] / total_jobs) * 100, 1),
                'jobs_with_requirements': round((validation_stats['data_quality']['jobs_with_requirements'] / total_jobs) * 100, 1),
                'jobs_with_application_url': round((validation_stats['data_quality']['jobs_with_application_url'] / total_jobs) * 100, 1)
            }
        
        if total_applications > 0:
            report['data_quality_percentages']['applications_with_notes'] = round((validation_stats['data_quality']['applications_with_notes'] / total_applications) * 100, 1)
        
        if total_documents > 0:
            report['data_quality_percentages']['documents_with_analysis'] = round((validation_stats['data_quality']['documents_with_analysis'] / total_documents) * 100, 1)
        
        logger.info("Migration validation report generated successfully")
        return report

    def generate_migration_report(self) -> Dict:
        """Generate final migration report"""
        self.migration_report['completed_at'] = datetime.now()
        self.migration_report['total_jobs'] = (
            self.migration_report['job_tracker_1']['jobs_migrated'] +
            self.migration_report['job_tracker_2']['jobs_migrated']
        )
        self.migration_report['total_files'] = (
            self.migration_report['job_tracker_1']['files_migrated'] +
            self.migration_report['job_tracker_2']['files_migrated']
        )
        
        return self.migration_report.copy()