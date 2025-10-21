"""
Skill matching API endpoints
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.skill_matching_service import skill_matching_service
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


class SkillExtractionRequest(BaseModel):
    text: str


class SkillMatchingRequest(BaseModel):
    user_skills: List[str]
    job_skills: List[str]
    use_semantic: bool = True


class SkillSimilarityRequest(BaseModel):
    skill1: str
    skill2: str


class BatchSkillExtractionRequest(BaseModel):
    texts: List[str]


class SkillExtractionResponse(BaseModel):
    skills: List[str]
    count: int


class SkillMatchingResponse(BaseModel):
    score: float
    details: Dict[str, Any]


class SkillSimilarityResponse(BaseModel):
    similarity: float


class BatchSkillExtractionResponse(BaseModel):
    results: List[List[str]]
    total_unique_skills: int
    most_common_skills: List[Dict[str, Any]]


class ModelInfoResponse(BaseModel):
    sentence_transformer_available: bool
    sentence_transformer_model: str = None
    spacy_available: bool
    spacy_model: str = None
    openai_available: bool
    vocabulary_size: int
    cache_stats: Dict[str, Any]


@router.post("/extract-skills", response_model=SkillExtractionResponse)
async def extract_skills(
    request: SkillExtractionRequest,
    current_user: User = Depends(get_current_user)
):
    """Extract skills from text using NLP"""
    try:
        skills = skill_matching_service.extract_skills_from_text(request.text)
        return SkillExtractionResponse(
            skills=skills,
            count=len(skills)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Skill extraction failed: {str(e)}")


@router.post("/match-skills", response_model=SkillMatchingResponse)
async def match_skills(
    request: SkillMatchingRequest,
    current_user: User = Depends(get_current_user)
):
    """Calculate skill match score between user skills and job requirements"""
    try:
        score, details = skill_matching_service.calculate_skill_match_score(
            request.user_skills,
            request.job_skills,
            use_semantic=request.use_semantic
        )
        return SkillMatchingResponse(
            score=score,
            details=details
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Skill matching failed: {str(e)}")


@router.post("/skill-similarity", response_model=SkillSimilarityResponse)
async def calculate_skill_similarity(
    request: SkillSimilarityRequest,
    current_user: User = Depends(get_current_user)
):
    """Calculate semantic similarity between two skills"""
    try:
        similarity = skill_matching_service.calculate_semantic_similarity(
            request.skill1,
            request.skill2
        )
        return SkillSimilarityResponse(similarity=similarity)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similarity calculation failed: {str(e)}")


@router.post("/batch-extract-skills", response_model=BatchSkillExtractionResponse)
async def batch_extract_skills(
    request: BatchSkillExtractionRequest,
    current_user: User = Depends(get_current_user)
):
    """Extract skills from multiple texts efficiently"""
    try:
        results = skill_matching_service.batch_extract_skills(request.texts)
        
        # Calculate statistics
        all_skills = [skill for skills in results for skill in skills]
        unique_skills = list(set(all_skills))
        
        from collections import Counter
        skill_counts = Counter(all_skills)
        most_common = [
            {"skill": skill, "count": count}
            for skill, count in skill_counts.most_common(10)
        ]
        
        return BatchSkillExtractionResponse(
            results=results,
            total_unique_skills=len(unique_skills),
            most_common_skills=most_common
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch extraction failed: {str(e)}")


@router.post("/analyze-skill-gaps")
async def analyze_skill_gaps(
    request: SkillMatchingRequest,
    current_user: User = Depends(get_current_user)
):
    """Analyze skill gaps and provide learning recommendations"""
    try:
        analysis = skill_matching_service.analyze_skill_gaps(
            request.user_skills,
            request.job_skills
        )
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Skill gap analysis failed: {str(e)}")


@router.get("/model-info", response_model=ModelInfoResponse)
async def get_model_info(current_user: User = Depends(get_current_user)):
    """Get information about loaded NLP models and system status"""
    try:
        info = skill_matching_service.get_model_info()
        return ModelInfoResponse(**info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")


@router.post("/clear-cache")
async def clear_embedding_cache(current_user: User = Depends(get_current_user)):
    """Clear the embedding cache"""
    try:
        skill_matching_service.clear_embedding_cache()
        return {"message": "Embedding cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get("/vocabulary")
async def get_skill_vocabulary(current_user: User = Depends(get_current_user)):
    """Get the skill vocabulary used for extraction"""
    try:
        vocabulary = sorted(list(skill_matching_service.skill_vocabulary))
        return {
            "vocabulary": vocabulary,
            "size": len(vocabulary)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get vocabulary: {str(e)}")