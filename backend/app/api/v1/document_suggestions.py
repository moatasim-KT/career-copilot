"""
Document suggestion API endpoints for Career Co-Pilot system
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.document_suggestion_service import DocumentSuggestionService
from app.schemas.document_suggestion import (
    DocumentSuggestionResponse,
    DocumentOptimizationResponse,
    DocumentPerformanceResponse,
    JobDocumentMatchResponse,
    BulkDocumentAnalysisRequest,
    BulkDocumentAnalysisResponse,
    DocumentPortfolioAnalysis,
    SmartDocumentRecommendation,
    DocumentTemplateRecommendation
)

router = APIRouter(prefix="/document-suggestions", tags=["document-suggestions"])


@router.get("/job/{job_id}", response_model=DocumentSuggestionResponse)
async def get_document_suggestions_for_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document suggestions for a specific job application"""
    
    service = DocumentSuggestionService(db)
    
    try:
        suggestions = service.suggest_documents_for_job(job_id, current_user.id)
        
        # Get job details for response
        from app.services.job_service import JobService
        job_service = JobService(db)
        job = job_service.get_job(job_id, current_user.id)
        
        return DocumentSuggestionResponse(
            job_id=job.id,
            job_title=job.title,
            company=job.company,
            suggestions=suggestions,
            total_suggestions=len(suggestions)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document suggestions: {str(e)}")


@router.get("/document/{document_id}/optimization", response_model=DocumentOptimizationResponse)
async def get_document_optimization_recommendations(
    document_id: int,
    target_job_id: Optional[int] = Query(None, description="Optional target job for context"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get optimization recommendations for a document"""
    
    service = DocumentSuggestionService(db)
    
    try:
        recommendations = service.get_document_optimization_recommendations(
            document_id, current_user.id, target_job_id
        )
        
        # Get document details for response
        from app.services.document_service import DocumentService
        doc_service = DocumentService(db)
        document = doc_service.get_document(document_id, current_user.id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentOptimizationResponse(
            document_id=document.id,
            document_type=document.document_type,
            filename=document.original_filename,
            recommendations=recommendations,
            total_recommendations=len(recommendations)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get optimization recommendations: {str(e)}")


@router.get("/document/{document_id}/performance", response_model=DocumentPerformanceResponse)
async def get_document_performance_metrics(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get performance metrics for a document"""
    
    service = DocumentSuggestionService(db)
    
    try:
        performance_metrics = service.get_document_performance_metrics(document_id, current_user.id)
        
        if not performance_metrics:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get document details for response
        from app.services.document_service import DocumentService
        doc_service = DocumentService(db)
        document = doc_service.get_document(document_id, current_user.id)
        
        return DocumentPerformanceResponse(
            document_id=document.id,
            document_type=document.document_type,
            filename=document.original_filename,
            performance_metrics=performance_metrics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")


@router.get("/job-matches", response_model=JobDocumentMatchResponse)
async def get_job_document_matches(
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of matches to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get jobs that best match user's documents"""
    
    service = DocumentSuggestionService(db)
    
    try:
        matches = service.get_job_document_matches(current_user.id, limit)
        
        return JobDocumentMatchResponse(
            matches=matches,
            total_matches=len(matches)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job-document matches: {str(e)}")


@router.post("/bulk-analysis", response_model=BulkDocumentAnalysisResponse)
async def bulk_document_analysis(
    request: BulkDocumentAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Perform bulk analysis on multiple documents"""
    
    service = DocumentSuggestionService(db)
    
    try:
        analyses = []
        total_recommendations = 0
        total_performance_issues = 0
        
        for document_id in request.document_ids:
            analysis = {"document_id": document_id}
            
            if request.include_optimization:
                recommendations = service.get_document_optimization_recommendations(
                    document_id, current_user.id
                )
                analysis["optimization_recommendations"] = recommendations
                total_recommendations += len(recommendations)
            
            if request.include_performance:
                performance = service.get_document_performance_metrics(
                    document_id, current_user.id
                )
                analysis["performance_metrics"] = performance
                
                if performance and performance.response_rate < 0.2:
                    total_performance_issues += 1
            
            analyses.append(analysis)
        
        summary = {
            "total_documents_analyzed": len(request.document_ids),
            "total_recommendations": total_recommendations,
            "documents_with_performance_issues": total_performance_issues,
            "avg_recommendations_per_document": total_recommendations / len(request.document_ids) if request.document_ids else 0
        }
        
        return BulkDocumentAnalysisResponse(
            analyses=analyses,
            summary=summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform bulk analysis: {str(e)}")


@router.get("/portfolio-analysis", response_model=DocumentPortfolioAnalysis)
async def get_document_portfolio_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive analysis of user's document portfolio"""
    
    service = DocumentSuggestionService(db)
    
    try:
        # Get all user documents
        from app.services.document_service import DocumentService
        doc_service = DocumentService(db)
        documents, total = doc_service.get_user_documents(current_user.id, page=1, per_page=1000)
        
        if not documents:
            return DocumentPortfolioAnalysis(
                total_documents=0,
                documents_by_type={},
                overall_performance=service._get_document_performance(0, current_user.id),
                top_performing_documents=[],
                underperforming_documents=[],
                missing_document_types=["resume", "cover_letter"],
                portfolio_score=0.0
            )
        
        # Analyze document types
        documents_by_type = {}
        for doc in documents:
            doc_type = doc.document_type
            documents_by_type[doc_type] = documents_by_type.get(doc_type, 0) + 1
        
        # Get performance metrics for all documents
        all_suggestions = []
        for doc in documents:
            performance = service.get_document_performance_metrics(doc.id, current_user.id)
            if performance:
                # Create a simple suggestion object
                from app.schemas.document_suggestion import DocumentSuggestion
                suggestion = DocumentSuggestion(
                    document_id=doc.id,
                    document_type=doc.document_type,
                    filename=doc.original_filename,
                    relevance_score=0.5,  # Default relevance
                    suggestion_reason="Portfolio analysis",
                    performance_metrics=performance,
                    last_used=doc.last_used,
                    usage_count=doc.usage_count
                )
                all_suggestions.append(suggestion)
        
        # Sort by performance
        all_suggestions.sort(key=lambda x: x.performance_metrics.success_rate, reverse=True)
        
        top_performing = all_suggestions[:5]
        underperforming = [s for s in all_suggestions if s.performance_metrics.response_rate < 0.2][-5:]
        
        # Calculate overall performance
        if all_suggestions:
            total_apps = sum(s.performance_metrics.total_applications for s in all_suggestions)
            total_responses = sum(s.performance_metrics.total_applications * s.performance_metrics.response_rate for s in all_suggestions)
            total_interviews = sum(s.performance_metrics.total_applications * s.performance_metrics.interview_rate for s in all_suggestions)
            total_successes = sum(s.performance_metrics.total_applications * s.performance_metrics.success_rate for s in all_suggestions)
            
            from app.schemas.document_suggestion import DocumentPerformanceMetrics
            overall_performance = DocumentPerformanceMetrics(
                total_applications=total_apps,
                response_rate=total_responses / total_apps if total_apps > 0 else 0,
                interview_rate=total_interviews / total_apps if total_apps > 0 else 0,
                success_rate=total_successes / total_apps if total_apps > 0 else 0,
                avg_response_time_days=None,
                best_performing_job_types=[],
                last_30_days_usage=0
            )
        else:
            overall_performance = service._get_document_performance(0, current_user.id)
        
        # Identify missing document types
        essential_types = ["resume", "cover_letter"]
        recommended_types = ["portfolio", "reference_letter", "certificate"]
        
        missing_essential = [t for t in essential_types if t not in documents_by_type]
        missing_recommended = [t for t in recommended_types if t not in documents_by_type]
        missing_document_types = missing_essential + missing_recommended
        
        # Calculate portfolio score
        portfolio_score = 0.0
        
        # Base score for having documents
        if documents:
            portfolio_score += 0.3
        
        # Score for essential document types
        for doc_type in essential_types:
            if doc_type in documents_by_type:
                portfolio_score += 0.25
        
        # Score for recommended document types
        for doc_type in recommended_types:
            if doc_type in documents_by_type:
                portfolio_score += 0.05
        
        # Performance bonus
        if overall_performance.response_rate > 0.3:
            portfolio_score += 0.1
        if overall_performance.interview_rate > 0.2:
            portfolio_score += 0.1
        
        portfolio_score = min(portfolio_score, 1.0)
        
        return DocumentPortfolioAnalysis(
            total_documents=len(documents),
            documents_by_type=documents_by_type,
            overall_performance=overall_performance,
            top_performing_documents=top_performing,
            underperforming_documents=underperforming,
            missing_document_types=missing_document_types,
            portfolio_score=portfolio_score
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze document portfolio: {str(e)}")


@router.get("/smart-recommendations", response_model=List[SmartDocumentRecommendation])
async def get_smart_document_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get smart recommendations based on user patterns and market trends"""
    
    service = DocumentSuggestionService(db)
    
    try:
        recommendations = []
        
        # Get user's document portfolio
        from app.services.document_service import DocumentService
        doc_service = DocumentService(db)
        documents, _ = doc_service.get_user_documents(current_user.id, page=1, per_page=1000)
        
        # Get user's recent job applications
        from app.services.job_service import JobService
        job_service = JobService(db)
        recent_jobs, _ = job_service.get_jobs(current_user.id, page=1, per_page=50)
        
        # Analyze patterns and generate recommendations
        
        # 1. Document freshness recommendation
        outdated_docs = [doc for doc in documents if doc.last_used and 
                        (datetime.utcnow() - doc.last_used).days > 90]
        
        if outdated_docs:
            recommendations.append(SmartDocumentRecommendation(
                recommendation_type="maintenance",
                title="Update Outdated Documents",
                description=f"You have {len(outdated_docs)} documents that haven't been used in over 90 days",
                action_items=[
                    "Review and update resume with recent experience",
                    "Refresh cover letter templates",
                    "Update portfolio with latest projects"
                ],
                priority="medium",
                estimated_time_investment="2-3 hours",
                expected_outcome="Improved relevance and ATS compatibility"
            ))
        
        # 2. Missing document type recommendation
        doc_types = {doc.document_type for doc in documents}
        
        if "portfolio" not in doc_types and any("creative" in job.requirements.get("industry", "").lower() 
                                               for job in recent_jobs):
            recommendations.append(SmartDocumentRecommendation(
                recommendation_type="document_creation",
                title="Create Portfolio Document",
                description="Your recent job applications suggest you need a portfolio",
                action_items=[
                    "Compile your best work samples",
                    "Create a professional portfolio document",
                    "Include project descriptions and outcomes"
                ],
                priority="high",
                estimated_time_investment="4-6 hours",
                expected_outcome="Better showcase of skills for creative roles"
            ))
        
        # 3. Performance-based recommendation
        low_performing_docs = []
        for doc in documents:
            performance = service.get_document_performance_metrics(doc.id, current_user.id)
            if performance and performance.total_applications > 3 and performance.response_rate < 0.15:
                low_performing_docs.append(doc)
        
        if low_performing_docs:
            recommendations.append(SmartDocumentRecommendation(
                recommendation_type="optimization",
                title="Optimize Low-Performing Documents",
                description=f"{len(low_performing_docs)} documents have low response rates",
                action_items=[
                    "Review and rewrite key sections",
                    "Add more quantified achievements",
                    "Improve keyword optimization for ATS"
                ],
                priority="high",
                estimated_time_investment="3-4 hours per document",
                expected_outcome="Significantly improved response rates"
            ))
        
        # 4. Market trend recommendation
        if recent_jobs:
            common_skills = []
            for job in recent_jobs:
                skills = job.requirements.get("skills_required", [])
                common_skills.extend(skills)
            
            from collections import Counter
            top_skills = [skill for skill, count in Counter(common_skills).most_common(5)]
            
            if top_skills:
                recommendations.append(SmartDocumentRecommendation(
                    recommendation_type="content_optimization",
                    title="Highlight In-Demand Skills",
                    description="Emphasize skills that appear frequently in your target jobs",
                    action_items=[
                        f"Ensure {', '.join(top_skills[:3])} are prominently featured",
                        "Add specific examples of using these skills",
                        "Quantify achievements related to these skills"
                    ],
                    priority="medium",
                    estimated_time_investment="1-2 hours",
                    expected_outcome="Better alignment with market demands"
                ))
        
        return recommendations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get smart recommendations: {str(e)}")


@router.get("/template-recommendations", response_model=List[DocumentTemplateRecommendation])
async def get_document_template_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document template recommendations based on user profile and job targets"""
    
    try:
        recommendations = []
        
        # Get user's recent job applications to understand target industries/roles
        from app.services.job_service import JobService
        job_service = JobService(db)
        recent_jobs, _ = job_service.get_jobs(current_user.id, page=1, per_page=20)
        
        # Analyze target industries and experience levels
        industries = []
        experience_levels = []
        
        for job in recent_jobs:
            if job.requirements:
                industry = job.requirements.get("industry", "")
                if industry:
                    industries.append(industry.lower())
                
                exp_level = job.requirements.get("experience_level", "")
                if exp_level:
                    experience_levels.append(exp_level.lower())
        
        from collections import Counter
        top_industries = [industry for industry, _ in Counter(industries).most_common(3)]
        top_exp_levels = [level for level, _ in Counter(experience_levels).most_common(2)]
        
        # Generate template recommendations based on patterns
        
        # Tech industry templates
        if any("tech" in industry or "software" in industry for industry in top_industries):
            recommendations.append(DocumentTemplateRecommendation(
                template_type="resume",
                template_name="Technical Resume Template",
                reason="Optimized for technical roles with emphasis on skills and projects",
                target_industries=["technology", "software", "fintech"],
                target_experience_levels=["entry", "mid", "senior"],
                customization_suggestions=[
                    "Highlight programming languages and frameworks",
                    "Include GitHub links and project descriptions",
                    "Emphasize technical achievements with metrics"
                ]
            ))
        
        # Creative industry templates
        if any("creative" in industry or "design" in industry for industry in top_industries):
            recommendations.append(DocumentTemplateRecommendation(
                template_type="portfolio",
                template_name="Creative Portfolio Template",
                reason="Showcases visual work and creative projects effectively",
                target_industries=["design", "marketing", "advertising", "media"],
                target_experience_levels=["entry", "mid", "senior"],
                customization_suggestions=[
                    "Include high-quality project images",
                    "Describe creative process and outcomes",
                    "Show variety in project types and styles"
                ]
            ))
        
        # Senior level templates
        if "senior" in top_exp_levels or "lead" in top_exp_levels:
            recommendations.append(DocumentTemplateRecommendation(
                template_type="cover_letter",
                template_name="Executive Cover Letter Template",
                reason="Emphasizes leadership experience and strategic thinking",
                target_industries=["all"],
                target_experience_levels=["senior", "lead", "executive"],
                customization_suggestions=[
                    "Highlight team leadership and management experience",
                    "Include strategic initiatives and business impact",
                    "Demonstrate thought leadership and industry knowledge"
                ]
            ))
        
        # Entry level templates
        if "entry" in top_exp_levels or "junior" in top_exp_levels:
            recommendations.append(DocumentTemplateRecommendation(
                template_type="resume",
                template_name="Entry-Level Resume Template",
                reason="Maximizes impact of limited experience with focus on potential",
                target_industries=["all"],
                target_experience_levels=["entry", "junior", "graduate"],
                customization_suggestions=[
                    "Emphasize education, projects, and internships",
                    "Highlight relevant coursework and certifications",
                    "Include volunteer work and extracurricular activities"
                ]
            ))
        
        # Default recommendations if no specific patterns found
        if not recommendations:
            recommendations.extend([
                DocumentTemplateRecommendation(
                    template_type="resume",
                    template_name="Professional Resume Template",
                    reason="Clean, ATS-friendly format suitable for most industries",
                    target_industries=["all"],
                    target_experience_levels=["all"],
                    customization_suggestions=[
                        "Use consistent formatting and fonts",
                        "Include quantified achievements",
                        "Keep to 1-2 pages maximum"
                    ]
                ),
                DocumentTemplateRecommendation(
                    template_type="cover_letter",
                    template_name="Standard Cover Letter Template",
                    reason="Versatile template that can be customized for any role",
                    target_industries=["all"],
                    target_experience_levels=["all"],
                    customization_suggestions=[
                        "Personalize for each company and role",
                        "Connect your experience to job requirements",
                        "Show enthusiasm and cultural fit"
                    ]
                )
            ])
        
        return recommendations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get template recommendations: {str(e)}")