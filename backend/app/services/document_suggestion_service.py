"""
Document suggestion service for Career Co-Pilot system
Provides intelligent document recommendations based on job requirements
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from app.models.job import Job
from app.models.document import Document
from app.models.application import JobApplication
from app.models.user import User
from app.schemas.document_suggestion import (
    DocumentSuggestion, DocumentOptimizationRecommendation,
    DocumentPerformanceMetrics, JobDocumentMatch
)


class DocumentSuggestionService:
    """Service for intelligent document suggestions and optimization"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def suggest_documents_for_job(
        self, 
        job_id: int, 
        user_id: int
    ) -> List[DocumentSuggestion]:
        """Suggest relevant documents for a specific job application"""
        
        # Get the job and user's documents
        job = self.db.query(Job).filter(
            and_(Job.id == job_id, Job.user_id == user_id)
        ).first()
        
        if not job:
            return []
        
        user_documents = self.db.query(Document).filter(
            and_(
                Document.user_id == user_id,
                Document.is_current_version == "true"
            )
        ).all()
        
        if not user_documents:
            return []
        
        # Extract job requirements and keywords
        job_keywords = self._extract_job_keywords(job)
        required_skills = job.requirements.get('skills_required', [])
        experience_level = job.requirements.get('experience_level', 'mid')
        industry = job.requirements.get('industry', '')
        
        suggestions = []
        
        for document in user_documents:
            # Calculate relevance score
            relevance_score = self._calculate_document_relevance(
                document, job_keywords, required_skills, experience_level, industry
            )
            
            # Generate suggestion reason
            reason = self._generate_suggestion_reason(
                document, job, relevance_score, required_skills
            )
            
            # Get document performance metrics
            performance = self._get_document_performance(document.id, user_id)
            
            suggestion = DocumentSuggestion(
                document_id=document.id,
                document_type=document.document_type,
                filename=document.original_filename,
                relevance_score=relevance_score,
                suggestion_reason=reason,
                performance_metrics=performance,
                last_used=document.last_used,
                usage_count=document.usage_count
            )
            
            suggestions.append(suggestion)
        
        # Sort by relevance score (highest first)
        suggestions.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return suggestions
    
    def get_document_optimization_recommendations(
        self, 
        document_id: int, 
        user_id: int,
        target_job_id: Optional[int] = None
    ) -> List[DocumentOptimizationRecommendation]:
        """Get optimization recommendations for a document"""
        
        document = self.db.query(Document).filter(
            and_(Document.id == document_id, Document.user_id == user_id)
        ).first()
        
        if not document:
            return []
        
        recommendations = []
        
        # Get target job context if provided
        target_job = None
        if target_job_id:
            target_job = self.db.query(Job).filter(
                and_(Job.id == target_job_id, Job.user_id == user_id)
            ).first()
        
        # Analyze document content
        content_analysis = document.content_analysis or {}
        
        # ATS optimization recommendations
        ats_recommendations = self._generate_ats_recommendations(
            document, content_analysis, target_job
        )
        recommendations.extend(ats_recommendations)
        
        # Content optimization recommendations
        content_recommendations = self._generate_content_recommendations(
            document, content_analysis, target_job
        )
        recommendations.extend(content_recommendations)
        
        # Performance-based recommendations
        performance_recommendations = self._generate_performance_recommendations(
            document, user_id
        )
        recommendations.extend(performance_recommendations)
        
        # Sort by priority (high to low)
        priority_order = {"high": 3, "medium": 2, "low": 1}
        recommendations.sort(
            key=lambda x: priority_order.get(x.priority, 0), 
            reverse=True
        )
        
        return recommendations
    
    def get_document_performance_metrics(
        self, 
        document_id: int, 
        user_id: int
    ) -> Optional[DocumentPerformanceMetrics]:
        """Get comprehensive performance metrics for a document"""
        
        document = self.db.query(Document).filter(
            and_(Document.id == document_id, Document.user_id == user_id)
        ).first()
        
        if not document:
            return None
        
        return self._get_document_performance(document_id, user_id)
    
    def get_job_document_matches(
        self, 
        user_id: int, 
        limit: int = 10
    ) -> List[JobDocumentMatch]:
        """Get jobs that best match user's documents"""
        
        # Get user's current documents
        user_documents = self.db.query(Document).filter(
            and_(
                Document.user_id == user_id,
                Document.is_current_version == "true"
            )
        ).all()
        
        if not user_documents:
            return []
        
        # Get user's jobs that haven't been applied to yet
        available_jobs = self.db.query(Job).filter(
            and_(
                Job.user_id == user_id,
                Job.status == "not_applied"
            )
        ).order_by(desc(Job.recommendation_score)).limit(limit * 2).all()
        
        matches = []
        
        for job in available_jobs:
            # Find best matching documents for this job
            job_keywords = self._extract_job_keywords(job)
            required_skills = job.requirements.get('skills_required', [])
            
            best_documents = []
            for document in user_documents:
                relevance_score = self._calculate_document_relevance(
                    document, job_keywords, required_skills, 
                    job.requirements.get('experience_level', 'mid'),
                    job.requirements.get('industry', '')
                )
                
                if relevance_score > 0.3:  # Only include reasonably relevant documents
                    best_documents.append({
                        'document_id': document.id,
                        'document_type': document.document_type,
                        'filename': document.original_filename,
                        'relevance_score': relevance_score
                    })
            
            if best_documents:
                # Sort documents by relevance
                best_documents.sort(key=lambda x: x['relevance_score'], reverse=True)
                
                # Calculate overall match score
                overall_score = sum(doc['relevance_score'] for doc in best_documents[:3]) / 3
                
                match = JobDocumentMatch(
                    job_id=job.id,
                    job_title=job.title,
                    company=job.company,
                    overall_match_score=overall_score,
                    matching_documents=best_documents[:5],  # Top 5 matching documents
                    missing_document_types=self._identify_missing_document_types(
                        job, [doc['document_type'] for doc in best_documents]
                    )
                )
                
                matches.append(match)
        
        # Sort by overall match score
        matches.sort(key=lambda x: x.overall_match_score, reverse=True)
        
        return matches[:limit]
    
    def _extract_job_keywords(self, job: Job) -> List[str]:
        """Extract relevant keywords from job description and requirements"""
        keywords = []
        
        # Extract from title
        title_words = re.findall(r'\b\w+\b', job.title.lower())
        keywords.extend(title_words)
        
        # Extract from description
        if job.description:
            # Simple keyword extraction - in production, use NLP
            desc_words = re.findall(r'\b\w{3,}\b', job.description.lower())
            keywords.extend(desc_words)
        
        # Extract from requirements
        if job.requirements:
            skills = job.requirements.get('skills_required', [])
            keywords.extend([skill.lower() for skill in skills])
            
            # Add other requirement fields
            for key, value in job.requirements.items():
                if isinstance(value, str):
                    keywords.append(value.lower())
                elif isinstance(value, list):
                    keywords.extend([str(v).lower() for v in value])
        
        # Remove duplicates and common words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = list(set([kw for kw in keywords if kw not in stop_words and len(kw) > 2]))
        
        return keywords
    
    def _calculate_document_relevance(
        self, 
        document: Document, 
        job_keywords: List[str],
        required_skills: List[str],
        experience_level: str,
        industry: str
    ) -> float:
        """Calculate how relevant a document is for a specific job"""
        
        score = 0.0
        
        # Base score for document type relevance
        type_scores = {
            'resume': 0.8,
            'cover_letter': 0.6,
            'portfolio': 0.7,
            'certificate': 0.5,
            'transcript': 0.3,
            'reference_letter': 0.4,
            'writing_sample': 0.5,
            'project_documentation': 0.6
        }
        score += type_scores.get(document.document_type, 0.3)
        
        # Analyze document content if available
        content_analysis = document.content_analysis or {}
        
        if content_analysis:
            # Skills matching
            doc_skills = content_analysis.get('analysis', {}).get('skills_mentioned', [])
            if doc_skills and required_skills:
                skill_matches = len(set(doc_skills) & set(required_skills))
                skill_score = min(skill_matches / len(required_skills), 1.0) * 0.4
                score += skill_score
            
            # Keyword matching
            doc_keywords = content_analysis.get('analysis', {}).get('keywords', [])
            if doc_keywords and job_keywords:
                keyword_matches = len(set(doc_keywords) & set(job_keywords))
                keyword_score = min(keyword_matches / len(job_keywords), 1.0) * 0.3
                score += keyword_score
            
            # Experience level matching
            doc_experience = content_analysis.get('analysis', {}).get('experience_years', 0)
            if doc_experience > 0:
                exp_level_map = {'entry': 2, 'mid': 5, 'senior': 8, 'lead': 12}
                target_exp = exp_level_map.get(experience_level, 5)
                exp_diff = abs(doc_experience - target_exp)
                exp_score = max(0, (5 - exp_diff) / 5) * 0.2
                score += exp_score
        
        # Performance bonus
        if document.usage_count > 0:
            # Documents that have been used successfully get a small bonus
            performance_bonus = min(document.usage_count / 10, 0.1)
            score += performance_bonus
        
        # Recency bonus
        if document.last_used:
            days_since_used = (datetime.utcnow() - document.last_used).days
            if days_since_used < 30:
                recency_bonus = (30 - days_since_used) / 30 * 0.1
                score += recency_bonus
        
        # Tag matching
        if document.tags and industry:
            if industry.lower() in [tag.lower() for tag in document.tags]:
                score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _generate_suggestion_reason(
        self, 
        document: Document, 
        job: Job, 
        relevance_score: float,
        required_skills: List[str]
    ) -> str:
        """Generate a human-readable reason for the document suggestion"""
        
        reasons = []
        
        # Document type relevance
        if document.document_type == 'resume':
            reasons.append("Essential for job applications")
        elif document.document_type == 'cover_letter':
            reasons.append("Helps personalize your application")
        elif document.document_type == 'portfolio':
            reasons.append("Showcases your work and skills")
        
        # Skills matching
        content_analysis = document.content_analysis or {}
        doc_skills = content_analysis.get('analysis', {}).get('skills_mentioned', [])
        
        if doc_skills and required_skills:
            matching_skills = set(doc_skills) & set(required_skills)
            if matching_skills:
                skill_list = ', '.join(list(matching_skills)[:3])
                reasons.append(f"Contains relevant skills: {skill_list}")
        
        # Performance history
        if document.usage_count > 0:
            reasons.append(f"Previously used in {document.usage_count} applications")
        
        # Recent usage
        if document.last_used:
            days_ago = (datetime.utcnow() - document.last_used).days
            if days_ago < 7:
                reasons.append("Recently used document")
        
        # High relevance score
        if relevance_score > 0.8:
            reasons.append("High relevance match for this position")
        
        return "; ".join(reasons) if reasons else "General document relevance"
    
    def _get_document_performance(
        self, 
        document_id: int, 
        user_id: int
    ) -> DocumentPerformanceMetrics:
        """Calculate performance metrics for a document"""
        
        # Get applications that used this document
        applications = self.db.query(JobApplication).filter(
            JobApplication.user_id == user_id
        ).all()
        
        # Filter applications that contain this document
        relevant_applications = []
        for app in applications:
            for doc in app.documents:
                if doc.get('document_id') == document_id:
                    relevant_applications.append(app)
                    break
        
        total_applications = len(relevant_applications)
        
        if total_applications == 0:
            return DocumentPerformanceMetrics(
                total_applications=0,
                response_rate=0.0,
                interview_rate=0.0,
                success_rate=0.0,
                avg_response_time_days=None,
                best_performing_job_types=[],
                last_30_days_usage=0
            )
        
        # Calculate metrics
        responses = len([app for app in relevant_applications 
                        if app.status not in ['applied', 'under_review']])
        interviews = len([app for app in relevant_applications 
                         if 'interview' in app.status.lower()])
        successes = len([app for app in relevant_applications 
                        if app.status in ['offer_received', 'offer_accepted']])
        
        response_rate = responses / total_applications
        interview_rate = interviews / total_applications
        success_rate = successes / total_applications
        
        # Calculate average response time
        response_times = []
        for app in relevant_applications:
            if app.response_date and app.applied_at:
                days = (app.response_date - app.applied_at).days
                response_times.append(days)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else None
        
        # Find best performing job types
        job_types = []
        for app in relevant_applications:
            if app.job and app.job.requirements:
                job_type = app.job.requirements.get('employment_type', 'unknown')
                if app.status in ['interview_scheduled', 'interviewed', 'offer_received']:
                    job_types.append(job_type)
        
        best_job_types = [item[0] for item in Counter(job_types).most_common(3)]
        
        # Last 30 days usage
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_usage = len([app for app in relevant_applications 
                           if app.applied_at >= thirty_days_ago])
        
        return DocumentPerformanceMetrics(
            total_applications=total_applications,
            response_rate=response_rate,
            interview_rate=interview_rate,
            success_rate=success_rate,
            avg_response_time_days=avg_response_time,
            best_performing_job_types=best_job_types,
            last_30_days_usage=recent_usage
        )
    
    def _generate_ats_recommendations(
        self, 
        document: Document, 
        content_analysis: Dict[str, Any],
        target_job: Optional[Job] = None
    ) -> List[DocumentOptimizationRecommendation]:
        """Generate ATS (Applicant Tracking System) optimization recommendations"""
        
        recommendations = []
        
        # ATS score check
        ats_score = content_analysis.get('ats_score', 0)
        if ats_score < 70:
            recommendations.append(DocumentOptimizationRecommendation(
                type="ats_optimization",
                title="Improve ATS Compatibility",
                description=f"Current ATS score is {ats_score}%. Consider using standard section headings, avoiding graphics, and including more relevant keywords.",
                priority="high",
                estimated_impact="Increases chance of passing initial screening by 40%"
            ))
        
        # Keyword density
        if target_job and target_job.requirements:
            required_skills = target_job.requirements.get('skills_required', [])
            doc_skills = content_analysis.get('analysis', {}).get('skills_mentioned', [])
            
            missing_skills = set(required_skills) - set(doc_skills)
            if missing_skills and len(missing_skills) > 2:
                skill_list = ', '.join(list(missing_skills)[:5])
                recommendations.append(DocumentOptimizationRecommendation(
                    type="keyword_optimization",
                    title="Add Missing Keywords",
                    description=f"Include these relevant skills: {skill_list}",
                    priority="medium",
                    estimated_impact="Improves keyword matching by 25%"
                ))
        
        # File format recommendation
        if document.mime_type not in ['application/pdf', 'application/msword']:
            recommendations.append(DocumentOptimizationRecommendation(
                type="format_optimization",
                title="Use ATS-Friendly Format",
                description="Convert to PDF or Word format for better ATS compatibility",
                priority="medium",
                estimated_impact="Ensures document can be properly parsed"
            ))
        
        return recommendations
    
    def _generate_content_recommendations(
        self, 
        document: Document, 
        content_analysis: Dict[str, Any],
        target_job: Optional[Job] = None
    ) -> List[DocumentOptimizationRecommendation]:
        """Generate content optimization recommendations"""
        
        recommendations = []
        
        # Readability score
        readability_score = content_analysis.get('readability_score', 0)
        if readability_score < 80:
            recommendations.append(DocumentOptimizationRecommendation(
                type="content_optimization",
                title="Improve Readability",
                description=f"Current readability score is {readability_score}%. Use shorter sentences and clearer language.",
                priority="low",
                estimated_impact="Makes document easier to scan and understand"
            ))
        
        # Quantified achievements
        achievements = content_analysis.get('analysis', {}).get('quantified_achievements', 0)
        if achievements < 3:
            recommendations.append(DocumentOptimizationRecommendation(
                type="content_optimization",
                title="Add Quantified Achievements",
                description="Include more specific numbers and metrics to demonstrate impact",
                priority="high",
                estimated_impact="Quantified results are 40% more compelling to recruiters"
            ))
        
        # Document length
        if document.document_type == 'resume':
            word_count = len(content_analysis.get('extracted_text', '').split())
            if word_count > 800:
                recommendations.append(DocumentOptimizationRecommendation(
                    type="content_optimization",
                    title="Reduce Document Length",
                    description="Resume is too long. Aim for 1-2 pages (400-600 words)",
                    priority="medium",
                    estimated_impact="Shorter resumes get more attention from recruiters"
                ))
        
        return recommendations
    
    def _generate_performance_recommendations(
        self, 
        document: Document, 
        user_id: int
    ) -> List[DocumentOptimizationRecommendation]:
        """Generate recommendations based on document performance history"""
        
        recommendations = []
        
        # Low usage recommendation
        if document.usage_count == 0:
            recommendations.append(DocumentOptimizationRecommendation(
                type="usage_optimization",
                title="Document Not Yet Used",
                description="This document hasn't been used in any applications yet. Consider reviewing and updating it.",
                priority="low",
                estimated_impact="Ensures document is application-ready"
            ))
        
        # Performance comparison
        performance = self._get_document_performance(document.id, user_id)
        
        if performance.total_applications > 5:
            if performance.response_rate < 0.2:
                recommendations.append(DocumentOptimizationRecommendation(
                    type="performance_optimization",
                    title="Low Response Rate",
                    description=f"This document has a {performance.response_rate:.1%} response rate. Consider major revisions.",
                    priority="high",
                    estimated_impact="Could significantly improve application success"
                ))
            elif performance.interview_rate < 0.1:
                recommendations.append(DocumentOptimizationRecommendation(
                    type="performance_optimization",
                    title="Low Interview Rate",
                    description=f"This document has a {performance.interview_rate:.1%} interview rate. Focus on highlighting achievements.",
                    priority="medium",
                    estimated_impact="Better achievement highlighting improves interview chances"
                ))
        
        # Outdated document
        if document.last_used:
            days_since_used = (datetime.utcnow() - document.last_used).days
            if days_since_used > 90:
                recommendations.append(DocumentOptimizationRecommendation(
                    type="maintenance",
                    title="Update Outdated Document",
                    description=f"Document hasn't been used in {days_since_used} days. Consider updating with recent experience.",
                    priority="medium",
                    estimated_impact="Fresh content shows current relevance"
                ))
        
        return recommendations
    
    def _identify_missing_document_types(
        self, 
        job: Job, 
        available_types: List[str]
    ) -> List[str]:
        """Identify document types that might be missing for a job application"""
        
        missing_types = []
        
        # Essential documents
        if 'resume' not in available_types:
            missing_types.append('resume')
        
        # Industry-specific recommendations
        industry = job.requirements.get('industry', '').lower()
        
        if 'creative' in industry or 'design' in industry:
            if 'portfolio' not in available_types:
                missing_types.append('portfolio')
        
        if 'academic' in industry or 'research' in industry:
            if 'transcript' not in available_types:
                missing_types.append('transcript')
        
        # Experience level recommendations
        experience_level = job.requirements.get('experience_level', '').lower()
        
        if experience_level in ['senior', 'lead', 'principal']:
            if 'reference_letter' not in available_types:
                missing_types.append('reference_letter')
        
        # Job type recommendations
        employment_type = job.requirements.get('employment_type', '').lower()
        
        if 'contract' in employment_type or 'freelance' in employment_type:
            if 'portfolio' not in available_types:
                missing_types.append('portfolio')
        
        return missing_types