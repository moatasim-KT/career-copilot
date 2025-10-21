"""
Enhanced Risk Assessment Agent

This module implements the enhanced risk assessment agent with multi-LLM support,
advanced risk scoring algorithms, trend analysis, and comprehensive mitigation strategies.
"""

import json
import logging
import re
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from crewai import Task

from ..core.exceptions import ErrorCategory, ErrorSeverity, ValidationError, WorkflowExecutionError
from ..core.langsmith_integration import trace_ai_operation
from ..services.llm_manager import get_enhanced_llm_manager, TaskType, LLMProvider
from ..repositories.contract_repository import get_contract_repository
from ..core.caching import get_cache_manager
from ..monitoring.metrics_collector import get_metrics_collector
from .base_agent import AgentCommunicationProtocol, BaseContractAgent
from ..core.agent_cache_manager import AgentType
from ..core.retry_handler import with_retry, RetryConfig
from ..core.correlation_manager import log_with_correlation, correlation_context

logger = logging.getLogger(__name__)


class RiskTrendPeriod(str, Enum):
    """Time periods for risk trend analysis."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class RiskMitigationStrategy(str, Enum):
    """Risk mitigation strategy types."""
    NEGOTIATE = "negotiate"
    ACCEPT = "accept"
    TRANSFER = "transfer"
    AVOID = "avoid"
    MONITOR = "monitor"


@dataclass
class RiskTrendData:
    """Risk trend analysis data."""
    period: RiskTrendPeriod
    risk_scores: List[float]
    timestamps: List[datetime]
    contract_types: List[str]
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_strength: float  # 0.0 to 1.0
    statistical_significance: float
    recommendations: List[str]


@dataclass
class RiskMitigationPlan:
    """Comprehensive risk mitigation plan."""
    risk_id: str
    risk_category: str
    current_score: float
    target_score: float
    strategy: RiskMitigationStrategy
    actions: List[str]
    timeline: str
    cost_estimate: str
    success_probability: float
    monitoring_metrics: List[str]


@dataclass
class EnhancedRiskAssessment:
    """Enhanced risk assessment with multi-LLM analysis."""
    clause_id: str
    overall_risk_score: float
    confidence_score: float
    llm_assessments: Dict[str, Dict[str, Any]]
    consensus_analysis: Dict[str, Any]
    risk_categories: Dict[str, Dict[str, Any]]
    identified_threats: List[Dict[str, Any]]
    mitigation_plan: RiskMitigationPlan
    trend_analysis: Optional[RiskTrendData]
    calibration_data: Dict[str, Any]


class EnhancedRiskAssessmentAgent(BaseContractAgent):
    """
    Enhanced risk assessment agent with multi-LLM support, advanced analytics, and comprehensive mitigation strategies.
    
    New Capabilities:
    - Multi-LLM provider analysis with consensus building
    - Risk scoring optimization and calibration
    - Historical trend analysis and pattern recognition
    - Advanced mitigation strategy generation
    - Real-time risk monitoring and alerting
    """
    
    def __init__(
        self,
        communication_protocol: AgentCommunicationProtocol,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the Enhanced Risk Assessment Agent.
        
        Args:
            communication_protocol: Shared communication protocol
            config: Optional configuration parameters
        """
        super().__init__(
            agent_name="enhanced_risk_assessment",
            role="Senior AI-Powered Legal Risk Analyst",
            goal="Provide comprehensive multi-dimensional risk analysis using advanced AI models, historical data, and predictive analytics",
            backstory="""You are an elite AI-powered legal risk analyst with expertise in leveraging multiple AI models 
            for comprehensive risk assessment. You combine traditional legal analysis with cutting-edge machine learning 
            techniques, historical pattern recognition, and predictive analytics. Your approach integrates insights from 
            multiple AI providers to build consensus-based risk assessments that are both accurate and actionable. 
            You specialize in risk trend analysis, calibrated scoring systems, and developing sophisticated mitigation 
            strategies that adapt to changing business environments and regulatory landscapes.""",
            communication_protocol=communication_protocol,
            config=config
        )
        
        # Initialize enhanced services
        self.llm_manager = get_enhanced_llm_manager()
        self.contract_repository = get_contract_repository()
        self.cache_manager = get_cache_manager()
        self.metrics_collector = get_metrics_collector()
        
        # Enhanced configuration
        self.multi_llm_config = {
            "consensus_threshold": 0.7,  # Agreement threshold for consensus
            "max_providers": 3,  # Maximum LLM providers to use
            "confidence_weight": 0.3,  # Weight for confidence in final score
            "enable_calibration": True,  # Enable risk score calibration
            "enable_trend_analysis": True,  # Enable historical trend analysis
        }
        
        # Set agent type for caching
        self.agent_type = AgentType.RISK_ASSESSOR
        
        # Risk calibration parameters
        self.calibration_config = {
            "historical_window_days": 90,
            "min_samples_for_calibration": 10,
            "calibration_factors": {
                "overestimation_penalty": 0.9,
                "underestimation_penalty": 1.1,
                "confidence_boost": 1.05
            }
        }
        
        # Risk assessment configuration
        self.risk_thresholds = {
            "critical": 9.0,
            "high": 7.0,
            "medium": 4.0,
            "low": 2.0,
            "minimal": 0.0
        }
        
        # Risk categories and their weights
        self.risk_categories = {
            "financial": 0.3,
            "legal": 0.25,
            "operational": 0.2,
            "compliance": 0.15,
            "reputational": 0.1
        }
        
        # Risk scoring algorithms configuration
        self.risk_algorithms = {
            "clause_type_weights": {
                "liability": 9.0,
                "indemnification": 8.5,
                "termination": 7.0,
                "payment_terms": 6.5,
                "intellectual_property": 6.0,
                "confidentiality": 5.5,
                "force_majeure": 4.0,
                "governing_law": 3.0,
                "general": 2.0
            },
            "risk_indicators": {
                "unlimited_liability": 10.0,
                "broad_indemnification": 9.0,
                "automatic_renewal": 7.5,
                "no_termination_right": 8.0,
                "penalty_clauses": 7.0,
                "exclusive_dealing": 6.5,
                "non_compete": 6.0,
                "liquidated_damages": 5.5,
                "assignment_restrictions": 4.5,
                "change_of_control": 4.0
            },
            "threat_patterns": {
                "financial_exposure": [
                    r"unlimited.*liability",
                    r"consequential.*damages",
                    r"punitive.*damages",
                    r"liquidated.*damages",
                    r"penalty.*fee",
                    r"interest.*rate.*\d+%"
                ],
                "operational_constraints": [
                    r"exclusive.*dealing",
                    r"non.*compete",
                    r"restraint.*trade",
                    r"minimum.*purchase",
                    r"volume.*commitment"
                ],
                "legal_vulnerabilities": [
                    r"indemnify.*against.*all",
                    r"hold.*harmless.*from.*any",
                    r"waive.*all.*rights",
                    r"disclaim.*all.*warranties",
                    r"as.*is.*basis"
                ],
                "compliance_risks": [
                    r"regulatory.*compliance",
                    r"data.*protection",
                    r"privacy.*laws",
                    r"export.*control",
                    r"anti.*corruption"
                ]
            }
        }
        
        # Threat identification patterns
        self.threat_categories = {
            "financial_threats": {
                "unlimited_liability": {
                    "severity": 10.0,
                    "description": "Unlimited financial exposure",
                    "patterns": [r"unlimited.*liability", r"without.*limitation.*liability"]
                },
                "consequential_damages": {
                    "severity": 8.5,
                    "description": "Exposure to consequential damages",
                    "patterns": [r"consequential.*damages", r"indirect.*damages", r"special.*damages"]
                },
                "penalty_clauses": {
                    "severity": 7.0,
                    "description": "Financial penalties for non-performance",
                    "patterns": [r"penalty.*clause", r"liquidated.*damages", r"penalty.*fee"]
                }
            },
            "operational_threats": {
                "exclusive_dealing": {
                    "severity": 6.5,
                    "description": "Exclusive dealing restrictions",
                    "patterns": [r"exclusive.*dealing", r"sole.*supplier", r"exclusive.*relationship"]
                },
                "non_compete": {
                    "severity": 6.0,
                    "description": "Non-compete restrictions",
                    "patterns": [r"non.*compete", r"restraint.*trade", r"competitive.*restriction"]
                },
                "automatic_renewal": {
                    "severity": 5.5,
                    "description": "Automatic contract renewal",
                    "patterns": [r"automatic.*renewal", r"auto.*renew", r"automatically.*extend"]
                }
            },
            "legal_threats": {
                "broad_indemnification": {
                    "severity": 9.0,
                    "description": "Broad indemnification obligations",
                    "patterns": [r"indemnify.*against.*all", r"hold.*harmless.*from.*any", r"defend.*indemnify.*hold.*harmless"]
                },
                "warranty_disclaimers": {
                    "severity": 4.5,
                    "description": "Broad warranty disclaimers",
                    "patterns": [r"disclaim.*all.*warranties", r"as.*is.*basis", r"without.*warranty"]
                }
            },
            "compliance_threats": {
                "regulatory_compliance": {
                    "severity": 7.5,
                    "description": "Regulatory compliance obligations",
                    "patterns": [r"regulatory.*compliance", r"comply.*with.*laws", r"legal.*requirements"]
                },
                "data_protection": {
                    "severity": 8.0,
                    "description": "Data protection and privacy risks",
                    "patterns": [r"data.*protection", r"privacy.*laws", r"personal.*data", r"gdpr", r"ccpa"]
                }
            }
        }
        
        # Set task type for fallback manager
        self.task_type = "risk_assessment"
        self.required_capabilities = ["analysis", "reasoning", "risk_evaluation"]
        
        logger.info("Enhanced Risk Assessment Agent initialized with error handling")
    
    @trace_ai_operation("enhanced_risk_assessment", "agent")
    async def execute_task(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute enhanced risk assessment task with multi-LLM analysis.
        
        Args:
            task_input: Input containing analysis_results and workflow_id
            
        Returns:
            Dict[str, Any]: Enhanced risk assessment results with multi-LLM analysis
        """
        # Validate input
        validation_errors = self.validate_input(
            task_input, 
            ["analysis_results"]
        )
        
        if validation_errors:
            raise ValidationError(f"Invalid input for enhanced risk assessment: {'; '.join(validation_errors)}")
        
        analysis_results = task_input["analysis_results"]
        workflow_id = task_input.get("workflow_id", "unknown")
        
        # Extract job application tracking data
        identified_clauses = analysis_results.get("identified_clauses", [])
        contract_structure = analysis_results.get("contract_structure", {})
        
        logger.info(f"Starting enhanced risk assessment for {len(identified_clauses)} clauses (workflow: {workflow_id})")
        
        try:
            # Step 1: Multi-LLM risk assessment for individual clauses
            enhanced_assessments = await self._perform_multi_llm_risk_assessment(
                identified_clauses, contract_structure
            )
            
            # Step 2: Risk score calibration and optimization
            calibrated_assessments = await self._calibrate_risk_scores(enhanced_assessments)
            
            # Step 3: Historical trend analysis
            trend_analysis = await self._perform_trend_analysis(
                calibrated_assessments, contract_structure
            )
            
            # Step 4: Generate comprehensive mitigation strategies
            mitigation_plans = await self._generate_mitigation_strategies(
                calibrated_assessments, trend_analysis
            )
            
            # Step 5: Calculate consensus-based overall risk score
            overall_risk_score = await self._calculate_consensus_risk_score(
                calibrated_assessments, contract_structure
            )
            
            # Step 6: Generate enhanced risk summary with insights
            risk_summary = await self._generate_enhanced_risk_summary(
                calibrated_assessments, overall_risk_score, trend_analysis
            )
            
            # Compile enhanced results
            results = {
                "success": True,
                "enhanced_assessments": calibrated_assessments,
                "overall_risk_score": overall_risk_score,
                "confidence_score": self._calculate_overall_confidence(calibrated_assessments),
                "risk_summary": risk_summary,
                "trend_analysis": trend_analysis,
                "mitigation_plans": mitigation_plans,
                "risk_distribution": self._calculate_enhanced_risk_distribution(calibrated_assessments),
                "consensus_metrics": self._calculate_consensus_metrics(calibrated_assessments),
                "workflow_id": workflow_id,
                "assessment_metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "llm_providers_used": self._get_providers_used(calibrated_assessments),
                    "calibration_applied": self.multi_llm_config["enable_calibration"],
                    "trend_analysis_enabled": self.multi_llm_config["enable_trend_analysis"]
                }
            }
            
            # Store results for future trend analysis
            await self._store_assessment_results(results, workflow_id)
            
            logger.info(f"Enhanced risk assessment completed: {len(calibrated_assessments)} clauses analyzed, "
                       f"overall score: {overall_risk_score:.2f}, confidence: {results['confidence_score']:.2f}")
            
            return results
            
        except Exception as e:
            error_msg = f"Enhanced risk assessment failed: {e}"
            logger.error(error_msg, exc_info=True)
            
            return {
                "success": False,
                "error": error_msg,
                "workflow_id": workflow_id
            }
    
    async def execute_task(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute risk assessment task.
        
        Args:
            task_input: Input containing analysis_results and workflow_id
            
        Returns:
            Dict[str, Any]: Risk assessment results including risky clauses and overall risk score
        """
        # Validate input
        validation_errors = self.validate_input(
            task_input, 
            ["analysis_results"]
        )
        
        if validation_errors:
            raise ValidationError(f"Invalid input for risk assessment: {'; '.join(validation_errors)}")
        
        analysis_results = task_input["analysis_results"]
        workflow_id = task_input.get("workflow_id", "unknown")
        
        # Extract job application tracking data
        identified_clauses = analysis_results.get("identified_clauses", [])
        contract_structure = analysis_results.get("contract_structure", {})
        
        logger.info(f"Starting risk assessment for {len(identified_clauses)} clauses (workflow: {workflow_id})")
        
        try:
            # Step 1: Assess individual clause risks
            risky_clauses = await self._assess_clause_risks(identified_clauses, contract_structure)
            
            # Step 2: Calculate overall risk score
            overall_risk_score = await self._calculate_overall_risk_score(risky_clauses, contract_structure)
            
            # Step 3: Generate risk summary
            risk_summary = await self._generate_risk_summary(risky_clauses, overall_risk_score)
            
            # Step 4: Identify critical risk areas
            critical_risk_areas = self._identify_critical_risk_areas(risky_clauses)
            
            # Step 5: Generate risk mitigation recommendations
            risk_recommendations = await self._generate_risk_recommendations(risky_clauses, critical_risk_areas)
            
            # Compile results
            results = {
                "success": True,
                "risky_clauses": risky_clauses,
                "overall_risk_score": overall_risk_score,
                "risk_summary": risk_summary,
                "critical_risk_areas": critical_risk_areas,
                "risk_recommendations": risk_recommendations,
                "risk_distribution": self._calculate_risk_distribution(risky_clauses),
                "workflow_id": workflow_id
            }
            
            logger.info(f"Risk assessment completed: {len(risky_clauses)} risky clauses, overall score: {overall_risk_score:.2f}")
            
            return results
            
        except Exception as e:
            error_msg = f"Risk assessment failed: {e}"
            logger.error(error_msg, exc_info=True)
            
            return {
                "success": False,
                "error": error_msg,
                "workflow_id": workflow_id
            }
    
    async def _assess_clause_risks(
        self, 
        identified_clauses: List[Dict[str, Any]], 
        contract_structure: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Assess risks for individual clauses using comprehensive risk evaluation algorithms.
        
        Args:
            identified_clauses: List of clauses from job application tracking
            contract_structure: Contract structure information
            
        Returns:
            List[Dict[str, Any]]: List of risky clauses with risk assessments
        """
        risky_clauses = []
        contract_type = contract_structure.get('contract_type', 'unknown')
        
        for clause in identified_clauses:
            try:
                clause_text = clause.get('clause_text', '')
                clause_type = clause.get('clause_type', 'unknown')
                
                # Step 1: Apply algorithmic risk scoring
                algorithmic_score = self._calculate_algorithmic_risk_score(clause_text, clause_type, contract_type)
                
                # Step 2: Identify specific threats
                identified_threats = self._identify_clause_threats(clause_text, clause_type)
                
                # Step 3: Assess risk categories
                risk_categories = self._assess_risk_categories(clause_text, clause_type, identified_threats)
                
                # Step 4: Use CrewAI agent for detailed analysis
                ai_assessment = await self._get_ai_risk_assessment(clause, contract_structure, identified_threats)
                
                # Step 5: Combine algorithmic and AI assessments
                combined_assessment = self._combine_risk_assessments(
                    clause, algorithmic_score, identified_threats, risk_categories, ai_assessment
                )
                
                # Only include clauses that meet risk threshold
                if combined_assessment.get("overall_risk_score", 0) >= self.risk_thresholds["medium"]:
                    risky_clauses.append(combined_assessment)
                
            except Exception as e:
                logger.warning(f"Failed to assess risk for clause {clause.get('clause_index', 'unknown')}: {e}")
                
                # Create a comprehensive fallback risk assessment
                fallback_risk = self._create_comprehensive_risk_assessment(clause, contract_type)
                if fallback_risk.get("overall_risk_score", 0) >= self.risk_thresholds["medium"]:
                    risky_clauses.append(fallback_risk)
        
        # Sort by risk score (highest first)
        risky_clauses.sort(key=lambda x: x.get("overall_risk_score", 0), reverse=True)
        
        return risky_clauses
    
    async def _calculate_overall_risk_score(
        self, 
        risky_clauses: List[Dict[str, Any]], 
        contract_structure: Dict[str, Any]
    ) -> float:
        """
        Calculate the overall risk score for the contract.
        
        Args:
            risky_clauses: List of risky clauses with risk scores
            contract_structure: Contract structure information
            
        Returns:
            float: Overall risk score (0-10)
        """
        if not risky_clauses:
            return 0.0
        
        try:
            # Use CrewAI agent to calculate overall risk
            overall_risk_task = Task(
                description=f"""Calculate the overall risk score for a contract based on individual clause risks.
                
                Risky Clauses Summary:
                {self._format_risky_clauses_summary(risky_clauses)}
                
                Contract Type: {contract_structure.get('contract_type', 'unknown')}
                Total Risky Clauses: {len(risky_clauses)}
                
                Consider:
                1. Individual clause risk scores and their relative importance
                2. Interaction effects between risky clauses
                3. Contract type and industry context
                4. Cumulative risk exposure
                5. Risk concentration in specific areas
                
                Provide an overall risk score (0-10) with justification.
                
                Provide results in JSON format with score and reasoning.""",
                agent=self.crew_agent,
                expected_output="JSON with overall risk score and detailed reasoning"
            )
            
            # Execute the overall risk calculation
            overall_result = await overall_risk_task.execute_async()
            
            # Parse the result
            overall_score = self._parse_overall_risk_score(overall_result, risky_clauses)
            
            return min(10.0, max(0.0, overall_score))  # Ensure score is within bounds
            
        except Exception as e:
            logger.warning(f"Failed to calculate overall risk score: {e}")
            
            # Fallback calculation
            return self._calculate_fallback_overall_risk(risky_clauses)
    
    async def _generate_risk_summary(
        self, 
        risky_clauses: List[Dict[str, Any]], 
        overall_risk_score: float
    ) -> str:
        """
        Generate a comprehensive risk summary.
        
        Args:
            risky_clauses: List of risky clauses
            overall_risk_score: Overall risk score
            
        Returns:
            str: Risk summary text
        """
        try:
            # Use CrewAI agent to generate summary
            summary_task = Task(
                description=f"Generate a comprehensive risk summary for a job application tracking.\n\n"
                           f"Overall Risk Score: {overall_risk_score:.2f}/10\n"
                           f"Number of Risky Clauses: {len(risky_clauses)}\n\n"
                           f"Risky Clauses Summary:\n{self._format_risky_clauses_summary(risky_clauses)}\n\n"
                           "Create a professional risk summary that includes:\n"
                           "1. Overall risk assessment and key findings\n"
                           "2. Most significant risk areas and their implications\n"
                           "3. Critical clauses that require immediate attention\n"
                           "4. Business impact assessment\n"
                           "5. Recommended priority actions\n\n"
                           "The summary should be clear, actionable, and suitable for executive review.""",
                agent=self.crew_agent,
                expected_output="Professional risk summary suitable for executive review"
            )
            
            # Execute the summary generation
            summary_result = await summary_task.execute_async()
            
            return str(summary_result).strip()
            
        except Exception as e:
            logger.warning(f"Failed to generate risk summary: {e}")
            
            # Fallback summary
            return self._generate_fallback_risk_summary(risky_clauses, overall_risk_score)
    
    async def _generate_risk_recommendations(
        self, 
        risky_clauses: List[Dict[str, Any]], 
        critical_risk_areas: List[str]
    ) -> List[str]:
        """
        Generate risk mitigation recommendations.
        
        Args:
            risky_clauses: List of risky clauses
            critical_risk_areas: List of critical risk areas
            
        Returns:
            List[str]: List of risk mitigation recommendations
        """
        try:
            # Use CrewAI agent to generate recommendations
            recommendations_task = Task(
                description=f"""Generate specific risk mitigation recommendations for contract risks.
                
                Critical Risk Areas: {', '.join(critical_risk_areas)}
                
                Risky Clauses Summary:
                {self._format_risky_clauses_summary(risky_clauses)}
                
                Provide specific, actionable recommendations for:
                1. Immediate actions to address high-risk clauses
                2. Negotiation strategies for risk mitigation
                3. Legal review priorities
                4. Business process adjustments
                5. Ongoing monitoring requirements
                
                Each recommendation should be specific, actionable, and prioritized.
                
                Provide results as a JSON list of recommendation strings.""",
                agent=self.crew_agent,
                expected_output="JSON list of specific, actionable risk mitigation recommendations"
            )
            
            # Execute the recommendations generation
            recommendations_result = await recommendations_task.execute_async()
            
            # Parse the recommendations
            recommendations = self._parse_recommendations(recommendations_result)
            
            return recommendations
            
        except Exception as e:
            logger.warning(f"Failed to generate risk recommendations: {e}")
            
            # Fallback recommendations
            return self._generate_fallback_recommendations(risky_clauses, critical_risk_areas)
    
    def _parse_risk_assessment(self, risk_result: str, original_clause: Dict[str, Any]) -> Dict[str, Any]:
        """Parse risk assessment result from the agent"""
        try:
            import json
            
            # Try to extract JSON from the result
            if isinstance(risk_result, str):
                start_idx = risk_result.find('{')
                end_idx = risk_result.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = risk_result[start_idx:end_idx]
                    risk_data = json.loads(json_str)
                    
                    # Enhance with original clause data
                    risk_assessment = {
                        "clause_text": original_clause.get("clause_text", ""),
                        "clause_type": original_clause.get("clause_type", "unknown"),
                        "clause_index": original_clause.get("clause_index", 0),
                        "risk_level": self._determine_risk_level(risk_data.get("overall_risk_score", 0)),
                        "overall_risk_score": risk_data.get("overall_risk_score", 0),
                        "risk_explanation": risk_data.get("risk_explanation", ""),
                        "financial_risk": risk_data.get("financial_risk", {}),
                        "legal_risk": risk_data.get("legal_risk", {}),
                        "operational_risk": risk_data.get("operational_risk", {}),
                        "compliance_risk": risk_data.get("compliance_risk", {}),
                        "reputational_risk": risk_data.get("reputational_risk", {}),
                        "potential_impact": risk_data.get("potential_impact", ""),
                        "business_impact": risk_data.get("business_impact", "")
                    }
                    
                    return risk_assessment
            
            # If parsing fails, create basic assessment
            return self._create_basic_risk_assessment(original_clause)
            
        except Exception as e:
            logger.warning(f"Failed to parse risk assessment: {e}")
            return self._create_basic_risk_assessment(original_clause)
    
    def _create_basic_risk_assessment(self, clause: Dict[str, Any]) -> Dict[str, Any]:
        """Create a basic risk assessment as fallback"""
        clause_type = clause.get("clause_type", "unknown").lower()
        
        # Basic risk scoring based on clause type
        risk_scores = {
            "liability": 8.0,
            "indemnification": 7.5,
            "termination": 6.0,
            "payment": 5.5,
            "confidentiality": 4.5,
            "intellectual_property": 6.5,
            "governing_law": 3.0,
            "general": 2.0
        }
        
        base_score = risk_scores.get(clause_type, 3.0)
        
        return {
            "clause_text": clause.get("clause_text", ""),
            "clause_type": clause.get("clause_type", "unknown"),
            "clause_index": clause.get("clause_index", 0),
            "risk_level": self._determine_risk_level(base_score),
            "overall_risk_score": base_score,
            "risk_explanation": f"Basic risk assessment for {clause_type} clause",
            "financial_risk": {"level": "Medium", "score": base_score * 0.8},
            "legal_risk": {"level": "Medium", "score": base_score * 0.9},
            "operational_risk": {"level": "Low", "score": base_score * 0.6},
            "compliance_risk": {"level": "Low", "score": base_score * 0.5},
            "reputational_risk": {"level": "Low", "score": base_score * 0.4},
            "potential_impact": f"Potential {clause_type} related risks",
            "business_impact": "Moderate business impact expected"
        }
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level based on score"""
        if risk_score >= self.risk_thresholds["high"]:
            return "High"
        elif risk_score >= self.risk_thresholds["medium"]:
            return "Medium"
        else:
            return "Low"
    
    def _format_risky_clauses_summary(self, risky_clauses: List[Dict[str, Any]]) -> str:
        """Format risky clauses for agent prompts"""
        summary_lines = []
        
        for i, clause in enumerate(risky_clauses[:10], 1):  # Limit to top 10
            summary_lines.append(
                f"{i}. {clause.get('clause_type', 'Unknown')} clause "
                f"(Risk: {clause.get('overall_risk_score', 0):.1f}/10) - "
                f"{clause.get('clause_text', '')[:100]}..."
            )
        
        return "\n".join(summary_lines)
    
    def _parse_overall_risk_score(self, overall_result: str, risky_clauses: List[Dict[str, Any]]) -> float:
        """Parse overall risk score from agent result"""
        try:
            import json
            import re
            
            # Try to extract JSON
            if isinstance(overall_result, str):
                start_idx = overall_result.find('{')
                end_idx = overall_result.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = overall_result[start_idx:end_idx]
                    result_data = json.loads(json_str)
                    return float(result_data.get("overall_risk_score", 0))
                
                # Try to extract number from text
                score_match = re.search(r'(\d+\.?\d*)\s*/\s*10', overall_result)
                if score_match:
                    return float(score_match.group(1))
            
            # Fallback calculation
            return self._calculate_fallback_overall_risk(risky_clauses)
            
        except Exception as e:
            logger.warning(f"Failed to parse overall risk score: {e}")
            return self._calculate_fallback_overall_risk(risky_clauses)
    
    def _calculate_fallback_overall_risk(self, risky_clauses: List[Dict[str, Any]]) -> float:
        """Calculate fallback overall risk score"""
        if not risky_clauses:
            return 0.0
        
        # Calculate weighted average of risk scores
        total_score = sum(clause.get("overall_risk_score", 0) for clause in risky_clauses)
        average_score = total_score / len(risky_clauses)
        
        # Apply multiplier based on number of risky clauses
        clause_count_multiplier = min(1.2, 1.0 + (len(risky_clauses) * 0.02))
        
        return min(10.0, average_score * clause_count_multiplier)
    
    def _identify_critical_risk_areas(self, risky_clauses: List[Dict[str, Any]]) -> List[str]:
        """Identify critical risk areas from risky clauses"""
        risk_area_counts = {}
        
        for clause in risky_clauses:
            clause_type = clause.get("clause_type", "unknown")
            risk_score = clause.get("overall_risk_score", 0)
            
            if clause_type not in risk_area_counts:
                risk_area_counts[clause_type] = {"count": 0, "total_score": 0}
            
            risk_area_counts[clause_type]["count"] += 1
            risk_area_counts[clause_type]["total_score"] += risk_score
        
        # Sort by average risk score and count
        critical_areas = []
        for area, data in risk_area_counts.items():
            avg_score = data["total_score"] / data["count"]
            if avg_score >= 6.0 or data["count"] >= 3:
                critical_areas.append(area)
        
        return critical_areas
    
    def _calculate_risk_distribution(self, risky_clauses: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate distribution of risk levels"""
        distribution = {"High": 0, "Medium": 0, "Low": 0}
        
        for clause in risky_clauses:
            risk_level = clause.get("risk_level", "Low")
            distribution[risk_level] = distribution.get(risk_level, 0) + 1
        
        return distribution
    
    def _generate_fallback_risk_summary(self, risky_clauses: List[Dict[str, Any]], overall_risk_score: float) -> str:
        """Generate fallback risk summary"""
        high_risk_count = sum(1 for clause in risky_clauses if clause.get("risk_level") == "High")
        medium_risk_count = sum(1 for clause in risky_clauses if clause.get("risk_level") == "Medium")
        
        return f"""Contract Risk Assessment Summary:

Overall Risk Score: {overall_risk_score:.2f}/10

Key Findings:
- {len(risky_clauses)} risky clauses identified
- {high_risk_count} high-risk clauses requiring immediate attention
- {medium_risk_count} medium-risk clauses requiring review

The contract presents {'significant' if overall_risk_score >= 7 else 'moderate' if overall_risk_score >= 4 else 'low'} risk exposure.
Priority should be given to addressing high-risk clauses and negotiating more favorable terms where possible."""
    
    def _parse_recommendations(self, recommendations_result: str) -> List[str]:
        """Parse recommendations from agent result"""
        try:
            import json
            
            if isinstance(recommendations_result, str):
                # Try to extract JSON array
                start_idx = recommendations_result.find('[')
                end_idx = recommendations_result.rfind(']') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = recommendations_result[start_idx:end_idx]
                    return json.loads(json_str)
                
                # Try to extract from text
                lines = recommendations_result.split('\n')
                recommendations = []
                for line in lines:
                    line = line.strip()
                    if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                        recommendations.append(line.lstrip('-•0123456789. '))
                
                return recommendations[:10]  # Limit to 10 recommendations
            
            return []
            
        except Exception as e:
            logger.warning(f"Failed to parse recommendations: {e}")
            return []
    
    def _calculate_algorithmic_risk_score(self, clause_text: str, clause_type: str, contract_type: str) -> float:
        """
        Calculate risk score using algorithmic approach.
        
        Args:
            clause_text: Text of the clause
            clause_type: Type of the clause
            contract_type: Type of the contract
            
        Returns:
            float: Algorithmic risk score (0-10)
        """
        try:
            # Base score from clause type
            base_score = self.risk_algorithms["clause_type_weights"].get(clause_type.lower(), 2.0)
            
            # Apply risk indicators
            indicator_score = 0.0
            for indicator, weight in self.risk_algorithms["risk_indicators"].items():
                if self._check_risk_indicator(clause_text, indicator):
                    indicator_score += weight
            
            # Apply threat pattern matching
            threat_score = 0.0
            for category, patterns in self.risk_algorithms["threat_patterns"].items():
                for pattern in patterns:
                    if re.search(pattern, clause_text, re.IGNORECASE):
                        threat_score += 2.0  # Each pattern match adds 2 points
                        break  # Only count once per category
            
            # Calculate weighted score
            total_score = (base_score * 0.5) + (indicator_score * 0.3) + (threat_score * 0.2)
            
            # Apply contract type modifier
            contract_modifier = self._get_contract_type_modifier(contract_type)
            final_score = total_score * contract_modifier
            
            # Ensure minimum score for payment terms with fees
            if clause_type.lower() == "payment_terms" and "fee" in clause_text.lower():
                final_score = max(final_score, 4.5)
            
            return min(10.0, max(0.0, final_score))
            
        except Exception as e:
            logger.warning(f"Failed to calculate algorithmic risk score: {e}")
            return 3.0  # Default moderate risk
    
    def _check_risk_indicator(self, clause_text: str, indicator: str) -> bool:
        """Check if a specific risk indicator is present in the clause text."""
        indicator_patterns = {
            "unlimited_liability": [r"unlimited.*liability", r"without.*limitation.*liability"],
            "broad_indemnification": [r"indemnify.*against.*all", r"hold.*harmless.*from.*any"],
            "automatic_renewal": [r"automatic.*renewal", r"auto.*renew", r"automatically.*extend"],
            "no_termination_right": [r"no.*right.*to.*terminate", r"cannot.*be.*terminated"],
            "penalty_clauses": [r"penalty.*clause", r"liquidated.*damages", r"penalty.*fee"],
            "exclusive_dealing": [r"exclusive.*dealing", r"sole.*supplier"],
            "non_compete": [r"non.*compete", r"restraint.*trade"],
            "liquidated_damages": [r"liquidated.*damages", r"predetermined.*damages"],
            "assignment_restrictions": [r"not.*assign", r"no.*assignment", r"assignment.*prohibited"],
            "change_of_control": [r"change.*of.*control", r"ownership.*change"]
        }
        
        patterns = indicator_patterns.get(indicator, [])
        for pattern in patterns:
            if re.search(pattern, clause_text, re.IGNORECASE):
                return True
        return False
    
    def _get_contract_type_modifier(self, contract_type: str) -> float:
        """Get risk modifier based on contract type."""
        contract_modifiers = {
            "employment": 1.2,
            "service_agreement": 1.1,
            "service agreement": 1.1,
            "software_license": 1.15,
            "nda": 0.9,
            "partnership": 1.3,
            "merger": 1.4,
            "loan": 1.25,
            "lease": 1.1,
            "purchase": 1.05
        }
        
        contract_type_lower = contract_type.lower()
        for contract_key, modifier in contract_modifiers.items():
            if contract_key in contract_type_lower:
                return modifier
        
        return 1.0  # Default modifier
    
    def _identify_clause_threats(self, clause_text: str, clause_type: str) -> List[Dict[str, Any]]:
        """
        Identify specific threats in a clause using pattern matching.
        
        Args:
            clause_text: Text of the clause
            clause_type: Type of the clause
            
        Returns:
            List[Dict[str, Any]]: List of identified threats
        """
        identified_threats = []
        
        for category, threats in self.threat_categories.items():
            for threat_name, threat_info in threats.items():
                for pattern in threat_info["patterns"]:
                    if re.search(pattern, clause_text, re.IGNORECASE):
                        threat = {
                            "threat_name": threat_name,
                            "threat_category": category,
                            "severity": threat_info["severity"],
                            "description": threat_info["description"],
                            "matched_pattern": pattern,
                            "clause_type": clause_type,
                            "mitigation_priority": self._calculate_mitigation_priority(
                                threat_info["severity"], clause_type
                            )
                        }
                        identified_threats.append(threat)
                        break  # Only match once per threat type
        
        # Sort by severity (highest first)
        identified_threats.sort(key=lambda x: x["severity"], reverse=True)
        
        return identified_threats
    
    def _calculate_mitigation_priority(self, severity: float, clause_type: str) -> str:
        """Calculate mitigation priority based on severity and clause type."""
        high_priority_clauses = ["liability", "indemnification", "termination", "payment_terms"]
        
        if severity >= 8.0 and clause_type in high_priority_clauses:
            return "critical"
        elif severity >= 7.0:
            return "high"
        elif severity >= 5.0:
            return "medium"
        else:
            return "low"
    
    def _assess_risk_categories(
        self, 
        clause_text: str, 
        clause_type: str, 
        identified_threats: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Assess risk across different categories.
        
        Args:
            clause_text: Text of the clause
            clause_type: Type of the clause
            identified_threats: List of identified threats
            
        Returns:
            Dict[str, Dict[str, Any]]: Risk assessment by category
        """
        risk_categories = {}
        
        # Financial risk assessment
        financial_risk = self._assess_financial_risk(clause_text, clause_type, identified_threats)
        risk_categories["financial"] = financial_risk
        
        # Legal risk assessment
        legal_risk = self._assess_legal_risk(clause_text, clause_type, identified_threats)
        risk_categories["legal"] = legal_risk
        
        # Operational risk assessment
        operational_risk = self._assess_operational_risk(clause_text, clause_type, identified_threats)
        risk_categories["operational"] = operational_risk
        
        # Compliance risk assessment
        compliance_risk = self._assess_compliance_risk(clause_text, clause_type, identified_threats)
        risk_categories["compliance"] = compliance_risk
        
        # Reputational risk assessment
        reputational_risk = self._assess_reputational_risk(clause_text, clause_type, identified_threats)
        risk_categories["reputational"] = reputational_risk
        
        return risk_categories
    
    def _assess_financial_risk(
        self, 
        clause_text: str, 
        clause_type: str, 
        identified_threats: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess financial risk for a clause."""
        base_score = 2.0
        
        # Clause type base scores
        financial_clause_scores = {
            "liability": 8.0,
            "indemnification": 7.5,
            "payment_terms": 6.0,
            "termination": 5.0,
            "penalty": 7.0
        }
        
        base_score = financial_clause_scores.get(clause_type, base_score)
        
        # Add threat-based scoring
        financial_threats = [t for t in identified_threats if t["threat_category"] == "financial_threats"]
        threat_score = sum(t["severity"] * 0.1 for t in financial_threats)
        
        # Pattern-based adjustments
        pattern_adjustments = 0.0
        financial_patterns = [
            (r"unlimited.*liability", 3.0),
            (r"consequential.*damages", 2.5),
            (r"punitive.*damages", 2.0),
            (r"liquidated.*damages", 1.5),
            (r"penalty.*fee", 1.0),
            (r"\$[\d,]+", 0.5)  # Specific monetary amounts
        ]
        
        for pattern, adjustment in financial_patterns:
            if re.search(pattern, clause_text, re.IGNORECASE):
                pattern_adjustments += adjustment
        
        final_score = min(10.0, base_score + threat_score + pattern_adjustments)
        
        return {
            "score": final_score,
            "level": self._score_to_level(final_score),
            "explanation": self._generate_financial_risk_explanation(final_score, financial_threats),
            "potential_impact": self._estimate_financial_impact(clause_text, final_score),
            "mitigation_suggestions": self._get_financial_mitigation_suggestions(clause_type, financial_threats)
        }
    
    def _assess_legal_risk(
        self, 
        clause_text: str, 
        clause_type: str, 
        identified_threats: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess legal risk for a clause."""
        base_score = 2.0
        
        # Clause type base scores
        legal_clause_scores = {
            "liability": 8.5,
            "indemnification": 9.0,
            "governing_law": 4.0,
            "dispute_resolution": 5.0,
            "intellectual_property": 6.5,
            "confidentiality": 5.5
        }
        
        base_score = legal_clause_scores.get(clause_type, base_score)
        
        # Add threat-based scoring
        legal_threats = [t for t in identified_threats if t["threat_category"] == "legal_threats"]
        threat_score = sum(t["severity"] * 0.1 for t in legal_threats)
        
        # Pattern-based adjustments
        pattern_adjustments = 0.0
        legal_patterns = [
            (r"indemnify.*against.*all", 2.5),
            (r"hold.*harmless.*from.*any", 2.0),
            (r"waive.*all.*rights", 2.0),
            (r"disclaim.*all.*warranties", 1.5),
            (r"as.*is.*basis", 1.0)
        ]
        
        for pattern, adjustment in legal_patterns:
            if re.search(pattern, clause_text, re.IGNORECASE):
                pattern_adjustments += adjustment
        
        final_score = min(10.0, base_score + threat_score + pattern_adjustments)
        
        return {
            "score": final_score,
            "level": self._score_to_level(final_score),
            "explanation": self._generate_legal_risk_explanation(final_score, legal_threats),
            "potential_impact": self._estimate_legal_impact(clause_text, final_score),
            "mitigation_suggestions": self._get_legal_mitigation_suggestions(clause_type, legal_threats)
        }
    
    def _assess_operational_risk(
        self, 
        clause_text: str, 
        clause_type: str, 
        identified_threats: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess operational risk for a clause."""
        base_score = 2.0
        
        # Clause type base scores
        operational_clause_scores = {
            "termination": 7.0,
            "performance": 6.0,
            "service_levels": 5.5,
            "delivery": 5.0,
            "change_control": 4.5
        }
        
        base_score = operational_clause_scores.get(clause_type, base_score)
        
        # Add threat-based scoring
        operational_threats = [t for t in identified_threats if t["threat_category"] == "operational_threats"]
        threat_score = sum(t["severity"] * 0.1 for t in operational_threats)
        
        # Pattern-based adjustments
        pattern_adjustments = 0.0
        operational_patterns = [
            (r"exclusive.*dealing", 2.0),
            (r"non.*compete", 1.8),
            (r"minimum.*purchase", 1.5),
            (r"volume.*commitment", 1.3),
            (r"automatic.*renewal", 1.0)
        ]
        
        for pattern, adjustment in operational_patterns:
            if re.search(pattern, clause_text, re.IGNORECASE):
                pattern_adjustments += adjustment
        
        final_score = min(10.0, base_score + threat_score + pattern_adjustments)
        
        return {
            "score": final_score,
            "level": self._score_to_level(final_score),
            "explanation": self._generate_operational_risk_explanation(final_score, operational_threats),
            "potential_impact": self._estimate_operational_impact(clause_text, final_score),
            "mitigation_suggestions": self._get_operational_mitigation_suggestions(clause_type, operational_threats)
        }
    
    def _assess_compliance_risk(
        self, 
        clause_text: str, 
        clause_type: str, 
        identified_threats: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess compliance risk for a clause."""
        base_score = 1.5
        
        # Clause type base scores
        compliance_clause_scores = {
            "data_protection": 8.0,
            "regulatory": 7.5,
            "export_control": 7.0,
            "anti_corruption": 6.5,
            "environmental": 5.0
        }
        
        base_score = compliance_clause_scores.get(clause_type, base_score)
        
        # Add threat-based scoring
        compliance_threats = [t for t in identified_threats if t["threat_category"] == "compliance_threats"]
        threat_score = sum(t["severity"] * 0.1 for t in compliance_threats)
        
        # Pattern-based adjustments
        pattern_adjustments = 0.0
        compliance_patterns = [
            (r"gdpr|ccpa|privacy.*law", 2.0),
            (r"regulatory.*compliance", 1.8),
            (r"export.*control", 1.5),
            (r"anti.*corruption", 1.3),
            (r"data.*protection", 1.5)
        ]
        
        for pattern, adjustment in compliance_patterns:
            if re.search(pattern, clause_text, re.IGNORECASE):
                pattern_adjustments += adjustment
        
        final_score = min(10.0, base_score + threat_score + pattern_adjustments)
        
        return {
            "score": final_score,
            "level": self._score_to_level(final_score),
            "explanation": self._generate_compliance_risk_explanation(final_score, compliance_threats),
            "potential_impact": self._estimate_compliance_impact(clause_text, final_score),
            "mitigation_suggestions": self._get_compliance_mitigation_suggestions(clause_type, compliance_threats)
        }
    
    def _assess_reputational_risk(
        self, 
        clause_text: str, 
        clause_type: str, 
        identified_threats: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess reputational risk for a clause."""
        base_score = 1.0
        
        # Clause type base scores
        reputational_clause_scores = {
            "publicity": 6.0,
            "confidentiality": 4.0,
            "non_disparagement": 5.0,
            "social_responsibility": 4.5
        }
        
        base_score = reputational_clause_scores.get(clause_type, base_score)
        
        # Pattern-based adjustments
        pattern_adjustments = 0.0
        reputational_patterns = [
            (r"public.*disclosure", 1.5),
            (r"media.*coverage", 1.3),
            (r"brand.*damage", 1.8),
            (r"reputation.*harm", 2.0)
        ]
        
        for pattern, adjustment in reputational_patterns:
            if re.search(pattern, clause_text, re.IGNORECASE):
                pattern_adjustments += adjustment
        
        final_score = min(10.0, base_score + pattern_adjustments)
        
        return {
            "score": final_score,
            "level": self._score_to_level(final_score),
            "explanation": self._generate_reputational_risk_explanation(final_score),
            "potential_impact": self._estimate_reputational_impact(clause_text, final_score),
            "mitigation_suggestions": self._get_reputational_mitigation_suggestions(clause_type)
        }
    
    def _score_to_level(self, score: float) -> str:
        """Convert numeric score to risk level."""
        if score >= self.risk_thresholds["critical"]:
            return "Critical"
        elif score >= self.risk_thresholds["high"]:
            return "High"
        elif score >= self.risk_thresholds["medium"]:
            return "Medium"
        elif score >= self.risk_thresholds["low"]:
            return "Low"
        else:
            return "Minimal"
    
    async def _get_ai_risk_assessment(
        self, 
        clause: Dict[str, Any], 
        contract_structure: Dict[str, Any],
        identified_threats: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get AI-powered risk assessment for additional insights."""
        try:
            threats_summary = "; ".join([f"{t['threat_name']} (severity: {t['severity']})" for t in identified_threats[:5]])
            
            risk_task = Task(
                description=f"""Provide a detailed risk assessment for this contract clause, considering the algorithmic analysis results.
                
                Clause Text: {clause.get('clause_text', '')}
                Clause Type: {clause.get('clause_type', 'unknown')}
                Contract Type: {contract_structure.get('contract_type', 'unknown')}
                
                Identified Threats: {threats_summary}
                
                Please provide:
                1. Overall risk assessment and justification
                2. Business impact analysis
                3. Legal implications and potential consequences
                4. Specific recommendations for risk mitigation
                5. Priority level for addressing this clause
                
                Focus on practical business implications and actionable insights.
                
                Provide results in JSON format with the following structure:
                {{
                    "ai_risk_score": <0-10>,
                    "business_impact": "<description>",
                    "legal_implications": "<description>",
                    "mitigation_recommendations": ["<recommendation1>", "<recommendation2>"],
                    "priority_level": "<critical/high/medium/low>",
                    "justification": "<detailed explanation>"
                }}""",
                agent=self.crew_agent,
                expected_output="JSON with detailed AI risk assessment"
            )
            
            # Execute the AI risk assessment
            ai_result = await risk_task.execute_async()
            
            # Parse the AI assessment result
            return self._parse_ai_risk_assessment(ai_result)
            
        except Exception as e:
            logger.warning(f"Failed to get AI risk assessment: {e}")
            return {
                "ai_risk_score": 5.0,
                "business_impact": "Moderate business impact expected",
                "legal_implications": "Standard legal considerations apply",
                "mitigation_recommendations": ["Review with legal counsel"],
                "priority_level": "medium",
                "justification": "AI assessment unavailable, using default values"
            }
    
    def _combine_risk_assessments(
        self,
        clause: Dict[str, Any],
        algorithmic_score: float,
        identified_threats: List[Dict[str, Any]],
        risk_categories: Dict[str, Dict[str, Any]],
        ai_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine algorithmic and AI risk assessments into final assessment."""
        
        # Calculate weighted overall score
        ai_score = ai_assessment.get("ai_risk_score", 5.0)
        category_scores = [cat["score"] for cat in risk_categories.values()]
        avg_category_score = sum(category_scores) / len(category_scores) if category_scores else 5.0
        
        # Weighted combination: 40% algorithmic, 30% AI, 30% category average
        overall_score = (algorithmic_score * 0.4) + (ai_score * 0.3) + (avg_category_score * 0.3)
        
        # Apply threat severity boost
        max_threat_severity = max([t["severity"] for t in identified_threats], default=0.0)
        if max_threat_severity >= 8.0:
            overall_score = min(10.0, overall_score * 1.2)
        
        return {
            "clause_text": clause.get("clause_text", ""),
            "clause_type": clause.get("clause_type", "unknown"),
            "clause_index": clause.get("clause_index", 0),
            "overall_risk_score": round(overall_score, 2),
            "risk_level": self._score_to_level(overall_score),
            "algorithmic_score": round(algorithmic_score, 2),
            "ai_score": round(ai_score, 2),
            "identified_threats": identified_threats,
            "risk_categories": risk_categories,
            "business_impact": ai_assessment.get("business_impact", ""),
            "legal_implications": ai_assessment.get("legal_implications", ""),
            "mitigation_recommendations": ai_assessment.get("mitigation_recommendations", []),
            "priority_level": ai_assessment.get("priority_level", "medium"),
            "risk_explanation": ai_assessment.get("justification", ""),
            "assessment_metadata": {
                "assessment_timestamp": datetime.utcnow().isoformat(),
                "threat_count": len(identified_threats),
                "highest_threat_severity": max_threat_severity,
                "assessment_method": "combined_algorithmic_ai"
            }
        }
    
    def _create_comprehensive_risk_assessment(self, clause: Dict[str, Any], contract_type: str) -> Dict[str, Any]:
        """Create comprehensive fallback risk assessment."""
        clause_type = clause.get("clause_type", "unknown").lower()
        clause_text = clause.get("clause_text", "")
        
        # Calculate algorithmic score
        algorithmic_score = self._calculate_algorithmic_risk_score(clause_text, clause_type, contract_type)
        
        # Identify threats
        identified_threats = self._identify_clause_threats(clause_text, clause_type)
        
        # Basic risk categories assessment
        risk_categories = {
            "financial": {"score": algorithmic_score * 0.8, "level": self._score_to_level(algorithmic_score * 0.8)},
            "legal": {"score": algorithmic_score * 0.9, "level": self._score_to_level(algorithmic_score * 0.9)},
            "operational": {"score": algorithmic_score * 0.6, "level": self._score_to_level(algorithmic_score * 0.6)},
            "compliance": {"score": algorithmic_score * 0.5, "level": self._score_to_level(algorithmic_score * 0.5)},
            "reputational": {"score": algorithmic_score * 0.4, "level": self._score_to_level(algorithmic_score * 0.4)}
        }
        
        return {
            "clause_text": clause_text,
            "clause_type": clause.get("clause_type", "unknown"),
            "clause_index": clause.get("clause_index", 0),
            "overall_risk_score": algorithmic_score,
            "risk_level": self._score_to_level(algorithmic_score),
            "algorithmic_score": algorithmic_score,
            "ai_score": algorithmic_score,  # Use algorithmic as fallback
            "identified_threats": identified_threats,
            "risk_categories": risk_categories,
            "business_impact": f"Potential {clause_type} related business impact",
            "legal_implications": f"Standard legal considerations for {clause_type} clauses",
            "mitigation_recommendations": self._get_fallback_mitigation_recommendations(clause_type, identified_threats),
            "priority_level": self._score_to_level(algorithmic_score).lower(),
            "risk_explanation": f"Comprehensive fallback assessment for {clause_type} clause",
            "assessment_metadata": {
                "assessment_timestamp": datetime.utcnow().isoformat(),
                "threat_count": len(identified_threats),
                "highest_threat_severity": max([t["severity"] for t in identified_threats], default=0.0),
                "assessment_method": "comprehensive_fallback"
            }
        }
    
    def _get_fallback_mitigation_recommendations(self, clause_type: str, identified_threats: List[Dict[str, Any]]) -> List[str]:
        """Generate fallback mitigation recommendations."""
        recommendations = []
        
        # Base recommendations by clause type
        clause_recommendations = {
            "liability": ["Negotiate liability caps", "Add exclusions for consequential damages", "Consider insurance coverage"],
            "indemnification": ["Limit indemnification scope", "Add mutual indemnification", "Exclude certain types of claims"],
            "termination": ["Negotiate reasonable notice periods", "Add termination for convenience", "Clarify post-termination obligations"],
            "payment_terms": ["Clarify payment schedules", "Add dispute resolution procedures", "Include late payment penalties"],
            "confidentiality": ["Define confidential information clearly", "Add reasonable exceptions", "Limit duration of obligations"]
        }
        
        recommendations.extend(clause_recommendations.get(clause_type, ["Review with legal counsel", "Consider business impact"]))
        
        # Add threat-specific recommendations
        for threat in identified_threats[:3]:  # Top 3 threats
            if threat["threat_name"] == "unlimited_liability":
                recommendations.append("Negotiate liability caps and limitations")
            elif threat["threat_name"] == "broad_indemnification":
                recommendations.append("Narrow indemnification scope and add exceptions")
            elif threat["threat_name"] == "automatic_renewal":
                recommendations.append("Add termination rights before renewal")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _generate_financial_risk_explanation(self, score: float, threats: List[Dict[str, Any]]) -> str:
        """Generate explanation for financial risk assessment."""
        if score >= 8.0:
            return f"High financial risk due to potential unlimited liability exposure and {len(threats)} identified financial threats."
        elif score >= 6.0:
            return f"Moderate financial risk with {len(threats)} identified threats requiring attention."
        elif score >= 4.0:
            return f"Low to moderate financial risk with {len(threats)} minor threats identified."
        else:
            return "Minimal financial risk identified in this clause."
    
    def _generate_legal_risk_explanation(self, score: float, threats: List[Dict[str, Any]]) -> str:
        """Generate explanation for legal risk assessment."""
        if score >= 8.0:
            return f"High legal risk due to broad liability or indemnification obligations and {len(threats)} legal threats."
        elif score >= 6.0:
            return f"Moderate legal risk with {len(threats)} identified legal concerns."
        elif score >= 4.0:
            return f"Low to moderate legal risk with {len(threats)} minor legal issues."
        else:
            return "Minimal legal risk identified in this clause."
    
    def _generate_operational_risk_explanation(self, score: float, threats: List[Dict[str, Any]]) -> str:
        """Generate explanation for operational risk assessment."""
        if score >= 7.0:
            return f"High operational risk due to restrictive terms and {len(threats)} operational constraints."
        elif score >= 5.0:
            return f"Moderate operational risk with {len(threats)} operational concerns."
        elif score >= 3.0:
            return f"Low operational risk with {len(threats)} minor operational issues."
        else:
            return "Minimal operational risk identified in this clause."
    
    def _generate_compliance_risk_explanation(self, score: float, threats: List[Dict[str, Any]]) -> str:
        """Generate explanation for compliance risk assessment."""
        if score >= 7.0:
            return f"High compliance risk due to regulatory requirements and {len(threats)} compliance threats."
        elif score >= 5.0:
            return f"Moderate compliance risk with {len(threats)} compliance concerns."
        elif score >= 3.0:
            return f"Low compliance risk with {len(threats)} minor compliance issues."
        else:
            return "Minimal compliance risk identified in this clause."
    
    def _generate_reputational_risk_explanation(self, score: float) -> str:
        """Generate explanation for reputational risk assessment."""
        if score >= 6.0:
            return "High reputational risk due to potential public exposure or brand damage."
        elif score >= 4.0:
            return "Moderate reputational risk with potential for negative publicity."
        elif score >= 2.0:
            return "Low reputational risk with minimal public exposure."
        else:
            return "Minimal reputational risk identified in this clause."
    
    def _estimate_financial_impact(self, clause_text: str, score: float) -> str:
        """Estimate financial impact based on clause content and score."""
        if score >= 8.0:
            return "Potentially unlimited financial exposure with significant monetary risk"
        elif score >= 6.0:
            return "Moderate to high financial impact with measurable monetary risk"
        elif score >= 4.0:
            return "Low to moderate financial impact with limited monetary exposure"
        else:
            return "Minimal financial impact expected"
    
    def _estimate_legal_impact(self, clause_text: str, score: float) -> str:
        """Estimate legal impact based on clause content and score."""
        if score >= 8.0:
            return "High legal exposure with potential for significant liability and litigation risk"
        elif score >= 6.0:
            return "Moderate legal impact with potential liability concerns"
        elif score >= 4.0:
            return "Low to moderate legal impact with standard legal considerations"
        else:
            return "Minimal legal impact with routine legal implications"
    
    def _estimate_operational_impact(self, clause_text: str, score: float) -> str:
        """Estimate operational impact based on clause content and score."""
        if score >= 7.0:
            return "High operational impact with significant business constraints"
        elif score >= 5.0:
            return "Moderate operational impact affecting business flexibility"
        elif score >= 3.0:
            return "Low operational impact with minor business considerations"
        else:
            return "Minimal operational impact on business operations"
    
    def _estimate_compliance_impact(self, clause_text: str, score: float) -> str:
        """Estimate compliance impact based on clause content and score."""
        if score >= 7.0:
            return "High compliance impact with significant regulatory obligations"
        elif score >= 5.0:
            return "Moderate compliance impact requiring regulatory attention"
        elif score >= 3.0:
            return "Low compliance impact with standard regulatory considerations"
        else:
            return "Minimal compliance impact with routine regulatory requirements"
    
    def _estimate_reputational_impact(self, clause_text: str, score: float) -> str:
        """Estimate reputational impact based on clause content and score."""
        if score >= 6.0:
            return "High reputational impact with potential for significant brand damage"
        elif score >= 4.0:
            return "Moderate reputational impact with potential negative publicity"
        elif score >= 2.0:
            return "Low reputational impact with minimal public exposure risk"
        else:
            return "Minimal reputational impact expected"
    
    def _get_financial_mitigation_suggestions(self, clause_type: str, threats: List[Dict[str, Any]]) -> List[str]:
        """Get financial risk mitigation suggestions."""
        suggestions = []
        
        if any(t["threat_name"] == "unlimited_liability" for t in threats):
            suggestions.append("Negotiate liability caps and limitations")
        if any(t["threat_name"] == "consequential_damages" for t in threats):
            suggestions.append("Exclude consequential and indirect damages")
        if any(t["threat_name"] == "penalty_clauses" for t in threats):
            suggestions.append("Review and negotiate penalty amounts")
        
        if clause_type == "payment_terms":
            suggestions.append("Clarify payment terms and dispute procedures")
        
        return suggestions
    
    def _get_legal_mitigation_suggestions(self, clause_type: str, threats: List[Dict[str, Any]]) -> List[str]:
        """Get legal risk mitigation suggestions."""
        suggestions = []
        
        if any(t["threat_name"] == "broad_indemnification" for t in threats):
            suggestions.append("Narrow indemnification scope and add exceptions")
        if any(t["threat_name"] == "warranty_disclaimers" for t in threats):
            suggestions.append("Negotiate reasonable warranty provisions")
        
        if clause_type in ["liability", "indemnification"]:
            suggestions.append("Add mutual liability provisions")
        
        return suggestions
    
    def _get_operational_mitigation_suggestions(self, clause_type: str, threats: List[Dict[str, Any]]) -> List[str]:
        """Get operational risk mitigation suggestions."""
        suggestions = []
        
        if any(t["threat_name"] == "exclusive_dealing" for t in threats):
            suggestions.append("Negotiate flexibility in supplier relationships")
        if any(t["threat_name"] == "non_compete" for t in threats):
            suggestions.append("Limit scope and duration of non-compete restrictions")
        if any(t["threat_name"] == "automatic_renewal" for t in threats):
            suggestions.append("Add termination rights before renewal periods")
        
        return suggestions
    
    def _get_compliance_mitigation_suggestions(self, clause_type: str, threats: List[Dict[str, Any]]) -> List[str]:
        """Get compliance risk mitigation suggestions."""
        suggestions = []
        
        if any(t["threat_name"] == "regulatory_compliance" for t in threats):
            suggestions.append("Clarify regulatory compliance responsibilities")
        if any(t["threat_name"] == "data_protection" for t in threats):
            suggestions.append("Ensure data protection compliance measures")
        
        return suggestions
    
    def _get_reputational_mitigation_suggestions(self, clause_type: str) -> List[str]:
        """Get reputational risk mitigation suggestions."""
        suggestions = []
        
        if clause_type == "publicity":
            suggestions.append("Add approval rights for public communications")
        if clause_type == "confidentiality":
            suggestions.append("Ensure adequate confidentiality protections")
        
        return suggestions
    
    def _parse_ai_risk_assessment(self, ai_result: str) -> Dict[str, Any]:
        """Parse AI risk assessment result."""
        try:
            # Try to extract JSON from the result
            if isinstance(ai_result, str):
                start_idx = ai_result.find('{')
                end_idx = ai_result.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = ai_result[start_idx:end_idx]
                    return json.loads(json_str)
            
            # Fallback parsing
            return {
                "ai_risk_score": 5.0,
                "business_impact": "Moderate business impact expected",
                "legal_implications": "Standard legal considerations apply",
                "mitigation_recommendations": ["Review with legal counsel"],
                "priority_level": "medium",
                "justification": "AI assessment parsing failed, using defaults"
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse AI risk assessment: {e}")
            return {
                "ai_risk_score": 5.0,
                "business_impact": "Assessment unavailable",
                "legal_implications": "Assessment unavailable",
                "mitigation_recommendations": ["Review with legal counsel"],
                "priority_level": "medium",
                "justification": f"Parsing error: {e}"
            }
    
    def _generate_fallback_recommendations(self, risky_clauses: List[Dict[str, Any]], critical_risk_areas: List[str]) -> List[str]:
        """Generate fallback recommendations"""
        recommendations = [
            "Conduct detailed legal review of all high-risk clauses",
            "Negotiate more favorable terms for liability and indemnification clauses",
            "Implement additional safeguards for payment and termination provisions",
            "Review compliance requirements and regulatory implications",
            "Consider risk mitigation strategies and insurance coverage"
        ]
        
        # Add specific recommendations based on critical risk areas
        for area in critical_risk_areas:
            if area == "liability":
                recommendations.append("Negotiate liability caps and exclusions")
            elif area == "termination":
                recommendations.append("Review termination notice periods and conditions")
            elif area == "payment":
                recommendations.append("Clarify payment terms and dispute resolution procedures")
        
        return recommendations[:8]  # Limit to 8 recommendations


# Maintain backward compatibility
RiskAssessmentAgent = EnhancedRiskAssessmentAgent
def get_risk_assessment_agent(
    communication_protocol: AgentCommunicationProtocol,
    config: Optional[Dict[str, Any]] = None
) -> EnhancedRiskAssessmentAgent:
    """Get enhanced risk assessment agent instance."""
    return EnhancedRiskAssessmentAgent(communication_protocol, config)


# Alias for backward compatibility
RiskAssessmentAgent = EnhancedRiskAssessmentAgent