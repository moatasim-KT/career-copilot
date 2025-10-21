"""
Production Contract Analysis Service
A robust, production-ready job application tracking service using the unified AI service
with proper error handling, caching, and comprehensive analysis capabilities.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
import hashlib

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.caching import get_cache_manager
from ..monitoring.metrics_collector import get_metrics_collector
from .unified_ai_service import get_unified_ai_service, AIModelType, AIProvider

logger = get_logger(__name__)
settings = get_settings()
cache_manager = get_cache_manager()
metrics_collector = get_metrics_collector()


class ProductionContractAnalysisService:
    """Production-ready job application tracking service."""
    
    def __init__(self):
        self.ai_service = get_unified_ai_service()
        self.cache_ttl = 3600  # 1 hour cache
        
    def _generate_cache_key(self, contract_text: str, analysis_type: str) -> str:
        """Generate cache key for analysis results."""
        content_hash = hashlib.md5(contract_text.encode()).hexdigest()
        return f"contract_analysis:{analysis_type}:{content_hash}"
    
    async def analyze_contract(
        self,
        contract_text: str,
        filename: str,
        analysis_type: str = "comprehensive",
        use_cache: bool = True,
        preferred_provider: Optional[AIProvider] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive job application tracking.
        
        Args:
            contract_text: The contract text to analyze
            filename: Name of the contract file
            analysis_type: Type of analysis (quick, standard, comprehensive)
            use_cache: Whether to use cached results
            preferred_provider: Preferred AI provider to use
            
        Returns:
            Dictionary containing analysis results
        """
        
        start_time = time.time()
        
        # Check cache first (if available)
        if use_cache and cache_manager:
            try:
                cache_key = self._generate_cache_key(contract_text, analysis_type)
                cached_result = None
                if hasattr(cache_manager, 'get'):
                    cached_result = await cache_manager.get(cache_key)
                if cached_result:
                    logger.info(f"Returning cached analysis for {filename}")
                    cached_result["from_cache"] = True
                    return cached_result
            except Exception as e:
                logger.debug(f"Cache lookup failed: {e}")
        
        try:
            # Determine model type based on analysis type
            model_type = self._get_model_type(analysis_type)
            
            # Perform the analysis
            if analysis_type == "quick":
                result = await self._quick_analysis(contract_text, filename, model_type, preferred_provider)
            elif analysis_type == "comprehensive":
                result = await self._comprehensive_analysis(contract_text, filename, model_type, preferred_provider)
            else:  # standard
                result = await self._standard_analysis(contract_text, filename, model_type, preferred_provider)
            
            # Add metadata
            result.update({
                "analysis_type": analysis_type,
                "processing_time": time.time() - start_time,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "from_cache": False
            })
            
            # Cache the result (if available)
            if use_cache and cache_manager:
                try:
                    if hasattr(cache_manager, 'set'):
                        await cache_manager.set(cache_key, result, ttl=self.cache_ttl)
                except Exception as e:
                    logger.debug(f"Cache storage failed: {e}")
            
            # Record metrics (if method exists)
            try:
                if hasattr(metrics_collector, 'record_analysis_completion'):
                    metrics_collector.record_analysis_completion(
                        analysis_type=analysis_type,
                        processing_time=result["processing_time"],
                        success=True,
                        provider=result.get("ai_provider", "unknown")
                    )
            except Exception as e:
                logger.debug(f"Failed to record analysis metrics: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Contract analysis failed for {filename}: {e}")
            
            # Record error metrics (if method exists)
            try:
                if hasattr(metrics_collector, 'record_analysis_completion'):
                    metrics_collector.record_analysis_completion(
                        analysis_type=analysis_type,
                        processing_time=time.time() - start_time,
                        success=False,
                        error=str(e)
                    )
            except Exception as e:
                logger.debug(f"Failed to record error metrics: {e}")
            
            # Return fallback response
            return self._create_fallback_response(filename, str(e))
    
    def _get_model_type(self, analysis_type: str) -> AIModelType:
        """Get appropriate model type for analysis type."""
        if analysis_type == "quick":
            return AIModelType.FAST
        elif analysis_type == "comprehensive":
            return AIModelType.PREMIUM
        else:
            return AIModelType.BALANCED
    
    async def _quick_analysis(
        self,
        contract_text: str,
        filename: str,
        model_type: AIModelType,
        preferred_provider: Optional[AIProvider]
    ) -> Dict[str, Any]:
        """Perform quick job application tracking."""
        
        prompt = self._create_quick_analysis_prompt(contract_text, filename)
        
        messages = [
            {"role": "system", "content": "You are a legal contract analyst. Provide concise, actionable analysis in valid JSON format."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.ai_service.chat_completion(
            messages=messages,
            model_type=model_type,
            temperature=0.3,
            max_tokens=1500,
            provider=preferred_provider
        )
        
        return self._parse_ai_response(response, filename, "quick")
    
    async def _standard_analysis(
        self,
        contract_text: str,
        filename: str,
        model_type: AIModelType,
        preferred_provider: Optional[AIProvider]
    ) -> Dict[str, Any]:
        """Perform standard job application tracking."""
        
        prompt = self._create_standard_analysis_prompt(contract_text, filename)
        
        messages = [
            {"role": "system", "content": "You are an expert legal contract analyst. Provide detailed analysis in valid JSON format."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.ai_service.chat_completion(
            messages=messages,
            model_type=model_type,
            temperature=0.2,
            max_tokens=3000,
            provider=preferred_provider
        )
        
        return self._parse_ai_response(response, filename, "standard")
    
    async def _comprehensive_analysis(
        self,
        contract_text: str,
        filename: str,
        model_type: AIModelType,
        preferred_provider: Optional[AIProvider]
    ) -> Dict[str, Any]:
        """Perform comprehensive job application tracking with multiple AI calls."""
        
        # Break down comprehensive analysis into multiple focused analyses
        analyses = await asyncio.gather(
            self._analyze_risk_factors(contract_text, model_type, preferred_provider),
            self._analyze_legal_clauses(contract_text, model_type, preferred_provider),
            self._generate_negotiation_points(contract_text, model_type, preferred_provider),
            return_exceptions=True
        )
        
        # Combine results
        risk_analysis = analyses[0] if not isinstance(analyses[0], Exception) else {}
        clause_analysis = analyses[1] if not isinstance(analyses[1], Exception) else {}
        negotiation_analysis = analyses[2] if not isinstance(analyses[2], Exception) else {}
        
        return self._combine_comprehensive_results(
            risk_analysis, clause_analysis, negotiation_analysis, filename
        )
    
    async def _analyze_risk_factors(
        self,
        contract_text: str,
        model_type: AIModelType,
        preferred_provider: Optional[AIProvider]
    ) -> Dict[str, Any]:
        """Analyze risk factors in the contract."""
        
        prompt = f"""
        Analyze the following contract for risk factors. Focus on:
        1. Financial risks (payment terms, penalties, liability caps)
        2. Operational risks (termination clauses, performance requirements)
        3. Legal risks (indemnification, governing law, dispute resolution)
        4. Compliance risks (regulatory requirements, data protection)
        
        Contract text (first 2000 chars):
        {contract_text[:2000]}
        
        Respond with JSON containing:
        {{
            "risk_factors": [
                {{
                    "category": "financial|operational|legal|compliance",
                    "risk_level": "Low|Medium|High",
                    "description": "Description of the risk",
                    "clause_reference": "Relevant clause text",
                    "impact": "Potential impact description",
                    "mitigation": "Suggested mitigation strategy"
                }}
            ],
            "overall_risk_score": 0.0-1.0
        }}
        """
        
        messages = [
            {"role": "system", "content": "You are a risk assessment specialist. Analyze contracts for potential risks."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.ai_service.chat_completion(
            messages=messages,
            model_type=model_type,
            temperature=0.1,
            max_tokens=2000,
            provider=preferred_provider
        )
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {"risk_factors": [], "overall_risk_score": 0.5}
    
    async def _analyze_legal_clauses(
        self,
        contract_text: str,
        model_type: AIModelType,
        preferred_provider: Optional[AIProvider]
    ) -> Dict[str, Any]:
        """Analyze specific legal clauses."""
        
        prompt = f"""
        Analyze the legal clauses in this contract. Identify:
        1. Problematic or unusual clauses
        2. Missing standard protections
        3. Ambiguous language that could cause disputes
        4. Clauses that favor one party over another
        
        Contract text (first 2000 chars):
        {contract_text[:2000]}
        
        Respond with JSON:
        {{
            "problematic_clauses": [
                {{
                    "clause_text": "Exact clause text",
                    "issue": "What's problematic about it",
                    "severity": "Low|Medium|High",
                    "recommendation": "How to address it"
                }}
            ],
            "missing_protections": ["List of missing standard clauses"],
            "ambiguous_language": ["List of ambiguous terms or phrases"]
        }}
        """
        
        messages = [
            {"role": "system", "content": "You are a legal clause analysis expert. Identify problematic contract language."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.ai_service.chat_completion(
            messages=messages,
            model_type=model_type,
            temperature=0.1,
            max_tokens=2000,
            provider=preferred_provider
        )
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {"problematic_clauses": [], "missing_protections": [], "ambiguous_language": []}
    
    async def _generate_negotiation_points(
        self,
        contract_text: str,
        model_type: AIModelType,
        preferred_provider: Optional[AIProvider]
    ) -> Dict[str, Any]:
        """Generate negotiation points and redlines."""
        
        prompt = f"""
        Based on this contract, generate specific negotiation points and suggested redlines:
        
        Contract text (first 2000 chars):
        {contract_text[:2000]}
        
        Respond with JSON:
        {{
            "negotiation_points": [
                {{
                    "priority": "High|Medium|Low",
                    "topic": "What to negotiate",
                    "current_language": "Current problematic language",
                    "suggested_change": "Proposed alternative language",
                    "rationale": "Why this change is important"
                }}
            ],
            "redlines": [
                {{
                    "section": "Contract section",
                    "original": "Original text",
                    "revised": "Revised text",
                    "justification": "Legal justification for change"
                }}
            ]
        }}
        """
        
        messages = [
            {"role": "system", "content": "You are a contract negotiation expert. Provide specific, actionable negotiation advice."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.ai_service.chat_completion(
            messages=messages,
            model_type=model_type,
            temperature=0.2,
            max_tokens=2000,
            provider=preferred_provider
        )
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {"negotiation_points": [], "redlines": []}
    
    def _create_quick_analysis_prompt(self, contract_text: str, filename: str) -> str:
        """Create prompt for quick analysis."""
        return f"""
        Perform a quick analysis of this contract: {filename}
        
        Contract text (first 1500 chars):
        {contract_text[:1500]}
        
        Provide a JSON response with:
        {{
            "summary": "Brief 2-3 sentence summary",
            "key_risks": ["List of 2-3 main risks"],
            "risk_score": 0.0-1.0,
            "recommendations": ["2-3 key recommendations"],
            "red_flags": ["Any immediate red flags"]
        }}
        
        Focus on the most critical issues only.
        """
    
    def _create_standard_analysis_prompt(self, contract_text: str, filename: str) -> str:
        """Create prompt for standard analysis."""
        return f"""
        Perform a standard legal analysis of this contract: {filename}
        
        Contract text (first 2500 chars):
        {contract_text[:2500]}
        
        Provide a comprehensive JSON response with:
        {{
            "contract_type": "Type of contract",
            "parties": ["List of parties involved"],
            "key_terms": {{
                "duration": "Contract duration",
                "payment_terms": "Payment structure",
                "termination": "Termination conditions"
            }},
            "risk_assessment": {{
                "overall_score": 0.0-1.0,
                "financial_risk": "Low|Medium|High",
                "legal_risk": "Low|Medium|High",
                "operational_risk": "Low|Medium|High"
            }},
            "risky_clauses": [
                {{
                    "clause": "Clause text",
                    "risk": "Risk description",
                    "severity": "Low|Medium|High"
                }}
            ],
            "recommendations": ["Detailed recommendations"],
            "missing_clauses": ["Important missing protections"]
        }}
        """
    
    def _parse_ai_response(self, ai_response, filename: str, analysis_type: str) -> Dict[str, Any]:
        """Parse AI response and convert to standard format."""
        
        try:
            # Try to parse as JSON first
            parsed_data = json.loads(ai_response.content)
        except json.JSONDecodeError:
            # If JSON parsing fails, create structured response from text
            parsed_data = self._extract_structured_data_from_text(ai_response.content)
        
        # Convert to API model format
        return self._convert_to_api_format(parsed_data, filename, ai_response)
    
    def _extract_structured_data_from_text(self, text_response: str) -> Dict[str, Any]:
        """Extract structured data from text response when JSON parsing fails."""
        
        # Basic extraction logic - look for key indicators
        risk_score = 0.3  # Default moderate risk
        
        # Simple keyword-based risk assessment
        high_risk_keywords = ["terminate", "penalty", "liability", "indemnif", "breach"]
        medium_risk_keywords = ["payment", "confidential", "intellectual property"]
        
        high_risk_count = sum(1 for keyword in high_risk_keywords if keyword.lower() in text_response.lower())
        medium_risk_count = sum(1 for keyword in medium_risk_keywords if keyword.lower() in text_response.lower())
        
        risk_score = min(0.9, 0.2 + (high_risk_count * 0.15) + (medium_risk_count * 0.1))
        
        return {
            "summary": "AI analysis completed but response format was not structured",
            "risk_score": risk_score,
            "key_findings": ["Analysis completed with text-based extraction"],
            "recommendations": ["Review contract with legal counsel for detailed analysis"]
        }
    
    def _convert_to_api_format(self, parsed_data: Dict, filename: str, ai_response) -> Dict[str, Any]:
        """Convert parsed data to API response format."""
        
        # Extract risky clauses
        risky_clauses = []
        
        # Handle different response formats
        if "risky_clauses" in parsed_data:
            for i, clause in enumerate(parsed_data["risky_clauses"][:5], 1):
                risky_clauses.append({
                    "clause_text": clause.get("clause", clause.get("clause_text", "Contract clause")),
                    "risk_explanation": clause.get("risk", clause.get("explanation", "Risk identified")),
                    "risk_level": self._normalize_risk_level(clause.get("severity", clause.get("risk_level", "Medium"))),
                    "precedent_reference": None,
                    "clause_index": i
                })
        elif "risk_factors" in parsed_data:
            for i, risk in enumerate(parsed_data["risk_factors"][:5], 1):
                risky_clauses.append({
                    "clause_text": risk.get("clause_reference", risk.get("description", "Risk factor identified")),
                    "risk_explanation": risk.get("description", risk.get("impact", "Risk description")),
                    "risk_level": self._normalize_risk_level(risk.get("risk_level", "Medium")),
                    "precedent_reference": None,
                    "clause_index": i
                })
        
        # Extract suggested redlines
        suggested_redlines = []
        
        if "redlines" in parsed_data:
            for i, redline in enumerate(parsed_data["redlines"][:3], 1):
                suggested_redlines.append({
                    "original_clause": redline.get("original", redline.get("current_language", "Original clause")),
                    "suggested_redline": redline.get("revised", redline.get("suggested_change", "Suggested revision")),
                    "risk_explanation": redline.get("justification", redline.get("rationale", "Recommended change")),
                    "clause_index": i,
                    "change_rationale": redline.get("justification", "Improves contract terms"),
                    "risk_mitigated": True
                })
        elif "negotiation_points" in parsed_data:
            for i, point in enumerate(parsed_data["negotiation_points"][:3], 1):
                suggested_redlines.append({
                    "original_clause": point.get("current_language", "Current terms"),
                    "suggested_redline": point.get("suggested_change", "Proposed revision"),
                    "risk_explanation": point.get("rationale", "Negotiation recommendation"),
                    "clause_index": i,
                    "change_rationale": point.get("rationale", "Improves negotiating position"),
                    "risk_mitigated": True
                })
        
        # Generate email draft
        email_draft = self._generate_email_draft(filename, parsed_data, risky_clauses)
        
        # Calculate overall risk score
        overall_risk_score = parsed_data.get("risk_score", parsed_data.get("overall_risk_score", 0.3))
        if isinstance(overall_risk_score, str):
            overall_risk_score = 0.3  # Default if string
        
        return {
            "risky_clauses": risky_clauses,
            "suggested_redlines": suggested_redlines,
            "email_draft": email_draft,
            "status": "completed",
            "overall_risk_score": float(overall_risk_score),
            "warnings": [],
            "errors": [],
            "ai_provider": ai_response.provider.value,
            "ai_model": ai_response.model,
            "tokens_used": ai_response.tokens_used,
            "cost_estimate": ai_response.cost_estimate
        }
    
    def _normalize_risk_level(self, risk_level: str) -> str:
        """Normalize risk level to API format."""
        if isinstance(risk_level, str):
            level = risk_level.lower()
            if level in ["low", "l"]:
                return "Low"
            elif level in ["high", "h"]:
                return "High"
            else:
                return "Medium"
        return "Medium"
    
    def _generate_email_draft(self, filename: str, analysis_data: Dict, risky_clauses: List) -> str:
        """Generate email draft based on analysis."""
        
        risk_score = analysis_data.get("risk_score", analysis_data.get("overall_risk_score", 0.3))
        risk_level = "low" if risk_score < 0.3 else "medium" if risk_score < 0.7 else "high"
        
        email = f"""Dear [Counterparty],

I have completed my review of the contract '{filename}'. Based on my analysis, I've identified a {risk_level} overall risk level (score: {risk_score:.1f}/1.0).

"""
        
        if risky_clauses:
            email += "Key areas that may require attention:\n\n"
            for i, clause in enumerate(risky_clauses[:3], 1):
                email += f"{i}. {clause.get('risk_explanation', 'Contract term requires review')}\n"
            email += "\n"
        
        # Add recommendations if available
        recommendations = analysis_data.get("recommendations", [])
        if recommendations:
            email += "My recommendations:\n\n"
            for i, rec in enumerate(recommendations[:3], 1):
                email += f"{i}. {rec}\n"
            email += "\n"
        
        email += """I recommend we discuss these points before proceeding. Please let me know your thoughts and if you'd like to schedule a call to review the details.

Best regards,
[Your Name]"""
        
        return email
    
    def _combine_comprehensive_results(
        self,
        risk_analysis: Dict,
        clause_analysis: Dict,
        negotiation_analysis: Dict,
        filename: str
    ) -> Dict[str, Any]:
        """Combine results from comprehensive analysis."""
        
        # Combine all risky clauses
        all_risky_clauses = []
        
        # From risk analysis
        for i, risk in enumerate(risk_analysis.get("risk_factors", [])[:3], 1):
            all_risky_clauses.append({
                "clause_text": risk.get("clause_reference", risk.get("description", "Risk factor")),
                "risk_explanation": risk.get("description", "Risk identified"),
                "risk_level": self._normalize_risk_level(risk.get("risk_level", "Medium")),
                "precedent_reference": None,
                "clause_index": i
            })
        
        # From clause analysis
        for i, clause in enumerate(clause_analysis.get("problematic_clauses", [])[:2], len(all_risky_clauses) + 1):
            all_risky_clauses.append({
                "clause_text": clause.get("clause_text", "Problematic clause"),
                "risk_explanation": clause.get("issue", "Issue identified"),
                "risk_level": self._normalize_risk_level(clause.get("severity", "Medium")),
                "precedent_reference": None,
                "clause_index": i
            })
        
        # Combine redlines
        all_redlines = []
        
        for i, redline in enumerate(negotiation_analysis.get("redlines", [])[:3], 1):
            all_redlines.append({
                "original_clause": redline.get("original", "Original clause"),
                "suggested_redline": redline.get("revised", "Revised clause"),
                "risk_explanation": redline.get("justification", "Recommended change"),
                "clause_index": i,
                "change_rationale": redline.get("justification", "Improves contract terms"),
                "risk_mitigated": True
            })
        
        # Calculate overall risk score
        risk_scores = [
            risk_analysis.get("overall_risk_score", 0.3),
            0.4 if clause_analysis.get("problematic_clauses") else 0.2,
            0.3 if negotiation_analysis.get("negotiation_points") else 0.2
        ]
        overall_risk_score = sum(risk_scores) / len(risk_scores)
        
        # Generate comprehensive email
        email_draft = self._generate_comprehensive_email(filename, risk_analysis, clause_analysis, negotiation_analysis)
        
        return {
            "risky_clauses": all_risky_clauses,
            "suggested_redlines": all_redlines,
            "email_draft": email_draft,
            "status": "completed",
            "overall_risk_score": overall_risk_score,
            "warnings": [],
            "errors": [],
            "comprehensive_analysis": {
                "risk_analysis": risk_analysis,
                "clause_analysis": clause_analysis,
                "negotiation_analysis": negotiation_analysis
            }
        }
    
    def _generate_comprehensive_email(self, filename: str, risk_analysis: Dict, clause_analysis: Dict, negotiation_analysis: Dict) -> str:
        """Generate comprehensive email draft."""
        
        overall_risk = risk_analysis.get("overall_risk_score", 0.3)
        risk_level = "low" if overall_risk < 0.3 else "medium" if overall_risk < 0.7 else "high"
        
        email = f"""Dear [Counterparty],

I have completed a comprehensive review of the contract '{filename}'. Based on my detailed analysis, I've identified a {risk_level} overall risk level (score: {overall_risk:.1f}/1.0).

## Key Findings:

"""
        
        # Risk factors
        risk_factors = risk_analysis.get("risk_factors", [])
        if risk_factors:
            email += "**Risk Factors:**\n"
            for risk in risk_factors[:3]:
                email += f"• {risk.get('description', 'Risk identified')} ({risk.get('risk_level', 'Medium')} risk)\n"
            email += "\n"
        
        # Problematic clauses
        problematic = clause_analysis.get("problematic_clauses", [])
        if problematic:
            email += "**Problematic Clauses:**\n"
            for clause in problematic[:2]:
                email += f"• {clause.get('issue', 'Issue identified')}\n"
            email += "\n"
        
        # Negotiation points
        negotiation_points = negotiation_analysis.get("negotiation_points", [])
        if negotiation_points:
            email += "**Key Negotiation Points:**\n"
            for point in negotiation_points[:3]:
                email += f"• {point.get('topic', 'Negotiation point')} ({point.get('priority', 'Medium')} priority)\n"
            email += "\n"
        
        email += """I recommend we schedule a detailed discussion to review these findings and develop a negotiation strategy. I can provide specific redline suggestions for the most critical issues.

Please let me know your availability for a call this week.

Best regards,
[Your Name]"""
        
        return email
    
    def _create_fallback_response(self, filename: str, error_msg: str) -> Dict[str, Any]:
        """Create fallback response when analysis fails."""
        
        return {
            "risky_clauses": [{
                "clause_text": "Unable to perform detailed AI analysis due to technical limitations",
                "risk_explanation": "Please review contract manually or try again later",
                "risk_level": "Medium",
                "precedent_reference": None,
                "clause_index": 1
            }],
            "suggested_redlines": [{
                "original_clause": "Contract terms",
                "suggested_redline": "Please have a legal professional review this contract",
                "risk_explanation": "Automated analysis was not available",
                "clause_index": 1,
                "change_rationale": "Manual review recommended due to technical limitations",
                "risk_mitigated": False
            }],
            "email_draft": f"""Dear [Counterparty],

I have reviewed the contract '{filename}'. Due to technical limitations with our AI analysis system, I was unable to perform a detailed automated risk assessment at this time.

I recommend having a legal professional review this contract to identify any potential risks or areas for negotiation.

Please let me know if you have any questions or if you'd like to discuss this further.

Best regards,
[Your Name]""",
            "status": "completed_with_warnings",
            "overall_risk_score": 0.5,
            "warnings": [f"AI analysis failed: {error_msg}"],
            "errors": [],
            "ai_provider": "fallback",
            "ai_model": "none",
            "tokens_used": 0,
            "cost_estimate": 0.0
        }


# Global service instance
_production_analysis_service = None

def get_production_contract_analysis_service() -> ProductionContractAnalysisService:
    """Get the global production job application tracking service instance."""
    global _production_analysis_service
    if _production_analysis_service is None:
        _production_analysis_service = ProductionContractAnalysisService()
    return _production_analysis_service