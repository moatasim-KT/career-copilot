"""
Intelligent document suggestions and optimization service
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from collections import Counter

from app.models.user import User
from app.models.job import Job
from app.models.document import Document
from app.models.application import JobApplication


class DocumentIntelligenceService:
    """Service for intelligent document suggestions and performance tracking"""
    
    def suggest_documents_for_job(self, db: Session, user_id: int, job_id: int) -> Dict:
        """Analyze job requirements and suggest relevant documents"""
        job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
        if not job:
            return {'error': 'Job not found'}
        
        # Get user's documents
        documents = db.query(Document).filter(
            Document.user_id == user_id,
            Document.is_current_version == "true"
        ).all()
        
        if not documents:
            return {'suggestions': [], 'message': 'No documents available'}
        
        # Extract job requirements
        requirements = job.requirements or {}
        required_skills = set(s.lower() for s in requirements.get('skills_required', []))
        job_level = requirements.get('experience_level', 'mid')
        
        # Score each document
        document_scores = []
        for doc in documents:
            score = self._calculate_document_relevance(doc, required_skills, job_level)
            if score > 0:
                document_scores.append({
                    'document_id': doc.id,
                    'filename': doc.original_filename,
                    'type': doc.document_type,
                    'relevance_score': score,
                    'reason': self._generate_suggestion_reason(doc, required_skills, job_level),
                    'last_used': doc.last_used.isoformat() if doc.last_used else None,
                    'usage_count': doc.usage_count
                })
        
        # Sort by relevance score
        document_scores.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return {
            'job_title': job.title,
            'company': job.company,
            'suggestions': document_scores[:5],
            'total_documents_analyzed': len(documents)
        }
    
    def _calculate_document_relevance(
        self, 
        document: Document, 
        required_skills: set, 
        job_level: str
    ) -> float:
        """Calculate document relevance score for a job"""
        score = 0.0
        
        # Base score by document type
        if document.document_type == 'resume':
            score += 50
        elif document.document_type == 'cover_letter':
            score += 40
        elif document.document_type == 'portfolio':
            score += 30
        
        # Analyze document content
        content_analysis = document.content_analysis or {}
        doc_skills = set(s.lower() for s in content_analysis.get('analysis', {}).get('skills_mentioned', []))
        
        # Skill matching bonus
        if doc_skills and required_skills:
            matching_skills = doc_skills.intersection(required_skills)
            skill_match_ratio = len(matching_skills) / len(required_skills) if required_skills else 0
            score += skill_match_ratio * 30
        
        # Usage history bonus (documents that performed well)
        if document.usage_count > 0:
            score += min(document.usage_count * 2, 10)
        
        # Recency bonus
        if document.last_used:
            days_since_use = (datetime.now() - document.last_used).days
            if days_since_use < 30:
                score += 5
        
        # Tag matching
        doc_tags = set(t.lower() for t in document.tags)
        if job_level in doc_tags:
            score += 10
        
        return round(score, 2)
    
    def _generate_suggestion_reason(
        self, 
        document: Document, 
        required_skills: set, 
        job_level: str
    ) -> str:
        """Generate human-readable reason for suggestion"""
        reasons = []
        
        content_analysis = document.content_analysis or {}
        doc_skills = set(s.lower() for s in content_analysis.get('analysis', {}).get('skills_mentioned', []))
        
        if doc_skills and required_skills:
            matching_skills = doc_skills.intersection(required_skills)
            if matching_skills:
                reasons.append(f"Highlights {len(matching_skills)} required skills")
        
        if document.usage_count > 5:
            reasons.append(f"High success rate ({document.usage_count} applications)")
        
        if document.document_type == 'resume':
            reasons.append("Essential application document")
        
        return '; '.join(reasons) if reasons else "Relevant to this position"
    
    def generate_optimization_recommendations(
        self, 
        db: Session, 
        document_id: int, 
        user_id: int,
        job_id: Optional[int] = None
    ) -> Dict:
        """Generate document optimization recommendations"""
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == user_id
        ).first()
        
        if not document:
            return {'error': 'Document not found'}
        
        recommendations = []
        
        # General recommendations
        content_analysis = document.content_analysis or {}
        ats_score = content_analysis.get('ats_score', 0)
        
        if ats_score < 70:
            recommendations.append({
                'priority': 'high',
                'category': 'ATS Optimization',
                'suggestion': 'Add more industry keywords to improve ATS compatibility',
                'impact': 'Increases chance of passing automated screening'
            })
        
        # Check for quantified achievements
        if document.document_type == 'resume':
            recommendations.append({
                'priority': 'medium',
                'category': 'Content Quality',
                'suggestion': 'Include quantified achievements (e.g., "Increased efficiency by 30%")',
                'impact': 'Makes accomplishments more concrete and impressive'
            })
        
        # Job-specific recommendations
        if job_id:
            job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
            if job:
                required_skills = job.requirements.get('skills_required', [])
                doc_skills = content_analysis.get('analysis', {}).get('skills_mentioned', [])
                
                missing_skills = set(s.lower() for s in required_skills) - set(s.lower() for s in doc_skills)
                if missing_skills:
                    recommendations.append({
                        'priority': 'high',
                        'category': 'Skill Alignment',
                        'suggestion': f'Add these required skills: {", ".join(list(missing_skills)[:3])}',
                        'impact': 'Better alignment with job requirements'
                    })
        
        # Version control recommendation
        if document.usage_count > 10 and document.version == 1:
            recommendations.append({
                'priority': 'low',
                'category': 'Version Control',
                'suggestion': 'Consider creating a new version with updated information',
                'impact': 'Keep document fresh and relevant'
            })
        
        return {
            'document_id': document_id,
            'document_type': document.document_type,
            'current_ats_score': ats_score,
            'recommendations': recommendations,
            'total_recommendations': len(recommendations)
        }
    
    def track_document_performance(self, db: Session, user_id: int) -> Dict:
        """Track document performance across applications"""
        documents = db.query(Document).filter(
            Document.user_id == user_id,
            Document.usage_count > 0
        ).all()
        
        if not documents:
            return {'message': 'No document usage data available'}
        
        performance_data = []
        
        for doc in documents:
            # Find applications using this document
            applications = db.query(JobApplication).filter(
                JobApplication.user_id == user_id
            ).all()
            
            # Count successful applications (interviews, offers)
            successful_apps = 0
            total_apps = 0
            
            for app in applications:
                if app.documents:
                    doc_ids = [d.get('document_id') for d in app.documents if isinstance(d, dict)]
                    if doc.id in doc_ids:
                        total_apps += 1
                        if app.status in ['interview_scheduled', 'interviewed', 'offer_received']:
                            successful_apps += 1
            
            success_rate = round(successful_apps / total_apps, 3) if total_apps > 0 else 0
            
            performance_data.append({
                'document_id': doc.id,
                'filename': doc.original_filename,
                'type': doc.document_type,
                'total_applications': total_apps,
                'successful_applications': successful_apps,
                'success_rate': success_rate,
                'last_used': doc.last_used.isoformat() if doc.last_used else None
            })
        
        # Sort by success rate
        performance_data.sort(key=lambda x: x['success_rate'], reverse=True)
        
        # Calculate overall statistics
        total_apps = sum(d['total_applications'] for d in performance_data)
        total_successful = sum(d['successful_applications'] for d in performance_data)
        overall_success_rate = round(total_successful / total_apps, 3) if total_apps > 0 else 0
        
        return {
            'document_performance': performance_data,
            'overall_statistics': {
                'total_documents_tracked': len(performance_data),
                'total_applications': total_apps,
                'successful_applications': total_successful,
                'overall_success_rate': overall_success_rate
            },
            'top_performing_document': performance_data[0] if performance_data else None
        }
    
    def get_document_insights(self, db: Session, user_id: int) -> Dict:
        """Get comprehensive document insights and recommendations"""
        # Get all user documents
        documents = db.query(Document).filter(
            Document.user_id == user_id
        ).all()
        
        if not documents:
            return {'message': 'No documents found'}
        
        # Analyze document portfolio
        doc_types = Counter(doc.document_type for doc in documents)
        current_versions = [doc for doc in documents if doc.is_current_version == "true"]
        
        insights = {
            'portfolio_summary': {
                'total_documents': len(documents),
                'current_versions': len(current_versions),
                'document_types': dict(doc_types),
                'total_usage': sum(doc.usage_count for doc in documents)
            },
            'recommendations': []
        }
        
        # Generate portfolio recommendations
        if doc_types.get('resume', 0) == 0:
            insights['recommendations'].append({
                'priority': 'critical',
                'message': 'Upload a resume to start applying for jobs'
            })
        
        if doc_types.get('cover_letter', 0) == 0:
            insights['recommendations'].append({
                'priority': 'high',
                'message': 'Add a cover letter template to personalize applications'
            })
        
        # Check for outdated documents
        outdated_docs = [
            doc for doc in current_versions 
            if doc.updated_at < datetime.now() - timedelta(days=180)
        ]
        
        if outdated_docs:
            insights['recommendations'].append({
                'priority': 'medium',
                'message': f'{len(outdated_docs)} documents haven\'t been updated in 6+ months'
            })
        
        # Performance insights
        performance = self.track_document_performance(db, user_id)
        if 'overall_statistics' in performance:
            insights['performance_summary'] = performance['overall_statistics']
        
        return insights


document_intelligence_service = DocumentIntelligenceService()