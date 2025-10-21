"""
Simple Contract Analysis Service
A working implementation that provides actual analysis results using Groq.
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from groq import Groq

from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class SimpleContractAnalysisService:
    """Simple working job application tracking service."""
    
    def __init__(self):
        self.groq_client = None
        self._initialize_groq()
    
    def _initialize_groq(self):
        """Initialize Groq client."""
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            try:
                self.groq_client = Groq(api_key=groq_api_key)
                logger.info("Groq client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.groq_client = None
        else:
            logger.warning("GROQ_API_KEY not found")
    
    def is_available(self) -> bool:
        """Check if the service is available."""
        return self.groq_client is not None
    
    async def analyze_contract_simple(self, contract_text: str, filename: str) -> Dict[str, Any]:
        """Perform simple job application tracking using Groq."""
        
        if not self.is_available():
            return self._create_fallback_response(filename, "AI service not available")
        
        try:
            # Create analysis prompt
            prompt = f"""
You are a legal contract analyst. Analyze the following contract and provide a structured response.

Contract filename: {filename}
Contract text:
{contract_text[:3000]}

Please analyze this contract and respond with a JSON object containing:
1. risky_clauses: List of potentially risky clauses (each with "clause", "risk_level", "explanation")
2. overall_risk_score: Number between 0.0 and 1.0 (0 = low risk, 1 = high risk)
3. key_findings: List of important findings
4. recommendations: List of recommendations for negotiation

Focus on common contract risks like:
- Unfavorable termination clauses
- Liability limitations
- Payment terms
- Intellectual property rights
- Confidentiality obligations
- Indemnification clauses

Respond only with valid JSON.
"""

            # Call Groq API
            start_time = time.time()
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a legal contract analyst. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
                timeout=30
            )
            
            processing_time = time.time() - start_time
            
            if response and response.choices:
                content = response.choices[0].message.content
                
                try:
                    # Parse JSON response
                    analysis_data = json.loads(content)
                    
                    # Extract and format results
                    risky_clauses = analysis_data.get("risky_clauses", [])
                    overall_risk_score = float(analysis_data.get("overall_risk_score", 0.3))
                    key_findings = analysis_data.get("key_findings", [])
                    recommendations = analysis_data.get("recommendations", [])
                    
                    # Format risky clauses for API model
                    formatted_clauses = []
                    for i, clause in enumerate(risky_clauses[:5], 1):  # Limit to 5 clauses
                        if isinstance(clause, dict):
                            risk_level = clause.get("risk_level", "medium")
                            # Capitalize risk level for validation
                            if risk_level.lower() == "low":
                                risk_level = "Low"
                            elif risk_level.lower() == "high":
                                risk_level = "High"
                            else:
                                risk_level = "Medium"
                            
                            formatted_clauses.append({
                                "clause_text": clause.get("clause", "Contract term requires review"),
                                "risk_explanation": clause.get("explanation", "This clause may present risks"),
                                "risk_level": risk_level,
                                "precedent_reference": None,
                                "clause_index": i
                            })
                    
                    # Create suggested redlines for API model
                    suggested_redlines = []
                    for i, rec in enumerate(recommendations[:3], 1):  # Limit to 3 redlines
                        suggested_redlines.append({
                            "original_clause": "Original contract clause",
                            "suggested_redline": str(rec),
                            "risk_explanation": "Based on risk analysis",
                            "clause_index": i,
                            "change_rationale": "Recommended to reduce contract risk",
                            "risk_mitigated": True
                        })
                    
                    # Create email draft
                    email_draft = self._create_email_draft(filename, formatted_clauses, overall_risk_score)
                    
                    return {
                        "risky_clauses": formatted_clauses,
                        "suggested_redlines": suggested_redlines,
                        "email_draft": email_draft,
                        "processing_time": processing_time,
                        "status": "completed",
                        "overall_risk_score": overall_risk_score,
                        "warnings": [],
                        "errors": [],
                        "analysis_timestamp": datetime.utcnow().isoformat(),
                        "key_findings": key_findings,
                        "ai_model": "llama-3.1-8b-instant"
                    }
                    
                except json.JSONDecodeError:
                    # If JSON parsing fails, create a basic response
                    logger.warning("Failed to parse AI response as JSON, creating basic analysis")
                    return self._create_basic_analysis_from_text(content, filename, processing_time)
            
            else:
                return self._create_fallback_response(filename, "No response from AI service")
                
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return self._create_fallback_response(filename, f"Analysis error: {str(e)}")
    
    def _create_basic_analysis_from_text(self, ai_response: str, filename: str, processing_time: float) -> Dict[str, Any]:
        """Create basic analysis from AI text response."""
        
        # Extract key information from text response
        risk_keywords = ["risk", "liability", "termination", "penalty", "indemnif", "confidential"]
        found_risks = [word for word in risk_keywords if word.lower() in ai_response.lower()]
        
        risk_score = min(len(found_risks) * 0.15, 0.8)  # Scale based on found risks
        
        risky_clauses = [{
            "clause_text": "Contract contains standard terms that may require review",
            "risk_explanation": "AI analysis identified potential areas of concern",
            "risk_level": "Medium",
            "precedent_reference": None,
            "clause_index": 1
        }]
        
        suggested_redlines = [{
            "original_clause": "Standard contract terms",
            "suggested_redline": "Consider negotiating key terms based on your requirements",
            "risk_explanation": "General contract review recommendation",
            "clause_index": 1,
            "change_rationale": "Recommended to reduce contract risk",
            "risk_mitigated": True
        }]
        
        email_draft = self._create_email_draft(filename, risky_clauses, risk_score)
        
        return {
            "risky_clauses": risky_clauses,
            "suggested_redlines": suggested_redlines,
            "email_draft": email_draft,
            "processing_time": processing_time,
            "status": "completed",
            "overall_risk_score": risk_score,
            "warnings": ["AI response was not in expected format"],
            "errors": [],
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "ai_model": "llama-3.1-8b-instant"
        }
    
    def _create_fallback_response(self, filename: str, error_msg: str) -> Dict[str, Any]:
        """Create fallback response when AI analysis fails."""
        
        risky_clauses = [{
            "clause_text": "Unable to perform detailed analysis due to technical limitations",
            "risk_explanation": "Please review contract manually or try again later",
            "risk_level": "Medium",
            "precedent_reference": None,
            "clause_index": 1
        }]
        
        suggested_redlines = [{
            "original_clause": "Contract terms",
            "suggested_redline": "Please have a legal professional review this contract",
            "risk_explanation": "Automated analysis was not available",
            "clause_index": 1,
            "change_rationale": "Manual review recommended due to technical limitations",
            "risk_mitigated": False
        }]
        
        email_draft = f"""Dear [Counterparty],

I have reviewed the contract '{filename}'. Due to technical limitations with our automated analysis system, I was unable to perform a detailed AI-powered risk assessment at this time.

I recommend having a legal professional review this contract to identify any potential risks or areas for negotiation.

Please let me know if you have any questions or if you'd like to discuss this further.

Best regards,
[Your Name]"""
        
        return {
            "risky_clauses": risky_clauses,
            "suggested_redlines": suggested_redlines,
            "email_draft": email_draft,
            "processing_time": 0.1,
            "status": "completed_with_warnings",
            "overall_risk_score": 0.5,  # Neutral score when unknown
            "warnings": [error_msg],
            "errors": [],
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    def _create_email_draft(self, filename: str, risky_clauses: List[Dict], risk_score: float) -> str:
        """Create email draft based on analysis results."""
        
        risk_level = "low" if risk_score < 0.3 else "medium" if risk_score < 0.7 else "high"
        
        email = f"""Dear [Counterparty],

I have completed my review of the contract '{filename}'. Based on my analysis, I've identified a {risk_level} overall risk level (score: {risk_score:.1f}/1.0).

"""
        
        if risky_clauses:
            email += "Key areas that may require attention:\n\n"
            for i, clause in enumerate(risky_clauses[:3], 1):
                email += f"{i}. {clause.get('explanation', 'Contract term requires review')}\n"
            email += "\n"
        
        email += """I recommend we discuss these points before proceeding. Please let me know your thoughts and if you'd like to schedule a call to review the details.

Best regards,
[Your Name]"""
        
        return email


# Global service instance
_simple_analysis_service = None

def get_simple_contract_analysis_service() -> SimpleContractAnalysisService:
    """Get the simple job application tracking service instance."""
    global _simple_analysis_service
    if _simple_analysis_service is None:
        _simple_analysis_service = SimpleContractAnalysisService()
    return _simple_analysis_service