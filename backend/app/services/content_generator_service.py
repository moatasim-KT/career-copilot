"""Content Generator Service for creating personalized cover letters and resume modifications"""

import logging
import json
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from ..services.llm_manager import LLMManager
from ..models.content_generation import ContentGeneration
from ..models.content_version import ContentVersion
from ..models.job import Job
from ..models.user import User
from ..utils.redis_client import redis_client

logger = logging.getLogger(__name__)


class ContentGeneratorService:
    """Service for generating personalized content using LLM"""

    def __init__(self):
        self.llm_manager = LLMManager()

        # Enhanced content templates with more options
        self.cover_letter_templates = {
            "professional": {
                "opening": "Dear Hiring Manager,\n\nI am writing to express my strong interest in the {job_title} position at {company}.",
                "closing": "Thank you for considering my application. I look forward to the opportunity to discuss how my skills and experience can contribute to {company}'s success.\n\nSincerely,\n{user_name}",
                "style": "formal, business-like, respectful",
            },
            "casual": {
                "opening": "Hi there!\n\nI'm excited to apply for the {job_title} role at {company}.",
                "closing": "Thanks for your time and consideration. I'd love to chat more about how I can help {company} achieve its goals!\n\nBest regards,\n{user_name}",
                "style": "friendly, conversational, approachable",
            },
            "enthusiastic": {
                "opening": "Dear {company} Team,\n\nI am thrilled to submit my application for the {job_title} position!",
                "closing": "I am genuinely excited about the possibility of joining {company} and contributing to your innovative work. Thank you for your consideration!\n\nWith enthusiasm,\n{user_name}",
                "style": "energetic, passionate, excited",
            },
            "confident": {
                "opening": "Dear Hiring Manager,\n\nWith my proven track record in {relevant_field}, I am confident I would be an excellent fit for the {job_title} position at {company}.",
                "closing": "I am ready to bring my expertise to {company} and contribute to your continued success. I look forward to discussing this opportunity further.\n\nBest regards,\n{user_name}",
                "style": "assertive, self-assured, results-focused",
            },
            "creative": {
                "opening": "Hello {company} Team,\n\nYour {job_title} position caught my attention because it perfectly aligns with my passion for {relevant_field} and innovation.",
                "closing": "I would love to bring my creative perspective and technical skills to {company}. Thank you for considering my application!\n\nCreatively yours,\n{user_name}",
                "style": "innovative, artistic, unique",
            },
        }

        # Job type specific templates
        self.job_type_templates = {
            "startup": {
                "focus": "adaptability, growth mindset, wearing multiple hats",
                "keywords": ["agile", "fast-paced", "innovative", "growth", "impact"],
            },
            "enterprise": {
                "focus": "scalability, process improvement, collaboration",
                "keywords": [
                    "enterprise",
                    "scale",
                    "process",
                    "collaboration",
                    "efficiency",
                ],
            },
            "remote": {
                "focus": "self-motivation, communication, time management",
                "keywords": [
                    "remote",
                    "autonomous",
                    "communication",
                    "self-directed",
                    "virtual",
                ],
            },
            "consulting": {
                "focus": "client service, problem-solving, adaptability",
                "keywords": [
                    "client",
                    "consulting",
                    "solutions",
                    "analysis",
                    "recommendations",
                ],
            },
        }

    async def generate_cover_letter(
        self,
        user: User,
        job: Job,
        tone: str = "professional",
        custom_instructions: Optional[str] = None,
        db: Session = None,
    ) -> ContentGeneration:
        """
        Generate a personalized cover letter for a specific job

        Args:
            user: User object
            job: Job object
            tone: Tone of the cover letter (professional, casual, enthusiastic)
            custom_instructions: Additional instructions for customization
            db: Database session

        Returns:
            ContentGeneration object with the generated cover letter
        """
        cache_key = f"cover_letter:{user.id}:{job.id}:{tone}:{custom_instructions}"
        if redis_client:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return ContentGeneration(**json.loads(cached_result))

        try:
            # Prepare context for LLM
            user_skills = (
                ", ".join(user.skills) if user.skills else "various technical skills"
            )
            job_tech_stack = (
                ", ".join(job.tech_stack)
                if job.tech_stack
                else "the required technologies"
            )

            # Create the prompt
            prompt = self._create_cover_letter_prompt(
                user=user,
                job=job,
                tone=tone,
                user_skills=user_skills,
                job_tech_stack=job_tech_stack,
                custom_instructions=custom_instructions,
            )

            # Generate content using LLM
            generated_content = await self.llm_manager.generate_response(prompt)

            # Fallback to template if LLM fails
            if not generated_content or len(generated_content.strip()) < 100:
                logger.warning(
                    "LLM generation failed or too short, using template fallback"
                )
                generated_content = self._generate_template_cover_letter(
                    user, job, tone
                )

            # Create and save the content generation record
            content_generation = ContentGeneration(
                user_id=user.id,
                job_id=job.id,
                content_type="cover_letter",
                generated_content=generated_content,
                generation_prompt=prompt,
                tone=tone,
                template_used="llm"
                if len(generated_content.strip()) >= 100
                else "template",
                status="generated",
            )

            if db:
                db.add(content_generation)
                db.commit()
                db.refresh(content_generation)

                # Create initial version
                self.create_content_version(
                    content_generation=content_generation,
                    content=generated_content,
                    change_description="Initial generation",
                    change_type="generated",
                    created_by="ai",
                    db=db,
                )

            if redis_client:
                redis_client.set(cache_key, content_generation.json(), ex=3600)

            logger.info(f"Generated cover letter for user {user.id} and job {job.id}")
            return content_generation

        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}")
            raise

    async def generate_resume_tailoring(
        self, user: User, job: Job, resume_sections: Dict[str, str], db: Session = None
    ) -> ContentGeneration:
        """
        Generate resume tailoring suggestions for a specific job

        Args:
            user: User object
            job: Job object
            resume_sections: Dictionary of resume sections to tailor
            db: Database session

        Returns:
            ContentGeneration object with tailoring suggestions
        """
        cache_key = f"resume_tailoring:{user.id}:{job.id}:{json.dumps(resume_sections)}"
        if redis_client:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return ContentGeneration(**json.loads(cached_result))

        try:
            # Create the prompt for resume tailoring
            prompt = self._create_resume_tailoring_prompt(user, job, resume_sections)

            # Generate suggestions using LLM
            generated_content = await self.llm_manager.generate_response(prompt)

            # Fallback to basic suggestions if LLM fails
            if not generated_content or len(generated_content.strip()) < 50:
                logger.warning(
                    "LLM generation failed, using basic tailoring suggestions"
                )
                generated_content = self._generate_basic_tailoring_suggestions(
                    user, job
                )

            # Create and save the content generation record
            content_generation = ContentGeneration(
                user_id=user.id,
                job_id=job.id,
                content_type="resume_tailoring",
                generated_content=generated_content,
                generation_prompt=prompt,
                status="generated",
            )

            if db:
                db.add(content_generation)
                db.commit()
                db.refresh(content_generation)

                # Create initial version
                self.create_content_version(
                    content_generation=content_generation,
                    content=generated_content,
                    change_description="Initial generation",
                    change_type="generated",
                    created_by="ai",
                    db=db,
                )

            if redis_client:
                redis_client.set(cache_key, content_generation.json(), ex=3600)

            logger.info(
                f"Generated resume tailoring for user {user.id} and job {job.id}"
            )
            return content_generation

        except Exception as e:
            logger.error(f"Error generating resume tailoring: {str(e)}")
            raise

    async def generate_email_template(
        self,
        user: User,
        job: Job,
        template_type: str = "follow_up",
        custom_instructions: Optional[str] = None,
        db: Session = None,
    ) -> ContentGeneration:
        """
        Generate email templates for job applications

        Args:
            user: User object
            job: Job object
            template_type: Type of email (follow_up, thank_you, inquiry)
            custom_instructions: Additional instructions
            db: Database session

        Returns:
            ContentGeneration object with the email template
        """
        cache_key = (
            f"email_template:{user.id}:{job.id}:{template_type}:{custom_instructions}"
        )
        if redis_client:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return ContentGeneration(**json.loads(cached_result))

        try:
            # Create the prompt for email template
            prompt = self._create_email_template_prompt(
                user, job, template_type, custom_instructions
            )

            # Generate content using LLM
            generated_content = await self.llm_manager.generate_response(prompt)

            # Fallback to basic template if LLM fails
            if not generated_content or len(generated_content.strip()) < 50:
                logger.warning("LLM generation failed, using basic email template")
                generated_content = self._generate_basic_email_template(
                    user, job, template_type
                )

            # Create and save the content generation record
            content_generation = ContentGeneration(
                user_id=user.id,
                job_id=job.id,
                content_type="email_template",
                generated_content=generated_content,
                generation_prompt=prompt,
                template_used=template_type,
                status="generated",
            )

            if db:
                db.add(content_generation)
                db.commit()
                db.refresh(content_generation)

                # Create initial version
                self.create_content_version(
                    content_generation=content_generation,
                    content=generated_content,
                    change_description="Initial generation",
                    change_type="generated",
                    created_by="ai",
                    db=db,
                )

            if redis_client:
                redis_client.set(cache_key, content_generation.json(), ex=3600)

            logger.info(
                f"Generated {template_type} email template for user {user.id} and job {job.id}"
            )
            return content_generation

        except Exception as e:
            logger.error(f"Error generating email template: {str(e)}")
            raise

    def _create_cover_letter_prompt(
        self,
        user: User,
        job: Job,
        tone: str,
        user_skills: str,
        job_tech_stack: str,
        custom_instructions: Optional[str] = None,
    ) -> str:
        """Create a prompt for cover letter generation"""

        tone_instructions = {
            "professional": "Write in a professional, formal tone. Be respectful and business-like.",
            "casual": "Write in a friendly, conversational tone. Be approachable but still professional.",
            "enthusiastic": "Write with enthusiasm and energy. Show genuine excitement about the opportunity.",
        }

        prompt = f"""
        Write a personalized cover letter for the following job application:

        Job Details:
        - Position: {job.title}
        - Company: {job.company}
        - Location: {job.location or "Not specified"}
        - Required Skills: {job_tech_stack}
        - Job Description: {job.description[:500] if job.description else "Not provided"}

        Candidate Details:
        - Name: {user.username}
        - Skills: {user_skills}
        - Experience Level: {user.experience_level or "Not specified"}

        Instructions:
        - {tone_instructions.get(tone, tone_instructions["professional"])}
        - Highlight relevant skills that match the job requirements
        - Keep it concise (3-4 paragraphs)
        - Include a strong opening and professional closing
        - Make it specific to this job and company
        - Avoid generic statements

        {f"Additional Instructions: {custom_instructions}" if custom_instructions else ""}

        Please write the complete cover letter:
        """

        return prompt

    def _create_resume_tailoring_prompt(
        self, user: User, job: Job, resume_sections: Dict[str, str]
    ) -> str:
        """Create a prompt for resume tailoring suggestions"""

        sections_text = "\n".join(
            [f"{section}: {content}" for section, content in resume_sections.items()]
        )
        job_tech_stack = (
            ", ".join(job.tech_stack) if job.tech_stack else "Not specified"
        )

        prompt = f"""
        Provide specific suggestions to tailor this resume for the following job:

        Job Details:
        - Position: {job.title}
        - Company: {job.company}
        - Required Skills: {job_tech_stack}
        - Job Description: {job.description[:500] if job.description else "Not provided"}

        Current Resume Sections:
        {sections_text}

        Please provide specific, actionable suggestions for:
        1. Skills section - which skills to emphasize or add
        2. Experience section - how to reframe experience to match job requirements
        3. Summary/Objective - how to align with the job
        4. Keywords to include for ATS optimization

        Format your response as clear, numbered suggestions for each section.
        """

        return prompt

    def _create_email_template_prompt(
        self,
        user: User,
        job: Job,
        template_type: str,
        custom_instructions: Optional[str] = None,
    ) -> str:
        """Create a prompt for email template generation"""

        template_instructions = {
            "follow_up": "Write a polite follow-up email to check on application status",
            "thank_you": "Write a thank you email after an interview",
            "inquiry": "Write an inquiry email about the position before applying",
        }

        prompt = f"""
        Write a professional email template for the following scenario:

        Email Type: {template_type}
        Purpose: {template_instructions.get(template_type, "Professional communication")}

        Job Details:
        - Position: {job.title}
        - Company: {job.company}

        Candidate: {user.username}

        Instructions:
        - Keep it concise and professional
        - Include appropriate subject line
        - Be respectful of the recipient's time
        - Include a clear call to action if appropriate

        {f"Additional Instructions: {custom_instructions}" if custom_instructions else ""}

        Please write the complete email including subject line:
        """

        return prompt

    def _generate_template_cover_letter(self, user: User, job: Job, tone: str) -> str:
        """Generate a basic cover letter using templates"""

        template = self.cover_letter_templates.get(
            tone, self.cover_letter_templates["professional"]
        )

        # Basic template substitution
        opening = template["opening"].format(job_title=job.title, company=job.company)

        # Simple middle paragraph
        middle = f"With my background in {', '.join(user.skills[:3]) if user.skills else 'technology'} and {user.experience_level or 'relevant'} experience, I am confident I can contribute effectively to your team. I am particularly drawn to this opportunity because of {job.company}'s reputation and the chance to work with {', '.join(job.tech_stack[:2]) if job.tech_stack else 'cutting-edge technologies'}."

        closing = template["closing"].format(
            company=job.company, user_name=user.username
        )

        return f"{opening}\n\n{middle}\n\n{closing}"

    def _generate_basic_tailoring_suggestions(self, user: User, job: Job) -> str:
        """Generate basic resume tailoring suggestions"""

        suggestions = []

        # Skills suggestions
        if job.tech_stack:
            user_skills_set = set(user.skills) if user.skills else set()
            job_skills_set = set(job.tech_stack)
            missing_skills = job_skills_set - user_skills_set

            if missing_skills:
                suggestions.append(
                    f"Skills Section: Consider adding these relevant skills if you have experience with them: {', '.join(list(missing_skills)[:5])}"
                )

            matching_skills = job_skills_set & user_skills_set
            if matching_skills:
                suggestions.append(
                    f"Skills Section: Emphasize these matching skills: {', '.join(list(matching_skills)[:5])}"
                )

        # Experience suggestions
        suggestions.append(
            f"Experience Section: Highlight projects and achievements that demonstrate your ability to work with {job.tech_stack[0] if job.tech_stack else 'the required technologies'}"
        )

        # Summary suggestions
        suggestions.append(
            f"Summary Section: Mention your interest in {job.title} roles and experience with {job.company}'s industry"
        )

        return "\n".join(
            [f"{i + 1}. {suggestion}" for i, suggestion in enumerate(suggestions)]
        )

    def _generate_basic_email_template(
        self, user: User, job: Job, template_type: str
    ) -> str:
        """Generate basic email templates"""

        templates = {
            "follow_up": f"""Subject: Following up on {job.title} Application

Dear Hiring Manager,

I hope this email finds you well. I wanted to follow up on my application for the {job.title} position at {job.company} that I submitted recently.

I remain very interested in this opportunity and would welcome the chance to discuss how my skills and experience align with your team's needs.

Thank you for your time and consideration.

Best regards,
{user.username}""",
            "thank_you": f"""Subject: Thank you for the {job.title} interview

Dear Hiring Manager,

Thank you for taking the time to interview me for the {job.title} position at {job.company}. I enjoyed our conversation and learning more about the role and your team.

I am very excited about the opportunity to contribute to {job.company} and look forward to hearing about the next steps.

Thank you again for your consideration.

Best regards,
{user.username}""",
            "inquiry": f"""Subject: Inquiry about {job.title} Position

Dear Hiring Manager,

I hope this email finds you well. I am writing to express my interest in the {job.title} position at {job.company}.

I would appreciate the opportunity to learn more about this role and discuss how my background might be a good fit for your team.

Thank you for your time and consideration.

Best regards,
{user.username}""",
        }

        return templates.get(template_type, templates["inquiry"])

    async def improve_content(
        self, original_content: str, feedback: str, content_type: str = "cover_letter"
    ) -> str:
        """
        Improve existing content based on user feedback

        Args:
            original_content: The original generated content
            feedback: User feedback for improvement
            content_type: Type of content being improved

        Returns:
            Improved content string
        """
        try:
            prompt = f"""
            Please improve the following {content_type} based on the user's feedback:

            Original Content:
            {original_content}

            User Feedback:
            {feedback}

            Please provide an improved version that addresses the feedback while maintaining the overall structure and professionalism.
            """

            improved_content = await self.llm_manager.generate_response(prompt)

            if not improved_content or len(improved_content.strip()) < 50:
                logger.warning("Content improvement failed, returning original")
                return original_content

            return improved_content

        except Exception as e:
            logger.error(f"Error improving content: {str(e)}")
            return original_content

    def create_content_version(
        self,
        content_generation: ContentGeneration,
        content: str,
        change_description: str,
        change_type: str = "user_modified",
        created_by: str = "user",
        db: Session = None,
    ) -> ContentVersion:
        """
        Create a new version of content for version tracking

        Args:
            content_generation: ContentGeneration object
            content: The content for this version
            change_description: Description of what changed
            change_type: Type of change (generated, user_modified, ai_improved)
            created_by: Who created this version (user, system, ai)
            db: Database session

        Returns:
            ContentVersion object
        """
        try:
            # Get the next version number
            if db:
                last_version = (
                    db.query(ContentVersion)
                    .filter(
                        ContentVersion.content_generation_id == content_generation.id
                    )
                    .order_by(ContentVersion.version_number.desc())
                    .first()
                )

                version_number = (
                    (last_version.version_number + 1) if last_version else 1
                )
            else:
                version_number = 1

            # Create new version
            content_version = ContentVersion(
                content_generation_id=content_generation.id,
                version_number=version_number,
                content=content,
                change_description=change_description,
                change_type=change_type,
                created_by=created_by,
            )

            if db:
                db.add(content_version)
                db.commit()
                db.refresh(content_version)

            logger.info(
                f"Created version {version_number} for content {content_generation.id}"
            )
            return content_version

        except Exception as e:
            logger.error(f"Error creating content version: {str(e)}")
            raise

    def get_content_versions(
        self, content_generation_id: int, db: Session
    ) -> List[ContentVersion]:
        """
        Get all versions of a content generation

        Args:
            content_generation_id: ID of the content generation
            db: Database session

        Returns:
            List of ContentVersion objects ordered by version number
        """
        try:
            versions = (
                db.query(ContentVersion)
                .filter(ContentVersion.content_generation_id == content_generation_id)
                .order_by(ContentVersion.version_number.desc())
                .all()
            )

            return versions

        except Exception as e:
            logger.error(f"Error getting content versions: {str(e)}")
            return []

    def rollback_to_version(
        self, content_generation: ContentGeneration, version_number: int, db: Session
    ) -> ContentGeneration:
        """
        Rollback content to a specific version

        Args:
            content_generation: ContentGeneration object
            version_number: Version number to rollback to
            db: Database session

        Returns:
            Updated ContentGeneration object
        """
        try:
            # Get the target version
            target_version = (
                db.query(ContentVersion)
                .filter(
                    ContentVersion.content_generation_id == content_generation.id,
                    ContentVersion.version_number == version_number,
                )
                .first()
            )

            if not target_version:
                raise ValueError(f"Version {version_number} not found")

            # Update the content generation with the target version content
            old_content = content_generation.generated_content
            content_generation.generated_content = target_version.content
            content_generation.status = "rolled_back"

            # Create a new version entry for the rollback
            self.create_content_version(
                content_generation=content_generation,
                content=target_version.content,
                change_description=f"Rolled back to version {version_number}",
                change_type="rollback",
                created_by="user",
                db=db,
            )

            db.commit()
            db.refresh(content_generation)

            logger.info(
                f"Rolled back content {content_generation.id} to version {version_number}"
            )
            return content_generation

        except Exception as e:
            logger.error(f"Error rolling back content: {str(e)}")
            raise

    def get_template_suggestions(self, job: Job, user: User) -> Dict[str, Any]:
        """
        Get template suggestions based on job and user context

        Args:
            job: Job object
            user: User object

        Returns:
            Dictionary with template suggestions
        """
        suggestions = {
            "recommended_tone": "professional",
            "job_type": "general",
            "focus_areas": [],
            "keywords": [],
        }

        # Analyze job description for tone suggestions
        if job.description:
            description_lower = job.description.lower()

            # Determine job type
            if any(
                word in description_lower for word in ["startup", "fast-paced", "agile"]
            ):
                suggestions["job_type"] = "startup"
                suggestions["recommended_tone"] = "enthusiastic"
            elif any(
                word in description_lower
                for word in ["enterprise", "large", "corporation"]
            ):
                suggestions["job_type"] = "enterprise"
                suggestions["recommended_tone"] = "professional"
            elif any(
                word in description_lower
                for word in ["remote", "work from home", "distributed"]
            ):
                suggestions["job_type"] = "remote"
                suggestions["recommended_tone"] = "confident"
            elif any(
                word in description_lower
                for word in ["creative", "design", "innovative"]
            ):
                suggestions["recommended_tone"] = "creative"

            # Get job type specific suggestions
            if suggestions["job_type"] in self.job_type_templates:
                template = self.job_type_templates[suggestions["job_type"]]
                suggestions["focus_areas"] = [template["focus"]]
                suggestions["keywords"] = template["keywords"]

        # Consider user experience level
        if user.experience_level == "senior":
            suggestions["recommended_tone"] = "confident"
        elif user.experience_level == "junior":
            suggestions["recommended_tone"] = "enthusiastic"

        return suggestions

    def track_user_modifications(
        self,
        content_generation: ContentGeneration,
        original_content: str,
        modified_content: str,
        db: Session,
    ) -> None:
        """
        Track user modifications for learning purposes

        Args:
            content_generation: ContentGeneration object
            original_content: Original generated content
            modified_content: User-modified content
            db: Database session
        """
        try:
            # Calculate modification patterns (simplified)
            modifications = {
                "length_change": len(modified_content) - len(original_content),
                "word_count_change": len(modified_content.split())
                - len(original_content.split()),
                "has_structural_changes": "\n\n"
                in modified_content
                != "\n\n"
                in original_content,
                "tone_indicators": self._analyze_tone_changes(
                    original_content, modified_content
                ),
            }

            # Store user modifications
            content_generation.user_modifications = modified_content

            # Create version for tracking
            self.create_content_version(
                content_generation=content_generation,
                content=modified_content,
                change_description="User modifications applied",
                change_type="user_modified",
                created_by="user",
                db=db,
            )

            logger.info(
                f"Tracked user modifications for content {content_generation.id}"
            )

        except Exception as e:
            logger.error(f"Error tracking user modifications: {str(e)}")

    def _analyze_tone_changes(self, original: str, modified: str) -> Dict[str, bool]:
        """Analyze tone changes between original and modified content"""

        formal_indicators = ["Dear", "Sincerely", "respectfully", "formally"]
        casual_indicators = ["Hi", "Hey", "Thanks", "Cheers"]
        enthusiastic_indicators = ["excited", "thrilled", "passionate", "!"]

        original_lower = original.lower()
        modified_lower = modified.lower()

        return {
            "became_more_formal": (
                sum(1 for word in formal_indicators if word.lower() in modified_lower)
                > sum(1 for word in formal_indicators if word.lower() in original_lower)
            ),
            "became_more_casual": (
                sum(1 for word in casual_indicators if word.lower() in modified_lower)
                > sum(1 for word in casual_indicators if word.lower() in original_lower)
            ),
            "became_more_enthusiastic": (
                sum(
                    1
                    for word in enthusiastic_indicators
                    if word.lower() in modified_lower
                )
                > sum(
                    1
                    for word in enthusiastic_indicators
                    if word.lower() in original_lower
                )
            ),
        }
