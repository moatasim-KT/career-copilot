"""Resume parsing API endpoints"""

import logging
import os
import uuid

from fastapi import (APIRouter, BackgroundTasks, Depends, File, HTTPException,
                     Response, UploadFile)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...dependencies import get_current_user
from ...models.content_generation import ContentGeneration
from ...models.job import Job
from ...models.resume_upload import ResumeUpload
from ...models.user import User
from ...schemas.resume import (ContentGenerationRequest,
                               ContentGenerationResponse, ContentResponse,
                               ContentUpdateRequest,
                               JobDescriptionParseRequest,
                               JobDescriptionParseResponse,
                               ParsedJobDescription, ProfileUpdateSuggestions,
                               ResumeParsingRequest, ResumeParsingStatus,
                               ResumeUploadResponse)
from ...services.content_generator_service import ContentGeneratorService
from ...services.content_quality_service import ContentQualityService
from ...services.job_description_parser_service import \
    JobDescriptionParserService
from ...services.profile_service import ProfileService
from ...services.resume_parser_service import ResumeParserService

# NOTE: This file has been converted to use AsyncSession.
# Database queries need to be converted to async: await db.execute(select(...)) instead of db.query(...)

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
resume_parser = ResumeParserService()
job_description_parser = JobDescriptionParserService()
content_generator = ContentGeneratorService()
content_quality = ContentQualityService()
profile_service = ProfileService()

# Upload directory configuration
UPLOAD_DIR = "backend/uploads/resumes"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
	background_tasks: BackgroundTasks, file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""
	Upload a resume file for parsing

	Accepts PDF, DOCX, and DOC files up to 10MB
	"""
	try:
		# Validate file
		if not file.filename:
			raise HTTPException(status_code=400, detail="No file provided")

		# Check file extension
		allowed_extensions = {".pdf", ".docx", ".doc"}
		file_ext = os.path.splitext(file.filename)[1].lower()
		if file_ext not in allowed_extensions:
			raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF, DOCX, or DOC files.")

		# Generate unique filename
		unique_filename = f"{uuid.uuid4()}_{file.filename}"
		file_path = os.path.join(UPLOAD_DIR, unique_filename)

		# Save file
		content = await file.read()
		file_size = len(content)

		# Check file size (10MB limit)
		if file_size > 10 * 1024 * 1024:
			raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

		with open(file_path, "wb") as f:
			f.write(content)

		# Validate the saved file
		is_valid, error_msg = resume_parser.validate_file(file_path)
		if not is_valid:
			# Clean up the file
			os.remove(file_path)
			raise HTTPException(status_code=400, detail=error_msg)

		# Create database record
		resume_upload = ResumeUpload(
			user_id=current_user.id,
			filename=file.filename,
			file_path=file_path,
			file_size=file_size,
			file_type=file_ext[1:],  # Remove the dot
			parsing_status="pending",
		)

		db.add(resume_upload)
		await db.commit()
		await db.refresh(resume_upload)

		# Start background parsing task
		background_tasks.add_task(parse_resume_background, resume_upload.id, file_path, file.filename, current_user.id)

		logger.info(f"Resume uploaded successfully: {file.filename} for user {current_user.id}")

		return ResumeUploadResponse(
			upload_id=resume_upload.id,
			filename=resume_upload.filename,
			file_size=resume_upload.file_size,
			file_type=resume_upload.file_type,
			parsing_status=resume_upload.parsing_status,
			created_at=resume_upload.created_at,
		)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error uploading resume: {e!s}")
		raise HTTPException(status_code=500, detail="Internal server error during file upload")


@router.get("/{upload_id}/status", response_model=ResumeParsingStatus)
async def get_parsing_status(upload_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get the parsing status and results for a resume upload
	"""
	try:
		# Get the resume upload record
		result = await db.execute(select(ResumeUpload).where(ResumeUpload.id == upload_id, ResumeUpload.user_id == current_user.id))

		resume_upload = result.scalar_one_or_none()

		if not resume_upload:
			raise HTTPException(status_code=404, detail="Resume upload not found")

		return ResumeParsingStatus(
			upload_id=resume_upload.id,
			parsing_status=resume_upload.parsing_status,
			parsed_data=resume_upload.parsed_data,
			extracted_skills=resume_upload.extracted_skills,
			extracted_experience=resume_upload.extracted_experience,
			extracted_contact_info=resume_upload.extracted_contact_info,
			parsing_error=resume_upload.parsing_error,
			created_at=resume_upload.created_at,
			updated_at=resume_upload.updated_at,
		)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error getting parsing status: {e!s}")
		raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{upload_id}/suggestions", response_model=ProfileUpdateSuggestions)
async def get_profile_suggestions(upload_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get profile update suggestions based on parsed resume data
	"""
	try:
		# Get the resume upload record
		result = await db.execute(select(ResumeUpload).where(ResumeUpload.id == upload_id, ResumeUpload.user_id == current_user.id))

		resume_upload = result.scalar_one_or_none()

		if not resume_upload:
			raise HTTPException(status_code=404, detail="Resume upload not found")

		if resume_upload.parsing_status != "completed":
			raise HTTPException(status_code=400, detail="Resume parsing not completed yet")

		# Get current user profile
		current_profile = {"skills": current_user.skills or [], "experience_level": current_user.experience_level, "email": current_user.email}

		# Generate suggestions
		suggestions = await resume_parser.suggest_profile_updates(resume_upload.parsed_data or {}, current_profile)

		return ProfileUpdateSuggestions(**suggestions)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error generating profile suggestions: {e!s}")
		raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{upload_id}/apply-suggestions")
async def apply_profile_suggestions(
	upload_id: int, request: ResumeParsingRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""
	Apply profile update suggestions from parsed resume data
	"""
	try:
		# Get the resume upload record
		result = await db.execute(select(ResumeUpload).where(ResumeUpload.id == upload_id, ResumeUpload.user_id == current_user.id))

		resume_upload = result.scalar_one_or_none()

		if not resume_upload:
			raise HTTPException(status_code=404, detail="Resume upload not found")

		if resume_upload.parsing_status != "completed":
			raise HTTPException(status_code=400, detail="Resume parsing not completed yet")

		# Get current profile and suggestions
		current_profile = {"skills": current_user.skills or [], "experience_level": current_user.experience_level, "email": current_user.email}

		suggestions = await resume_parser.suggest_profile_updates(resume_upload.parsed_data or {}, current_profile)

		# Apply suggestions if requested
		if request.apply_suggestions:
			updates_applied = {}

			# Add new skills
			if suggestions["skills_to_add"]:
				current_skills = set(current_user.skills or [])
				new_skills = current_skills.union(set(suggestions["skills_to_add"]))
				current_user.skills = list(new_skills)
				updates_applied["skills_added"] = suggestions["skills_to_add"]

			# Update experience level
			if suggestions["experience_level_suggestion"]:
				current_user.experience_level = suggestions["experience_level_suggestion"]
				updates_applied["experience_level"] = suggestions["experience_level_suggestion"]

			await db.commit()

			logger.info(f"Applied profile suggestions for user {current_user.id}: {updates_applied}")

			return {"success": True, "message": "Profile suggestions applied successfully", "updates_applied": updates_applied}
		else:
			return {"success": True, "message": "Suggestions retrieved successfully", "suggestions": suggestions}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error applying profile suggestions: {e!s}")
		raise HTTPException(status_code=500, detail="Internal server error")


async def parse_resume_background(upload_id: int, file_path: str, filename: str, user_id: int):
	"""
	Background task to parse resume file
	"""
	db = next(get_db())
	try:
		# Update status to processing
		result = await db.execute(select(ResumeUpload).where(ResumeUpload.id == upload_id))

		resume_upload = result.scalar_one_or_none()
		if resume_upload:
			resume_upload.parsing_status = "processing"
			await db.commit()

		# Parse the resume
		parsed_data = await resume_parser.parse_resume(file_path, filename, user_id)

		# Update the database record with results
		if resume_upload:
			resume_upload.parsing_status = "completed"
			resume_upload.parsed_data = parsed_data
			resume_upload.extracted_skills = parsed_data.get("skills", [])
			resume_upload.extracted_experience = parsed_data.get("experience_level")
			resume_upload.extracted_contact_info = parsed_data.get("contact_info", {})
			await db.commit()

		logger.info(f"Resume parsing completed for upload {upload_id}")

	except Exception as e:
		logger.error(f"Error in background resume parsing: {e!s}")

		# Update status to failed
		if resume_upload:
			resume_upload.parsing_status = "failed"
			resume_upload.parsing_error = str(e)
			await db.commit()

	finally:
		db.close()


@router.post("/parse-job-description", response_model=JobDescriptionParseResponse)
async def parse_job_description(request: JobDescriptionParseRequest, current_user: User = Depends(get_current_user)):
	"""
	Parse a job description from URL or text to extract structured data

	Accepts either job_url or description_text (at least one required)
	"""
	try:
		# Validate input
		if not request.job_url and not request.description_text:
			raise HTTPException(status_code=400, detail="Either job_url or description_text must be provided")

		# Parse the job description
		parsed_data = await job_description_parser.parse_job_description(job_url=request.job_url, description_text=request.description_text)

		# Generate suggestions for auto-population
		suggestions = job_description_parser.generate_job_suggestions(parsed_data)

		logger.info(f"Job description parsed successfully for user {current_user.id}")

		return JobDescriptionParseResponse(success=True, parsed_data=ParsedJobDescription(**parsed_data), suggestions=suggestions)

	except ValueError as e:
		logger.warning(f"Job description parsing validation error: {e!s}")
		return JobDescriptionParseResponse(success=False, error_message=str(e))
	except Exception as e:
		logger.error(f"Error parsing job description: {e!s}")
		return JobDescriptionParseResponse(success=False, error_message="Internal server error during job description parsing")


@router.get("/job-description/test")
async def test_job_description_parsing(url: str, current_user: User = Depends(get_current_user)):
	"""
	Test endpoint for job description parsing (development use)
	"""
	try:
		parsed_data = await job_description_parser.parse_job_description(job_url=url)
		return {"success": True, "parsed_data": parsed_data, "suggestions": job_description_parser.generate_job_suggestions(parsed_data)}
	except Exception as e:
		return {"success": False, "error": str(e)}


@router.post("/content/generate", response_model=ContentGenerationResponse)
async def generate_content(request: ContentGenerationRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Generate personalized content (cover letters, resume tailoring, email templates)
	"""
	try:
		# Get job if job_id is provided
		job = None
		if request.job_id:
			result = await db.execute(select(Job).where(Job.id == request.job_id, Job.user_id == current_user.id))

			job = result.scalar_one_or_none()

			if not job:
				raise HTTPException(status_code=404, detail="Job not found")

		# Generate content based on type
		if request.content_type == "cover_letter":
			if not job:
				raise HTTPException(status_code=400, detail="Job ID required for cover letter generation")

			content_generation = await content_generator.generate_cover_letter(
				user=current_user, job=job, tone=request.tone or "professional", custom_instructions=request.custom_instructions, db=db
			)

		elif request.content_type == "resume_tailoring":
			if not job:
				raise HTTPException(status_code=400, detail="Job ID required for resume tailoring")

			# For now, use basic resume sections - in a full implementation,
			# this would come from the parsed resume data
			resume_sections = {
				"skills": ", ".join(current_user.skills) if current_user.skills else "",
				"experience": f"{current_user.experience_level} level experience",
				"summary": f"Professional with {current_user.experience_level} experience",
			}

			content_generation = await content_generator.generate_resume_tailoring(user=current_user, job=job, resume_sections=resume_sections, db=db)

		elif request.content_type == "email_template":
			if not job:
				raise HTTPException(status_code=400, detail="Job ID required for email template generation")

			content_generation = await content_generator.generate_email_template(
				user=current_user, job=job, template_type=request.template_type or "follow_up", custom_instructions=request.custom_instructions, db=db
			)

		else:
			raise HTTPException(status_code=400, detail="Invalid content type")

		logger.info(f"Generated {request.content_type} for user {current_user.id}")

		return ContentGenerationResponse(
			content_id=content_generation.id,
			content_type=content_generation.content_type,
			generated_content=content_generation.generated_content,
			tone=content_generation.tone,
			template_used=content_generation.template_used,
			created_at=content_generation.created_at,
		)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error generating content: {e!s}")
		raise HTTPException(status_code=500, detail="Internal server error during content generation")


@router.get("/content/{content_id}", response_model=ContentResponse)
async def get_content(content_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get generated content by ID
	"""
	try:
		result = await db.execute(select(ContentGeneration).where(ContentGeneration.id == content_id, ContentGeneration.user_id == current_user.id))

		content = result.scalar_one_or_none()

		if not content:
			raise HTTPException(status_code=404, detail="Content not found")

		return ContentResponse(
			id=content.id,
			user_id=content.user_id,
			job_id=content.job_id,
			content_type=content.content_type,
			generated_content=content.generated_content,
			user_modifications=content.user_modifications,
			generation_prompt=content.generation_prompt,
			tone=content.tone,
			template_used=content.template_used,
			status=content.status,
			created_at=content.created_at,
			updated_at=content.updated_at,
		)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error getting content: {e!s}")
		raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/content/{content_id}", response_model=ContentResponse)
async def update_content(
	content_id: int, request: ContentUpdateRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""
	Update generated content with user modifications
	"""
	try:
		result = await db.execute(select(ContentGeneration).where(ContentGeneration.id == content_id, ContentGeneration.user_id == current_user.id))

		content = result.scalar_one_or_none()

		if not content:
			raise HTTPException(status_code=404, detail="Content not found")

		# Update the content
		content.user_modifications = request.user_modifications
		content.status = request.status

		await db.commit()
		await db.refresh(content)

		logger.info(f"Updated content {content_id} for user {current_user.id}")

		return ContentResponse(
			id=content.id,
			user_id=content.user_id,
			job_id=content.job_id,
			content_type=content.content_type,
			generated_content=content.generated_content,
			user_modifications=content.user_modifications,
			generation_prompt=content.generation_prompt,
			tone=content.tone,
			template_used=content.template_used,
			status=content.status,
			created_at=content.created_at,
			updated_at=content.updated_at,
		)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error updating content: {e!s}")
		raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/content/user/{user_id}")
async def get_user_content(
	user_id: int, content_type: str | None = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""
	Get all content generated by a user (only accessible by the user themselves)
	"""
	try:
		# Ensure user can only access their own content
		if user_id != current_user.id:
			raise HTTPException(status_code=403, detail="Access denied")

		stmt = select(ContentGeneration).where(ContentGeneration.user_id == user_id)

		if content_type:
			stmt = stmt.where(ContentGeneration.content_type == content_type)

		result = await db.execute(stmt.order_by(ContentGeneration.created_at.desc()))
		content_list = result.scalars().all()

		return {
			"content": [
				{
					"id": content.id,
					"content_type": content.content_type,
					"job_id": content.job_id,
					"status": content.status,
					"created_at": content.created_at,
					"updated_at": content.updated_at,
				}
				for content in content_list
			]
		}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error getting user content: {e!s}")
		raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/content/{content_id}/versions")
async def get_content_versions(content_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get all versions of a content generation
	"""
	try:
		# Verify content belongs to user
		result = await db.execute(select(ContentGeneration).where(ContentGeneration.id == content_id, ContentGeneration.user_id == current_user.id))

		content = result.scalar_one_or_none()

		if not content:
			raise HTTPException(status_code=404, detail="Content not found")

		# Get versions using the service
		versions = content_generator.get_content_versions(content_id, db)

		return {
			"versions": [
				{
					"id": version.id,
					"version_number": version.version_number,
					"content": version.content,
					"change_description": version.change_description,
					"change_type": version.change_type,
					"created_at": version.created_at,
					"created_by": version.created_by,
				}
				for version in versions
			]
		}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error getting content versions: {e!s}")
		raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/content/{content_id}/rollback/{version_number}")
async def rollback_content(content_id: int, version_number: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Rollback content to a specific version
	"""
	try:
		# Verify content belongs to user
		result = await db.execute(select(ContentGeneration).where(ContentGeneration.id == content_id, ContentGeneration.user_id == current_user.id))

		content = result.scalar_one_or_none()

		if not content:
			raise HTTPException(status_code=404, detail="Content not found")

		# Rollback using the service
		updated_content = content_generator.rollback_to_version(content, version_number, db)

		return {
			"message": f"Content rolled back to version {version_number}",
			"content_id": updated_content.id,
			"current_content": updated_content.generated_content,
			"status": updated_content.status,
		}

	except ValueError as e:
		raise HTTPException(status_code=404, detail=str(e))
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error rolling back content: {e!s}")
		raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/content/{content_id}/suggestions")
async def get_template_suggestions(content_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Get template suggestions for content based on job and user context
	"""
	try:
		# Get content and associated job
		result = await db.execute(select(ContentGeneration).where(ContentGeneration.id == content_id, ContentGeneration.user_id == current_user.id))

		content = result.scalar_one_or_none()

		if not content:
			raise HTTPException(status_code=404, detail="Content not found")

		if not content.job_id:
			raise HTTPException(status_code=400, detail="Content must be associated with a job for suggestions")

		result = await db.execute(select(Job).where(Job.id == content.job_id))


		job = result.scalar_one_or_none()
		if not job:
			raise HTTPException(status_code=404, detail="Associated job not found")

		# Get suggestions using the service
		suggestions = content_generator.get_template_suggestions(job, current_user)

		return suggestions

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error getting template suggestions: {e!s}")
		raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/content/{content_id}/track-modifications")
async def track_content_modifications(
	content_id: int, request: ContentUpdateRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""
	Track user modifications to content for learning purposes
	"""
	try:
		# Get content
		result = await db.execute(select(ContentGeneration).where(ContentGeneration.id == content_id, ContentGeneration.user_id == current_user.id))

		content = result.scalar_one_or_none()

		if not content:
			raise HTTPException(status_code=404, detail="Content not found")

		# Track modifications using the service
		original_content = content.generated_content
		content_generator.track_user_modifications(content, original_content, request.user_modifications, db)

		return {"message": "User modifications tracked successfully", "content_id": content.id, "modifications_recorded": True}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error tracking content modifications: {e!s}")
		raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/content/{content_id}/analyze-quality")
async def analyze_content_quality(content_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Analyze content quality and provide scoring and suggestions
	"""
	try:
		# Get content
		result = await db.execute(select(ContentGeneration).where(ContentGeneration.id == content_id, ContentGeneration.user_id == current_user.id))

		content = result.scalar_one_or_none()

		if not content:
			raise HTTPException(status_code=404, detail="Content not found")

		# Get job keywords if available
		job_keywords = []
		if content.job_id:
			result = await db.execute(select(Job).where(Job.id == content.job_id))

			job = result.scalar_one_or_none()
			if job and job.tech_stack:
				job_keywords = job.tech_stack

		# Analyze quality
		quality_score = content_quality.analyze_content_quality(
			content=content.generated_content,
			content_type=content.content_type,
			target_tone=content.tone or "professional",
			job_keywords=job_keywords,
		)

		return {
			"content_id": content_id,
			"quality_analysis": {
				"overall_score": quality_score.overall_score,
				"readability_score": quality_score.readability_score,
				"grammar_score": quality_score.grammar_score,
				"structure_score": quality_score.structure_score,
				"keyword_relevance_score": quality_score.keyword_relevance_score,
				"length_score": quality_score.length_score,
				"tone_consistency_score": quality_score.tone_consistency_score,
				"suggestions": quality_score.suggestions,
				"issues": quality_score.issues,
			},
		}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error analyzing content quality: {e!s}")
		raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/content/{content_id}/check-grammar")
async def check_content_grammar(content_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Check content for spelling and grammar issues
	"""
	try:
		# Get content
		result = await db.execute(select(ContentGeneration).where(ContentGeneration.id == content_id, ContentGeneration.user_id == current_user.id))

		content = result.scalar_one_or_none()

		if not content:
			raise HTTPException(status_code=404, detail="Content not found")

		# Check grammar and spelling
		grammar_check = content_quality.check_spelling_and_grammar(content.generated_content)

		return {"content_id": content_id, "grammar_check": grammar_check}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error checking grammar: {e!s}")
		raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/content/{content_id}/export/{format_type}")
async def export_content(content_id: int, format_type: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
	"""
	Export content in different formats (txt, html, markdown)
	"""
	try:
		# Validate format type
		if format_type not in ["txt", "html", "markdown"]:
			raise HTTPException(status_code=400, detail="Invalid format type. Supported: txt, html, markdown")

		# Get content
		result = await db.execute(select(ContentGeneration).where(ContentGeneration.id == content_id, ContentGeneration.user_id == current_user.id))

		content = result.scalar_one_or_none()

		if not content:
			raise HTTPException(status_code=404, detail="Content not found")

		# Export content
		exported_content = content_quality.export_content(content=content.user_modifications or content.generated_content, format_type=format_type)

		# Set appropriate content type
		content_types = {"txt": "text/plain", "html": "text/html", "markdown": "text/markdown"}

		return Response(
			content=exported_content,
			media_type=content_types[format_type],
			headers={"Content-Disposition": f"attachment; filename=content_{content_id}.{format_type}"},
		)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error exporting content: {e!s}")
		raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/content/preview")
async def preview_content_with_quality(
	request: ContentGenerationRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
	"""
	Generate content preview with quality analysis before saving
	"""
	try:
		# Get job if job_id is provided
		job = None
		job_keywords = []
		if request.job_id:
			result = await db.execute(select(Job).where(Job.id == request.job_id, Job.user_id == current_user.id))

			job = result.scalar_one_or_none()

			if not job:
				raise HTTPException(status_code=404, detail="Job not found")

			if job.tech_stack:
				job_keywords = job.tech_stack

		# Generate content preview (without saving)
		if request.content_type == "cover_letter":
			if not job:
				raise HTTPException(status_code=400, detail="Job ID required for cover letter generation")

			# Generate preview content
			preview_content = await content_generator.generate_cover_letter(
				user=current_user,
				job=job,
				tone=request.tone or "professional",
				custom_instructions=request.custom_instructions,
				db=None,  # Don't save to database
			)

		elif request.content_type == "resume_tailoring":
			if not job:
				raise HTTPException(status_code=400, detail="Job ID required for resume tailoring")

			resume_sections = {
				"skills": ", ".join(current_user.skills) if current_user.skills else "",
				"experience": f"{current_user.experience_level} level experience",
				"summary": f"Professional with {current_user.experience_level} experience",
			}

			preview_content = await content_generator.generate_resume_tailoring(
				user=current_user,
				job=job,
				resume_sections=resume_sections,
				db=None,  # Don't save to database
			)

		elif request.content_type == "email_template":
			if not job:
				raise HTTPException(status_code=400, detail="Job ID required for email template generation")

			preview_content = await content_generator.generate_email_template(
				user=current_user,
				job=job,
				template_type=request.template_type or "follow_up",
				custom_instructions=request.custom_instructions,
				db=None,  # Don't save to database
			)

		else:
			raise HTTPException(status_code=400, detail="Invalid content type")

		# Analyze quality of preview content
		quality_score = content_quality.analyze_content_quality(
			content=preview_content.generated_content,
			content_type=request.content_type,
			target_tone=request.tone or "professional",
			job_keywords=job_keywords,
		)

		return {
			"preview": {
				"content_type": preview_content.content_type,
				"generated_content": preview_content.generated_content,
				"tone": preview_content.tone,
				"template_used": preview_content.template_used,
			},
			"quality_analysis": {
				"overall_score": quality_score.overall_score,
				"readability_score": quality_score.readability_score,
				"grammar_score": quality_score.grammar_score,
				"structure_score": quality_score.structure_score,
				"keyword_relevance_score": quality_score.keyword_relevance_score,
				"length_score": quality_score.length_score,
				"tone_consistency_score": quality_score.tone_consistency_score,
				"suggestions": quality_score.suggestions,
				"issues": quality_score.issues,
			},
		}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Error generating content preview: {e!s}")
		raise HTTPException(status_code=500, detail="Internal server error")
