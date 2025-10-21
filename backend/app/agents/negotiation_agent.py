"""
Enhanced Negotiation Agent

This module implements the specialized CrewAI agent responsible for
generating redline suggestions and negotiation strategies with multi-LLM support,
outcome tracking, and multi-language capabilities.
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from crewai import Task

from ..core.exceptions import ErrorCategory, ErrorSeverity, ValidationError, WorkflowExecutionError
from ..core.langsmith_integration import trace_ai_operation
from ..services.llm_manager import get_enhanced_llm_manager, TaskType
from .base_agent import AgentCommunicationProtocol, BaseContractAgent
from ..core.agent_cache_manager import AgentType

logger = logging.getLogger(__name__)


class NegotiationOutcome(str, Enum):
    """Possible negotiation outcomes."""
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    MODIFIED = "modified"
    PENDING = "pending"
    WITHDRAWN = "withdrawn"
    ESCALATED = "escalated"


class NegotiationPhase(str, Enum):
    """Phases of negotiation process."""
    PREPARATION = "preparation"
    INITIAL_PROPOSAL = "initial_proposal"
    COUNTERPROPOSAL = "counterproposal"
    REFINEMENT = "refinement"
    FINAL_TERMS = "final_terms"
    CLOSURE = "closure"


class SupportedLanguage(str, Enum):
    """Supported languages for international contracts."""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    RUSSIAN = "ru"
    ARABIC = "ar"


class NegotiationAgent(BaseContractAgent):
    """
    Enhanced specialized agent for redline generation and negotiation strategy development.
    
    Responsibilities:
    - Generate specific redline recommendations using multiple LLMs
    - Suggest alternative clause language with multi-language support
    - Provide negotiation strategies with outcome tracking
    - Create revision tracking and analysis
    - Support international contract negotiations
    """
    
    def __init__(
        self,
        communication_protocol: AgentCommunicationProtocol,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the Enhanced Negotiation Agent.
        
        Args:
            communication_protocol: Shared communication protocol
            config: Optional configuration parameters
        """
        super().__init__(
            agent_name="enhanced_negotiation",
            role="Senior International Contract Negotiation Strategist",
            goal="Develop comprehensive multi-language negotiation strategies and generate precise redline recommendations using multiple AI providers to optimize contract terms and mitigate risks across international jurisdictions",
            backstory="""You are a senior international contract negotiation strategist with over 25 years of experience in complex 
            commercial negotiations across multiple industries and jurisdictions. You have successfully negotiated billions of dollars in 
            contracts for Fortune 500 companies, international law firms, and government agencies across North America, Europe, Asia, 
            and Latin America. Your expertise includes cross-cultural negotiation strategies, multi-jurisdictional risk mitigation, 
            alternative clause development, and win-win negotiation tactics. You are fluent in multiple languages and understand 
            cultural nuances that affect contract negotiations. You are known for your ability to identify leverage points, craft 
            compelling redline suggestions, and develop negotiation strategies that protect client interests while maintaining positive 
            business relationships across different legal systems and business cultures. Your approach combines legal precision with 
            business acumen and cultural sensitivity, always focusing on practical, implementable solutions that address both legal 
            risks and commercial objectives in international contexts.""",
            communication_protocol=communication_protocol,
            config=config
        )
        
        # Initialize enhanced LLM manager for multi-provider support
        self.llm_manager = get_enhanced_llm_manager()
        
        # Enhanced negotiation strategy configuration
        self.negotiation_priorities = {
            "risk_mitigation": 0.35,
            "commercial_balance": 0.25,
            "relationship_preservation": 0.20,
            "legal_compliance": 0.15,
            "cultural_sensitivity": 0.05
        }
        
        # Set agent type for caching
        self.agent_type = AgentType.NEGOTIATION
        
        # Enhanced redline categories with international considerations
        self.redline_categories = {
            "critical": {"priority": 1, "description": "Must-have changes for deal viability", "escalation_required": True},
            "important": {"priority": 2, "description": "Significant improvements to terms", "escalation_required": False},
            "preferred": {"priority": 3, "description": "Nice-to-have optimizations", "escalation_required": False},
            "minor": {"priority": 4, "description": "Minor clarifications or improvements", "escalation_required": False},
            "cultural": {"priority": 2, "description": "Cultural or jurisdictional adaptations", "escalation_required": False}
        }
        
        # Enhanced contract revision tracking with outcome analysis
        self.revision_history = []
        self.change_tracking = {}
        self.revision_counter = 0
        self.outcome_tracking = {}
        self.negotiation_analytics = {}
        
        # Multi-language support configuration
        self.supported_languages = {lang.value: lang.name.title() for lang in SupportedLanguage}
        self.default_language = SupportedLanguage.ENGLISH
        
        # Negotiation outcome tracking
        self.outcome_history = []
        self.success_metrics = {
            "total_negotiations": 0,
            "successful_closures": 0,
            "average_negotiation_time": 0.0,
            "acceptance_rate_by_priority": {},
            "common_rejection_reasons": {},
            "cultural_adaptation_success": {}
        }
        
        logger.info("Enhanced Negotiation Agent initialized with multi-LLM and multi-language support")
    
    async def generate_multi_llm_negotiation_strategy(
        self,
        risky_clauses: List[Dict[str, Any]],
        precedent_matches: List[Dict[str, Any]],
        contract_structure: Dict[str, Any],
        target_language: str = "en",
        cultural_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate negotiation strategy using multiple LLM providers for enhanced quality.
        
        Args:
            risky_clauses: List of risky clauses
            precedent_matches: List of precedent matches
            contract_structure: Contract structure information
            target_language: Target language for strategy
            cultural_context: Cultural context for international negotiations
            
        Returns:
            Dict[str, Any]: Enhanced negotiation strategy with multi-LLM insights
        """
        try:
            # Prepare context for multiple LLM providers
            context = {
                "contract_type": contract_structure.get("contract_type", "unknown"),
                "risk_count": len(risky_clauses),
                "high_risk_count": len([c for c in risky_clauses if c.get("risk_level") == "High"]),
                "precedent_count": len(precedent_matches),
                "target_language": target_language,
                "cultural_context": cultural_context
            }
            
            # Generate strategies using different LLM providers
            strategies = {}
            
            # Strategy 1: OpenAI for comprehensive analysis
            openai_prompt = self._create_strategy_prompt(
                risky_clauses, precedent_matches, context, "comprehensive"
            )
            openai_strategy = await self.llm_manager.get_completion(
                prompt=openai_prompt,
                task_type=TaskType.NEGOTIATION,
                preferred_provider="openai"
            )
            strategies["comprehensive"] = openai_strategy.content
            
            # Strategy 2: GROQ for speed and efficiency focus
            groq_prompt = self._create_strategy_prompt(
                risky_clauses, precedent_matches, context, "efficient"
            )
            groq_strategy = await self.llm_manager.get_completion(
                prompt=groq_prompt,
                task_type=TaskType.NEGOTIATION,
                preferred_provider="groq"
            )
            strategies["efficient"] = groq_strategy.content
            
            # Strategy 3: Ollama for alternative perspective (if available)
            try:
                ollama_prompt = self._create_strategy_prompt(
                    risky_clauses, precedent_matches, context, "alternative"
                )
                ollama_strategy = await self.llm_manager.get_completion(
                    prompt=ollama_prompt,
                    task_type=TaskType.NEGOTIATION,
                    preferred_provider="ollama"
                )
                strategies["alternative"] = ollama_strategy.content
            except Exception as e:
                logger.warning(f"Ollama strategy generation failed: {e}")
                strategies["alternative"] = "Alternative strategy unavailable"
            
            # Synthesize strategies into unified approach
            unified_strategy = await self._synthesize_strategies(strategies, context)
            
            # Add multi-language support if needed
            if target_language != "en":
                unified_strategy = await self._translate_strategy(unified_strategy, target_language)
            
            # Add cultural adaptations if context provided
            if cultural_context:
                unified_strategy = await self._adapt_strategy_culturally(
                    unified_strategy, cultural_context, target_language
                )
            
            return {
                "unified_strategy": unified_strategy,
                "individual_strategies": strategies,
                "strategy_metadata": {
                    "providers_used": list(strategies.keys()),
                    "target_language": target_language,
                    "cultural_context": cultural_context,
                    "synthesis_confidence": self._calculate_synthesis_confidence(strategies)
                }
            }
            
        except Exception as e:
            logger.error(f"Multi-LLM strategy generation failed: {e}")
            # Fallback to single provider
            return await self._generate_fallback_strategy(risky_clauses, precedent_matches, context)
    
    async def track_negotiation_outcome(
        self,
        negotiation_id: str,
        clause_id: str,
        outcome: NegotiationOutcome,
        outcome_details: Dict[str, Any],
        negotiation_phase: NegotiationPhase = NegotiationPhase.REFINEMENT
    ) -> Dict[str, Any]:
        """
        Track negotiation outcomes for analysis and improvement.
        
        Args:
            negotiation_id: Unique negotiation identifier
            clause_id: Specific clause identifier
            outcome: Negotiation outcome
            outcome_details: Detailed outcome information
            negotiation_phase: Current phase of negotiation
            
        Returns:
            Dict[str, Any]: Updated tracking information
        """
        try:
            timestamp = datetime.utcnow()
            
            # Initialize tracking if not exists
            if negotiation_id not in self.outcome_tracking:
                self.outcome_tracking[negotiation_id] = {
                    "negotiation_id": negotiation_id,
                    "start_time": timestamp,
                    "clauses": {},
                    "phases": [],
                    "overall_status": "active",
                    "success_metrics": {}
                }
            
            # Track clause outcome
            self.outcome_tracking[negotiation_id]["clauses"][clause_id] = {
                "clause_id": clause_id,
                "outcome": outcome.value,
                "outcome_details": outcome_details,
                "phase": negotiation_phase.value,
                "timestamp": timestamp.isoformat(),
                "duration_days": (timestamp - self.outcome_tracking[negotiation_id]["start_time"]).days
            }
            
            # Update phase tracking
            current_phases = self.outcome_tracking[negotiation_id]["phases"]
            if not current_phases or current_phases[-1]["phase"] != negotiation_phase.value:
                current_phases.append({
                    "phase": negotiation_phase.value,
                    "start_time": timestamp.isoformat(),
                    "clauses_in_phase": [clause_id]
                })
            else:
                current_phases[-1]["clauses_in_phase"].append(clause_id)
            
            # Update success metrics
            self._update_success_metrics(negotiation_id, outcome, outcome_details)
            
            # Add to outcome history
            self.outcome_history.append({
                "negotiation_id": negotiation_id,
                "clause_id": clause_id,
                "outcome": outcome.value,
                "phase": negotiation_phase.value,
                "timestamp": timestamp.isoformat(),
                "details": outcome_details
            })
            
            logger.info(f"Tracked negotiation outcome: {negotiation_id}/{clause_id} -> {outcome.value}")
            
            return {
                "success": True,
                "tracking_id": f"{negotiation_id}_{clause_id}",
                "outcome_recorded": outcome.value,
                "phase": negotiation_phase.value,
                "total_clauses_tracked": len(self.outcome_tracking[negotiation_id]["clauses"])
            }
            
        except Exception as e:
            error_msg = f"Failed to track negotiation outcome: {e}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    async def analyze_negotiation_patterns(
        self,
        negotiation_id: Optional[str] = None,
        time_period_days: int = 90
    ) -> Dict[str, Any]:
        """
        Analyze negotiation patterns and outcomes for insights.
        
        Args:
            negotiation_id: Specific negotiation to analyze (optional)
            time_period_days: Time period for analysis
            
        Returns:
            Dict[str, Any]: Negotiation pattern analysis
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)
            
            if negotiation_id:
                # Analyze specific negotiation
                if negotiation_id not in self.outcome_tracking:
                    return {"success": False, "error": "Negotiation not found"}
                
                negotiation_data = self.outcome_tracking[negotiation_id]
                analysis = self._analyze_single_negotiation(negotiation_data)
            else:
                # Analyze all recent negotiations
                recent_outcomes = [
                    outcome for outcome in self.outcome_history
                    if datetime.fromisoformat(outcome["timestamp"]) >= cutoff_date
                ]
                analysis = self._analyze_outcome_patterns(recent_outcomes)
            
            return {
                "success": True,
                "analysis": analysis,
                "analysis_period_days": time_period_days,
                "total_outcomes_analyzed": len(recent_outcomes) if not negotiation_id else len(self.outcome_tracking[negotiation_id]["clauses"])
            }
            
        except Exception as e:
            error_msg = f"Failed to analyze negotiation patterns: {e}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    async def generate_multi_language_strategy(
        self,
        base_strategy: str,
        target_languages: List[str],
        cultural_adaptations: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate negotiation strategy in multiple languages with cultural adaptations.
        
        Args:
            base_strategy: Base strategy in English
            target_languages: List of target language codes
            cultural_adaptations: Optional cultural adaptation notes
            
        Returns:
            Dict[str, Any]: Multi-language strategies
        """
        try:
            multi_language_strategies = {}
            
            for lang_code in target_languages:
                if lang_code not in self.supported_languages:
                    logger.warning(f"Unsupported language: {lang_code}")
                    continue
                
                # Translate strategy
                translated_strategy = await self._translate_strategy(base_strategy, lang_code)
                
                # Apply cultural adaptations if provided
                if cultural_adaptations and lang_code in cultural_adaptations:
                    cultural_context = cultural_adaptations[lang_code]
                    adapted_strategy = await self._adapt_strategy_culturally(
                        translated_strategy, cultural_context, lang_code
                    )
                    multi_language_strategies[lang_code] = {
                        "strategy": adapted_strategy,
                        "language": self.supported_languages[lang_code],
                        "cultural_adaptations": cultural_context,
                        "translation_confidence": 0.9  # Placeholder for actual confidence scoring
                    }
                else:
                    multi_language_strategies[lang_code] = {
                        "strategy": translated_strategy,
                        "language": self.supported_languages[lang_code],
                        "cultural_adaptations": None,
                        "translation_confidence": 0.85
                    }
            
            return {
                "success": True,
                "base_language": "en",
                "target_languages": target_languages,
                "strategies": multi_language_strategies,
                "supported_languages": list(self.supported_languages.keys())
            }
            
        except Exception as e:
            error_msg = f"Failed to generate multi-language strategy: {e}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    @trace_ai_operation("enhanced_negotiation_strategy", "agent")
    async def execute_task(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute negotiation strategy and redline generation task.
        
        Args:
            task_input: Input containing analysis_results, risk_results, precedent_results, and workflow_id
            
        Returns:
            Dict[str, Any]: Negotiation results including redlines and strategies
        """
        # Validate input
        validation_errors = self.validate_input(
            task_input, 
            ["analysis_results", "risk_results", "precedent_results"]
        )
        
        if validation_errors:
            raise ValidationError(f"Invalid input for negotiation strategy: {'; '.join(validation_errors)}")
        
        analysis_results = task_input["analysis_results"]
        risk_results = task_input["risk_results"]
        precedent_results = task_input["precedent_results"]
        workflow_id = task_input.get("workflow_id", "unknown")
        
        # Extract relevant data
        risky_clauses = risk_results.get("risky_clauses", [])
        precedent_matches = precedent_results.get("precedent_matches", [])
        contract_structure = analysis_results.get("contract_structure", {})
        
        logger.info(f"Starting negotiation strategy development for {len(risky_clauses)} risky clauses (workflow: {workflow_id})")
        
        try:
            # Step 1: Generate redline suggestions for risky clauses
            suggested_redlines = await self._generate_redline_suggestions(risky_clauses, precedent_matches)
            
            # Step 2: Develop overall negotiation strategy
            negotiation_strategy = await self._develop_negotiation_strategy(
                risky_clauses, precedent_matches, contract_structure
            )
            
            # Step 3: Create alternative clause language
            alternative_clauses = await self._create_alternative_clauses(risky_clauses, precedent_matches)
            
            # Step 4: Prioritize negotiation points
            negotiation_priorities = self._prioritize_negotiation_points(suggested_redlines, risky_clauses)
            
            # Step 5: Generate negotiation talking points
            talking_points = await self._generate_talking_points(suggested_redlines, negotiation_strategy)
            
            # Step 6: Create fallback positions
            fallback_positions = await self._create_fallback_positions(suggested_redlines, risky_clauses)
            
            # Step 7: Initialize contract revision tracking
            revision_tracking = self._initialize_revision_tracking(
                suggested_redlines, workflow_id, contract_structure
            )
            
            # Compile results
            results = {
                "success": True,
                "suggested_redlines": suggested_redlines,
                "negotiation_strategy": negotiation_strategy,
                "alternative_clauses": alternative_clauses,
                "negotiation_priorities": negotiation_priorities,
                "talking_points": talking_points,
                "fallback_positions": fallback_positions,
                "revision_tracking": revision_tracking,
                "negotiation_metadata": {
                    "total_redlines": len(suggested_redlines),
                    "critical_redlines": len([r for r in suggested_redlines if r.get("priority") == "critical"]),
                    "strategy_focus": self._determine_strategy_focus(risky_clauses),
                    "negotiation_complexity": self._assess_negotiation_complexity(risky_clauses)
                },
                "workflow_id": workflow_id
            }
            
            logger.info(f"Negotiation strategy completed: {len(suggested_redlines)} redlines generated")
            
            return results
            
        except Exception as e:
            error_msg = f"Enhanced negotiation strategy development failed: {e}"
            logger.error(error_msg, exc_info=True)
            
            return {
                "success": False,
                "error": error_msg,
                "workflow_id": workflow_id
            }
    
    def _create_strategy_prompt(
        self,
        risky_clauses: List[Dict[str, Any]],
        precedent_matches: List[Dict[str, Any]],
        context: Dict[str, Any],
        strategy_type: str
    ) -> str:
        """Create strategy prompt based on type and context."""
        base_context = f"""
        Contract Type: {context.get('contract_type', 'unknown')}
        Risk Analysis: {context.get('risk_count', 0)} total risks, {context.get('high_risk_count', 0)} high-risk
        Available Precedents: {context.get('precedent_count', 0)}
        Target Language: {context.get('target_language', 'en')}
        Cultural Context: {context.get('cultural_context', 'Not specified')}
        """
        
        if strategy_type == "comprehensive":
            return f"""
            {base_context}
            
            Develop a comprehensive negotiation strategy that covers all aspects of risk mitigation,
            relationship management, and commercial objectives. Focus on detailed analysis and
            thorough preparation. Consider long-term implications and multiple scenarios.
            
            Risky Clauses Summary: {self._format_clauses_for_prompt(risky_clauses[:5])}
            """
        elif strategy_type == "efficient":
            return f"""
            {base_context}
            
            Develop an efficient, streamlined negotiation strategy focused on quick wins and
            priority issues. Emphasize speed, clarity, and actionable next steps.
            Identify the most critical 3-5 negotiation points.
            
            Top Risk Areas: {self._format_top_risks_for_prompt(risky_clauses[:3])}
            """
        elif strategy_type == "alternative":
            return f"""
            {base_context}
            
            Provide an alternative negotiation approach that considers creative solutions,
            win-win scenarios, and innovative deal structures. Think outside conventional
            negotiation frameworks.
            
            Key Challenges: {self._format_challenges_for_prompt(risky_clauses)}
            """
        else:
            return f"{base_context}\n\nDevelop a balanced negotiation strategy."
    
    async def _synthesize_strategies(
        self,
        strategies: Dict[str, str],
        context: Dict[str, Any]
    ) -> str:
        """Synthesize multiple strategies into unified approach."""
        synthesis_prompt = f"""
        Synthesize the following negotiation strategies into a unified, comprehensive approach:
        
        Comprehensive Strategy:
        {strategies.get('comprehensive', 'Not available')[:1000]}
        
        Efficient Strategy:
        {strategies.get('efficient', 'Not available')[:1000]}
        
        Alternative Strategy:
        {strategies.get('alternative', 'Not available')[:1000]}
        
        Context: {context}
        
        Create a unified strategy that combines the best elements of each approach,
        maintaining comprehensiveness while ensuring efficiency and incorporating
        creative alternatives where appropriate.
        """
        
        try:
            synthesis_response = await self.llm_manager.get_completion(
                prompt=synthesis_prompt,
                task_type=TaskType.NEGOTIATION,
                preferred_provider="openai"
            )
            return synthesis_response.content
        except Exception as e:
            logger.warning(f"Strategy synthesis failed: {e}")
            # Return the comprehensive strategy as fallback
            return strategies.get('comprehensive', strategies.get('efficient', 'Strategy synthesis unavailable'))
    
    async def _translate_strategy(self, strategy: str, target_language: str) -> str:
        """Translate strategy to target language."""
        if target_language == "en":
            return strategy
        
        language_name = self.supported_languages.get(target_language, target_language)
        
        translation_prompt = f"""
        Translate the following negotiation strategy to {language_name} ({target_language}).
        Maintain legal precision and professional tone. Adapt cultural references appropriately.
        
        Original Strategy:
        {strategy}
        
        Provide the translation maintaining the structure and professional legal language.
        """
        
        try:
            translation_response = await self.llm_manager.get_completion(
                prompt=translation_prompt,
                task_type=TaskType.GENERAL,
                preferred_provider="openai"
            )
            return translation_response.content
        except Exception as e:
            logger.warning(f"Strategy translation failed: {e}")
            return f"[Translation to {language_name} unavailable]\n\n{strategy}"
    
    async def _adapt_strategy_culturally(
        self,
        strategy: str,
        cultural_context: str,
        target_language: str
    ) -> str:
        """Adapt strategy for cultural context."""
        language_name = self.supported_languages.get(target_language, target_language)
        
        adaptation_prompt = f"""
        Adapt the following negotiation strategy for the cultural context: {cultural_context}
        Target language/culture: {language_name} ({target_language})
        
        Original Strategy:
        {strategy}
        
        Provide cultural adaptations that consider:
        1. Communication styles and preferences
        2. Business relationship norms
        3. Decision-making processes
        4. Legal and regulatory considerations
        5. Negotiation etiquette and expectations
        
        Maintain the core strategic objectives while adapting the approach.
        """
        
        try:
            adaptation_response = await self.llm_manager.get_completion(
                prompt=adaptation_prompt,
                task_type=TaskType.NEGOTIATION,
                preferred_provider="openai"
            )
            return adaptation_response.content
        except Exception as e:
            logger.warning(f"Cultural adaptation failed: {e}")
            return f"[Cultural adaptation for {cultural_context} unavailable]\n\n{strategy}"
    
    def _calculate_synthesis_confidence(self, strategies: Dict[str, str]) -> float:
        """Calculate confidence score for strategy synthesis."""
        available_strategies = len([s for s in strategies.values() if s and s != "Not available"])
        total_strategies = len(strategies)
        
        if available_strategies == 0:
            return 0.0
        elif available_strategies == 1:
            return 0.6
        elif available_strategies == 2:
            return 0.8
        else:
            return 0.95
    
    def _update_success_metrics(
        self,
        negotiation_id: str,
        outcome: NegotiationOutcome,
        outcome_details: Dict[str, Any]
    ):
        """Update success metrics based on outcome."""
        self.success_metrics["total_negotiations"] += 1
        
        if outcome in [NegotiationOutcome.ACCEPTED, NegotiationOutcome.MODIFIED]:
            self.success_metrics["successful_closures"] += 1
        
        # Update acceptance rate by priority
        priority = outcome_details.get("priority", "unknown")
        if priority not in self.success_metrics["acceptance_rate_by_priority"]:
            self.success_metrics["acceptance_rate_by_priority"][priority] = {"total": 0, "accepted": 0}
        
        self.success_metrics["acceptance_rate_by_priority"][priority]["total"] += 1
        if outcome == NegotiationOutcome.ACCEPTED:
            self.success_metrics["acceptance_rate_by_priority"][priority]["accepted"] += 1
        
        # Track rejection reasons
        if outcome == NegotiationOutcome.REJECTED:
            reason = outcome_details.get("rejection_reason", "unknown")
            if reason not in self.success_metrics["common_rejection_reasons"]:
                self.success_metrics["common_rejection_reasons"][reason] = 0
            self.success_metrics["common_rejection_reasons"][reason] += 1
    
    def _analyze_single_negotiation(self, negotiation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patterns in a single negotiation."""
        clauses = negotiation_data["clauses"]
        phases = negotiation_data["phases"]
        
        outcomes = [clause["outcome"] for clause in clauses.values()]
        outcome_counts = {outcome: outcomes.count(outcome) for outcome in set(outcomes)}
        
        avg_duration = sum(clause["duration_days"] for clause in clauses.values()) / len(clauses)
        
        return {
            "negotiation_id": negotiation_data["negotiation_id"],
            "total_clauses": len(clauses),
            "outcome_distribution": outcome_counts,
            "average_clause_duration_days": avg_duration,
            "phases_completed": len(phases),
            "success_rate": (outcome_counts.get("accepted", 0) + outcome_counts.get("modified", 0)) / len(clauses),
            "most_common_outcome": max(outcome_counts, key=outcome_counts.get) if outcome_counts else "none"
        }
    
    def _analyze_outcome_patterns(self, recent_outcomes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns across multiple negotiations."""
        if not recent_outcomes:
            return {"message": "No recent outcomes to analyze"}
        
        outcomes = [outcome["outcome"] for outcome in recent_outcomes]
        phases = [outcome["phase"] for outcome in recent_outcomes]
        
        outcome_counts = {outcome: outcomes.count(outcome) for outcome in set(outcomes)}
        phase_counts = {phase: phases.count(phase) for phase in set(phases)}
        
        success_rate = (outcome_counts.get("accepted", 0) + outcome_counts.get("modified", 0)) / len(outcomes)
        
        return {
            "total_outcomes": len(recent_outcomes),
            "outcome_distribution": outcome_counts,
            "phase_distribution": phase_counts,
            "overall_success_rate": success_rate,
            "most_successful_phase": max(phase_counts, key=phase_counts.get) if phase_counts else "none",
            "trends": self._identify_trends(recent_outcomes)
        }
    
    def _identify_trends(self, outcomes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify trends in negotiation outcomes."""
        # Sort by timestamp
        sorted_outcomes = sorted(outcomes, key=lambda x: x["timestamp"])
        
        if len(sorted_outcomes) < 2:
            return {"message": "Insufficient data for trend analysis"}
        
        # Calculate success rate over time (simple trend)
        mid_point = len(sorted_outcomes) // 2
        early_outcomes = sorted_outcomes[:mid_point]
        recent_outcomes = sorted_outcomes[mid_point:]
        
        early_success = sum(1 for o in early_outcomes if o["outcome"] in ["accepted", "modified"]) / len(early_outcomes)
        recent_success = sum(1 for o in recent_outcomes if o["outcome"] in ["accepted", "modified"]) / len(recent_outcomes)
        
        trend_direction = "improving" if recent_success > early_success else "declining" if recent_success < early_success else "stable"
        
        return {
            "success_rate_trend": trend_direction,
            "early_period_success_rate": early_success,
            "recent_period_success_rate": recent_success,
            "trend_magnitude": abs(recent_success - early_success)
        }
    
    def _format_clauses_for_prompt(self, clauses: List[Dict[str, Any]]) -> str:
        """Format clauses for prompt inclusion."""
        formatted = []
        for i, clause in enumerate(clauses[:5], 1):
            formatted.append(f"{i}. {clause.get('clause_type', 'Unknown')}: {clause.get('risk_explanation', 'No explanation')[:100]}...")
        return "\n".join(formatted)
    
    def _format_top_risks_for_prompt(self, clauses: List[Dict[str, Any]]) -> str:
        """Format top risks for efficient strategy prompt."""
        formatted = []
        for i, clause in enumerate(clauses[:3], 1):
            risk_score = clause.get('overall_risk_score', 0)
            formatted.append(f"{i}. Risk Score {risk_score}/10: {clause.get('clause_type', 'Unknown')}")
        return "\n".join(formatted)
    
    def _format_challenges_for_prompt(self, clauses: List[Dict[str, Any]]) -> str:
        """Format challenges for alternative strategy prompt."""
        challenges = []
        for clause in clauses[:5]:
            if clause.get('risk_level') == 'High':
                challenges.append(f"High-risk {clause.get('clause_type', 'clause')}")
        return ", ".join(challenges) if challenges else "Standard contract risks"
    
    async def _generate_fallback_strategy(
        self,
        risky_clauses: List[Dict[str, Any]],
        precedent_matches: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate fallback strategy when multi-LLM approach fails."""
        try:
            # Use single provider fallback
            fallback_prompt = self._create_strategy_prompt(
                risky_clauses, precedent_matches, context, "comprehensive"
            )
            
            fallback_response = await self.llm_manager.get_completion(
                prompt=fallback_prompt,
                task_type=TaskType.NEGOTIATION
            )
            
            return {
                "unified_strategy": fallback_response.content,
                "individual_strategies": {"fallback": fallback_response.content},
                "strategy_metadata": {
                    "providers_used": ["fallback"],
                    "target_language": context.get("target_language", "en"),
                    "cultural_context": context.get("cultural_context"),
                    "synthesis_confidence": 0.7
                }
            }
        except Exception as e:
            logger.error(f"Fallback strategy generation failed: {e}")
            return {
                "unified_strategy": "Strategy generation unavailable due to system error.",
                "individual_strategies": {},
                "strategy_metadata": {
                    "providers_used": [],
                    "error": str(e),
                    "synthesis_confidence": 0.0
                }
            }
    
    async def _generate_redline_suggestions(
        self, 
        risky_clauses: List[Dict[str, Any]], 
        precedent_matches: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate specific redline suggestions for risky clauses.
        
        Args:
            risky_clauses: List of risky clauses
            precedent_matches: List of relevant precedents
            
        Returns:
            List[Dict[str, Any]]: List of redline suggestions
        """
        redline_suggestions = []
        
        for clause in risky_clauses:
            try:
                # Find relevant precedents for this clause
                relevant_precedents = self._find_relevant_precedents(clause, precedent_matches)
                
                # Use CrewAI agent to generate redlines
                redline_task = Task(
                    description=f"""Generate specific redline suggestions for a risky contract clause.
                    
                    Original Clause:
                    Text: {clause.get('clause_text', '')}
                    Type: {clause.get('clause_type', 'unknown')}
                    Risk Level: {clause.get('risk_level', 'unknown')}
                    Risk Score: {clause.get('overall_risk_score', 0)}/10
                    Risk Explanation: {clause.get('risk_explanation', '')}
                    
                    Relevant Precedents:
                    {self._format_precedents_for_redlines(relevant_precedents)}
                    
                    Please provide:
                    1. Specific redlined text with tracked changes
                    2. Alternative clause language options
                    3. Rationale for each change
                    4. Risk mitigation achieved
                    5. Priority level (critical/important/preferred/minor)
                    6. Negotiation difficulty assessment
                    7. Business impact of the change
                    
                    Focus on practical, implementable changes that reduce risk while maintaining commercial viability.
                    
                    Provide results in JSON format.""",
                    agent=self.crew_agent,
                    expected_output="JSON with detailed redline suggestions and rationale"
                )
                
                # Execute the redline generation
                redline_result = await redline_task.execute_async()
                
                # Parse the redline suggestions
                parsed_redlines = self._parse_redline_suggestions(redline_result, clause)
                
                redline_suggestions.extend(parsed_redlines)
                
            except Exception as e:
                logger.warning(f"Failed to generate redlines for clause {clause.get('clause_index', 'unknown')}: {e}")
                
                # Create basic redline as fallback
                basic_redline = self._create_basic_redline(clause)
                redline_suggestions.append(basic_redline)
        
        return redline_suggestions
    
    async def _develop_negotiation_strategy(
        self,
        risky_clauses: List[Dict[str, Any]],
        precedent_matches: List[Dict[str, Any]],
        contract_structure: Dict[str, Any]
    ) -> str:
        """
        Develop overall negotiation strategy.
        
        Args:
            risky_clauses: List of risky clauses
            precedent_matches: List of precedent matches
            contract_structure: Contract structure information
            
        Returns:
            str: Comprehensive negotiation strategy
        """
        try:
            # Use CrewAI agent to develop strategy
            strategy_task = Task(
                description=f"""Develop a comprehensive negotiation strategy for contract risk mitigation.
                
                Contract Context:
                Type: {contract_structure.get('contract_type', 'unknown')}
                Risky Clauses: {len(risky_clauses)}
                High-Risk Clauses: {len([c for c in risky_clauses if c.get('risk_level') == 'High'])}
                
                Key Risk Areas:
                {self._format_risk_areas_for_strategy(risky_clauses)}
                
                Available Precedents: {len(precedent_matches)}
                
                Please develop a strategy that includes:
                1. Overall negotiation approach and philosophy
                2. Key leverage points and negotiation priorities
                3. Sequencing of negotiation points
                4. Risk vs. relationship balance considerations
                5. Potential concessions and trade-offs
                6. Timeline and milestone recommendations
                7. Success metrics and fallback positions
                8. Communication and relationship management tactics
                
                The strategy should be practical, actionable, and focused on achieving optimal risk mitigation
                while preserving business relationships and commercial objectives.""",
                agent=self.crew_agent,
                expected_output="Comprehensive negotiation strategy with actionable recommendations"
            )
            
            # Execute the strategy development
            strategy_result = await strategy_task.execute_async()
            
            return str(strategy_result).strip()
            
        except Exception as e:
            logger.warning(f"Failed to develop negotiation strategy: {e}")
            
            # Fallback strategy
            return self._generate_fallback_negotiation_strategy(risky_clauses, contract_structure)
    
    async def _create_alternative_clauses(
        self,
        risky_clauses: List[Dict[str, Any]],
        precedent_matches: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create alternative clause language options.
        
        Args:
            risky_clauses: List of risky clauses
            precedent_matches: List of precedent matches
            
        Returns:
            List[Dict[str, Any]]: List of alternative clause options
        """
        alternative_clauses = []
        
        # Focus on high-risk clauses for alternatives
        high_risk_clauses = [c for c in risky_clauses if c.get('risk_level') == 'High']
        
        for clause in high_risk_clauses[:5]:  # Limit to top 5 high-risk clauses
            try:
                relevant_precedents = self._find_relevant_precedents(clause, precedent_matches)
                
                # Use CrewAI agent to create alternatives
                alternatives_task = Task(
                    description=f"""Create alternative clause language options for a high-risk contract clause.
                    
                    Original High-Risk Clause:
                    Text: {clause.get('clause_text', '')}
                    Type: {clause.get('clause_type', 'unknown')}
                    Risk Explanation: {clause.get('risk_explanation', '')}
                    
                    Relevant Precedents:
                    {self._format_precedents_for_alternatives(relevant_precedents)}
                    
                    Please provide 3-4 alternative clause options:
                    1. Conservative alternative (minimal risk, may be less favorable commercially)
                    2. Balanced alternative (moderate risk reduction with commercial balance)
                    3. Aggressive alternative (maximum risk reduction, may impact commercial terms)
                    4. Industry standard alternative (based on precedents and best practices)
                    
                    For each alternative, provide:
                    - Complete alternative clause text
                    - Risk reduction achieved
                    - Commercial impact assessment
                    - Likelihood of acceptance
                    - Implementation considerations
                    
                    Provide results in JSON format.""",
                    agent=self.crew_agent,
                    expected_output="JSON with multiple alternative clause options and assessments"
                )
                
                # Execute the alternatives creation
                alternatives_result = await alternatives_task.execute_async()
                
                # Parse the alternatives
                parsed_alternatives = self._parse_alternative_clauses(alternatives_result, clause)
                
                alternative_clauses.extend(parsed_alternatives)
                
            except Exception as e:
                logger.warning(f"Failed to create alternatives for clause {clause.get('clause_index', 'unknown')}: {e}")
                
                # Create basic alternatives as fallback
                basic_alternatives = self._create_basic_alternatives(clause)
                alternative_clauses.extend(basic_alternatives)
        
        return alternative_clauses
    
    async def _generate_talking_points(
        self,
        suggested_redlines: List[Dict[str, Any]],
        negotiation_strategy: str
    ) -> List[Dict[str, Any]]:
        """
        Generate negotiation talking points.
        
        Args:
            suggested_redlines: List of redline suggestions
            negotiation_strategy: Overall negotiation strategy
            
        Returns:
            List[Dict[str, Any]]: List of talking points
        """
        try:
            # Use CrewAI agent to generate talking points
            talking_points_task = Task(
                description=f"""Generate specific negotiation talking points for contract discussions.
                
                Negotiation Strategy Overview:
                {negotiation_strategy[:1000]}...
                
                Key Redlines to Discuss:
                {self._format_redlines_for_talking_points(suggested_redlines[:10])}
                
                Please provide talking points that include:
                1. Opening statements and positioning
                2. Rationale for each major redline request
                3. Business justification and risk explanations
                4. Precedent-based arguments
                5. Compromise and trade-off suggestions
                6. Responses to likely counterarguments
                7. Closing and next steps language
                
                Each talking point should be:
                - Clear and persuasive
                - Backed by business rationale
                - Professional and relationship-preserving
                - Focused on mutual benefit where possible
                
                Provide results in JSON format as a list of talking point objects.""",
                agent=self.crew_agent,
                expected_output="JSON list of structured negotiation talking points"
            )
            
            # Execute the talking points generation
            talking_points_result = await talking_points_task.execute_async()
            
            # Parse the talking points
            talking_points = self._parse_talking_points(talking_points_result)
            
            return talking_points
            
        except Exception as e:
            logger.warning(f"Failed to generate talking points: {e}")
            
            # Fallback talking points
            return self._generate_fallback_talking_points(suggested_redlines)
    
    async def _create_fallback_positions(
        self,
        suggested_redlines: List[Dict[str, Any]],
        risky_clauses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create fallback positions for negotiations.
        
        Args:
            suggested_redlines: List of redline suggestions
            risky_clauses: List of risky clauses
            
        Returns:
            List[Dict[str, Any]]: List of fallback positions
        """
        try:
            # Use CrewAI agent to create fallback positions
            fallback_task = Task(
                description=f"""Create fallback positions for contract negotiations.
                
                Primary Redline Requests:
                {self._format_redlines_for_fallbacks(suggested_redlines)}
                
                Risk Context:
                High-Risk Clauses: {len([c for c in risky_clauses if c.get('risk_level') == 'High'])}
                Medium-Risk Clauses: {len([c for c in risky_clauses if c.get('risk_level') == 'Medium'])}
                
                For each major negotiation point, please provide:
                1. Primary position (ideal outcome)
                2. Secondary position (acceptable compromise)
                3. Minimum acceptable position (deal-breaker threshold)
                4. Walk-away criteria
                5. Alternative value creation opportunities
                
                Focus on maintaining deal viability while protecting critical interests.
                
                Provide results in JSON format.""",
                agent=self.crew_agent,
                expected_output="JSON with structured fallback positions for key negotiation points"
            )
            
            # Execute the fallback creation
            fallback_result = await fallback_task.execute_async()
            
            # Parse the fallback positions
            fallback_positions = self._parse_fallback_positions(fallback_result)
            
            return fallback_positions
            
        except Exception as e:
            logger.warning(f"Failed to create fallback positions: {e}")
            
            # Fallback fallbacks (meta-fallback)
            return self._generate_fallback_fallback_positions(suggested_redlines)
    
    def _initialize_revision_tracking(
        self,
        suggested_redlines: List[Dict[str, Any]],
        workflow_id: str,
        contract_structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Initialize contract revision tracking system.
        
        Args:
            suggested_redlines: List of redline suggestions
            workflow_id: Current workflow identifier
            contract_structure: Contract structure information
            
        Returns:
            Dict[str, Any]: Revision tracking data structure
        """
        self.revision_counter += 1
        revision_id = f"rev_{self.revision_counter}_{workflow_id}"
        
        # Create revision tracking entry
        revision_entry = {
            "revision_id": revision_id,
            "created_at": datetime.utcnow().isoformat(),
            "workflow_id": workflow_id,
            "contract_type": contract_structure.get("contract_type", "unknown"),
            "total_changes": len(suggested_redlines),
            "changes_by_priority": {
                "critical": len([r for r in suggested_redlines if r.get("priority") == "critical"]),
                "important": len([r for r in suggested_redlines if r.get("priority") == "important"]),
                "preferred": len([r for r in suggested_redlines if r.get("priority") == "preferred"]),
                "minor": len([r for r in suggested_redlines if r.get("priority") == "minor"])
            },
            "changes": [],
            "status": "proposed",
            "acceptance_tracking": {},
            "modification_history": []
        }
        
        # Track individual changes
        for i, redline in enumerate(suggested_redlines):
            change_id = f"change_{i+1}_{revision_id}"
            change_entry = {
                "change_id": change_id,
                "clause_index": redline.get("clause_index", i),
                "clause_type": redline.get("clause_type", "unknown"),
                "original_text": redline.get("original_clause", ""),
                "suggested_text": redline.get("suggested_redline", ""),
                "change_type": self._classify_change_type(redline),
                "priority": redline.get("priority", "preferred"),
                "rationale": redline.get("change_rationale", ""),
                "risk_mitigation": redline.get("risk_mitigated", False),
                "business_impact": redline.get("business_impact", ""),
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
                "modified_at": None,
                "accepted_at": None,
                "rejected_at": None,
                "modification_count": 0,
                "modification_history": []
            }
            revision_entry["changes"].append(change_entry)
        
        # Store in revision history
        self.revision_history.append(revision_entry)
        self.change_tracking[revision_id] = revision_entry
        
        logger.info(f"Initialized revision tracking for {len(suggested_redlines)} changes (revision: {revision_id})")
        
        return revision_entry
    
    def track_change_acceptance(
        self,
        revision_id: str,
        change_id: str,
        status: str,
        modified_text: Optional[str] = None,
        user_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Track acceptance, rejection, or modification of a specific change.
        
        Args:
            revision_id: Revision identifier
            change_id: Specific change identifier
            status: New status (accepted, rejected, modified)
            modified_text: Modified text if status is 'modified'
            user_notes: Optional user notes
            
        Returns:
            Dict[str, Any]: Updated change tracking information
        """
        if revision_id not in self.change_tracking:
            raise ValidationError(f"Revision {revision_id} not found in tracking system")
        
        revision = self.change_tracking[revision_id]
        change_found = False
        
        for change in revision["changes"]:
            if change["change_id"] == change_id:
                change_found = True
                old_status = change["status"]
                
                # Update change status
                change["status"] = status
                change["modified_at"] = datetime.utcnow().isoformat()
                
                if status == "accepted":
                    change["accepted_at"] = datetime.utcnow().isoformat()
                elif status == "rejected":
                    change["rejected_at"] = datetime.utcnow().isoformat()
                elif status == "modified":
                    change["modification_count"] += 1
                    if modified_text:
                        change["suggested_text"] = modified_text
                    
                    # Track modification history
                    modification_entry = {
                        "modification_id": f"mod_{change['modification_count']}_{change_id}",
                        "previous_text": change.get("suggested_text", ""),
                        "new_text": modified_text or "",
                        "modified_at": datetime.utcnow().isoformat(),
                        "user_notes": user_notes
                    }
                    change["modification_history"].append(modification_entry)
                
                # Update revision-level tracking
                if old_status != status:
                    if status not in revision["acceptance_tracking"]:
                        revision["acceptance_tracking"][status] = 0
                    revision["acceptance_tracking"][status] += 1
                    
                    if old_status in revision["acceptance_tracking"]:
                        revision["acceptance_tracking"][old_status] -= 1
                
                logger.info(f"Change {change_id} status updated from {old_status} to {status}")
                break
        
        if not change_found:
            raise ValidationError(f"Change {change_id} not found in revision {revision_id}")
        
        return revision
    
    def generate_revised_contract(
        self,
        revision_id: str,
        original_contract_text: str,
        include_only_accepted: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a revised contract document with tracked changes.
        
        Args:
            revision_id: Revision identifier
            original_contract_text: Original contract text
            include_only_accepted: Whether to include only accepted changes
            
        Returns:
            Dict[str, Any]: Revised contract information
        """
        if revision_id not in self.change_tracking:
            raise ValidationError(f"Revision {revision_id} not found in tracking system")
        
        revision = self.change_tracking[revision_id]
        revised_text = original_contract_text
        applied_changes = []
        
        # Sort changes by clause index to apply in order
        changes = sorted(revision["changes"], key=lambda x: x.get("clause_index", 0))
        
        for change in changes:
            should_apply = False
            
            if include_only_accepted:
                should_apply = change["status"] == "accepted"
            else:
                should_apply = change["status"] in ["accepted", "modified"]
            
            if should_apply:
                original_text = change["original_text"]
                suggested_text = change["suggested_text"]
                
                # Apply the change to the contract text
                if original_text and original_text in revised_text:
                    revised_text = revised_text.replace(original_text, suggested_text, 1)
                    applied_changes.append({
                        "change_id": change["change_id"],
                        "clause_type": change["clause_type"],
                        "change_type": change["change_type"],
                        "priority": change["priority"],
                        "applied_at": datetime.utcnow().isoformat()
                    })
        
        # Generate change summary
        change_summary = {
            "total_changes_proposed": len(revision["changes"]),
            "changes_applied": len(applied_changes),
            "changes_by_priority": {},
            "changes_by_type": {},
            "revision_metadata": {
                "revision_id": revision_id,
                "generated_at": datetime.utcnow().isoformat(),
                "include_only_accepted": include_only_accepted
            }
        }
        
        # Aggregate statistics
        for change in applied_changes:
            priority = change["priority"]
            change_type = change["change_type"]
            
            if priority not in change_summary["changes_by_priority"]:
                change_summary["changes_by_priority"][priority] = 0
            change_summary["changes_by_priority"][priority] += 1
            
            if change_type not in change_summary["changes_by_type"]:
                change_summary["changes_by_type"][change_type] = 0
            change_summary["changes_by_type"][change_type] += 1
        
        logger.info(f"Generated revised contract with {len(applied_changes)} applied changes")
        
        return {
            "revised_contract_text": revised_text,
            "applied_changes": applied_changes,
            "change_summary": change_summary,
            "revision_id": revision_id
        }
    
    def get_revision_status(self, revision_id: str) -> Dict[str, Any]:
        """
        Get the current status of a revision.
        
        Args:
            revision_id: Revision identifier
            
        Returns:
            Dict[str, Any]: Revision status information
        """
        if revision_id not in self.change_tracking:
            raise ValidationError(f"Revision {revision_id} not found in tracking system")
        
        revision = self.change_tracking[revision_id]
        
        # Calculate status statistics
        status_counts = {"pending": 0, "accepted": 0, "rejected": 0, "modified": 0}
        for change in revision["changes"]:
            status = change["status"]
            if status in status_counts:
                status_counts[status] += 1
        
        # Calculate completion percentage
        total_changes = len(revision["changes"])
        processed_changes = status_counts["accepted"] + status_counts["rejected"] + status_counts["modified"]
        completion_percentage = (processed_changes / total_changes * 100) if total_changes > 0 else 0
        
        return {
            "revision_id": revision_id,
            "total_changes": total_changes,
            "status_counts": status_counts,
            "completion_percentage": completion_percentage,
            "created_at": revision["created_at"],
            "last_modified": max(
                [change.get("modified_at") or change["created_at"] for change in revision["changes"]]
            ) if revision["changes"] else revision["created_at"]
        }
    
    def _classify_change_type(self, redline: Dict[str, Any]) -> str:
        """
        Classify the type of change based on redline content.
        
        Args:
            redline: Redline suggestion
            
        Returns:
            str: Change type classification
        """
        original_text = redline.get("original_clause", "").lower()
        suggested_text = redline.get("suggested_redline", "").lower()
        
        # Check for specific patterns first (more specific rules)
        if "shall not exceed" in suggested_text and "shall not exceed" not in original_text:
            return "limitation"
        elif "liability" in original_text and "liability" in suggested_text:
            return "liability_modification"
        elif "termination" in original_text and "termination" in suggested_text:
            return "termination_modification"
        elif "payment" in original_text and "payment" in suggested_text:
            return "payment_modification"
        # Then check for length-based patterns (less specific rules)
        elif len(suggested_text) > len(original_text) * 1.5:
            return "addition"
        elif len(suggested_text) < len(original_text) * 0.5:
            return "deletion"
        else:
            return "modification"

    def _find_relevant_precedents(
        self, 
        clause: Dict[str, Any], 
        precedent_matches: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find precedents relevant to a specific clause"""
        clause_type = clause.get("clause_type", "").lower()
        relevant_precedents = []
        
        for precedent in precedent_matches:
            original_clause = precedent.get("original_clause", {})
            if original_clause.get("clause_type", "").lower() == clause_type:
                relevant_precedents.append(precedent)
        
        return relevant_precedents[:3]  # Limit to top 3 relevant precedents
    
    def _prioritize_negotiation_points(
        self, 
        suggested_redlines: List[Dict[str, Any]], 
        risky_clauses: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Prioritize negotiation points by importance"""
        priorities = {
            "critical": [],
            "important": [],
            "preferred": [],
            "minor": []
        }
        
        for redline in suggested_redlines:
            priority = redline.get("priority", "preferred")
            if priority in priorities:
                priorities[priority].append(redline)
        
        return priorities
    
    def _determine_strategy_focus(self, risky_clauses: List[Dict[str, Any]]) -> str:
        """Determine the primary focus of negotiation strategy"""
        high_risk_count = len([c for c in risky_clauses if c.get('risk_level') == 'High'])
        
        if high_risk_count >= 5:
            return "aggressive_risk_mitigation"
        elif high_risk_count >= 2:
            return "balanced_risk_reduction"
        else:
            return "minor_optimizations"
    
    def _assess_negotiation_complexity(self, risky_clauses: List[Dict[str, Any]]) -> str:
        """Assess the complexity of the negotiation"""
        total_risk_score = sum(c.get('overall_risk_score', 0) for c in risky_clauses)
        avg_risk_score = total_risk_score / len(risky_clauses) if risky_clauses else 0
        
        if avg_risk_score >= 7:
            return "high"
        elif avg_risk_score >= 5:
            return "medium"
        else:
            return "low"
    
    def _format_precedents_for_redlines(self, precedents: List[Dict[str, Any]]) -> str:
        """Format precedents for redline generation prompts"""
        if not precedents:
            return "No relevant precedents found."
        
        formatted = []
        for i, precedent in enumerate(precedents, 1):
            precedent_clause = precedent.get("precedent_clause", {})
            formatted.append(
                f"{i}. {getattr(precedent_clause, 'source_document', 'Unknown')}: "
                f"{getattr(precedent_clause, 'text', '')[:200]}..."
            )
        
        return "\n".join(formatted)
    
    def _format_precedents_for_alternatives(self, precedents: List[Dict[str, Any]]) -> str:
        """Format precedents for alternative clause generation"""
        return self._format_precedents_for_redlines(precedents)
    
    def _format_risk_areas_for_strategy(self, risky_clauses: List[Dict[str, Any]]) -> str:
        """Format risk areas for strategy development"""
        risk_areas = {}
        
        for clause in risky_clauses:
            clause_type = clause.get("clause_type", "unknown")
            risk_level = clause.get("risk_level", "unknown")
            
            if clause_type not in risk_areas:
                risk_areas[clause_type] = {"high": 0, "medium": 0, "low": 0}
            
            risk_areas[clause_type][risk_level.lower()] += 1
        
        formatted = []
        for area, counts in risk_areas.items():
            total = sum(counts.values())
            formatted.append(f"- {area.title()}: {total} clauses (High: {counts['high']}, Medium: {counts['medium']}, Low: {counts['low']})")
        
        return "\n".join(formatted)
    
    def _format_redlines_for_talking_points(self, redlines: List[Dict[str, Any]]) -> str:
        """Format redlines for talking points generation"""
        formatted = []
        
        for i, redline in enumerate(redlines, 1):
            formatted.append(
                f"{i}. {redline.get('clause_type', 'Unknown')} - "
                f"Priority: {redline.get('priority', 'unknown')} - "
                f"Change: {redline.get('change_summary', 'No summary available')}"
            )
        
        return "\n".join(formatted)
    
    def _format_redlines_for_fallbacks(self, redlines: List[Dict[str, Any]]) -> str:
        """Format redlines for fallback position generation"""
        return self._format_redlines_for_talking_points(redlines)
    
    def _parse_redline_suggestions(self, redline_result: str, original_clause: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse redline suggestions from agent result"""
        try:
            import json
            
            # Try to extract JSON from the result
            if isinstance(redline_result, str):
                start_idx = redline_result.find('{')
                end_idx = redline_result.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = redline_result[start_idx:end_idx]
                    redline_data = json.loads(json_str)
                    
                    # Convert to list if single redline
                    if not isinstance(redline_data, list):
                        redline_data = [redline_data]
                    
                    parsed_redlines = []
                    for redline in redline_data:
                        parsed_redline = {
                            "original_clause": original_clause.get("clause_text", ""),
                            "suggested_redline": redline.get("suggested_redline", ""),
                            "clause_type": original_clause.get("clause_type", "unknown"),
                            "clause_index": original_clause.get("clause_index", 0),
                            "change_rationale": redline.get("change_rationale", ""),
                            "risk_mitigated": redline.get("risk_mitigated", True),
                            "priority": redline.get("priority", "preferred"),
                            "negotiation_difficulty": redline.get("negotiation_difficulty", "medium"),
                            "business_impact": redline.get("business_impact", ""),
                            "change_summary": redline.get("change_summary", "")
                        }
                        parsed_redlines.append(parsed_redline)
                    
                    return parsed_redlines
            
            # If parsing fails, create basic redline
            return [self._create_basic_redline(original_clause)]
            
        except Exception as e:
            logger.warning(f"Failed to parse redline suggestions: {e}")
            return [self._create_basic_redline(original_clause)]
    
    def _create_basic_redline(self, clause: Dict[str, Any]) -> Dict[str, Any]:
        """Create basic redline as fallback"""
        clause_type = clause.get("clause_type", "unknown").lower()
        
        # Basic redline templates
        redline_templates = {
            "liability": "Add liability cap: 'Total liability shall not exceed the total fees paid under this agreement.'",
            "termination": "Add notice period: 'Either party may terminate with thirty (30) days written notice.'",
            "payment": "Clarify payment terms: 'Payment is due within thirty (30) days of invoice receipt.'",
            "confidentiality": "Add mutual confidentiality: 'Both parties agree to maintain confidentiality of disclosed information.'"
        }
        
        suggested_redline = redline_templates.get(clause_type, "Review and clarify terms to reduce risk exposure.")
        
        return {
            "original_clause": clause.get("clause_text", ""),
            "suggested_redline": suggested_redline,
            "clause_type": clause.get("clause_type", "unknown"),
            "clause_index": clause.get("clause_index", 0),
            "change_rationale": f"Risk mitigation for {clause_type} clause",
            "risk_mitigated": True,
            "priority": "important",
            "negotiation_difficulty": "medium",
            "business_impact": "Moderate positive impact on risk profile",
            "change_summary": f"Added standard {clause_type} protection"
        }
    
    def _parse_alternative_clauses(self, alternatives_result: str, original_clause: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse alternative clauses from agent result"""
        try:
            import json
            
            # Try to extract JSON from the result
            if isinstance(alternatives_result, str):
                start_idx = alternatives_result.find('[')
                end_idx = alternatives_result.rfind(']') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = alternatives_result[start_idx:end_idx]
                    alternatives_data = json.loads(json_str)
                    
                    parsed_alternatives = []
                    for alt in alternatives_data:
                        parsed_alternative = {
                            "original_clause": original_clause,
                            "alternative_text": alt.get("alternative_text", ""),
                            "alternative_type": alt.get("alternative_type", "balanced"),
                            "risk_reduction": alt.get("risk_reduction", "moderate"),
                            "commercial_impact": alt.get("commercial_impact", "neutral"),
                            "acceptance_likelihood": alt.get("acceptance_likelihood", "medium"),
                            "implementation_notes": alt.get("implementation_notes", "")
                        }
                        parsed_alternatives.append(parsed_alternative)
                    
                    return parsed_alternatives
            
            # If parsing fails, create basic alternatives
            return self._create_basic_alternatives(original_clause)
            
        except Exception as e:
            logger.warning(f"Failed to parse alternative clauses: {e}")
            return self._create_basic_alternatives(original_clause)
    
    def _create_basic_alternatives(self, clause: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create basic alternatives as fallback"""
        return [
            {
                "original_clause": clause,
                "alternative_text": "Conservative alternative with maximum risk protection",
                "alternative_type": "conservative",
                "risk_reduction": "high",
                "commercial_impact": "may reduce commercial flexibility",
                "acceptance_likelihood": "low",
                "implementation_notes": "Requires significant negotiation"
            },
            {
                "original_clause": clause,
                "alternative_text": "Balanced alternative with moderate risk reduction",
                "alternative_type": "balanced",
                "risk_reduction": "moderate",
                "commercial_impact": "neutral",
                "acceptance_likelihood": "medium",
                "implementation_notes": "Good starting point for negotiations"
            }
        ]
    
    def _parse_talking_points(self, talking_points_result: str) -> List[Dict[str, Any]]:
        """Parse talking points from agent result"""
        try:
            import json
            
            # Try to extract JSON from the result
            if isinstance(talking_points_result, str):
                start_idx = talking_points_result.find('[')
                end_idx = talking_points_result.rfind(']') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = talking_points_result[start_idx:end_idx]
                    return json.loads(json_str)
            
            # If parsing fails, create basic talking points
            return self._generate_fallback_talking_points([])
            
        except Exception as e:
            logger.warning(f"Failed to parse talking points: {e}")
            return self._generate_fallback_talking_points([])
    
    def _parse_fallback_positions(self, fallback_result: str) -> List[Dict[str, Any]]:
        """Parse fallback positions from agent result"""
        try:
            import json
            
            # Try to extract JSON from the result
            if isinstance(fallback_result, str):
                start_idx = fallback_result.find('[')
                end_idx = fallback_result.rfind(']') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = fallback_result[start_idx:end_idx]
                    return json.loads(json_str)
            
            # If parsing fails, create basic fallback positions
            return self._generate_fallback_fallback_positions([])
            
        except Exception as e:
            logger.warning(f"Failed to parse fallback positions: {e}")
            return self._generate_fallback_fallback_positions([])
    
    def _generate_fallback_negotiation_strategy(
        self, 
        risky_clauses: List[Dict[str, Any]], 
        contract_structure: Dict[str, Any]
    ) -> str:
        """Generate fallback negotiation strategy"""
        high_risk_count = len([c for c in risky_clauses if c.get('risk_level') == 'High'])
        
        return f"""Negotiation Strategy Summary:

Approach: {'Aggressive risk mitigation' if high_risk_count >= 3 else 'Balanced negotiation'}

Key Priorities:
1. Address {high_risk_count} high-risk clauses immediately
2. Negotiate balanced risk allocation
3. Maintain positive business relationship
4. Ensure legal compliance and protection

Recommended Sequence:
1. Start with relationship-building and context setting
2. Present business rationale for changes
3. Focus on mutual benefit and risk sharing
4. Use precedents and industry standards as support
5. Be prepared to offer reasonable concessions

Success Metrics:
- Reduce high-risk clause count by at least 50%
- Achieve acceptable risk allocation balance
- Maintain deal viability and timeline
- Preserve long-term business relationship"""
    
    def _generate_fallback_talking_points(self, suggested_redlines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate fallback talking points"""
        return [
            {
                "topic": "Opening Position",
                "talking_point": "We've conducted a thorough risk assessment and identified areas for improvement",
                "rationale": "Sets professional tone and demonstrates due diligence",
                "timing": "opening"
            },
            {
                "topic": "Risk Mitigation",
                "talking_point": "These changes will create a more balanced risk allocation",
                "rationale": "Focuses on mutual benefit rather than one-sided changes",
                "timing": "main_discussion"
            },
            {
                "topic": "Industry Standards",
                "talking_point": "Our proposed terms align with industry best practices",
                "rationale": "Uses external validation to support positions",
                "timing": "main_discussion"
            },
            {
                "topic": "Closing",
                "talking_point": "We're committed to finding mutually acceptable solutions",
                "rationale": "Maintains positive relationship focus",
                "timing": "closing"
            }
        ]
    
    def _generate_fallback_fallback_positions(self, suggested_redlines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate fallback fallback positions (meta-fallback)"""
        return [
            {
                "negotiation_point": "Liability Limitations",
                "primary_position": "Cap liability at contract value",
                "secondary_position": "Cap liability at 2x contract value",
                "minimum_position": "Exclude consequential damages",
                "walk_away_criteria": "Unlimited liability exposure"
            },
            {
                "negotiation_point": "Termination Rights",
                "primary_position": "30-day termination notice",
                "secondary_position": "60-day termination notice",
                "minimum_position": "90-day termination notice",
                "walk_away_criteria": "No termination rights"
            }
        ]