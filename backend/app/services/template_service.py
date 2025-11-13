"""
Document template service for Career Co-Pilot system
"""

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.models.job import Job
from app.models.template import DocumentTemplate, GeneratedDocument
from app.models.user import User
from app.schemas.template import (
	TEMPLATE_TYPES,
	DocumentTemplateCreate,
	DocumentTemplateUpdate,
	JobTailoredContent,
	TemplateAnalysis,
	TemplateGenerationRequest,
	TemplateSearchFilters,
	TemplateUsageStats,
)
from fastapi import HTTPException
from jinja2 import BaseLoader, Environment, select_autoescape
from jinja2.sandbox import SandboxedEnvironment
from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session


class TemplateService:
	"""Service for managing document templates and generation"""

	def __init__(self, db: Session):
		self.db = db
		self.templates_dir = Path(settings.UPLOAD_DIR) / "templates"
		self.generated_dir = Path(settings.UPLOAD_DIR) / "generated"
		self.templates_dir.mkdir(parents=True, exist_ok=True)
		self.generated_dir.mkdir(parents=True, exist_ok=True)

		# Initialize Jinja2 sandboxed environment for secure template rendering
		# Using SandboxedEnvironment to prevent code injection attacks
		self.jinja_env = SandboxedEnvironment(
			loader=BaseLoader(), autoescape=select_autoescape(enabled_extensions=("html", "xml"), default_for_string=True)
		)

	def create_template(self, user_id: Optional[int], template_data: DocumentTemplateCreate) -> DocumentTemplate:
		"""Create a new document template"""

		# Validate template type
		if template_data.template_type not in TEMPLATE_TYPES:
			raise HTTPException(status_code=400, detail=f"Invalid template type. Must be one of: {TEMPLATE_TYPES}")

		# Create template record
		template = DocumentTemplate(
			user_id=user_id,
			name=template_data.name,
			description=template_data.description,
			template_type=template_data.template_type,
			template_structure=template_data.template_structure.dict(),
			template_content=template_data.template_content,
			template_styles=template_data.template_styles,
			is_system_template=template_data.is_system_template,
			category=template_data.category,
			tags=template_data.tags,
			version="1.0",
			usage_count=0,
			is_active=True,
		)

		self.db.add(template)
		self.db.commit()
		self.db.refresh(template)

		return template

	def get_template(self, template_id: int, user_id: Optional[int] = None) -> Optional[DocumentTemplate]:
		"""Get a template by ID"""
		query = self.db.query(DocumentTemplate).filter(DocumentTemplate.id == template_id)

		# If user_id provided, ensure user can access template (own template or system template)
		if user_id is not None:
			query = query.filter(or_(DocumentTemplate.user_id == user_id, DocumentTemplate.is_system_template == True))

		return query.first()

	def get_templates(
		self, user_id: Optional[int] = None, filters: Optional[TemplateSearchFilters] = None, page: int = 1, per_page: int = 20
	) -> Tuple[List[DocumentTemplate], int]:
		"""Get templates with optional filtering"""

		query = self.db.query(DocumentTemplate).filter(DocumentTemplate.is_active == True)

		# Filter by user access (own templates + system templates)
		if user_id is not None:
			query = query.filter(or_(DocumentTemplate.user_id == user_id, DocumentTemplate.is_system_template == True))

		# Apply filters
		if filters:
			if filters.template_type:
				query = query.filter(DocumentTemplate.template_type == filters.template_type)

			if filters.category:
				query = query.filter(DocumentTemplate.category == filters.category)

			if filters.is_system_template is not None:
				query = query.filter(DocumentTemplate.is_system_template == filters.is_system_template)

			if filters.tags:
				# Filter templates that have any of the specified tags
				for tag in filters.tags:
					query = query.filter(DocumentTemplate.tags.contains([tag]))

			if filters.search_text:
				# Search in name and description
				search_term = f"%{filters.search_text}%"
				query = query.filter(or_(DocumentTemplate.name.ilike(search_term), DocumentTemplate.description.ilike(search_term)))

		# Get total count
		total = query.count()

		# Apply pagination and ordering
		templates = (
			query.order_by(desc(DocumentTemplate.usage_count), desc(DocumentTemplate.created_at)).offset((page - 1) * per_page).limit(per_page).all()
		)

		return templates, total

	def update_template(self, template_id: int, user_id: int, update_data: DocumentTemplateUpdate) -> Optional[DocumentTemplate]:
		"""Update a template (only owner can update)"""

		template = self.db.query(DocumentTemplate).filter(and_(DocumentTemplate.id == template_id, DocumentTemplate.user_id == user_id)).first()

		if not template:
			return None

		# Update fields
		update_dict = update_data.dict(exclude_unset=True)
		for field, value in update_dict.items():
			if field == "template_structure" and value:
				setattr(template, field, value.dict())
			else:
				setattr(template, field, value)

		template.updated_at = datetime.now(timezone.utc)

		self.db.commit()
		self.db.refresh(template)

		return template

	def delete_template(self, template_id: int, user_id: int) -> bool:
		"""Delete a template (only owner can delete, not system templates)"""

		template = (
			self.db.query(DocumentTemplate)
			.filter(and_(DocumentTemplate.id == template_id, DocumentTemplate.user_id == user_id, DocumentTemplate.is_system_template == False))
			.first()
		)

		if not template:
			return False

		# Soft delete by marking as inactive
		template.is_active = False
		template.updated_at = datetime.now(timezone.utc)

		self.db.commit()

		return True

	def generate_document(self, user_id: int, generation_request: TemplateGenerationRequest) -> GeneratedDocument:
		"""Generate a document from a template"""

		# Get template
		template = self.get_template(generation_request.template_id, user_id)
		if not template:
			raise HTTPException(status_code=404, detail="Template not found")

		# Get user data
		user = self.db.query(User).filter(User.id == user_id).first()
		if not user:
			raise HTTPException(status_code=404, detail="User not found")

		# Get job data if specified
		job_data = None
		if generation_request.job_id:
			job = self.db.query(Job).filter(and_(Job.id == generation_request.job_id, Job.user_id == user_id)).first()
			if job:
				job_data = {
					"company": job.company,
					"title": job.title,
					"location": job.location,
					"description": job.description,
					"requirements": job.requirements,
					"salary_min": job.salary_min,
					"salary_max": job.salary_max,
				}

		# Prepare generation data
		user_profile_data = user.profile if user.profile else {}
		generation_data = {
			"user_data": {"id": user.id, "email": user.email, "profile": user_profile_data, **generation_request.customizations.get("user_data", {})},
			"job_data": job_data,
			"customizations": generation_request.customizations,
			"preferences": {"include_job_matching": generation_request.include_job_matching, "output_format": generation_request.output_format},
		}

		# Generate tailored content if job matching is enabled
		tailored_content = None
		if generation_request.include_job_matching and job_data:
			tailored_content = self._generate_job_tailored_content(user_profile_data, job_data, template.template_structure)
			generation_data["tailored_content"] = tailored_content.dict()

		# Render template with data
		rendered_html = self._render_template(template, generation_data)

		# Create generated document record
		generated_doc = GeneratedDocument(
			user_id=user_id,
			template_id=template.id,
			job_id=generation_request.job_id,
			name=f"{template.name} - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
			document_type=template.template_type,
			generation_data=generation_data,
			generated_html=rendered_html,
			file_format=generation_request.output_format,
			generation_method="template",
			customization_level="basic" if not tailored_content else "advanced",
			status="generated",
			usage_count=0,
		)

		# Save file if not HTML
		if generation_request.output_format != "html":
			file_path = self._save_generated_file(generated_doc, rendered_html, generation_request.output_format)
			generated_doc.file_path = str(file_path.relative_to(self.generated_dir))

		self.db.add(generated_doc)

		# Update template usage
		template.usage_count += 1
		template.last_used = datetime.now(timezone.utc)

		self.db.commit()
		self.db.refresh(generated_doc)

		return generated_doc

	def _generate_job_tailored_content(
		self, user_profile: Dict[str, Any], job_data: Dict[str, Any], template_structure: Dict[str, Any]
	) -> JobTailoredContent:
		"""Generate job-specific content tailoring"""

		user_skills = user_profile.get("skills", [])
		job_requirements = job_data.get("requirements", {})

		# Extract required skills from job
		required_skills = []
		if isinstance(job_requirements, dict):
			required_skills = job_requirements.get("skills", [])
		elif isinstance(job_requirements, list):
			required_skills = job_requirements

		# Find matching skills to highlight
		highlighted_skills = [skill for skill in user_skills if skill.lower() in [req.lower() for req in required_skills]]

		# Generate tailored summary (basic keyword matching for now)
		tailored_summary = self._generate_tailored_summary(user_profile, job_data, highlighted_skills)

		# Identify relevant experience
		relevant_experience = self._identify_relevant_experience(user_profile, job_data)

		# Generate ATS keywords
		keyword_optimization = self._generate_ats_keywords(job_data)

		return JobTailoredContent(
			highlighted_skills=highlighted_skills,
			tailored_summary=tailored_summary,
			relevant_experience=relevant_experience,
			keyword_optimization=keyword_optimization,
			customized_sections={},
		)

	def _generate_tailored_summary(self, user_profile: Dict[str, Any], job_data: Dict[str, Any], highlighted_skills: List[str]) -> str:
		"""Generate a job-tailored professional summary"""

		base_summary = user_profile.get("summary", "")
		experience_level = user_profile.get("experience_level", "mid")

		# Basic template-based summary generation
		if highlighted_skills:
			skills_text = ", ".join(highlighted_skills[:3])  # Top 3 matching skills
			tailored_summary = f"Experienced {experience_level}-level professional with expertise in {skills_text}. "

			if base_summary:
				tailored_summary += base_summary
			else:
				tailored_summary += (
					f"Seeking to leverage technical skills and experience to contribute to {job_data.get('company', 'the organization')}'s success."
				)
		else:
			tailored_summary = base_summary or "Dedicated professional seeking new opportunities to grow and contribute."

		return tailored_summary

	def _identify_relevant_experience(self, user_profile: Dict[str, Any], job_data: Dict[str, Any]) -> List[Dict[str, Any]]:
		"""Identify most relevant experience items for the job"""

		experience = user_profile.get("experience", [])
		if not experience:
			return []

		# Simple relevance scoring based on keyword matching
		job_keywords = set()
		if job_data.get("description"):
			job_keywords.update(job_data["description"].lower().split())
		if job_data.get("requirements"):
			if isinstance(job_data["requirements"], dict):
				for req_list in job_data["requirements"].values():
					if isinstance(req_list, list):
						job_keywords.update([req.lower() for req in req_list])

		# Score experience items
		scored_experience = []
		for exp in experience:
			score = 0
			exp_text = (exp.get("description", "") + " " + exp.get("title", "")).lower()

			for keyword in job_keywords:
				if keyword in exp_text:
					score += 1

			if score > 0:
				scored_experience.append({"experience": exp, "relevance_score": score})

		# Return top 3 most relevant
		scored_experience.sort(key=lambda x: x["relevance_score"], reverse=True)
		return [item["experience"] for item in scored_experience[:3]]

	def _generate_ats_keywords(self, job_data: Dict[str, Any]) -> List[str]:
		"""Generate ATS-friendly keywords from job data"""

		keywords = set()

		# Add job title variations
		if job_data.get("title"):
			keywords.add(job_data["title"])

		# Add company name
		if job_data.get("company"):
			keywords.add(job_data["company"])

		# Add requirements
		if job_data.get("requirements"):
			if isinstance(job_data["requirements"], dict):
				for req_list in job_data["requirements"].values():
					if isinstance(req_list, list):
						keywords.update(req_list)
			elif isinstance(job_data["requirements"], list):
				keywords.update(job_data["requirements"])

		return list(keywords)[:10]  # Limit to top 10

	def _render_template(self, template: DocumentTemplate, data: Dict[str, Any]) -> str:
		"""Render template with provided data"""

		try:
			# Create Jinja2 template
			jinja_template = self.jinja_env.from_string(template.template_content)

			# Prepare template context
			context = {
				"user": data.get("user_data", {}),
				"job": data.get("job_data", {}),
				"tailored": data.get("tailored_content", {}),
				"customizations": data.get("customizations", {}),
				"template_structure": template.template_structure,
			}

			# Render template
			rendered_html = jinja_template.render(**context)

			# Add CSS styles if provided
			if template.template_styles:
				rendered_html = f"<style>{template.template_styles}</style>\n{rendered_html}"

			return rendered_html

		except Exception as e:
			raise HTTPException(status_code=500, detail=f"Template rendering failed: {e!s}")

	def _save_generated_file(self, generated_doc: GeneratedDocument, html_content: str, output_format: str) -> Path:
		"""Save generated document to file system"""

		# Create user-specific directory
		user_dir = (self.generated_dir / str(generated_doc.user_id)).resolve()
		user_dir.mkdir(parents=True, exist_ok=True)

		safe_format = self._normalize_output_format(output_format)
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		base_name = f"{generated_doc.document_type}_{timestamp}"
		safe_name = self._sanitize_filename(base_name)
		file_path = (user_dir / f"{safe_name}.{safe_format}").resolve()

		if not self._is_within_directory(user_dir, file_path):
			raise HTTPException(status_code=400, detail="Invalid output file path")

		if safe_format == "txt":
			text_content = re.sub(r"<[^>]+>", "", html_content)
			text_content = re.sub(r"\s+", " ", text_content).strip()
			self._write_text_file(file_path, text_content)
		else:
			self._write_text_file(file_path, html_content)

		return file_path

	def _sanitize_filename(self, name: str) -> str:
		sanitized = re.sub(r"[^A-Za-z0-9_.-]+", "_", name)
		sanitized = sanitized.strip("._")
		return sanitized or "document"

	def _normalize_output_format(self, output_format: str) -> str:
		allowed = {"html", "txt", "pdf", "docx"}
		fmt = (output_format or "html").lower()
		if fmt not in allowed:
			raise HTTPException(status_code=400, detail="Unsupported output format")
		return fmt

	def _write_text_file(self, file_path: Path, contents: str) -> None:
		file_path.parent.mkdir(parents=True, exist_ok=True)
		with file_path.open("w", encoding="utf-8") as destination:
			destination.write(contents)

	def _is_within_directory(self, directory: Path, target: Path) -> bool:
		directory_path = directory.resolve()
		target_path = target.resolve()
		try:
			target_path.relative_to(directory_path)
			return True
		except ValueError:
			return False

	def get_generated_document(self, document_id: int, user_id: int) -> Optional[GeneratedDocument]:
		"""Get a generated document by ID"""

		return self.db.query(GeneratedDocument).filter(and_(GeneratedDocument.id == document_id, GeneratedDocument.user_id == user_id)).first()

	def get_user_generated_documents(
		self, user_id: int, template_id: Optional[int] = None, job_id: Optional[int] = None, page: int = 1, per_page: int = 20
	) -> Tuple[List[GeneratedDocument], int]:
		"""Get generated documents for a user"""

		query = self.db.query(GeneratedDocument).filter(GeneratedDocument.user_id == user_id)

		if template_id:
			query = query.filter(GeneratedDocument.template_id == template_id)

		if job_id:
			query = query.filter(GeneratedDocument.job_id == job_id)

		# Get total count
		total = query.count()

		# Apply pagination and ordering
		documents = query.order_by(desc(GeneratedDocument.created_at)).offset((page - 1) * per_page).limit(per_page).all()

		return documents, total

	def analyze_template(self, template_id: int, user_id: Optional[int] = None) -> TemplateAnalysis:
		"""Analyze template for ATS compatibility and optimization"""

		template = self.get_template(template_id, user_id)
		if not template:
			raise HTTPException(status_code=404, detail="Template not found")

		# Calculate ATS compatibility score (0-100)
		ats_score = self._calculate_ats_score(template)
		
		# Calculate readability score (0-100)
		readability_score = self._calculate_readability_score(template)
		
		# Extract keyword density
		keyword_density = self._extract_keyword_density(template)
		
		# Generate suggestions based on analysis
		suggestions = self._generate_suggestions(template, ats_score, readability_score)

		# Check for common sections
		sections = template.template_structure.get("sections", [])
		section_ids = [section.get("id", "") for section in sections]

		recommended_sections = ["header", "summary", "experience", "skills", "education"]
		missing = [section for section in recommended_sections if section not in section_ids]

		analysis = TemplateAnalysis(
			ats_compatibility=ats_score,
			readability_score=readability_score,
			keyword_density=keyword_density,
			suggestions=suggestions,
			missing_sections=missing,
		)

		return analysis
	
	def _calculate_ats_score(self, template) -> int:
		"""Calculate ATS compatibility score based on resume structure and content"""
		score = 100
		sections = template.template_structure.get("sections", [])
		content = str(template.template_structure)
		
		# Penalize for missing critical sections (-15 points each)
		required_sections = {"header", "experience", "skills"}
		section_ids = {section.get("id", "") for section in sections}
		missing_required = required_sections - section_ids
		score -= len(missing_required) * 15
		
		# Penalize for complex formatting that ATS can't parse (-10 points)
		if "table" in content.lower() or "column" in content.lower():
			score -= 10
		
		# Penalize for images/graphics in main content (-5 points)
		if "image" in content.lower() or "graphic" in content.lower():
			score -= 5
		
		# Bonus for standard section names (+5 points)
		standard_names = ["experience", "education", "skills", "summary"]
		if any(name in section_ids for name in standard_names):
			score += 5
		
		# Bonus for bullet points (ATS-friendly) (+5 points)
		if "•" in content or "bullet" in content.lower():
			score += 5
		
		return max(0, min(100, score))
	
	def _calculate_readability_score(self, template) -> int:
		"""Calculate readability score based on content structure"""
		score = 100
		sections = template.template_structure.get("sections", [])
		
		# Penalize for too many sections (-5 points per excess section)
		if len(sections) > 8:
			score -= (len(sections) - 8) * 5
		
		# Penalize for missing section headers (-10 points)
		sections_without_headers = sum(1 for s in sections if not s.get("title"))
		score -= sections_without_headers * 10
		
		# Bonus for consistent structure (+10 points)
		has_consistent_fields = all("fields" in s for s in sections)
		if has_consistent_fields:
			score += 10
		
		# Bonus for proper hierarchy (+5 points)
		if len(sections) >= 3:
			score += 5
		
		return max(0, min(100, score))
	
	def _extract_keyword_density(self, template) -> Dict[str, float]:
		"""Extract keyword frequency from template content"""
		content = str(template.template_structure).lower()
		
		# Common keywords to track
		keywords = ["experience", "skills", "education", "project", "achievement", 
		           "leadership", "team", "management", "development", "analysis"]
		
		keyword_density = {}
		word_count = len(content.split())
		
		for keyword in keywords:
			count = content.count(keyword)
			if count > 0:
				density = round((count / word_count) * 100, 2)
				keyword_density[keyword] = density
		
		return keyword_density
	
	def _generate_suggestions(self, template, ats_score: int, readability_score: int) -> List[str]:
		"""Generate improvement suggestions based on scores"""
		suggestions = []
		sections = template.template_structure.get("sections", [])
		section_ids = [s.get("id", "") for s in sections]
		
		# ATS-related suggestions
		if ats_score < 70:
			suggestions.append("Improve ATS compatibility by using standard section names")
			suggestions.append("Avoid complex tables and graphics that ATS systems can't parse")
		
		if "experience" not in section_ids:
			suggestions.append("Add an 'Experience' section to highlight your work history")
		
		if "skills" not in section_ids:
			suggestions.append("Add a 'Skills' section with relevant technical and soft skills")
		
		# Readability suggestions
		if readability_score < 70:
			suggestions.append("Simplify template structure for better readability")
			suggestions.append("Ensure all sections have clear headers")
		
		if len(sections) > 8:
			suggestions.append("Consider consolidating sections for a more focused resume")
		
		# General suggestions
		suggestions.append("Use quantified achievements (e.g., 'Increased sales by 30%')")
		suggestions.append("Include relevant industry keywords throughout your resume")
		suggestions.append("Keep formatting consistent across all sections")
		
		return suggestions[:5]  # Return top 5 suggestions

	def get_template_usage_stats(self, template_id: int, user_id: Optional[int] = None) -> TemplateUsageStats:
		"""Get usage statistics for a template"""

		template = self.get_template(template_id, user_id)
		if not template:
			raise HTTPException(status_code=404, detail="Template not found")

		# Count generated documents
		generated_count = self.db.query(GeneratedDocument).filter(GeneratedDocument.template_id == template_id).count()

		return TemplateUsageStats(
			template_id=template_id,
			usage_count=template.usage_count,
			last_used=template.last_used,
			generated_documents_count=generated_count,
			average_rating=None,  # Would need rating system
			popular_customizations=[],  # Would analyze common customizations
		)

	def create_system_templates(self):
		"""Create default system templates"""

		# Check if system templates already exist
		existing = self.db.query(DocumentTemplate).filter(DocumentTemplate.is_system_template == True).first()

		if existing:
			return  # System templates already created

		# Create basic resume template
		resume_template = self._create_basic_resume_template()
		self.db.add(resume_template)

		# Create basic cover letter template
		cover_letter_template = self._create_basic_cover_letter_template()
		self.db.add(cover_letter_template)

		self.db.commit()

	def _create_basic_resume_template(self) -> DocumentTemplate:
		"""Create a basic resume template"""

		template_structure = {
			"sections": [
				{
					"id": "header",
					"name": "Header",
					"type": "header",
					"required": True,
					"order": 1,
					"fields": [
						{"name": "full_name", "type": "text", "required": True, "placeholder": "Your Full Name"},
						{"name": "email", "type": "email", "required": True, "placeholder": "your.email@example.com"},
						{"name": "phone", "type": "tel", "required": False, "placeholder": "(555) 123-4567"},
						{"name": "location", "type": "text", "required": False, "placeholder": "City, State"},
					],
				},
				{
					"id": "summary",
					"name": "Professional Summary",
					"type": "text_area",
					"required": False,
					"dynamic_content": True,
					"job_matching": True,
					"order": 2,
					"fields": [{"name": "summary_text", "type": "textarea", "required": False, "placeholder": "Brief professional summary..."}],
				},
				{
					"id": "experience",
					"name": "Work Experience",
					"type": "list",
					"required": True,
					"dynamic_content": True,
					"job_matching": True,
					"order": 3,
					"fields": [
						{"name": "title", "type": "text", "required": True, "placeholder": "Job Title"},
						{"name": "company", "type": "text", "required": True, "placeholder": "Company Name"},
						{"name": "location", "type": "text", "required": False, "placeholder": "City, State"},
						{"name": "start_date", "type": "date", "required": True, "placeholder": "MM/YYYY"},
						{"name": "end_date", "type": "date", "required": False, "placeholder": "MM/YYYY or Present"},
						{"name": "description", "type": "textarea", "required": True, "placeholder": "Key achievements and responsibilities..."},
					],
				},
				{
					"id": "skills",
					"name": "Skills",
					"type": "list",
					"required": True,
					"dynamic_content": True,
					"job_matching": True,
					"order": 4,
					"fields": [
						{"name": "category", "type": "text", "required": False, "placeholder": "Technical Skills"},
						{"name": "skills_list", "type": "text", "required": True, "placeholder": "Python, JavaScript, React, etc."},
					],
				},
				{
					"id": "education",
					"name": "Education",
					"type": "list",
					"required": True,
					"order": 5,
					"fields": [
						{"name": "degree", "type": "text", "required": True, "placeholder": "Bachelor of Science"},
						{"name": "field", "type": "text", "required": True, "placeholder": "Computer Science"},
						{"name": "school", "type": "text", "required": True, "placeholder": "University Name"},
						{"name": "graduation_date", "type": "date", "required": False, "placeholder": "MM/YYYY"},
						{"name": "gpa", "type": "text", "required": False, "placeholder": "3.8/4.0"},
					],
				},
			],
			"styling": {
				"font_family": "Arial, sans-serif",
				"font_size": "11pt",
				"margins": {"top": "1in", "bottom": "1in", "left": "1in", "right": "1in"},
				"colors": {"primary": "#000000", "accent": "#333333"},
			},
		}

		template_content = """
<div class="resume">
    <header class="header">
        <h1>{{ user.profile.full_name or user.email }}</h1>
        <div class="contact-info">
            <span>{{ user.email }}</span>
            {% if user.profile.phone %}<span>{{ user.profile.phone }}</span>{% endif %}
            {% if user.profile.location %}<span>{{ user.profile.location }}</span>{% endif %}
        </div>
    </header>
    
    {% if tailored.tailored_summary or user.profile.summary %}
    <section class="summary">
        <h2>Professional Summary</h2>
        <p>{{ tailored.tailored_summary or user.profile.summary }}</p>
    </section>
    {% endif %}
    
    {% if user.profile.experience %}
    <section class="experience">
        <h2>Work Experience</h2>
        {% for exp in user.profile.experience %}
        <div class="experience-item">
            <h3>{{ exp.title }} - {{ exp.company }}</h3>
            <div class="dates">{{ exp.start_date }} - {{ exp.end_date or 'Present' }}</div>
            {% if exp.location %}<div class="location">{{ exp.location }}</div>{% endif %}
            <p>{{ exp.description }}</p>
        </div>
        {% endfor %}
    </section>
    {% endif %}
    
    {% if tailored.highlighted_skills or user.profile.skills %}
    <section class="skills">
        <h2>Skills</h2>
        <div class="skills-list">
            {% for skill in (tailored.highlighted_skills or user.profile.skills) %}
            <span class="skill">{{ skill }}</span>
            {% endfor %}
        </div>
    </section>
    {% endif %}
    
    {% if user.profile.education %}
    <section class="education">
        <h2>Education</h2>
        {% for edu in user.profile.education %}
        <div class="education-item">
            <h3>{{ edu.degree }} in {{ edu.field }}</h3>
            <div class="school">{{ edu.school }}</div>
            {% if edu.graduation_date %}<div class="date">{{ edu.graduation_date }}</div>{% endif %}
            {% if edu.gpa %}<div class="gpa">GPA: {{ edu.gpa }}</div>{% endif %}
        </div>
        {% endfor %}
    </section>
    {% endif %}
</div>
        """

		template_styles = """
.resume {
    max-width: 8.5in;
    margin: 0 auto;
    padding: 1in;
    font-family: Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.2;
}

.header {
    text-align: center;
    margin-bottom: 20pt;
    border-bottom: 1pt solid #333;
    padding-bottom: 10pt;
}

.header h1 {
    margin: 0;
    font-size: 18pt;
    font-weight: bold;
}

.contact-info {
    margin-top: 5pt;
}

.contact-info span {
    margin: 0 10pt;
}

section {
    margin-bottom: 15pt;
}

section h2 {
    font-size: 14pt;
    font-weight: bold;
    margin-bottom: 8pt;
    border-bottom: 0.5pt solid #333;
    padding-bottom: 2pt;
}

.experience-item, .education-item {
    margin-bottom: 10pt;
}

.experience-item h3, .education-item h3 {
    font-size: 12pt;
    font-weight: bold;
    margin-bottom: 2pt;
}

.dates, .location, .school, .date, .gpa {
    font-style: italic;
    color: #666;
    font-size: 10pt;
}

.skills-list {
    display: flex;
    flex-wrap: wrap;
    gap: 5pt;
}

.skill {
    background-color: #f0f0f0;
    padding: 2pt 6pt;
    border-radius: 3pt;
    font-size: 10pt;
}
        """

		return DocumentTemplate(
			user_id=None,
			name="Professional Resume Template",
			description="Clean, ATS-friendly resume template suitable for most industries",
			template_type="resume",
			template_structure=template_structure,
			template_content=template_content.strip(),
			template_styles=template_styles.strip(),
			is_system_template=True,
			category="professional",
			tags=["professional", "ats-friendly", "clean"],
			version="1.0",
			usage_count=0,
			is_active=True,
		)

	def _create_basic_cover_letter_template(self) -> DocumentTemplate:
		"""Create a basic cover letter template"""

		template_structure = {
			"sections": [
				{
					"id": "header",
					"name": "Header",
					"type": "header",
					"required": True,
					"order": 1,
					"fields": [
						{"name": "full_name", "type": "text", "required": True},
						{"name": "email", "type": "email", "required": True},
						{"name": "phone", "type": "tel", "required": False},
						{"name": "location", "type": "text", "required": False},
					],
				},
				{
					"id": "date_address",
					"name": "Date and Address",
					"type": "address",
					"required": True,
					"job_matching": True,
					"order": 2,
					"fields": [
						{"name": "date", "type": "date", "required": True},
						{"name": "hiring_manager", "type": "text", "required": False},
						{"name": "company", "type": "text", "required": True},
						{"name": "company_address", "type": "textarea", "required": False},
					],
				},
				{
					"id": "opening",
					"name": "Opening Paragraph",
					"type": "text_area",
					"required": True,
					"dynamic_content": True,
					"job_matching": True,
					"order": 3,
					"fields": [{"name": "opening_text", "type": "textarea", "required": True}],
				},
				{
					"id": "body",
					"name": "Body Paragraphs",
					"type": "text_area",
					"required": True,
					"dynamic_content": True,
					"job_matching": True,
					"order": 4,
					"fields": [{"name": "body_text", "type": "textarea", "required": True}],
				},
				{
					"id": "closing",
					"name": "Closing",
					"type": "text_area",
					"required": True,
					"order": 5,
					"fields": [{"name": "closing_text", "type": "textarea", "required": True}],
				},
			],
			"styling": {
				"font_family": "Arial, sans-serif",
				"font_size": "11pt",
				"margins": {"top": "1in", "bottom": "1in", "left": "1in", "right": "1in"},
				"colors": {"primary": "#000000", "accent": "#333333"},
			},
		}

		template_content = """
<div class="cover-letter">
    <header class="header">
        <div class="sender-info">
            <h1>{{ user.profile.full_name or user.email }}</h1>
            <div class="contact-info">
                <div>{{ user.email }}</div>
                {% if user.profile.phone %}<div>{{ user.profile.phone }}</div>{% endif %}
                {% if user.profile.location %}<div>{{ user.profile.location }}</div>{% endif %}
            </div>
        </div>
    </header>
    
    <div class="date">
        {{ customizations.date or "Date" }}
    </div>
    
    <div class="recipient">
        {% if customizations.hiring_manager %}
        <div>{{ customizations.hiring_manager }}</div>
        {% endif %}
        <div>{{ job.company or customizations.company or "Company Name" }}</div>
        {% if customizations.company_address %}
        <div>{{ customizations.company_address }}</div>
        {% endif %}
    </div>
    
    <div class="salutation">
        Dear {% if customizations.hiring_manager %}{{ customizations.hiring_manager }}{% else %}Hiring Manager{% endif %},
    </div>
    
    <div class="body">
        <p class="opening">
            {{ customizations.opening_text or "I am writing to express my interest in the " + (job.title or "position") + " at " + (job.company or "your company") + "." }}
        </p>
        
        <p class="body-content">
            {{ customizations.body_text or "With my background in " + (tailored.highlighted_skills | join(", ") if tailored.highlighted_skills else "relevant technologies") + ", I am confident I would be a valuable addition to your team." }}
        </p>
        
        <p class="closing-paragraph">
            {{ customizations.closing_text or "Thank you for considering my application. I look forward to hearing from you." }}
        </p>
    </div>
    
    <div class="signature">
        <p>Sincerely,</p>
        <p>{{ user.profile.full_name or user.email }}</p>
    </div>
</div>
        """

		template_styles = """
.cover-letter {
    max-width: 8.5in;
    margin: 0 auto;
    padding: 1in;
    font-family: Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.4;
}

.header {
    margin-bottom: 20pt;
}

.sender-info h1 {
    margin: 0;
    font-size: 16pt;
    font-weight: bold;
}

.contact-info {
    margin-top: 5pt;
    font-size: 10pt;
}

.date {
    margin-bottom: 20pt;
}

.recipient {
    margin-bottom: 20pt;
}

.salutation {
    margin-bottom: 15pt;
}

.body p {
    margin-bottom: 12pt;
    text-align: justify;
}

.signature {
    margin-top: 20pt;
}

.signature p {
    margin-bottom: 5pt;
}
        """

		return DocumentTemplate(
			user_id=None,
			name="Professional Cover Letter Template",
			description="Standard cover letter template with job-specific customization",
			template_type="cover_letter",
			template_structure=template_structure,
			template_content=template_content.strip(),
			template_styles=template_styles.strip(),
			is_system_template=True,
			category="professional",
			tags=["professional", "standard", "customizable"],
			version="1.0",
			usage_count=0,
			is_active=True,
		)
