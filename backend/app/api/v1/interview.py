"""API endpoints for interview practice"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from typing import List

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.interview import (
    InterviewSessionCreate, InterviewSessionUpdate, InterviewSessionResponse,
    InterviewQuestionCreate, InterviewQuestionUpdate, InterviewQuestionResponse
)
from app.services.interview_practice_service import InterviewPracticeService
from app.services.llm_service import LLMService, ModelType
from app.services.job_service import JobService

router = APIRouter(
    prefix="/api/v1/interview",
    tags=["interview"],
    responses={404: {"description": "Not found"}},
)

def get_interview_practice_service(db: Session = Depends(get_db)) -> InterviewPracticeService:
    ai_service_manager = LLMService()
    job_service = JobService(db)
    return InterviewPracticeService(db=db, ai_service_manager=ai_service_manager, job_service=job_service)

@router.post("/sessions", response_model=InterviewSessionResponse)
async def create_interview_session(
    session_create: InterviewSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    interview_practice_service: InterviewPracticeService = Depends(get_interview_practice_service)
):
    """Create a new interview session."""
    return await interview_practice_service.create_session(user_id=current_user.id, session_create=session_create)

@router.get("/sessions/{session_id}", response_model=InterviewSessionResponse)
async def get_interview_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    interview_practice_service: InterviewPracticeService = Depends(get_interview_practice_service)
):
    """Get an interview session."""
    session = await interview_practice_service.get_session(session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.put("/sessions/{session_id}", response_model=InterviewSessionResponse)
async def update_interview_session(
    session_id: int,
    session_update: InterviewSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    interview_practice_service: InterviewPracticeService = Depends(get_interview_practice_service)
):
    """Update an interview session."""
    session = await interview_practice_service.get_session(session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return await interview_practice_service.update_session(session_id=session_id, session_update=session_update)

@router.post("/sessions/{session_id}/questions", response_model=InterviewQuestionResponse)
async def add_question_to_session(
    session_id: int,
    question_create: InterviewQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    interview_practice_service: InterviewPracticeService = Depends(get_interview_practice_service)
):
    """Add a question to an interview session."""
    session = await interview_practice_service.get_session(session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return await interview_practice_service.add_question_to_session(session_id=session_id, question_create=question_create)

@router.put("/questions/{question_id}", response_model=InterviewQuestionResponse)
async def update_question(
    question_id: int,
    question_update: InterviewQuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    interview_practice_service: InterviewPracticeService = Depends(get_interview_practice_service)
):
    """Update an interview question."""
    question = await interview_practice_service.get_question(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    session = await interview_practice_service.get_session(question.session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this question")
    return await interview_practice_service.update_question(question_id=question_id, question_update=question_update)

@router.post("/sessions/{session_id}/generate-question", response_model=InterviewQuestionResponse)
async def generate_ai_question(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    interview_practice_service: InterviewPracticeService = Depends(get_interview_practice_service)
):
    """Generate a new AI question for a session."""
    session = await interview_practice_service.get_session(session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return await interview_practice_service.generate_ai_question(session_id=session_id)

@router.post("/questions/{question_id}/evaluate-answer", response_model=InterviewQuestionResponse)
async def evaluate_answer(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    interview_practice_service: InterviewPracticeService = Depends(get_interview_practice_service)
):
    """Evaluate the user's answer for a question."""
    question = await interview_practice_service.get_question(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    session = await interview_practice_service.get_session(question.session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to evaluate this answer")
    return await interview_practice_service.evaluate_answer(question_id=question_id)

@router.get("/sessions/history", response_model=List[InterviewSessionResponse])
async def get_session_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    interview_practice_service: InterviewPracticeService = Depends(get_interview_practice_service)
):
    """Get the interview session history for the current user."""
    return await interview_practice_service.get_session_history(user_id=current_user.id)

@router.get("/sessions/analytics", response_model=dict)
async def get_interview_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    interview_practice_service: InterviewPracticeService = Depends(get_interview_practice_service)
):
    """Get interview analytics for the current user."""
    return await interview_practice_service.get_interview_analytics(user_id=current_user.id)
