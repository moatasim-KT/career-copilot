"""
Document suggestion schemas for Career Co-Pilot system
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentPerformanceMetrics(BaseModel):
    """Schema for document performance metrics"""
    total_applications: int = Field(..., description="Total applications using this document")
    response_rate: float = Field(..., ge=0, le=1, description="Rate of responses received")
    interview_rate: float = Field(..., ge=0, le=1, description="Rate of interviews obtained")
    success_rate: float = Field(..., ge=0, le=1, description="Rate of successful outcomes")
    avg_response_time_days: Optional[float] = Field(None, description="Average response time in days")
    best_performing_job_types: List[str] = Field(default_factory=list, description="Job types where document performs best")
    last_30_days_usage: int = Field(..., description="Usage count in last 30 days")


class DocumentSuggestion(BaseModel):
    """Schema for document suggestions"""
    document_id: int = Field(..., description="Document ID")
    document_type: str = Field(..., description="Type of document")
    filename: str = Field(..., description="Document filename")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance score for the job")
    suggestion_reason: str = Field(..., description="Human-readable reason for suggestion")
    performance_metrics: DocumentPerformanceMetrics = Field(..., description="Performance metrics")
    last_used: Optional[datetime] = Field(None, description="When document was last used")
    usage_count: int = Field(..., description="Total usage count")


class DocumentOptimizationRecommendation(BaseModel):
    """Schema for document optimization recommendations"""
    type: str = Field(..., description="Type of recommendation")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed recommendation description")
    priority: str = Field(..., description="Priority level: high, medium, low")
    estimated_impact: str = Field(..., description="Expected impact of implementing recommendation")


class JobDocumentMatch(BaseModel):
    """Schema for job-document matching results"""
    job_id: int = Field(..., description="Job ID")
    job_title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    overall_match_score: float = Field(..., ge=0, le=1, description="Overall match score")
    matching_documents: List[Dict[str, Any]] = Field(default_factory=list, description="List of matching documents")
    missing_document_types: List[str] = Field(default_factory=list, description="Document types that might be missing")


class DocumentSuggestionRequest(BaseModel):
    """Schema for requesting document suggestions"""
    job_id: int = Field(..., description="Job ID to get suggestions for")


class DocumentOptimizationRequest(BaseModel):
    """Schema for requesting document optimization recommendations"""
    document_id: int = Field(..., description="Document ID to optimize")
    target_job_id: Optional[int] = Field(None, description="Optional target job for context")


class DocumentPerformanceRequest(BaseModel):
    """Schema for requesting document performance metrics"""
    document_id: int = Field(..., description="Document ID to analyze")


class JobDocumentMatchRequest(BaseModel):
    """Schema for requesting job-document matches"""
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of matches to return")


class DocumentSuggestionResponse(BaseModel):
    """Response schema for document suggestions"""
    job_id: int = Field(..., description="Job ID")
    job_title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    suggestions: List[DocumentSuggestion] = Field(default_factory=list, description="Document suggestions")
    total_suggestions: int = Field(..., description="Total number of suggestions")


class DocumentOptimizationResponse(BaseModel):
    """Response schema for document optimization recommendations"""
    document_id: int = Field(..., description="Document ID")
    document_type: str = Field(..., description="Document type")
    filename: str = Field(..., description="Document filename")
    recommendations: List[DocumentOptimizationRecommendation] = Field(default_factory=list, description="Optimization recommendations")
    total_recommendations: int = Field(..., description="Total number of recommendations")


class DocumentPerformanceResponse(BaseModel):
    """Response schema for document performance metrics"""
    document_id: int = Field(..., description="Document ID")
    document_type: str = Field(..., description="Document type")
    filename: str = Field(..., description="Document filename")
    performance_metrics: DocumentPerformanceMetrics = Field(..., description="Performance metrics")


class JobDocumentMatchResponse(BaseModel):
    """Response schema for job-document matches"""
    matches: List[JobDocumentMatch] = Field(default_factory=list, description="Job-document matches")
    total_matches: int = Field(..., description="Total number of matches")


class BulkDocumentAnalysisRequest(BaseModel):
    """Schema for bulk document analysis request"""
    document_ids: List[int] = Field(..., description="List of document IDs to analyze")
    include_optimization: bool = Field(default=True, description="Include optimization recommendations")
    include_performance: bool = Field(default=True, description="Include performance metrics")


class BulkDocumentAnalysisResponse(BaseModel):
    """Response schema for bulk document analysis"""
    analyses: List[Dict[str, Any]] = Field(default_factory=list, description="Document analyses")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Summary statistics")


class DocumentUsageInsight(BaseModel):
    """Schema for document usage insights"""
    document_id: int = Field(..., description="Document ID")
    document_type: str = Field(..., description="Document type")
    filename: str = Field(..., description="Document filename")
    usage_trend: str = Field(..., description="Usage trend: increasing, decreasing, stable")
    success_trend: str = Field(..., description="Success trend: improving, declining, stable")
    recommendations: List[str] = Field(default_factory=list, description="Usage recommendations")


class DocumentPortfolioAnalysis(BaseModel):
    """Schema for analyzing user's entire document portfolio"""
    total_documents: int = Field(..., description="Total number of documents")
    documents_by_type: Dict[str, int] = Field(default_factory=dict, description="Document count by type")
    overall_performance: DocumentPerformanceMetrics = Field(..., description="Overall portfolio performance")
    top_performing_documents: List[DocumentSuggestion] = Field(default_factory=list, description="Top performing documents")
    underperforming_documents: List[DocumentSuggestion] = Field(default_factory=list, description="Documents needing attention")
    missing_document_types: List[str] = Field(default_factory=list, description="Recommended document types to add")
    portfolio_score: float = Field(..., ge=0, le=1, description="Overall portfolio completeness score")


class SmartDocumentRecommendation(BaseModel):
    """Schema for smart document recommendations based on user patterns"""
    recommendation_type: str = Field(..., description="Type of recommendation")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    action_items: List[str] = Field(default_factory=list, description="Specific action items")
    priority: str = Field(..., description="Priority level")
    estimated_time_investment: str = Field(..., description="Estimated time to implement")
    expected_outcome: str = Field(..., description="Expected outcome")


class DocumentTemplateRecommendation(BaseModel):
    """Schema for document template recommendations"""
    template_type: str = Field(..., description="Type of template recommended")
    template_name: str = Field(..., description="Template name")
    reason: str = Field(..., description="Reason for recommendation")
    target_industries: List[str] = Field(default_factory=list, description="Industries this template works well for")
    target_experience_levels: List[str] = Field(default_factory=list, description="Experience levels this template suits")
    customization_suggestions: List[str] = Field(default_factory=list, description="Customization suggestions")