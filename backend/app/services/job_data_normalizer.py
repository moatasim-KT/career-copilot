from typing import Dict, List, Optional, Any
from app.schemas.job import JobCreate
from app.core.logging import get_logger
import re

logger = get_logger(__name__)

class JobDataNormalizer:
    """Normalizes job data from different sources into a unified schema"""
    
    def __init__(self):
        self.location_patterns = {
            'remote': ['remote', 'work from home', 'wfh', 'telecommute', 'distributed'],
            'hybrid': ['hybrid', 'flexible', 'part remote'],
            'onsite': ['on-site', 'onsite', 'office', 'in-person']
        }
        
        self.job_type_patterns = {
            'full-time': ['full-time', 'full time', 'permanent', 'regular'],
            'part-time': ['part-time', 'part time', 'parttime'],
            'contract': ['contract', 'contractor', 'freelance', 'consulting'],
            'temporary': ['temporary', 'temp', 'seasonal'],
            'internship': ['internship', 'intern', 'co-op', 'coop'],
            'volunteer': ['volunteer', 'unpaid']
        }
        
        self.tech_keywords = {
            # Programming Languages
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 
            'php', 'ruby', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl',
            
            # Web Technologies
            'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask', 
            'spring', 'laravel', 'rails', 'asp.net', 'blazor',
            
            # Databases
            'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'cassandra', 
            'dynamodb', 'oracle', 'sql server', 'sqlite', 'neo4j',
            
            # Cloud Platforms
            'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 
            'terraform', 'ansible', 'jenkins', 'gitlab ci', 'github actions',
            
            # Data & Analytics
            'pandas', 'numpy', 'tensorflow', 'pytorch', 'spark', 'hadoop', 
            'kafka', 'airflow', 'dbt', 'snowflake', 'databricks',
            
            # DevOps & Tools
            'git', 'jenkins', 'gitlab', 'github', 'jira', 'confluence', 
            'slack', 'teams', 'figma', 'sketch'
        }

    def normalize_job_data(self, job_data: Dict[str, Any], source: str) -> JobCreate:
        """Normalize job data from any source into unified JobCreate schema"""
        try:
            normalized_data = {
                'company': self._normalize_company(job_data.get('company', '')),
                'title': self._normalize_title(job_data.get('title', '')),
                'location': self._normalize_location(job_data.get('location', '')),
                'description': self._normalize_description(job_data.get('description', '')),
                'salary_range': self._normalize_salary(job_data.get('salary_range')),
                'job_type': self._normalize_job_type(job_data.get('job_type', ''), job_data.get('description', '')),
                'remote_option': self._normalize_remote_option(job_data.get('remote_option', ''), job_data.get('description', '')),
                'tech_stack': self._normalize_tech_stack(job_data.get('tech_stack', []), job_data.get('description', '')),
                'requirements': job_data.get('requirements', ''),
                'responsibilities': job_data.get('responsibilities', ''),
                'link': self._normalize_url(job_data.get('link', '')),
                'source': source
            }
            
            return JobCreate(**normalized_data)
        except Exception as e:
            logger.error(f"Error normalizing job data from {source}: {e}")
            # Return minimal valid job data
            return JobCreate(
                company=job_data.get('company', 'Unknown Company'),
                title=job_data.get('title', 'Unknown Position'),
                source=source
            )

    def _normalize_company(self, company: str) -> str:
        """Normalize company name"""
        if not company:
            return "Unknown Company"
        
        # Remove common suffixes and clean up
        company = company.strip()
        company = re.sub(r'\s+(Inc\.?|LLC|Ltd\.?|Corp\.?|Corporation|Company)$', '', company, flags=re.IGNORECASE)
        
        return company.strip() or "Unknown Company"

    def _normalize_title(self, title: str) -> str:
        """Normalize job title"""
        if not title:
            return "Unknown Position"
        
        # Clean up HTML tags and extra whitespace
        title = re.sub(r'<[^>]+>', '', title)
        title = re.sub(r'\s+', ' ', title)
        
        return title.strip() or "Unknown Position"

    def _normalize_location(self, location: str) -> str:
        """Normalize location string"""
        if not location:
            return "Unknown Location"
        
        # Clean up and standardize location format
        location = location.strip()
        location = re.sub(r'\s+', ' ', location)
        
        # Handle common location patterns
        if any(pattern in location.lower() for pattern in self.location_patterns['remote']):
            return "Remote"
        
        return location or "Unknown Location"

    def _normalize_description(self, description: str) -> str:
        """Normalize job description"""
        if not description:
            return ""
        
        # Remove HTML tags
        description = re.sub(r'<[^>]+>', '', description)
        # Clean up extra whitespace
        description = re.sub(r'\s+', ' ', description)
        # Remove excessive newlines
        description = re.sub(r'\n\s*\n', '\n\n', description)
        
        return description.strip()

    def _normalize_salary(self, salary: Any) -> Optional[str]:
        """Normalize salary information"""
        if not salary:
            return None
        
        if isinstance(salary, (int, float)):
            return f"${salary:,}"
        
        if isinstance(salary, str):
            # Clean up salary string
            salary = salary.strip()
            if salary and salary.lower() not in ['not specified', 'n/a', 'unknown']:
                return salary
        
        return None

    def _normalize_job_type(self, job_type: str, description: str) -> str:
        """Normalize job type"""
        if job_type:
            job_type_lower = job_type.lower()
            for normalized_type, patterns in self.job_type_patterns.items():
                if any(pattern in job_type_lower for pattern in patterns):
                    return normalized_type
        
        # Try to infer from description
        if description:
            description_lower = description.lower()
            for normalized_type, patterns in self.job_type_patterns.items():
                if any(pattern in description_lower for pattern in patterns):
                    return normalized_type
        
        return "full-time"  # Default

    def _normalize_remote_option(self, remote_option: str, description: str) -> str:
        """Normalize remote work option"""
        if remote_option:
            remote_lower = remote_option.lower()
            for option, patterns in self.location_patterns.items():
                if any(pattern in remote_lower for pattern in patterns):
                    return option
        
        # Try to infer from description
        if description:
            description_lower = description.lower()
            for option, patterns in self.location_patterns.items():
                if any(pattern in description_lower for pattern in patterns):
                    return option
        
        return "onsite"  # Default

    def _normalize_tech_stack(self, tech_stack: List[str], description: str) -> List[str]:
        """Normalize and enhance tech stack"""
        normalized_stack = set()
        
        # Add existing tech stack items
        if tech_stack:
            for tech in tech_stack:
                if tech and tech.strip():
                    normalized_stack.add(tech.strip().title())
        
        # Extract additional technologies from description
        if description:
            extracted_tech = self._extract_technologies_from_text(description)
            normalized_stack.update(extracted_tech)
        
        return sorted(list(normalized_stack))

    def _extract_technologies_from_text(self, text: str) -> List[str]:
        """Extract technology keywords from text"""
        if not text:
            return []
        
        text_lower = text.lower()
        found_tech = []
        
        for tech in self.tech_keywords:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(tech.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_tech.append(tech.title())
        
        return found_tech

    def _normalize_url(self, url: str) -> Optional[str]:
        """Normalize URL"""
        if not url:
            return None
        
        url = url.strip()
        if url and not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url if url.startswith(('http://', 'https://')) else None

    def merge_duplicate_jobs(self, jobs: List[JobCreate]) -> List[JobCreate]:
        """Merge duplicate jobs from different sources"""
        if not jobs:
            return []
        
        # Group jobs by company and title
        job_groups = {}
        for job in jobs:
            key = f"{job.company.lower().strip()}|{job.title.lower().strip()}"
            if key not in job_groups:
                job_groups[key] = []
            job_groups[key].append(job)
        
        merged_jobs = []
        for job_list in job_groups.values():
            if len(job_list) == 1:
                merged_jobs.append(job_list[0])
            else:
                merged_job = self._merge_job_list(job_list)
                merged_jobs.append(merged_job)
        
        return merged_jobs

    def _merge_job_list(self, jobs: List[JobCreate]) -> JobCreate:
        """Merge multiple job postings of the same position"""
        if not jobs:
            raise ValueError("Cannot merge empty job list")
        
        if len(jobs) == 1:
            return jobs[0]
        
        # Use source priority to determine base job
        source_priority = {
            'linkedin': 5, 'glassdoor': 4, 'indeed': 3, 'adzuna': 2,
            'usajobs': 2, 'github_jobs': 1, 'remoteok': 1, 'manual': 5
        }
        
        base_job = max(jobs, key=lambda j: source_priority.get(j.source, 0))
        
        # Merge data from all jobs
        merged_data = base_job.model_dump()
        
        # Combine tech stacks
        all_tech = set(base_job.tech_stack or [])
        for job in jobs:
            if job.tech_stack:
                all_tech.update(job.tech_stack)
        merged_data['tech_stack'] = sorted(list(all_tech))
        
        # Use the most complete description
        descriptions = [job.description for job in jobs if job.description]
        if descriptions:
            merged_data['description'] = max(descriptions, key=len)
        
        # Use salary if any job has it
        salaries = [job.salary_range for job in jobs if job.salary_range]
        if salaries:
            merged_data['salary_range'] = salaries[0]
        
        # Combine sources
        sources = [job.source for job in jobs]
        merged_data['source'] = ','.join(sorted(set(sources)))
        
        return JobCreate(**merged_data)

    def validate_job_data_quality(self, job: JobCreate) -> Dict[str, Any]:
        """Validate and score job data quality"""
        quality_score = 0
        max_score = 10
        issues = []
        
        # Check required fields
        if job.company and job.company != "Unknown Company":
            quality_score += 2
        else:
            issues.append("Missing or invalid company name")
        
        if job.title and job.title != "Unknown Position":
            quality_score += 2
        else:
            issues.append("Missing or invalid job title")
        
        # Check optional but important fields
        if job.location and job.location != "Unknown Location":
            quality_score += 1
        else:
            issues.append("Missing location information")
        
        if job.description and len(job.description) > 50:
            quality_score += 2
        else:
            issues.append("Missing or insufficient job description")
        
        if job.tech_stack and len(job.tech_stack) > 0:
            quality_score += 1
        else:
            issues.append("No technology stack information")
        
        if job.salary_range:
            quality_score += 1
        else:
            issues.append("No salary information")
        
        if job.link:
            quality_score += 1
        else:
            issues.append("No job posting URL")
        
        quality_percentage = (quality_score / max_score) * 100
        
        return {
            'quality_score': quality_score,
            'max_score': max_score,
            'quality_percentage': quality_percentage,
            'quality_grade': self._get_quality_grade(quality_percentage),
            'issues': issues
        }

    def _get_quality_grade(self, percentage: float) -> str:
        """Get quality grade based on percentage"""
        if percentage >= 90:
            return "Excellent"
        elif percentage >= 80:
            return "Good"
        elif percentage >= 70:
            return "Fair"
        elif percentage >= 60:
            return "Poor"
        else:
            return "Very Poor"