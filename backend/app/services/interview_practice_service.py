"""Interview Practice Service"""

import json
from typing import List

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models import InterviewQuestion, InterviewSession, InterviewType
from app.schemas.interview import (
	InterviewQuestionCreate,
	InterviewQuestionResponse,
	InterviewQuestionUpdate,
	InterviewSessionCreate,
	InterviewSessionResponse,
	InterviewSessionUpdate,
)
from app.services.job_service import JobService
from app.services.llm_service import LLMService, ModelType

from .cache_service import cache_service

logger = get_logger(__name__)


class InterviewPracticeService:
	def __init__(self, db: Session, ai_service_manager: LLMService, job_service: JobService):
		self.db = db
		self.llm_service = ai_service_manager
		self.db = db
		self.ai_service_manager = ai_service_manager

	async def create_session(self, user_id: int, session_create: InterviewSessionCreate) -> InterviewSessionResponse:
		session = InterviewSession(**session_create.model_dump(), user_id=user_id)
		self.db.add(session)
		await self.db.commit()
		await self.db.refresh(session)
		return InterviewSessionResponse.from_orm(session)

	async def get_session(self, session_id: int) -> InterviewSessionResponse:
		session = self.db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
		if not session:
			return None
		return InterviewSessionResponse.from_orm(session)

	async def update_session(self, session_id: int, session_update: InterviewSessionUpdate) -> InterviewSessionResponse:
		session = self.db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
		if not session:
			return None

		update_data = session_update.model_dump(exclude_unset=True)
		for key, value in update_data.items():
			setattr(session, key, value)

		self.db.commit()
		self.db.refresh(session)
		return InterviewSessionResponse.from_orm(session)

	async def add_question_to_session(self, session_id: int, question_create: InterviewQuestionCreate) -> InterviewQuestionResponse:
		question = InterviewQuestion(**question_create.model_dump(), session_id=session_id)
		self.db.add(question)
		self.db.commit()
		self.db.refresh(question)
		return InterviewQuestionResponse.from_orm(question)

	async def update_question(self, question_id: int, question_update: InterviewQuestionUpdate) -> InterviewQuestionResponse:
		question = self.db.query(InterviewQuestion).filter(InterviewQuestion.id == question_id).first()
		if not question:
			return None

		update_data = question_update.model_dump(exclude_unset=True)
		for key, value in update_data.items():
			setattr(question, key, value)

		self.db.commit()
		self.db.refresh(question)
		return InterviewQuestionResponse.from_orm(question)

	async def get_question(self, question_id: int) -> InterviewQuestionResponse:
		question = self.db.query(InterviewQuestion).filter(InterviewQuestion.id == question_id).first()
		if not question:
			return None
		return InterviewQuestionResponse.from_orm(question)

	async def get_session_history(self, user_id: int) -> List[InterviewSessionResponse]:
		sessions = self.db.query(InterviewSession).filter(InterviewSession.user_id == user_id).all()
		return [InterviewSessionResponse.from_orm(session) for session in sessions]

	async def get_interview_analytics(self, user_id: int) -> dict:
		sessions = self.db.query(InterviewSession).filter(InterviewSession.user_id == user_id).all()
		if not sessions:
			return {"message": "No interview sessions found."}

		# Basic analytics
		total_sessions = len(sessions)
		avg_score = sum(s.score for s in sessions if s.score) / total_sessions if total_sessions > 0 else 0

		# Score by interview type
		scores_by_type = {}
		for interview_type in InterviewType:
			type_sessions = [s for s in sessions if s.interview_type == interview_type and s.score]
			if type_sessions:
				avg_type_score = sum(s.score for s in type_sessions) / len(type_sessions)
				scores_by_type[interview_type.value] = avg_type_score

		# Score trend
		score_trend = []
		for session in sorted(sessions, key=lambda s: s.started_at):
			if session.score:
				score_trend.append({"date": session.started_at, "score": session.score})

		# Personalized improvement recommendations
		personalized_recommendations = []
		if scores_by_type:
			lowest_score_type = min(scores_by_type, key=scores_by_type.get)
			personalized_recommendations.append(
				f"Focus on improving your {lowest_score_type} interview skills. Your average score for this type is {scores_by_type[lowest_score_type]:.2f}."
			)
		if avg_score < 3.0:
			personalized_recommendations.append("Review common interview questions and practice structuring your answers using the STAR method.")

		# Interview preparation suggestions based on job context
		preparation_suggestions = []
		job_ids = [session.job_id for session in sessions if session.job_id]
		if job_ids:
			# Assuming a JobService exists to fetch job details
			from app.services.job_service import JobService

			job_service = JobService(self.db)
			for job_id in list(set(job_ids)):  # Process unique job IDs
				job = job_service.get_job(job_id)  # Assuming get_job method exists
				if job and job.requirements:
					preparation_suggestions.append(f"For roles like '{job.title}', focus on these requirements: {job.requirements[:100]}...")
					if job.tech_stack:
						preparation_suggestions.append(f"Brush up on technical skills like: {', '.join(job.tech_stack[:3])}.")

		return {
			"total_sessions": total_sessions,
			"average_score": avg_score,
			"scores_by_type": scores_by_type,
			"score_trend": score_trend,
			"personalized_recommendations": personalized_recommendations,
			"preparation_suggestions": preparation_suggestions,
		}

	async def generate_ai_question(self, session_id: int) -> InterviewQuestionResponse:
		session = self.db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
		if not session:
			return None

		job_context = ""
		if session.job:
			job_context = f"Job Title: {session.job.title}\nJob Description: {session.job.description}"

		# Check cache for similar interview questions
		context_key = f"{session.interview_type.value}:{job_context}"
		cached_questions = cache_service.get_cached_interview_questions(context_key)

		if cached_questions:
			# Use a cached question if available
			question_text = cached_questions[0]  # Use first cached question
			logger.info(f"Using cached interview question for session {session_id}")
		else:
			# Generate new question with AI
			prompt = f"""
            Generate a {session.interview_type.value} interview question.
            The user is practicing for an interview.
            {job_context}
            The question should be clear, concise, and relevant to the job context if provided.
            """

			ai_response = await self.llm_service.analyze_with_fallback(
				model_type=ModelType.GENERAL, prompt=prompt, criteria="quality", user_id=str(session.user_id), session_id=str(session.id)
			)

			question_text = ai_response.content

			# Cache the generated question
			cache_service.cache_interview_questions(context_key, [question_text], ttl=3600)

		question_create = InterviewQuestionCreate(question_text=question_text, question_type=session.interview_type.value)

		return await self.add_question_to_session(session_id, question_create)

	async def evaluate_answer(self, question_id: int) -> InterviewQuestionResponse:
		question = self.db.query(InterviewQuestion).filter(InterviewQuestion.id == question_id).first()
		if not question or not question.answer_text:
			return None

		session = question.session

		# Check cache for similar feedback
		cached_feedback = cache_service.get_cached_interview_feedback(question.question_text, question.answer_text)

		if cached_feedback:
			feedback = cached_feedback.get("feedback")
			score = cached_feedback.get("score")
			logger.info(f"Using cached interview feedback for question {question_id}")
		else:
			# Generate new feedback with AI
			prompt = f"""
            Evaluate the user's answer to the following interview question.
            Interview Type: {session.interview_type.value}
            Question: {question.question_text}
            User's Answer: {question.answer_text}

            Provide feedback on the answer and a score from 1 to 5.
            Return the response as a JSON object with two keys: "feedback" and "score".
            For example:
            {{
                "feedback": "Your answer was well-structured and provided a good example. You could improve by...",
                "score": 4.5
            }}
            """

			ai_response = await self.llm_service.analyze_with_fallback(
				model_type=ModelType.GENERAL, prompt=prompt, criteria="quality", user_id=str(session.user_id), session_id=str(session.id)
			)

			try:
				response_data = json.loads(ai_response.content)
				feedback = response_data.get("feedback")
				score = response_data.get("score")

				# Cache the feedback
				feedback_data = {"feedback": feedback, "score": score}
				cache_service.cache_interview_feedback(question.question_text, question.answer_text, feedback_data, ttl=3600)

			except (json.JSONDecodeError, AttributeError):
				feedback = "Could not parse AI response."
				score = None

		question_update = InterviewQuestionUpdate(feedback=feedback, score=score)
		return await self.update_question(question_id, question_update)
		question_update = InterviewQuestionUpdate(feedback=feedback, score=score)
		return await self.update_question(question_id, question_update)
