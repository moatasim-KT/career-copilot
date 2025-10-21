"""
Document template system with dynamic content generation
"""

from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from jinja2 import Environment, BaseLoader, Template

from app.models.user import User
from app.models.job import Job
from app.models.document import Document


class DocumentTemplateService:
    """Service for managing document templates and dynamic generation"""
    
    def __init__(self):
        self.jinja_env = Environment(loader=BaseLoader())
    
    def get_resume_templates(self) -> Dict[str, str]:
        """Get available resume templates"""
        return {
            'professional': self._get_professional_resume_template(),
            'modern': self._get_modern_resume_template(),
            'technical': self._get_technical_resume_template()
        }
    
    def get_cover_letter_templates(self) -> Dict[str, str]:
        """Get available cover letter templates"""
        return {
            'standard': self._get_standard_cover_letter_template(),
            'enthusiastic': self._get_enthusiastic_cover_letter_template(),
            'technical': self._get_technical_cover_letter_template()
        }
    
    def _get_professional_resume_template(self) -> str:
        """Professional resume template"""
        return """
{{ name }}
{{ email }} | {{ phone }} | {{ location }}
{{ linkedin }} | {{ github }}

PROFESSIONAL SUMMARY
{{ summary }}

SKILLS
{% for category, skills in skills_by_category.items() %}
{{ category }}: {{ skills|join(', ') }}
{% endfor %}

EXPERIENCE
{% for exp in experience %}
{{ exp.title }} | {{ exp.company }}
{{ exp.start_date }} - {{ exp.end_date }}
{% for achievement in exp.achievements %}
• {{ achievement }}
{% endfor %}

{% endfor %}

EDUCATION
{% for edu in education %}
{{ edu.degree }} | {{ edu.institution }}
{{ edu.graduation_year }}
{% endfor %}
"""
    
    def _get_modern_resume_template(self) -> str:
        """Modern resume template with emphasis on achievements"""
        return """
{{ name.upper() }}
{{ email }} • {{ phone }} • {{ location }}

ABOUT
{{ summary }}

KEY SKILLS
{{ skills|join(' • ') }}

PROFESSIONAL EXPERIENCE
{% for exp in experience %}
{{ exp.title }} @ {{ exp.company }} ({{ exp.start_date }} - {{ exp.end_date }})
{% for achievement in exp.achievements %}
→ {{ achievement }}
{% endfor %}

{% endfor %}

EDUCATION & CERTIFICATIONS
{% for edu in education %}
{{ edu.degree }}, {{ edu.institution }} ({{ edu.graduation_year }})
{% endfor %}
"""
    
    def _get_technical_resume_template(self) -> str:
        """Technical resume template for engineering roles"""
        return """
{{ name }}
{{ email }} | {{ github }} | {{ portfolio }}

TECHNICAL SKILLS
{% for category, skills in skills_by_category.items() %}
{{ category }}: {{ skills|join(', ') }}
{% endfor %}

PROFESSIONAL EXPERIENCE
{% for exp in experience %}
{{ exp.title }} - {{ exp.company }}
{{ exp.start_date }} to {{ exp.end_date }}
{% for achievement in exp.achievements %}
• {{ achievement }}
{% endfor %}
Technologies: {{ exp.technologies|join(', ') }}

{% endfor %}

PROJECTS
{% for project in projects %}
{{ project.name }} - {{ project.description }}
Tech Stack: {{ project.tech_stack|join(', ') }}
{% endfor %}

EDUCATION
{% for edu in education %}
{{ edu.degree }}, {{ edu.institution }} ({{ edu.graduation_year }})
{% endfor %}
"""
    
    def _get_standard_cover_letter_template(self) -> str:
        """Standard cover letter template"""
        return """
{{ date }}

{{ hiring_manager_name }}
{{ company_name }}
{{ company_address }}

Dear {{ hiring_manager_name or 'Hiring Manager' }},

I am writing to express my interest in the {{ job_title }} position at {{ company_name }}. With {{ years_experience }} years of experience in {{ field }}, I am confident in my ability to contribute to your team.

{{ why_company }}

{{ relevant_experience }}

{{ key_achievements }}

I am particularly excited about this opportunity because {{ enthusiasm_reason }}. I believe my skills in {{ top_skills|join(', ') }} align well with your requirements.

Thank you for considering my application. I look forward to discussing how I can contribute to {{ company_name }}'s success.

Sincerely,
{{ name }}
"""
    
    def _get_enthusiastic_cover_letter_template(self) -> str:
        """Enthusiastic cover letter template"""
        return """
{{ date }}

Dear {{ hiring_manager_name or 'Hiring Team' }},

I'm thrilled to apply for the {{ job_title }} position at {{ company_name }}! {{ why_excited }}

{{ relevant_experience }}

What excites me most about {{ company_name }} is {{ company_appeal }}. I'm particularly drawn to {{ specific_aspect }}.

My experience with {{ top_skills|join(', ') }} has prepared me to make an immediate impact. {{ key_achievement }}

I'd love the opportunity to discuss how my passion and skills can contribute to your team's success.

Best regards,
{{ name }}
"""
    
    def _get_technical_cover_letter_template(self) -> str:
        """Technical cover letter template"""
        return """
{{ date }}

{{ hiring_manager_name }}
{{ company_name }}

Re: {{ job_title }} Position

Dear {{ hiring_manager_name or 'Hiring Manager' }},

I am applying for the {{ job_title }} role at {{ company_name }}. My {{ years_experience }} years of experience with {{ primary_tech_stack|join(', ') }} makes me a strong fit for this position.

Technical Highlights:
{% for highlight in technical_highlights %}
• {{ highlight }}
{% endfor %}

{{ relevant_project_experience }}

I am impressed by {{ company_name }}'s work on {{ company_projects }}, and I'm excited about the opportunity to contribute to {{ specific_initiative }}.

I look forward to discussing how my technical expertise can benefit your team.

Best regards,
{{ name }}
"""
    
    def generate_resume(self, db: Session, user_id: int, template_name: str = 'professional') -> str:
        """Generate resume from template using user profile data"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return ""
        
        profile = user.profile or {}
        templates = self.get_resume_templates()
        template_str = templates.get(template_name, templates['professional'])
        
        # Prepare context from user profile
        context = {
            'name': profile.get('name', user.email.split('@')[0]),
            'email': user.email,
            'phone': profile.get('phone', ''),
            'location': profile.get('location', ''),
            'linkedin': profile.get('linkedin', ''),
            'github': profile.get('github', ''),
            'portfolio': profile.get('portfolio', ''),
            'summary': profile.get('summary', ''),
            'skills': profile.get('skills', []),
            'skills_by_category': self._categorize_skills(profile.get('skills', [])),
            'experience': profile.get('experience', []),
            'education': profile.get('education', []),
            'projects': profile.get('projects', [])
        }
        
        template = self.jinja_env.from_string(template_str)
        return template.render(**context)
    
    def generate_cover_letter(
        self, 
        db: Session, 
        user_id: int, 
        job_id: int, 
        template_name: str = 'standard'
    ) -> str:
        """Generate cover letter from template tailored to specific job"""
        user = db.query(User).filter(User.id == user_id).first()
        job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
        
        if not user or not job:
            return ""
        
        profile = user.profile or {}
        templates = self.get_cover_letter_templates()
        template_str = templates.get(template_name, templates['standard'])
        
        # Extract job requirements
        requirements = job.requirements or {}
        required_skills = requirements.get('skills_required', [])
        
        # Prepare context
        context = {
            'date': datetime.now().strftime('%B %d, %Y'),
            'name': profile.get('name', user.email.split('@')[0]),
            'hiring_manager_name': '',
            'company_name': job.company,
            'company_address': job.location or '',
            'job_title': job.title,
            'years_experience': self._calculate_years_experience(profile.get('experience', [])),
            'field': self._infer_field(profile.get('skills', [])),
            'top_skills': profile.get('skills', [])[:5],
            'primary_tech_stack': required_skills[:5],
            'why_company': self._generate_why_company(job),
            'why_excited': self._generate_enthusiasm(job),
            'company_appeal': self._generate_company_appeal(job),
            'specific_aspect': requirements.get('industry', 'your innovative approach'),
            'relevant_experience': self._generate_relevant_experience(profile, job),
            'key_achievements': self._generate_key_achievements(profile),
            'key_achievement': self._generate_key_achievements(profile),
            'enthusiasm_reason': self._generate_enthusiasm_reason(job),
            'technical_highlights': self._generate_technical_highlights(profile, required_skills),
            'relevant_project_experience': self._generate_project_experience(profile, required_skills),
            'company_projects': requirements.get('company_focus', 'innovative solutions'),
            'specific_initiative': requirements.get('team_focus', 'upcoming projects')
        }
        
        template = self.jinja_env.from_string(template_str)
        return template.render(**context)
    
    def _categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """Categorize skills into groups"""
        categories = {
            'Languages': [],
            'Frameworks': [],
            'Tools': [],
            'Other': []
        }
        
        languages = {'python', 'javascript', 'java', 'typescript', 'go', 'rust', 'c++', 'c#'}
        frameworks = {'react', 'vue', 'angular', 'django', 'flask', 'fastapi', 'express', 'spring'}
        tools = {'docker', 'kubernetes', 'git', 'jenkins', 'aws', 'azure', 'gcp'}
        
        for skill in skills:
            skill_lower = skill.lower()
            if skill_lower in languages:
                categories['Languages'].append(skill)
            elif skill_lower in frameworks:
                categories['Frameworks'].append(skill)
            elif skill_lower in tools:
                categories['Tools'].append(skill)
            else:
                categories['Other'].append(skill)
        
        return {k: v for k, v in categories.items() if v}
    
    def _calculate_years_experience(self, experience: List[Dict]) -> int:
        """Calculate total years of experience"""
        if not experience:
            return 0
        return len(experience)  # Simplified calculation
    
    def _infer_field(self, skills: List[str]) -> str:
        """Infer professional field from skills"""
        skills_lower = [s.lower() for s in skills]
        if any(s in skills_lower for s in ['python', 'java', 'javascript']):
            return 'software development'
        return 'technology'
    
    def _generate_why_company(self, job: Job) -> str:
        """Generate why interested in company"""
        return f"I am impressed by {job.company}'s reputation in the industry and commitment to innovation."
    
    def _generate_enthusiasm(self, job: Job) -> str:
        """Generate enthusiasm statement"""
        return f"Your company's work in {job.requirements.get('industry', 'the field')} aligns perfectly with my career goals."
    
    def _generate_company_appeal(self, job: Job) -> str:
        """Generate company appeal statement"""
        return f"your innovative approach and strong team culture"
    
    def _generate_relevant_experience(self, profile: Dict, job: Job) -> str:
        """Generate relevant experience paragraph"""
        experience = profile.get('experience', [])
        if experience:
            latest = experience[0]
            return f"In my recent role as {latest.get('title', 'professional')}, I successfully {latest.get('achievements', ['delivered results'])[0]}."
        return "My professional experience has equipped me with the skills needed for this role."
    
    def _generate_key_achievements(self, profile: Dict) -> str:
        """Generate key achievements statement"""
        experience = profile.get('experience', [])
        if experience and experience[0].get('achievements'):
            return experience[0]['achievements'][0]
        return "I have consistently delivered high-quality results in my previous roles."
    
    def _generate_enthusiasm_reason(self, job: Job) -> str:
        """Generate enthusiasm reason"""
        return f"it aligns with my passion for {job.requirements.get('industry', 'technology')} and career growth"
    
    def _generate_technical_highlights(self, profile: Dict, required_skills: List[str]) -> List[str]:
        """Generate technical highlights"""
        user_skills = set(s.lower() for s in profile.get('skills', []))
        matching_skills = [s for s in required_skills if s.lower() in user_skills]
        
        highlights = []
        for skill in matching_skills[:3]:
            highlights.append(f"Proficient in {skill} with hands-on project experience")
        
        return highlights or ["Strong technical background with relevant experience"]
    
    def _generate_project_experience(self, profile: Dict, required_skills: List[str]) -> str:
        """Generate project experience paragraph"""
        projects = profile.get('projects', [])
        if projects:
            project = projects[0]
            return f"I recently worked on {project.get('name', 'a project')} where I {project.get('description', 'applied my technical skills')}."
        return "My project experience demonstrates my ability to deliver technical solutions."
    
    def save_generated_document(
        self, 
        db: Session, 
        user_id: int, 
        content: str, 
        document_type: str,
        filename: str
    ) -> Document:
        """Save generated document content"""
        from pathlib import Path
        import uuid
        from app.core.config import settings
        
        # Create document file
        upload_dir = Path(settings.UPLOAD_DIR)
        user_dir = upload_dir / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        
        unique_filename = f"{uuid.uuid4()}.txt"
        file_path = user_dir / unique_filename
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        # Create document record
        document = Document(
            user_id=user_id,
            filename=unique_filename,
            original_filename=filename,
            file_path=str(file_path.relative_to(upload_dir)),
            document_type=document_type,
            mime_type='text/plain',
            file_size=len(content.encode('utf-8')),
            version=1,
            is_current_version="true",
            usage_count=0,
            content_analysis={'generated': True, 'template_based': True}
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return document


document_template_service = DocumentTemplateService()